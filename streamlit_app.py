import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

# Configuração da página
st.set_page_config(page_title="Reaper Dashboard", layout="wide")

# Função para autenticar no Firestore usando as Secrets do Streamlit
def get_db():
    try:
        # Carrega as credenciais das Secrets do Streamlit
        creds_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=creds_dict['project_id'])
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return None

db = get_db()

st.title("🎯 Reaper Dashboard")

if db:
    # Exemplo: Buscar dados de uma coleção chamada 'vendas' ou 'utilizadores'
    # Ajusta o nome 'dados' para a tua coleção real no Firestore
    try:
        docs = db.collection('dados').stream()
        data = [doc.to_dict() for doc in docs]
        
        if data:
            st.write("### Dados em Tempo Real")
            st.dataframe(data)
        else:
            st.info("Conectado com sucesso, mas a coleção está vazia.")
    except Exception as e:
        st.warning("Conectado! Mas não encontrei a coleção 'dados'. Verifique o nome no Firestore.")

st.sidebar.success("Conectado ao Firebase")
