import sqlite3

def conectar():
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    # Garante as colunas de valor no banco
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE produtos ADD COLUMN valor_compra REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE produtos ADD COLUMN valor_venda REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN motivo TEXT")
        conn.commit()
    except:
        pass
    conn = conectar()
    cursor = conn.cursor()

    # --- TABELA CLIENTES ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT,
            telefone TEXT,
            data_nasc TEXT,
            email TEXT,
            empresa TEXT
        )
    ''')

    # --- TABELA USUÁRIOS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            cargo TEXT NOT NULL
        )
    ''')

    # --- TABELA PRODUTOS (ESTOQUE) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'ativo',
            unidades_por_caixa INTEGER DEFAULT 1,
            estoque_unidades_total INTEGER DEFAULT 0,
            valor_unitario REAL DEFAULT 0.0
        )
    ''')

    # --- TABELA PEDIDOS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            produtos TEXT,
            valor_total REAL,
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    # --- TABELA PAGAMENTOS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            pedido_id INTEGER,
            data TEXT,
            valor REAL,
            metodo TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    # --- TABELA MOVIMENTAÇÕES (HISTÓRICO GERAL) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            produto TEXT,
            tipo TEXT,
            quantidade_unid INTEGER,
            usuario TEXT
        )
    ''')

    # Cria usuário admin padrão se não existir
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, password, cargo) VALUES ('admin', 'admin123', 'Admin')")

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")