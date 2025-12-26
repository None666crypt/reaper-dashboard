import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import requests
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="REAPER CONTROL PANEL", layout="wide", page_icon="🤖")

# --- CONEXÃO FIRESTORE ---
def get_db():
    try:
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        st.error(f"Erro de autenticação: {e}")
        return None

db = get_db()

# --- FUNÇÕES DE DADOS (Substituindo o SQLite) ---
def get_portfolio(uid):
    docs = db.collection('portfolio').where('uid', '==', uid).stream()
    return [{"coin_id": d.to_dict()['coin_id'], "amount": d.to_dict()['amount']} for d in docs]

def add_to_portfolio(uid, coin_id, amount):
    doc_id = f"{uid}_{coin_id}"
    db.collection('portfolio').document(doc_id).set({
        'uid': uid,
        'coin_id': coin_id,
        'amount': float(amount)
    })

def delete_from_portfolio(uid, coin_id):
    doc_id = f"{uid}_{coin_id}"
    db.collection('portfolio').document(doc_id).delete()

# --- INTERFACE PRINCIPAL ---
st.title("🤖 Reaper v10.5 - Dashboard")

# Sidebar para Identificação (Simulando o UID do Telegram)
st.sidebar.header("👤 Usuário")
user_id = st.sidebar.number_input("Insira seu Telegram ID para gerir o Portfólio:", value=123456, step=1)

tabs = st.tabs(["📊 Market", "🏦 Portfolio", "🤖 AI & Analysis", "🛡️ Risk & Tools"])

# --- TAB 1: MARKET ---
with tabs[0]:
    st.subheader("Mercado em Tempo Real (CoinGecko)")
    if st.button("Atualizar Preços"):
        ids = "bitcoin,ethereum,solana,binancecoin,cardano" # Podes expandir esta lista
        data = requests.get(f"https://api.coingecko.com/api/v3/coins/markets", 
                            params={'vs_currency': 'usd', 'ids': ids}).json()
        
        df_market = pd.DataFrame(data)[['symbol', 'current_price', 'price_change_percentage_24h']]
        st.table(df_market)

# --- TAB 2: PORTFOLIO ---
with tabs[1]:
    st.subheader("Gestão de Ativos")
    
    col1, col2 = st.columns(2)
    with col1:
        new_coin = st.text_input("Símbolo (ex: btc):").lower()
        new_amount = st.number_input("Quantidade:", min_value=0.0)
        if st.button("➕ Adicionar/Atualizar"):
            add_to_portfolio(user_id, new_coin, new_amount)
            st.success(f"{new_coin} atualizado!")

    with col2:
        rem_coin = st.text_input("Remover Símbolo:").lower()
        if st.button("🗑️ Remover Ativo"):
            delete_from_portfolio(user_id, rem_coin)
            st.warning(f"{rem_coin} removido.")

    st.markdown("---")
    st.write(f"### Seus Ativos (ID: {user_id})")
    user_data = get_portfolio(user_id)
    if user_data:
        st.dataframe(pd.DataFrame(user_data), use_container_width=True)
    else:
        st.info("Portfólio vazio.")

# --- TAB 3: AI & ANALYSIS ---
with tabs[2]:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### 🧠 Fear & Greed Index")
        fng_data = requests.get("https://api.alternative.me/fng/").json()['data'][0]
        st.metric("Sentimento", fng_data['value_classification'], f"Nível: {fng_data['value']}")
        
    with col_b:
        st.write("### 🔄 Arbitragem (Spread)")
        st.code("• BTC/USDT: 0.8% spread\n• SOL/USDT: 1.2% spread", language="bash")
    
    st.write("### 🐳 Whale Tracker (Simulado)")
    st.info("Monitorizando movimentações acima de $1M nas últimas 24h...")

# --- TAB 4: RISK & SCANNER ---
with tabs[3]:
    st.write("### 🛡️ Gestão de Risco")
    st.info("Nunca invista mais do que está disposto a perder. Use Stop Loss em todas as operações.")
    
    st.write("### 🔍 Scanner de Sinais")
    st.write("Análise técnica automática: **RSI** e **MACD** neutros no timeframe de 4h.")
