import pandas as pd 
import folium
from folium import plugins

def mapaLoja(path_excel):
    """
    Gera um mapa Folium leve das lojas e retorna o HTML do mapa
    """
    df = pd.read_excel(path_excel, engine='openpyxl')
    df_clean = df.dropna(subset=['Latitude', 'Longitude'])

    # Mapa base mais leve
    mapa = folium.Map(
        location=[-15.7801, -47.9292], 
        zoom_start=4, 
        tiles='CartoDB positron',  # Tile mais leve
        prefer_canvas=True  # Renderização mais rápida
    )

    # TODOS OS PONTOS AZUIS SEM ÍCONE
    for _, row in df_clean.iterrows():
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 280px; font-size: 11px;">
            <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 14px;">{row['HUB']}</h4>
            <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 2px 0;"><b>Empresa:</b></td><td style="padding: 2px 0;">{row['EMPRESA']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Cidade:</b></td><td style="padding: 2px 0;">{row['CIDADE']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Capital:</b></td><td style="padding: 2px 0;">{row['CAPITAL']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Região:</b></td><td style="padding: 2px 0;">{row['REGIÃO']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>UF:</b></td><td style="padding: 2px 0;">{row['UF']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>CEP:</b></td><td style="padding: 2px 0;">{row['CEP']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Endereço:</b></td><td style="padding: 2px 0;">{row['ENDEREÇO ATUAL']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Acessibilidade:</b></td><td style="padding: 2px 0;">{row['Acessibilidade']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Supervisão:</b></td><td style="padding: 2px 0;">{row['SUPERVISÃO']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>E-mail:</b></td><td style="padding: 2px 0;">{row['E-MAIL SUPERVISÃO']}</td></tr>
                <tr><td style="padding: 2px 0;"><b>Telefone:</b></td><td style="padding: 2px 0;">{row['TELEFONE LOJA']}</td></tr>
            </table>
        </div>
        """
        
        # CÍRCULO AZUL SIMPLES (SEM ÍCONE)
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=6,  # Tamanho do círculo
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🏪 {row['HUB']} - {row['CIDADE']}/{row['UF']}",
            color='#3b82f6',  # Borda azul
            fill=True,
            fillColor='#3b82f6',  # Preenchimento azul
            fillOpacity=0.8,
            weight=2
        ).add_to(mapa)

    # TÍTULO REMOVIDO
    # title_html = '''...'''  # COMENTADO
    # mapa.get_root().html.add_child(folium.Element(title_html))  # COMENTADO
    
    # Plugins otimizados
    plugins.Fullscreen(
        title='Tela Cheia',
        title_cancel='Sair',
        force_separate_button=True
    ).add_to(mapa)
    
    return mapa._repr_html_()

# Uso
mapa_lojahtml = mapaLoja("../../Data/Raw/endereco_lojas_2025.xlsx")