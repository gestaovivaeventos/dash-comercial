from utils import buscar_todos_os_dados
import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")


# --- ESTILO CUSTOMIZADO (CSS) ---
# Tema mais claro com métricas em laranja
st.markdown(
    """
<style>
    body {
        background-color: #f0f2f6;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stMetric {
        border: 1px solid #d0d3d8;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        background-color: #ffffff;
        color: #ff7f0e !important;
    }
    .stMetric label,
    .stMetric [data-testid="stMetricValue"] {
        color: #ff7f0e !important;
    }
    .stMetric .st-ae {
        justify-content: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNÇÕES AUXILIARES ---
def format_currency(valor: float) -> str:
    """Formata valores monetários no padrão brasileiro."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_int(valor: float) -> str:
    """Formata inteiros com separador de milhar."""
    return f"{int(valor):,}".replace(",", ".")


# --- FUNÇÃO PARA BUSCAR OS DADOS (cacheada para performance) ---
@st.cache_data(ttl="1h") # Adicionamos um TTL (Time To Live) para o cache. Ele será invalidado a cada 1 hora.
def buscar_todos_os_dados():
    API_URL = "https://api-adesoes-comercial.vercel.app/dados" # URL da sua API
    page_size = 5000
    offset = 0
    all_data = []
    
    status_text = st.empty()
    while True:
        paginated_url = f"{API_URL}?limit={page_size}&offset={offset}"
        
        # Mostra o progresso de forma mais discreta
        total_encontrado = len(all_data)
        if total_encontrado > 0:
            status_text.text(f"Buscando... {total_encontrado} registros carregados.")

        response = requests.get(paginated_url)
        if response.status_code != 200:
            st.error(f"Erro ao buscar dados da API. Status: {response.status_code}")
            return None
        
        data_object = response.json()
        page_data = data_object.get("dados", [])
        
        if not page_data:
            break
            
        all_data.extend(page_data)
        offset += page_size
        
    status_text.success(f"Busca finalizada! {len(all_data)} registros carregados.")
    df = pd.DataFrame(all_data)
    
    # --- PRÉ-PROCESSAMENTO DOS DADOS ---
    # Convertendo colunas importantes para os tipos corretos
    df['dt_cadastro_fundo'] = pd.to_datetime(df['dt_cadastro_fundo'], errors='coerce')
    df['vl_plano'] = pd.to_numeric(df['vl_plano'], errors='coerce').fillna(0)
    # Cria uma coluna 'periodo' (Ano-Mês) para facilitar agregações mensais
    df['periodo'] = df['dt_cadastro_fundo'].dt.to_period('M').astype(str)

    return df

# --- CARREGAMENTO INICIAL DOS DADOS ---
df_original = buscar_todos_os_dados()

# --- TÍTULO DO DASHBOARD ---
st.title("📈 Dashboard de Vendas e Adesões")
st.markdown("---")

# --- BARRA LATERAL COM FILTROS ---
st.sidebar.header("Filtros")

if df_original is not None and not df_original.empty:

    # Filtro de Unidade
    lista_unidades = ['Todas'] + sorted(df_original['nm_unidade'].dropna().unique())
    unidade_selecionada = st.sidebar.selectbox("Unidade", options=lista_unidades)

    # Filtro de Tipo de Cliente
    lista_tipos_cliente = ['Todos'] + sorted(df_original['tipo_cliente'].dropna().unique())
    tipo_cliente_selecionado = st.sidebar.selectbox("Tipo de Cliente", options=lista_tipos_cliente)

    # Filtro de Ano
    anos_disponiveis = ['Todos'] + sorted(df_original['dt_cadastro_fundo'].dt.year.dropna().unique())
    ano_selecionado = st.sidebar.selectbox("Ano", options=anos_disponiveis)

    # Aplica filtros iniciais
    df_filtrado = df_original.copy()
    if unidade_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['nm_unidade'] == unidade_selecionada]
    if tipo_cliente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_cliente'] == tipo_cliente_selecionado]
    if ano_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['dt_cadastro_fundo'].dt.year == ano_selecionado]

    # Filtro de Mês (dependente do Ano selecionado)
    meses_disponiveis = ['Todos'] + sorted(df_filtrado['dt_cadastro_fundo'].dt.month.dropna().unique())
    mes_selecionado = st.sidebar.selectbox("Mês", options=meses_disponiveis)
    if mes_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['dt_cadastro_fundo'].dt.month == mes_selecionado]

    # --- EXIBIÇÃO DO DASHBOARD PRINCIPAL ---

    # KPIs
    total_vvr = df_filtrado['vl_plano'].sum()
    num_adesoes = len(df_filtrado)
    ticket_medio = total_vvr / num_adesoes if num_adesoes > 0 else 0

    adesoes_vendas = df_filtrado['tipo_cliente'].str.contains('venda', case=False, na=False).sum()
    adesoes_pos_vendas = df_filtrado['tipo_cliente'].str.contains('pos', case=False, na=False).sum()

    vendas_mensais_series = df_filtrado.groupby('periodo')['vl_plano'].sum().sort_index()
    vendas_mensais_series.index = pd.to_datetime(vendas_mensais_series.index)
    vendas_mensais_series = vendas_mensais_series.sort_index()

    vvr_periodo_atual = vendas_mensais_series.iloc[-1] if len(vendas_mensais_series) > 0 else 0
    vvr_periodo_anterior = vendas_mensais_series.iloc[-2] if len(vendas_mensais_series) > 1 else 0
    dif_vvr = vvr_periodo_atual - vvr_periodo_anterior

    if len(vendas_mensais_series) >= 2:
        x = np.arange(len(vendas_mensais_series))
        y = vendas_mensais_series.values
        coef = np.polyfit(x, y, 1)
        previsao_proximo_mes = float(np.polyval(coef, len(vendas_mensais_series)))
    else:
        previsao_proximo_mes = float(vendas_mensais_series.iloc[-1]) if len(vendas_mensais_series) > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VVR Período (R$)", format_currency(vvr_periodo_atual))
    col2.metric("VVR Período Anterior (R$)", format_currency(vvr_periodo_anterior))
    col3.metric("Diferença (R$)", format_currency(dif_vvr))
    col4.metric("Prev. Próx. Mês (R$)", format_currency(previsao_proximo_mes))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Adesões Vendas", format_int(adesoes_vendas))
    col6.metric("Adesões Pós-Vendas", format_int(adesoes_pos_vendas))
    col7.metric("Ticket Médio (R$)", format_currency(ticket_medio))
    col8.metric("Total de Adesões", format_int(num_adesoes))

    st.markdown("---")

    # GRÁFICOS INTERATIVOS
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Volume de Vendas Mensal (R$)")
        vendas_mensais_df = vendas_mensais_series.reset_index()
        vendas_mensais_df.columns = ["periodo", "vl_plano"]
        meta_mensal = vendas_mensais_df["vl_plano"].mean() * 1.1 if not vendas_mensais_df.empty else 0
        fig_mensal = px.line(
            vendas_mensais_df,
            x="periodo",
            y="vl_plano",
            markers=True,
            labels={"periodo": "Período", "vl_plano": "Valor"},
        )
        fig_mensal.add_scatter(
            x=vendas_mensais_df["periodo"],
            y=[meta_mensal] * len(vendas_mensais_df),
            mode="lines",
            name="Meta",
        )
        st.plotly_chart(fig_mensal, use_container_width=True)

    with col_graf2:
        st.subheader("Volume de Vendas Anual (R$)")
        vendas_anuais = (
            df_filtrado.groupby(df_filtrado['dt_cadastro_fundo'].dt.year)['vl_plano']
            .sum()
            .reset_index(name='vl_plano')
        )
        vendas_anuais.columns = ['Ano', 'vl_plano']
        fig_anual = px.bar(
            vendas_anuais,
            x='Ano',
            y='vl_plano',
            labels={'Ano': 'Ano', 'vl_plano': 'Valor'},
        )
        st.plotly_chart(fig_anual, use_container_width=True)

    col_graf3, col_graf4 = st.columns(2)

    with col_graf3:
        st.subheader("VVR por Tipo de Cliente")
        vvr_tipo = (
            df_filtrado.groupby(['periodo', 'tipo_cliente'])['vl_plano']
            .sum()
            .reset_index()
        )
        fig_vvr_tipo = px.bar(
            vvr_tipo,
            x='periodo',
            y='vl_plano',
            color='tipo_cliente',
            barmode='stack',
            labels={'periodo': 'Período', 'vl_plano': 'VVR', 'tipo_cliente': 'Tipo'},
        )
        st.plotly_chart(fig_vvr_tipo, use_container_width=True)

    with col_graf4:
        st.subheader("Mapa de Vendas (Ano x Mês)")
        heatmap_df = (
            df_filtrado
            .pivot_table(index=df_filtrado['dt_cadastro_fundo'].dt.year,
                        columns=df_filtrado['dt_cadastro_fundo'].dt.month,
                        values='vl_plano', aggfunc='sum')
            .fillna(0)
        )
        fig_heatmap = px.imshow(
            heatmap_df,
            labels={'x': 'Mês', 'y': 'Ano', 'color': 'VVR'},
            aspect="auto",
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")

    st.subheader("Tabela de Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.warning("Não foi possível carregar os dados. Verifique a API ou tente recarregar a página.")
