import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# URL da sua API de dados
API_URL = "https://api-adesoes-comercial.vercel.app/dados"

# --- CSS para o efeito do ticker (sem a duração da animação) ---
st.markdown("""
<style>
@keyframes ticker {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: #1a1a1a;
    padding: 15px 0;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.ticker-move {
    display: inline-block;
    white-space: nowrap;
    /* A duração será definida dinamicamente abaixo */
    animation-name: ticker;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    font-size: 20px;
    color: #00ff41;
    font-family: 'Courier New', Courier, monospace;
}
.ticker-move span {
    margin: 0 40px;
}
</style>
""", unsafe_allow_html=True)


# --- Função para buscar apenas os dados mais recentes ---
@st.cache_data(ttl="10s") # Cache curto para a função de busca
def buscar_dados_recentes():
    # Para um sistema real, a API deveria ter um endpoint que ordena por data DESC.
    # Como não temos, vamos pegar a primeira página como "a mais recente".
    url = f"{API_URL}?limit=50&offset=0" # Busca as 50 mais recentes (baseado na sua query)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.DataFrame(response.json().get("dados", []))
            # Garante que a coluna de data/hora esteja no formato correto para ordenação
            df['dt_cadastro_integrante'] = pd.to_datetime(df['dt_cadastro_integrante'])
            return df.sort_values(by='dt_cadastro_integrante', ascending=False)
    except Exception as e:
        st.error(f"Erro ao contatar a API: {e}")
        return pd.DataFrame()

# --- Lógica da Página ---
st.title("📡 Monitor de Novas Adesões em Tempo Real")

# Usamos o 'session_state' para guardar informações entre as atualizações
if 'ultima_adesao_vista' not in st.session_state:
    st.session_state.ultima_adesao_vista = None
if 'ticker_html' not in st.session_state:
    st.session_state.ticker_html = '<div class="ticker-wrap"><div class="ticker-move" style="animation-duration: 60s;"><span>Aguardando novas adesões...</span></div></div>'

# Placeholders para os elementos que vamos atualizar
tabela_placeholder = st.empty()
ticker_placeholder = st.empty()

# Loop infinito para atualização em tempo real
while True:
    df_recentes = buscar_dados_recentes()

    if not df_recentes.empty:
        # Pega o ID da adesão mais recente da busca atual
        id_mais_recente_atual = df_recentes.iloc[0]['codigo_integrante']

        # Se não tivermos um ID salvo, salvamos o atual e seguimos
        if st.session_state.ultima_adesao_vista is None:
            st.session_state.ultima_adesao_vista = id_mais_recente_atual

        # Compara o ID mais recente da busca com o último que vimos
        if id_mais_recente_atual > st.session_state.ultima_adesao_vista:
            
            # Filtra apenas as adesões que são REALMENTE novas
            novas_adesoes = df_recentes[df_recentes['codigo_integrante'] > st.session_state.ultima_adesao_vista]
            
            # Monta o texto para o ticker com as novas adesões
            ticker_items = []
            for _, row in novas_adesoes.iterrows():
                ticker_items.append(f"<span>NOVA ADESÃO: {row['nm_integrante']} ({row['nm_unidade'].upper()})</span>")
            
            texto_ticker = " +++ ".join(ticker_items)
            
            # --- CÁLCULO DA VELOCIDADE DINÂMICA ---
            # Ajuste o '50' para mais ou menos para controlar a velocidade base
            velocidade_base = 50 
            duracao_animacao = max(20, len(texto_ticker) / velocidade_base)

            # Atualiza o HTML do ticker no session_state
            st.session_state.ticker_html = f'<div class="ticker-wrap"><div class="ticker-move" style="animation-duration: {duracao_animacao:.2f}s;">{texto_ticker}</div></div>'
            
            # Toca um som de notificação para cada nova adesão
            for _ in range(len(novas_adesoes)):
                st.toast('🚀 Nova Adesão!', icon='🎉')
                time.sleep(0.5) # Pequena pausa entre toasts se houverem muitos
            
            # Atualiza o ID da última adesão que vimos
            st.session_state.ultima_adesao_vista = id_mais_recente_atual
        
        # Atualiza os elementos na tela
        with ticker_placeholder.container():
            st.markdown(st.session_state.ticker_html, unsafe_allow_html=True)
        
        with tabela_placeholder.container():
            st.subheader("Últimas 10 Adesões Registradas")
            st.dataframe(df_recentes.head(10), use_container_width=True)
            
    # Pausa a execução por 10 segundos antes de rodar tudo de novo
    time.sleep(10)
