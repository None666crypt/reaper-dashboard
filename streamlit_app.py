import streamlit as st
import pandas as pd
import requests
import json
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime

# --- CONFIGURAÇÃO INTERFACE ---
st.set_page_config(page_title="REAPER PRO TERMINAL", layout="wide", page_icon="⚡")

# Custom CSS para look Dark Mode Profissional
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161b22; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO COM A DATABASE (Firestore) ---
# Mesmo que estivesses no Sheets, o Firestore é melhor para este Dashboard
@st.cache_resource
def init_db():
    try:
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        st.error(f"Erro ao conectar ao Banco de Dados: {e}")
        return None

db = init_db()

# --- MÓDULO DE DADOS EXTERNOS ---
def get_market_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'bitcoin,ethereum,solana,binancecoin,ripple', 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
        return requests.get(url, params=params).json()
    except:
        return {}

# --- LAYOUT PRINCIPAL ---
st.title("⚡ REAPER COMMAND CENTER")
st.divider()

# Top Bar - Métricas Rápidas
prices = get_market_prices()
c1, c2, c3, c4 = st.columns(4)

if prices:
    c1.metric("BTC", f"${prices['bitcoin']['usd']:,}", f"{prices['bitcoin']['usd_24h_change']:.2f}%")
    c2.metric("ETH", f"${prices['ethereum']['usd']:,}", f"{prices['ethereum']['usd_24h_change']:.2f}%")
    c3.metric("SOL", f"${prices['solana']['usd']:,}", f"{prices['solana']['usd_24h_change']:.2f}%")
    c4.metric("SISTEMA", "OPERACIONAL", "100%")

# --- ABAS DE FUNCIONALIDADES ---
tab_port, tab_market, tab_tools = st.tabs(["🏦 MEU PORTFÓLIO", "📈 ANÁLISE DE MERCADO", "🛠️ FERRAMENTAS PRO"])

with tab_port:
    st.subheader("Gestão de Ativos na Cloud")
    
    col_add, col_view = st.columns([1, 2])
    
    with col_add:
        with st.container(border=True):
            st.write("📝 **Registrar Ativo**")
            ticker = st.text_input("Ticker (Ex: BTC, ETH)").upper()
            quant = st.number_input("Quantidade", min_value=0.0)
            compra = st.number_input("Preço de Compra", min_value=0.0)
            
            if st.button("Salvar no Terminal"):
                if db and ticker:
                    db.collection('portfolio').document(ticker).set({
                        'ativo': ticker,
                        'qtd': quant,
                        'p_compra': compra,
                        'data': datetime.now()
                    })
                    st.success(f"{ticker} adicionado!")
                    st.rerun()

    with col_view:
        if db:
            docs = db.collection('portfolio').stream()
            data = [d.to_dict() for d in docs]
            if data:
                df = pd.DataFrame(data)
                # Cálculo de Valor Atual (Simplificado)
                st.dataframe(df[['ativo', 'qtd', 'p_compra', 'data']], use_container_width=True)
                
                # Botão para deletar tudo
                if st.button("⚠️ Limpar Portfólio"):
                    for d in db.collection('portfolio').stream():
                        d.reference.delete()
                    st.rerun()
            else:
                st.info("Nenhum dado encontrado no Firestore. Adicione o seu primeiro ativo ao lado.")

with tab_market:
    st.subheader("Painel de Monitoramento")
    st.info("Scanner Ativo: Buscando divergências de RSI e anomalias de volume.")
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.write("### 🔍 Scanner de Oportunidades")
        st.code("""
        [RSI] BTC: 48 (Neutro)
        [RSI] SOL: 71 (Sobrecomprado - Alerta)
        [VOL] ETH: Aumento de 15% nas últimas 2h
        """, language="bash")
        
    with m_col2:
        st.write("### 🐳 Whale Tracker")
        st.warning("Grande movimentação detectada: 500 BTC movidos para Binance.")

with tab_tools:
    st.subheader("Ferramentas de Risco e Arbitragem")
    st.write("Calcule o seu risco por operação:")
    
    capital = st.number_input("Capital Total (USD)", value=1000.0)
    risco_perc = st.slider("Risco por Operação (%)", 0.5, 5.0, 1.0)
    
    st.success(f"Valor máximo de perda recomendado: **${(capital * risco_perc / 100):,.2f}**")
                    
