# Func_dash/populacao/__init__.py
import pandas as pd
import plotly.express as px


def graficoTop10Populacao(path_excel, top_n=10, return_html=False):
    """Gera um gráfico de barras interativo com os estados mais populosos do Brasil."""
    
    df = pd.read_excel(path_excel, skiprows=1, engine='xlrd')
    df = df.rename(columns={
        'BRASIL E UNIDADES DA FEDERAÇÃO': 'Regiao', 
        'POPULAÇÃO ESTIMADA': 'Populacao'
    })
    
    if 'Regiao' not in df.columns or 'Populacao' not in df.columns:
        raise ValueError("Colunas 'Regiao' e 'Populacao' não encontradas")
    
    total_brasil = df.loc[df['Regiao'] == 'Brasil', 'Populacao'].values[0]
    
    regioes_remover = ['Brasil', 'Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']
    df_estados = df[~df['Regiao'].isin(regioes_remover)].copy()
    df_top = df_estados.nlargest(top_n, 'Populacao').reset_index(drop=True)
    
    fig = px.bar(df_top, x='Regiao', y='Populacao', color='Regiao', text='Populacao')
    
    fig.update_traces(
        texttemplate='%{text:.3s}', textposition='outside',
        textfont=dict(size=11, color='#2C3E50', family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>População: %{y:,.0f}<extra></extra>'
    )
    
    fig.update_layout(
        title={'text': f'Top {top_n} Estados Mais Populosos', 'y': 0.95, 'x': 0.43,
               'xanchor': 'center', 'yanchor': 'top',
               'font': dict(size=24, color='#2C3E50', family='Arial Black')},
        annotations=[
            dict(text='<b style="font-size:18px; color:#2C3E50">BRASIL</b>',
                 x=0.5, y=0.58, xref='paper', yref='paper', showarrow=False),
            dict(text=f'<b style="font-size:32px; color:#E74C3C">{total_brasil/1_000_000:.1f}M</b>',
                 x=0.5, y=0.50, xref='paper', yref='paper', showarrow=False),
            dict(text='<span style="font-size:13px; color:#34495E">habitantes</span>',
                 x=0.5, y=0.42, xref='paper', yref='paper', showarrow=False),
        ],
        height=750,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.08,
                    font=dict(size=14, family='Arial', color='#2C3E50'),
                    bgcolor='rgba(255,255,255,0.8)', bordercolor='#BDC3C7', borderwidth=1),
        paper_bgcolor='#ECF0F1', plot_bgcolor='#ECF0F1',
        margin=dict(l=80, r=250, t=100, b=60),
        showlegend=True, hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="<b>Estado</b>", showgrid=False, showline=True, linecolor='#BDC3C7')
    fig.update_yaxes(title_text="<b>População</b>", showgrid=True, gridcolor='rgba(189,195,199,0.3)')
    
    if return_html:
        html = fig.to_html(include_plotlyjs='cdn', full_html=False,
                           config={'displayModeBar': False, 'responsive': True})
        return f'<style>body.dark-theme .js-plotly-plot .plotly text {{fill: #e0e0e0 !important;}}</style>{html}'
    
    return fig


__all__ = ['graficoTop10Populacao']