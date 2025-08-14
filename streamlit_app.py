import streamlit as st
import requests
# A linha "import pandas as pd" foi removida.

# --- CONFIGURAÇÃO ---
API_URL = "https://api-adesoes-comercial.vercel.app/dados" # Verifique se esta é a URL correta da sua API de dados

# --- FUNÇÃO PARA BUSCAR OS DADOS ---
def buscar_todos_os_dados():
    page_size = 5000
    offset = 0
    all_data = []
    
    while True:
        paginated_url = f"{API_URL}?limit={page_size}&offset={offset}"
        print(f"Buscando em: {paginated_url}")
        
        response = requests.get(paginated_url)
        
        if response.status_code != 200:
            st.error(f"Erro ao buscar dados da API. Status: {response.status_code}")
            break
        
        data_object = response.json()
        page_data = data_object.get("dados", [])
        
        if not page_data:
            break
            
        all_data.extend(page_data)
        offset += page_size
        
    return all_data

# --- INTERFACE DO DASHBOARD ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Fundos e Adesões")

if st.button("Buscar e Atualizar Dados"):
    
    with st.spinner('Aguarde... Buscando registros da sua API...'):
        dados_completos = buscar_todos_os_dados()

    if dados_completos:
        st.success(f"Sucesso! {len(dados_completos)} registros encontrados.")
        
        # A linha "df = pd.DataFrame(dados_completos)" foi removida.
        
        st.subheader("Dados Completos")
        # Passamos a lista de dados diretamente para o Streamlit.
        st.dataframe(dados_completos)
        
        # Os gráficos que dependiam do Pandas foram removidos por enquanto.
        
    else:
        st.warning("Nenhum dado foi retornado pela API.")
