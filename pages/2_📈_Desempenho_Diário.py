import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time

# Tenta importar a função do arquivo de utilidades.
try:
    from utils import buscar_todos_os_dados
except ImportError:
    st.error("Arquivo 'utils.py' não encontrado. Por favor, garanta que a estrutura de múltiplas páginas está correta.")
    def buscar_todos_os_dados(): return None


# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(layout="wide", page_title="Pregão de Vendas")

st.markdown("""
<style>
@keyframes ticker {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: #0E1117;
    padding: 20px 0;
    border: 1px solid #2e3138;
    border-radius: 10px;
}
.ticker-move {
    display: inline-block;
    white-space: nowrap;
    animation-name: ticker;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    font-size: 24px;
    font-family: 'Courier New', Courier, monospace;
}
.ticker-item { margin: 0 50px; }
.up { color: #00ff41; }
.down { color: #ff4b4b; }
.neutral { color: #a0a3a8; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ATUALIZAÇÃO ---
st.sidebar.header("Controles")
auto_refresh = st.sidebar.checkbox("Ligar atualização automática (a cada 90s)")
if st.sidebar.button("Forçar Atualização Agora"):
    st.cache_data.clear()

# --- TÍTULO ---
st.title("📊 Pregão de Desempenho Diário")
st.markdown(f"Dados de hoje ({date.today().strftime('%d/%m/%Y')}) comparados com o dia anterior.")
st.markdown("---")

# Carrega os dados usando a função do arquivo utils.py
df_original = buscar_todos_os_dados()

if df_original is not None and not df_original.empty:
    
    # --- CORREÇÃO IMPORTANTE: Usando a coluna de data correta ---
    date_column = 'dt_cadastro_integrante'
    df_original[date_column] = pd.to_datetime(df_original[date_column], errors='coerce')

    # --- CÁLCULOS ---
    hoje = pd.to_datetime(date.today())
    ontem = pd.to_datetime(date.today() - timedelta(days=1))

    df_hoje = df_original[df_original[date_column].dt.date == hoje.date()]
    df_ontem = df_original[df_original[date_column].dt.date == ontem.date()]

    unidades = sorted(pd.concat([df_hoje['nm_unidade'], df_ontem['nm_unidade']]).dropna().unique())
    
    # --- KPIs GERAIS DO DIA ---
    total_vendas_hoje = df_hoje['vl_plano'].sum()
    total_adesoes_hoje = len(df_hoje)

    col1, col2 = st.columns(2)
    col1.metric("VVR Total Hoje", f"R$ {total_vendas_hoje:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Adesões Hoje", f"{total_adesoes_hoje}")

    # --- MONTAGEM DO TEXTO PARA O TICKER ---
    ticker_items = []
    for unidade in unidades:
        vendas_hoje = df_hoje[df_hoje['nm_unidade'] == unidade]['vl_plano'].sum()
        vendas_ontem = df_ontem[df_ontem['nm_unidade'] == unidade]['vl_plano'].sum()
        
        delta_str = ""
        css_class = "neutral"

        if vendas_ontem > 0:
            diferenca = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
            if diferenca >= 0:
                css_class = "up"
                delta_str = f"▲ {diferenca:.2f}%"
            else:
                css_class = "down"
                delta_str = f"▼ {diferenca:.2f}%"
        elif vendas_hoje > 0:
            css_class = "up"
            delta_str = "▲ N/A"

        vendas_hoje_str = f"R$ {vendas_hoje:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ticker_items.append(f'<span class="ticker-item {css_class}">{unidade.upper()}: {vendas_hoje_str} {delta_str}</span>')
    
    texto_ticker = "".join(ticker_items)
    
    # --- CÁLCULO DA VELOCIDADE DINÂMICA ---
    velocidade_base = 10 # Velocidade mais lenta como padrão
    duracao_animacao = max(25, len(texto_ticker) / velocidade_base)
    
    # --- EXIBIÇÃO DO TICKER ---
    st.markdown(f'<div class="ticker-wrap"><div class="ticker-move" style="animation-duration: {duracao_animacao:.2f}s;">{texto_ticker}</div></div>', unsafe_allow_html=True)
            
else:
    st.warning("Aguardando dados da API...")

# --- LÓGICA DE AUTO-REFRESH CONTROLADA ---
if auto_refresh:
    time.sleep(90)
    st.experimental_rerun()
