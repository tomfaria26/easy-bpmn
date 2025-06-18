import streamlit as st
import requests
import os
from dotenv import load_dotenv
import base64
import json
import unicodedata

# Configuração da página
st.set_page_config(
    page_title="Acompanhamento de Tarefas",
    page_icon="📋",
    layout="wide"
)

# --- Funções Utilitárias ---
def format_date(date_string):
    if not date_string: return 'Data não disponível'
    try:
        from datetime import datetime, timedelta
        dt_utc = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        sao_paulo_offset = timedelta(hours=-3)
        dt_sao_paulo = dt_utc + sao_paulo_offset
        return dt_sao_paulo.strftime('%d/%m/%Y - %H:%M')
    except Exception: return date_string

def load_file_content(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError:
        if "bpmn_container.html" not in file_name:
            st.error(f"Erro: Ficheiro '{file_name}' não encontrado.")
        return ""

def normalize_string(s: str) -> str:
    if not isinstance(s, str): return ""
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower().strip()

# --- Funções de Busca de Dados ---
@st.cache_data(ttl=300)
def fetch_data(url):
    headers = {'api_token': API_TOKEN}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return json.loads(response.content.decode('utf-8'))
    except Exception as e:
        st.error(f"Erro ao buscar dados de {url}: {e}")
        return None

def fetch_bpmn_xml(process_id):
    """Função específica para buscar o XML BPMN."""
    return fetch_data(f"https://app-api.holmesdoc.io/v1/admin/processes/{process_id}/troubleshooting/template")


# --- Início da Aplicação ---
st.markdown(f"<style>{load_file_content('styles.css')}</style>", unsafe_allow_html=True)
st.title('📋 Acompanhamento de Tarefas - Auditoria BIM')

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
API_URL = 'https://app-api.holmesdoc.io/v1/processes/'

if not API_TOKEN: st.error('⚠️ API_TOKEN não encontrado no .env!'); st.stop()

processes_data = fetch_data(API_URL)
if not processes_data: st.info("Nenhuma tarefa encontrada ou falha ao carregar os dados."); st.stop()

processes = processes_data.get('processes', processes_data) if isinstance(processes_data, dict) else processes_data
processes = [p for p in processes if p.get('status') != 'canceled']

# --- Lógica de Processamento de Tarefas ---
process_id_map, all_tasks, unique_tasks = {}, [], {}
for process in processes:
    process_id = process.get('id')
    if not process_id: continue
    process_id_map[process.get('identifier')] = process_id
    history_data = fetch_data(f"https://app-api.holmesdoc.io/v1/processes/{process_id}/history")
    if not history_data: continue
    histories = history_data.get('histories', [])
    completed_fragments = {msg.split('tarefa')[1].strip().strip("'\"") for hist in histories if (msg := hist.get('message', '')) and 'tomou a ação' in msg.lower() and 'na tarefa' in msg.lower()}
    for hist in histories:
        props, task_name = hist.get('properties', {}), hist.get('properties', {}).get('task_name')
        if task_name and props.get('long_link'):
            task_key = f"{process.get('identifier')}-{task_name}"
            if task_key not in unique_tasks:
                task_details = {'process_id': process_id, 'process_identifier': process.get('identifier'), 'task_name': task_name, 'long_link': props.get('long_link'), 'created_at': hist.get('created_at', '')}
                task_name_norm = normalize_string(task_name)
                task_details['is_completed'] = any(task_name_norm in normalize_string(frag) for frag in completed_fragments)
                unique_tasks[task_key] = task_details
all_tasks = sorted(list(unique_tasks.values()), key=lambda x: x['created_at'], reverse=True)
pending_tasks = [task for task in all_tasks if not task['is_completed']]
completed_tasks = [task for task in all_tasks if task['is_completed']]

# --- Interface do Usuário ---
col1, col2 = st.columns([4, 1])
with col1:
    filter_options = ["Todos os processos"] + sorted(list(set(t['process_identifier'] for t in all_tasks)))
    selected_process = st.selectbox("🔍 Filtrar por processo:", options=filter_options)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar"): st.rerun()

if selected_process != "Todos os processos":
    pending_tasks = [t for t in pending_tasks if t['process_identifier'] == selected_process]
    completed_tasks = [t for t in completed_tasks if t['process_identifier'] == selected_process]

col_pending, col_completed = st.columns(2)
with col_pending:
    st.markdown(f'<div class="kanban-header kanban-header-pending">⏳ PENDENTE ({len(pending_tasks)})</div>', unsafe_allow_html=True)
    for task in pending_tasks:
        # Usa um container para criar a aparência de um card
        with st.container(border=True):
            # O popover funciona como o título clicável
            with st.popover(task['task_name']):
                st.markdown(f"#### Ação da Tarefa")
                st.components.v1.iframe(task['long_link'], height=600, scrolling=True)
            
            # Os metadados são adicionados abaixo, dentro do mesmo card
            st.caption(f"📁 {task['process_identifier']} | 📅 {format_date(task['created_at'])}")

with col_completed:
    st.markdown(f'<div class="kanban-header kanban-header-completed">✅ CONCLUÍDA ({len(completed_tasks)})</div>', unsafe_allow_html=True)
    for task in completed_tasks:
        with st.container(border=True):
             st.markdown(f"**{task['task_name']}**")
             st.caption(f"📁 {task['process_identifier']} | 📅 {format_date(task['created_at'])}")


# --- Métricas e Diagrama ---
st.markdown("---")
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1: st.metric("📊 Total de Tarefas", len(all_tasks))
with m_col2: st.metric("⏳ Pendentes", len(pending_tasks))
with m_col3: st.metric("✅ Concluídas", len(completed_tasks))

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
            js_data = {"xmlB64": xml_b64, "completedTasks": [t['task_name'] for t in completed_tasks], "pendingTasks": [t['task_name'] for t in pending_tasks]}
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
