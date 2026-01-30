import sqlite3
import os
from datetime import datetime

# --- CONFIGURAÇÕES GERAIS ---
DB_NAME = "gestao_de_negocio.db"

# =================================================================
#               CAMADA DE DADOS (SQLITE / DATABASE)
# =================================================================

def conectar():
    """Retorna uma conexão com suporte a chaves estrangeiras ativo."""
    conn = sqlite3.connect(DB_NAME)
    # Ativa o suporte a chaves estrangeiras (essencial para o ON DELETE CASCADE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def inicializar_bd():
    """Cria as tabelas necessárias se não existirem."""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_pedido TEXT NOT NULL,
            nome_cliente TEXT NOT NULL,
            valor_total REAL DEFAULT 0.0,
            status_logistico TEXT DEFAULT 'Pendente'
        )
    ''')

    # Tabela de Itens do Pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Pagamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            valor_pago REAL NOT NULL,
            data_pagamento TEXT NOT NULL,
            forma_pagamento TEXT NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Banco de Dados SQL inicializado e pronto.")

# =================================================================
#               LÓGICA DE NEGÓCIO (TRANSAÇÕES)
# =================================================================

def salvar_pedido_completo(nome_cliente, lista_itens, pagamento_inicial, forma_pagamento):
    """Salva pedido, itens e pagamento numa única transação segura."""
    conn = conectar()
    cursor = conn.cursor()
    data_agora = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    try:
        # 1. Inserir Pedido
        cursor.execute('''
            INSERT INTO pedidos (data_pedido, nome_cliente, status_logistico)
            VALUES (?, ?, ?)
        ''', (data_agora, nome_cliente, 'Pendente'))
        
        pedido_id = cursor.lastrowid # Recupera o ID gerado automaticamente

        # 2. Inserir Itens e calcular total
        valor_total_pedido = 0.0
        for item in lista_itens:
            subtotal = item['qtd'] * item['valor_un']
            valor_total_pedido += subtotal
            cursor.execute('''
                INSERT INTO itens_pedido (pedido_id, produto, quantidade, valor_unitario, valor_subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (pedido_id, item['produto'], item['qtd'], item['valor_un'], subtotal))

        # 3. Atualizar valor total do pedido
        cursor.execute('UPDATE pedidos SET valor_total = ? WHERE id = ?', (valor_total_pedido, pedido_id))

        # 4. Inserir pagamento inicial
        if pagamento_inicial > 0:
            cursor.execute('''
                INSERT INTO pagamentos (pedido_id, valor_pago, data_pagamento, forma_pagamento)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, pagamento_inicial, data_agora, forma_pagamento))

        conn.commit()
        print(f"\n✅ Pedido #{pedido_id} gravado com sucesso!")

    except Exception as e:
        conn.rollback() # Reverte TUDO se houver erro (Conceito de Cloud: Resiliência)
        print(f"❌ Erro ao salvar pedido: {e}")
    finally:
        conn.close()

# =================================================================
#               INTERFACE TEMPORÁRIA (MENU)
# =================================================================

def menu():
    inicializar_bd()
    while True:
        print("\n=== GESTÃO DE NEGÓCIO (SQL) ===")
        print("1. Novo Pedido")
        print("2. Sair")
        opcao = input("Escolha: ")

        if opcao == '1':
            nome = input("Cliente: ")
            # Simulação de um item para teste rápido
            prod = input("Produto: ")
            q = int(input("Qtd: "))
            v = float(input("Preço Un: "))
            pag = float(input("Valor Pago Agora: "))
            forma = input("Forma (Pix/Dinheiro): ")
            
            itens = [{'produto': prod, 'qtd': q, 'valor_un': v}]
            salvar_pedido_completo(nome, itens, pag, forma)
        
        elif opcao == '2':
            break

if __name__ == "__main__":
    menu()