import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

# --- ESTILO CUSTOMIZADO (CSS) ---
# Injetamos um pouco de CSS para um visual mais limpo e profissional
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
    .stMetric {
        border: 1px solid #2e3138;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .stMetric .st-ae { /* Ajusta o alinhamento do valor */
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)


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
    
    # Filtro de Unidade (agora como selectbox/dropdown)
    lista_unidades = ['Todas'] + sorted(df_original['nm_unidade'].unique())
    unidade_selecionada = st.sidebar.selectbox("Unidade", options=lista_unidades)

    # Filtro de Tipo de Cliente
    lista_tipos_cliente = ['Todos'] + sorted(df_original['tipo_cliente'].unique())
    tipo_cliente_selecionado = st.sidebar.selectbox("Tipo de Cliente", options=lista_tipos_cliente)

    # Filtro de Data
    data_min = df_original['dt_cadastro_fundo'].min().date()
    data_max = df_original['dt_cadastro_fundo'].max().date()
    filtro_data = st.sidebar.date_input('Período de Cadastro', value=(data_min, data_max))
    
    # --- APLICAÇÃO DOS FILTROS ---
    df_filtrado = df_original.copy()
    if unidade_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['nm_unidade'] == unidade_selecionada]
    if tipo_cliente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_cliente'] == tipo_cliente_selecionado]
    if len(filtro_data) == 2:
        start_date = pd.to_datetime(filtro_data[0])
        end_date = pd.to_datetime(filtro_data[1])
        df_filtrado = df_filtrado[(df_filtrado['dt_cadastro_fundo'] >= start_date) & (df_filtrado['dt_cadastro_fundo'] <= end_date)]

    # --- EXIBIÇÃO DO DASHBOARD PRINCIPAL ---

    # KPIs
    total_vvr = df_filtrado['vl_plano'].sum()
    num_adesoes = len(df_filtrado)
    ticket_medio = total_vvr / num_adesoes if num_adesoes > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="VVR Total (R$)", value=f"{total_vvr:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric(label="Número de Adesões", value=f"{num_adesoes:,}".replace(",", "."))
    col3.metric(label="Ticket Médio (R$)", value=f"{ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("---")

    # GRÁFICOS
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("VVR (Valor do Plano) por Mês")
        vvr_por_mes = df_filtrado.groupby('periodo')['vl_plano'].sum().sort_index()
        st.line_chart(vvr_por_mes)
        
    with col_graf2:
        st.subheader("Número de Adesões por Mês")
        adesoes_por_mes = df_filtrado.groupby('periodo')['id_fundo'].count().sort_index()
        st.line_chart(adesoes_por_mes, color="#ffaa00") # Cor diferente

    st.markdown("---")

    st.subheader("Adesões por Mês (Vendas vs Pós-Vendas)")
    # IMPORTANTE: Aqui estamos usando a coluna 'tipo_cliente' para criar as pilhas.
    # Se a coluna correta for outra, basta alterar a palavra 'tipo_cliente' abaixo.
    adesoes_empilhadas = df_filtrado.groupby(['periodo', 'tipo_cliente'])['id_fundo'].count().unstack(fill_value=0)
    st.bar_chart(adesoes_empilhadas)

    st.markdown("---")
    
    st.subheader("Tabela de Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)
    
else:
    st.warning("Não foi possível carregar os dados. Verifique a API ou tente recarregar a página.")
