# ============================================================================
# Func_dash/municipios_coordenadas.py - VERSÃO COM CENTROIDE
# ============================================================================

import pandas as pd
import numpy as np
import re


def extrair_coordenadas_centroide(centroide_str):
    """
    Extrai latitude e longitude de uma string de centroide
    
    Formatos suportados:
    - "POINT(-47.123 -23.456)"
    - "(-47.123, -23.456)"
    - "-47.123,-23.456"
    - "lat: -23.456, lon: -47.123"
    
    Retorna:
    --------
    tuple: (latitude, longitude) ou (None, None)
    """
    if pd.isna(centroide_str):
        return (None, None)
    
    try:
        centroide_str = str(centroide_str).strip()
        
        # Padrão 1: POINT(lon lat) - formato WKT
        match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', centroide_str, re.IGNORECASE)
        if match:
            lon = float(match.group(1))
            lat = float(match.group(2))
            return (lat, lon)
        
        # Padrão 2: (lon, lat) ou [lon, lat]
        match = re.search(r'[\(\[]\s*([-\d.]+)\s*,\s*([-\d.]+)\s*[\)\]]', centroide_str)
        if match:
            val1 = float(match.group(1))
            val2 = float(match.group(2))
            # Determinar qual é lat e qual é lon pelo range
            if -90 <= val1 <= 90 and -180 <= val2 <= 180:
                return (val1, val2)  # val1=lat, val2=lon
            elif -90 <= val2 <= 90 and -180 <= val1 <= 180:
                return (val2, val1)  # val2=lat, val1=lon
        
        # Padrão 3: "lon,lat" ou "lon lat"
        match = re.search(r'([-\d.]+)[\s,]+([-\d.]+)', centroide_str)
        if match:
            val1 = float(match.group(1))
            val2 = float(match.group(2))
            # Determinar ordem
            if -90 <= val1 <= 90 and -180 <= val2 <= 180:
                return (val1, val2)
            elif -90 <= val2 <= 90 and -180 <= val1 <= 180:
                return (val2, val1)
        
        # Padrão 4: "lat: X, lon: Y" ou "latitude: X, longitude: Y"
        lat_match = re.search(r'lat(?:itude)?[:\s]+([-\d.]+)', centroide_str, re.IGNORECASE)
        lon_match = re.search(r'lon(?:gitude)?[:\s]+([-\d.]+)', centroide_str, re.IGNORECASE)
        if lat_match and lon_match:
            lat = float(lat_match.group(1))
            lon = float(lon_match.group(1))
            return (lat, lon)
        
    except (ValueError, AttributeError):
        pass
    
    return (None, None)


def validar_coluna_coordenada(df, coluna):
    """Valida se uma coluna contém coordenadas válidas"""
    try:
        amostra = df[coluna].dropna().head(100)
        
        if len(amostra) == 0:
            return False
        
        valores_numericos = pd.to_numeric(amostra, errors='coerce')
        validos = valores_numericos.notna().sum()
        
        if validos < len(amostra) * 0.5:
            return False
        
        valores_validos = valores_numericos.dropna()
        
        if len(valores_validos) == 0:
            return False
        
        if valores_validos.abs().max() > 180:
            return False
        
        return True
        
    except:
        return False


def carregar_municipios_coordenadas(path='../../Data/Raw/municipios_br.csv'):
    """
    Carrega arquivo com coordenadas dos municípios brasileiros
    Suporta formato com coluna 'centroide' ou 'latitude'/'longitude' separadas
    """
    
    print(f"\n🔍 Tentando carregar: {path}")
    
    configuracoes = [
        {'encoding': 'utf-8', 'sep': ',', 'low_memory': False},
        {'encoding': 'utf-8', 'sep': ';', 'low_memory': False},
        {'encoding': 'latin-1', 'sep': ',', 'low_memory': False},
        {'encoding': 'latin-1', 'sep': ';', 'low_memory': False},
    ]
    
    df = None
    
    for i, config in enumerate(configuracoes, 1):
        try:
            print(f"  Tentativa {i}/{len(configuracoes)}: {config['encoding']}, sep='{config['sep']}'", end='')
            df = pd.read_csv(path, **config)
            print(" ✓")
            break
        except:
            print(f" ✗")
            continue
    
    if df is None:
        print("❌ Não foi possível carregar o arquivo")
        return None
    
    print(f"\n✅ Arquivo carregado: {len(df):,} registros, {len(df.columns)} colunas")
    
    # Normalizar colunas
    df.columns = df.columns.str.strip().str.lower()
    
    print("\n🔎 Colunas disponíveis:")
    for col in list(df.columns)[:15]:
        print(f"  • {col}")
    if len(df.columns) > 15:
        print(f"  ... e mais {len(df.columns) - 15} colunas")
    
    # IDENTIFICAR COLUNAS
    print("\n🔍 Identificando colunas...")
    
    col_mapping = {}
    tem_centroide = False
    
    # 1. MUNICÍPIO
    candidatos_municipio = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(palavra in col_lower for palavra in ['nome', 'municipio', 'cidade']) and 'id' not in col_lower:
            candidatos_municipio.append(col)
    
    if candidatos_municipio:
        col_mapping['municipio'] = 'nome' if 'nome' in candidatos_municipio else candidatos_municipio[0]
        print(f"  ✓ municipio: '{col_mapping['municipio']}'")
    else:
        print(f"  ✗ municipio: não encontrado")
    
    # 2. UF
    for col in df.columns:
        col_lower = str(col).lower()
        if any(palavra in col_lower for palavra in ['sigla_uf', 'uf', 'estado']):
            col_mapping['uf'] = col
            print(f"  ✓ uf: '{col}'")
            break
    
    # 3. VERIFICAR SE TEM CENTROIDE
    for col in df.columns:
        if 'centroid' in str(col).lower() or str(col).lower() == 'centroide':
            col_mapping['centroide'] = col
            tem_centroide = True
            print(f"  ✓ centroide: '{col}' (será extraído lat/lon)")
            break
    
    # 4. SE NÃO TEM CENTROIDE, BUSCAR LAT/LON SEPARADAS
    if not tem_centroide:
        print("\n  Procurando latitude/longitude separadas...")
        
        # Latitude
        for col in df.columns:
            col_lower = str(col).lower()
            if 'lat' in col_lower and 'lon' not in col_lower:
                if validar_coluna_coordenada(df, col):
                    col_mapping['latitude'] = col
                    print(f"  ✓ latitude: '{col}'")
                    break
        
        # Longitude
        for col in df.columns:
            col_lower = str(col).lower()
            if any(palavra in col_lower for palavra in ['lon', 'lng']) and 'lat' not in col_lower:
                if validar_coluna_coordenada(df, col):
                    col_mapping['longitude'] = col
                    print(f"  ✓ longitude: '{col}'")
                    break
    
    # VERIFICAR ESSENCIAIS
    if tem_centroide:
        essenciais = ['municipio', 'centroide']
    else:
        essenciais = ['municipio', 'latitude', 'longitude']
    
    faltando = [c for c in essenciais if c not in col_mapping]
    
    if faltando:
        print(f"\n❌ Colunas essenciais faltando: {faltando}")
        return None
    
    # CRIAR DATAFRAME FINAL
    try:
        if tem_centroide:
            # Extrair lat/lon do centroide
            print("\n🔄 Extraindo coordenadas do centroide...")
            
            colunas_manter = [col_mapping['municipio'], col_mapping['centroide']]
            if 'uf' in col_mapping:
                colunas_manter.append(col_mapping['uf'])
            
            df_temp = df[colunas_manter].copy()
            
            # Renomear
            rename_dict = {
                col_mapping['municipio']: 'municipio',
                col_mapping['centroide']: 'centroide'
            }
            if 'uf' in col_mapping:
                rename_dict[col_mapping['uf']] = 'uf'
            
            df_temp = df_temp.rename(columns=rename_dict)
            
            # Extrair lat/lon
            coords = df_temp['centroide'].apply(extrair_coordenadas_centroide)
            df_temp['latitude'] = coords.apply(lambda x: x[0])
            df_temp['longitude'] = coords.apply(lambda x: x[1])
            
            # Remover coluna centroide
            df_final = df_temp.drop(columns=['centroide'])
            
            # Mostrar amostra de extração
            print("\n  Amostra de extração:")
            for i in range(min(3, len(df_temp))):
                centroide_orig = df[col_mapping['centroide']].iloc[i]
                lat = df_final['latitude'].iloc[i]
                lon = df_final['longitude'].iloc[i]
                print(f"    '{centroide_orig}' → lat={lat}, lon={lon}")
            
        else:
            # Usar lat/lon separadas
            colunas_manter = [
                col_mapping['municipio'],
                col_mapping['latitude'],
                col_mapping['longitude']
            ]
            if 'uf' in col_mapping:
                colunas_manter.append(col_mapping['uf'])
            
            df_final = df[colunas_manter].copy()
            
            rename_dict = {
                col_mapping['municipio']: 'municipio',
                col_mapping['latitude']: 'latitude',
                col_mapping['longitude']: 'longitude'
            }
            if 'uf' in col_mapping:
                rename_dict[col_mapping['uf']] = 'uf'
            
            df_final = df_final.rename(columns=rename_dict)
        
    except Exception as e:
        print(f"\n❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    print(f"\n✅ Colunas finais: {list(df_final.columns)}")
    
    # CONVERTER COORDENADAS
    print("\n🔄 Convertendo coordenadas para numérico...")
    
    df_final['latitude'] = pd.to_numeric(df_final['latitude'], errors='coerce')
    df_final['longitude'] = pd.to_numeric(df_final['longitude'], errors='coerce')
    
    # ESTATÍSTICAS
    total = len(df_final)
    lat_validas = df_final['latitude'].notna().sum()
    lon_validas = df_final['longitude'].notna().sum()
    
    print(f"\n📊 Conversão:")
    print(f"  • Total: {total:,}")
    print(f"  • Lat válidas: {lat_validas:,} ({lat_validas/total*100:.1f}%)")
    print(f"  • Lon válidas: {lon_validas:,} ({lon_validas/total*100:.1f}%)")
    
    # LIMPAR
    df_final = df_final.dropna(subset=['latitude', 'longitude'])
    
    if len(df_final) == 0:
        print("\n❌ Nenhum registro válido")
        return None
    
    # FILTRAR BRASIL
    print("\n🇧🇷 Filtrando coordenadas do Brasil...")
    antes = len(df_final)
    
    df_final = df_final[
        (df_final['latitude'] >= -34) & (df_final['latitude'] <= 6) &
        (df_final['longitude'] >= -75) & (df_final['longitude'] <= -28)
    ]
    
    print(f"  • Antes: {antes:,}")
    print(f"  • Depois: {len(df_final):,}")
    
    # REMOVER DUPLICATAS
    if 'uf' in df_final.columns:
        df_final = df_final.drop_duplicates(subset=['municipio', 'uf'], keep='first')
    else:
        df_final = df_final.drop_duplicates(subset=['municipio'], keep='first')
    
    print(f"  • Únicos: {len(df_final):,}")
    
    # NORMALIZAR
    df_final['municipio_normalizado'] = df_final['municipio'].astype(str).str.upper().str.strip()
    
    # AMOSTRA
    print("\n📋 Amostra dos dados finais:")
    print(df_final.head(5).to_string())
    
    # STATS POR UF
    if 'uf' in df_final.columns:
        print("\n📊 Top 5 estados:")
        for uf, count in df_final['uf'].value_counts().head(5).items():
            print(f"  • {uf}: {count:,}")
    
    print("\n✅ Carregamento concluído com sucesso!")
    
    return df_final


def obter_coordenadas_municipio_br(municipio, df_municipios_br, uf=None):
    """Obtém coordenadas de um município"""
    
    if df_municipios_br is None or len(df_municipios_br) == 0:
        return None
    
    try:
        municipio_norm = str(municipio).strip().upper()
        
        # Busca exata
        if 'municipio_normalizado' in df_municipios_br.columns:
            df_busca = df_municipios_br[df_municipios_br['municipio_normalizado'] == municipio_norm]
        else:
            df_busca = df_municipios_br[
                df_municipios_br['municipio'].astype(str).str.upper().str.strip() == municipio_norm
            ]
        
        # Busca parcial
        if len(df_busca) == 0:
            df_busca = df_municipios_br[
                df_municipios_br['municipio'].astype(str).str.upper().str.contains(municipio_norm, na=False, regex=False)
            ]
        
        # Filtrar por UF
        if uf and 'uf' in df_busca.columns and len(df_busca) > 0:
            df_uf = df_busca[df_busca['uf'].astype(str).str.upper() == str(uf).upper()]
            if len(df_uf) > 0:
                df_busca = df_uf
        
        if len(df_busca) > 0:
            resultado = df_busca.iloc[0]
            lat = float(resultado['latitude'])
            lon = float(resultado['longitude'])
            zoom = 11
            
            if 'capital_uf' in resultado:
                try:
                    if int(resultado['capital_uf']) == 1:
                        zoom = 10
                except:
                    pass
            
            return (lat, lon, zoom)
        
    except:
        pass
    
    return None


def tentar_carregar_municipios_coordenadas():
    """Tenta carregar de múltiplos locais"""
    import os
    
    caminhos = [
        '../../Data/Raw/municipios_br.csv',
        '../../Data/Processed/municipios_br.csv',
        'municipios_br.csv',
    ]
    
    print("\n🔍 Procurando municipios_br.csv...")
    
    for caminho in caminhos:
        if os.path.exists(caminho):
            print(f"✓ Encontrado: {caminho}")
            return carregar_municipios_coordenadas(caminho)
        else:
            print(f"✗ Não: {caminho}")
    
    print("\n⚠️ Arquivo não encontrado - usando fallback")
    return None


def testar_municipios_comuns(df_municipios_br):
    """Testa municípios comuns"""
    if df_municipios_br is None:
        return
    
    print("\n" + "="*70)
    print("TESTE DE MUNICÍPIOS".center(70))
    print("="*70)
    
    testes = ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Curitiba', 'Belo Horizonte']
    
    for mun in testes:
        coords = obter_coordenadas_municipio_br(mun, df_municipios_br)
        if coords:
            lat, lon, zoom = coords
            print(f"  ✓ {mun}: ({lat:.4f}, {lon:.4f})")
        else:
            print(f"  ✗ {mun}: não encontrado")
    
    print("="*70)


def testar_cobertura_municipios(df_municipios_br, lista_municipios, limite=50):
    """Testa cobertura"""
    if df_municipios_br is None:
        return None
    
    encontrados = sum(1 for m in lista_municipios[:limite] 
                        if obter_coordenadas_municipio_br(m, df_municipios_br))
    
    print(f"\n📊 Cobertura: {encontrados}/{limite} ({encontrados/limite*100:.1f}%)")
    
    return {'encontrados': encontrados, 'total': limite}


__all__ = [
    'carregar_municipios_coordenadas',
    'obter_coordenadas_municipio_br',
    'tentar_carregar_municipios_coordenadas',
    'testar_cobertura_municipios',
    'testar_municipios_comuns',
    'extrair_coordenadas_centroide'
]