# BAH - Business Analytics Hub

Dashboard interativo para análise demográfica e imobiliária com visualizações geográficas avançadas.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-0.14+-77B829?style=for-the-badge&logo=leaflet&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.0+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## Sobre o Projeto

**BAH (Business Analytics Hub)** é uma plataforma analítica desenvolvida para auxiliar na tomada de decisões estratégicas através de análises demográficas e imobiliárias. O sistema oferece visualizações interativas e insights baseados em dados reais de todo o Brasil.

### Principais Recursos

- Análise demográfica detalhada por faixa etária e região
- Mapeamento georreferenciado de imóveis e estabelecimentos
- Visualização de densidade populacional através de mapas de calor
- Projeções demográficas para planejamento estratégico
- Interface responsiva com tema claro/escuro

---

## Funcionalidades

### Análise Demográfica
- Busca inteligente de municípios com autocomplete
- Configuração de raio de análise de 10 a 200 km
- Filtros personalizáveis por faixas etárias
- Visualização de densidade populacional em mapas interativos

### Mapeamento de Lojas
- Geolocalização de todas as unidades
- Informações detalhadas por estabelecimento
- Dados de contato e acessibilidade
- Coordenadas geográficas precisas

### Visualizações
- Mapas interativos com Folium
- Gráficos dinâmicos com Plotly
- Mapas de calor para análise de concentração
- Dashboard customizável

---

## Estrutura do Projeto

```
BAH/
│
├── Data/
│   ├── Raw/                                    # Dados originais
│   │   ├── endereco_lojas_2025.xlsx           # Endereços das lojas
│   │   ├── populacao.xls                      # Dados populacionais
│   │   ├── municipios_br.csv                  # Lista de municípios brasileiros
│   │   ├── centros_comerciais_brasil.csv      # Centros comerciais
│   │   ├── projecoes.xlsx                     # Projeções demográficas
│   │   ├── idade.csv                          # Dados de faixa etária
│   │   ├── imovel_br.csv                      # Imóveis Brasil
│   │   ├── imovel_sp.csv                      # Imóveis São Paulo
│   │   ├── info_br_geral.csv                  # Informações gerais
│   │   ├── acesso_financeiro.xlsx             # Dados de acesso financeiro
│   │   └── agencias.xlsx                      # Dados de agências
│   │
│   ├── Interim/                                # Dados intermediários
│   │   └── idade_corrigido.csv
│   │
│   └── Processed/                              # Dados tratados
│       ├── imovel_tratado.csv
│       ├── municipios_idade_coordenadas.csv
│       ├── idade_tratado.csv
│       ├── acesso_financeiro_tratado.csv
│       └── agencias_tratado.csv
│
├── Notebooks/
│   ├── 01_Exploracao/                          # Análise exploratória de dados
│   │   ├── acesso_financeiro.ipynb
│   │   ├── agencias.ipynb
│   │   ├── api_overpass.ipynb
│   │   ├── centro_comerciais.ipynb
│   │   ├── idade.ipynb
│   │   ├── imoveis.ipynb
│   │   └── municipios.ipynb
│   │
│   ├── 02_Tratamento/                          # Processamento e limpeza
│   │   ├── agencia_localizacao.ipynb
│   │   ├── idade_localizao.ipynb
│   │   └── pesquisa_hub.ipynb
│   │
│   ├── 03_Analise/                             # Análises avançadas
│   │   ├── hubs.ipynb
│   │   ├── populacao.ipynb
│   │   └── projecao.ipynb
│   │
│   └── 04_Dashbord/                            # Dashboard e visualizações
│       ├── Func_dash/                          # Módulos do dashboard
│       │   ├── populacao/
│       │   ├── analise_demografica_dashboard.py
│       │   ├── centro_comercial.py
│       │   ├── funcmapa.py
│       │   ├── imoveis.py
│       │   ├── mapaloja.py
│       │   ├── municipios_coordenadas.py
│       │   ├── populacao.py
│       │   ├── projecoes.py
│       │   ├── regra_calor.py
│       │   ├── regra_idade.py
│       │   └── __init__.py
│       │
│       ├── dashboard.html
│       ├── dashboardi.html
│       ├── dashboard_exemplo_campinas.html
│       └── final.ipynb
│
└── Docs/                                       # Documentação do projeto
```

---

## Tecnologias Utilizadas

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)

- **Python 3.8+** - Linguagem principal
- **Pandas** - Manipulação e análise de dados
- **NumPy** - Computação numérica
- **OpenPyXL** - Processamento de arquivos Excel

### Visualização
![Folium](https://img.shields.io/badge/Folium-77B829?style=flat-square&logo=leaflet&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=flat-square&logo=python&logoColor=white)

- **Folium** - Mapas interativos
- **Plotly** - Gráficos dinâmicos
- **Matplotlib** - Visualizações estáticas

### Frontend
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Font Awesome](https://img.shields.io/badge/Font_Awesome-339AF0?style=flat-square&logo=fontawesome&logoColor=white)

- **HTML5/CSS3** - Estrutura e estilização
- **JavaScript (ES6+)** - Interatividade
- **Font Awesome** - Biblioteca de ícones

---

## Instalação

### Pré-requisitos

![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Jupyter Notebook
- Git

### Passos de Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/bah-analytics.git
cd bah-analytics
```

**2. Crie um ambiente virtual**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install pandas folium plotly openpyxl jupyter numpy matplotlib
```

**4. Inicie o Jupyter Notebook**

```bash
jupyter notebook
```

**5. Navegue até o dashboard**

```
Notebooks/04_Dashbord/final.ipynb
```

---

## Uso

### Geração do Dashboard

```python
# Importe os módulos necessários
from Func_dash import *

# Execute a célula de geração
# O arquivo dashboard.html será criado automaticamente
```

### Visualização

Abra o arquivo `dashboard.html` gerado no seu navegador preferido.

---

## Exemplos de Uso

### Análise Regional

```python
# Análise demográfica de Campinas com raio de 20km
resultado = funcmapa(
    municipio="Campinas - SP",
    raio_km=20,
    faixas_etarias=['80 a 84 anos', '85 a 89 anos', '90 a 94 anos']
)
```

### Mapeamento de Estabelecimentos

```python
# Gerar mapa interativo de lojas
mapa_lojas = mapaLoja("../../Data/Raw/endereco_lojas_2025.xlsx")
```

### Análise de Projeções

```python
# Visualizar projeções demográficas
projecoes = mapaProjecoes(
    path_excel='../../Data/Raw/projecoes.xlsx',
    return_html=True
)
```

---

## Datasets

### Dados Brutos (Raw)

| Arquivo | Descrição | Formato |
|---------|-----------|---------|
| `endereco_lojas_2025.xlsx` | Localização de estabelecimentos | Excel |
| `populacao.xls` | Dados populacionais do IBGE | Excel |
| `municipios_br.csv` | Lista completa de municípios | CSV |
| `centros_comerciais_brasil.csv` | Centros comerciais mapeados | CSV |
| `projecoes.xlsx` | Projeções demográficas | Excel |
| `idade.csv` | Distribuição por faixa etária | CSV |
| `imovel_br.csv` | Base de imóveis nacional | CSV |
| `imovel_sp.csv` | Base de imóveis São Paulo | CSV |

### Dados Processados (Processed)

| Arquivo | Descrição |
|---------|-----------|
| `imovel_tratado.csv` | Dados imobiliários consolidados e limpos |
| `municipios_idade_coordenadas.csv` | Dados demográficos com geolocalização |
| `idade_tratado.csv` | Distribuição etária processada |
| `acesso_financeiro_tratado.csv` | Dados de acesso a serviços financeiros |
| `agencias_tratado.csv` | Informações de agências bancárias |

---

## Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

### Diretrizes

- Mantenha o código limpo e bem documentado
- Siga as convenções PEP 8 para Python
- Adicione testes para novas funcionalidades
- Atualize a documentação quando necessário

---

## Roadmap

**Versão 2.0**
- [ ] API REST para integração externa
- [ ] Exportação de relatórios em PDF
- [ ] Sistema de notificações automáticas
- [ ] Análises preditivas com Machine Learning

**Versão 3.0**
- [ ] Aplicativo mobile
- [ ] Dashboard em tempo real
- [ ] Integração com banco de dados
- [ ] Suporte multilíngue

---

## Licença

![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

```
MIT License

Copyright (c) 2025 BAH - Business Analytics Hub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## Autores

**Equipe BAH**
- Desenvolvimento e Análise de Dados
- ![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat-square&logo=github&logoColor=white) [BAH Analytics](https://github.com/seu-usuario/bah-analytics)

---

## Agradecimentos

- **IBGE** - Dados demográficos e geográficos
- **OpenStreetMap** - Dados de geolocalização
- **Folium** - Biblioteca de mapas interativos
- **Plotly** - Visualizações dinâmicas
- **Pandas** - Análise de dados

---

<div align="center">

### BAH - Business Analytics Hub

**Transformando dados em decisões estratégicas**

[![GitHub stars](https://img.shields.io/github/stars/seu-usuario/bah-analytics?style=social)](https://github.com/seu-usuario/bah-analytics/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/seu-usuario/bah-analytics?style=social)](https://github.com/seu-usuario/bah-analytics/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/seu-usuario/bah-analytics?style=social)](https://github.com/seu-usuario/bah-analytics/watchers)

---

Desenvolvido com dedicação pela equipe BAH

</div>
