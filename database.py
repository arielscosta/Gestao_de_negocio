import sqlite3
from datetime import datetime

def conectar():
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    return conn

def registrar_log(usuario, acao):
    """Função centralizada para registro de atividades no sistema."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("INSERT INTO movimentacoes (data_hora, usuario, tipo, motivo) VALUES (?, ?, 'LOG', ?)",
                       (data_hora, usuario, 'LOG_SISTEMA', acao))
        conn.commit()
    finally:
        conn.close()

# No seu database.py
def inicializar_bd():
    conn = conectar()
    cursor = conn.cursor()
    
    # Criando a tabela de clientes com o campo status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT,
            telefone TEXT,
            data_nasc TEXT,
            email TEXT,
            empresa TEXT,
            status TEXT DEFAULT 'Pendente'
        )
    ''')
    
    # Aproveite para garantir que a tabela de usuários também está ok
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            cargo TEXT,
            matricula TEXT,
            nome_completo TEXT,
            cpf TEXT,
            celular TEXT
        )
    ''')

    # Criando a tabela de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            valor_total REAL,
            data TEXT,
            status TEXT DEFAULT 'Aberto',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    # Criando a tabela de pagamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            valor REAL,
            data_pagamento TEXT,
            metodo TEXT,
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    # Criando a tabela de itens do pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        tipo TEXT, -- 'unidade' ou 'caixa'
        subtotal REAL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
        )
    ''')
    
          # Bloco de segurança: Garante que as novas colunas existam caso o banco já tenha sido criado antes
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN matricula TEXT UNIQUE")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nome_completo TEXT")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN cpf TEXT")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN celular TEXT")
        conn.commit()
    except:
        # Se as colunas já existirem, o SQLite dará erro e o código apenas ignora e segue adiante
        pass

    # --- TABELA PRODUTOS (Padronizada) ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        status TEXT DEFAULT 'ativo',
        unidades_por_caixa INTEGER DEFAULT 1,
        estoque_unidades_total INTEGER DEFAULT 0,
        valor_compra REAL DEFAULT 0.0,
        valor_venda REAL DEFAULT 0.0)''')

    # --- TABELA MOVIMENTAÇÕES ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT, produto TEXT, tipo TEXT,
        quantidade_unid INTEGER, usuario TEXT, motivo TEXT)''')

    # Admin padrão
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, password, cargo) VALUES ('admin', 'admin123', 'Admin')")

    conn.commit()
    conn.close()
    print("✅ Banco de dados e logs inicializados!")