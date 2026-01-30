import database, estoque, clientes, os  # Certifique-se de que 'os' está aqui

def limpar_tela():
    # 'nt' é Windows, 'posix' é Linux/Docker/WSL2
    os.system('cls' if os.name == 'nt' else 'clear') # Função para limpar a tela do terminal

USUARIO_ATUAL = None

def login():
    """Sistema de autenticação por camadas."""
    limpar_tela()
    global USUARIO_ATUAL
    print("\n" + "="*40)
    print("      ACESSO RESTRITO - GESTÃO ERP")
    print("="*40)
    user = input("Usuário: ")
    senha = input("Senha: ")
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (user, senha))
    u = cursor.fetchone()
    conn.close() # Conexão fechada aqui - CORRETO
    
    if u:
        USUARIO_ATUAL = u
        try:
            # Tentativa de log, se o banco estiver ocupado ele ignora e entra no sistema
            database.registrar_log(u['id'], "Login realizado")
        except:
            pass 
        return True
    return False

def menu_principal():
    """Navegação baseada na hierarquia solicitada."""
    while True:
        limpar_tela() # Limpa a tela a cada iteração do menu
        print(f"\n--- MENU PRINCIPAL | OPERADOR: {USUARIO_ATUAL['username'].upper()} ---") # Título do menu com o nome do usuário
        print("1- Novo Cliente")
        print("2- Lista de Clientes")
        print("3- Consultar Estoque")
        print("4- Editar Estoque")
        print("5- Sair")
        
        op = input("\nSelecione: ")

        if op == '1': # Menu Cliente
            clientes.novo_cliente(USUARIO_ATUAL['id'])
        
        elif op == '2': # Submenu Lista Clientes
            # Primeiro, mostra todo mundo
            if clientes.listar_clientes():
                print("\n1- Consultar detalhes de um ID")
                print("2- Voltar")
                if input("Escolha: ") == '1': 
                    clientes.consultar_cliente_id(USUARIO_ATUAL['id'])
            else:
                input("\nPresione Enter para voltar...")
            
        elif op == '3': # Consulta Estoque
            estoque.listar_tudo()
            input("\nEnter para voltar...")
            
        elif op == '4': # Submenu Estoque
            print("\n1- Novo/Editar Produto\n2- Registrar Saída de Produto\n3- Voltar")
            sub = input("Escolha: ")
            if sub == '1': estoque.gerenciar_produto(USUARIO_ATUAL['id'])
            elif sub == '2': estoque.registrar_saida(USUARIO_ATUAL['id'])
            
        elif op == '5':
            database.registrar_log(USUARIO_ATUAL['id'], "Logout do sistema")
            break

if __name__ == "__main__":
    database.inicializar_bd()
    if login():
        menu_principal()
    else:
        print("❌ Acesso negado. Credenciais inválidas.")