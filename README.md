
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
├── styles.css            # Estilo visual da interface
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

## 🛑 Observações Importantes

- 🔒 **NUNCA suba seu arquivo `.env` em repositórios públicos.**

---

## 💡 Melhorias Futuras

- ✅ Autenticação de usuários.
- 📊 Dashboard com métricas e KPIs.
- 🗃️ Histórico e relatórios exportáveis.
- 🔔 Notificações e alertas automáticos.

---

## 👨‍💻 Desenvolvido por

**GPL Incorporadora - BIM**
