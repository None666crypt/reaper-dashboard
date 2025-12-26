import streamlit as st
import pandas as pd
import requests
import json
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURAÇÃO INTERFACE ---
st.set_page_config(page_title="REAPER PRO TERMINAL", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #161b22; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_db():
    try:
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        return None

db = init_db()

def get_market_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'ids': 'bitcoin,ethereum,solana,binancecoin,ripple', 'price_change_percentage': '24h'}
        return requests.get(url, params=params).json()
    except:
        return []

# --- HEADER MÉTRICAS ---
data_market = get_market_data()
if data_market:
    cols = st.columns(len(data_market[:4]) + 1)
    for i, coin in enumerate(data_market[:4]):
        cols[i].metric(coin['symbol'].upper(), f"${coin['current_price']:,}", f"{coin['price_change_percentage_24h']:.2f}%")
    cols[-1].metric("SISTEMA", "OPERACIONAL", "100%")

st.divider()

tab_port, tab_market, tab_tools = st.tabs(["🏦 MEU PORTFÓLIO", "📈 ANÁLISE DE MERCADO", "🛠️ FERRAMENTAS PRO"])

# --- ABA 1: PORTFÓLIO ---
with tab_port:
    col_add, col_view = st.columns([1, 2])
    with col_add:
        with st.container(border=True):
            st.write("📝 **Registrar Ativo**")
            ticker = st.text_input("Ticker (Ex: BTC)").upper()
            quant = st.number_input("Quantidade", min_value=0.0, format="%.4f")
            compra = st.number_input("Preço de Compra", min_value=0.0, format="%.2f")
            if st.button("Salvar no Terminal"):
                if db and ticker:
                    db.collection('portfolio').document(ticker).set({
                        'ativo': ticker, 'qtd': quant, 'p_compra': compra, 'data': datetime.now()
                    })
                    st.success("Guardado!")
                    st.rerun()

    with col_view:
        if db:
            docs = db.collection('portfolio').stream()
            items = [d.to_dict() for d in docs]
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
                if st.button("🗑️ Limpar Tudo"):
                    for d in db.collection('portfolio').stream(): d.reference.delete()
                    st.rerun()
            else:
                st.info("Portfólio vazio.")

# --- ABA 2: ANÁLISE DE MERCADO ---
with tab_market:
    st.subheader("📊 Intelligence & Market Signals")
    col_fng, col_signals = st.columns(2)
    
    with col_fng:
        try:
            fng_res = requests.get("https://api.alternative.me/fng/").json()
            val = int(fng_res['data'][0]['value'])
            classif = fng_res['data'][0]['value_classification']
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val,
                title = {'text': f"Sentimento: {classif}"},
                gauge = {'axis': {'range': [0, 100]},
                         'bar': {'color': "#00ffcc"},
                         'steps': [
                             {'range': [0, 30], 'color': "#ff4b4b"},
                             {'range': [30, 70], 'color': "#3d3d3d"},
                             {'range': [70, 100], 'color': "#00cc66"}]}
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("Erro ao carregar F&G Index")

    with col_signals:
        st.write("### 🚨 Whale Tracker (Live)")
        with st.container(border=True):
            st.markdown(f"**[{datetime.now().strftime('%H:%M')}]** 🐳 850 BTC transferidos para Binance")
            st.markdown(f"**[{datetime.now().strftime('%H:%M')}]** 🚨 Whale Alert: 12,000 ETH em movimento")
            st.markdown(f"**[NEWS]** Volume de trading subiu 12% nas últimas 24h")

# --- ABA 3: FERRAMENTAS PRO ---
with tab_tools:
    st.subheader("🛠️ Risk Management")
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        with st.container(border=True):
            st.write("### 📐 Position Sizing")
            cap = st.number_input("Capital Total ($)", value=1000.0)
            risk = st.slider("Risco por Trade (%)", 0.1, 5.0, 1.0)
            entry = st.number_input("Entrada", value=100.0)
            stop = st.number_input("Stop Loss", value=95.0)
            
            if entry > stop:
                pos_size = (cap * (risk/100)) / (entry - stop)
                st.success(f"Tamanho da Posição: **{pos_size:.4f}**")
            else:
                st.warning("O Stop Loss deve ser menor que a Entrada")
    
    with t_col2:
        with st.container(border=True):
            st.write("### 🔄 Arbitrage Spreads")
            df_arb = pd.DataFrame({
                'Par': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                'Spread': ['0.02%', '0.08%', '0.15%'],
                'Status': ['Baixo', 'Médio', 'Oportunidade']
            })
            st.table(df_arb)

st.sidebar.markdown("---")
st.sidebar.caption("REAPER PRO TERMINAL v10.5")
        
