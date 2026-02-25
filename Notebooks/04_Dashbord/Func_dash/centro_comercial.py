import pandas as pd
import plotly.graph_objects as go

def mapaCalor(path_csv, lat_col="latitude", lon_col="longitude", return_html=False, amostra=5000):
    """
    Gera um mapa de calor interativo com zoom habilitado por touchpad.
    """

    # --- Carrega dataset ---
    df = pd.read_csv(path_csv)
    print(f" Dataset carregado: {len(df):,} estabelecimentos")

    # --- Amostragem opcional ---
    if len(df) > amostra:
        df = df.sample(amostra, random_state=42)
        print(f" Amostra utilizada: {amostra:,} pontos")

    # --- Centro e zoom inicial ---
    centro = {"lat": -14.2350, "lon": -51.9253}  
    zoom = 2.7  

    # --- Figura ---
    fig = go.Figure()

    # --- Heatmap ---
    fig.add_trace(go.Densitymapbox(
        lat=df[lat_col],
        lon=df[lon_col],
        radius=25,
        colorscale=[
            [0.0, "rgba(50, 50, 150, 0)"],
            [0.2, "rgba(100, 80, 200, 0.3)"],
            [0.4, "rgba(150, 30, 250, 0.5)"],
            [0.6, "rgba(255, 80, 80, 0.8)"],
            [0.8, "rgba(255, 40, 40, 0.9)"],
            [1.0, "rgba(255, 0, 0, 1.0)"]
        ],
        showscale=False,
        hoverinfo='skip',
        name='',
        showlegend=False
    ))

    # --- Pontos individuais ---
    fig.add_trace(go.Scattermapbox(
        lat=df[lat_col],
        lon=df[lon_col],
        mode="markers",
        marker=dict(size=3, color="rgba(255,255,255,0.6)", opacity=0.5),
        hovertemplate="<b>📍 Estabelecimento</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        name='',
        showlegend=False
    ))

    # --- Layout ---
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=centro,
            zoom=zoom,
            accesstoken=None
        ),
        height=725,
        margin=dict(r=0, t=0, l=0, b=0, pad=0),
        paper_bgcolor="rgba(10,10,20,1)",
        plot_bgcolor="rgba(10,10,20,1)",
        showlegend=False,
        hovermode='closest',
        hoverlabel=dict(
            bgcolor="#1a1a2e",
            font_size=12,
            font_color="#e0e0e0"
        ),
        dragmode='zoom',  # Ativa interação de zoom
        modebar=dict(
            bgcolor="rgba(20, 20, 30, 0.9)",
            color="#667eea",
            activecolor="#764ba2",
        )
    )

    fig.update_annotations(visible=False)

    # --- Configuração interativa ---
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True,
        'scrollZoom': True,  # 👈 ***permite zoom via rolagem e touchpad***
        'doubleClick': 'reset',  # duplo clique reseta zoom
        'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines']
    }

    # --- Retorna HTML ou figura ---
    if return_html:
        html = fig.to_html(include_plotlyjs='cdn', full_html=False, config=config, div_id='mapa-calor')
        return html

    return fig