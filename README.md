# Varex

Dashboard interativo desenvolvido em Python com Streamlit para analise de vendas no varejo. O projeto foi criado com foco em leitura executiva, apoio a decisao e apresentacao de indicadores de negocio de forma visual e objetiva.

## O que o projeto faz

O `Varex` simula um painel de inteligencia comercial para acompanhamento de vendas, lucro e margem. A aplicacao permite analisar uma base padrao gerada automaticamente ou uma base historica em CSV, exibindo metricas, filtros, graficos e sugestoes de acao comercial.

Principais entregas do dashboard:

- resumo executivo com faturamento, lucro, margem media, volume e ticket medio;
- leitura visual da performance por tempo, categoria e produto;
- mineracao dinamica com consultas prontas de negocio;
- diagnostico de risco e oportunidade por margem e relevancia;
- projecao simples de lucro para os proximos 7 dias;
- recomendacoes comerciais para campanhas e destaque de vitrine.

## Tecnologias utilizadas

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Requests

## Estrutura principal

- `dashboard.py`: aplicacao principal do dashboard.
- `vendas_brutas.csv`: base historica usada no modo de analise com CSV.
- `requirements.txt`: dependencias do projeto.

## Como funciona

Ao iniciar a aplicacao, o usuario escolhe entre:

- `Base padrao`: usa uma base simulada gerada pelo proprio sistema.
- `Base historica`: usa a base `vendas_brutas.csv`.

Depois disso, o usuario pode aplicar filtros por:

- categoria;
- produto;
- periodo;
- busca textual;
- simulacao de reajuste medio de preco.

Com esses filtros, o painel recalcula automaticamente os indicadores e atualiza os graficos em tempo real.

## Principais analises do painel

### 1. Resumo Executivo

Mostra os KPIs principais para uma leitura rapida do desempenho comercial:

- faturamento total;
- lucro real;
- margem media;
- volume vendido;
- ticket medio;
- lucro projetado com simulacao.

### 2. Resumo Visual

Exibe graficos para facilitar a interpretacao:

- evolucao de faturamento e lucro no tempo;
- comparativo por categoria;
- participacao no faturamento;
- relacao entre volume, margem e relevancia;
- heatmap por dia e categoria;
- pareto dos produtos mais relevantes.

### 3. Mineracao Dinamica

Entrega consultas prontas para leitura de negocio, como:

- produtos com maior faturamento;
- produtos com menor margem;
- produtos para campanha imediata;
- categorias mais lucrativas;
- historico diario resumido.

### 4. Diagnostico para Tomada de Decisao

Ajuda a identificar:

- itens com margem pressionada;
- produtos que merecem escala ou protecao;
- acoes sugeridas por classe ABC;
- tendencia de lucro futuro.

### 5. Central de Acionamento Comercial

Transforma os dados em sugestoes praticas, como:

- campanhas de escoamento;
- itens para destaque de vitrine;
- leitura comercial mais orientada a acao.

## Regras e tratamento dos dados

O sistema faz um tratamento automatico da base para ficar mais robusto:

- aceita pequenas variacoes em nomes de colunas;
- interpreta datas em formatos comuns;
- calcula custo, faturamento, lucro e margem;
- gera classificacao ABC por relevancia;
- impede falhas visuais com rotulos grandes nos graficos.

## Como executar localmente

1. Abra o terminal na pasta do projeto.
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Rode a aplicacao:

```bash
python -m streamlit run dashboard.py
```

## Possiveis usos

Este projeto pode ser usado como:

- demonstracao de dashboard para hackathon;
- portfolio de Python com Streamlit;
- base para evolucao de um painel real de BI comercial;
- estudo pratico de analise de dados e visualizacao.

## Melhorias futuras

- conexao com banco de dados real;
- upload de CSV pelo proprio usuario;
- autenticacao;
- exportacao de relatorios;
- modelos preditivos mais robustos para previsao de lucro.

## Autor

Projeto desenvolvido por Natan Almeida Albuquerque como parte de aprendizado e aplicacao pratica de Python, analise de dados e visualizacao executiva. Na data de 29/04/2026
