# =================================================================
#               CAMADA DE DADOS (SQLITE / DATABASE)
# =================================================================

import sqlite3
import os
from datetime import datetime

DB_NAME = "gestao_de_negocio.db"

def conectar():
    """Conecta ao banco e ativa o suporte a chaves estrangeiras."""
    conn = sqlite3.connect(DB_NAME)
    # Garante que as regras de relacionamento (CASCADE) funcionem
    conn.execute("PRAGMA foreign_keys = ON")
    # Permite acessar colunas pelo nome (ex: linha['nome_cliente'])
    conn.row_factory = sqlite3.Row 
    return conn

def inicializar_bd():
    """Cria as tabelas com integridade referencial."""
    conn = conectar()
    cursor = conn.cursor()

    # 1. Tabela de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_pedido TEXT NOT NULL,
            nome_cliente TEXT NOT NULL,
            valor_total REAL DEFAULT 0.0,
            status_logistico TEXT DEFAULT 'Pendente'
        )
    ''')

    # 2. Tabela de Itens (Ligada ao Pedido)
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

    # 3. Tabela de Pagamentos (Onde salvaremos o histórico de cada centavo)
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
    print("✅ Banco de Dados 'Gestao_de_negocio' configurado com sucesso.")

# Executa a inicialização ao rodar o script
if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        inicializar_bd()
    else:
        print("ℹ️ Banco de dados já existe. Pronto para operar.")


# =================================================================
#               Visualização de Dados (pedidos)
# =================================================================

def visualizar_todos_pedidos():
    """Consulta o banco e exibe todos os pedidos cadastrados."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Buscamos os pedidos (do mais novo para o mais antigo)
    cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    
    if not pedidos:
        print("\n📭 Nenhum pedido encontrado no sistema.")
    else:
        print("\n" + "="*70)
        print(f"{'ID':<4} | {'CLIENTE':<20} | {'DATA':<18} | {'TOTAL (R$)':<10} | {'STATUS'}")
        print("-" * 70)
        
        for p in pedidos:
            # Como usamos sqlite3.Row, acessamos pelo nome da coluna:
            print(f"{p['id']:<4} | {p['nome_cliente']:<20} | {p['data_pedido']:<18} | {p['valor_total']:<10.2f} | {p['status_logistico']}")
        print("="*70)
    
    conn.close()
    input("\nPressione Enter para voltar ao menu...")

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

def menu_principal():
    inicializar_bd() # Garante que o banco e tabelas existam
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Limpa a tela para ficar organizado
        print("\n=== GESTÃO DE NEGÓCIO (SQL) ===")
        print("1. Lançar Novo Pedido")
        print("2. Visualizar Todos os Pedidos")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ")

        if opcao == '1':
            print("\n--- LANÇAR NOVO PEDIDO ---")
            nome = input("Nome do Cliente: ")
            
            # Coleta de Itens (podemos futuramente fazer um loop para vários itens)
            produto = input("Produto: ")
            try:
                qtd = int(input("Quantidade: "))
                valor_un = float(input("Valor Unitário: "))
                
                # Coleta do Pagamento Inicial
                pag_inicial = float(input("Valor do Pagamento Inicial (0 se não houver): "))
                forma = ""
                if pag_inicial > 0:
                    forma = input("Forma de Pagamento (Pix/Dinheiro/Cartão): ")

                # Prepara a lista de itens para a função
                itens = [{'produto': produto, 'qtd': qtd, 'valor_un': valor_un}]

                # Chama a transação SQL que você já escreveu
                salvar_pedido_completo(nome, itens, pag_inicial, forma)
                
            except ValueError:
                print("❌ Erro: Quantidade e Valor devem ser números!")
            
            input("\nPressione Enter para voltar ao menu...")

if __name__ == "__main__":
    menu_principal()