import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
# Usamos set_page_config no início para definir o layout e o título da aba do navegador.
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

# --- FUNÇÃO PARA BUSCAR OS DADOS (cacheada para performance) ---
# O decorator @st.cache_data é a "mágica" do Streamlit. Ele armazena o resultado da
# função em cache. Assim, os dados da API só são buscados uma vez. Se o usuário
# mexer nos filtros, o Streamlit não precisa chamar a API de novo, tornando
# o dashboard super rápido. O cache é limpo quando a página é recarregada (F5).
@st.cache_data
def buscar_todos_os_dados():
    API_URL = "https://api-adesoes-comercial.vercel.app/dados" # URL da sua API
    page_size = 5000
    offset = 0
    all_data = []
    
    # Este objeto será mostrado enquanto os dados são buscados
    status_text = st.empty()

    while True:
        paginated_url = f"{API_URL}?limit={page_size}&offset={offset}"
        status_text.text(f"Buscando... {len(all_data)} registros encontrados.")
        
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
    return pd.DataFrame(all_data)

# --- CARREGAMENTO DOS DADOS ---
# Chama a função para buscar os dados e convertê-los em um DataFrame do Pandas.
# O Pandas é essencial para fazer as filtragens e agregações de forma eficiente.
df_original = buscar_todos_os_dados()

# --- TÍTULO DO DASHBOARD ---
st.title("📈 Dashboard de Vendas e Adesões")
st.markdown("---")

# --- BARRA LATERAL COM FILTROS ---
st.sidebar.header("Filtros")

# Verifica se o dataframe foi carregado com sucesso antes de criar os filtros
if df_original is not None and not df_original.empty:
    # Converte as colunas de data para o formato datetime, tratando possíveis erros.
    df_original['dt_cadastro_fundo'] = pd.to_datetime(df_original['dt_cadastro_fundo'], errors='coerce')
    
    # Filtro de Unidade
    unidades = sorted(df_original['nm_unidade'].unique())
    unidade_selecionada = st.sidebar.multiselect(
        "Unidade",
        options=unidades,
        default=unidades # Por padrão, todas vêm selecionadas
    )

    # Filtro de Tipo de Cliente (antigo 'fundo')
    tipos_cliente = sorted(df_original['tipo_cliente'].unique())
    tipo_cliente_selecionado = st.sidebar.multiselect(
        "Tipo de Cliente",
        options=tipos_cliente,
        default=tipos_cliente
    )

    # Filtro de Data
    data_min = df_original['dt_cadastro_fundo'].min()
    data_max = df_original['dt_cadastro_fundo'].max()
    
    filtro_data = st.sidebar.date_input(
        'Período de Cadastro',
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )
    
    # --- APLICAÇÃO DOS FILTROS NO DATAFRAME ---
    # Cria uma cópia filtrada dos dados com base nas seleções do usuário
    df_filtrado = df_original.query(
        "nm_unidade == @unidade_selecionada & " +
        "tipo_cliente == @tipo_cliente_selecionado & " +
        "dt_cadastro_fundo >= @filtro_data[0] & dt_cadastro_fundo <= @filtro_data[1]"
    )

    # --- EXIBIÇÃO DO DASHBOARD PRINCIPAL ---

    # KPIs (Indicadores Chave)
    total_registros = len(df_filtrado)
    valor_total_plano = df_filtrado['vl_plano'].sum()
    
    # Usamos colunas para organizar os KPIs lado a lado
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total de Registros no Período", value=f"{total_registros:,}".replace(",", "."))
    with col2:
        st.metric(label="Valor Total dos Planos (R$)", value=f"{valor_total_plano:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # Gráficos
    st.subheader("Análise por Unidade")
    # Agrupa os dados por unidade e soma os valores dos planos
    vendas_por_unidade = df_filtrado.groupby('nm_unidade')['vl_plano'].sum().sort_values(ascending=False)
    st.bar_chart(vendas_por_unidade)
    
    st.subheader("Tabela de Dados Filtrados")
    # Exibe a tabela com os dados já filtrados
    st.dataframe(df_filtrado)
    
else:
    st.warning("Não foi possível carregar os dados. Verifique a API ou tente recarregar a página.")
