# Func_dash/analise_demografica_dashboard.py (VERSÃO CORRIGIDA FINAL)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import cKDTree
import logging
import unicodedata
from typing import Optional, Dict, List, Tuple
import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== Imports com Fallback ====================
try:
    from analise_demografica import (
        analisar_imoveis_demograficos,
        carregar_dados_demograficos,
        obter_estatisticas
    )
    from regra_idade import (
        get_faixas_disponiveis,
        filtrar_multiplas_faixas,
        validar_faixas_etarias,
        criar_resumo_faixas,
        calcular_distancia_haversine,
        encontrar_municipios_proximos,
        calcular_score_demografico
    )
    print("✓ Módulos de análise demográfica carregados")
except ImportError as e:
    print(f"⚠️ Aviso: Módulos não encontrados ({e}). Usando modo simplificado.")
    
    def carregar_dados_demograficos(path):
        return pd.read_csv(path, sep=',', encoding='utf-8')
    
    def get_faixas_disponiveis():
        return [
            "0 a 4 anos", "5 a 9 anos", "10 a 14 anos", "15 a 19 anos",
            "20 a 24 anos", "25 a 29 anos", "30 a 34 anos", "35 a 39 anos",
            "40 a 44 anos", "45 a 49 anos", "50 a 54 anos", "55 a 59 anos",
            "60 a 64 anos", "65 a 69 anos", "70 a 74 anos", "75 ou mais"
        ]
    
    def filtrar_multiplas_faixas(df, faixas):
        return df
    
    def validar_faixas_etarias(faixas):
        return True
    
    def encontrar_municipios_proximos(df1, df2, raio_km):
        return df1
    
    def calcular_score_demografico(df):
        if 'populacao_faixa' not in df.columns:
            df['populacao_faixa'] = 0
        df['score_demografico'] = np.random.random(len(df))
        return df

# ==================== Configuração de Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== Funções Auxiliares ====================

def normalizar_texto(texto: str) -> str:
    """
    Remove acentos e normaliza texto
    
    Args:
        texto: Texto para normalizar
    
    Returns:
        Texto sem acentos em maiúsculas
    """
    if not isinstance(texto, str):
        texto = str(texto)
    
    # Normalizar unicode (NFD = Canonical Decomposition)
    nfkd = unicodedata.normalize('NFD', texto)
    
    # Remover caracteres de combinação (acentos)
    sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    return sem_acento.upper().strip()


# ==================== Cache Global ====================
class DataCache:
    """Cache para evitar recálculos"""
    def __init__(self):
        self.kdtree = None
        self.imoveis_coords = None
        self.municipios_dict = {}
        self.municipios_dict_normalizado = {}  # Novo: cache sem acentos
        self.df_imoveis = None
        self.df_idade = None
        self.lista_municipios = []

_cache = DataCache()

# ==================== Funções Principais ====================


def inicializar_dados(
    path_imoveis: str = "../../Data/Processed/imovel_tratado.csv",
    path_demografico: str = "../../Data/Processed/municipios_idade_coordenadas.csv",
    path_municipios: str = "../../Data/Raw/municipios_br.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Carrega e inicializa todos os dados com normalização"""
    
    logger.info("=" * 60)
    logger.info("Inicializando dados demográficos...")
    logger.info("=" * 60)
    
    try:
        # 1. Carregar imóveis
        logger.info(f"Carregando imóveis: {path_imoveis}")
        df_imoveis = pd.read_csv(path_imoveis, sep=';', encoding='utf-8', low_memory=False)
        logger.info(f"✓ Imóveis carregados: {len(df_imoveis):,}")
        
        # Limpar coordenadas
        df_imoveis[['Latitude', 'Longitude']] = df_imoveis[['Latitude', 'Longitude']].apply(
            pd.to_numeric, errors='coerce'
        )
        
        mask = (
            df_imoveis['Latitude'].notna() & 
            df_imoveis['Longitude'].notna() &
            df_imoveis['Latitude'].between(-34, 6) &
            df_imoveis['Longitude'].between(-74, -34)
        )
        df_imoveis = df_imoveis[mask].copy()
        logger.info(f"✓ Imóveis válidos: {len(df_imoveis):,}")
        
        # Criar KDTree
        _cache.imoveis_coords = df_imoveis[['Latitude', 'Longitude']].values
        _cache.kdtree = cKDTree(_cache.imoveis_coords)
        _cache.df_imoveis = df_imoveis
        logger.info("✓ Índice espacial criado")
        
        # 2. Carregar dados demográficos
        logger.info(f"Carregando dados demográficos: {path_demografico}")
        df_idade = carregar_dados_demograficos(path_demografico)
        logger.info(f"✓ Municípios carregados: {len(df_idade):,}")
        _cache.df_idade = df_idade
        
        # 3. Criar índice com múltiplas variações
        logger.info("Criando índice de municípios (com e sem acentos)...")
        
        for idx, row in df_idade.iterrows():
            municipio_original = str(row['MUNICIPIO'])
            uf = str(row['sigla_uf'])
            
            dados = {
                'lat': row['latitude'],
                'lon': row['longitude'],
                'data': row,
                'nome_original': municipio_original,
                'uf': uf
            }
            
            # Chave original (com acentos)
            key_original = f"{municipio_original.upper()}_{uf}"
            _cache.municipios_dict[key_original] = dados
            
            # Chave normalizada (sem acentos)
            key_normalizada = f"{normalizar_texto(municipio_original)}_{uf}"
            _cache.municipios_dict_normalizado[key_normalizada] = dados
            
            # Variações adicionais
            variações = [
                f"{municipio_original.title()}_{uf}",
                f"{municipio_original.lower()}_{uf}",
                f"{normalizar_texto(municipio_original).title()}_{uf}",
            ]
            
            for key in variações:
                if key not in _cache.municipios_dict:
                    _cache.municipios_dict[key] = dados
        
        total_entradas = len(_cache.municipios_dict) + len(_cache.municipios_dict_normalizado)
        logger.info(f"✓ Índice criado: {total_entradas:,} entradas ({len(df_idade):,} municípios únicos)")
        
        # 4. ⭐ CORREÇÃO: Carregar lista de municípios do arquivo correto
        logger.info("Gerando lista de municípios para dropdown...")
        
        try:
            # Carregar arquivo municipios_br.csv
            df_mun = pd.read_csv(path_municipios, sep=',', encoding='utf-8')
            logger.info(f"✓ Arquivo carregado: {len(df_mun):,} registros")
            
            # ⭐ USAR COLUNAS CORRETAS: 'nome' e 'sigla_uf'
            if 'nome' in df_mun.columns and 'sigla_uf' in df_mun.columns:
                # Filtrar apenas linhas válidas (não nulas)
                df_mun_valido = df_mun[
                    df_mun['nome'].notna() & 
                    df_mun['sigla_uf'].notna()
                ].copy()
                
                # Gerar lista formatada: "Nome do Município - UF"
                lista_municipios = sorted(set([
                    f"{str(row['nome']).strip()} - {str(row['sigla_uf']).strip().upper()}" 
                    for _, row in df_mun_valido.iterrows()
                ]))
                
                logger.info(f"✓ Lista carregada de municipios_br.csv: {len(lista_municipios):,} municípios")
                
                # Mostrar exemplos
                logger.info("Exemplos de municípios:")
                for i, mun in enumerate(lista_municipios[:5], 1):
                    logger.info(f"  {i}. {mun}")
            else:
                raise ValueError(f"Colunas 'nome' ou 'sigla_uf' não encontradas. Colunas disponíveis: {df_mun.columns.tolist()}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar municipios_br.csv: {e}")
            logger.info("Gerando lista a partir dos dados demográficos...")
            
            # FALLBACK: Usar dados demográficos
            lista_municipios = sorted(set([
                f"{str(row['MUNICIPIO']).strip()} - {str(row['sigla_uf']).strip().upper()}" 
                for _, row in df_idade.iterrows()
                if pd.notna(row['MUNICIPIO']) and pd.notna(row['sigla_uf'])
            ]))
            
            logger.info(f"✓ Lista gerada dos dados demográficos: {len(lista_municipios):,} municípios")
            
            # Mostrar exemplos
            logger.info("Exemplos de municípios:")
            for i, mun in enumerate(lista_municipios[:5], 1):
                logger.info(f"  {i}. {mun}")
        
        # Validar lista final
        if len(lista_municipios) == 0:
            raise ValueError("❌ Lista de municípios está vazia!")
        
        _cache.lista_municipios = lista_municipios
        
        logger.info("=" * 60)
        logger.info("✓ DADOS CARREGADOS COM SUCESSO!")
        logger.info(f"✓ Total de municípios disponíveis: {len(lista_municipios):,}")
        logger.info("=" * 60)
        
        return df_imoveis, df_idade, lista_municipios
    
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise
def buscar_municipio(municipio_texto: str) -> Optional[Dict]:
    """
    Busca coordenadas de um município com normalização avançada
    
    Args:
        municipio_texto: String no formato "MUNICIPIO - UF"
    
    Returns:
        Dict com dados do município ou None
    """
    try:
        # Validar formato
        if ' - ' not in municipio_texto:
            logger.warning(f"Formato inválido (falta ' - '): {municipio_texto}")
            return None
        
        partes = municipio_texto.split(' - ')
        if len(partes) != 2:
            logger.warning(f"Formato inválido: {municipio_texto}")
            return None
        
        nome_municipio = partes[0].strip()
        uf = partes[1].strip().upper()
        
        # Estratégia 1: Busca direta (com acentos)
        variações_diretas = [
            f"{nome_municipio.upper()}_{uf}",
            f"{nome_municipio.title()}_{uf}",
            f"{nome_municipio.lower()}_{uf}",
        ]
        
        for key in variações_diretas:
            if key in _cache.municipios_dict:
                mun_data = _cache.municipios_dict[key]
                lat = float(mun_data['lat'])
                lon = float(mun_data['lon'])
                
                if -34 <= lat <= 6 and -74 <= lon <= -34:
                    logger.info(f"✓ Município encontrado (busca direta): {nome_municipio} - {uf}")
                    return {
                        'lat': lat,
                        'lon': lon,
                        'nome': mun_data['nome_original'],
                        'uf': uf,
                        'data': mun_data['data']
                    }
        
        # Estratégia 2: Busca normalizada (sem acentos)
        nome_normalizado = normalizar_texto(nome_municipio)
        key_normalizada = f"{nome_normalizado}_{uf}"
        
        if key_normalizada in _cache.municipios_dict_normalizado:
            mun_data = _cache.municipios_dict_normalizado[key_normalizada]
            lat = float(mun_data['lat'])
            lon = float(mun_data['lon'])
            
            if -34 <= lat <= 6 and -74 <= lon <= -34:
                logger.info(f"✓ Município encontrado (busca normalizada): {mun_data['nome_original']} - {uf}")
                return {
                    'lat': lat,
                    'lon': lon,
                    'nome': mun_data['nome_original'],
                    'uf': uf,
                    'data': mun_data['data']
                }
        
        # Estratégia 3: Busca no DataFrame (fuzzy)
        if _cache.df_idade is not None:
            logger.info(f"Tentando busca fuzzy no DataFrame para: {nome_municipio}")
            
            # Busca case-insensitive e sem acentos
            mask = (
                _cache.df_idade['MUNICIPIO'].apply(normalizar_texto).str.contains(nome_normalizado, na=False) &
                (_cache.df_idade['sigla_uf'].str.upper() == uf)
            )
            
            df_resultado = _cache.df_idade[mask]
            
            if len(df_resultado) > 0:
                row = df_resultado.iloc[0]
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                
                logger.info(f"✓ Município encontrado (busca fuzzy): {row['MUNICIPIO']} - {row['sigla_uf']}")
                
                return {
                    'lat': lat,
                    'lon': lon,
                    'nome': row['MUNICIPIO'],
                    'uf': row['sigla_uf'],
                    'data': row
                }
        
        # Não encontrado
        logger.error(f"❌ Município NÃO encontrado: {municipio_texto}")
        logger.info(f"   Tentativas: {variações_diretas + [key_normalizada]}")
        
        # Sugestões
        if _cache.df_idade is not None:
            sugestoes = _cache.df_idade[
                _cache.df_idade['sigla_uf'].str.upper() == uf
            ]['MUNICIPIO'].head(5).tolist()
            logger.info(f"   Municípios disponíveis em {uf}: {', '.join(sugestoes)}")
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar município '{municipio_texto}': {e}")
        import traceback
        traceback.print_exc()
        return None


def obter_lista_municipios() -> List[str]:
    """Retorna lista de municípios disponíveis"""
    if not _cache.lista_municipios:
        logger.warning("⚠️ Execute inicializar_dados() primeiro")
        return []
    return _cache.lista_municipios


def obter_faixas_etarias_disponiveis() -> List[str]:
    """Retorna lista de faixas etárias disponíveis"""
    return get_faixas_disponiveis()


def calcular_distancias_vetorizado(lat_centro, lon_centro, df_coords):
    """Cálculo vetorizado de distâncias Haversine"""
    R = 6371
    lat1 = np.radians(lat_centro)
    lon1 = np.radians(lon_centro)
    lat2 = np.radians(df_coords['Latitude'].values)
    lon2 = np.radians(df_coords['Longitude'].values)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c


def filtrar_imoveis_por_raio(lat_centro, lon_centro, raio_km):
    """Filtra imóveis dentro de um raio"""
    if _cache.kdtree is None:
        raise ValueError("Execute inicializar_dados() primeiro")
    
    raio_graus = raio_km / 111.0
    indices = _cache.kdtree.query_ball_point([lat_centro, lon_centro], raio_graus)
    
    if len(indices) == 0:
        logger.warning(f"Nenhum imóvel encontrado em {raio_km}km")
        return pd.DataFrame()
    
    df_resultado = _cache.df_imoveis.iloc[indices].copy()
    df_resultado['distancia_municipio'] = calcular_distancias_vetorizado(
        lat_centro, lon_centro, df_resultado
    )
    df_resultado = df_resultado[df_resultado['distancia_municipio'] <= raio_km]
    
    logger.info(f"✓ {len(df_resultado):,} imóveis encontrados")
    return df_resultado


def processar_analise_demografica(municipio_texto, raio_km, faixas_etarias=None, usar_filtro_idade=False):
    """Processa análise demográfica completa"""
    
    logger.info(f"Processando análise: {municipio_texto}, raio={raio_km}km")
    
    municipio_coords = buscar_municipio(municipio_texto)
    if not municipio_coords:
        raise ValueError(f"Município não encontrado: {municipio_texto}")
    
    df_imoveis = filtrar_imoveis_por_raio(
        municipio_coords['lat'],
        municipio_coords['lon'],
        raio_km
    )
    
    if len(df_imoveis) == 0:
        raise ValueError(f"Nenhum imóvel encontrado em {raio_km}km de {municipio_texto}")
    
    if usar_filtro_idade and faixas_etarias:
        logger.info(f"Aplicando filtro demográfico: {len(faixas_etarias)} faixas")
        df_idade_filtrado = filtrar_multiplas_faixas(_cache.df_idade, faixas_etarias)
        df_resultado = encontrar_municipios_proximos(df_imoveis, df_idade_filtrado, raio_km)
        df_resultado = calcular_score_demografico(df_resultado)
        df_resultado = df_resultado.sort_values('score_demografico', ascending=False)
    else:
        df_resultado = df_imoveis.copy()
        df_resultado['score_demografico'] = np.nan
        df_resultado['populacao_faixa'] = 0
    
    logger.info(f"✓ Análise concluída: {len(df_resultado)} registros")
    return df_resultado


def gerar_mapa_demografico(df_filtrado, municipio_texto, raio_km, usar_filtro_idade=False, altura=900):
    """Gera mapa HTML"""
    
    if df_filtrado is None or len(df_filtrado) == 0:
        return "<div style='text-align: center; padding: 50px; color: #999;'>Nenhum dado disponível</div>"
    
    # Preparar dados
    df_map = df_filtrado.copy()
    
    if 'imovel_lat' in df_map.columns:
        df_map['Latitude'] = pd.to_numeric(df_map['imovel_lat'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['imovel_lon'], errors='coerce')
    
    df_map = df_map.dropna(subset=['Latitude', 'Longitude'])
    
    if len(df_map) == 0:
        return "<div style='text-align: center; padding: 50px; color: #999;'>Sem coordenadas válidas</div>"
    
    # Criar mapa
    fig = go.Figure()
    
    if usar_filtro_idade and 'score_demografico' in df_map.columns:
        df_map['score_demografico'] = pd.to_numeric(df_map['score_demografico'], errors='coerce')
        df_validos = df_map[df_map['score_demografico'].notna()].copy()
        
        if len(df_validos) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=df_validos['Latitude'],
                lon=df_validos['Longitude'],
                mode='markers',
                marker=dict(
                    size=12,
                    color=df_validos['score_demografico'],
                    colorscale='Greens',
                    opacity=0.7,
                    showscale=True,
                    colorbar=dict(title="Score")
                ),
                text=[f"Score: {s:.3f}" for s in df_validos['score_demografico']],
                hoverinfo='text',
                name='Imóveis'
            ))
    else:
        fig.add_trace(go.Scattermapbox(
            lat=df_map['Latitude'],
            lon=df_map['Longitude'],
            mode='markers',
            marker=dict(size=8, color='#22c55e', opacity=0.6),
            hoverinfo='skip',
            name='Imóveis'
        ))
    
    # Adicionar município central
    municipio_coords = buscar_municipio(municipio_texto)
    if municipio_coords:
        fig.add_trace(go.Scattermapbox(
            lat=[municipio_coords['lat']],
            lon=[municipio_coords['lon']],
            mode='markers+text',
            marker=dict(size=25, color='#ef4444', symbol='star'),
            text=[municipio_coords['nome']],
            textposition='top center',
            textfont=dict(size=12, color='#1f2937'),
            hovertext=f"<b>{municipio_coords['nome']} - {municipio_coords['uf']}</b>",
            hoverinfo='text',
            name='Município'
        ))
    
    # Layout
    lat_centro = df_map['Latitude'].mean()
    lon_centro = df_map['Longitude'].mean()
    
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=lat_centro, lon=lon_centro),
            zoom=9
        ),
        height=altura,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='mapa-demografico')


def analise_demografica_completa(municipio, raio_km=50, faixas_etarias=None, usar_filtro_idade=False, altura_mapa=900):
    """Função principal para dashboard"""
    
    try:
        logger.info("="*60)
        logger.info(f"ANÁLISE DEMOGRÁFICA: {municipio}")
        logger.info("="*60)
        
        df_resultado = processar_analise_demografica(
            municipio, raio_km, faixas_etarias, usar_filtro_idade
        )
        
        mapa_html = gerar_mapa_demografico(
            df_resultado, municipio, raio_km, usar_filtro_idade, altura_mapa
        )
        
        estatisticas = {
            'total_imoveis': len(df_resultado),
            'score_medio': float(df_resultado.get('score_demografico', pd.Series([0])).mean()),
            'score_max': float(df_resultado.get('score_demografico', pd.Series([0])).max()),
            'populacao_total': int(df_resultado.get('populacao_faixa', pd.Series([0])).sum())
        }
        
        logger.info(f"✓ Análise concluída com sucesso!")
        logger.info(f"  Imóveis: {estatisticas['total_imoveis']:,}")
        logger.info("="*60)
        
        return {
            'sucesso': True,
            'mensagem': f'{len(df_resultado):,} imóveis encontrados',
            'mapa_html': mapa_html,
            'df_resultado': df_resultado,
            'estatisticas': estatisticas
        }
    
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': str(e),
            'mapa_html': f"<div style='text-align: center; padding: 50px; color: #ef4444;'><h3>❌ Erro</h3><p>{str(e)}</p></div>",
            'df_resultado': pd.DataFrame(),
            'estatisticas': {'total_imoveis': 0, 'score_medio': 0, 'score_max': 0, 'populacao_total': 0}
        }


def funcmapa(municipio="Campinas - SP", raio_km=50, faixas_etarias=None, usar_filtro_idade=False, altura_mapa=900, return_html=True):
    """Função simplificada para uso direto"""
    resultado = analise_demografica_completa(municipio, raio_km, faixas_etarias, usar_filtro_idade, altura_mapa)
    return resultado['mapa_html'] if return_html else resultado


# Exportar funções
__all__ = [
    'inicializar_dados',
    'obter_lista_municipios',
    'obter_faixas_etarias_disponiveis',
    'analise_demografica_completa',
    'funcmapa',
    'buscar_municipio',
    'processar_analise_demografica',
    'gerar_mapa_demografico',
    'normalizar_texto'
]