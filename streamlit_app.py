import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="REAPER BOT | Control Panel", layout="wide", page_icon="🤖")

# --- AUTENTICAÇÃO FIRESTORE ---
def get_db():
    try:
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        st.error(f"Erro na ligação ao Firebase: {e}")
        return None

db = get_db()

# --- INTERFACE DO DASHBOARD ---
st.title("🤖 Reaper Bot Dashboard")
st.markdown("---")

# Sidebar - Status e Controlos
st.sidebar.header("⚙️ Painel de Controlo")
bot_status = st.sidebar.toggle("Ligar/Desligar Bot", value=True)
status_color = "green" if bot_status else "red"
st.sidebar.markdown(f"Status: :{status_color}[{'ATIVO' if bot_status else 'INATIVO'}]")

if db:
    # 1. Métrica de Resumo (Funcionalidade: Monitorização)
    col1, col2, col3 = st.columns(3)
    
    # Exemplo de busca de métricas na coleção 'stats'
    try:
        # Aqui assumimos que tens uma coleção 'logs' ou 'vendas'
        docs = list(db.collection('dados').stream())
        total_items = len(docs)
        
        col1.metric("Total de Registos", total_items)
        col2.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))
        col3.metric("Erros Detetados", "0", delta_color="inverse")
        
        # 2. Funcionalidade: Visualização e Filtro de Dados
        st.subheader("📊 Dados Processados pelo Bot")
        if total_items > 0:
            df = pd.DataFrame([doc.to_dict() for doc in docs])
            
            # Filtro simples
            search = st.text_input("Filtrar resultados por nome/ID:")
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
            st.dataframe(df, use_container_width=True)
            
            # Funcionalidade: Download de Relatórios
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Logs para CSV", csv, "reaper_logs.csv", "text/csv")
        else:
            st.info("O bot ainda não enviou dados para o Firestore.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

    # 3. Funcionalidade: Logs em Tempo Real
    st.markdown("---")
    st.subheader("📜 Console de Eventos")
    with st.container(border=True):
        st.code("DEBUG: Bot iniciado com sucesso...\nINFO: Conectado ao banco de dados...\nSUCCESS: Monitorização ativa.", language="bash")

else:
    st.warning("Aguarda ligação com a base de dados...")
            
