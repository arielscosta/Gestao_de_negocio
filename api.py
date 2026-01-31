from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import database

# Inicializa o banco (Cria tabelas se não existirem)
database.inicializar_bd()

app = FastAPI()

# --- ESTILO ---
def get_style():
    return """
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f4f7f6; }
        nav { background: #2c3e50; padding: 15px; color: white; display: flex; gap: 20px; align-items: center; }
        nav a { color: white; text-decoration: none; font-weight: bold; }
        .container { padding: 30px; max-width: 1100px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #34495e; color: white; }
        input, select, textarea { padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; width: 100%; box-sizing: border-box; }
        .btn { padding: 10px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; color: white; width: 100%; display: block; text-align: center; text-decoration: none; box-sizing: border-box; }
        .btn-green { background: #27ae60; }
        .btn-red { background: #e74c3c; }
        .btn-blue { background: #3498db; }
        .btn-purple { background: #8e44ad; }
        .flex-row { display: flex; gap: 10px; align-items: flex-end; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; background: #34495e; color: white; }
    </style>
    """

# --- AUXILIAR: PEGAR CARGO ---
def get_user_cargo(request: Request):
    usuario_nome = request.cookies.get("usuario_login")
    if not usuario_nome: return None
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cargo FROM usuarios WHERE username = ?", (usuario_nome,))
    u = cursor.fetchone()
    conn.close()
    return u['cargo'] if u else None

# --- ACESSO ---
@app.get("/", response_class=HTMLResponse)
def home_login(request: Request):
    if request.cookies.get("usuario_login"): return RedirectResponse("/dashboard")
    return f"<html><head>{get_style()}</head><body style='display:flex;justify-content:center;align-items:center;height:100vh;background:#1a2a3a;'><div class='card' style='width:320px;text-align:center;'><h2>🚀 ERP Login</h2><form action='/login' method='post'><input type='text' name='u' placeholder='Usuário'><input type='password' name='s' placeholder='Senha'><button class='btn btn-blue' style='margin-top:10px;'>Entrar</button></form></div></body></html>"

# --- LOGIN ---
@app.post("/login")
def login(u: str = Form(...), s: str = Form(...)):
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u, s))
    user = cursor.fetchone()
    conn.close()
    if user:
        res = RedirectResponse("/dashboard", status_code=303)
        res.set_cookie("usuario_login", u)
        return res
    return RedirectResponse("/", status_code=303)

# --- LOGOUT ---
@app.get("/logout")
def logout():
    res = RedirectResponse("/", status_code=303)
    res.delete_cookie("usuario_login")
    return res

# --- DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    cargo = get_user_cargo(request)
    if not cargo: return RedirectResponse("/")
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes"); c_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM produtos WHERE status='ativo'"); p_count = cursor.fetchone()[0]
    conn.close()

    return f"""
    <html><head>{get_style()}</head><body>
    <nav>
        <b>ERP PRO</b>
        <a href='/dashboard'>🏠 Home</a>
        {f"<a href='/clientes_web'>👥 Clientes</a>" if cargo != 'Comum' else ""}
        {f"<a href='/estoque_web'>📦 Estoque</a>" if cargo != 'Comum' else ""}
        <a href='/logout' style='margin-left:auto;'>🚪 Sair</a>
    </nav>
    <div class='container'>
        <h2>Olá, {request.cookies.get('usuario_login')} <span class='badge'>{cargo}</span></h2>
        <div style='display:flex; gap:20px;'>
            <div class='card' style='flex:1;text-align:center;'><h1>{c_count}</h1><p>Clientes</p></div>
            <div class='card' style='flex:1;text-align:center;'><h1>{p_count}</h1><p>Produtos</p></div>
        </div>
        <div class='card'>
            <h3>Atalhos Rápidos</h3>
            <div style='display:flex; gap:10px;'>
                {f"<a href='/clientes_web' class='btn btn-green'>Clientes</a>" if cargo != 'Comum' else ""}
                {f"<a href='/estoque_web' class='btn btn-blue'>Estoque</a>" if cargo != 'Comum' else ""}
                {f"<a href='/usuarios_web' class='btn btn-purple'>Usuários</a>" if cargo == 'Admin' else ""}
            </div>
        </div>
    </div></body></html>
    """

# --- CLIENTES ---
@app.get("/clientes_web", response_class=HTMLResponse)
def clientes_web(request: Request):
    cargo = get_user_cargo(request)
    if cargo not in ["Admin", "Gerência", "Operacional"]: return RedirectResponse("/dashboard")
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()

    linhas = "".join([f"<tr><td>{c['id']}</td><td>{c['nome']}</td><td>{c['empresa']}</td><td><a href='/clientes/detalhe/{c['id']}'>🔍 Ver</a></td></tr>" for c in clientes])
    
    form_novo = ""
    if cargo in ["Admin", "Gerência"]:
        form_novo = """
        <div class='card'>
            <h3>➕ Novo Cliente</h3>
            <form action='/clientes/novo' method='post' style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                <input name='nome' placeholder='Nome' required>
                <input name='endereco' placeholder='Endereço'>
                <input name='telefone' placeholder='Telefone'>
                <input type='date' name='data_nasc'>
                <input name='email' placeholder='Email'>
                <input name='empresa' placeholder='Empresa'>
                <button type='submit' class='btn btn-green' style='grid-column: span 2;'>Salvar</button>
            </form>
        </div>
        """

    return f"<html><head>{get_style()}</head><body><nav><a href='/dashboard'>⬅️ Voltar</a></nav><div class='container'>{form_novo}<div class='card'><h3>Lista de Clientes</h3><table><tr><th>ID</th><th>Nome</th><th>Empresa</th><th>Ação</th></tr>{linhas}</table></div></div></body></html>"

# --- DELETAR CLIENTE ---
@app.get("/clientes/deletar/{id}")
def deletar_cliente(id: int, request: Request):
    cargo = get_user_cargo(request)
    if cargo not in ["Admin", "Gerência"]:
        return RedirectResponse("/dashboard")

    conn = database.conectar()
    cursor = conn.cursor()
    
    # Última verificação de segurança: checar se há débitos antes de deletar
    cursor.execute("SELECT SUM(valor_total) FROM pedidos WHERE cliente_id=? AND status='Pendente'", (id,))
    debito = cursor.fetchone()[0] or 0
    
    if debito <= 0:
        # Deleta histórico de pagamentos e pedidos antes do cliente (integridade referencial)
        cursor.execute("DELETE FROM pagamentos WHERE cliente_id=?", (id,))
        cursor.execute("DELETE FROM pedidos WHERE cliente_id=?", (id,))
        cursor.execute("DELETE FROM clientes WHERE id=?", (id,))
        conn.commit()
    
    conn.close()
    return RedirectResponse("/clientes_web", status_code=303)

# --- FORMULÁRIOS E AÇÕES DE CLIENTES ---
@app.post("/clientes/novo")
def novo_cliente(nome: str=Form(...), endereco: str=Form(None), telefone: str=Form(None), data_nasc: str=Form(None), email: str=Form(None), empresa: str=Form(None)):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nome, endereco, telefone, data_nasc, email, empresa) VALUES (?,?,?,?,?,?)", (nome, endereco, telefone, data_nasc, email, empresa))
    conn.commit(); conn.close()
    return RedirectResponse("/clientes_web", status_code=303)

@app.get("/clientes/detalhe/{id}", response_class=HTMLResponse)
def detalhe_cliente(id: int):
    conn = database.conectar()
    cursor = conn.cursor()
    
    # Busca dados do cliente
    cursor.execute("SELECT * FROM clientes WHERE id=?", (id,))
    c = cursor.fetchone()
    
    # Busca pedidos para verificar débitos
    cursor.execute("SELECT * FROM pedidos WHERE cliente_id=?", (id,))
    peds = cursor.fetchall()
    
    # Busca pagamentos
    cursor.execute("SELECT * FROM pagamentos WHERE cliente_id=?", (id,))
    pags = cursor.fetchall()
    conn.close()
    
    if not c: return RedirectResponse("/clientes_web")

    # Lógica de Débito: Soma pedidos pendentes
    valor_pendente = sum([p['valor_total'] for p in peds if p['status'] == 'Pendente'])
    
    # Botão Excluir: Só aparece se valor_pendente for 0
    btn_excluir = ""
    if valor_pendente <= 0:
        btn_excluir = f"<a href='/clientes/deletar/{id}' class='btn btn-red' onclick='return confirm(\"Tem certeza?\")' style='margin-top:10px;'>🗑️ Excluir Cliente</a>"
    else:
        btn_excluir = f"<p style='color:#e74c3c; font-size:12px; margin-top:10px;'>⚠️ Exclusão bloqueada: Cliente possui R$ {valor_pendente:.2f} em débitos.</p>"

    return f"""
    <html><head>{get_style()}</head><body>
    <nav><a href='/clientes_web'>⬅️ Voltar para Lista</a></nav>
    <div class='container'>
        <div style='display:flex; gap:20px;'>
            <div style='flex:1;'>
                <div class='card'>
                    <h2>👤 {c['nome']}</h2>
                    <hr>
                    <p><b>📧 Email:</b> {c['email'] or 'Não informado'}</p>
                    <p><b>📞 Telefone:</b> {c['telefone'] or 'Não informado'}</p>
                    <p><b>🏠 Endereço:</b> {c['endereco'] or 'Não informado'}</p>
                    <p><b>🎂 Nascimento:</b> {c['data_nasc'] or 'Não informado'}</p>
                    <p><b>🏢 Empresa:</b> {c['empresa'] or 'Não informado'}</p>
                    <hr>
                    <div style='display:flex; flex-direction:column; gap:5px;'>
                        <a href='/clientes/pedido/{id}' class='btn btn-blue'>🛒 Novo Pedido</a>
                        <a href='/clientes/pagamento/{id}' class='btn btn-green'>💰 Registrar Pagamento</a>
                        <a href='/clientes/editar/{id}' class='btn btn-purple'>📝 Editar Cadastro</a>
                        {btn_excluir}
                    </div>
                </div>
            </div>

            <div style='flex:2;'>
                <div class='card'>
                    <h3>📦 Pedidos e Débitos</h3>
                    <table>
                        <tr><th>Data</th><th>Produtos</th><th>Valor</th><th>Status</th></tr>
                        {"".join([f"<tr><td>{p['data']}</td><td>{p['produtos']}</td><td>R$ {p['valor_total']:.2f}</td><td>{p['status']}</td></tr>" for p in peds]) or "<tr><td colspan='4'>Sem histórico.</td></tr>"}
                    </table>
                </div>
            </div>
        </div>
    </div></body></html>
    """

# --- PEDIDOS E PAGAMENTOS ---
@app.get("/clientes/pedido/{id}", response_class=HTMLResponse)
def form_pedido(id: int):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE estoque_unidades_total > 0"); prods = cursor.fetchall()
    conn.close()
    opts = "".join([f"<option value='{p['id']}'>{p['nome']} (R$ {p['valor_unitario']})</option>" for p in prods])
    return f"<html><head>{get_style()}</head><body><div class='container'><div class='card'><h3>Lançar Pedido</h3><form action='/clientes/pedido/{id}' method='post'><select name='pid'>{opts}</select><input type='number' name='q' value='1'><button class='btn btn-blue'>Finalizar</button></form></div></div></body></html>"

@app.post("/clientes/pedido/{id}")
def criar_pedido(id: int, pid: int=Form(...), q: int=Form(...)):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id=?", (pid,)); p = cursor.fetchone()
    total = q * p['valor_unitario']
    cursor.execute("INSERT INTO pedidos (cliente_id, data, produtos, valor_total, status) VALUES (?,?,?,?,'Pendente')", (id, datetime.now().strftime("%d/%m/%Y"), p['nome'], total))
    cursor.execute("UPDATE produtos SET estoque_unidades_total = estoque_unidades_total - ? WHERE id=?", (q, pid))
    conn.commit(); conn.close()
    return RedirectResponse(f"/clientes/detalhe/{id}", status_code=303)

@app.get("/clientes/pagamento/{id}", response_class=HTMLResponse)
def form_pagamento(id: int):
    return f"<html><head>{get_style()}</head><body><div class='container'><div class='card'><h3>Receber Pagamento</h3><form action='/clientes/pagamento/{id}' method='post'><input type='number' step='0.01' name='v' placeholder='Valor'><button class='btn btn-green'>Confirmar</button></form></div></div></body></html>"

@app.post("/clientes/pagamento/{id}")
def pagar(id: int, v: float=Form(...)):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO pagamentos (cliente_id, data, valor) VALUES (?,?,?)", (id, datetime.now().strftime("%d/%m/%Y"), v))
    cursor.execute("UPDATE pedidos SET status='Pago' WHERE cliente_id=? AND status='Pendente'", (id,))
    conn.commit(); conn.close()
    return RedirectResponse(f"/clientes/detalhe/{id}", status_code=303)

# --- LISTAGEM DE ESTOQUE ---
@app.get("/estoque_web", response_class=HTMLResponse)
def estoque_web(request: Request, busca: str = ""):
    cargo = get_user_cargo(request)
    conn = database.conectar(); cursor = conn.cursor()
    
    # Pegamos todos os dados para o JavaScript preencher os campos automaticamente
    cursor.execute("SELECT nome, valor_compra, valor_venda, unidades_por_caixa FROM produtos WHERE status = 'ativo'")
    produtos_data = [dict(p) for p in cursor.fetchall()]
    
    # Filtro da tabela
    if busca:
        cursor.execute("SELECT * FROM produtos WHERE status = 'ativo' AND nome LIKE ?", (f"%{busca}%",))
    else:
        cursor.execute("SELECT * FROM produtos WHERE status = 'ativo'")
    prods = cursor.fetchall()
    conn.close()

    sugestoes = "".join([f"<option value='{p['nome']}'>" for p in produtos_data])
    
    # Tabela... (mesma lógica anterior)
    linhas = ""
    for p in prods:
        total = p['estoque_unidades_total']; uc = p['unidades_por_caixa']
        linhas += f"<tr><td>{p['nome']}</td><td>{total//uc} cx e {total%uc} un</td><td>R$ {p['valor_venda']:.2f}</td><td><a href='/estoque/editar/{p['id']}' class='btn btn-blue' style='padding:5px; font-size:12px;'>📝 Detalhes</a></td></tr>"

    return f"""
    <html><head>
        {get_style()}
        <script>
            const produtosExistentes = {produtos_data};
            
            function preencherDados() {{
                const nomeInput = document.getElementById('nome_prod').value;
                const match = produtosExistentes.find(p => p.nome === nomeInput);
                
                if (match) {{
                    document.getElementById('v_compra').value = match.valor_compra;
                    document.getElementById('v_venda').value = match.valor_venda;
                    document.getElementById('unid_caixa').value = match.unidades_por_caixa;
                }}
            }}
        </script>
    </head>
    <body>
        <nav><a href='/dashboard'>🏠 Home</a></nav>
        <div class='container'>
            <div class='card'>
                <h3>📦 Entrada de Mercadoria</h3>
                <form action='/estoque/novo' method='post' style='display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;'>
                    <div style='grid-column: span 1;'>
                        <input id='nome_prod' name='nome' list='datalist_prod' placeholder='Nome do Produto' oninput='preencherDados()' required>
                        <datalist id='datalist_prod'>{sugestoes}</datalist>
                    </div>
                    <input type='number' step='0.01' id='v_compra' name='v_compra' placeholder='Custo Un' required>
                    <input type='number' step='0.01' id='v_venda' name='v_venda' placeholder='Venda Un' required>
                    <input type='number' id='unid_caixa' name='unid_caixa' placeholder='Qtd na Caixa' required>
                    <input type='number' name='qtd_entrada' placeholder='Quantidade' required>
                    <select name='tipo_entrada'>
                        <option value='unid'>Unidades</option>
                        <option value='caixa'>Caixas</option>
                    </select>
                    <button type='submit' class='btn btn-green' style='grid-column: span 3;'>Confirmar Entrada</button>
                </form>
            </div>
            <div class='card'>
                <table><tr><th>Produto</th><th>Saldo</th><th>Preço Un</th><th>Ações</th></tr>{linhas}</table>
            </div>
        </div>
    </body></html>
    """
# --- PROCESSAR NOVO PRODUTO (ATUALIZAÇÃO SE EXISTIR) ---
@app.post("/estoque/novo")
def novo_produto(nome: str=Form(...), v_compra: float=Form(...), v_venda: float=Form(...), unid_caixa: int=Form(...), qtd_entrada: int=Form(...), tipo_entrada: str=Form(...)):
    total_unid = (qtd_entrada * unid_caixa) if tipo_entrada == 'caixa' else qtd_entrada
    
    conn = database.conectar(); cursor = conn.cursor()
    
    # BUSCA POR NOME E TAMANHO DA CAIXA
    cursor.execute("""
        SELECT id, estoque_unidades_total FROM produtos 
        WHERE nome = ? AND unidades_por_caixa = ? AND status = 'ativo'
    """, (nome, unid_caixa))
    existente = cursor.fetchone()
    
    if existente:
        novo_saldo = existente['estoque_unidades_total'] + total_unid
        cursor.execute("UPDATE produtos SET valor_compra=?, valor_venda=?, estoque_unidades_total=? WHERE id=?",
                       (v_compra, v_venda, novo_saldo, existente['id']))
    else:
        cursor.execute("INSERT INTO produtos (nome, valor_compra, valor_venda, unidades_por_caixa, estoque_unidades_total) VALUES (?,?,?,?,?)",
                       (nome, v_compra, v_venda, unid_caixa, total_unid))
    
    conn.commit(); conn.close()
    return RedirectResponse("/estoque_web", status_code=303)

# --- PROCESSAR NOVO PRODUTO ---
@app.post("/estoque/novo")
def novo_produto(nome: str=Form(...), v_compra: float=Form(...), v_venda: float=Form(...), unid_caixa: int=Form(...), qtd_entrada: int=Form(...), tipo_entrada: str=Form(...)):
    # Cálculo de entrada: se for caixa, multiplica pela qtd de unidades
    total_unid = (qtd_entrada * unid_caixa) if tipo_entrada == 'caixa' else qtd_entrada
    
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (nome, valor_compra, valor_venda, unidades_por_caixa, estoque_unidades_total) VALUES (?,?,?,?,?)",
                   (nome, v_compra, v_venda, unid_caixa, total_unid))
    conn.commit(); conn.close()
    return RedirectResponse("/estoque_web", status_code=303)

# --- TELA DE EDIÇÃO E SAÍDA DETALHADA ---
@app.get("/estoque/editar/{id}", response_class=HTMLResponse)
def form_editar_estoque(id: int):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,)); p = cursor.fetchone()
    conn.close()
    
    return f"""
    <html><head>{get_style()}</head><body>
    <nav><a href='/estoque_web'>⬅️ Cancelar</a></nav>
    <div class='container'>
        <div class='card'>
            <h3>📝 Gerenciar: {p['nome']}</h3>
            <p>Saldo atual: <b>{p['estoque_unidades_total']} unidades</b></p>
            <hr>
            <h4>🚨 Registrar Saída (Avaria, Venda Avulsa, etc)</h4>
            <form action='/estoque/saida_detalhada/{id}' method='post' class='flex-row'>
                <input type='number' name='qtd' placeholder='Qtd' required>
                <select name='tipo'>
                    <option value='unid'>Unidades</option>
                    <option value='caixa'>Caixas</option>
                </select>
                <input name='motivo' placeholder='Motivo (Ex: Avaria, Brinde...)' required>
                <button type='submit' class='btn btn-red'>Confirmar Saída</button>
            </form>
        </div>
    </div></body></html>
    """
# --- PROCESSAR SAÍDA DETALHADA ---
@app.post("/estoque/saida_detalhada/{id}")
def processar_saida(request: Request, id: int, qtd: int=Form(...), tipo: str=Form(...), motivo: str=Form(...)):
    usuario = request.cookies.get("usuario_login")
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,)); p = cursor.fetchone()
    
    total_saida = (qtd * p['unidades_por_caixa']) if tipo == 'caixa' else qtd
    
    if p['estoque_unidades_total'] >= total_saida:
        novo_saldo = p['estoque_unidades_total'] - total_saida
        cursor.execute("UPDATE produtos SET estoque_unidades_total = ? WHERE id = ?", (novo_saldo, id))
        cursor.execute("INSERT INTO movimentacoes (data_hora, produto, tipo, quantidade_unid, usuario, motivo) VALUES (?,?,'SAÍDA',?,?,?)",
                       (datetime.now().strftime("%d/%m/%Y %H:%M"), p['nome'], total_saida, usuario, motivo))
        conn.commit()
    
    conn.close()
    return RedirectResponse("/estoque_web", status_code=303)
# --- USUÁRIOS ---
@app.get("/usuarios_web", response_class=HTMLResponse)
def usuarios_web(request: Request):
    if get_user_cargo(request) != "Admin": return RedirectResponse("/dashboard")
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios"); users = cursor.fetchall()
    conn.close()
    linhas = "".join([f"<tr><td>{u['username']}</td><td>{u['cargo']}</td></tr>" for u in users])
    return f"<html><head>{get_style()}</head><body><nav><a href='/dashboard'>⬅️ Voltar</a></nav><div class='container'><div class='card'><h3>Gestão de Acesso</h3><table><tr><th>Usuário</th><th>Cargo</th></tr>{linhas}</table></div></div></body></html>"