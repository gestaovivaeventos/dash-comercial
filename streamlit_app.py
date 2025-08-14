import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

# --- ESTILO CUSTOMIZADO (CSS) ---
# Injetamos um pouco de CSS para um visual mais claro e profissional
st.markdown(
    """
<style>
    body {
        background-color: #f5f7fa;
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
        color: #ff7f0e !important; /* Torna o texto laranja para melhor legibilidade */
    }
    .stMetric label,
    .stMetric [data-testid="stMetricValue"] {
        color: #ff7f0e !important;
    }
    .stMetric .st-ae { /* Ajusta o alinhamento do valor */
        justify-content: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


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
    df['dt_cadastro_integrante'] = pd.to_datetime(df['dt_cadastro_integrante'], errors='coerce')
    df['vl_plano'] = pd.to_numeric(df['vl_plano'], errors='coerce').fillna(0)
    # Cria uma coluna 'periodo' (Ano-Mês) para facilitar agregações mensais
    df['periodo'] = df['dt_cadastro_integrante'].dt.to_period('M').astype(str)

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
    if len(vendas_mensais_series) >= 2:
        x = np.arange(len(vendas_mensais_series))
        y = vendas_mensais_series.values
        coef = np.polyfit(x, y, 1)
        previsao_proximo_mes = float(np.polyval(coef, len(vendas_mensais_series)))
    else:
        previsao_proximo_mes = float(vendas_mensais_series.iloc[-1]) if len(vendas_mensais_series) > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        label="VVR Total (R$)",
        value=f"{total_vvr:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    col2.metric(
        label="Adesões Vendas",
        value=f"{adesoes_vendas:,}".replace(",", "."),
    )
    col3.metric(
        label="Adesões Pós-Vendas",
        value=f"{adesoes_pos_vendas:,}".replace(",", "."),
    )
    col4.metric(
        label="Ticket Médio (R$)",
        value=f"{ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    col5.metric(
        label="Prev. Próx. Mês (R$)",
        value=f"{previsao_proximo_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    st.markdown("---")

    # GRÁFICOS INTERATIVOS
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Volume de Vendas Mensal (R$)")
        vendas_mensais_df = vendas_mensais_series.reset_index()
        vendas_mensais_df.columns = ["periodo", "vl_plano"]
        fig_mensal = px.line(
            vendas_mensais_df,
            x="periodo",
            y="vl_plano",
            markers=True,
            labels={"periodo": "Período", "vl_plano": "Valor"},
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

    st.markdown("---")

    st.subheader("Adesões por Mês (Vendas vs Pós-Vendas)")
    adesoes_tipo = (
        df_filtrado.groupby(['periodo', 'tipo_cliente'])['id_fundo']
        .count()
        .reset_index(name='adesoes')
    )
    fig_adesoes = px.bar(
        adesoes_tipo,
        x='periodo',
        y='adesoes',
        color='tipo_cliente',
        barmode='stack',
        labels={'periodo': 'Período', 'adesoes': 'Adesões', 'tipo_cliente': 'Tipo'},
    )
    st.plotly_chart(fig_adesoes, use_container_width=True)

    st.markdown("---")

    st.subheader("Tabela de Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.warning("Não foi possível carregar os dados. Verifique a API ou tente recarregar a página.")
