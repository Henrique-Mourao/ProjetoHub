

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from IPython.display import display, HTML, clear_output
import ipywidgets as widgets
import time
import logging
from scipy.spatial import cKDTree
import base64
from io import BytesIO

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

# ==================== Cache ====================
class DataCache:
    """Cache para evitar recálculos"""
    def __init__(self):
        self.kdtree = None
        self.imoveis_coords = None
        self.municipios_dict = {}

class AnalysisCache:
    """Cache de resultados de análise"""
    def __init__(self, max_size=50):
        self.cache = {}
        self.max_size = max_size
    
    def get_key(self, municipio, raio, faixas):
        """Gera chave única para cache"""
        faixas_str = ','.join(sorted(faixas)) if faixas else 'all'
        return f"{municipio}_{raio}_{faixas_str}"
    
    def get(self, key):
        """Recupera resultado do cache"""
        return self.cache.get(key)
    
    def set(self, key, value):
        """Armazena resultado no cache"""
        if len(self.cache) >= self.max_size:
            # Remove o item mais antigo
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value
    
    def clear(self):
        """Limpa o cache"""
        self.cache.clear()

cache = DataCache()
analysis_cache = AnalysisCache()

# ==================== Carregamento de Dados ====================
def carregar_dados():
    """Carregamento otimizado com índices"""
    logger.info("Carregando dados...")
    
    try:
        df_imoveis = pd.read_csv(
            "../../Data/Processed/imovel_tratado.csv", 
            sep=';', 
            encoding='utf-8',
            low_memory=False
        )
        logger.info(f"Imóveis carregados: {len(df_imoveis):,}")
        
        # Conversão e limpeza
        df_imoveis[['Latitude', 'Longitude']] = df_imoveis[['Latitude', 'Longitude']].apply(
            pd.to_numeric, errors='coerce'
        )
        
        # Filtro vetorizado
        mask = (
            df_imoveis['Latitude'].notna() & 
            df_imoveis['Longitude'].notna() &
            df_imoveis['Latitude'].between(-34, 6) &
            df_imoveis['Longitude'].between(-74, -34)
        )
        df_imoveis = df_imoveis[mask].copy()
        logger.info(f"Imóveis com coordenadas válidas: {len(df_imoveis):,}")
        
        # Criar KDTree
        cache.imoveis_coords = df_imoveis[['Latitude', 'Longitude']].values
        cache.kdtree = cKDTree(cache.imoveis_coords)
        
        df_idade = carregar_dados_demograficos(
            "../../Data/Processed/municipios_idade_coordenadas.csv"
        )
        logger.info(f"Municípios carregados: {len(df_idade):,}")
        
        # Criar índice de municípios
        for idx, row in df_idade.iterrows():
            key = f"{row['MUNICIPIO'].upper()}_{row['sigla_uf']}"
            cache.municipios_dict[key] = {
                'lat': row['latitude'],
                'lon': row['longitude'],
                'data': row
            }
        
        try:
            df_municipios_br = pd.read_csv(
                "../../Data/Processed/municipios_br.csv",
                sep=',',
                encoding='utf-8',
                usecols=['MUNICIPIO', 'sigla_uf']
            )
            lista_municipios = sorted([
                f"{row['MUNICIPIO']} - {row['sigla_uf']}" 
                for _, row in df_municipios_br.iterrows()
            ])
        except Exception as e:
            logger.warning(f"Erro ao carregar municipios_br.csv: {e}. Usando dados demográficos.")
            lista_municipios = sorted([
                f"{row['MUNICIPIO']} - {row['sigla_uf']}" 
                for _, row in df_idade.iterrows()
            ])
        
        return df_imoveis, df_idade, lista_municipios
    
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        raise


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


def filtrar_imoveis_por_raio_otimizado(df_imoveis, lat_centro, lon_centro, raio_km):
    """Filtragem otimizada usando KDTree"""
    logger.info(f"Filtrando imóveis em raio de {raio_km}km...")
    
    if cache.kdtree is None:
        distancias = calcular_distancias_vetorizado(lat_centro, lon_centro, df_imoveis)
        mask = distancias <= raio_km
        df_resultado = df_imoveis[mask].copy()
        df_resultado['distancia_municipio'] = distancias[mask]
        return df_resultado
    
    raio_graus = raio_km / 111.0
    indices = cache.kdtree.query_ball_point([lat_centro, lon_centro], raio_graus)
    
    if len(indices) == 0:
        return pd.DataFrame()
    
    df_resultado = df_imoveis.iloc[indices].copy()
    df_resultado['distancia_municipio'] = calcular_distancias_vetorizado(
        lat_centro, lon_centro, df_resultado
    )
    df_resultado = df_resultado[df_resultado['distancia_municipio'] <= raio_km]
    
    logger.info(f"Encontrados {len(df_resultado):,} imóveis no raio")
    return df_resultado


def buscar_municipio_otimizado(municipio_texto):
    """Busca otimizada com validação de coordenadas"""
    try:
        nome_municipio = municipio_texto.split(' - ')[0]
        uf = municipio_texto.split(' - ')[1]
        
        key = f"{nome_municipio.upper()}_{uf}"
        
        if key in cache.municipios_dict:
            mun_data = cache.municipios_dict[key]
            lat = float(mun_data['lat'])
            lon = float(mun_data['lon'])
            
            # Validar se está no Brasil
            if not (-34 <= lat <= 6 and -74 <= lon <= -34):
                logger.warning(f"Coordenadas inválidas para {nome_municipio}: Lat={lat}, Lon={lon}")
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


# ==================== Funções de Visualização ====================
def _preparar_dataframe_mapa(df_filtrado):
    """Prepara dataframe para visualização no mapa"""
    df_map = df_filtrado.copy()
    
    # Corrigir coordenadas
    if 'imovel_lat' in df_map.columns and 'imovel_lon' in df_map.columns:
        df_map['Latitude'] = pd.to_numeric(df_map['imovel_lat'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['imovel_lon'], errors='coerce')
    else:
        df_map['Latitude'] = pd.to_numeric(df_map['Latitude'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['Longitude'], errors='coerce')
    
    # Remover NaN e validar Brasil
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


def _calcular_bounds_mapa(df_map, municipio_coords, municipio_selecionado, raio_km_value):
    """Calcula bounds do mapa"""
    if municipio_coords and municipio_selecionado:
        lat_centro = municipio_coords['lat']
        lon_centro = municipio_coords['lon']
        
        # Margem de 5%
        delta_lat = (raio_km_value / 111.0) * 1.05
        delta_lon = (raio_km_value / (111.0 * np.cos(np.radians(lat_centro)))) * 1.05
        
        lat_min = lat_centro - delta_lat
        lat_max = lat_centro + delta_lat
        lon_min = lon_centro - delta_lon
        lon_max = lon_centro + delta_lon
        
        logger.info(f"Mapa centralizado em: {municipio_selecionado}")
        logger.info(f"Centro: Lat={lat_centro:.6f}, Lon={lon_centro:.6f}")
        logger.info(f"Raio: {raio_km_value}km (margem: 5%)")
    else:
        lat_min = df_map['Latitude'].min()
        lat_max = df_map['Latitude'].max()
        lon_min = df_map['Longitude'].min()
        lon_max = df_map['Longitude'].max()
        
        lat_margin = (lat_max - lat_min) * 0.05
        lon_margin = (lon_max - lon_min) * 0.05
        
        lat_min -= lat_margin
        lat_max += lat_margin
        lon_min -= lon_margin
        lon_max += lon_margin
    
    logger.info(f"Bounds: Lat[{lat_min:.4f}, {lat_max:.4f}] Lon[{lon_min:.4f}, {lon_max:.4f}]")
    
    return lat_min, lat_max, lon_min, lon_max


def _criar_figura_mapa(df_map, municipio_coords, municipio_selecionado, raio_km_value, usar_filtro_idade=False):
    """
    Função auxiliar para criar figura do mapa (DRY principle)
    
    Args:
        df_map: DataFrame preparado com coordenadas
        municipio_coords: Coordenadas do município consultado
        municipio_selecionado: Nome do município
        raio_km_value: Raio de busca em km
        usar_filtro_idade: Se True, usa score demográfico
    
    Returns:
        go.Figure: Figura Plotly do mapa
    """
    # Calcular bounds
    lat_min, lat_max, lon_min, lon_max = _calcular_bounds_mapa(
        df_map, municipio_coords, municipio_selecionado, raio_km_value
    )
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar imóveis
    if usar_filtro_idade and 'score_demografico' in df_map.columns:
        df_map['score_demografico'] = pd.to_numeric(df_map['score_demografico'], errors='coerce')
        
        if 'populacao_faixa' not in df_map.columns:
            df_map['populacao_faixa'] = 0
        
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
                f"População: {row['populacao_faixa']:,.0f}<br>"
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
        
        df_map_sem_score = df_map[df_map['score_demografico'].isna()]
        if len(df_map_sem_score) > 0:
            hover_text_sem = [
                f"<b>{row['municipio_completo']}</b><br>Distância: {row['distancia']:.1f} km"
                for _, row in df_map_sem_score.iterrows()
            ]
            
            fig.add_trace(go.Scattermapbox(
                lat=df_map_sem_score['Latitude'],
                lon=df_map_sem_score['Longitude'],
                mode='markers',
                marker=dict(size=8, color='#d1d5db', opacity=0.4),
                text=hover_text_sem,
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
    if municipio_coords and municipio_selecionado:
        nome_mun = municipio_coords['nome']
        uf_mun = municipio_coords['uf']
        
        fig.add_trace(go.Scattermapbox(
            lat=[municipio_coords['lat']],
            lon=[municipio_coords['lon']],
            mode='markers+text',
            marker=dict(
                size=30,
                color='#ef4444',
                symbol='star',
                opacity=1.0
            ),
            text=[f"{nome_mun}"],
            textposition="top center",
            textfont=dict(
                size=14,
                color='#1f2937',
                family='Arial Black'
            ),
            hovertext=f"<b>MUNICÍPIO CONSULTADO</b><br>{nome_mun} - {uf_mun}<br>Raio de busca: {raio_km_value}km",
            hoverinfo='text',
            showlegend=False,
            name='Município Consultado'
        ))
        
        logger.info(f"Marcador adicionado em: {nome_mun} - {uf_mun}")
    
    # Layout
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            style="open-street-map",
            center=dict(
                lat=(lat_min + lat_max) / 2,
                lon=(lon_min + lon_max) / 2
            ),
            zoom=8
        ),
        height=900,
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial")
    )
    
    return fig


def gerar_mapa_plotly_otimizado():
    """Geração do mapa para exibição no notebook"""
    global df_filtrado, municipio_coords, municipio_selecionado
    
    if df_filtrado is None or len(df_filtrado) == 0:
        with output_visualizacao:
            output_visualizacao.clear_output()
            display(HTML("<div style='text-align: center; padding: 20px; color: #e53e3e;'>Nenhum dado para exibir</div>"))
        return
    
    # Preparar dataframe
    df_map = _preparar_dataframe_mapa(df_filtrado)
    
    if len(df_map) == 0:
        with output_visualizacao:
            output_visualizacao.clear_output()
            display(HTML("<div style='text-align: center; padding: 20px; color: #e53e3e;'>Nenhuma coordenada válida</div>"))
        return
    
    # Criar figura
    fig = _criar_figura_mapa(
        df_map, 
        municipio_coords, 
        municipio_selecionado, 
        raio_km.value, 
        usar_filtro_idade.value
    )
    
    with output_visualizacao:
        output_visualizacao.clear_output(wait=True)
        
        # Exibir estatísticas
        exibir_estatisticas_resumo(df_filtrado)
        
        # Exibir mapa
        fig.show()
        
        # Botão de download
        if df_filtrado is not None and len(df_filtrado) > 0:
            download_link = gerar_download_csv(df_filtrado)
            display(HTML(download_link))


def exportar_mapa_para_dashboard(df_filtrado, municipio_coords, municipio_selecionado, raio_km_value, usar_filtro_idade=False):
    """
    Exporta o mapa gerado como HTML string para o dashboard
    
    Args:
        df_filtrado: DataFrame com dados filtrados
        municipio_coords: Dicionário com coordenadas do município
        municipio_selecionado: Nome do município consultado
        raio_km_value: Raio de busca em km
        usar_filtro_idade: Se True, usa score demográfico na visualização
    
    Returns:
        str: HTML do mapa Plotly
    """
    
    if df_filtrado is None or len(df_filtrado) == 0:
        return "<div style='text-align: center; padding: 50px; color: #e53e3e;'>Nenhum dado disponível para visualização</div>"
    
    # Preparar dataframe
    df_map = _preparar_dataframe_mapa(df_filtrado)
    
    if len(df_map) == 0:
        return "<div style='text-align: center; padding: 50px; color: #e53e3e;'>Nenhuma coordenada válida encontrada</div>"
    
    # Criar figura
    fig = _criar_figura_mapa(
        df_map, 
        municipio_coords, 
        municipio_selecionado, 
        raio_km_value, 
        usar_filtro_idade
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


# ==================== Funções Auxiliares ====================
def exibir_estatisticas_resumo(df):
    """Exibe cards com estatísticas principais"""
    if 'score_demografico' in df.columns:
        score_medio = df['score_demografico'].mean()
        score_max = df['score_demografico'].max()
        pop_total = df.get('populacao_faixa', pd.Series([0])).sum()
    else:
        score_medio = score_max = pop_total = 0
    
    html = f"""
    <div style='display: flex; gap: 20px; margin: 20px 0; justify-content: center; flex-wrap: wrap;'>
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; 
                    flex: 1; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 36px; font-weight: bold; color: white;'>{len(df):,}</div>
            <div style='color: rgba(255,255,255,0.9); margin-top: 8px; font-size: 14px;'>Imóveis Encontrados</div>
        </div>
        <div style='background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; 
                    flex: 1; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 36px; font-weight: bold; color: white;'>{score_medio:.3f}</div>
            <div style='color: rgba(255,255,255,0.9); margin-top: 8px; font-size: 14px;'>Score Médio</div>
        </div>
        <div style='background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; 
                    flex: 1; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 36px; font-weight: bold; color: white;'>{pop_total:,.0f}</div>
            <div style='color: rgba(255,255,255,0.9); margin-top: 8px; font-size: 14px;'>População Total</div>
        </div>
    </div>
    """
    
    display(HTML(html))


def gerar_download_csv(df):
    """Gera link de download para CSV"""
    csv = df.to_csv(index=False, sep=';', encoding='utf-8')
    b64 = base64.b64encode(csv.encode()).decode()
    
    return f"""
    <div style='text-align: center; margin: 20px 0;'>
        <a href="data:text/csv;base64,{b64}" download="analise_demografica.csv" 
           style="background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); 
                  color: white; padding: 12px 30px; border-radius: 8px; 
                  text-decoration: none; display: inline-block; font-weight: 600;
                  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
                  transition: transform 0.2s;">
            📥 Baixar Resultados (CSV)
        </a>
    </div>
    """


def aplicar_estilos():
    """Aplica estilos CSS personalizados"""
    display(HTML("""
    <style>
        .widget-dropdown select, .widget-text input, .widget-combobox input {
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .widget-dropdown select:focus, .widget-text input:focus, .widget-combobox input:focus {
            border-color: #667eea;
            outline: none;
        }
        .widget-button button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            font-size: 16px;
            padding: 15px 40px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .widget-button button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        .widget-button button:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
            box-shadow: none;
        }
        .info-badge {
            background: #e6fffa;
            color: #234e52;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 12px;
            margin-top: 8px;
        }
        .error-badge {
            background: #fed7d7;
            color: #c53030;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 12px;
            margin-top: 8px;
        }
    </style>
    """))


def toggle_filtro_idade(change):
    """Toggle de exibição do filtro de idade"""
    if usar_filtro_idade.value:
        faixas_selecionadas.layout.display = 'block'
        contador_faixas.layout.display = 'block'
        atualizar_contador_faixas(None)
    else:
        faixas_selecionadas.layout.display = 'none'
        contador_faixas.layout.display = 'none'
        botao_processar.disabled = False


def atualizar_opcoes_combobox(change):
    """Atualiza opções do combobox com busca incremental"""
    texto = busca_municipio.value.strip()
    if len(texto) >= 2:
        texto_upper = texto.upper()
        opcoes_filtradas = [m for m in lista_municipios if texto_upper in m.upper()][:30]
        busca_municipio.options = opcoes_filtradas
    else:
        busca_municipio.options = []


def atualizar_info_municipio(change):
    """Atualiza informações do município selecionado"""
    global municipio_coords, municipio_selecionado
    
    municipio_texto = busca_municipio.value.strip()
    
    if municipio_texto not in lista_municipios:
        atualizar_opcoes_combobox(change)
        info_municipio_selecionado.value = ""
        municipio_coords = None
        municipio_selecionado = None
        return
    
    municipio_data = buscar_municipio_otimizado(municipio_texto)
    
    if municipio_data:
        municipio_coords = municipio_data
        municipio_selecionado = municipio_texto
        
        info_municipio_selecionado.value = f"""
        <div class='info-badge'>
            <strong>✓ {municipio_data['nome']} - {municipio_data['uf']}</strong><br>
            📍 Lat: {municipio_data['lat']:.4f}, Lon: {municipio_data['lon']:.4f}
        </div>
        """
    else:
        info_municipio_selecionado.value = """
        <div class='error-badge'>
            ✗ Município não encontrado
        </div>
        """
        municipio_coords = None
        municipio_selecionado = None


def atualizar_contador_faixas(change):
    """Atualiza contador de faixas etárias selecionadas"""
    if not usar_filtro_idade.value:
        return
    
    count = len(faixas_selecionadas.value)
    
    if count == 0:
        contador_faixas.value = "<div style='color: #e53e3e; font-weight: 600;'>⚠️ Selecione pelo menos uma faixa</div>"
        botao_processar.disabled = True
    else:
        contador_faixas.value = f"<div style='color: #48bb78; font-weight: 600;'>✓ {count} faixa(s) selecionada(s)</div>"
        botao_processar.disabled = False


def voltar_para_busca(button):
    """Retorna para a tela de busca"""
    container_principal.layout.display = 'flex'
    botao_voltar_busca.layout.display = 'none'
    with output_visualizacao:
        output_visualizacao.clear_output()


# ==================== Processamento Principal ====================
def processar_analise_otimizado(button):
    """Processamento principal com cache e error handling"""
    global df_filtrado, municipio_selecionado
    
    inicio = time.time()
    
    with output_visualizacao:
        output_visualizacao.clear_output()
        
        progress = widgets.IntProgress(
            value=0, min=0, max=100,
            description='Processando:',
            bar_style='info',
            style={'bar_color': '#667eea'},
            layout=widgets.Layout(width='50%', margin='20px auto')
        )
        status = widgets.HTML(value="<center>Iniciando análise...</center>")
        display(widgets.VBox([progress, status], layout=widgets.Layout(align_items='center')))
    
    try:
        # Etapa 1: Validação (10%)
        progress.value = 10
        status.value = "<center>🔍 Validando filtros...</center>"
        
        if usar_filtro_idade.value:
            faixas_lista = list(faixas_selecionadas.value)
            if not validar_faixas_etarias(faixas_lista) or len(faixas_lista) == 0:
                raise ValueError("Selecione pelo menos uma faixa etária válida")
        else:
            faixas_lista = None
        
        # Verificar cache
        cache_key = analysis_cache.get_key(
            municipio_selecionado or 'all',
            raio_km.value,
            faixas_lista or []
        )
        
        cached_result = analysis_cache.get(cache_key)
        if cached_result is not None:
            logger.info("✓ Usando resultado em cache")
            df_filtrado = cached_result
            progress.value = 100
            status.value = "<center>✓ Dados recuperados do cache</center>"
            
            container_principal.layout.display = 'none'
            botao_voltar_busca.layout.display = 'block'
            gerar_mapa_plotly_otimizado()
            
            tempo_total = time.time() - inicio
            logger.info(f"Análise concluída em {tempo_total:.1f}s (cache)")
            return
        
        # Etapa 2: Filtro geográfico (30%)
        progress.value = 30
        status.value = "<center>📍 Filtrando imóveis por localização...</center>"
        
        if municipio_selecionado and municipio_coords:
            df_imoveis_filtrado = filtrar_imoveis_por_raio_otimizado(
                df_imoveis,
                municipio_coords['lat'],
                municipio_coords['lon'],
                raio_km.value
            )
            
            if len(df_imoveis_filtrado) == 0:
                raise ValueError(
                    f"Nenhum imóvel encontrado em um raio de {raio_km.value}km "
                    f"de {municipio_selecionado}"
                )
        else:
            df_imoveis_filtrado = df_imoveis.copy()
        
        # Etapa 3: Análise demográfica (60%)
        progress.value = 60
        status.value = "<center>📊 Analisando dados demográficos...</center>"
        
        if usar_filtro_idade.value and faixas_lista:
            logger.info("Aplicando filtro demográfico...")
            
            # Filtrar municípios por faixa etária
            df_idade_filtrado = filtrar_multiplas_faixas(df_idade, faixas_lista)
            logger.info(f"Municípios com população nas faixas: {len(df_idade_filtrado)}")
            
            if len(df_idade_filtrado) == 0:
                raise ValueError("Nenhum município encontrado com as faixas etárias selecionadas")
            
            # Buscar municípios próximos para cada imóvel
            df_resultado = encontrar_municipios_proximos(
                df_imoveis_filtrado,
                df_idade_filtrado,
                raio_km=raio_km.value
            )
            
            if len(df_resultado) == 0:
                raise ValueError("Nenhuma correspondência encontrada entre imóveis e municípios")
            
            logger.info(f"Correspondências encontradas: {len(df_resultado)}")
            
            # Calcular scores
            df_filtrado = calcular_score_demografico(df_resultado)
            
            # Ordenar por score
            df_filtrado = df_filtrado.sort_values('score_demografico', ascending=False)
            
            logger.info(f"Análise concluída: {len(df_filtrado)} registros")
            
        else:
            # Sem filtro demográfico
            df_filtrado = df_imoveis_filtrado.copy()
            df_filtrado['score_demografico'] = np.nan
            df_filtrado['populacao_faixa'] = 0
        
        if len(df_filtrado) == 0:
            raise ValueError("Nenhum resultado encontrado com os filtros aplicados")
        
        # Armazenar no cache
        analysis_cache.set(cache_key, df_filtrado)
        
        # Etapa 4: Visualização (90%)
        progress.value = 90
        status.value = "<center>🗺️ Gerando visualização...</center>"
        
        container_principal.layout.display = 'none'
        botao_voltar_busca.layout.display = 'block'
        
        gerar_mapa_plotly_otimizado()
        
        # Concluído
        progress.value = 100
        tempo_total = time.time() - inicio
        logger.info(f"✓ Análise concluída em {tempo_total:.1f}s")
        
    except ValueError as e:
        # Erros de validação (esperados)
        with output_visualizacao:
            output_visualizacao.clear_output()
            display(HTML(f"""
            <div style='background: #fed7d7; color: #c53030; padding: 20px; 
                        border-radius: 12px; text-align: center; margin: 20px 0;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <div style='font-size: 24px; margin-bottom: 10px;'>⚠️</div>
                <b>Validação:</b> {str(e)}
            </div>
            """))
        logger.warning(f"Erro de validação: {e}")
    
    except FileNotFoundError as e:
        # Erros de arquivo
        with output_visualizacao:
            output_visualizacao.clear_output()
            display(HTML(f"""
            <div style='background: #fed7d7; color: #c53030; padding: 20px; 
                        border-radius: 12px; text-align: center; margin: 20px 0;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <div style='font-size: 24px; margin-bottom: 10px;'>📁</div>
                <b>Arquivo não encontrado:</b> {str(e)}
            </div>
            """))
        logger.error(f"Arquivo não encontrado: {e}")
    
    except Exception as e:
        # Erros inesperados
        with output_visualizacao:
            output_visualizacao.clear_output()
            display(HTML(f"""
            <div style='background: #fed7d7; color: #c53030; padding: 20px; 
                        border-radius: 12px; text-align: center; margin: 20px 0;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <div style='font-size: 24px; margin-bottom: 10px;'>❌</div>
                <b>Erro inesperado:</b> {str(e)}
            </div>
            """))
            import traceback
            print("\n" + "="*60)
            print("DETALHES DO ERRO:")
            print("="*60)
            traceback.print_exc()
            print("="*60)
        logger.error(f"Erro inesperado: {e}", exc_info=True)


# ==================== Inicialização ====================
logger.info("="*60)
logger.info("Iniciando Dashboard de Análise Demográfica de Imóveis")
logger.info("="*60)

try:
    df_imoveis, df_idade, lista_municipios = carregar_dados()
    faixas_disponiveis = get_faixas_disponiveis()
    logger.info("✓ Sistema pronto!\n")
except Exception as e:
    logger.error(f"Erro ao inicializar sistema: {e}")
    raise

aplicar_estilos()

# ==================== Widgets ====================
busca_municipio = widgets.Combobox(
    placeholder='Digite o município (ex: Campinas)',
    options=[],
    description='🏙️ Município',
    ensure_option=False,
    style={'description_width': '120px'},
    layout=widgets.Layout(width='100%', margin='0 0 15px 0')
)

info_municipio_selecionado = widgets.HTML(
    value="", 
    layout=widgets.Layout(margin='0 0 15px 0')
)

usar_filtro_idade = widgets.Checkbox(
    value=False,
    description='👥 Filtrar por faixa etária',
    style={'description_width': 'initial'},
    layout=widgets.Layout(margin='0 0 15px 0')
)

faixas_selecionadas = widgets.SelectMultiple(
    options=faixas_disponiveis,
    value=["18 a 29 anos"],
    description='📊 Faixas Etárias',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='100%', height='140px', display='none', margin='0 0 10px 0')
)

contador_faixas = widgets.HTML(
    value="", 
    layout=widgets.Layout(display='none', margin='0 0 15px 0')
)

raio_km = widgets.IntSlider(
    value=50, min=10, max=200, step=10,
    description='📏 Raio (km)',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='100%', margin='0 0 15px 0')
)

top_n = widgets.IntSlider(
    value=10, min=5, max=50, step=5,
    description='🏆 Top Municípios',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='100%', margin='0 0 20px 0')
)

botao_processar = widgets.Button(
    description='🚀 Processar Análise',
    layout=widgets.Layout(width='auto', height='auto', margin='0')
)

botao_voltar_busca = widgets.Button(
    description='⬅️ Voltar à Busca',
    layout=widgets.Layout(width='auto', height='auto', margin='0', display='none')
)

output_visualizacao = widgets.Output()

# Variáveis globais
df_filtrado = None
municipio_coords = None
municipio_selecionado = None

# ==================== Observers ====================
usar_filtro_idade.observe(toggle_filtro_idade, names='value')
busca_municipio.observe(atualizar_info_municipio, names='value')
faixas_selecionadas.observe(atualizar_contador_faixas, names='value')
botao_processar.on_click(processar_analise_otimizado)
botao_voltar_busca.on_click(voltar_para_busca)

# ==================== Interface ====================
titulo = widgets.HTML(value="""
<div style='text-align: center; margin-bottom: 30px;'>
    <h1 style='color: #1f2937; margin-bottom: 10px;'>
        🏘️ Dashboard de Análise Demográfica de Imóveis
    </h1>
    <p style='color: #6b7280; font-size: 16px;'>
        Análise espacial com filtros demográficos e visualização interativa
    </p>
</div>
""")

container_principal = widgets.VBox([
    titulo,
    busca_municipio,
    info_municipio_selecionado,
    usar_filtro_idade,
    faixas_selecionadas,
    contador_faixas,
    raio_km,
    top_n,
    widgets.HBox(
        [botao_processar], 
        layout=widgets.Layout(justify_content='center', width='100%', margin='20px 0 0 0')
    ),
], layout=widgets.Layout(
    width='700px',
    margin='0 auto',
    padding='30px',
    background='white',
    border_radius='20px',
    box_shadow='0 10px 40px rgba(0, 0, 0, 0.15)'
))

display(container_principal)
display(botao_voltar_busca)
display(output_visualizacao)

# ==================== Exportação para Dashboard ====================
logger.info("\n" + "="*60)
logger.info("FUNÇÕES DE EXPORTAÇÃO DISPONÍVEIS:")
logger.info("="*60)
logger.info("1. exportar_mapa_para_dashboard() - Exporta mapa como HTML")
logger.info("2. gerar_download_csv() - Gera link de download CSV")
logger.info("3. exibir_estatisticas_resumo() - Exibe estatísticas")
logger.info("="*60)

# Exemplo de uso da exportação (descomente para usar):
"""
if df_filtrado is not None and len(df_filtrado) > 0:
    logger.info("\n Gerando HTML do mapa para dashboard...")
    
    mapa_demografico_html = exportar_mapa_para_dashboard(
        df_filtrado=df_filtrado,
        municipio_coords=municipio_coords,
        municipio_selecionado=municipio_selecionado,
        raio_km_value=raio_km.value,
        usar_filtro_idade=usar_filtro_idade.value
    )
    
    logger.info(f"✓ Mapa HTML gerado com sucesso!")
    logger.info(f" Tamanho do HTML: {len(mapa_demografico_html):,} caracteres")
    
    # Salvar em arquivo
    with open("temp_mapa_demografico.html", "w", encoding="utf-8") as f:
        f.write(mapa_demografico_html)
    
    logger.info(" Arquivo salvo: temp_mapa_demografico.html")
else:
    logger.info(" Nenhuma análise foi processada ainda.")
    logger.info(" Execute 'Processar Análise' primeiro para gerar o mapa.")
"""