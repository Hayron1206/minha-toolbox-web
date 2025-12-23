import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import streamlit as st
import hashlib

# --- CONEXÃO COM O FIREBASE ---
# Verifica se já não foi inicializado para evitar erros de recarregamento no Streamlit
if not firebase_admin._apps:
    try:
        # Cenário 1: Rodando na Nuvem (Streamlit Cloud)
        if "firebase" in st.secrets:
            # Converte o objeto de segredos do Streamlit para um dicionário Python
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        
        # Cenário 2: Rodando Localmente (Seu PC)
        else:
            # Você precisa baixar o arquivo JSON do console do Firebase e salvar como 'firebase_key.json'
            # Se o arquivo não existir, vai dar erro, o que é esperado se não configurado
            cred = credentials.Certificate("firebase_key.json")
            
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro de Conexão com Firebase: {e}")
        st.warning("Dica: Verifique se o arquivo 'firebase_key.json' existe (local) ou se os 'Secrets' estão configurados (nuvem).")
        st.stop()

# Cliente do Banco de Dados Firestore
db = firestore.client()

def _get_password_hash(password):
    """Gera o hash SHA-256 da senha para segurança."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """Verifica usuário e senha direto na nuvem (Firestore)."""
    try:
        # Busca o documento com o ID igual ao nome do usuário na coleção 'users'
        doc_ref = db.collection("users").document(username)
        doc = doc_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            # Compara o hash da senha digitada com o hash salvo no banco
            if user_data.get("password") == _get_password_hash(password):
                return True
    except Exception as e:
        print(f"Erro ao verificar credenciais: {e}")
    
    return False

def save_new_user(username, password):
    """Cria um novo usuário na nuvem (Firestore)."""
    try:
        if len(password) < 4:
            return False, "A senha deve ter pelo menos 4 caracteres."
            
        doc_ref = db.collection("users").document(username)
        
        # Verifica se já existe um documento com esse nome de usuário
        if doc_ref.get().exists:
            return False, "Este usuário já existe."
        
        # Salva os dados no Firestore
        doc_ref.set({
            "password": _get_password_hash(password),
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "Usuário criado com sucesso na nuvem!"
        
    except Exception as e:
        return False, f"Erro ao salvar no banco: {e}"
