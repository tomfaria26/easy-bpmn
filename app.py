import streamlit as st
import requests
import os
from dotenv import load_dotenv
import base64
import json
import unicodedata
import re

# Configuração da página
st.set_page_config(
    page_title="Acompanhamento de Tarefas",
    page_icon="📋",
    layout="wide"
)

# --- Variável para Filtrar Processos por Nome ---
# Altere o valor abaixo para o nome exato do processo que você deseja filtrar.
# Deixe como None para carregar todos os processos.
PROCESS_NAME_TO_FILTER = "Auditoria BIM"


# --- Funções Utilitárias ---
def format_date(date_string, include_time=True):
    """Formata uma string de data ISO para o fuso horário de São Paulo."""
    if not date_string: return 'Data não disponível'
    try:
        from datetime import datetime, timedelta
        dt_utc = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        sao_paulo_offset = timedelta(hours=-3)
        dt_sao_paulo = dt_utc + sao_paulo_offset
        if include_time:
            return dt_sao_paulo.strftime('%d/%m/%Y - %H:%M')
        else:
            return dt_sao_paulo.strftime('%d/%m/%Y')
    except Exception:
        return date_string

def load_file_content(file_name):
    """Carrega o conteúdo de um arquivo de texto."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        if "bpmn_container.html" not in file_name:
            st.error(f"Erro: Ficheiro '{file_name}' não encontrado.")
        return ""

def normalize_string(s: str) -> str:
    """Normaliza uma string, removendo acentos e convertendo para minúsculas."""
    if not isinstance(s, str): return ""
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower().strip()

# --- Funções de Busca de Dados ---
def fetch_data(url, method='GET', payload=None):
    """Busca dados de uma API, suportando GET e POST."""
    headers = {'api_token': API_TOKEN}
    try:
        if method.upper() == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, json=payload)
        else:
            response = requests.get(url, headers=headers)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if 'tasks' not in url:
            st.error(f"Erro ao buscar dados de {url} com método {method}: {e}")
        return None

def fetch_bpmn_xml(process_id):
    """Função específica para buscar o XML BPMN de um processo."""
    return fetch_data(f"https://app-api.holmesdoc.io/v1/admin/processes/{process_id}/troubleshooting/template")

@st.cache_data(ttl=600)
def fetch_instances_for_dropdown():
    """Busca e processa os dados para o dropdown de criação de processo."""
    instance_data_url = "https://app-api.holmesdoc.io/v1/entities/68597a8e0b52b4fa33e34995/instances/search"
    search_payload = {
        "query": {
            "from": 0,
            "size": 200,
            "order": "asc",
            "groups": [
                {
                    "match_all": True,
                    "terms": [
                        {
                            "field": "entity_id",
                            "type": "is",
                            "value": "68597a8e0b52b4fa33e34995"
                        }
                    ]
                }
            ],
            "sort": "8547a640-504b-11f0-a2c8-75d9e0938171"
        }
    }
    data = fetch_data(instance_data_url, method='POST', payload=search_payload)
    
    if data and 'docs' in data:
        instance_map = {}
        for doc in data['docs']:
            if doc.get('props') and len(doc['props']) > 0 and 'value' in doc['props'][0]:
                display_name = doc['props'][0]['value']
                instance_id = doc.get('instance_id')
                if display_name and instance_id:
                    instance_map[display_name] = instance_id
        return instance_map
    return {}


# --- Início da Aplicação ---
st.markdown(f"<style>{load_file_content('styles.css')}</style>", unsafe_allow_html=True)
st.title('📋 Acompanhamento de Tarefas - Auditoria BIM')

# Inicializa o estado da sessão para a mensagem de sucesso
if 'creation_success_message' not in st.session_state:
    st.session_state.creation_success_message = None

# Exibe a mensagem de sucesso se ela existir
if st.session_state.creation_success_message:
    st.success(st.session_state.creation_success_message)
    st.session_state.creation_success_message = None # Limpa a mensagem após exibição

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
API_URL = 'https://app-api.holmesdoc.io/v1/processes/'
WORKFLOW_START_URL = "https://app-api.holmesdoc.io/v1/workflows/684b215594374c145b750317/start"

if not API_TOKEN:
    st.error('⚠️ API_TOKEN não encontrado no .env!'); st.stop()


# --- Interface do Usuário (Controles) ---
with st.container():
    # CORREÇÃO: Ajusta as colunas para incluir o botão de atualizar ao lado do filtro
    filter_col, refresh_col, create_col = st.columns([10, 2, 4])
    
    with filter_col:
        processes_data = fetch_data(API_URL)
        if not processes_data:
            st.info("Nenhuma tarefa encontrada ou falha ao carregar os dados.")
            st.stop()
        
        processes = processes_data.get('processes', processes_data) if isinstance(processes_data, dict) else []
        
        if PROCESS_NAME_TO_FILTER:
            processes = [p for p in processes if p.get('name') == PROCESS_NAME_TO_FILTER]
        
        processes = [p for p in processes if p.get('status') != 'canceled']
        
        all_identifiers = sorted(list(set(p['identifier'] for p in processes)))
        filter_options = ["Todos os processos"] + all_identifiers
        selected_process = st.selectbox("🔍 Filtrar por processo:", options=filter_options)

    with refresh_col:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄"):
            st.rerun()

    with create_col:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        with st.popover("➕ Criar Novo Processo"):
            instance_map = fetch_instances_for_dropdown()
            with st.form("new_process_form_popover"):
                st.write("Preencha os dados para iniciar um novo processo.")
                
                prop_value_1 = st.text_input("Disciplina (ex: HID, ARQ)")
                prop_value_2 = st.text_input("Etapa (ex: PB, EP)")
                
                selected_instance_name = st.selectbox(
                    "Selecione a Instância",
                    options=[""] + list(instance_map.keys()),
                    index=0,
                    help="Selecione o item para vincular ao novo processo."
                )
                
                submitted = st.form_submit_button("Iniciar Processo")

                if submitted:
                    # CORREÇÃO: Valida se todos os campos estão preenchidos
                    if not all([prop_value_1, prop_value_2, selected_instance_name]):
                        st.error("Todos os campos são obrigatórios. Por favor, preencha tudo.")
                    else:
                        selected_instance_id = instance_map[selected_instance_name]
                        start_payload = {
                            "workflow": {
                                "start_event": "StartEvent_1",
                                "property_values": [
                                    {"id": "f59f23f0-4aec-11f0-83f5-4dfed4731510", "value": prop_value_1},
                                    {"id": "f1f6dc70-4aec-11f0-83f5-4dfed4731510", "value": prop_value_2}
                                ],
                                "instance_id": selected_instance_id, "whats": "", "documents": [],
                                "test": False, "run_automations": True, "run_triggers": True
                            }
                        }
                        
                        response = fetch_data(WORKFLOW_START_URL, method='POST', payload=start_payload)
                        if response and response.get('id'):
                            st.session_state.creation_success_message = f"Processo iniciado com sucesso! ID: {response.get('id')}"
                            st.rerun()
                        else:
                            st.error("Falha ao iniciar o processo.")


# --- Lógica de Processamento de Tarefas ---
process_id_map = {}
all_tasks = {}  # Dicionário central para todas as tarefas, chave=task_id

history_payload = {
    "filters": [], "page": 1, "per_page": 100,
    "sortBy": ["created_at", "asc"]
}

# Processamento de dados
for process in processes:
    process_id = process.get('id')
    process_identifier = process.get('identifier')
    if not process_id or not process_identifier: continue
    
    process_id_map[process_identifier] = process_id
    history_response = fetch_data(f"https://app-api.holmesdoc.io/v1/processes/{process_id}/history", method='POST', payload=history_payload)
    if not history_response: continue
    
    for hist in history_response.get('histories', []):
        props = hist.get('properties', {})
        task_id = props.get('task_id')
        if task_id and props.get('long_link'):
            if task_id not in all_tasks:
                all_tasks[task_id] = {
                    'process_id': process_id, 'process_identifier': process_identifier,
                    'task_name': props.get('task_name'), 'long_link': props.get('long_link'),
                    'task_id': task_id, 'created_at': hist.get('created_at', ''),
                }

for process in processes:
    process_id = process.get('id')
    if not process_id: continue
    history_response = fetch_data(f"https://app-api.holmesdoc.io/v1/processes/{process_id}/history", method='POST', payload=history_payload)
    if not history_response: continue

    for hist in history_response.get('histories', []):
        if hist.get('key') == 'history.take_action':
            props = hist.get('properties', {})
            task_id = props.get('task_id')
            if task_id in all_tasks:
                completion_date = hist.get('created_at')
                current_completion = all_tasks[task_id].get('completion_date')
                if not current_completion or completion_date > current_completion:
                    all_tasks[task_id]['is_completed'] = True
                    all_tasks[task_id]['completion_date'] = completion_date

for task_id, task_details in all_tasks.items():
    if not task_details.get('is_completed'):
        task_api_data = fetch_data(f"https://app-api.holmesdoc.io/v1/tasks/{task_id}")
        if task_api_data and task_api_data.get('due_date'):
            task_details['due_date'] = task_api_data.get('due_date')


all_tasks_list_final = sorted(list(all_tasks.values()), key=lambda x: x['created_at'], reverse=True)
pending_tasks = [task for task in all_tasks_list_final if not task.get('is_completed')]
completed_tasks = [task for task in all_tasks_list_final if task.get('is_completed')]

display_pending = [t for t in pending_tasks if selected_process == "Todos os processos" or t['process_identifier'] == selected_process]
display_completed = [t for t in completed_tasks if selected_process == "Todos os processos" or t['process_identifier'] == selected_process]


# --- Exibição dos Cards Kanban ---
col_pending, col_completed = st.columns(2)
with col_pending:
    st.markdown(f'<div class="kanban-header kanban-header-pending">⏳ PENDENTE ({len(display_pending)})</div>', unsafe_allow_html=True)
    for task in display_pending:
        creation_date_formatted = format_date(task.get('created_at', ''))
        due_date_formatted = format_date(task.get('due_date'), include_time=False)
        caption_parts = [f"📁 {task['process_identifier']}", f"📅 {creation_date_formatted}"]
        if task.get('due_date'):
            caption_parts.append(f"🎯 {due_date_formatted}")
        card_caption = " | ".join(caption_parts)
        card_html = f"""
        <a href="{task['long_link']}" target="_blank" class="card-link-wrapper">
            <div class="custom-card pending-card">
                <div class="card-title">{task['task_name']}</div>
                <div class="card-caption">{card_caption}</div>
            </div>
        </a>
        """
        st.markdown(card_html, unsafe_allow_html=True)

with col_completed:
    st.markdown(f'<div class="kanban-header kanban-header-completed">✅ CONCLUÍDA ({len(display_completed)})</div>', unsafe_allow_html=True)
    for task in display_completed:
        creation_date_formatted = format_date(task.get('created_at', ''))
        completion_date_formatted = format_date(task.get('completion_date', ''))
        caption_parts = [
            f"📁 {task['process_identifier']}",
            f"📅 {creation_date_formatted}",
            f"✅ {completion_date_formatted}"
        ]
        card_caption = " | ".join(caption_parts)
        card_html = f"""
        <div class="custom-card completed-card">
            <div class="card-title">{task['task_name']}</div>
            <div class="card-caption">{card_caption}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


# --- Métricas e Diagrama ---
st.markdown("---")
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1: st.metric("📊 Total de Tarefas", len(all_tasks_list_final))
with m_col2: st.metric("⏳ Pendentes", len(display_pending))
with m_col3: st.metric("✅ Concluídas", len(display_completed))

js_data, bpmn_container_html = {}, ""
if selected_process != "Todos os processos":
    st.markdown("---")
    st.markdown(f"### 🔄 Diagrama BPMN para: **{selected_process}**")
    selected_process_id = process_id_map.get(selected_process)
    if selected_process_id:
        xml_data = fetch_bpmn_xml(selected_process_id)
        if xml_data and xml_data.get('xml'):
            xml_content = xml_data.get('xml')
            xml_b64 = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
            js_data = {"xmlB64": xml_b64, "completedTasks": [t['task_name'] for t in display_completed], "pendingTasks": [t['task_name'] for t in display_pending]}
            bpmn_container_html = load_file_content('bpmn_container.html')
        else:
            st.warning(f"⚠️ Não foi possível carregar o diagrama BPMN para o processo **{selected_process}**.")
else:
    st.info("🔍 **Selecione um processo específico** no filtro acima para visualizar seu diagrama BPMN.")

main_js = load_file_content('main.js')

if bpmn_container_html and main_js:
    js_data_script = f'<script>window.bpmnData = {json.dumps(js_data)};</script>'
    final_html = f"""
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Componente BPMN</title>
    <style>{load_file_content('styles.css')}</style>
    <script src="https://unpkg.com/bpmn-js@17.0.2/dist/bpmn-navigated-viewer.production.min.js"></script></head>
    <body>{bpmn_container_html}{js_data_script}<script>{main_js}</script></body></html>"""
    st.components.v1.html(final_html, height=510)
