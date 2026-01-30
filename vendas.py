from database import conectar
from datetime import datetime

def salvar_pedido_completo(nome_cliente, lista_itens, pagamento_inicial, forma_pagamento):
    """Lógica transacional de venda com baixa automática no estoque."""
    conn = conectar()
    cursor = conn.cursor()
    data_agora = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    try:
        # 1. Inserir Cabeçalho do Pedido
        cursor.execute('''
            INSERT INTO pedidos (data_pedido, nome_cliente, status_logistico)
            VALUES (?, ?, ?)
        ''', (data_agora, nome_cliente, 'Pendente'))
        
        pedido_id = cursor.lastrowid
        total_geral = 0.0

        # 2. Processar Itens e Baixar Estoque
        for item in lista_itens:
            subtotal = item['qtd'] * item['valor_un']
            total_geral += subtotal
            
            # Registra o item no pedido
            cursor.execute('''
                INSERT INTO itens_pedido (pedido_id, produto, quantidade, valor_unitario, valor_subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (pedido_id, item['produto'], item['qtd'], item['valor_un'], subtotal))

            # BAIXA NO ESTOQUE (Crucial para Cloud/Consistency)
            cursor.execute('''
                UPDATE produtos SET estoque_qtd = estoque_qtd - ? 
                WHERE nome = ?
            ''', (item['qtd'], item['produto']))

        # 3. Atualiza o total do pedido
        cursor.execute('UPDATE pedidos SET valor_total = ? WHERE id = ?', (total_geral, pedido_id))

        # 4. Registrar pagamento
        if pagamento_inicial > 0:
            cursor.execute('''
                INSERT INTO pagamentos (pedido_id, valor_pago, data_pagamento, forma_pagamento)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, pagamento_inicial, data_agora, forma_pagamento))

        conn.commit()
        print(f"\n✅ Venda #{pedido_id} realizada com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro na transação de venda: {e}")
    finally:
        conn.close()

def listar_vendas():
    """Visualização rápida dos pedidos realizados."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    conn.close()
    
    if not pedidos:
        print("\n📭 Nenhuma venda registrada.")
        return

    print(f"\n{'ID':<4} | {'CLIENTE':<20} | {'TOTAL':<10} | {'STATUS'}")
    print("-" * 50)
    for p in pedidos:
        print(f"{p['id']:<4} | {p['nome_cliente']:<20} | R${p['valor_total']:<8.2f} | {p['status_logistico']}")