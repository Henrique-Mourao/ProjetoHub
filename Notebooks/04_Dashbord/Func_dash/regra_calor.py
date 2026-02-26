"""
Módulo para aplicar filtros geográficos e de dados ao mapa de calor
"""
import pandas as pd
import numpy as np


def get_estados_disponiveis(df):
    """
    Retorna lista de estados (UF) disponíveis no dataset
    
    Args:
        df: DataFrame com coluna 'sigla_uf' ou 'Estado'
        
    Returns:
        list: Lista ordenada de UFs únicas
    """
    col_uf = 'sigla_uf' if 'sigla_uf' in df.columns else 'Estado'
    
    if col_uf not in df.columns:
        return []
    
    estados = df[col_uf].dropna().unique().tolist()
    return sorted(estados)


def get_regioes_disponiveis():
    """Retorna dicionário com regiões e seus estados"""
    return {
        "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        "Centro-Oeste": ["DF", "GO", "MT", "MS"],
        "Sudeste": ["ES", "MG", "RJ", "SP"],
        "Sul": ["PR", "RS", "SC"]
    }


def filtrar_por_estados(df, estados_selecionados, coluna_uf='sigla_uf'):
    """
    Filtra DataFrame por estados selecionados
    
    Args:
        df: DataFrame com dados
        estados_selecionados: Lista de UFs (ex: ['SP', 'RJ', 'MG'])
        coluna_uf: Nome da coluna com UF
        
    Returns:
        DataFrame filtrado
    """
    if not estados_selecionados:
        return df
    
    # Tenta diferentes nomes de coluna
    if coluna_uf not in df.columns:
        if 'Estado' in df.columns:
            coluna_uf = 'Estado'
        else:
            print(f"⚠️ Coluna '{coluna_uf}' não encontrada")
            return df
    
    df_filtrado = df[df[coluna_uf].isin(estados_selecionados)].copy()
    
    print(f"✓ Filtrado por estados: {len(df_filtrado):,} registros ({len(estados_selecionados)} UFs)")
    
    return df_filtrado


def filtrar_por_regiao(df, regioes_selecionadas, coluna_uf='sigla_uf'):
    """
    Filtra DataFrame por regiões do Brasil
    
    Args:
        df: DataFrame com dados
        regioes_selecionadas: Lista de regiões (ex: ['Sudeste', 'Sul'])
        coluna_uf: Nome da coluna com UF
        
    Returns:
        DataFrame filtrado
    """
    if not regioes_selecionadas:
        return df
    
    mapa_regioes = get_regioes_disponiveis()
    
    # Coleta todos os estados das regiões selecionadas
    estados_incluir = []
    for regiao in regioes_selecionadas:
        if regiao in mapa_regioes:
            estados_incluir.extend(mapa_regioes[regiao])
    
    if not estados_incluir:
        return df
    
    return filtrar_por_estados(df, estados_incluir, coluna_uf)


def filtrar_por_coordenadas(df, lat_min=None, lat_max=None, lon_min=None, lon_max=None,
                            lat_col='latitude', lon_col='longitude'):
    """
    Filtra DataFrame por área geográfica (bounding box)
    
    Args:
        df: DataFrame com coordenadas
        lat_min, lat_max: Limites de latitude
        lon_min, lon_max: Limites de longitude
        lat_col, lon_col: Nomes das colunas de coordenadas
        
    Returns:
        DataFrame filtrado
    """
    df_filtrado = df.copy()
    
    if lat_min is not None:
        df_filtrado = df_filtrado[df_filtrado[lat_col] >= lat_min]
    
    if lat_max is not None:
        df_filtrado = df_filtrado[df_filtrado[lat_col] <= lat_max]
    
    if lon_min is not None:
        df_filtrado = df_filtrado[df_filtrado[lon_col] >= lon_min]
    
    if lon_max is not None:
        df_filtrado = df_filtrado[df_filtrado[lon_col] <= lon_max]
    
    print(f"✓ Filtrado por coordenadas: {len(df_filtrado):,} registros")
    
    return df_filtrado


def filtrar_por_raio(df, lat_centro, lon_centro, raio_km,
                     lat_col='latitude', lon_col='longitude'):
    """
    Filtra pontos dentro de um raio a partir de um centro
    
    Args:
        df: DataFrame com coordenadas
        lat_centro, lon_centro: Coordenadas do centro
        raio_km: Raio em quilômetros
        lat_col, lon_col: Nomes das colunas
        
    Returns:
        DataFrame filtrado com coluna 'distancia_centro_km'
    """
    from scipy.spatial.distance import cdist
    
    df_filtrado = df.copy()
    
    # Calcular distâncias (vetorizado)
    coords_pontos = df_filtrado[[lat_col, lon_col]].values
    coords_centro = np.array([[lat_centro, lon_centro]])
    
    # Haversine aproximado (em graus)
    distancias_graus = cdist(coords_pontos, coords_centro, metric='euclidean')
    distancias_km = distancias_graus.flatten() * 111  # 1 grau ≈ 111 km
    
    df_filtrado['distancia_centro_km'] = distancias_km
    
    # Filtrar por raio
    df_filtrado = df_filtrado[df_filtrado['distancia_centro_km'] <= raio_km].copy()
    
    print(f"✓ Filtrado por raio de {raio_km}km: {len(df_filtrado):,} registros")
    
    return df_filtrado


def filtrar_por_densidade(df, percentil_min=0, percentil_max=100,
                          lat_col='latitude', lon_col='longitude',
                          grid_size=0.1):
    """
    Filtra áreas por densidade de pontos
    Remove áreas muito esparsas ou muito densas
    
    Args:
        df: DataFrame com coordenadas
        percentil_min: Percentil mínimo de densidade (0-100)
        percentil_max: Percentil máximo de densidade (0-100)
        lat_col, lon_col: Colunas de coordenadas
        grid_size: Tamanho da célula do grid (em graus)
        
    Returns:
        DataFrame filtrado
    """
    df_temp = df.copy()
    
    # Criar grid
    df_temp['grid_lat'] = (df_temp[lat_col] / grid_size).round() * grid_size
    df_temp['grid_lon'] = (df_temp[lon_col] / grid_size).round() * grid_size
    
    # Contar pontos por célula
    densidade = df_temp.groupby(['grid_lat', 'grid_lon']).size().reset_index(name='densidade')
    
    # Calcular percentis
    densidade_min = np.percentile(densidade['densidade'], percentil_min)
    densidade_max = np.percentile(densidade['densidade'], percentil_max)
    
    # Filtrar células
    celulas_validas = densidade[
        (densidade['densidade'] >= densidade_min) & 
        (densidade['densidade'] <= densidade_max)
    ][['grid_lat', 'grid_lon']]
    
    # Merge com dados originais
    df_filtrado = df_temp.merge(celulas_validas, on=['grid_lat', 'grid_lon'], how='inner')
    df_filtrado = df_filtrado.drop(columns=['grid_lat', 'grid_lon'])
    
    print(f"✓ Filtrado por densidade (p{percentil_min}-p{percentil_max}): {len(df_filtrado):,} registros")
    
    return df_filtrado


def filtrar_outliers_geograficos(df, lat_col='latitude', lon_col='longitude', 
                                  desvios=3):
    """
    Remove outliers geográficos usando desvio padrão
    
    Args:
        df: DataFrame com coordenadas
        lat_col, lon_col: Colunas de coordenadas
        desvios: Número de desvios padrão para considerar outlier
        
    Returns:
        DataFrame sem outliers
    """
    df_filtrado = df.copy()
    
    # Calcular limites
    lat_mean, lat_std = df[lat_col].mean(), df[lat_col].std()
    lon_mean, lon_std = df[lon_col].mean(), df[lon_col].std()
    
    lat_min = lat_mean - desvios * lat_std
    lat_max = lat_mean + desvios * lat_std
    lon_min = lon_mean - desvios * lon_std
    lon_max = lon_mean + desvios * lon_std
    
    # Filtrar
    df_filtrado = df_filtrado[
        (df_filtrado[lat_col] >= lat_min) &
        (df_filtrado[lat_col] <= lat_max) &
        (df_filtrado[lon_col] >= lon_min) &
        (df_filtrado[lon_col] <= lon_max)
    ].copy()
    
    removidos = len(df) - len(df_filtrado)
    print(f"✓ Removidos {removidos:,} outliers geográficos ({removidos/len(df)*100:.1f}%)")
    
    return df_filtrado


def aplicar_filtros_combinados(df, filtros_config):
    """
    Aplica múltiplos filtros de forma sequencial
    
    Args:
        df: DataFrame original
        filtros_config: Dicionário com configurações dos filtros
            {
                'estados': ['SP', 'RJ'],
                'regioes': ['Sudeste'],
                'raio': {'lat': -23.5, 'lon': -46.6, 'km': 50},
                'densidade': {'min': 10, 'max': 90},
                'remover_outliers': True
            }
    
    Returns:
        DataFrame filtrado
    """
    df_resultado = df.copy()
    original_count = len(df_resultado)
    
    print(f"\n🔍 Aplicando filtros...")
    print(f"  Registros iniciais: {original_count:,}")
    
    # Filtro por estados
    if 'estados' in filtros_config and filtros_config['estados']:
        df_resultado = filtrar_por_estados(df_resultado, filtros_config['estados'])
    
    # Filtro por regiões
    if 'regioes' in filtros_config and filtros_config['regioes']:
        df_resultado = filtrar_por_regiao(df_resultado, filtros_config['regioes'])
    
    # Filtro por raio
    if 'raio' in filtros_config:
        config_raio = filtros_config['raio']
        df_resultado = filtrar_por_raio(
            df_resultado,
            config_raio['lat'],
            config_raio['lon'],
            config_raio['km']
        )
    
    # Filtro por coordenadas (bounding box)
    if 'bbox' in filtros_config:
        bbox = filtros_config['bbox']
        df_resultado = filtrar_por_coordenadas(
            df_resultado,
            bbox.get('lat_min'),
            bbox.get('lat_max'),
            bbox.get('lon_min'),
            bbox.get('lon_max')
        )
    
    # Filtro por densidade
    if 'densidade' in filtros_config:
        dens = filtros_config['densidade']
        df_resultado = filtrar_por_densidade(
            df_resultado,
            dens.get('min', 0),
            dens.get('max', 100)
        )
    
    # Remover outliers
    if filtros_config.get('remover_outliers', False):
        df_resultado = filtrar_outliers_geograficos(df_resultado)
    
    final_count = len(df_resultado)
    reducao = (1 - final_count/original_count) * 100 if original_count > 0 else 0
    
    print(f"\n✅ Filtros aplicados!")
    print(f"  Registros finais: {final_count:,}")
    print(f"  Redução: {reducao:.1f}%\n")
    
    return df_resultado


def criar_resumo_geografico(df, lat_col='latitude', lon_col='longitude'):
    """
    Cria resumo estatístico da distribuição geográfica
    
    Returns:
        dict: Estatísticas geográficas
    """
    if len(df) == 0:
        return {}
    
    return {
        'total_pontos': len(df),
        'lat_min': float(df[lat_col].min()),
        'lat_max': float(df[lat_col].max()),
        'lon_min': float(df[lon_col].min()),
        'lon_max': float(df[lon_col].max()),
        'lat_centro': float(df[lat_col].mean()),
        'lon_centro': float(df[lon_col].mean()),
        'lat_mediana': float(df[lat_col].median()),
        'lon_mediana': float(df[lon_col].median()),
        'estados_unicos': df['sigla_uf'].nunique() if 'sigla_uf' in df.columns else 0
    }