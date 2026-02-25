import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def mapaProjecoes(path_excel, local='Brasil', return_html=False):
    """
    Gera um gráfico interativo Plotly com projeções populacionais.
    """
    
    # --- Leitura ---
    df = pd.read_excel(path_excel, skiprows=5, engine='openpyxl')
    
    # --- Preparação dos dados ---
    def preparar_dados_crescimento(df, local='Brasil'):
        """Prepara e pivota os dados de crescimento populacional."""
        coluna_local = next((col for col in df.columns if col.upper() == 'LOCAL'), None)
        
        if coluna_local is None:
            raise ValueError("Coluna 'LOCAL' não encontrada no DataFrame.")
        
        df_local = df[df[coluna_local] == local].copy()
        if df_local.empty:
            raise ValueError(f"Nenhum dado encontrado para o local '{local}'")
        
        colunas_anos = sorted([
            int(col) for col in df_local.columns 
            if isinstance(col, (int, float)) or (isinstance(col, str) and col.isdigit())
        ])
        
        dados_crescimento = []
        for _, row in df_local.iterrows():
            sexo = row['SEXO']
            for ano in colunas_anos:
                dados_crescimento.append({
                    'Ano': ano,
                    'Sexo': sexo,
                    'Populacao': row[ano]
                })
        
        df_pivot = pd.DataFrame(dados_crescimento)
        df_resultado = df_pivot.pivot_table(
            index='Ano',
            columns='Sexo',
            values='Populacao',
            aggfunc='sum'
        )
        df_resultado.columns.name = None
        return df_resultado

    df_crescimento = preparar_dados_crescimento(df, local)
    
    # --- Cálculos ---
    taxa_crescimento = df_crescimento['Ambos'].pct_change() * 100
    percentual_mulheres = (df_crescimento['Mulheres'] / df_crescimento['Ambos']) * 100
    
    # --- Configuração da figura ---
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.55, 0.45],
        subplot_titles=('', ''),
        vertical_spacing=0.12,
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )
    
    # Paleta de cores
    cores = {
        'ambos': '#6366f1',
        'homens': '#3b82f6',
        'mulheres': '#ec4899',
        'crescimento_pos': '#10b981',
        'crescimento_neg': '#ef4444'
    }
    
    # ===== GRÁFICO PRINCIPAL =====
    fig.add_trace(go.Scatter(
        x=df_crescimento.index, 
        y=df_crescimento['Ambos'],
        name='População Total',
        line=dict(color=cores['ambos'], width=3),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.15)',
        hovertemplate='<b>%{x}</b><br>População: %{y:,.0f}<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_crescimento.index, 
        y=df_crescimento['Homens'],
        name='Homens',
        line=dict(color=cores['homens'], width=2.5, dash='dash'),
        hovertemplate='<b>%{x}</b><br>Homens: %{y:,.0f}<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_crescimento.index, 
        y=df_crescimento['Mulheres'],
        name='Mulheres',
        line=dict(color=cores['mulheres'], width=2.5, dash='dot'),
        hovertemplate='<b>%{x}</b><br>Mulheres: %{y:,.0f}<extra></extra>'
    ), row=1, col=1)
    
    # Anotações nos extremos
    anos_destaque = [df_crescimento.index.min(), df_crescimento.index.max()]
    for i, ano in enumerate(anos_destaque):
        fig.add_annotation(
            x=ano,
            y=df_crescimento.loc[ano, 'Ambos'],
            text=f"<b>{df_crescimento.loc[ano, 'Ambos']/1e6:.1f}M</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2.5,
            arrowcolor='#ffffff',
            ax=60 if i == 0 else -60,
            ay=-45,
            font=dict(size=12, color='#1f2937', family='Arial Black'),
            bgcolor='#ffffff',
            bordercolor=cores['ambos'],
            borderwidth=2.5,
            borderpad=6,
            opacity=1,
            row=1, col=1
        )
    
    # ===== GRÁFICO INFERIOR =====
    cores_taxa = [
        cores['crescimento_pos'] if x >= 0 else cores['crescimento_neg'] 
        for x in taxa_crescimento.values
    ]
    
    fig.add_trace(go.Bar(
        x=taxa_crescimento.index, 
        y=taxa_crescimento.values,
        name='Crescimento Anual',
        marker=dict(color=cores_taxa, line=dict(width=0)),
        hovertemplate='<b>%{x}</b><br>Crescimento: %{y:.2f}%<extra></extra>'
    ), row=2, col=1, secondary_y=False)
    
    fig.add_trace(go.Scatter(
        x=percentual_mulheres.index,
        y=percentual_mulheres.values,
        name='% Mulheres',
        line=dict(color=cores['mulheres'], width=3),
        hovertemplate='<b>%{x}</b><br>Mulheres: %{y:.2f}%<extra></extra>'
    ), row=2, col=1, secondary_y=True)
    
    # Linha de paridade (50%)
    fig.add_hline(
        y=50, 
        line_dash="dash", 
        line_color="rgba(200, 200, 200, 0.6)", 
        line_width=2,
        row=2, col=1, 
        secondary_y=True
    )
    
    # ===== LAYOUT GERAL =====
    fig.update_layout(
        height=700,  # Altura igual ao mapa de calor
        showlegend=True,
        hovermode='x unified',
        template='plotly_dark',
        
        # LEGENDA NO TOPO
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.46,  
            font=dict(size=11, color='#e0e0e0'),
            bgcolor='rgba(30, 30, 46, 0.9)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1,
            itemsizing='constant',
            traceorder='normal'
        ),
        
        font=dict(
            family="Arial, sans-serif", 
            size=11,
            color='#e0e0e0'
        ),
        
        # MARGENS MÍNIMAS PARA PREENCHER A TELA
        margin=dict(t=70, b=50, l=60, r=80),  # Margens reduzidas
        
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # ===== EIXOS =====
    # Eixo X superior
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(255, 255, 255, 0.1)',
        showline=True,
        linewidth=1.5,
        linecolor='rgba(255, 255, 255, 0.3)',
        row=1, col=1, 
        tickfont=dict(size=11, color='#e0e0e0')
    )
    
    # Eixo Y - População
    fig.update_yaxes(
        title_text="<b>População</b>", 
        title_standoff=8,
        row=1, col=1, 
        showgrid=True, 
        gridwidth=1,
        gridcolor='rgba(255, 255, 255, 0.1)',
        tickformat=',',
        separatethousands=True,
        title_font=dict(size=12, color='#e0e0e0'),
        tickfont=dict(size=10, color='#e0e0e0'),
        showline=True,
        linewidth=1.5,
        linecolor='rgba(255, 255, 255, 0.3)'
    )
    
    # Eixo X inferior
    fig.update_xaxes(
        title_text="<b>Ano</b>", 
        title_standoff=8,
        row=2, col=1, 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(255, 255, 255, 0.1)',
        showline=True,
        linewidth=1.5,
        linecolor='rgba(255, 255, 255, 0.3)',
        title_font=dict(size=12, color='#e0e0e0'),
        tickfont=dict(size=10, color='#e0e0e0')
    )
    
    # Eixo Y esquerdo - Taxa
    fig.update_yaxes(
        title_text="<b>Taxa (%)</b>", 
        title_standoff=8,
        row=2, col=1, 
        showgrid=True, 
        gridwidth=1,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='rgba(255, 255, 255, 0.3)',
        title_font=dict(size=12, color='#e0e0e0'),
        tickfont=dict(size=10, color='#e0e0e0'),
        secondary_y=False,
        showline=True,
        linewidth=1.5,
        linecolor='rgba(255, 255, 255, 0.3)'
    )
    
    # Eixo Y direito - Proporção
    fig.update_yaxes(
        title_text="<b>Proporção (%)</b>", 
        title_standoff=8,
        row=2, col=1, 
        showgrid=False,
        range=[48.5, 51.5],
        title_font=dict(size=12, color='#e0e0e0'),
        tickfont=dict(size=10, color='#e0e0e0'),
        secondary_y=True,
        showline=True,
        linewidth=1.5,
        linecolor='rgba(255, 255, 255, 0.3)'
    )
    
    # --- Retorno ---
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
        
        # CSS para tema claro
        html = f"""
<style>
/* ========== TEMA CLARO ========== */
body.light-theme .js-plotly-plot .plotly {{
    color: #212529 !important;
}}

body.light-theme .js-plotly-plot .plotly text {{
    fill: #212529 !important;
}}

body.light-theme .js-plotly-plot .plotly .xtitle,
body.light-theme .js-plotly-plot .plotly .ytitle {{
    fill: #212529 !important;
}}

body.light-theme .js-plotly-plot .plotly .xtick text,
body.light-theme .js-plotly-plot .plotly .ytick text {{
    fill: #212529 !important;
}}

body.light-theme .js-plotly-plot .plotly .gridlayer line {{
    stroke: rgba(0, 0, 0, 0.15) !important;
}}

body.light-theme .js-plotly-plot .plotly .zerolinelayer line {{
    stroke: rgba(0, 0, 0, 0.4) !important;
}}

body.light-theme .js-plotly-plot .plotly .xaxislayer-above line,
body.light-theme .js-plotly-plot .plotly .yaxislayer-above line {{
    stroke: rgba(0, 0, 0, 0.4) !important;
}}

body.light-theme .js-plotly-plot .plotly .legend {{
    fill: rgba(255, 255, 255, 0.95) !important;
}}

body.light-theme .js-plotly-plot .plotly .legend .bg {{
    fill: rgba(255, 255, 255, 0.95) !important;
}}

body.light-theme .js-plotly-plot .plotly .legend text {{
    fill: #212529 !important;
}}

body.light-theme .js-plotly-plot .plotly .legend .outline {{
    stroke: rgba(0, 0, 0, 0.2) !important;
}}

body.light-theme .js-plotly-plot .plotly .hoverlayer .hovertext path {{
    fill: rgba(255, 255, 255, 0.95) !important;
    stroke: rgba(0, 0, 0, 0.2) !important;
}}

body.light-theme .js-plotly-plot .plotly .hoverlayer .hovertext text {{
    fill: #212529 !important;
}}
</style>
{html}
"""
        
        return html
    
    return fig