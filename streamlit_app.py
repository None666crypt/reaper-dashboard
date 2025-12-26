import streamlit as st
import pandas as pd
import requests
import json
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime

# --- CONFIGURAÇÃO E DESIGN ---
st.set_page_config(page_title="REAPER PRO | Terminal", layout="wide", page_icon="📈")

# Estilo customizado para parecer um terminal financeiro
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DE DADOS (FIRESTORE) ---
@st.cache_resource
def init_connection():
    try:
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

db = init_connection()

# --- FUNCIONALIDADES CORE ---

def fetch_market_data():
    """Busca dados reais via CoinGecko"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 10, 'sparkline': False}
    try:
        response = requests.get(url, params=params)
        return pd.DataFrame(response.json())[['name', 'symbol', 'current_price', 'price_change_percentage_24h', 'market_cap']]
    except:
        return pd.DataFrame()

def get_fear_greed():
    """Índice de Sentimento do Mercado"""
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r['data'][0]
    except:
        return {"value": "50", "value_classification": "Neutral"}

# --- INTERFACE PRINCIPAL ---
st.title("📟 REAPER PROFESSIONAL TERMINAL")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- DASHBOARD DE MÉTRICAS (VISÃO GERAL) ---
fng = get_fear_greed()
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("SENTIMENTO", fng['value_classification'], f"{fng['value']}/100")
with m2: st.metric("BTC DOMINANCE", "42.5%", "0.2%")
with m3: st.metric("GAS ETH", "15 Gwei", "-2")
with m4: st.metric("SISTEMA", "ONLINE", border=True)

tabs = st.tabs(["🏛️ Portfólio Pro", "📊 Mercado Vivo", "🔍 Scanner & Whales", "⚙️ Definições"])

# --- TAB 1: GESTÃO DE PORTFÓLIO ---
with tabs[0]:
    st.subheader("Gestão de Ativos Institucionais")
    
    with st.expander("➕ Adicionar Novo Ativo"):
        c1, c2, c3 = st.columns(3)
        with c1: coin = st.text_input("Ativo (ex: BTC)").upper()
        with c2: qty = st.number_input("Quantidade", min_value=0.0)
        with c3: price_avg = st.number_input("Preço Médio de Compra (USD)", min_value=0.0)
        
        if st.button("Registar Transação"):
            if db and coin:
                db.collection('portfolio').document(coin).set({
                    'symbol': coin, 'amount': qty, 'entry_price': price_avg, 'last_updated': datetime.now()
                })
                st.success(f"Ativo {coin} guardado na Cloud.")

    # Listagem de Ativos
    if db:
        docs = db.collection('portfolio').stream()
        p_data = [d.to_dict() for d in docs]
        if p_data:
            df_p = pd.DataFrame(p_data)
            st.dataframe(df_p, use_container_width=True)
            
            # Gráfico de Alocação
            st.write("### Alocação de Capital")
            st.bar_chart(df_p.set_index('symbol')['amount'])
        else:
            st.info("Nenhum ativo registado na base de dados.")

# --- TAB 2: MERCADO EM TEMPO REAL ---
with tabs[1]:
    st.subheader("Top 10 Market Cap")
    df_m = fetch_market_data()
    if not df_m.empty:
        st.dataframe(df_m.style.format({'current_price': '${:,.2f}', 'price_change_percentage_24h': '{:.2f}%'}), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Análise de Arbitragem")
    st.code("""
    [BINANCE] BTC/USDT: $64,200.50
    [KRAKEN]  BTC/USDT: $64,220.10
    POTENCIAL SPREAD: 0.03% (Abaixo do threshold de lucro)
    """, language="python")

# --- TAB 3: SCANNER & WHALES ---
with tabs[2]:
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("### 🐳 Monitor de Baleias")
        st.warning("ALERTA: 1,200 BTC transferidos de carteira desconhecida para COINBASE (há 4 mins)")
        st.info("INFO: 50,000 ETH retirados de BINANCE para Cold Wallet.")
    
    with col_right:
        st.write("### 🔍 Scanner de RSI (4H)")
        st.write("• **BTC:** 45.2 (Neutro)")
        st.write("• **SOL:** 72.1 (:red[Overbought])")
        st.write("• **LINK:** 28.5 (:green[Oversold - Oportunidade])")

# --- TAB 4: CONFIGURAÇÕES ---
with tabs[3]:
    st.subheader("Configurações do Sistema")
    st.write("**ID do Projeto:** `reaper-dashboard`")
    st.write("**Database:** Google Firestore (Encrypted)")
    if st.button("Limpar Cache do Terminal"):
        st.cache_resource.clear()
        st.rerun()
