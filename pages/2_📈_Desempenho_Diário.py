# Dentro do arquivo pages/2_📈_Desempenho_Diário.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils import buscar_todos_os_dados # Importa a função do nosso arquivo de utilidades

st.set_page_config(layout="wide", page_title="Desempenho Diário")

# --- ESTILO CUSTOMIZADO (CSS) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stMetric {
        border: 1px solid #2e3138;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stMetric .st-ae { justify-content: center; }
    h3 {
        color: #b0b3b8;
        margin-bottom: -10px;
    }
</style>
""", unsafe_allow_html=True)


st.title("📊 Desempenho Diário por Franquia")
st.markdown("Comparativo de VVR (Valor do Plano) de hoje com o dia anterior.")

# Botão para forçar a atualização dos dados (limpando o cache)
if st.button("Atualizar Dados Agora"):
    st.cache_data.clear()

# Carrega os dados usando a função do arquivo utils.py
df_original = buscar_todos_os_dados()

if df_original is not None and not df_original.empty:
    
    # Define as datas de hoje e ontem
    hoje = pd.to_datetime(date.today())
    ontem = pd.to_datetime(date.today() - timedelta(days=1))
    
    # Filtra o DataFrame para obter apenas os dados de hoje e ontem
    df_hoje = df_original[df_original['dt_cadastro_integrante'].dt.date == hoje.date()]
    df_ontem = df_original[df_original['dt_cadastro_integrante'].dt.date == ontem.date()]

    # Pega a lista de todas as unidades que tiveram vendas nos dois dias
    unidades = sorted(pd.concat([df_hoje['nm_unidade'], df_ontem['nm_unidade']]).dropna().unique())
    
    st.markdown("---")

    # --- KPIs GERAIS DO DIA ---
    total_vendas_hoje = df_hoje['vl_plano'].sum()
    total_vendas_ontem = df_ontem['vl_plano'].sum()
    
    if total_vendas_ontem > 0:
        delta_geral = ((total_vendas_hoje - total_vendas_ontem) / total_vendas_ontem) * 100
        delta_geral_str = f"{delta_geral:.2f}%"
    else:
        delta_geral_str = "N/A" # Não há base para comparação

    st.header(f"Resultados de Hoje ({hoje.strftime('%d/%m/%Y')})")
    col1, col2, col3 = st.columns(3)
    col1.metric("VVR Total Hoje", f"R$ {total_vendas_hoje:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=delta_geral_str)
    col2.metric("Adesões Hoje", f"{len(df_hoje)}")
    col3.metric("Ticket Médio Hoje", f"R$ {(total_vendas_hoje/len(df_hoje) if len(df_hoje)>0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")
    st.header("Análise por Franquia")

    # Itera sobre cada unidade para criar um "card" de desempenho
    for unidade in unidades:
        vendas_hoje = df_hoje[df_hoje['nm_unidade'] == unidade]['vl_plano'].sum()
        vendas_ontem = df_ontem[df_ontem['nm_unidade'] == unidade]['vl_plano'].sum()
        
        delta_str = None
        if vendas_ontem > 0:
            diferenca = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
            delta_str = f"{diferenca:.2f}%"
        elif vendas_hoje > 0:
            delta_str = "100%" # Se ontem foi 0 e hoje não, o crescimento é "infinito"
        
        # Cria a visualização
        col_unidade, col_metrica = st.columns([2, 1]) # Coluna do nome com o dobro do tamanho
        
        with col_unidade:
            st.subheader(unidade)
            
        with col_metrica:
            st.metric(
                label="VVR Hoje vs. Ontem",
                value=f"R$ {vendas_hoje:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                delta=delta_str
            )
        st.markdown("<hr style='margin-top: -10px; border-top: 1px solid #2e3138;'>", unsafe_allow_html=True)

else:
    st.warning("Não foi possível carregar os dados. Verifique a API ou tente recarregar a página.")
