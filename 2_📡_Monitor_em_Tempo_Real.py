# Dentro do arquivo pages/2_📡_Monitor_em_Tempo_Real.py

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# URL da sua API de dados
API_URL = "https://api-adesoes-comercial.vercel.app/dados"

# --- CSS para o efeito do ticker ---
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
    animation: ticker 25s linear infinite;
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
# Note que esta função NÃO é cacheada, para sempre buscar os dados mais novos.
def buscar_dados_recentes(offset):
    page_size = 500 # Buscamos um número menor para ser mais rápido
    url = f"{API_URL}?limit={page_size}&offset={offset}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json().get("dados", []))
    except Exception as e:
        st.error(f"Erro ao contatar a API: {e}")
        return pd.DataFrame()

# --- Lógica da Página ---
st.title("📡 Monitor de Novas Adesões em Tempo Real")
st.markdown("Esta página atualiza automaticamente a cada 10 segundos.")

# Usamos o 'session_state' para guardar informações entre as atualizações
if 'total_registros_anterior' not in st.session_state:
    st.session_state.total_registros_anterior = 0
if 'novas_adesoes_texto' not in st.session_state:
    st.session_state.novas_adesoes_texto = "Aguardando novas adesões..."

# Placeholders para os elementos que vamos atualizar
kpi_placeholder = st.empty()
ticker_placeholder = st.empty()
tabela_placeholder = st.empty()

# Loop infinito para atualização em tempo real
while True:
    # Busca o número total de registros
    df_total_count_check = buscar_dados_recentes(0)
    if not df_total_count_check.empty:
        # Para saber o total, teríamos que buscar tudo. Vamos simular um total.
        # Uma API otimizada teria um endpoint /count. Por agora, vamos buscar a última página.
        # Esta é uma simplificação. Em um cenário real, a API deveria prover o total.
        # Vamos assumir que a primeira busca nos dá uma ideia do total.
        total_registros_atual = len(df_total_count_check) + 50000 # Simulação para exibição
    else:
        total_registros_atual = st.session_state.total_registros_anterior

    # Busca os dados mais recentes (últimas 500 adesões)
    # Para um sistema real, a API deveria ter um endpoint que ordena por data DESC.
    # Como não temos, vamos pegar a primeira página como "a mais recente".
    df_recentes = df_total_count_check

    if not df_recentes.empty:
        # Identifica se houve novas adesões desde a última checagem
        if total_registros_atual > st.session_state.total_registros_anterior:
            num_novas_adesoes = total_registros_atual - st.session_state.total_registros_anterior
            
            # Pega as N novas adesões do topo da lista
            novas_adesoes = df_recentes.head(num_novas_adesoes)
            
            # Monta o texto para o ticker
            ticker_items = []
            for _, row in novas_adesoes.iterrows():
                ticker_items.append(f"<span>NOVA ADESÃO: {row['nm_unidade'].upper()}</span>")
            st.session_state.novas_adesoes_texto = " +++ ".join(ticker_items)
            
            # Toca um som de notificação
            st.toast('🚀 Nova Adesão!', icon='🎉')
        
        # Atualiza o total para a próxima checagem
        st.session_state.total_registros_anterior = total_registros_atual

        # Atualiza os elementos na tela
        with kpi_placeholder.container():
            st.metric(label="Total de Registros (Estimado)", value=f"{total_registros_atual:,}".replace(",", "."))
        
        with ticker_placeholder.container():
            st.markdown(f'<div class="ticker-wrap"><div class="ticker-move">{st.session_state.novas_adesoes_texto}</div></div>', unsafe_allow_html=True)
        
        with tabela_placeholder.container():
            st.subheader("Últimas 10 Adesões Registradas")
            st.dataframe(df_recentes.head(10), use_container_width=True)
            
    # Pausa a execução por 10 segundos antes de rodar tudo de novo
    time.sleep(10)
