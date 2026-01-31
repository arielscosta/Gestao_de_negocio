import sqlite3
from datetime import datetime

DB_NAME = "gestao.db"

def conectar():
    """
    Estabelece conexão com o SQLite.
    Adicionado 'timeout' para esperar o banco destravar e 'WAL' para permitir 
    leitura e escrita simultâneas.
    """
    # O timeout de 20 faz o Python esperar 20 segundos antes de dar erro de 'locked'
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.row_factory = sqlite3.Row
    
    # Ativa o modo Write-Ahead Logging (WAL) - essencial para Docker/WSL2
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except:
        pass
        
    return conn

def inicializar_bd():
    """Cria todas as tabelas e garante a estrutura correta."""
    conn = conectar()
    try:
        cursor = conn.cursor()

        # TABELAS DE ACESSO
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            cargo TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS logs_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            acao TEXT,
            data_hora TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id))''')

        # TABELAS DE NEGÓCIO
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            endereco TEXT,
            empresa TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            estoque_qtd INTEGER NOT NULL DEFAULT 0,
            preco_unitario REAL NOT NULL,
            qtd_por_caixa INTEGER NOT NULL,
            preco_caixa REAL NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            usuario_id INTEGER,
            data_pedido TEXT,
            valor_total REAL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            valor_pago REAL,
            data_pagamento TEXT,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id))''')

        cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, cargo) VALUES ('admin', 'admin123', 'Admin')")
        
        conn.commit()
    finally:
        conn.close()

def registrar_log(usuario_id, acao):
    """Registra auditoria com tratamento de erro para não travar o sistema principal."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("INSERT INTO logs_sistema (usuario_id, acao, data_hora) VALUES (?, ?, ?)",
                       (usuario_id, acao, data_hora))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Aviso de Log: {e}")
    finally:
        conn.close()