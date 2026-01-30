# test_db.py
import database # Importa o seu módulo de banco de dados para testá-lo

def test_conexao_inicial():
    """Teste de fumaça para garantir que a estrutura do DB está íntegra."""
    print("🚀 Iniciando teste de integridade do banco de dados...")
    
    try:
        # 1. Tenta inicializar o banco (cria as tabelas se não existirem)
        database.inicializar_bd()
        
        # 2. Tenta conectar para verificar se o arquivo .db foi criado
        conn = database.conectar()
        cursor = conn.cursor()
        
        # 3. Consulta as tabelas que existem no banco SQLite
        # sqlite_master é uma tabela padrão do SQLite que guarda o esquema do banco
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        conn.close()
        
        # 4. Extrai apenas os nomes das tabelas para uma lista
        nomes_tabelas = [t['name'] for t in tabelas]
        
        # 5. Verifica se as tabelas fundamentais estão lá (usando 'assert')
        # Se 'usuarios' não estiver na lista, o Python gera um erro e para o teste
        assert 'usuarios' in nomes_tabelas
        assert 'produtos' in nomes_tabelas
        assert 'logs_sistema' in nomes_tabelas
        
        print("✅ Sucesso: O banco de dados foi criado com a estrutura correta!")
        return True

    except Exception as e:
        # Se qualquer coisa acima der errado, o erro é capturado aqui
        print(f"❌ FALHA NO TESTE: {e}")
        # exit(1) avisa o GitHub que o teste falhou (qualquer número diferente de 0 é erro)
        exit(1) 

if __name__ == "__main__":
    test_conexao_inicial()