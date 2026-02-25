import pandas as pd
import plotly.express as px


def graficoTop10Populacao(path_excel, top_n=10, return_html=False):
    """
    Gera um gráfico de barras interativo com os estados mais populosos do Brasil.
    
    Parâmetros:
    -----------
    path_excel : str
        Caminho para o arquivo Excel com dados de população (populacao.xls)
    top_n : int, opcional (padrão=10)
        Número de estados a exibir no ranking
    return_html : bool, opcional (padrão=False)
        Se True, retorna HTML responsivo com suporte a tema claro/escuro
        Se False, retorna objeto fig do Plotly
    
    Retorna:
    --------
    plotly.graph_objects.Figure ou str (HTML)
    
    Exemplo de uso:
    ---------------
    # Retornar figura Plotly
    fig = graficoTop10Populacao('../../Data/Raw/populacao.xls')
    fig.show()
    
    # Retornar HTML para embed
    html = graficoTop10Populacao('../../Data/Raw/populacao.xls', return_html=True)
    """
    
    # --- LEITURA E PREPARAÇÃO DOS DADOS ---
    df = pd.read_excel(path_excel, skiprows=1, engine='xlrd')
    
    # Renomear colunas
    df = df.rename(columns={
        'BRASIL E UNIDADES DA FEDERAÇÃO': 'Regiao', 
        'POPULAÇÃO ESTIMADA': 'Populacao'
    })
    
    # Validação
    if 'Regiao' not in df.columns or 'Populacao' not in df.columns:
        raise ValueError("Colunas 'Regiao' e 'Populacao' não encontradas no arquivo")
    
    # Extrair total do Brasil
    total_brasil_row = df.loc[df['Regiao'] == 'Brasil', 'Populacao']
    if total_brasil_row.empty:
        raise ValueError("Linha 'Brasil' não encontrada no dataset")
    total_brasil = total_brasil_row.values[0]
    
    # Filtrar apenas estados (remover Brasil e regiões)
    regioes_remover = ['Brasil', 'Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']
    df_estados = df[~df['Regiao'].isin(regioes_remover)].copy()
    
    # Ordenar por população (decrescente) e pegar top N
    df_top = df_estados.nlargest(top_n, 'Populacao').reset_index(drop=True)
    
    # --- CRIAÇÃO DO GRÁFICO ---
    fig = px.bar(
        df_top,
        x='Regiao',
        y='Populacao',
        color='Regiao',
        text='Populacao'
    )
    
    # Formatar texto nas barras
    fig.update_traces(
        texttemplate='%{text:.3s}',
        textposition='outside',
        textfont=dict(size=11, color='#2C3E50', family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>População: %{y:,.0f}<extra></extra>'
    )
    
    # --- LAYOUT GERAL ---
    fig.update_layout(
        title={
            'text': f'Top {top_n} Estados Mais Populosos',
            'y': 0.95,
            'x': 0.43,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#2C3E50', family='Arial Black')
        },
        
        annotations=[
            dict(
                text='<b style="font-size:18px; color:#2C3E50">BRASIL</b>',
                x=0.5, y=0.58,
                xref='paper', yref='paper',
                font=dict(family='Arial Black'),
                showarrow=False
            ),
            dict(
                text=f'<b style="font-size:32px; color:#E74C3C">{total_brasil/1_000_000:.1f}M</b>',
                x=0.5, y=0.50,
                xref='paper', yref='paper',
                font=dict(family='Arial Black'),
                showarrow=False
            ),
            dict(
                text='<span style="font-size:13px; color:#34495E">habitantes</span>',
                x=0.5, y=0.42,
                xref='paper', yref='paper',
                font=dict(family='Arial'),
                showarrow=False
            ),
        ],
        
        height=750,
        
        # Legenda aprimorada
        legend=dict(
            title='',
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.08,
            font=dict(size=14, family='Arial', color='#2C3E50'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#BDC3C7',
            borderwidth=1,
            itemsizing='trace',
            traceorder='normal',
            tracegroupgap=3
        ),
        
        paper_bgcolor='#ECF0F1',
        plot_bgcolor='#ECF0F1',
        margin=dict(l=80, r=250, t=100, b=60),
        font=dict(size=13, family='Arial', color='#2C3E50'),
        
        showlegend=True,
        hovermode='x unified'
    )
    
    # --- EIXOS ---
    fig.update_xaxes(
        title_text="<b>Estado</b>",
        title_standoff=10,
        showgrid=False,
        showline=True,
        linewidth=1.5,
        linecolor='#BDC3C7',
        tickfont=dict(size=11, color='#2C3E50'),
        title_font=dict(size=13, color='#2C3E50')
    )
    
    fig.update_yaxes(
        title_text="<b>População</b>",
        title_standoff=10,
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(189, 195, 199, 0.3)',
        showline=True,
        linewidth=1.5,
        linecolor='#BDC3C7',
        tickformat=',',
        separatethousands=True,
        tickfont=dict(size=11, color='#2C3E50'),
        title_font=dict(size=13, color='#2C3E50')
    )
    
    # --- RETORNO ---
    if return_html:
        html = fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={
                'displayModeBar': False,
                'responsive': True,
                'displaylogo': False
            }
        )
        
        # CSS para tema escuro
        html = f"""
<style>
/* ========== TEMA ESCURO ========== */
body.dark-theme .js-plotly-plot .plotly {{
    color: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly text {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .xtitle,
body.dark-theme .js-plotly-plot .plotly .ytitle {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .xtick text,
body.dark-theme .js-plotly-plot .plotly .ytick text {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .gridlayer line {{
    stroke: rgba(255, 255, 255, 0.15) !important;
}}

body.dark-theme .js-plotly-plot .plotly .xaxislayer-above line,
body.dark-theme .js-plotly-plot .plotly .yaxislayer-above line {{
    stroke: rgba(255, 255, 255, 0.3) !important;
}}

body.dark-theme .js-plotly-plot .plotly .legend {{
    fill: rgba(30, 30, 46, 0.9) !important;
}}

body.dark-theme .js-plotly-plot .plotly .legend .bg {{
    fill: rgba(30, 30, 46, 0.9) !important;
}}

body.dark-theme .js-plotly-plot .plotly .legend text {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .legend .outline {{
    stroke: rgba(255, 255, 255, 0.2) !important;
}}

body.dark-theme .js-plotly-plot .plotly .hoverlayer .hovertext path {{
    fill: rgba(30, 30, 46, 0.95) !important;
    stroke: rgba(255, 255, 255, 0.2) !important;
}}

body.dark-theme .js-plotly-plot .plotly .hoverlayer .hovertext text {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .annotation text {{
    fill: #e0e0e0 !important;
}}

body.dark-theme .js-plotly-plot .plotly .bg {{
    fill: rgba(0, 0, 0, 0) !important;
}}
</style>
{html}
"""
        
        return html
    
    return fig


__all__ = ['graficoTop10Populacao']