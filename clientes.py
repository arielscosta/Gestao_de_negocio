from database import conectar, registrar_log
import pedidos

def novo_cliente(user_id):
    """Cadastra um novo cliente e já oferece a abertura de um pedido."""
    print("\n--- CADASTRO DE NOVO CLIENTE ---")
    nome = input("Nome: ")
    tel = input("Telefone: ")
    end = input("Endereço: ")
    emp = input("Empresa: ")
    
    conn = conectar() # Agora ele vai encontrar a função!
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (nome, telefone, endereco, empresa) VALUES (?, ?, ?, ?)",
                       (nome, tel, end, emp))
        conn.commit()
        
        # Pega o ID do cliente que acabamos de criar
        cliente_id = cursor.lastrowid 
        
        registrar_log(user_id, f"Cadastrou cliente: {nome}")
        print("✅ Cliente registrado com sucesso!")
        
        # Direciona para o fluxo de pedido
        pergunta_pedido(user_id, cliente_id)
        
    except Exception as e:
        print(f"❌ Erro ao cadastrar cliente: {e}")
    finally:
        conn.close()

def consultar_cliente_id(user_id):
    """Consulta um cliente e oferece a abertura de pedido."""
    c_id = input("\nID do cliente para consulta: ")
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (c_id,))
        c = cursor.fetchone() # Aqui definimos a variável 'c'
        
        if c:
            print(f"\n[ID {c['id']}] {c['nome']}")
            print(f"Empresa: {c['empresa']} | Tel: {c['telefone']}")
            print(f"Endereço: {c['endereco']}")
            
            # Direciona para o fluxo de pedido usando os dados de 'c'
            pergunta_pedido(user_id, c['id'])
        else:
            print("❌ Cliente não localizado.")
    finally:
        conn.close()

def listar_clientes():
    """Lista todos os clientes antes da consulta."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes")
        lista = cursor.fetchall()
        if not lista:
            print("\n📭 Nenhum cliente cadastrado.")
            return False
        
        print(f"\n{'ID':<4} | {'NOME':<20} | {'EMPRESA'}")
        for cli in lista:
            print(f"{cli['id']:<4} | {cli['nome']:<20} | {cli['empresa']}")
        return True
    finally:
        conn.close()

def pergunta_pedido(user_id, cliente_id):
    """Função auxiliar para o direcionamento solicitado."""
    op = input("\n📝 Deseja lançar um pedido para este cliente? (S/N): ").upper()
    if op == 'S':
        pedidos.lancar_pedido(user_id, cliente_id)