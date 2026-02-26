# analise_demografica_dashboard.py

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import cKDTree
import logging
from typing import Optional, Dict, List, Tuple

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

# ==================== Configuração de Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==================== Cache Global ====================
class DataCache:
    """Cache para evitar recálculos"""
    def __init__(self):
        self.kdtree = None
        self.imoveis_coords = None
        self.municipios_dict = {}
        self.df_imoveis = None
        self.df_idade = None
        self.lista_municipios = []

_cache = DataCache()


# ==================== Funções de Carregamento ====================
def inicializar_dados(
    path_imoveis: str = "../../Data/Processed/imovel_tratado.csv",
    path_demografico: str = "../../Data/Processed/municipios_idade_coordenadas.csv",
    path_municipios: str = "../../Data/Processed/municipios_br.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Carrega e inicializa todos os dados necessários
    
    Args:
        path_imoveis: Caminho do arquivo de imóveis
        path_demografico: Caminho do arquivo demográfico
        path_municipios: Caminho do arquivo de municípios
    
    Returns:
        Tuple com (df_imoveis, df_idade, lista_municipios)
    """
    logger.info("Carregando dados...")
    
    try:
        # Carregar imóveis
        df_imoveis = pd.read_csv(
            path_imoveis, 
            sep=';', 
            encoding='utf-8',
            low_memory=False
        )
        logger.info(f"Imóveis carregados: {len(df_imoveis):,}")
        
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
        logger.info(f"Imóveis válidos: {len(df_imoveis):,}")
        
        # Criar KDTree
        _cache.imoveis_coords = df_imoveis[['Latitude', 'Longitude']].values
        _cache.kdtree = cKDTree(_cache.imoveis_coords)
        _cache.df_imoveis = df_imoveis
        
        # Carregar dados demográficos
        df_idade = carregar_dados_demograficos(path_demografico)
        logger.info(f"Municípios carregados: {len(df_idade):,}")
        _cache.df_idade = df_idade
        
        # Criar índice de municípios
        for idx, row in df_idade.iterrows():
            key = f"{row['MUNICIPIO'].upper()}_{row['sigla_uf']}"
            _cache.municipios_dict[key] = {
                'lat': row['latitude'],
                'lon': row['longitude'],
                'data': row
            }
        
        # Carregar lista de municípios
        try:
            df_municipios_br = pd.read_csv(
                path_municipios,
                sep=',',
                encoding='utf-8',
                usecols=['MUNICIPIO', 'sigla_uf']
            )
            lista_municipios = sorted([
                f"{row['MUNICIPIO']} - {row['sigla_uf']}" 
                for _, row in df_municipios_br.iterrows()
            ])
        except Exception as e:
            logger.warning(f"Usando dados demográficos para lista de municípios: {e}")
            lista_municipios = sorted([
                f"{row['MUNICIPIO']} - {row['sigla_uf']}" 
                for _, row in df_idade.iterrows()
            ])
        
        _cache.lista_municipios = lista_municipios
        
        logger.info("✓ Dados carregados com sucesso!")
        return df_imoveis, df_idade, lista_municipios
    
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        raise


# ==================== Funções de Busca ====================
def buscar_municipio(municipio_texto: str) -> Optional[Dict]:
    """
    Busca coordenadas e dados de um município
    
    Args:
        municipio_texto: String no formato "MUNICIPIO - UF"
    
    Returns:
        Dict com dados do município ou None
    """
    try:
        nome_municipio = municipio_texto.split(' - ')[0]
        uf = municipio_texto.split(' - ')[1]
        
        key = f"{nome_municipio.upper()}_{uf}"
        
        if key in _cache.municipios_dict:
            mun_data = _cache.municipios_dict[key]
            lat = float(mun_data['lat'])
            lon = float(mun_data['lon'])
            
            if not (-34 <= lat <= 6 and -74 <= lon <= -34):
                logger.warning(f"Coordenadas inválidas: {nome_municipio}")
                return None
            
            return {
                'lat': lat,
                'lon': lon,
                'nome': nome_municipio,
                'uf': uf,
                'data': mun_data['data']
            }
    except Exception as e:
        logger.error(f"Erro ao buscar município: {e}")
    
    return None


# ==================== Funções de Filtro ====================
def calcular_distancias_vetorizado(
    lat_centro: float, 
    lon_centro: float, 
    df_coords: pd.DataFrame
) -> np.ndarray:
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


def filtrar_imoveis_por_raio(
    lat_centro: float, 
    lon_centro: float, 
    raio_km: float
) -> pd.DataFrame:
    """
    Filtra imóveis dentro de um raio
    
    Args:
        lat_centro: Latitude do centro
        lon_centro: Longitude do centro
        raio_km: Raio em km
    
    Returns:
        DataFrame filtrado
    """
    logger.info(f"Filtrando imóveis em raio de {raio_km}km...")
    
    if _cache.kdtree is None or _cache.df_imoveis is None:
        raise ValueError("Dados não inicializados. Execute inicializar_dados() primeiro.")
    
    raio_graus = raio_km / 111.0
    indices = _cache.kdtree.query_ball_point([lat_centro, lon_centro], raio_graus)
    
    if len(indices) == 0:
        return pd.DataFrame()
    
    df_resultado = _cache.df_imoveis.iloc[indices].copy()
    df_resultado['distancia_municipio'] = calcular_distancias_vetorizado(
        lat_centro, lon_centro, df_resultado
    )
    df_resultado = df_resultado[df_resultado['distancia_municipio'] <= raio_km]
    
    logger.info(f"Encontrados {len(df_resultado):,} imóveis")
    return df_resultado


# ==================== Análise Demográfica ====================
def processar_analise_demografica(
    municipio_texto: str,
    raio_km: float,
    faixas_etarias: Optional[List[str]] = None,
    usar_filtro_idade: bool = False
) -> pd.DataFrame:
    """
    Processa análise demográfica completa
    
    Args:
        municipio_texto: Município no formato "NOME - UF"
        raio_km: Raio de busca em km
        faixas_etarias: Lista de faixas etárias para filtrar
        usar_filtro_idade: Se True, aplica filtro demográfico
    
    Returns:
        DataFrame com resultados
    """
    logger.info("="*60)
    logger.info("INICIANDO ANÁLISE DEMOGRÁFICA")
    logger.info("="*60)
    
    # 1. Buscar município
    municipio_coords = buscar_municipio(municipio_texto)
    if not municipio_coords:
        raise ValueError(f"Município não encontrado: {municipio_texto}")
    
    logger.info(f"Município: {municipio_coords['nome']} - {municipio_coords['uf']}")
    logger.info(f"Coordenadas: Lat={municipio_coords['lat']:.4f}, Lon={municipio_coords['lon']:.4f}")
    logger.info(f"Raio: {raio_km}km")
    
    # 2. Filtrar imóveis por raio
    df_imoveis_filtrado = filtrar_imoveis_por_raio(
        municipio_coords['lat'],
        municipio_coords['lon'],
        raio_km
    )
    
    if len(df_imoveis_filtrado) == 0:
        raise ValueError(f"Nenhum imóvel encontrado em {raio_km}km de {municipio_texto}")
    
    # 3. Aplicar filtro demográfico (se solicitado)
    if usar_filtro_idade and faixas_etarias:
        logger.info(f"Aplicando filtro demográfico: {len(faixas_etarias)} faixas")
        
        if not validar_faixas_etarias(faixas_etarias):
            raise ValueError("Faixas etárias inválidas")
        
        # Filtrar municípios por faixa etária
        df_idade_filtrado = filtrar_multiplas_faixas(_cache.df_idade, faixas_etarias)
        
        if len(df_idade_filtrado) == 0:
            raise ValueError("Nenhum município encontrado com as faixas etárias selecionadas")
        
        # Encontrar municípios próximos
        df_resultado = encontrar_municipios_proximos(
            df_imoveis_filtrado,
            df_idade_filtrado,
            raio_km=raio_km
        )
        
        if len(df_resultado) == 0:
            raise ValueError("Nenhuma correspondência encontrada")
        
        # Calcular scores
        df_resultado = calcular_score_demografico(df_resultado)
        df_resultado = df_resultado.sort_values('score_demografico', ascending=False)
        
        logger.info(f"✓ Análise concluída: {len(df_resultado)} registros com score")
    
    else:
        # Sem filtro demográfico
        df_resultado = df_imoveis_filtrado.copy()
        df_resultado['score_demografico'] = np.nan
        df_resultado['populacao_faixa'] = 0
        
        logger.info(f"✓ Análise concluída: {len(df_resultado)} imóveis")
    
    return df_resultado


# ==================== Geração de Mapa ====================
def _preparar_dataframe_mapa(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """Prepara DataFrame para visualização"""
    df_map = df_filtrado.copy()
    
    # Corrigir coordenadas
    if 'imovel_lat' in df_map.columns:
        df_map['Latitude'] = pd.to_numeric(df_map['imovel_lat'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['imovel_lon'], errors='coerce')
    else:
        df_map['Latitude'] = pd.to_numeric(df_map['Latitude'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['Longitude'], errors='coerce')
    
    # Validar
    df_map = df_map.dropna(subset=['Latitude', 'Longitude'])
    df_map = df_map[
        (df_map['Latitude'].between(-34, 6)) &
        (df_map['Longitude'].between(-74, -34))
    ]
    
    # Preparar colunas
    df_map['municipio_nome'] = df_map.get('municipio', df_map.get('Cidade', 'N/A'))
    df_map['uf_nome'] = df_map.get('uf', df_map.get('Estado', ''))
    df_map['municipio_completo'] = df_map['municipio_nome'].astype(str) + ' - ' + df_map['uf_nome'].astype(str)
    
    if 'distancia_km' in df_map.columns:
        df_map['distancia'] = df_map['distancia_km']
    elif 'distancia_municipio' in df_map.columns:
        df_map['distancia'] = df_map['distancia_municipio']
    else:
        df_map['distancia'] = 0
    
    return df_map


def gerar_mapa_demografico(
    df_filtrado: pd.DataFrame,
    municipio_texto: str,
    raio_km: float,
    usar_filtro_idade: bool = False,
    altura: int = 900
) -> str:
    """
    Gera mapa HTML da análise demográfica
    
    Args:
        df_filtrado: DataFrame com resultados
        municipio_texto: Município consultado
        raio_km: Raio de busca
        usar_filtro_idade: Se usa score demográfico
        altura: Altura do mapa em pixels
    
    Returns:
        String HTML do mapa
    """
    if df_filtrado is None or len(df_filtrado) == 0:
        return "<div style='text-align: center; padding: 50px;'>Nenhum dado disponível</div>"
    
    # Buscar coordenadas do município
    municipio_coords = buscar_municipio(municipio_texto)
    
    # Preparar dados
    df_map = _preparar_dataframe_mapa(df_filtrado)
    
    if len(df_map) == 0:
        return "<div style='text-align: center; padding: 50px;'>Nenhuma coordenada válida</div>"
    
    # Calcular bounds
    if municipio_coords:
        lat_centro = municipio_coords['lat']
        lon_centro = municipio_coords['lon']
        
        delta_lat = (raio_km / 111.0) * 1.05
        delta_lon = (raio_km / (111.0 * np.cos(np.radians(lat_centro)))) * 1.05
        
        lat_min = lat_centro - delta_lat
        lat_max = lat_centro + delta_lat
        lon_min = lon_centro - delta_lon
        lon_max = lon_centro + delta_lon
    else:
        lat_min = df_map['Latitude'].min()
        lat_max = df_map['Latitude'].max()
        lon_min = df_map['Longitude'].min()
        lon_max = df_map['Longitude'].max()
        
        margin = 0.05
        lat_min -= (lat_max - lat_min) * margin
        lat_max += (lat_max - lat_min) * margin
        lon_min -= (lon_max - lon_min) * margin
        lon_max += (lon_max - lon_min) * margin
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar imóveis
    if usar_filtro_idade and 'score_demografico' in df_map.columns:
        df_map['score_demografico'] = pd.to_numeric(df_map['score_demografico'], errors='coerce')
        df_map_validos = df_map[df_map['score_demografico'].notna()].copy()
        
        if len(df_map_validos) > 0:
            score_min = df_map_validos['score_demografico'].min()
            score_max = df_map_validos['score_demografico'].max()
            
            if score_max > score_min:
                df_map_validos['tamanho'] = 8 + (df_map_validos['score_demografico'] - score_min) / (score_max - score_min) * 17
            else:
                df_map_validos['tamanho'] = 15
            
            hover_text = [
                f"<b>{row['municipio_completo']}</b><br>"
                f"Score: {row['score_demografico']:.3f}<br>"
                f"População: {row.get('populacao_faixa', 0):,.0f}<br>"
                f"Distância: {row['distancia']:.1f} km"
                for _, row in df_map_validos.iterrows()
            ]
            
            fig.add_trace(go.Scattermapbox(
                lat=df_map_validos['Latitude'],
                lon=df_map_validos['Longitude'],
                mode='markers',
                marker=dict(
                    size=df_map_validos['tamanho'],
                    color=df_map_validos['score_demografico'],
                    colorscale=[[0, '#86efac'], [0.5, '#22c55e'], [1, '#15803d']],
                    opacity=0.8,
                    showscale=False
                ),
                text=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
    else:
        hover_text = [
            f"<b>{row['municipio_completo']}</b><br>Distância: {row['distancia']:.1f} km"
            for _, row in df_map.iterrows()
        ]
        
        fig.add_trace(go.Scattermapbox(
            lat=df_map['Latitude'],
            lon=df_map['Longitude'],
            mode='markers',
            marker=dict(size=10, color='#22c55e', opacity=0.7),
            text=hover_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    # Adicionar marcador do município
    if municipio_coords:
        fig.add_trace(go.Scattermapbox(
            lat=[municipio_coords['lat']],
            lon=[municipio_coords['lon']],
            mode='markers+text',
            marker=dict(size=30, color='#ef4444', symbol='star', opacity=1.0),
            text=[municipio_coords['nome']],
            textposition="top center",
            textfont=dict(size=14, color='#1f2937', family='Arial Black'),
            hovertext=f"<b>MUNICÍPIO CONSULTADO</b><br>{municipio_coords['nome']} - {municipio_coords['uf']}",
            hoverinfo='text',
            showlegend=False
        ))
    
    # Layout
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=(lat_min + lat_max) / 2, lon=(lon_min + lon_max) / 2),
            zoom=8
        ),
        height=altura,
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial")
    )
    
    # Converter para HTML
    html_string = fig.to_html(
        include_plotlyjs='cdn',
        div_id='mapa-demografico',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'responsive': True
        }
    )
    
    return html_string


# ==================== Função Principal para Dashboard ====================
def analise_demografica_completa(
    municipio: str,
    raio_km: float = 50,
    faixas_etarias: Optional[List[str]] = None,
    usar_filtro_idade: bool = False,
    altura_mapa: int = 900
) -> Dict:
    """
    Função principal para integração com dashboard
    
    Args:
        municipio: Município no formato "NOME - UF"
        raio_km: Raio de busca em km
        faixas_etarias: Lista de faixas etárias (ex: ["18 a 29 anos", "30 a 39 anos"])
        usar_filtro_idade: Se True, aplica filtro demográfico
        altura_mapa: Altura do mapa em pixels
    
    Returns:
        Dict com:
            - 'mapa_html': HTML do mapa
            - 'df_resultado': DataFrame com resultados
            - 'estatisticas': Dict com estatísticas
            - 'sucesso': Boolean indicando sucesso
            - 'mensagem': Mensagem de status
    """
    try:
        # Processar análise
        df_resultado = processar_analise_demografica(
            municipio_texto=municipio,
            raio_km=raio_km,
            faixas_etarias=faixas_etarias,
            usar_filtro_idade=usar_filtro_idade
        )
        
        # Gerar mapa
        mapa_html = gerar_mapa_demografico(
            df_filtrado=df_resultado,
            municipio_texto=municipio,
            raio_km=raio_km,
            usar_filtro_idade=usar_filtro_idade,
            altura=altura_mapa
        )
        
        # Calcular estatísticas
        estatisticas = {
            'total_imoveis': len(df_resultado),
            'score_medio': df_resultado.get('score_demografico', pd.Series([0])).mean(),
            'score_max': df_resultado.get('score_demografico', pd.Series([0])).max(),
            'populacao_total': df_resultado.get('populacao_faixa', pd.Series([0])).sum()
        }
        
        return {
            'sucesso': True,
            'mensagem': f'Análise concluída: {len(df_resultado)} imóveis encontrados',
            'mapa_html': mapa_html,
            'df_resultado': df_resultado,
            'estatisticas': estatisticas
        }
    
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        return {
            'sucesso': False,
            'mensagem': str(e),
            'mapa_html': f"<div style='text-align: center; padding: 50px; color: #e53e3e;'>Erro: {str(e)}</div>",
            'df_resultado': pd.DataFrame(),
            'estatisticas': {}
        }


# ==================== Funções Auxiliares ====================
def obter_faixas_etarias_disponiveis() -> List[str]:
    """Retorna lista de faixas etárias disponíveis"""
    return get_faixas_disponiveis()


def obter_lista_municipios() -> List[str]:
    """Retorna lista de municípios disponíveis"""
    return _cache.lista_municipios


def exportar_csv(df: pd.DataFrame, nome_arquivo: str = "analise_demografica.csv"):
    """
    Exporta DataFrame para CSV
    
    Args:
        df: DataFrame para exportar
        nome_arquivo: Nome do arquivo
    """
    df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8')
    logger.info(f"✓ Arquivo exportado: {nome_arquivo}")