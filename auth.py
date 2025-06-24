import sqlite3
import bcrypt
import streamlit as st

# Nome do arquivo do banco de dados SQLite
DB_NAME = "auth.db"

def get_db_connection():
    """
    Cria e retorna um objeto de conexão com o banco de dados SQLite.
    """
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def init_db():
    """
    Inicializa o banco de dados. Cria a tabela de usuários se não existir
    e adiciona um usuário 'admin' padrão se a tabela estiver vazia.
    """
    if "db_initialized" in st.session_state:
        return

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Cria a tabela 'users' com um campo 'role'
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """)
            
            # Verifica se algum usuário existe
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            # Se não houver usuários, cria o admin padrão
            if user_count == 0:
                admin_username = "admin"
                admin_password = "admin"
                hashed_pw = hash_password(admin_password)
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (admin_username, hashed_pw, 'admin')
                )
                print(f"Usuário administrador padrão '{admin_username}' com senha '{admin_password}' foi criado.")
            
            conn.commit()
            conn.close()
            st.session_state.db_initialized = True
            print("Banco de dados SQLite inicializado com sucesso.")
    except sqlite3.Error as e:
        st.error(f"Erro ao inicializar o banco de dados SQLite: {e}")
        st.stop()

# --- Funções de HASH de Senha ---

def hash_password(password: str) -> bytes:
    """Gera o hash de uma senha usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, hashed_password: bytes) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# --- Funções de Gerenciamento de Usuário ---

def create_user(username: str, password: str, role: str = "user") -> bool:
    """
    Cria um novo usuário no banco de dados com um cargo específico.
    """
    conn = get_db_connection()
    if not conn: return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False  # Usuário já existe

        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao criar usuário: {e}")
        return False
    finally:
        conn.close()

def login_user(username: str, password: str) -> tuple[bool, str | None]:
    """
    Verifica as credenciais do usuário.
    Retorna uma tupla: (True, role) em caso de sucesso, ou (False, None) em caso de falha.
    """
    conn = get_db_connection()
    if not conn: return False, None

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            hashed_password_from_db, user_role = result
            if check_password(password, hashed_password_from_db):
                return True, user_role
        
        return False, None
    except sqlite3.Error as e:
        print(f"Erro ao fazer login: {e}")
        return False, None
    finally:
        conn.close()

def change_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Altera a senha de um usuário existente.
    """
    conn = get_db_connection()
    if not conn: return False

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if not result or not check_password(old_password, result[0]):
            return False

        new_hashed_pw = hash_password(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_pw, username))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao alterar senha: {e}")
        return False
    finally:
        conn.close()

def get_all_users() -> list:
    """Retorna uma lista de todos os usernames."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users ORDER BY username")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_details(username: str) -> dict | None:
    """Busca os detalhes (role) de um usuário."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"role": result[0]}
    return None

def update_user_by_admin(username: str, new_password: str | None, new_role: str) -> bool:
    """
    Permite que um admin atualize a senha e/ou o cargo de um usuário.
    """
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        if new_password:
            new_hashed_pw = hash_password(new_password)
            cursor.execute("UPDATE users SET password = ?, role = ? WHERE username = ?", (new_hashed_pw, new_role, username))
        else:
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar usuário pelo admin: {e}")
        return False
    finally:
        conn.close()
