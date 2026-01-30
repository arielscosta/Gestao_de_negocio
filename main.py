import os
from database import inicializar_bd, conectar
import estoque
import vendas

def exibir_menu_vendas():
    while True:
        print("\n--- PDV: LANÇAR VENDA ---")
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco_unitario, preco_caixa, estoque_qtd FROM produtos")
        prods = cursor.fetchall()
        conn.close()

        if not prods:
            print("⚠️ Estoque vazio. Peça ao administrador para cadastrar produtos.")
            break

        for p in prods:
            print(f"[{p['id']}] {p['nome']} | Un: R${p['preco_unitario']} | Cx: R${p['preco_caixa']} | Estoque: {p['estoque_qtd']}")

        escolha = input("\nID do produto (ou 'S' para sair): ")
        if escolha.upper() == 'S': break

        try:
            p_id = int(escolha)
            cliente = input("Nome do Cliente: ")
            tipo = input("Tipo (U para Unitário / C para Caixa): ").upper()
            qtd = int(input("Quantidade: "))
            
            # Busca preço correto
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (p_id,))
            prod = cursor.fetchone()
            conn.close()

            if prod and qtd <= prod['estoque_qtd']:
                preco = prod['preco_unitario'] if tipo == 'U' else prod['preco_caixa']
                pag = float(input("Pagamento Inicial: "))
                forma = input("Forma: ") if pag > 0 else ""
                
                itens = [{'produto': prod['nome'], 'qtd': qtd, 'valor_un': preco}]
                vendas.salvar_pedido_completo(cliente, itens, pag, forma)
            else:
                print("❌ Produto não encontrado ou estoque insuficiente!")
        except ValueError:
            print("❌ Entrada inválida.")

def main():
    inicializar_bd()
    while True:
        # os.system('cls' if os.name == 'nt' else 'clear')
        print("\n===== GESTÃO DE NEGÓCIO 2.0 (MODULAR) =====")
        print("1. Área de Vendas (Operacional)")
        print("2. Visualizar Pedidos")
        print("3. Gestão de Estoque (Administrativo)")
        print("4. Sair")
        
        op = input("\nSelecione: ")

        if op == '1':
            exibir_menu_vendas()
        elif op == '2':
            vendas.listar_vendas()
            input("\nEnter para voltar...")
        elif op == '3':
            # Chama a função do outro arquivo
            estoque.adicionar_produto_estoque()
        elif op == '4':
            break

if __name__ == "__main__":
    main()