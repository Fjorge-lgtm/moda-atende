# =============================================================
# app.py — Loja de Roupas | Sistema de Atendimento
# Framework: Flask + SQLAlchemy + SQLite
# =============================================================

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
import calendar
import re
import os

# -------------------------------------------------------------
# CONFIGURAÇÃO
# -------------------------------------------------------------
app = Flask(__name__)

# VERCEL COMPATIBILITY: Use /tmp for SQLite in serverless environments
if os.environ.get('VERCEL'):
    DATABASE_PATH = '/tmp/loja_roupas.db'
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    os.makedirs(DATABASE_DIR, exist_ok=True)
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'loja_roupas.db')

app.config['SECRET_KEY']              = os.environ.get('SECRET_KEY', 'loja-roupas-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =============================================================
# MODELOS
# =============================================================

class Usuario(db.Model):
    """Tabela de usuários: Cliente, Atendente ou Administrador."""
    __tablename__ = 'usuarios'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash    = db.Column(db.String(256), nullable=False)
    cargo         = db.Column(db.String(20), nullable=False, default='Cliente')
    ocorrencia    = db.Column(db.String(50), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    atendimentos_cliente   = db.relationship(
        'Atendimento', foreign_keys='Atendimento.cliente_id',
        backref='cliente', lazy=True
    )
    atendimentos_atendente = db.relationship(
        'Atendimento', foreign_keys='Atendimento.atendente_id',
        backref='atendente', lazy=True
    )

    def set_senha(self, senha):
        """Gera hash seguro da senha."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Verifica se a senha está correta."""
        return check_password_hash(self.senha_hash, senha)


class Atendimento(db.Model):
    """Tabela de tickets de atendimento."""
    __tablename__ = 'atendimentos'

    id               = db.Column(db.Integer, primary_key=True)
    cliente_id       = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    atendente_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    descricao        = db.Column(db.Text, nullable=False)
    status           = db.Column(db.String(20), nullable=False, default='Aberto')
    data_criacao     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_atualizacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))


class Produto(db.Model):
    """Tabela de produtos para controle de estoque."""
    __tablename__ = 'produtos'

    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(120), nullable=False)
    categoria   = db.Column(db.String(50), nullable=False)  # bolsas, sapatos, cintos
    quantidade  = db.Column(db.Integer, nullable=False, default=0)
    preco       = db.Column(db.Float, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# =============================================================
# DECORADORES DE ACESSO
# =============================================================

def login_obrigatorio(f):
    """Bloqueia rotas para usuários não autenticados."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para continuar.', 'aviso')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado


def cargo_obrigatorio(*cargos):
    """Bloqueia rotas para cargos não autorizados."""
    def decorador(f):
        @wraps(f)
        def decorado(*args, **kwargs):
            if session.get('cargo') not in cargos:
                flash('Acesso não autorizado.', 'erro')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorado
    return decorador


# =============================================================
# AUTENTICAÇÃO
# =============================================================



@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['nome']       = usuario.nome
            session['cargo']      = usuario.cargo
            flash(f'Bem-vindo(a), {usuario.nome}!', 'sucesso')
            return redirect(url_for('dashboard'))
        else:
            flash('E-mail ou senha incorretos.', 'erro')

    return render_template('login.html')


@app.route('/logout')
@login_obrigatorio
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# =============================================================
# DASHBOARDS
# =============================================================

@app.route('/dashboard')
@login_obrigatorio
def dashboard():
    """Redireciona ao painel correto conforme o cargo."""
    cargo = session.get('cargo')
    if cargo == 'Administrador':
        return redirect(url_for('painel_admin'))
    elif cargo == 'Atendente':
        return redirect(url_for('painel_atendente'))
    return redirect(url_for('painel_cliente'))


@app.route('/admin')
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def painel_admin():
    """Painel do administrador com estatísticas gerais."""
    return render_template('dashboard_admin.html',
        total_usuarios     = Usuario.query.count(),
        total_atendimentos = Atendimento.query.count(),
        qtd_abertos        = Atendimento.query.filter_by(status='Aberto').count(),
        qtd_andamento      = Atendimento.query.filter_by(status='Em Andamento').count(),
        qtd_concluidos     = Atendimento.query.filter_by(status='Concluido').count(),
        recentes           = Atendimento.query.options(
                                joinedload(Atendimento.cliente),
                                joinedload(Atendimento.atendente)
                            ).order_by(Atendimento.data_criacao.desc()).limit(10).all(),
    )


@app.route('/atendente')
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def painel_atendente():
    """Painel do atendente com seus tickets e os abertos."""
    uid = session['usuario_id']
    return render_template('dashboard_atendente.html',
        meus_tickets  = Atendimento.query.filter_by(atendente_id=uid)
                            .order_by(Atendimento.data_criacao.desc()).all(),
        sem_atendente = Atendimento.query.filter_by(status='Aberto', atendente_id=None)
                            .order_by(Atendimento.data_criacao.asc()).all(),
    )


@app.route('/cliente')
@login_obrigatorio
@cargo_obrigatorio('Cliente', 'Administrador')
def painel_cliente():
    """Painel do cliente com seus pedidos de atendimento."""
    uid = session['usuario_id']
    return render_template('dashboard_cliente.html',
        meus_pedidos = Atendimento.query.filter_by(cliente_id=uid)
                           .order_by(Atendimento.data_criacao.desc()).all(),
    )


# =============================================================
# CRUD — ATENDIMENTOS
# =============================================================

@app.route('/atendimentos/novo', methods=['GET', 'POST'])
@login_obrigatorio
def novo_atendimento():
    """Cria um novo ticket de atendimento."""
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    if request.method == 'POST':
        descricao = request.form.get('descricao', '').strip()
        if len(descricao) < 10:
            flash('Descrição muito curta. Detalhe melhor sua solicitação.', 'erro')
            return redirect(url_for('novo_atendimento'))

        db.session.add(Atendimento(
            cliente_id=session['usuario_id'],
            descricao=descricao,
            status='Aberto',
        ))
        db.session.commit()
        flash('Atendimento aberto com sucesso!', 'sucesso')
        return redirect(url_for('dashboard'))

    return render_template('novo_atendimento.html', cliente_nome=usuario.nome)


@app.route('/atendimentos/<int:id>/editar', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def editar_atendimento(id):
    """Edita status e atendente de um ticket."""
    at        = db.get_or_404(Atendimento, id)
    atendentes = Usuario.query.filter_by(cargo='Atendente').all()

    if request.method == 'POST':
        novo_status    = request.form.get('status', at.status)
        nova_descricao = request.form.get('descricao', '').strip()
        atendente_id   = request.form.get('atendente_id', '')

        if novo_status in ('Aberto', 'Em Andamento', 'Concluido'):
            at.status = novo_status
        if nova_descricao:
            at.descricao = nova_descricao
        at.atendente_id      = int(atendente_id) if atendente_id and atendente_id != '0' else None
        at.data_atualizacao  = datetime.now(timezone.utc)

        db.session.commit()
        flash('Ticket atualizado!', 'sucesso')
        return redirect(url_for('dashboard'))

    return render_template('editar_atendimento.html', at=at, atendentes=atendentes)


@app.route('/atendimentos/<int:id>/assumir', methods=['POST'])
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def assumir_atendimento(id):
    """Atendente assume um ticket aberto."""
    at              = db.get_or_404(Atendimento, id)
    at.atendente_id = session['usuario_id']
    at.status       = 'Em Andamento'
    at.data_atualizacao = datetime.now(timezone.utc)
    db.session.commit()
    flash('Ticket assumido!', 'sucesso')
    return redirect(url_for('painel_atendente'))


@app.route('/atendimentos/<int:id>/excluir', methods=['POST'])
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def excluir_atendimento(id):
    """Remove um ticket (somente admin)."""
    at = db.get_or_404(Atendimento, id)
    db.session.delete(at)
    db.session.commit()
    flash('Atendimento excluído.', 'info')
    return redirect(url_for('painel_admin'))


# =============================================================
# CRUD — USUÁRIOS
# =============================================================

@app.route('/usuarios')
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.data_cadastro.desc()).all()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/usuarios/novo', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def novo_usuario():
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        cargo = request.form.get('cargo', 'Cliente')

        if not all([nome, email, senha]):
            flash('Preencha todos os campos.', 'erro')
            return redirect(url_for('novo_usuario'))

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'erro')
            return redirect(url_for('novo_usuario'))

        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            flash('E-mail inválido.', 'erro')
            return redirect(url_for('novo_usuario'))

        if cargo not in ['Cliente', 'Atendente', 'Administrador']:
            cargo = 'Cliente'

        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'erro')
            return redirect(url_for('novo_usuario'))

        u = Usuario(nome=nome, email=email, cargo=cargo)
        u.set_senha(senha)
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao criar o usuário. Verifique os dados e tente novamente.', 'erro')
            return redirect(url_for('novo_usuario'))

        flash(f'Usuário {nome} criado!', 'sucesso')
        return redirect(url_for('listar_usuarios'))

    return render_template('novo_usuario.html')


@app.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def editar_usuario(id):
    u = db.get_or_404(Usuario, id)

    if request.method == 'POST':
        u.nome  = request.form.get('nome', u.nome).strip()
        u.email = request.form.get('email', u.email).strip().lower()
        u.cargo = request.form.get('cargo', u.cargo)
        u.ocorrencia = request.form.get('ocorrencia', u.ocorrencia)
        senha   = request.form.get('senha', '').strip()
        if senha:
            u.set_senha(senha)
        db.session.commit()
        flash('Usuário atualizado!', 'sucesso')
        return redirect(url_for('listar_usuarios'))

    return render_template('editar_usuario.html', u=u)


@app.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def excluir_usuario(id):
    if id == session['usuario_id']:
        flash('Você não pode excluir sua própria conta.', 'erro')
        return redirect(url_for('listar_usuarios'))
    u = db.get_or_404(Usuario, id)
    try:
        db.session.delete(u)
        db.session.commit()
        flash('Usuário removido.', 'info')
    except IntegrityError:
        db.session.rollback()
        flash('Não é possível excluir este usuário pois ele possui atendimentos vinculados.', 'erro')
    return redirect(url_for('listar_usuarios'))


# =============================================================
# CRUD — PRODUTOS (CONTROLE DE ESTOQUE)
# =============================================================

@app.route('/produtos')
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def listar_produtos():
    produtos = Produto.query.order_by(Produto.categoria, Produto.nome).all()
    return render_template('produtos.html', produtos=produtos)


@app.route('/produtos/novo', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def novo_produto():
    if request.method == 'POST':
        nome      = request.form.get('nome', '').strip()
        categoria = request.form.get('categoria', '').strip()
        quantidade = request.form.get('quantidade', type=int, default=0)
        preco     = request.form.get('preco', type=float, default=0.0)

        if not all([nome, categoria]) or categoria not in ['bolsas', 'sapatos', 'cintos']:
            flash('Preencha todos os campos corretamente. Categoria deve ser bolsas, sapatos ou cintos.', 'erro')
            return redirect(url_for('novo_produto'))

        p = Produto(nome=nome, categoria=categoria, quantidade=quantidade, preco=preco)
        db.session.add(p)
        db.session.commit()
        flash(f'Produto {nome} adicionado ao estoque!', 'sucesso')
        return redirect(url_for('listar_produtos'))

    return render_template('novo_produto.html')


@app.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def editar_produto(id):
    p = db.get_or_404(Produto, id)

    if request.method == 'POST':
        p.nome      = request.form.get('nome', p.nome).strip()
        p.categoria = request.form.get('categoria', p.categoria).strip()
        p.quantidade = request.form.get('quantidade', type=int, default=p.quantidade)
        p.preco     = request.form.get('preco', type=float, default=p.preco)

        if p.categoria not in ['bolsas', 'sapatos', 'cintos']:
            flash('Categoria inválida.', 'erro')
            return redirect(url_for('editar_produto', id=id))

        db.session.commit()
        flash('Produto atualizado!', 'sucesso')
        return redirect(url_for('listar_produtos'))

    return render_template('editar_produto.html', p=p)


@app.route('/produtos/<int:id>/excluir', methods=['POST'])
@login_obrigatorio
@cargo_obrigatorio('Administrador')
def excluir_produto(id):
    p = db.get_or_404(Produto, id)
    db.session.delete(p)
    db.session.commit()
    flash('Produto removido do estoque.', 'info')
    return redirect(url_for('listar_produtos'))


# =============================================================
# RELATÓRIOS
# =============================================================

@app.route('/relatorio/clientes-atendidos', methods=['GET', 'POST'])
@login_obrigatorio
@cargo_obrigatorio('Atendente', 'Administrador')
def relatorio_clientes_atendidos():
    """
    Relatório de clientes atendidos.

    Exibe três seções:
    1. Filtro por mês/ano  → atendimentos concluídos no período selecionado
    2. Histórico mensal    → resumo dos últimos 12 meses (quantos clientes/mês)
    3. NOVO: Histórico por cliente → todos os clientes que já tiveram atendimento
                                     concluído em qualquer data (linha do tempo)
    """

    # ------------------------------------------------------------------
    # PARÂMETROS DE FILTRO
    # O usuário pode passar ?mes=3&ano=2025 na URL (via formulário GET).
    # Se não passar nada, usa o mês e ano atuais como padrão.
    # ------------------------------------------------------------------
    hoje = datetime.now(timezone.utc)

    ano = request.args.get('ano', default=hoje.year,  type=int)
    mes = request.args.get('mes', default=hoje.month, type=int)

    # Garante que mês e ano estejam dentro de faixas válidas
    if mes < 1 or mes > 12:
        mes = hoje.month
    if ano < 2020 or ano > hoje.year + 1:
        ano = hoje.year

    # ------------------------------------------------------------------
    # QUERY 1 — CLIENTES DO PERÍODO SELECIONADO
    #
    # Busca todos os clientes que tiveram ao menos um atendimento com
    # status 'Concluido' dentro do mês/ano escolhido no filtro.
    #
    # GROUP BY cliente_id agrupa várias linhas do mesmo cliente em uma só,
    # permitindo calcular: quantos atendimentos teve (COUNT), quando foi
    # o primeiro (MIN) e o último (MAX).
    # ------------------------------------------------------------------
    inicio_periodo = datetime(ano, 1, 1)
    ultimo_dia     = calendar.monthrange(ano, mes)[1]
    fim_periodo    = datetime(ano, mes, ultimo_dia, 23, 59, 59)

    atendimentos_mes = db.session.query(
        Atendimento.cliente_id,
        Usuario.nome,
        Usuario.email,
        func.count(Atendimento.id).label('qtd_atendimentos'),
        func.min(Atendimento.data_criacao).label('primeiro_atendimento'),
        func.max(Atendimento.data_criacao).label('ultimo_atendimento')
    ).join(
        Usuario, Atendimento.cliente_id == Usuario.id
    ).filter(
        Atendimento.data_criacao >= inicio_periodo,
        Atendimento.data_criacao <= fim_periodo,
        Atendimento.status == 'Concluido'
    ).group_by(
        Atendimento.cliente_id, Usuario.nome, Usuario.email
    ).order_by(
        func.count(Atendimento.id).desc()
    ).all()

    # ------------------------------------------------------------------
    # QUERY 2 — HISTÓRICO MENSAL (últimos 12 meses)
    #
    # Agrupa os atendimentos concluídos por mês/ano para mostrar a
    # evolução ao longo do tempo na barra de histórico.
    # extract('year'/'month') puxa apenas o componente de data desejado.
    # ------------------------------------------------------------------
    historico_mensal = db.session.query(
        extract('year',  Atendimento.data_criacao).label('ano'),
        extract('month', Atendimento.data_criacao).label('mes'),
        func.count(func.distinct(Atendimento.cliente_id)).label('clientes_unicos'),
        func.count(Atendimento.id).label('total_atendimentos')
    ).filter(
        Atendimento.status == 'Concluido',
        Atendimento.data_criacao >= (hoje - timedelta(days=365))
    ).group_by(
        extract('year',  Atendimento.data_criacao),
        extract('month', Atendimento.data_criacao)
    ).order_by(
        extract('year',  Atendimento.data_criacao).desc(),
        extract('month', Atendimento.data_criacao).desc()
    ).all()

    # ------------------------------------------------------------------
    # QUERY 3 — HISTÓRICO COMPLETO POR CLIENTE  ← NOVIDADE
    #
    # Lista TODOS os clientes que já tiveram pelo menos um atendimento
    # com status 'Concluido', independente da data.
    #
    # Diferença em relação à Query 1:
    #   • Query 1 filtra por período (mês/ano selecionado)
    #   • Query 3 não tem filtro de data → mostra o histórico completo
    #
    # Para cada cliente calcula:
    #   • qtd_atendimentos  → total de atendimentos já concluídos
    #   • primeiro_atendimento → data do primeiro (mais antigo)
    #   • ultimo_atendimento   → data do mais recente
    #
    # ORDER BY ultimo_atendimento DESC coloca quem foi atendido mais
    # recentemente no topo da lista.
    # ------------------------------------------------------------------
    historico_clientes = db.session.query(
        Atendimento.cliente_id,
        Usuario.nome,
        Usuario.email,
        func.count(Atendimento.id).label('qtd_atendimentos'),
        func.min(Atendimento.data_criacao).label('primeiro_atendimento'),
        func.max(Atendimento.data_criacao).label('ultimo_atendimento')
    ).join(
        Usuario, Atendimento.cliente_id == Usuario.id
    ).filter(
        Atendimento.status == 'Concluido'       # ← sem filtro de data: pega tudo
    ).group_by(
        Atendimento.cliente_id, Usuario.nome, Usuario.email
    ).order_by(
        func.max(Atendimento.data_criacao).desc()   # mais recente primeiro
    ).all()

    # ------------------------------------------------------------------
    # QUERY 4 — LINHA DO TEMPO POR CLIENTE  ← NOVIDADE
    #
    # Para cada cliente do histórico, busca TODOS os seus atendimentos
    # individuais concluídos (sem agrupar), para exibir a linha do tempo
    # detalhada quando o usuário expandir um cliente.
    #
    # Retorna um dicionário: { cliente_id: [lista de atendimentos] }
    # O template usa: timeline[item.cliente_id]
    # ------------------------------------------------------------------
    todos_concluidos = db.session.query(
        Atendimento.cliente_id,
        Atendimento.id,
        Atendimento.descricao,
        Atendimento.data_criacao,
        Atendimento.data_atualizacao,
        Usuario.nome.label('atendente_nome')        # nome do atendente responsável
    ).join(
        Usuario, Atendimento.atendente_id == Usuario.id,
        isouter=True    # LEFT JOIN: inclui atendimentos sem atendente atribuído
    ).filter(
        Atendimento.status == 'Concluido'
    ).order_by(
        Atendimento.cliente_id,
        Atendimento.data_criacao.desc()     # mais recente primeiro dentro de cada cliente
    ).all()

    # Agrupa os registros individuais por cliente_id num dicionário
    # { 1: [atend_A, atend_B], 2: [atend_C], ... }
    timeline = {}
    for row in todos_concluidos:
        if row.cliente_id not in timeline:
            timeline[row.cliente_id] = []
        timeline[row.cliente_id].append(row)

    # ------------------------------------------------------------------
    # MAPA DE NOMES DOS MESES
    # Dicionário usado tanto para formatar datas no template quanto
    # para popular o <select> de filtro de mês.
    # ------------------------------------------------------------------
    meses_nomes = {
        1: 'Janeiro',  2: 'Fevereiro', 3: 'Março',    4: 'Abril',
        5: 'Maio',     6: 'Junho',     7: 'Julho',     8: 'Agosto',
        9: 'Setembro', 10: 'Outubro',  11: 'Novembro', 12: 'Dezembro'
    }

    # Formata o histórico mensal adicionando o nome do mês como string
    historico_formatado = []
    for item in historico_mensal:
        historico_formatado.append({
            'ano':                int(item[0]),
            'mes':                int(item[1]),
            'mes_nome':           meses_nomes[int(item[1])],
            'clientes_unicos':    item[2],
            'total_atendimentos': item[3]
        })

    # Totalizadores do período filtrado (para os cards de resumo)
    total_clientes      = len(atendimentos_mes)
    total_atendimentos  = sum(a[3] for a in atendimentos_mes)

    # Total geral do histórico completo (independente do filtro)
    total_historico_clientes     = len(historico_clientes)
    total_historico_atendimentos = sum(a[3] for a in historico_clientes)

    return render_template('relatorio_clientes_mes.html',
        # Filtro de período
        ano                          = ano,
        mes                          = mes,
        mes_nome                     = meses_nomes[mes],
        meses_nomes                  = meses_nomes,
        now                          = hoje,
        # Seção 1: clientes do período selecionado
        atendimentos                 = atendimentos_mes,
        total_clientes               = total_clientes,
        total_atendimentos           = total_atendimentos,
        # Seção 2: histórico mensal (últimos 12 meses)
        historico                    = historico_formatado,
        # Seção 3: histórico completo por cliente  ← NOVO
        historico_clientes           = historico_clientes,
        total_historico_clientes     = total_historico_clientes,
        total_historico_atendimentos = total_historico_atendimentos,
        # Seção 4: linha do tempo detalhada por cliente  ← NOVO
        timeline                     = timeline,
    )


# =============================================================
# DADOS DE EXEMPLO
# =============================================================

def seed():
    """Cria dados iniciais de demonstração."""
    if Usuario.query.count() > 0:
        return

    admin  = Usuario(nome='Ana Proprietária', email='admin@loja.com',  cargo='Administrador')
    atend  = Usuario(nome='Juliana Atendente', email='juliana@loja.com', cargo='Atendente')
    cli1   = Usuario(nome='Beatriz Santos',   email='beatriz@email.com', cargo='Cliente')
    cli2   = Usuario(nome='Camila Oliveira',  email='camila@email.com',  cargo='Cliente')

    for u, s in [(admin,'admin123'),(atend,'atend123'),(cli1,'cli123'),(cli2,'cli123')]:
        u.set_senha(s)

    db.session.add_all([admin, atend, cli1, cli2])
    db.session.flush()

    db.session.add_all([
        Atendimento(cliente_id=cli1.id, atendente_id=atend.id,
            descricao='Quero trocar blusa M por G, comprei há 3 dias.',
            status='Em Andamento'),
        Atendimento(cliente_id=cli1.id,
            descricao='Vestido floral veio com costura soltando.',
            status='Aberto'),
        Atendimento(cliente_id=cli2.id, atendente_id=atend.id,
            descricao='Casaco bege disponível no tamanho P?',
            status='Concluido'),
        Atendimento(cliente_id=cli2.id,
            descricao='Pedido #4521 ainda não chegou.',
            status='Aberto'),
    ])

    # Produtos de exemplo
    db.session.add_all([
        Produto(nome='Bolsa de Couro Preta', categoria='bolsas', quantidade=15, preco=299.99),
        Produto(nome='Bolsa Tote Marrom', categoria='bolsas', quantidade=8, preco=199.99),
        Produto(nome='Sapato Social Preto', categoria='sapatos', quantidade=20, preco=399.99),
        Produto(nome='Sandália Conforto', categoria='sapatos', quantidade=12, preco=149.99),
        Produto(nome='Cinto Couro Marrom', categoria='cintos', quantidade=25, preco=89.99),
        Produto(nome='Cinto Casual Preto', categoria='cintos', quantidade=18, preco=79.99),
    ])

    db.session.commit()
    print('✅ Dados de exemplo criados!')


# =============================================================
# INICIALIZAÇÃO DO BANCO (Compatível com Vercel/Serverless)
# =============================================================
with app.app_context():
    db.create_all()
    seed()

if __name__ == '__main__':
    app.run(debug=True, port=5000)==================================
try:
    with app.app_context():
        db.create_all()
        seed()
except Exception as e:
    print(f"Erro ao inicializar banco de dados: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)