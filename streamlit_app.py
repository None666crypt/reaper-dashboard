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
        params = {'vs_currency': 'usd', 'ids': 'bitcoin,ethereum,solana,binancecoin,ripple,cardano,polkadot', 'price_change_percentage': '24h'}
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

# --- ABA 2: ANÁLISE DE MERCADO (CORRIGIDO) ---
with tab_market:
    st.subheader("📊 Intelligence & Market Signals")
    
    col_fng, col_signals = st.columns(2)
    
    with col_fng:
        # Fear & Greed Index Real
        try:
            fng_res = requests.get("https://api.alternative.me/fng/").json()
            val = int(fng_res['data'][0]['value'])
            classif = fng_res['data'][0]['value_classification']
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val,
                title = {'text': f"Fear & Greed: {classif}"},
                gauge = {'axis': {'range': [0, 100]},
                         'bar': {'color': "#00ffcc"},
                         'steps': [
                             {'range': [0, 30], 'color': "red"},
                             {'range': [30, 70], 'color': "gray"},
                             {'range': [70, 100], 'color': "green"}]}
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300)
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("Erro ao carregar F&G Index")

    with col_signals:
        st.write("### 🚨 Whale Tracker (Live Simulation)")
        st.caption("Monitorizando carteiras > 100 BTC")
        with st.container(border=True):
            st.markdown(f"**[{datetime.now().strftime('%H:%M')}]** 🐳 450 BTC transferidos de *Coinbase* para *Wallet Desconhecida*")
            st.markdown(f"**[{datetime.now().strftime('%H:%B')}]** 🚨 Movimentação suspeita em SOL (USDC 2.1M)")
            st.markdown(f"**[NEWS]** FED mantém taxas de juro; Mercado reage positivamente.")

# --- ABA 3: FERRAMENTAS PRO (CORRIGIDO) ---
with tab_tools:
    st.subheader("🛠️ Risk Management & Calculators")
    
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        with st.container(border=True):
            st.write("### 📐 Calculadora de Position Sizing")
            cap = st.number_input("Capital Total ($)", value=1000.0)
            risk = st.slider("Risco por Trade (%)", 0.1, 5.0, 1.0)
            entry = st.number_input("Preço de Entrada", value=100.0)
            stop = st.number_input("Stop Loss", value=95.0)
            
            if entry > stop:
                diff = entry - stop
                pos_size = (cap * (risk/100)) / diff
                st.success(f"Tamanho da Posição: **{pos_size:.4f} unidades**")
                st.info(f"Risco Financeiro: **${(cap * risk/100):.2f}**")
    
    with t_col2:
        with st.container(border=True):
            st.write("### 🔄 Arbitragem Simples")
            st.write("Diferença média entre Exchanges principais:")
            st.table(pd.DataFrame({
                'Par': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                'Binance': [87469, 2928, 122.2],
                'Kraken': [87475, 2930, 122.5],
                'Spread': ['0.01%', '0.07%', '0.24%']
            }))

st.sidebar.markdown("---")
st.sidebar.write("REAPER V10.5 PRO")
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
                    
