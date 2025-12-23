import hashlib
import json
import os

# Nome do arquivo onde os dados serão salvos
USER_DB_FILE = "users_db.json"

def _get_password_hash(password):
    """Gera o hash SHA-256 da senha para não salvá-la em texto puro."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Carrega usuários do arquivo JSON ou cria padrão se não existir."""
    if not os.path.exists(USER_DB_FILE):
        # Cria usuário padrão admin/1234 se o arquivo não existir
        default_db = {
            "admin": _get_password_hash("1234")
        }
        try:
            with open(USER_DB_FILE, "w") as f:
                json.dump(default_db, f)
        except Exception as e:
            print(f"Erro ao criar banco de dados: {e}")
            return default_db
        return default_db
    
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler banco de dados: {e}")
        return {}

def save_new_user(username, password):
    """
    Tenta salvar um novo usuário.
    Retorna (True, "Mensagem") se sucesso ou (False, "Erro") se falha.
    """
    users = load_users()
    
    if username in users:
        return False, "Usuário já existe."
    
    if len(password) < 4:
        return False, "A senha deve ter pelo menos 4 caracteres."
    
    # Gera o hash e salva
    users[username] = _get_password_hash(password)
    
    try:
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)
        return True, "Usuário criado com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar no disco: {e}"

def verify_credentials(username, password):
    """Verifica se o usuário e senha correspondem."""
    users = load_users()
    pwd_hash = _get_password_hash(password)
    
    if username in users and users[username] == pwd_hash:
        return True
    return False
