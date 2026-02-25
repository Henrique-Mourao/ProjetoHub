"""
Módulo para análise demográfica de imóveis
"""
import pandas as pd
import numpy as np
from .regra_idade import (
    encontrar_municipios_proximos,
    calcular_score_demografico
)


def carregar_dados_demograficos(caminho_csv):
    """Carrega dados demográficos dos municípios"""
    df = pd.read_csv(caminho_csv, sep=',', encoding='utf-8')
    
    # Padroniza nomes de colunas
    df.columns = df.columns.str.strip()
    
    # Converte coordenadas
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Remove linhas sem coordenadas
    df = df.dropna(subset=['latitude', 'longitude'])
    
    return df


def analisar_imoveis_demograficos(df_imoveis, df_idade, faixas_etarias, top_n=10, raio_km=50, verbose=True):
    """
    Analisa imóveis considerando dados demográficos
    
    Args:
        df_imoveis: DataFrame com imóveis
        df_idade: DataFrame com dados demográficos (já filtrado por faixas)
        faixas_etarias: Lista de faixas etárias selecionadas
        top_n: Número de municípios a considerar
        raio_km: Raio de busca em km
        verbose: Mostrar mensagens
        
    Returns:
        DataFrame com análise completa
    """
    if verbose:
        print(f"🔍 Analisando {len(df_imoveis):,} imóveis...")
        print(f"📊 Municípios com dados: {len(df_idade):,}")
        print(f"🎯 Raio de busca: {raio_km} km")
    
    # Encontra municípios próximos
    df_resultado = encontrar_municipios_proximos(df_imoveis, df_idade, raio_km)
    
    if len(df_resultado) == 0:
        if verbose:
            print("⚠️ Nenhum município encontrado no raio especificado")
        return pd.DataFrame()
    
    # Calcula score demográfico
    df_resultado = calcular_score_demografico(df_resultado)
    
    # Ordena por score
    df_resultado = df_resultado.sort_values('score_demografico', ascending=False)
    
    # Agrupa por imóvel e pega top N municípios
    df_final = df_resultado.groupby('imovel_id').head(top_n).reset_index(drop=True)
    
    if verbose:
        print(f"✅ Análise concluída: {len(df_final):,} registros")
        print(f"📍 Imóveis com influência: {df_final['imovel_id'].nunique():,}")
    
    return df_final


def obter_estatisticas(df_resultado):
    """
    Obtém estatísticas da análise
    
    Args:
        df_resultado: DataFrame resultado da análise
        
    Returns:
        dict: Estatísticas
    """
    if len(df_resultado) == 0:
        return {
            'total_imoveis': 0,
            'com_influencia': 0,
            'score_medio': 0,
            'populacao_total': 0
        }
    
    return {
        'total_imoveis': df_resultado['imovel_id'].nunique(),
        'com_influencia': df_resultado['imovel_id'].nunique(),
        'score_medio': df_resultado['score_demografico'].mean(),
        'populacao_total': df_resultado['populacao_faixa'].sum()
    }