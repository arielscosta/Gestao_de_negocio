from database import conectar

def adicionar_produto_estoque():
    nome = input("Nome do Produto: ").upper()
    qtd = int(input("Quantidade inicial: "))
    p_un = float(input("Preço Unitário: "))
    p_cx = float(input("Preço Caixa (Atacado): "))
    
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO produtos (nome, estoque_qtd, preco_unitario, preco_caixa)
            VALUES (?, ?, ?, ?)
        ''', (nome, qtd, p_un, p_cx))
        
        # O PONTO CRÍTICO É ESTA LINHA ABAIXO:
        conn.commit() 
        
        print(f"✅ {nome} adicionado ao estoque!")
    except Exception as e:
        print(f"❌ Erro ao cadastrar: {e}")
    finally:
        conn.close()