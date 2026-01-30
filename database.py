import sqlite3

DB_NAME = "gestao_de_negocio.db"

def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    conn = conectar()
    cursor = conn.cursor()
    # Tabela de Pedidos, Itens, Pagamentos e agora PRODUTOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            estoque_qtd INTEGER NOT NULL DEFAULT 0,
            preco_unitario REAL NOT NULL,
            preco_caixa REAL NOT NULL
        )
    ''')
    # ... (as outras tabelas que já criamos)
    conn.commit()
    conn.close()