# Dentro do arquivo utils.py
import streamlit as st
import requests
import pandas as pd

@st.cache_data(ttl="1h")
def buscar_todos_os_dados():
    API_URL = "https://api-adesoes-comercial.vercel.app/dados" # URL da sua API
    # ... O resto da sua função de busca continua igual ...
    page_size = 5000
    offset = 0
    all_data = []
    status_text = st.empty()
    while True:
        paginated_url = f"{API_URL}?limit={page_size}&offset={offset}"
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
    df['dt_cadastro_integrante'] = pd.to_datetime(df['dt_cadastro_integrante'], errors='coerce')
    df['vl_plano'] = pd.to_numeric(df['vl_plano'], errors='coerce').fillna(0)
    df['periodo'] = df['dt_cadastro_integrante'].dt.to_period('M').astype(str)
    return df
