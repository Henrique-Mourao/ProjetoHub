"""
Módulo para aplicar regras e filtros de faixas etárias personalizadas - CORRIGIDO
"""
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

def get_faixas_disponiveis():
    """Retorna lista de faixas etárias disponíveis"""
    return [
        "18 a 29 anos",
        "30 a 49 anos",
        "50 a 79 anos",
        "80 ou mais"
    ]


def validar_faixas_etarias(faixas):
    """Valida se as faixas etárias selecionadas são válidas"""
    faixas_validas = get_faixas_disponiveis()
    return all(faixa in faixas_validas for faixa in faixas)


def mapear_colunas_para_faixas(faixas_selecionadas):
    """
    Mapeia as faixas selecionadas para as colunas correspondentes do DataFrame
    
    Args:
        faixas_selecionadas: Lista de faixas no formato "18 a 29 anos"
        
    Returns:
        list: Lista de colunas do DataFrame a serem mantidas
    """
    mapeamento = {
        "18 a 29 anos": ["15 a 19 anos", "20 a 29 anos"],
        "30 a 49 anos": ["30 a 39 anos", "40 a 49 anos"],
        "50 a 79 anos": ["50 a 59 anos", "60 a 69 anos", "70 a 79 anos"],
        "80 ou mais": ["80 anos e mais"]
    }
    
    colunas_necessarias = []
    for faixa in faixas_selecionadas:
        if faixa in mapeamento:
            colunas_necessarias.extend(mapeamento[faixa])
    
    return colunas_necessarias


def filtrar_multiplas_faixas(df, faixas_selecionadas, coluna_idade=None):
    """
    Filtra DataFrame mantendo apenas as colunas das faixas selecionadas
    
    Args:
        df: DataFrame com faixas etárias como colunas
        faixas_selecionadas: Lista com faixas selecionadas
        coluna_idade: Não usado (compatibilidade)
        
    Returns:
        DataFrame filtrado
    """
    if not faixas_selecionadas:
        return df
    
    df = df.copy()
    
    # Obtém as colunas das faixas
    colunas_faixas = mapear_colunas_para_faixas(faixas_selecionadas)
    
    # Colunas obrigatórias
    colunas_obrigatorias = ['MUNICIPIO', 'sigla_uf', 'latitude', 'longitude']
    
    # Colunas finais
    colunas_manter = colunas_obrigatorias + colunas_faixas
    
    # Filtra apenas existentes
    colunas_existentes = [col for col in colunas_manter if col in df.columns]
    
    df_filtrado = df[colunas_existentes].copy()
    
    # Converte colunas numéricas (VETORIZADO)
    colunas_numericas = [col for col in colunas_faixas if col in df_filtrado.columns]
    if colunas_numericas:
        df_filtrado[colunas_numericas] = df_filtrado[colunas_numericas].apply(
            pd.to_numeric, errors='coerce'
        ).fillna(0)
        
        # Soma total das faixas selecionadas (VETORIZADO)
        df_filtrado['populacao_faixa_selecionada'] = df_filtrado[colunas_numericas].sum(axis=1)
        
        # Remove municípios sem população nas faixas selecionadas
        df_filtrado = df_filtrado[df_filtrado['populacao_faixa_selecionada'] > 0].copy()
    
    return df_filtrado


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre dois pontos usando a fórmula de Haversine
    VETORIZADO para arrays numpy
    
    Args:
        lat1, lon1: Coordenadas do ponto 1 (podem ser arrays)
        lat2, lon2: Coordenadas do ponto 2 (podem ser arrays)
        
    Returns:
        float ou array: Distância em quilômetros
    """
    # Raio da Terra em km
    R = 6371.0
    
    # Converte para radianos
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distancia = R * c
    
    return distancia


    """
    Calcula a distância entre dois pontos usando a fórmula de Haversine
    VETORIZADO para arrays numpy
    
    Args:
        lat1, lon1: Coordenadas do ponto 1 (podem ser arrays)
        lat2, lon2: Coordenadas do ponto 2 (podem ser arrays)
        
    Returns:
        float ou array: Distância em quilômetros
    """

def encontrar_municipios_proximos_otimizado(df_imoveis, df_municipios, raio_km=50, batch_size=100):
    """
    VERSÃO OTIMIZADA: Usa KDTree para busca espacial eficiente
    Complexidade: O(n log m) ao invés de O(n × m)
    
    Args:
        df_imoveis: DataFrame com imóveis (deve ter Latitude e Longitude)
        df_municipios: DataFrame com municípios (deve ter latitude e longitude)
        raio_km: Raio de busca em km
        batch_size: Tamanho do lote para processamento
        
    Returns:
        DataFrame com imóveis e municípios próximos
    """
    
    # Validar dados
    if len(df_imoveis) == 0 or len(df_municipios) == 0:
        print(" DataFrames vazios")
        return pd.DataFrame()
    
    # Preparar coordenadas dos municípios
    coords_municipios = df_municipios[['latitude', 'longitude']].values
    
    # Criar KDTree (busca espacial eficiente)
    # Converter raio de km para graus (aproximação: 1 grau ≈ 111 km)
    raio_graus = raio_km / 111.0
    tree = cKDTree(coords_municipios)
    
    # Processar em lotes para economizar memória
    resultados = []
    total_imoveis = len(df_imoveis)
    
    for start_idx in range(0, total_imoveis, batch_size):
        end_idx = min(start_idx + batch_size, total_imoveis)
        batch = df_imoveis.iloc[start_idx:end_idx]
        
        if start_idx % 500 == 0:
            print(f"  Processando imóveis {start_idx}/{total_imoveis}...")
        
        for idx_imovel, imovel in batch.iterrows():
            lat_imovel = imovel['Latitude']
            lon_imovel = imovel['Longitude']
            
            # Validar coordenadas
            if pd.isna(lat_imovel) or pd.isna(lon_imovel):
                continue
            
            # Busca rápida com KDTree
            indices_proximos = tree.query_ball_point([lat_imovel, lon_imovel], raio_graus)
            
            if len(indices_proximos) == 0:
                continue
            
            # Pegar apenas municípios próximos
            municipios_proximos = df_municipios.iloc[indices_proximos].copy()
            
            # Calcular distâncias exatas (vetorizado)
            distancias = calcular_distancia_haversine(
                lat_imovel, 
                lon_imovel,
                municipios_proximos['latitude'].values,
                municipios_proximos['longitude'].values
            )
            
            # Filtrar por distância exata
            mask_raio = distancias <= raio_km
            municipios_filtrados = municipios_proximos[mask_raio].copy()
            distancias_filtradas = distancias[mask_raio]
            
            if len(municipios_filtrados) == 0:
                continue
            
            # Criar registros de forma eficiente
            for (idx_mun, municipio), distancia in zip(municipios_filtrados.iterrows(), distancias_filtradas):
                resultado = {
                    'imovel_id': idx_imovel,
                    'imovel_lat': lat_imovel,
                    'imovel_lon': lon_imovel,
                    'municipio': municipio['MUNICIPIO'],
                    'uf': municipio['sigla_uf'],
                    'distancia_km': float(distancia),
                    'populacao_faixa': float(municipio.get('populacao_faixa_selecionada', 0))
                }
                
                # Adicionar colunas relevantes do imóvel (evitar todas as colunas)
                colunas_relevantes = ['Cidade', 'Estado', 'Preco', 'Quartos', 'Banheiros']
                for col in colunas_relevantes:
                    if col in imovel.index and col not in ['Latitude', 'Longitude']:
                        resultado[f'imovel_{col}'] = imovel[col]
                
                resultados.append(resultado)
    
    print(f"✓ Encontradas {len(resultados)} combinações imóvel-município")
    
    if len(resultados) == 0:
        return pd.DataFrame()
    
    return pd.DataFrame(resultados)


def encontrar_municipios_proximos(df_imoveis, df_municipios, raio_km=50):
    """
    Wrapper que chama a versão otimizada
    Mantido para compatibilidade
    """
    return encontrar_municipios_proximos_otimizado(df_imoveis, df_municipios, raio_km)


def calcular_score_demografico(df_resultado, peso_distancia=0.4, peso_populacao=0.6):
    """
    Calcula score demográfico combinando distância e população
    VERSÃO OTIMIZADA com operações vetorizadas
    
    Args:
        df_resultado: DataFrame com imóveis e municípios
        peso_distancia: Peso da proximidade (0-1)
        peso_populacao: Peso da população (0-1)
        
    Returns:
        DataFrame com score calculado
    """
    if len(df_resultado) == 0:
        return df_resultado
    
    df = df_resultado.copy()
    
    # Garantir que as colunas existem
    if 'distancia_km' not in df.columns:
        df['distancia_km'] = 0
    if 'populacao_faixa' not in df.columns:
        df['populacao_faixa'] = 0
    
    # Normaliza distância (quanto menor, melhor) - VETORIZADO
    max_dist = df['distancia_km'].max()
    if max_dist > 0:
        df['score_distancia'] = 1 - (df['distancia_km'] / max_dist)
    else:
        df['score_distancia'] = 1.0
    
    # Normaliza população (quanto maior, melhor) - VETORIZADO
    max_pop = df['populacao_faixa'].max()
    if max_pop > 0:
        df['score_populacao'] = df['populacao_faixa'] / max_pop
    else:
        df['score_populacao'] = 0.0
    
    # Score final - VETORIZADO
    df['score_demografico'] = (
        peso_distancia * df['score_distancia'] + 
        peso_populacao * df['score_populacao']
    )
    
    return df


def criar_resumo_faixas(df, faixas_selecionadas):
    """Cria resumo estatístico das faixas selecionadas - OTIMIZADO"""
    colunas_faixas = mapear_colunas_para_faixas(faixas_selecionadas)
    colunas_existentes = [col for col in colunas_faixas if col in df.columns]
    
    if not colunas_existentes or len(df) == 0:
        return {
            'total_populacao': 0,
            'media_por_municipio': 0,
            'municipios_com_dados': 0,
            'colunas_utilizadas': []
        }
    
    df_temp = df[colunas_existentes].copy()
    
    # Conversão vetorizada
    df_temp = df_temp.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Cálculos vetorizados
    populacao_total = df_temp.values.sum()
    soma_por_municipio = df_temp.sum(axis=1)
    media_por_municipio = soma_por_municipio.mean()
    municipios_com_dados = len(df_temp)
    
    return {
        'total_populacao': int(populacao_total),
        'media_por_municipio': float(media_por_municipio),
        'municipios_com_dados': municipios_com_dados,
        'colunas_utilizadas': colunas_existentes
    }


def analisar_por_municipio_agregado(df_imoveis, df_municipios, raio_km=50):
    """
    Versão ULTRA-OTIMIZADA que agrupa imóveis por município primeiro
    Reduz drasticamente o número de cálculos
    
    Args:
        df_imoveis: DataFrame com imóveis
        df_municipios: DataFrame com municípios
        raio_km: Raio de busca
        
    Returns:
        DataFrame agregado por município
    """
    
    # Agrupar imóveis por cidade
    if 'Cidade' in df_imoveis.columns:
        imoveis_por_cidade = df_imoveis.groupby('Cidade').agg({
            'Latitude': 'mean',
            'Longitude': 'mean',
            'Cidade': 'count'  # contador
        }).rename(columns={'Cidade': 'quantidade_imoveis'}).reset_index()
        
        print(f"  Agrupados em {len(imoveis_por_cidade)} cidades únicas")
        
        # Buscar municípios próximos apenas para cidades únicas
        resultado = encontrar_municipios_proximos_otimizado(
            imoveis_por_cidade, 
            df_municipios, 
            raio_km
        )
        
        return resultado
    else:
        # Fallback para método normal
        return encontrar_municipios_proximos_otimizado(
            df_imoveis, 
            df_municipios, 
            raio_km
        )


# Funções de compatibilidade
def filtrar_por_faixa_etaria(df, faixas_selecionadas):
    """Alias para filtrar_multiplas_faixas"""
    return filtrar_multiplas_faixas(df, faixas_selecionadas)


def agrupar_por_faixa(df, coluna_idade=None):
    """Mantido por compatibilidade"""
    return df