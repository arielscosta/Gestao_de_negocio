from database import conectar, registrar_log
from datetime import datetime
import estoque

def lancar_pedido(user_id, cliente_id):
    """Gerencia um carrinho de compras antes de salvar definitivamente no banco."""
    carrinho = []  # Lista temporária para armazenar os itens do pedido atual
    
    while True:
        print("\n" + "="*60)
        print(f"🛒 CARRINHO DE COMPRAS - CLIENTE ID: {cliente_id}")
        print("="*60)
        
        if not carrinho:
            print("Seu carrinho está vazio.")
        else:
            total_pedido = 0
            print(f"{'ITEM':<4} | {'PRODUTO':<20} | {'QTD':<6} | {'SUBTOTAL'}")
            for i, item in enumerate(carrinho):
                subtotal = item['qtd'] * item['preco_unitario']
                total_pedido += subtotal
                print(f"{i:<4} | {item['nome']:<20} | {item['qtd']:<6} | R$ {subtotal:.2f}")
            print("-" * 60)
            print(f"TOTAL DO PEDIDO: R$ {total_pedido:.2f}")

        print("\nOPÇÕES:")
        print("1- Adicionar Produto")
        print("2- Remover/Editar Item do Carrinho")
        print("3- Finalizar e Salvar Pedido")
        print("4- Cancelar Tudo e Sair")
        
        op = input("\nEscolha: ")

        if op == '1':
            estoque.listar_tudo()
            p_id = input("\nID do Produto para adicionar: ")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (p_id,))
            produto = cursor.fetchone()
            conn.close()

            if produto:
                qtd = int(input(f"Quantidade de {produto['nome']}: "))
                if qtd <= produto['estoque_qtd']:
                    carrinho.append({
                        'id': produto['id'],
                        'nome': produto['nome'],
                        'qtd': qtd,
                        'preco_unitario': produto['preco_unitario']
                    })
                else:
                    print("❌ Estoque insuficiente!")
            else:
                print("❌ Produto não encontrado.")

        elif op == '2' and carrinho:
            idx = int(input("Digite o número do ITEM (coluna ITEM) para remover: "))
            if 0 <= idx < len(carrinho):
                removido = carrinho.pop(idx)
                print(f"✅ {removido['nome']} removido.")
            else:
                print("❌ Índice inválido.")

        elif op == '3' and carrinho:
            confirmar = input("Confirma o fechamento do pedido? (S/N): ").upper()
            if confirmar == 'S':
                salvar_pedido_completo(user_id, cliente_id, carrinho)
                break

        elif op == '4':
            print("🚫 Pedido cancelado.")
            break

def salvar_pedido_completo(user_id, cliente_id, carrinho):
    """Grava o pedido e todos os itens no banco e atualiza o estoque."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        total_geral = sum(item['qtd'] * item['preco_unitario'] for item in carrinho)
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # 1. Salva o cabeçalho do pedido
        cursor.execute('''INSERT INTO pedidos (cliente_id, usuario_id, data_pedido, valor_total)
                          VALUES (?, ?, ?, ?)''', (cliente_id, user_id, data_atual, total_geral))
        
        # 2. Atualiza o estoque para cada item
        for item in carrinho:
            cursor.execute("UPDATE produtos SET estoque_qtd = estoque_qtd - ? WHERE id = ?", 
                           (item['qtd'], item['id']))
        
        conn.commit()
        registrar_log(user_id, f"Pedido FINALIZADO para Cliente {cliente_id}. Total: R$ {total_geral:.2f}")
        print(f"\n✅ PEDIDO {cursor.lastrowid} SALVO COM SUCESSO!")
    except Exception as e:
        print(f"❌ Erro ao salvar pedido: {e}")
    finally:
        conn.close()