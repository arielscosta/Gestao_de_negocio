import os
import sys
import sqlite3

def run_test():
    print("🚀 Iniciando Teste de Integridade...")
    
    # 1. Tenta importar os módulos (Garante que arquivos existem)
    try:
        import database
        import estoque
        import clientes
        print("✅ Módulos carregados.")
    except ImportError as e:
        print(f"❌ Erro: Arquivo faltando ou erro de import: {e}")
        sys.exit(1)

    # 2. Resetar banco para o teste
    if os.path.exists('erp.db'):
        os.remove('erp.db')

    # 3. Inicializar banco e testar tabelas
    try:
        database.inicializar_bd()
        conn = database.conectar()
        cursor = conn.cursor()
        
        # Testar se a coluna correta existe
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if 'estoque_unidades_total' in colunas:
            print("✅ Estrutura da tabela 'produtos' está correta.")
        else:
            print("❌ Erro: Coluna 'estoque_unidades_total' não encontrada!")
            sys.exit(1)
            
        conn.close()
    except Exception as e:
        print(f"❌ Erro no Banco de Dados: {e}")
        sys.exit(1)

    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    sys.exit(0)

if __name__ == "__main__":
    run_test()