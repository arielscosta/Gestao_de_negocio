from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import database

app = FastAPI()

# --- LOGIN (Simplificado) ---
@app.get("/", response_class=HTMLResponse)
def login_page():
    return """
    <html><body style="font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#2c3e50; margin:0;">
        <form action="/login" method="post" style="background:white; padding:40px; border-radius:10px; text-align:center;">
            <h2>🔐 Login ERP</h2>
            <input type="text" name="usuario" placeholder="Seu Nome" required style="padding:10px; width:100%; margin-bottom:10px;"><br>
            <button type="submit" style="padding:10px; width:100%; background:#27ae60; color:white; border:none; cursor:pointer;">Entrar</button>
        </form>
    </body></html>
    """

@app.post("/login")
def login(response: Response, usuario: str = Form(...)):
    res = RedirectResponse(url="/dashboard", status_code=303)
    res.set_cookie(key="usuario_login", value=usuario)
    return res

# --- DASHBOARD COM OPÇÃO CAIXA/UNIDADE ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    usuario = request.cookies.get("usuario_login")
    if not usuario: 
        return RedirectResponse(url="/", status_code=303)

    conn = database.conectar()
    conn.row_factory = database.sqlite3.Row
    cursor = conn.cursor()
    
    # Garante as tabelas
    cursor.execute("""CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        unidades_por_caixa INTEGER,
        estoque_unidades_total INTEGER DEFAULT 0,
        valor_unitario REAL,
        status TEXT DEFAULT 'ativo'
    )""")
    
    cursor.execute("SELECT * FROM produtos WHERE status = 'ativo' ORDER BY nome ASC")
    produtos = cursor.fetchall()
    conn.close()

    # 1. PRIMEIRO: Criamos a variável com as linhas da tabela
    linhas_tabela = ""
    for p in produtos:
        caixas = p['estoque_unidades_total'] // p['unidades_por_caixa']
        sobras = p['estoque_unidades_total'] % p['unidades_por_caixa']
        
        linhas_tabela += f"""
        <tr>
            <td><strong>{p['nome']}</strong></td>
            <td>
                {p['estoque_unidades_total']} un. 
                <br><span class="badge-cx">{caixas} cx e {sobras} un</span>
            </td>
            <td>R$ {p['valor_unitario']:.2f}</td>
            <td>
                <form action="/saida/{p['id']}" method="post" class="form-saida">
                    <input type="number" name="qtd_saida" placeholder="Qtd" required style="width:60px;">
                    <select name="tipo_saida">
                        <option value="unidade">Unid.</option>
                        <option value="caixa">Caixa</option>
                    </select>
                    <input type="text" name="motivo" placeholder="Motivo" required style="width:100px;">
                    <button type="submit" class="btn-saida">⬇</button>
                </form>
            </td>
        </tr>"""

    # 2. SEGUNDO: Retornamos o HTML usando a variável que já foi definida acima
    return f"""
    <html>
        <head>
            <title>Gestão ERP</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }}
                .container {{ width: 100%; max-width: 1100px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); }}
                .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 15px; margin-bottom: 20px; }}
                .form-entrada {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 30px; }}
                input, select {{ padding: 12px; border: 1px solid #ccc; border-radius: 6px; }}
                .btn-cadastrar {{ grid-column: 1 / -1; background: #2c3e50; color: white; font-weight: bold; border: none; cursor: pointer; padding: 15px; border-radius: 6px; }}
                .table-container {{ overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; min-width: 700px; }}
                th {{ background: #34495e; color: white; padding: 15px; text-align: left; }}
                td {{ padding: 15px; border-bottom: 1px solid #eee; }}
                .badge-cx {{ background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
                .form-saida {{ display: flex; gap: 8px; margin: 0; }}
                .btn-saida {{ background: #e74c3c; color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📦 Estoque Ativo: <span style="color:#3498db;">{usuario}</span></h2>
                    <a href="/historico" style="text-decoration:none; color:#3498db; font-weight:bold;">📜 Ver Histórico</a>
                </div>
                
                <form action="/cadastrar" method="post" class="form-entrada">
                    <input type="text" name="nome" placeholder="Produto" required>
                    <input type="number" name="unidades_por_caixa" placeholder="Unid. na Caixa" required>
                    <input type="number" name="quantidade_entrada" placeholder="Qtd Entrada" required>
                    <select name="tipo_entrada">
                        <option value="unidade">Unidades</option>
                        <option value="caixa">Caixas</option>
                    </select>
                    <input type="number" step="0.01" name="preco_unit" placeholder="Preço Unit. (R$)" required>
                    <button type="submit" class="btn-cadastrar">REGISTRAR ENTRADA</button>
                </form>

                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th><th>Estoque Total</th><th>Unitário</th><th>Saída Rápida</th>
                            </tr>
                        </thead>
                        <tbody>
                            {linhas_tabela}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
    </html>
    """

# --- LÓGICA DE PROCESSAMENTO ---

@app.post("/cadastrar")
def cadastrar(request: Request, nome: str = Form(...), unidades_por_caixa: int = Form(...), 
              quantidade_entrada: int = Form(...), tipo_entrada: str = Form(...), preco_unit: float = Form(...)):
    
    # Cálculo: Transforma tudo em unidades
    total_unidades = quantidade_entrada * unidades_por_caixa if tipo_entrada == "caixa" else quantidade_entrada
    usuario = request.cookies.get("usuario_login", "Sistema")
    
    conn = database.conectar()
    cursor = conn.cursor()
    
    # Verifica se produto já existe para somar estoque ou criar novo
    cursor.execute("SELECT id, estoque_unidades_total FROM produtos WHERE nome = ? AND status = 'ativo'", (nome,))
    existente = cursor.fetchone()
    
    if existente:
        novo_total = existente[1] + total_unidades
        cursor.execute("UPDATE produtos SET estoque_unidades_total = ?, valor_unitario = ? WHERE id = ?", (novo_total, preco_unit, existente[0]))
    else:
        cursor.execute("INSERT INTO produtos (nome, unidades_por_caixa, estoque_unidades_total, valor_unitario) VALUES (?, ?, ?, ?)", 
                       (nome, unidades_por_caixa, total_unidades, preco_unit))
    
    cursor.execute("INSERT INTO movimentacoes (data_hora, produto, tipo, quantidade_unid, usuario, motivo) VALUES (?, ?, ?, ?, ?, ?)",
                   (datetime.now().strftime("%d/%m/%Y %H:%M"), nome, "ENTRADA", total_unidades, usuario, f"Entrada de {quantidade_entrada} {tipo_entrada}"))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/saida/{id}")
def saida(id: int, request: Request, qtd_saida: int = Form(...), tipo_saida: str = Form(...), motivo: str = Form(...)):
    usuario = request.cookies.get("usuario_login", "Sistema")
    conn = database.conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nome, unidades_por_caixa, estoque_unidades_total FROM produtos WHERE id = ?", (id,))
    p = cursor.fetchone()
    
    if p:
        unid_remover = qtd_saida * p[1] if tipo_saida == "caixa" else qtd_saida
        
        if p[2] >= unid_remover:
            novo_estoque = p[2] - unid_remover
            cursor.execute("UPDATE produtos SET estoque_unidades_total = ? WHERE id = ?", (novo_estoque, id))
            cursor.execute("INSERT INTO movimentacoes (data_hora, produto, tipo, quantidade_unid, usuario, motivo) VALUES (?, ?, ?, ?, ?, ?)",
                           (datetime.now().strftime("%d/%m/%Y %H:%M"), p[0], "SAÍDA", unid_remover, usuario, motivo))
            conn.commit()
        else:
            return {"erro": "Estoque insuficiente para essa quantidade!"}
            
    conn.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/historico", response_class=HTMLResponse)
def historico():
    conn = database.conectar()
    conn.row_factory = database.sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movimentacoes ORDER BY id DESC")
    logs = cursor.fetchall()
    conn.close()
    
    linhas = "".join([f"<tr><td>{l['data_hora']}</td><td>{l['produto']}</td><td>{l['tipo']}</td><td>{l['quantidade_unid']} un</td><td>{l['usuario']}</td><td>{l['motivo']}</td></tr>" for l in logs])
    return f"<html><body><h2>📜 Histórico</h2><table border='1'>{linhas}</table><br><a href='/dashboard'>Voltar</a></body></html>"