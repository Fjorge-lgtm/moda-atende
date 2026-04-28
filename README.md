# ModaAtende 👗
### Sistema de Gerenciamento de Atendimento — Loja de Roupas

---

## ⚡ Execução em 3 passos

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar o servidor
python app.py

# 3. Abrir no navegador
# http://localhost:5000
```

---

## 🔐 Credenciais de acesso (geradas automaticamente)

| Cargo         | E-mail                | Senha     |
|---------------|-----------------------|-----------|
| Administrador | admin@loja.com        | admin123  |
| Atendente     | juliana@loja.com      | atend123  |
| Cliente       | beatriz@email.com     | cli123    |
| Cliente       | camila@email.com      | cli123    |

---

## 📁 Estrutura do projeto

```
loja_roupas/
│
├── app.py                        ← Backend Flask (rotas, modelos, lógica)
├── requirements.txt              ← Dependências Python
│
├── static/
│   ├── css/
│   │   └── style.css            ← Todos os estilos (variáveis, layout, componentes)
│   └── js/
│       └── main.js              ← Dark mode, sidebar, validações, contadores
│
└── templates/
    ├── base.html                 ← Layout base com sidebar, topbar e flash messages
    ├── login.html                ← Tela de login
    ├── dashboard_admin.html      ← Painel do administrador
    ├── dashboard_atendente.html  ← Painel do atendente
    ├── dashboard_cliente.html    ← Painel do cliente
    ├── novo_atendimento.html     ← Formulário de abertura de ticket
    ├── editar_atendimento.html   ← Edição de ticket (atendente/admin)
    ├── usuarios.html             ← Listagem de usuários (admin)
    ├── novo_usuario.html         ← Criação de usuário (admin)
    ├── editar_usuario.html       ← Edição de usuário (admin)
    ├── produtos.html             ← Controle de estoque (atendente/admin)
    ├── novo_produto.html         ← Adição de produto ao estoque
    └── editar_produto.html       ← Edição de produto
```

---

## 👥 Permissões por cargo

### 👑 Administrador
- Acessa painel com estatísticas gerais e gráfico de distribuição
- Cria, edita e exclui **todos os usuários**
- Cria, edita e exclui **todos os atendimentos**
- Gerencia controle de estoque (bolsas, sapatos, cintos)
- Acessa todos os dashboards

### 🎧 Atendente
- Vê tickets abertos sem responsável e pode **assumir**
- Edita status e responsável dos seus tickets
- Gerencia controle de estoque (bolsas, sapatos, cintos)
- Não acessa painel administrativo nem gestão de usuários

### 🛍️ Cliente
- Abre novos atendimentos com seletor de tipo
- Acompanha status dos **seus próprios** atendimentos
- Vê quem é o atendente responsável

---

## 📦 Controle de Estoque

O sistema inclui controle completo de estoque para três categorias principais:
- **Bolsas** 👜
- **Sapatos** 👠  
- **Cintos** 🪢

### Funcionalidades:
- Cadastro de produtos com nome, categoria, quantidade e preço
- Edição de informações dos produtos
- Exclusão de produtos (apenas administradores)
- Visualização organizada por categoria
- Controle de acesso por cargo

---

## 🎨 Design

- **Paleta:** Rosa pó, bege marfim, branco — tema moda feminina elegante
- **Fontes:** Playfair Display (títulos) + Lato (corpo)
- **Dark Mode:** toggle persistente via `localStorage`
- **Responsivo:** sidebar retrátil com overlay no mobile
- **Animações:** entrada suave com atraso escalonado por elemento

---

## 🛡️ Segurança

- Senhas com hash PBKDF2 via Werkzeug
- Controle de acesso por decoradores Python (RBAC)
- Proteção de sessão com `SECRET_KEY`
- Validação dupla: JavaScript (UX rápida) + Python (segurança real)

---

## 🐳 Executar com Docker

```bash
# Criar Dockerfile na raiz do projeto:
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .
# EXPOSE 5000
# CMD ["python", "app.py"]

docker build -t moda-atende .
docker run -d --name moda -p 5000:5000 -v moda_data:/app/instance moda-atende
```

---

## 📦 Dependências

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.1
Werkzeug>=3.0.0
```

> O banco `instance/loja_roupas.db` é criado automaticamente na primeira execução.

## 🐳 Executar com Docker

```bash
# Criar Dockerfile na raiz do projeto:
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .
# EXPOSE 5000
# CMD ["python", "app.py"]

docker build -t moda-atende .
docker run -d --name moda -p 5000:5000 -v moda_data:/app/instance moda-atende
```

---

## 📦 Dependências

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.1
Werkzeug>=3.0.0
```

> O banco `instance/loja_roupas.db` é criado automaticamente na primeira execução.
