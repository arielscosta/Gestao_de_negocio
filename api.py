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

# --- FUNÇÃO AUXILIAR COM PESO DE ACESSO ---
def get_user_info(request: Request):
    usuario_nome = request.cookies.get("usuario_login")
    if not usuario_nome: return None, None, 0
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cargo FROM usuarios WHERE username = ?", (usuario_nome,))
    u = cursor.fetchone()
    conn.close()
    
    patente = u['cargo'] if u else None
    
    # Define o peso da camada para validação simples
    niveis = {"Estoquista": 1, "Operador": 2, "Gerente": 3, "Admin": 4}
    nivel = niveis.get(patente, 0)
    
    return usuario_nome, patente, nivel

# --- ACESSO ---
@app.get("/", response_class=HTMLResponse)
def home_login(request: Request):
    # Só redireciona se o cookie existir
    user_cookie = request.cookies.get("usuario_login")
    if user_cookie:
        # Opcional: Você pode verificar aqui se o user ainda existe no banco
        return RedirectResponse("/dashboard")
    
    return f"<html><head>{get_style()}</head><body style='display:flex;justify-content:center;align-items:center;height:100vh;background:#1a2a3a;'><div class='card' style='width:320px;text-align:center;'><h2>🚀 ERP Login</h2><form action='/login' method='post'><input type='text' name='u' placeholder='Usuário' required><input type='password' name='s' placeholder='Senha' required><button class='btn btn-blue' style='margin-top:10px;'>Entrar</button></form></div></body></html>"
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
    usuario_atual, cargo, nivel = get_user_info(request)
    if not cargo: return RedirectResponse("/")
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes"); c_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM produtos WHERE status='ativo'"); p_count = cursor.fetchone()[0]
    conn.close()

    return f"""
    <html><head>{get_style()}</head><body>
    <nav>
        <a href='/usuarios_web'>👤 Gestão de Usuários</a>
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
    user_logado, cargo, nivel = get_user_info(request)

    if not user_logado:
        # Se o cookie existe mas o get_user_info falhou (ex: banco resetado)
        # Precisamos MATAR o cookie antes de mandar para o login
        res = RedirectResponse("/", status_code=303)
        res.delete_cookie("usuario_login")
        return res
    
    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()

    # --- LÓGICA DAS LINHAS COM STATUS E APROVAÇÃO ---
    linhas = ""    
    for c in clientes:
        # Acesso correto para sqlite3.Row
        status_atual = c['status'] if 'status' in c.keys() else 'Pendente'
        if not status_atual: status_atual = 'Pendente'
        
        cor = "#e67e22" if status_atual == "Pendente" else "#27ae60"        
              
        # Só mostra o botão 'Aprovar' se for Gerente/Admin e o cliente estiver Pendente
        btn_aprovar = ""
        if nivel >= 3 and status_atual == "Pendente":
            btn_aprovar = f"""
            <a href='/clientes/aprovar/{c['id']}' 
               style='background:#2ecc71; color:white; padding:2px 6px; text-decoration:none; border-radius:4px; font-size:11px; margin-left:10px;'>
               ✅ Aprovar
            </a>"""

        linhas += f"""
        <tr>
            <td>{c['id']}</td>
            <td>{c['nome']} <small style='color:{cor}; font-weight:bold;'>({status_atual})</small></td>
            <td>{c['empresa']}</td>
            <td>
                <a href='/clientes/detalhe/{c['id']}'>🔍 Ver</a>
                {btn_aprovar}
            </td>
        </tr>
        """
    # -----------------------------------------------
    
    form_novo = ""
    if cargo in ["Admin", "Gerente", "Operador"]:
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
    user_logado, cargo, nivel = get_user_info(request)
    if cargo not in ["Admin", "Gerente"]:
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
def novo_cliente(
    request: Request,
    nome: str=Form(...),
    endereco: str=Form(None),
    telefone: str=Form(None), 
    data_nasc: str=Form(None), 
    email: str=Form(None), 
    empresa: str=Form(None)):
    # Trava de Segurança Camada 2 (Estoquista não cadastra cliente)
    _, _, nivel = get_user_info(request) 
    if nivel < 2:
        return RedirectResponse("/dashboard", status_code=303)
    conn = database.conectar(); cursor = conn.cursor()
    # Adicione uma coluna 'status' como 'Pendente' para o gerente aprovar depois
    cursor.execute("""
        INSERT INTO clientes (nome, endereco, telefone, status) 
        VALUES (?, ?, ?, 'Pendente')
    """, (nome, endereco, telefone))
    conn.commit(); conn.close()
    
    return RedirectResponse("/clientes_web", status_code=303)

 #-- APROVAR CLIENTE ---
@app.get("/clientes/detalhe/{id}", response_class=HTMLResponse)
def detalhe_cliente(id: int):
    conn = database.conectar()
    cursor = conn.cursor()
    
    # Busca dados do cliente
    cursor.execute("SELECT * FROM clientes WHERE id=?", (id,))
    c = cursor.fetchone()
    
    # Busca pedidos (Note que não pedimos mais a coluna 'produtos' que não existe)
    cursor.execute("SELECT id, data, valor_total, status FROM pedidos WHERE cliente_id=?", (id,))
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

    # CORREÇÃO DA TABELA: Substituímos p['produtos'] por Pedido # + id
    linhas_pedidos = "".join([
        f"<tr><td>{p['data']}</td><td>Pedido #{p['id']}</td><td>R$ {p['valor_total']:.2f}</td><td>{p['status']}</td></tr>" 
        for p in peds
    ]) or "<tr><td colspan='4'>Sem histórico.</td></tr>"

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
                        <tr><th>Data</th><th>Identificação</th><th>Valor</th><th>Status</th></tr>
                        {linhas_pedidos}
                    </table>
                </div>
            </div>
        </div>
    </div></body></html>
    """

                                            # --- PEDIDOS E PAGAMENTOS ---
        #-- FORMULÁRIO DE PEDIDO ---
@app.get("/clientes/pedido/{id}", response_class=HTMLResponse)
def form_pedido(id: int, request: Request):
    conn = database.conectar(); cursor = conn.cursor()
    cursor.execute("SELECT id, nome, valor_venda, unidades_por_caixa, estoque_unidades_total FROM produtos WHERE estoque_unidades_total > 0")
    prods = cursor.fetchall()
    conn.close()

    # Gerando os dados dos produtos para o JavaScript usar
    # Criamos uma lista de botões na tabela
    linhas_produtos = ""
    for p in prods:
        valor_cx = p['valor_venda'] * p['unidades_por_caixa']
        linhas_produtos += f"""
    <tr class='produto-linha' data-nome='{p['nome'].lower()}'>
        <td style='min-width: 150px;'>{p['nome']}</td>
        <td>R$ {p['valor_venda']:.2f}</td>
        <td>R$ {valor_cx:.2f}</td>
        <td class='col-estoque'>{p['estoque_unidades_total']}</td>
        <td style='min-width: 220px;'>
            <div style='display: flex; gap: 8px; align-items: center;'>
                <input type='number' id='qtd_{p['id']}' class='qtd-input' value='1' min='1'>
                <button onclick="addCarrinho({p['id']}, '{p['nome']}', {p['valor_venda']}, {p['unidades_por_caixa']}, 'unidade')" class='btn-un'>+Un</button>
                <button onclick="addCarrinho({p['id']}, '{p['nome']}', {p['valor_venda']}, {p['unidades_por_caixa']}, 'caixa')" class='btn-cx'>+Cx</button>
            </div>
        </td>
    </tr>"""

    return f"""
    <html>
    <head>
        {get_style()}
        <style>
            .topo-fixo {{ position: sticky; top: 0; background: #2c3e50; color: white; padding: 15px; display: flex; justify-content: space-between; z-index: 100; border-radius: 0 0 10px 10px; }}
            .carrinho-container {{ background: #ecf0f1; padding: 15px; border-radius: 10px; margin-top: 20px; border: 2px dashed #bdc3c7; }}
            .btn-un {{ background: #2980b9; color: white; border: none; padding: 5px; cursor: pointer; }}
            .btn-cx {{ background: #27ae60; color: white; border: none; padding: 5px; cursor: pointer; }}
            .item-carrinho {{ display: flex; justify-content: space-between; background: white; padding: 10px; margin-bottom: 5px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class='topo-fixo'>
            <span style='font-size: 20px;'>🛒 Pedido: Cliente #{id}</span>
            <span style='font-size: 24px; font-weight: bold;'>Total: R$ <span id='txt-total'>0.00</span></span>
        </div>

        <div class='container'>
            <input type='text' id='busca' onkeyup='filtrar()' placeholder='🔍 Pesquisar produto...' style='width:100%; padding:10px; margin: 15px 0;'>
            
            <div style='display: flex; gap: 20px;'>
                <div style='flex: 2;'>
                    <table style='width: 100%; background: white;'>
                        <thead><tr><th>Produto</th><th>Un</th><th>Cx</th><th>Est</th><th>Ação</th></tr></thead>
                        <tbody id='corpo'>{linhas_produtos}</tbody>
                    </table>
                </div>

                <div style='flex: 1;'>
                    <div class='carrinho-container'>
                        <h3>Lista do Pedido</h3>
                        <div id='lista-carrinho'>
                            </div>
                        <form action='/pedido/finalizar' method='post' id='form-final'>
                            <input type='hidden' name='cliente_id' value='{id}'>
                            <input type='hidden' name='carrinho_data' id='carrinho_data'>
                            <button type='button' onclick='enviarPedido()' class='btn btn-green' style='width: 100%; margin-top: 15px; padding: 15px;'>FINALIZAR PEDIDO</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let carrinho = [];
            let totalGeral = 0;

            function addCarrinho(id, nome, precoUn, unidCx, tipo) {{
                let qtd = parseInt(document.getElementById('qtd_'+id).value);
                let valorItem = (tipo === 'caixa') ? (precoUn * unidCx * qtd) : (precoUn * qtd);
                
                carrinho.push({{ id, nome, qtd, tipo, valorItem }});
                atualizarInterface();
            }}

            function atualizarInterface() {{
                let html = "";
                totalGeral = 0;
                carrinho.forEach((item, index) => {{
                    totalGeral += item.valorItem;
                    html += `<div class='item-carrinho'>
                        <span>${{item.qtd}}x ${{item.nome}} (${{item.tipo}})</span>
                        <b>R$ ${{item.valorItem.toFixed(2)}}</b>
                        <button onclick='remover(${{index}})' style='color:red; border:none; background:none; cursor:pointer;'>X</button>
                    </div>`;
                }});
                document.getElementById('lista-carrinho').innerHTML = html;
                document.getElementById('txt-total').innerText = totalGeral.toFixed(2);
                document.getElementById('carrinho_data').value = JSON.stringify(carrinho);
            }}

            function remover(index) {{
                carrinho.splice(index, 1);
                atualizarInterface();
            }}

            function enviarPedido() {{
                if(carrinho.length === 0) return alert("Carrinho vazio!");
                document.getElementById('form-final').submit();
            }}

            function filtrar() {{
                let busca = document.getElementById('busca').value.toLowerCase();
                let linhas = document.getElementsByClassName('produto-linha');
                for (let l of linhas) l.style.display = l.getAttribute('data-nome').includes(busca) ? '' : 'none';
            }}
        </script>
    </body>
    </html>
    """
    
    #-- FINALIZAR PEDIDO ---
import json

@app.post("/pedido/finalizar")
def finalizar_pedido(cliente_id: int = Form(...), carrinho_data: str = Form(...)):
    carrinho = json.loads(carrinho_data)
    conn = database.conectar(); cursor = conn.cursor()
    
    total_pedido = sum(item['valorItem'] for item in carrinho)
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # 1. Cria o Pedido
    cursor.execute("INSERT INTO pedidos (cliente_id, valor_total, data, status) VALUES (?,?,?,?)",
                   (cliente_id, total_pedido, data_atual, 'Pendente'))
    pedido_id = cursor.lastrowid

    # 2. Salva os Itens e Baixa Estoque
    for item in carrinho:
        # Busca dados do produto para saber qts unidades tem na caixa
        cursor.execute("SELECT unidades_por_caixa FROM produtos WHERE id = ?", (item['id'],))
        p = cursor.fetchone()
        
        qtd_unidades = item['qtd'] * p['unidades_por_caixa'] if item['tipo'] == 'caixa' else item['qtd']
        
        cursor.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, tipo, subtotal) VALUES (?,?,?,?,?)",
                       (pedido_id, item['id'], item['qtd'], item['tipo'], item['valorItem']))
        
        cursor.execute("UPDATE produtos SET estoque_unidades_total = estoque_unidades_total - ? WHERE id = ?",
                       (qtd_unidades, item['id']))

    conn.commit(); conn.close()
    return RedirectResponse(f"/pedido/entrega/{cliente_id}", status_code=303)

                                                   # --- PAGAMENTOS ---
        
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

# --- ESTOQUE WEB ---
@app.get("/estoque_web", response_class=HTMLResponse)
def estoque_web(request: Request, busca: str = ""):
    usuario_atual, cargo, nivel = get_user_info(request)
    if cargo not in ["Admin", "Gerente", "Estoquista"]: return RedirectResponse("/dashboard")
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
def processar_entrada_estoque(
    request: Request, 
    nome: str = Form(...), 
    v_compra: float = Form(...), 
    v_venda: float = Form(...), 
    unid_caixa: int = Form(...), 
    qtd_entrada: int = Form(...), 
    tipo_entrada: str = Form(...)
):
    # Trava de Segurança Camada 3 (Apenas Gerente e Admin podem alterar estoque)
    _, _, nivel = get_user_info(request)
    if nivel < 3:
        return RedirectResponse("/estoque_web", status_code=303)

    usuario = request.cookies.get("usuario_login")
        
    # Calcula o total em unidades (se for caixa, multiplica pelo tamanho da caixa)
    total_novas_unid = (qtd_entrada * unid_caixa) if tipo_entrada == 'caixa' else qtd_entrada
    
    conn = database.conectar()
    cursor = conn.cursor()
    
    # Busca se já existe um produto com o mesmo NOME e mesmo TAMANHO DE CAIXA
    cursor.execute("SELECT id, estoque_unidades_total FROM produtos WHERE nome = ? AND unidades_por_caixa = ?", 
                   (nome.upper(), unid_caixa))
    produto_existente = cursor.fetchone()

    if produto_existente:
        # Se existe, apenas soma a nova quantidade ao saldo atual
        novo_saldo = produto_existente['estoque_unidades_total'] + total_novas_unid
        cursor.execute("""
            UPDATE produtos 
            SET valor_compra = ?, valor_venda = ?, estoque_unidades_total = ? 
            WHERE id = ?
        """, (v_compra, v_venda, novo_saldo, produto_existente['id']))
        acao_log = f"Entrada de {total_novas_unid} un no produto {nome} (Estoque Atualizado)"
    else:
        # Se não existe, cria o registro do zero
        cursor.execute("""
            INSERT INTO produtos (nome, valor_compra, valor_venda, unidades_por_caixa, estoque_unidades_total) 
            VALUES (?, ?, ?, ?, ?)
        """, (nome.upper(), v_compra, v_venda, unid_caixa, total_novas_unid))
    acao_log = f"Novo produto cadastrado: {nome} com {total_novas_unid} un"

    conn.commit()
    conn.close()
    
    # Registra a ação no log (Certifique-se que a função registrar_log existe no database.py)
    try:
        database.registrar_log(usuario, acao_log)
    except:
        pass # Evita travar a API se a função de log ainda não estiver pronta
        
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
@app.post("/estoque/saida")
def registrar_saida(
    request: Request, 
    id: int = Form(...), 
    qtd: int = Form(...), 
    tipo: str = Form(...), 
    motivo: str = Form(...)
):
    # Trava de Segurança Camada 3 (Apenas Gerente e Admin podem alterar estoque)
    _, _, nivel = get_user_info(request)
    if nivel < 3:
        return RedirectResponse("/estoque_web", status_code=303)

    usuario = request.cookies.get("usuario_login")   
    conn = database.conectar()
    cursor = conn.cursor()
    
    # Busca o produto para saber o tamanho da caixa e o saldo atual
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    p = cursor.fetchone()
    
    if not p:
        conn.close()
        return RedirectResponse("/estoque_web", status_code=303)

    # Calcula o total que vai sair em unidades
    total_saida = (qtd * p['unidades_por_caixa']) if tipo == 'caixa' else qtd
    
    # Verifica se há saldo suficiente
    if p['estoque_unidades_total'] >= total_saida:
        novo_saldo = p['estoque_unidades_total'] - total_saida
        cursor.execute("UPDATE produtos SET estoque_unidades_total = ? WHERE id = ?", (novo_saldo, id))
        
        # Registra a movimentação no histórico
        cursor.execute("""
            INSERT INTO movimentacoes (data_hora, produto, tipo, quantidade_unid, usuario, motivo) 
            VALUES (?, ?, 'SAÍDA', ?, ?, ?)
        """, (datetime.now().strftime("%d/%m/%Y %H:%M"), p['nome'], total_saida, usuario, motivo))
        
        conn.commit()
        conn.close()
        return RedirectResponse("/estoque_web", status_code=303)

# --- USUÁRIOS ---
@app.get("/usuarios_web", response_class=HTMLResponse)
def usuarios_web(request: Request):
    # Trava de Segurança Camada 4
    _, _, nivel = get_user_info(request)
    if nivel < 4:
        return RedirectResponse("/dashboard", status_code=303)
    """
    Exibe a lista de usuários e o formulário de cadastro.
    Restrito ao cargo 'Admin' para controle de camadas de acesso.
    """
    user_logado, cargo, nivel = get_user_info(request) 
    
    # Camada de acesso: Apenas Admin pode gerenciar usuários
    if cargo != "Admin":
        return RedirectResponse("/dashboard", status_code=303)

    conn = database.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY matricula ASC")
    lista_users = cursor.fetchall()
    conn.close()

    linhas = ""
    for u in lista_users:
        linhas += f"<tr><td>{u['matricula']}</td><td>{u['nome_completo']}</td><td>{u['cargo']}</td><td>{u['username']}</td></tr>"

    return f"""
    <html><head>{get_style()}</head><body>
    <nav><a href='/dashboard'>🏠 Home</a><b>Gestão de Acessos</b></nav>
    <div class='container'>
        <div class='card'>
            <h3>👤 Cadastrar Novo Usuário (Camada de Acesso)</h3>
            <form action='/usuarios/novo' method='post' style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                <input name='nome_completo' placeholder='Nome Completo' required style='grid-column: span 2;'>
                <input name='cpf' placeholder='CPF (Somente números)' required>
                <input name='celular' placeholder='Celular' required>
                <input name='username' placeholder='Login de Acesso' required>
                <input type='password' name='password' placeholder='Senha' required>
                <select name='cargo' style='grid-column: span 2;'>
                    <option value='Estoquista'>Nível 1: Estoquista (Logística)</option>
                    <option value='Operador'>Nível 2: Operador (Vendas/Cadastro)</option>
                    <option value='Gerente'>Nível 3: Gerente (Aprovação/Estoque)</option>
                    <option value='Admin'>Nível 4: Admin (Sistema)</option>
                </select>
                <button type='submit' class='btn btn-blue' style='grid-column: span 2;'>Gerar Matrícula e Salvar</button>
            </form>
        </div>
        <div class='card'>
            <h3>📋 Usuários Ativos</h3>
            <table><tr><th>Matrícula</th><th>Nome</th><th>Patente/Cargo</th><th>Login</th></tr>{linhas}</table>
        </div>
    </div></body></html>
    """

# --- ROTA PARA CRIAR USUÁRIO COM MATRÍCULA AUTOMÁTICA ---
@app.post("/usuarios/novo")
def criar_usuario(
    request: Request, 
    nome_completo: str = Form(...), 
    cpf: str = Form(...), 
    celular: str = Form(...), 
    username: str = Form(...), 
    password: str = Form(...), 
    cargo: str = Form(...)
):
    # Trava de Segurança Camada 4
    _, _, nivel = get_user_info(request)
    if nivel < 4:
        return RedirectResponse("/dashboard", status_code=303)
    
    conn = database.conectar()
    cursor = conn.cursor()

    # 2. GERADOR DE MATRÍCULA AUTOMÁTICA
    # Buscamos a maior matrícula atual transformando o texto em número
    cursor.execute("SELECT MAX(CAST(matricula AS INTEGER)) FROM usuarios")
    resultado = cursor.fetchone()[0]
    
    if resultado is None:
        nova_matricula = "1000"  # Primeira matrícula do sistema
    else:
        nova_matricula = str(resultado + 1) # Soma 1 ao último cadastrado

    # 3. INSERÇÃO NO BANCO
    try:
        cursor.execute('''
            INSERT INTO usuarios (username, password, cargo, matricula, nome_completo, cpf, celular) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, cargo, nova_matricula, nome_completo, cpf, celular))
        
        conn.commit()
        
        # Registra quem criou quem (Auditoria entre Usuários e Logs)
        database.registrar_log(usuario_logado, f"GEROU ACESSO: Matrícula {nova_matricula} para {nome_completo}")
        
    except Exception as e:
        print(f"Erro ao salvar: {e}")
    finally:
        conn.close()

    return RedirectResponse("/usuarios_web", status_code=303)
# --- APROVAR CLIENTE ---
@app.get("/clientes/aprovar/{id}")
def aprovar_cliente(id: int, request: Request):
    # Verifica quem está tentando aprovar
    _, _, nivel = get_user_info(request)
    
    if nivel < 3: # Se não for Gerente ou Admin, expulsa
        return RedirectResponse("/dashboard", status_code=303)

    conn = database.conectar()
    cursor = conn.cursor()
    
    # Atualiza o status para Ativo
    cursor.execute("UPDATE clientes SET status = 'Ativo' WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse("/clientes_web", status_code=303)
# --- TELA DE NOVO PEDIDO ---#
@app.get("/pedido/novo/{cliente_id}", response_class=HTMLResponse)
def tela_novo_pedido(cliente_id: int, request: Request):
    _, _, nivel = get_user_info(request)
    conn = database.conectar(); cursor = conn.cursor()
    
    # Busca produtos e informações do cliente
    cursor.execute("SELECT * FROM produtos WHERE quantidade > 0")
    produtos = cursor.fetchall()
    cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()
    conn.close()

    lista_produtos = ""
    for p in produtos:
        # Supondo que você tenha campos preco_un e preco_cx
        lista_produtos += f"""
        <div class='product-item' data-nome='{p['nome'].lower()}'>
            <span><b>{p['nome']}</b> (Estoque: {p['quantidade']})</span>
            <div style='display:flex; gap:10px; align-items:center;'>
                <span>Un: R$ {p['preco']:.2f}</span>
                <input type='number' class='qtd-input' data-preco='{p['preco']}' placeholder='Qtd' style='width:100px;' oninput='calcularTotal()'>
                <select class='tipo-input' onchange='calcularTotal()'>
                    <option value='un'>Unidade</option>
                    <option value='cx'>Caixa</option>
                </select>
            </div>
        </div><hr>"""

    return f"""
    <html>
    <head>
        {get_style()}
        <style>
            /* Slot de Total no topo */
            .sticky-total {{ 
                position: fixed; top: 10px; right: 10px; 
                background: #27ae60; color: white; padding: 20px; 
                border-radius: 8px; font-size: 28px; font-weight: bold;
                z-index: 1000; box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
            }}
            /* Slot de Quantidade - Aumentado para números grandes */
            .qtd-input-pdv {{ 
                width: 100px !important; 
                height: 40px;
                font-size: 18px;
                text-align: center;
                border: 2px solid #3498db;
                border-radius: 5px;
            }}
            .search-bar {{ width: 100%; padding: 15px; margin-bottom: 20px; border-radius: 8px; border: 2px solid #ddd; font-size: 16px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
            .btn-un {{ background: #2980b9; color: white; border: none; padding: 10px; cursor: pointer; border-radius: 4px; font-weight: bold; }}
            .btn-cx {{ background: #27ae60; color: white; border: none; padding: 10px; cursor: pointer; border-radius: 4px; font-weight: bold; }}
            .item-carrinho {{ background: #f9f9f9; padding: 10px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; }}
        </style>
    </head>
    <body>
        <div class='sticky-total'>R$ <span id='txt-total'>0.00</span></div>
        
        <div class='container'>
            <h2>🛒 Novo Pedido: {cliente['nome']}</h2>
            <input type='text' class='search-bar' id='pesquisa' placeholder='🔍 Pesquisar produto por nome...' onkeyup='filtrar()'>
            
            <div style='display: flex; gap: 20px;'>
                <div style='flex: 2;' class='card'>
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th>Unitário</th>
                                <th>Caixa</th>
                                <th>Estoque</th>
                                <th>Quantidade e Lançamento</th>
                            </tr>
                        </thead>
                        <tbody id='lista-produtos'>
                            {lista_produtos}
                        </tbody>
                    </table>
                </div>

                <div style='flex: 1;' class='card'>
                    <h3>📋 Resumo do Pedido</h3>
                    <div id='lista-carrinho' style='max-height: 400px; overflow-y: auto; margin-bottom: 15px;'>
                        <p style='color: #888;'>Nenhum item adicionado...</p>
                    </div>
                    
                    <form action='/pedido/finalizar' method='post' id='form-final'>
                        <input type='hidden' name='cliente_id' value='{cliente_id}'>
                        <input type='hidden' name='carrinho_data' id='carrinho_data'>
                        <button type='button' onclick='enviarPedido()' class='btn btn-green' style='width:100%; padding:20px; font-size: 18px;'>
                            CONFIRMAR PEDIDO
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <script>
            let carrinho = [];

            function addCarrinho(id, nome, precoUn, unidCx, tipo) {{
                let inputQtd = document.getElementById('qtd_'+id);
                let qtd = parseInt(inputQtd.value);
                
                if (qtd <= 0 || isNaN(qtd)) return alert("Insira uma quantidade válida");

                let valorItem = (tipo === 'caixa') ? (precoUn * unidCx * qtd) : (precoUn * qtd);
                
                carrinho.push({{ id, nome, qtd, tipo, valorItem }});
                inputQtd.value = 1; // Reseta o campo após adicionar
                atualizarInterface();
            }}

            function atualizarInterface() {{
                let html = "";
                let total = 0;
                carrinho.forEach((item, index) => {{
                    total += item.valorItem;
                    html += `<div class='item-carrinho'>
                        <span>${{item.qtd}}x ${{item.nome}} (${{item.tipo}})</span>
                        <b>R$ ${{item.valorItem.toFixed(2)}}</b>
                        <button onclick='remover(${{index}})' style='color:red; border:none; background:none; cursor:pointer;'>[X]</button>
                    </div>`;
                }});
                
                if(carrinho.length === 0) html = "<p style='color: #888;'>Nenhum item adicionado...</p>";
                
                document.getElementById('lista-carrinho').innerHTML = html;
                document.getElementById('txt-total').innerText = total.toFixed(2);
                document.getElementById('carrinho_data').value = JSON.stringify(carrinho);
            }}

            function remover(index) {{
                carrinho.splice(index, 1);
                atualizarInterface();
            }}

            function enviarPedido() {{
                if(carrinho.length === 0) return alert("Adicione pelo menos um item!");
                document.getElementById('form-final').submit();
            }}

            function filtrar() {{
                let input = document.getElementById('pesquisa').value.toLowerCase();
                let linhas = document.getElementsByClassName('produto-linha');
                for (let l of linhas) {{
                    l.style.display = l.getAttribute('data-nome').includes(input) ? '' : 'none';
                }}
            }}
        </script>
    </body>
    </html>
    """
# --- AÇÃO: FINALIZAR PEDIDO E IR PARA ENTREGA ---
@app.post("/pedido/finalizar")
def finalizar_pedido_inicial(request: Request, cliente_id: int = Form(...)):
    # Aqui, no futuro, salvaremos os itens. 
    # Por enquanto, ele serve como gatilho para a próxima tela do seu fluxo.
    return RedirectResponse(f"/pedido/entrega/{cliente_id}", status_code=303)

# --- TELA: AGENDAMENTO DE ENTREGA ---
@app.get("/pedido/entrega/{cliente_id}", response_class=HTMLResponse)
def tela_entrega(cliente_id: int, request: Request):
    return f"""
    <html>
    <head>{get_style()}</head>
    <body>
        <div class='container'>
            <div class='card'>
                <h2>🚚 Agendar Entrega</h2>
                <form action='/pedido/pagamento' method='post'>
                    <input type='hidden' name='cliente_id' value='{cliente_id}'>
                    
                    <label>Data da Entrega:</label>
                    <input type='date' name='data_entrega' required style='width:100%; margin-bottom:15px;'>
                    
                    <label>Horário Aproximado:</label>
                    <input type='time' name='hora_entrega' required style='width:100%; margin-bottom:15px;'>
                    
                    <button type='submit' class='btn btn-blue' style='width:100%;'>Ir para Pagamento 💳</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

# --- TELA: PAGAMENTO ---
@app.get("/pedido/pagamento/{cliente_id}", response_class=HTMLResponse)
def tela_pagamento(cliente_id: int, request: Request):
    return f"""
    <html>
    <head>{get_style()}</head>
    <body>
        <div class='container'>
            <div class='card' style='max-width: 400px; margin: auto; text-align: center;'>
                <h2>💳 Formas de Pagamento</h2>
                <p>Selecione como o cliente irá pagar:</p>
                
                <form action='/pedido/concluir' method='post'>
                    <input type='hidden' name='cliente_id' value='{cliente_id}'>
                    
                    <div style='display: grid; gap: 10px; margin-top: 20px;'>
                        <label class='btn' style='background:#f1c40f; color:black;'>
                            <input type='radio' name='metodo' value='Dinheiro' checked> 💵 Dinheiro
                        </label>
                        <label class='btn' style='background:#3498db; color:white;'>
                            <input type='radio' name='metodo' value='Pix'> 📱 Pix
                        </label>
                        <label class='btn' style='background:#9b59b6; color:white;'>
                            <input type='radio' name='metodo' value='Cartão Crédito'> 💳 Cartão Crédito
                        </label>
                        <label class='btn' style='background:#8e44ad; color:white;'>
                            <input type='radio' name='metodo' value='Cartão Débito'> 💳 Cartão Débito
                        </label>
                    </div>

                    <button type='submit' class='btn btn-green' style='width:100%; margin-top:30px; padding:15px; font-size:18px;'>
                        ✅ Finalizar e Gerar Comprovante
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

# --- AÇÃO: CONCLUIR TUDO ---
@app.post("/pedido/pagamento")
def processar_entrega_para_pagamento(cliente_id: int = Form(...)):
    # Esta rota apenas faz a ponte entre a tela de entrega e a de pagamento
    return RedirectResponse(f"/pedido/pagamento/{cliente_id}", status_code=303)

@app.post("/pedido/concluir")
def concluir_pedido(cliente_id: int = Form(...), metodo: str = Form(...)):
    # Aqui é onde o pedido seria salvo definitivamente no banco com o status 'Concluído'
    # Por agora, vamos redirecionar para o detalhe do cliente com uma mensagem de sucesso
    return RedirectResponse(f"/clientes/detalhe/{cliente_id}", status_code=303)