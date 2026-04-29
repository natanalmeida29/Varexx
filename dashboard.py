"""
Projeto Final: Varex
Dashboard executivo com filtros, busca e foco em decisao.
"""

import datetime
import random
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="Varex", layout="wide", initial_sidebar_state="expanded")

ARQUIVO_CSV = Path(__file__).with_name("vendas_brutas.csv")


st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(24, 123, 205, 0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(255, 171, 63, 0.12), transparent 24%);
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #123b5d 55%, #1d6fa5 100%);
        padding: 1.5rem;
        border-radius: 22px;
        color: white;
        margin-bottom: 1rem;
    }
    .hero small {
        letter-spacing: 0.12rem;
        text-transform: uppercase;
        opacity: 0.75;
    }
    .hero h1 {
        margin: 0.4rem 0 0.7rem 0;
        font-size: 2.1rem;
        line-height: 1.1;
    }
    .hero p {
        margin: 0;
        max-width: 820px;
    }
    .insight {
        background: color-mix(in srgb, var(--background-color) 92%, white 8%);
        border: 1px solid var(--secondary-background-color);
        border-left: 5px solid #1d6fa5;
        border-radius: 18px;
        padding: 1rem;
        min-height: 140px;
    }
    .insight strong {
        display: block;
        margin: 0.3rem 0 0.5rem 0;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def moeda(valor):
    """Formata valores numericos no padrao monetario brasileiro."""
    return f"R$ {valor:,.2f}"


def normalizar_texto(valor):
    """Normaliza textos para comparacoes seguras de nomes de colunas."""
    return (
        unicodedata.normalize("NFKD", str(valor))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def quebrar_rotulo(rotulo_texto: str, limite: int = 18) -> str:
    """Quebra rotulos longos em multiplas linhas para melhorar a leitura."""
    palavras = str(rotulo_texto).split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        candidata = f"{linha_atual} {palavra}".strip()
        if len(candidata) <= limite or not linha_atual:
            linha_atual = candidata
        else:
            linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return "<br>".join(linhas)


def sugestao_campanha(produto):
    """Retorna uma sugestao de campanha estavel para cada produto."""
    opcoes = ["15% OFF", "20% OFF", "Frete Gratis", "Combo progressivo"]
    indice = sum(ord(letra) for letra in str(produto)) % len(opcoes)
    return opcoes[indice]


@st.cache_data(ttl=1800)
def carregar_dolar():
    """Busca a cotacao do dolar com fallback seguro para a demo."""
    try:
        resposta = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL", timeout=5)
        resposta.raise_for_status()
        cotacao = float(resposta.json()["USDBRL"]["bid"])
        return cotacao if cotacao > 0 else 5.00
    except (requests.exceptions.RequestException, KeyError, TypeError, ValueError):
        return 5.00


def base_produtos():
    """Define o catalogo base de produtos, categorias e custos."""
    return {
        "Camiseta Basica": ("Vestuario", 30.0, 49.9),
        "Calca Jeans": ("Vestuario", 60.0, 119.9),
        "Tenis Esportivo": ("Calcados", 120.0, 249.5),
        "Mochila Escolar": ("Acessorios", 40.0, 89.9),
        "Jaqueta Corta Vento": ("Vestuario", 90.0, 189.9),
        "Bone": ("Acessorios", 15.0, 35.0),
        "Tenis Casual": ("Calcados", 80.0, 159.9),
        "Meia Cano Alto": ("Vestuario", 5.0, 15.5),
        "Cinto de Couro": ("Acessorios", 20.0, 45.0),
        "Camisa Polo": ("Vestuario", 45.0, 89.9),
        "Bermuda Sarja": ("Vestuario", 55.0, 110.0),
        "Sapato Social": ("Calcados", 110.0, 220.0),
        "Carteira": ("Acessorios", 25.0, 59.9),
        "Oculos de Sol": ("Acessorios", 50.0, 130.0),
    }


@st.cache_data(ttl=600)
def gerar_demo():
    """Gera uma base simulada para demonstracao do dashboard."""
    random.seed(42)
    catalogo_produtos = list(base_produtos().items())
    hoje = datetime.date.today()
    linhas = []

    for i in range(1, 1501):
        nome, (categoria_nome, custo, valor) = random.choice(catalogo_produtos)
        qtd = random.randint(2, 10) if valor < 50 else random.randint(1, 5)
        linhas.append(
            {
                "Data": hoje - datetime.timedelta(days=random.randint(0, 45)),
                "ID_Venda": 5000 + i,
                "Produto": nome,
                "Categoria": categoria_nome,
                "Quantidade": qtd,
                "Valor_Unitario": valor,
                "Custo_Unitario": custo,
            }
        )

    return pd.DataFrame(linhas)


@st.cache_data(ttl=600)
def carregar_csv_local():
    """Carrega o CSV local do projeto quando ele existir."""
    if ARQUIVO_CSV.exists():
        return pd.read_csv(ARQUIVO_CSV, encoding="utf-8-sig")
    return pd.DataFrame()


def tratar_base(base_df):
    """Padroniza a base de dados e calcula os indicadores derivados."""
    catalogo = base_produtos()
    base_df = base_df.copy()
    mapa_colunas = {
        "data": "Data",
        "dt_venda": "Data",
        "id_venda": "ID_Venda",
        "id": "ID_Venda",
        "produto": "Produto",
        "item": "Produto",
        "categoria": "Categoria",
        "quantidade": "Quantidade",
        "qtd": "Quantidade",
        "qtde": "Quantidade",
        "valor_unitario": "Valor_Unitario",
        "preco_unitario": "Valor_Unitario",
        "valorunitario": "Valor_Unitario",
        "vlr_unitario": "Valor_Unitario",
        "valor_unitário": "Valor_Unitario",
        "custo_unitario": "Custo_Unitario",
        "custounitario": "Custo_Unitario",
        "custo_unitário": "Custo_Unitario",
    }
    base_df.columns = [mapa_colunas.get(normalizar_texto(col), str(col).strip()) for col in base_df.columns]

    obrigatorias = ["Data", "Produto", "Quantidade", "Valor_Unitario"]
    for nome_coluna in obrigatorias:
        if nome_coluna not in base_df.columns:
            raise ValueError(f"A base precisa conter a coluna '{nome_coluna}'.")

    if "ID_Venda" not in base_df.columns:
        base_df["ID_Venda"] = range(100000, 100000 + len(base_df))
    if "Categoria" not in base_df.columns:
        base_df["Categoria"] = base_df["Produto"].map(lambda x: catalogo.get(x, ("Outros", 0, 0))[0])
    if "Custo_Unitario" not in base_df.columns:
        base_df["Custo_Unitario"] = base_df["Produto"].map(lambda x: catalogo.get(x, ("Outros", 0, 0))[1])

    data_original = base_df["Data"].copy()
    base_df["Data"] = pd.to_datetime(base_df["Data"], errors="coerce", format="%Y-%m-%d")
    datas_invalidas = base_df["Data"].isna()
    if datas_invalidas.any():
        base_df.loc[datas_invalidas, "Data"] = pd.to_datetime(data_original[datas_invalidas], errors="coerce", dayfirst=True)

    base_df["Quantidade"] = pd.to_numeric(base_df["Quantidade"], errors="coerce")
    base_df["Valor_Unitario"] = pd.to_numeric(base_df["Valor_Unitario"], errors="coerce")
    base_df["Custo_Unitario"] = pd.to_numeric(base_df["Custo_Unitario"], errors="coerce").fillna(0)

    if not base_df.empty and base_df["Data"].isna().all():
        raise ValueError("A coluna 'Data' nao foi reconhecida. Use datas como YYYY-MM-DD ou DD/MM/YYYY.")

    base_df = base_df.dropna(subset=["Data", "Quantidade", "Valor_Unitario"])
    base_df = base_df[base_df["Quantidade"] > 0].copy()

    base_df["Faturamento_Total"] = base_df["Quantidade"] * base_df["Valor_Unitario"]
    base_df["Custo_Total"] = base_df["Quantidade"] * base_df["Custo_Unitario"]
    base_df["Lucro_Real"] = base_df["Faturamento_Total"] - base_df["Custo_Total"]
    base_df["Margem_Lucro"] = np.where(
        base_df["Faturamento_Total"] > 0,
        base_df["Lucro_Real"] / base_df["Faturamento_Total"] * 100,
        0,
    )
    base_df["Dia_Semana"] = pd.Categorical(
        base_df["Data"].dt.day_name(),
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )
    return base_df.sort_values("Data")


def calcular_abc(base_df):
    """Calcula a classificacao ABC e os indicadores por produto."""
    resumo = (
        base_df.groupby(["Categoria", "Produto"], as_index=False)
        .agg(
            Quantidade=("Quantidade", "sum"),
            Faturamento_Total=("Faturamento_Total", "sum"),
            Lucro_Real=("Lucro_Real", "sum"),
        )
        .sort_values("Lucro_Real", ascending=False)
    )
    if resumo.empty:
        return resumo

    resumo["Margem_Lucro"] = np.where(
        resumo["Faturamento_Total"] > 0,
        resumo["Lucro_Real"] / resumo["Faturamento_Total"] * 100,
        0,
    )
    total = resumo["Lucro_Real"].sum()
    if total > 0:
        resumo["Perc_Acumulado"] = resumo["Lucro_Real"].cumsum() / total * 100
        resumo["Classe"] = pd.cut(
            resumo["Perc_Acumulado"],
            bins=[0, 80, 95, 100],
            labels=["A", "B", "C"],
            include_lowest=True,
        ).astype(str).replace("nan", "C")
    else:
        resumo["Perc_Acumulado"] = 0
        resumo["Classe"] = "C"
    return resumo


def projetar_lucro(base_df):
    """Projeta o lucro dos proximos sete dias com tendencia linear simples."""
    serie_lucro = (
        base_df.groupby("Data", as_index=False)
        .agg(Lucro_Real=("Lucro_Real", "sum"))
        .sort_values("Data")
    )
    if serie_lucro.empty:
        return serie_lucro

    serie_lucro["Indice"] = range(len(serie_lucro))
    if len(serie_lucro) < 2:
        a, b = 0, float(serie_lucro["Lucro_Real"].iloc[0])
    else:
        a, b = np.polyfit(serie_lucro["Indice"], serie_lucro["Lucro_Real"], 1)

    futura = []
    ultima_data = serie_lucro["Data"].iloc[-1]
    ultimo_indice = int(serie_lucro["Indice"].iloc[-1])
    for i in range(1, 8):
        futura.append(
            {
                "Data": ultima_data + datetime.timedelta(days=i),
                "Lucro_Real": max(0, a * (ultimo_indice + i) + b),
                "Tipo": "Projecao",
            }
        )

    serie_lucro["Tipo"] = "Realizado"
    return pd.concat([serie_lucro[["Data", "Lucro_Real", "Tipo"]], pd.DataFrame(futura)], ignore_index=True)


with st.sidebar:
    st.title("Painel de Comando")
    fonte = st.radio("Ambiente de analise", ["Base padrao", "Base historica"])

try:
    if fonte == "Base padrao":
        df = tratar_base(gerar_demo())
        origem = "Base simulada"
    else:
        df = tratar_base(carregar_csv_local())
        origem = "Base historica do projeto"
except (ValueError, FileNotFoundError, OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as erro:
    st.error(f"Erro ao carregar a base: {erro}")
    st.stop()

if df.empty:
    st.warning("Nao foi possivel carregar dados para essa fonte.")
    st.stop()

dolar_hoje = carregar_dolar()

with st.sidebar:
    busca = st.text_input("Motor de busca", placeholder="Produto, categoria ou ID da venda")
    lista_categorias = sorted(df["Categoria"].dropna().unique().tolist())
    categorias_escolhidas = st.multiselect("Categorias", lista_categorias, default=lista_categorias)
    lista_produtos = sorted(df["Produto"].dropna().unique().tolist())
    produtos_escolhidos = st.multiselect("Produtos", lista_produtos, default=lista_produtos)
    data_min = df["Data"].min().date()
    data_max = df["Data"].max().date()
    periodo = st.date_input("Periodo", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    simulador_preco = st.slider("Simular reajuste medio (%)", 0, 30, 5, 1)

if len(periodo) == 2:
    inicio = pd.to_datetime(periodo[0])
    fim = pd.to_datetime(periodo[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df = df[(df["Data"] >= inicio) & (df["Data"] <= fim)].copy()

if categorias_escolhidas:
    df = df[df["Categoria"].isin(categorias_escolhidas)].copy()
if produtos_escolhidos:
    df = df[df["Produto"].isin(produtos_escolhidos)].copy()
if busca:
    termo = busca.lower().strip()
    filtro_busca = (
        df["Produto"].astype(str).str.lower().str.contains(termo, na=False)
        | df["Categoria"].astype(str).str.lower().str.contains(termo, na=False)
        | df["ID_Venda"].astype(str).str.lower().str.contains(termo, na=False)
    )
    df = df[filtro_busca].copy()

if df.empty:
    st.warning("Os filtros removeram todos os dados. Ajuste a busca ou selecione mais opcoes.")
    st.stop()

df["Preco_USD"] = df["Valor_Unitario"] / dolar_hoje
df["Faturamento_Simulado"] = df["Faturamento_Total"] * (1 + simulador_preco / 100)
df["Lucro_Simulado"] = df["Faturamento_Simulado"] - df["Custo_Total"]
df_abc = calcular_abc(df)

st.markdown(
    f"""
    <div class="hero">
        <small>Varex</small>
        <h1>Painel de mineracao comercial orientado a decisao</h1>
        <p>
            Acompanhe faturamento, margem, risco comercial, oportunidades de campanha e mineracao
            dinamica da base. Fonte ativa: <strong>{origem}</strong>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

insights = []
cat_lider = (
    df.groupby("Categoria", as_index=False)["Lucro_Real"]
    .sum()
    .sort_values("Lucro_Real", ascending=False)
    .iloc[0]
)
insights.append(
    ("Motor de lucro", cat_lider["Categoria"], f"Gera {moeda(cat_lider['Lucro_Real'])} em lucro e merece prioridade comercial.")
)
if not df_abc.empty:
    baixa_margem = df_abc.sort_values(["Margem_Lucro", "Faturamento_Total"], ascending=[True, False]).iloc[0]
    insights.append(
        (
            "Revisao de preco",
            baixa_margem["Produto"],
            f"Tem margem de {baixa_margem['Margem_Lucro']:.1f}% e alto impacto no resultado.",
        )
    )
    classe_c = df_abc[df_abc["Classe"] == "C"].sort_values("Quantidade", ascending=False)
    if not classe_c.empty:
        item_c = classe_c.iloc[0]
        insights.append(
            (
                "Acao rapida",
                item_c["Produto"],
                "Classe C no ABC. Bom candidato para campanha de escoamento ou combo.",
            )
        )

colunas_insight = st.columns(len(insights))
for coluna, (rotulo, titulo, texto) in zip(colunas_insight, insights):
    with coluna:
        st.markdown(
            f"""
            <div class="insight">
                <span>{rotulo}</span>
                <strong>{titulo}</strong>
                <div>{texto}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

faturamento = df["Faturamento_Total"].sum()
lucro = df["Lucro_Real"].sum()
lucro_projetado = df["Lucro_Simulado"].sum()
margem = df["Margem_Lucro"].mean()
volume = df["Quantidade"].sum()
ticket = faturamento / max(volume, 1)

st.subheader("Resumo Executivo")
m1, m2, m3 = st.columns(3)
with m1:
    with st.container(border=True):
        st.metric("Faturamento", moeda(faturamento))
with m2:
    with st.container(border=True):
        st.metric("Lucro", moeda(lucro))
with m3:
    with st.container(border=True):
        st.metric("Margem media", f"{margem:.1f}%")

m4, m5, m6 = st.columns(3)
with m4:
    with st.container(border=True):
        st.metric("Volume", f"{volume:,.0f}")
with m5:
    with st.container(border=True):
        st.metric("Ticket medio", moeda(ticket))
with m6:
    with st.container(border=True):
        st.metric("Lucro projetado", moeda(lucro_projetado), delta=moeda(lucro_projetado - lucro))

st.caption(f"Cotacao USD/BRL: {dolar_hoje:.2f} | Preco medio em USD: US$ {df['Preco_USD'].mean():.2f}")

abas = st.tabs(["Resumo Visual", "Mineracao Dinamica", "Diagnostico", "Acionamento"])

with abas[0]:
    col1, col2 = st.columns([1.8, 1.2])

    serie_temporal = (
        df.groupby("Data", as_index=False)
        .agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"))
        .sort_values("Data")
    )
    graf_linha = go.Figure()
    graf_linha.add_trace(go.Scatter(x=serie_temporal["Data"], y=serie_temporal["Faturamento_Total"], mode="lines+markers", name="Faturamento"))
    graf_linha.add_trace(go.Scatter(x=serie_temporal["Data"], y=serie_temporal["Lucro_Real"], mode="lines+markers", name="Lucro", yaxis="y2"))
    graf_linha.update_layout(
        title="Faturamento e lucro no tempo",
        yaxis=dict(title="Faturamento"),
        yaxis2=dict(title="Lucro", overlaying="y", side="right"),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h"),
    )

    resumo_categoria = (
        df.groupby("Categoria", as_index=False)
        .agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"))
        .sort_values("Faturamento_Total", ascending=False)
    )
    graf_categoria = px.bar(
        resumo_categoria,
        x="Categoria",
        y=["Faturamento_Total", "Lucro_Real"],
        barmode="group",
        title="Comparativo por categoria",
    )

    with col1:
        st.plotly_chart(graf_linha, use_container_width=True, theme="streamlit")
    with col2:
        st.plotly_chart(graf_categoria, use_container_width=True, theme="streamlit")

    col3, col4 = st.columns([1.1, 1.9])
    graf_donut = px.pie(
        resumo_categoria,
        names="Categoria",
        values="Faturamento_Total",
        hole=0.55,
        title="Participacao no faturamento",
    )
    graf_donut.update_traces(textposition="inside", textinfo="percent+label")

    graf_scatter = px.scatter(
        df_abc,
        x="Quantidade",
        y="Margem_Lucro",
        size="Faturamento_Total",
        color="Classe",
        hover_name="Produto",
        title="Volume x margem x relevancia",
        color_discrete_map={"A": "#16a34a", "B": "#f59e0b", "C": "#dc2626"},
    )

    with col3:
        st.plotly_chart(graf_donut, use_container_width=True, theme="streamlit")
    with col4:
        st.plotly_chart(graf_scatter, use_container_width=True, theme="streamlit")

    col5, col6 = st.columns(2)
    heat = (
        df.pivot_table(index="Dia_Semana", columns="Categoria", values="Faturamento_Total", aggfunc="sum", fill_value=0)
        .reindex(df["Dia_Semana"].cat.categories)
        .fillna(0)
    )
    graf_heat = px.imshow(heat, text_auto=".0f", aspect="auto", title="Heatmap por dia e categoria", color_continuous_scale="Blues")

    pareto = df_abc.sort_values("Faturamento_Total", ascending=False).head(10).copy()
    pareto_total = pareto["Faturamento_Total"].sum()
    if pareto_total > 0:
        pareto["Acumulado"] = pareto["Faturamento_Total"].cumsum() / pareto_total * 100
    else:
        pareto["Acumulado"] = 0
    pareto["Rotulo"] = pareto["Produto"].map(quebrar_rotulo)
    graf_pareto = go.Figure()
    graf_pareto.add_trace(go.Bar(x=pareto["Rotulo"], y=pareto["Faturamento_Total"], name="Faturamento"))
    graf_pareto.add_trace(go.Scatter(x=pareto["Rotulo"], y=pareto["Acumulado"], name="% acumulado", yaxis="y2"))
    graf_pareto.update_layout(
        title="Pareto dos produtos mais relevantes",
        yaxis2=dict(overlaying="y", side="right", range=[0, 100]),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h"),
        xaxis_tickangle=-20,
        height=460,
    )

    with col5:
        st.plotly_chart(graf_heat, use_container_width=True, theme="streamlit")
    with col6:
        st.plotly_chart(graf_pareto, use_container_width=True, theme="streamlit")

with abas[1]:
    st.subheader("Mineracao Dinamica")
    st.caption("Consultas prontas para leitura de negocio, sem parecer uma tela parada.")

    consultas = {
        "Produtos com maior faturamento": df_abc.nlargest(10, "Faturamento_Total")[["Produto", "Categoria", "Faturamento_Total", "Lucro_Real", "Margem_Lucro"]],
        "Produtos com menor margem": df_abc.nsmallest(10, "Margem_Lucro")[["Produto", "Categoria", "Margem_Lucro", "Faturamento_Total", "Lucro_Real"]],
        "Produtos para campanha imediata": df_abc[df_abc["Classe"] == "C"][["Produto", "Categoria", "Quantidade", "Margem_Lucro", "Lucro_Real"]].sort_values(["Quantidade", "Margem_Lucro"], ascending=[False, True]).head(10),
        "Categorias mais lucrativas": df.groupby("Categoria", as_index=False).agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"), Quantidade=("Quantidade", "sum")).sort_values("Lucro_Real", ascending=False),
        "Historico diario resumido": df.groupby("Data", as_index=False).agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"), Quantidade=("Quantidade", "sum")).sort_values("Data", ascending=False),
    }
    consulta = st.selectbox("Consulta de negocio", list(consultas.keys()))

    col7, col8 = st.columns([1, 1.4])
    with col7:
        nivel = st.radio("Visualizar por", ["Produto", "Categoria", "Dia"], horizontal=True)
        metricas = {
            "Lucro Real": "Lucro_Real",
            "Faturamento Total": "Faturamento_Total",
            "Quantidade": "Quantidade",
        }
        metrica_label = st.selectbox("Metrica", list(metricas.keys()))
        metrica = metricas[metrica_label]

        if nivel == "Produto":
            visao = df.groupby("Produto", as_index=False).agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"), Quantidade=("Quantidade", "sum")).sort_values(metrica, ascending=False).head(12)
            eixo = "Produto"
        elif nivel == "Categoria":
            visao = df.groupby("Categoria", as_index=False).agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"), Quantidade=("Quantidade", "sum")).sort_values(metrica, ascending=False)
            eixo = "Categoria"
        else:
            visao = df.groupby("Data", as_index=False).agg(Faturamento_Total=("Faturamento_Total", "sum"), Lucro_Real=("Lucro_Real", "sum"), Quantidade=("Quantidade", "sum")).sort_values("Data")
            eixo = "Data"

        orientacao_horizontal = eixo in ["Produto", "Categoria"]
        if orientacao_horizontal:
            visao = visao.copy()
            visao["Rotulo"] = visao[eixo].map(quebrar_rotulo)
            graf_query = px.bar(
                visao.sort_values(metrica, ascending=True),
                x=metrica,
                y="Rotulo",
                orientation="h",
                color=metrica,
                color_continuous_scale="Tealgrn",
                title=f"{metrica_label} por {nivel.lower()}",
            )
            graf_query.update_layout(
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=50, b=10),
                height=max(420, len(visao) * 42),
                yaxis_title=eixo,
            )
        else:
            graf_query = px.bar(
                visao,
                x=eixo,
                y=metrica,
                color=metrica,
                color_continuous_scale="Tealgrn",
                title=f"{metrica_label} por {nivel.lower()}",
            )
            graf_query.update_layout(
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=50, b=10),
                xaxis_tickangle=-35,
            )
        st.plotly_chart(graf_query, use_container_width=True, theme="streamlit")

    with col8:
        st.dataframe(consultas[consulta], use_container_width=True, hide_index=True)
        st.markdown("**Base filtrada para auditoria**")
        st.dataframe(
            df.sort_values("Data", ascending=False)[
                ["Data", "ID_Venda", "Produto", "Categoria", "Quantidade", "Valor_Unitario", "Faturamento_Total", "Lucro_Real"]
            ].head(50),
            use_container_width=True,
            hide_index=True,
        )

with abas[2]:
    st.subheader("Diagnostico para Tomada de Decisao")
    col9, col10 = st.columns(2)

    risco = df_abc.sort_values(["Margem_Lucro", "Faturamento_Total"], ascending=[True, False]).head(8)
    graf_risco = px.bar(risco, x="Margem_Lucro", y="Produto", orientation="h", color="Categoria", title="Itens com margem mais pressionada")
    oportunidade = df_abc.sort_values(["Lucro_Real", "Quantidade"], ascending=[False, False]).head(8)
    graf_oportunidade = px.bar(
        oportunidade,
        x="Lucro_Real",
        y="Produto",
        orientation="h",
        color="Classe",
        title="Itens para escalar ou proteger",
        color_discrete_map={"A": "#16a34a", "B": "#f59e0b", "C": "#dc2626"},
    )

    with col9:
        st.plotly_chart(graf_risco, use_container_width=True, theme="streamlit")
    with col10:
        st.plotly_chart(graf_oportunidade, use_container_width=True, theme="streamlit")

    st.markdown("**Radar de acao sugerida**")
    radar = df_abc.copy()
    radar["Acao_Sugerida"] = np.select(
        [
            (radar["Classe"] == "A") & (radar["Margem_Lucro"] >= radar["Margem_Lucro"].median()),
            (radar["Classe"] == "A") & (radar["Margem_Lucro"] < radar["Margem_Lucro"].median()),
            radar["Classe"] == "B",
        ],
        [
            "Proteger estoque e investimento",
            "Revisar preco para capturar margem",
            "Monitorar giro e abastecimento",
        ],
        default="Ativar campanha de escoamento",
    )
    st.dataframe(
        radar[["Produto", "Categoria", "Classe", "Quantidade", "Faturamento_Total", "Lucro_Real", "Margem_Lucro", "Acao_Sugerida"]],
        use_container_width=True,
        hide_index=True,
    )

    projecao = projetar_lucro(df)
    graf_proj = px.line(
        projecao,
        x="Data",
        y="Lucro_Real",
        color="Tipo",
        markers=True,
        title="Serie realizada e projecao linear de 7 dias",
        color_discrete_map={"Realizado": "#2563eb", "Projecao": "#dc2626"},
    )
    st.plotly_chart(graf_proj, use_container_width=True, theme="streamlit")
    st.caption("A projecao e simples e explicavel. Ela ajuda a conversa de negocio, mas nao substitui um modelo preditivo robusto.")

with abas[3]:
    st.subheader("Central de Acionamento Comercial")
    col11, col12 = st.columns(2)

    classe_c = df_abc[df_abc["Classe"] == "C"].sort_values(["Quantidade", "Margem_Lucro"], ascending=[False, True])
    classe_b = df_abc[df_abc["Classe"] == "B"].sort_values("Lucro_Real", ascending=False)

    with col11:
        st.markdown("**Campanhas de escoamento**")
        if classe_c.empty:
            st.success("Nao ha itens classe C no recorte atual.")
        else:
            for _, item in classe_c.head(6).iterrows():
                with st.expander(f"{item['Produto']} | {item['Categoria']}"):
                    desconto = sugestao_campanha(item["Produto"])
                    st.write(f"Margem atual: {item['Margem_Lucro']:.1f}%")
                    st.write(f"Lucro acumulado: {moeda(item['Lucro_Real'])}")
                    st.write(f"Acao sugerida: campanha com {desconto} e CTA de urgencia.")

    with col12:
        st.markdown("**Itens para destaque de vitrine**")
        st.dataframe(
            classe_b.head(6)[["Produto", "Categoria", "Lucro_Real", "Margem_Lucro", "Quantidade"]],
            use_container_width=True,
            hide_index=True,
        )
