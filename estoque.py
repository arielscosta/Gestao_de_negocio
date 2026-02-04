from database import conectar, registrar_log

def gerenciar_produto(user_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        identificador = input("\nID do produto (Vazio para NOVO): ")
        
        nome = input("Nome do Produto: ").upper()
        unid_por_cx = int(input("Unidades por caixa: "))
        v_compra = float(input("Valor de Compra: R$ "))
        v_venda = float(input("Valor de Venda: R$ "))
        qtd_total = int(input("Quantidade Total em Estoque (Unidades): "))

        if identificador:
            cursor.execute('''UPDATE produtos SET nome=?, unidades_por_caixa=?, valor_compra=?, 
                              valor_venda=?, estoque_unidades_total=? WHERE id=?''', 
                           (nome, unid_por_cx, v_compra, v_venda, qtd_total, identificador))
            acao = f"Editou produto {nome}"
        else:
            cursor.execute('''INSERT INTO produtos (nome, unidades_por_caixa, valor_compra, valor_venda, estoque_unidades_total)
                              VALUES (?, ?, ?, ?, ?)''', (nome, unid_por_cx, v_compra, v_venda, qtd_total))
            acao = f"Cadastrou produto {nome}"

        conn.commit()
        registrar_log(user_id, acao)
        print("✅ Operação realizada com sucesso!")
    finally:
        conn.close()

def registrar_saida(user_id):
    """Registra baixas manuais garantindo o fechamento da conexão."""
    p_id = input("\nID do produto para saída: ")
    motivo = input("Direcionamento (Motivo): ")
    
    conn = conectar()
    try:
        qtd = int(input("Quantidade a retirar: "))
        cursor = conn.cursor()
        cursor.execute("UPDATE produtos SET estoque_unidades_total = estoque_unidades_total - ? WHERE id = ?", (qtd, p_id))
        conn.commit()
        
        registrar_log(user_id, f"SAÍDA: {qtd} un do ID {p_id}. Motivo: {motivo}")
        print("✅ Baixa registrada.")
    except Exception as e:
        print(f"❌ Erro ao registrar saída: {e}")
    finally:
        conn.close()

def listar_tudo():
    """Consulta rápida com fechamento seguro."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos")
        prods = cursor.fetchall()
        print(f"\n{'ID':<4} | {'PRODUTO':<20} | {'ESTOQUE':<8} | {'PREÇO UN':<10} | {'PREÇO CX'}")
        for p in prods:
            print(f"{p['id']:<4} | {p['nome']:<20} | {p['estoque_unidades_total']:<8} | R${p['preco_unitario']:<8.2f} | R${p['preco_caixa']:.2f}")
    finally:
        conn.close()