from database import conectar, registrar_log

def gerenciar_produto(user_id):
    """Cadastra ou edita produtos com proteção contra travamento de banco."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        
        identificador = input("\nID do produto (Deixe em branco para NOVO): ")
        
        if identificador:
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (identificador,))
            prod_existente = cursor.fetchone()
            if not prod_existente:
                print("❌ ID não encontrado. Iniciando novo cadastro...")
                identificador = None

        nome = input("Nome do Produto: ").upper()
        qtd_un_cx = int(input("Qtd de unidades na caixa: "))
        v_unidade = float(input("Valor unitário: R$ "))
        
        v_caixa = v_unidade * qtd_un_cx
        qtd_estq = int(input("Quantidade total em estoque (unidades): "))

        if identificador:
            cursor.execute('''UPDATE produtos SET nome=?, estoque_qtd=?, preco_unitario=?, 
                              qtd_por_caixa=?, preco_caixa=? WHERE id=?''', 
                           (nome, qtd_estq, v_unidade, qtd_un_cx, v_caixa, identificador))
            acao_log = f"Editou produto ID {identificador}: {nome}"
        else:
            cursor.execute('''INSERT INTO produtos (nome, estoque_qtd, preco_unitario, qtd_por_caixa, preco_caixa)
                              VALUES (?, ?, ?, ?, ?)''', (nome, qtd_estq, v_unidade, qtd_un_cx, v_caixa))
            acao_log = f"Cadastrou novo produto: {nome}"

        conn.commit()
        # Registramos o log ainda dentro do bloco try
        registrar_log(user_id, acao_log)
        print(f"✅ Sucesso! Valor da caixa: R$ {v_caixa:.2f}")

    except ValueError:
        print("❌ Erro: Digite apenas números para quantidades e valores.")
    except Exception as e:
        print(f"❌ Erro operacional: {e}")
    finally:
        # ISSO É O MAIS IMPORTANTE: Fecha a conexão mesmo se der erro acima
        conn.close()

def registrar_saida(user_id):
    """Registra baixas manuais garantindo o fechamento da conexão."""
    p_id = input("\nID do produto para saída: ")
    motivo = input("Direcionamento (Motivo): ")
    
    conn = conectar()
    try:
        qtd = int(input("Quantidade a retirar: "))
        cursor = conn.cursor()
        cursor.execute("UPDATE produtos SET estoque_qtd = estoque_qtd - ? WHERE id = ?", (qtd, p_id))
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
            print(f"{p['id']:<4} | {p['nome']:<20} | {p['estoque_qtd']:<8} | R${p['preco_unitario']:<8.2f} | R${p['preco_caixa']:.2f}")
    finally:
        conn.close()