
# 📋 Acompanhamento de Tarefas - Auditoria BIM

Aplicação web desenvolvida em **Streamlit** para acompanhamento visual de tarefas de auditoria de modelos BIM. A solução permite visualizar o andamento dos processos, tarefas pendentes, concluídas e também exibe dinamicamente o diagrama BPMN do processo com destaque visual para cada etapa.

---

## 🚀 Funcionalidades

- ✅ Dashboard Kanban com tarefas **pendentes** e **concluídas**.
- 🔍 Filtro por processo específico.
- 📄 Visualização interativa do **diagrama BPMN**, com:
  - 🟢 Tarefas concluídas (verde).
  - 🟡 Tarefas pendentes (amarelo).
- 🔗 Acesso direto aos links das tarefas.
- 🎨 Interface personalizada com CSS.

---

## 🛠️ Tecnologias e Bibliotecas

- [Streamlit](https://streamlit.io/)
- [Requests](https://requests.readthedocs.io/en/latest/)
- [Python Dotenv](https://pypi.org/project/python-dotenv/)
- [bpmn-js](https://bpmn.io/toolkit/bpmn-js/) (via embed HTML/JS)
- HTML + CSS personalizado

---

## 📁 Estrutura de Arquivos

```
📦 Projeto
├── app.py                # Código principal da aplicação Streamlit
├── requirements.txt      # Dependências do projeto
├── .env                  # Variáveis de ambiente (não subir no GitHub)
├── styles.css            # Estilo visual da interface
├── run.sh                # Script de execução local (opcional)
├── AuditoriaBIMProcesso.xml # Modelo BPMN de exemplo
├── Dockerfile            # Arquivo para deploy na Vercel
├── vercel.json           # Configuração de build da Vercel
└── README.md             # Este documento
```

---

## 🔧 Como Rodar Localmente

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate   # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` na raiz com sua chave de API:

```env
API_TOKEN=seu_token_aqui
```

5. Execute o aplicativo:

```bash
streamlit run app.py
```

---

## 🚀 Deploy na Vercel

### ✅ Pré-requisitos:

- Conta na [Vercel](https://vercel.com)
- Conta no GitHub

### ⚙️ Passos:

1. Suba seu projeto no GitHub (certifique-se de que `.env` está no `.gitignore`).
2. Acesse o painel da Vercel e clique em **"New Project"**.
3. Conecte seu repositório.
4. A Vercel detectará o `vercel.json` e construirá usando o `Dockerfile`.
5. Configure suas variáveis de ambiente no painel da Vercel em:

```
Settings → Environment Variables
```

Adicione:

| KEY        | VALUE            |
| -----------|------------------|
| API_TOKEN  | seu_token_api    |

6. Clique em **Deploy**. A aplicação ficará disponível em:

```
https://seu-projeto.vercel.app
```

---

## 🛑 Observações Importantes

- 🔒 **NUNCA suba seu arquivo `.env` em repositórios públicos.**
- 🚫 A Vercel não é otimizada para aplicações Python em alta escala. Para produção, recomenda-se usar serviços como **Streamlit Cloud**, **Render**, **Railway**, ou **Fly.io**.

---

## 💡 Melhorias Futuras

- ✅ Autenticação de usuários.
- 📊 Dashboard com métricas e KPIs.
- 🗃️ Histórico e relatórios exportáveis.
- 🔔 Notificações e alertas automáticos.

---

## 👨‍💻 Desenvolvido por

**GPL Incorporadora - BIM**
