import streamlit as st
import requests
import pandas as pd

# --- CONFIGURAÇÃO ---
# Cole aqui a URL base da sua API FastAPI que já está funcionando na Vercel.
API_URL = "https://api-adesoes-comercial.vercel.app" # <<< MUDE AQUI!

# --- FUNÇÃO PARA BUSCAR OS DADOS ---
# Esta função usa a paginação para buscar todos os dados da sua API.
def buscar_todos_os_dados():
    page_size = 5000  # Mesmo tamanho de página da API
    offset = 0
    all_data = []
    
    while True:
        # Monta a URL para a página atual
        paginated_url = f"{API_URL}?limit={page_size}&offset={offset}"
        print(f"Buscando em: {paginated_url}") # Para vermos o progresso no terminal
        
        response = requests.get(paginated_url)
        
        # Se a resposta não for bem-sucedida, para o loop
        if response.status_code != 200:
            st.error(f"Erro ao buscar dados da API. Status: {response.status_code}")
            break
        
        data_object = response.json()
        page_data = data_object.get("dados", [])
        
        # Se a página veio vazia, significa que acabaram os dados
        if not page_data:
            break
            
        all_data.extend(page_data)
        offset += page_size
        
    return all_data

# --- INTERFACE DO DASHBOARD ---
st.set_page_config(layout="wide") # Deixa o dashboard usar a largura inteira da tela
st.title("📊 Dashboard de Fundos e Adesões")

# Botão para iniciar a busca dos dados
if st.button("Buscar e Atualizar Dados"):
    
    with st.spinner('Aguarde... Buscando milhares de registros da sua API...'):
        dados_completos = buscar_todos_os_dados()

    if dados_completos:
        st.success(f"Sucesso! {len(dados_completos)} registros encontrados.")
        
        # Converte os dados para um formato de tabela com Pandas
        df = pd.DataFrame(dados_completos)
        
        # Exibe a tabela de dados completa e interativa
        st.subheader("Dados Completos")
        st.dataframe(df)
        
        # --- BÔNUS: ALGUNS GRÁFICOS SIMPLES ---
        
        st.subheader("Registros por Unidade")
        # Conta quantos registros existem para cada 'nm_unidade'
        contagem_unidades = df['nm_unidade'].value_counts()
        st.bar_chart(contagem_unidades)
        
        st.subheader("Registros por Tipo de Cliente")
        contagem_clientes = df['tipo_cliente'].value_counts()
        st.bar_chart(contagem_clientes)
        
    else:
        st.warning("Nenhum dado foi retornado pela API.")
