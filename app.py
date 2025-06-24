import streamlit as st
import requests
import os
from dotenv import load_dotenv
import base64
import json
import unicodedata
import re
from auth import (
    create_user, 
    login_user, 
    init_db, 
    change_password,
    get_all_users,
    get_user_details,
    update_user_by_admin
)

# --- Configuração da Página e Inicialização do DB ---
st.set_page_config(page_title="Acompanhamento de Tarefas", page_icon="📋", layout="wide")
init_db()

# --- Carregando Variáveis de Ambiente ---
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    st.error('⚠️ API_TOKEN não encontrado no ficheiro .env! A aplicação não poderá buscar dados das tarefas.')
    st.stop()

# --- Funções Utilitárias ---
def format_date(date_string, include_time=True):
    if not date_string: return 'Data não disponível'
    try:
        from datetime import datetime, timedelta
        dt_utc = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        sao_paulo_offset = timedelta(hours=-3)
        dt_sao_paulo = dt_utc + sao_paulo_offset
        return dt_sao_paulo.strftime('%d/%m/%Y - %H:%M') if include_time else dt_sao_paulo.strftime('%d/%m/%Y')
    except Exception:
        return date_string

def load_file_content(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError:
        st.error(f"Erro: Ficheiro '{file_name}' não encontrado.")
        return ""

# --- Lógica de Login (sem registro público) ---
def show_login_page():
    st.title("Login - Acompanhamento de Tarefas")
    st.info("ℹ️ Na primeira execução, utilize o usuário `admin` e a senha `admin` para acessar.")
    
    with st.form("login_form"):
        st.markdown("### Acesse sua conta")
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            logged_in, user_role = login_user(username, password)
            if logged_in:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = user_role
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# --- Conteúdo Principal da Aplicação ---
def show_main_app():
    st.sidebar.title(f"Bem-vindo(a), {st.session_state.username}!")
    st.sidebar.markdown(f"**Cargo:** `{st.session_state.user_role}`")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Seção para o usuário logado alterar a própria senha
    with st.sidebar.expander("🔐 Alterar Minha Senha"):
        with st.form("change_password_form", clear_on_submit=True):
            current_password = st.text_input("Senha Atual", type="password", key="current_pw")
            new_password = st.text_input("Nova Senha", type="password", key="new_pw")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password", key="confirm_pw")
            
            submitted = st.form_submit_button("Alterar Senha")
            if submitted:
                if not all([current_password, new_password, confirm_password]):
                    st.warning("Por favor, preencha todos os campos.")
                elif new_password != confirm_password:
                    st.error("As novas senhas não coincidem.")
                else:
                    success = change_password(st.session_state.username, current_password, new_password)
                    if success:
                        st.success("Senha alterada com sucesso!")
                    else:
                        st.error("A senha atual está incorreta.")

    # Seção de Gerenciamento de Usuários, visível apenas para admins
    if st.session_state.user_role == 'admin':
        st.sidebar.markdown("---")
        with st.sidebar.expander("🔑 Gerenciamento de Usuários", expanded=False):
            
            # --- Formulário de Criação de Usuário ---
            with st.form("create_user_form", clear_on_submit=True):
                st.subheader("Criar Novo Usuário")
                new_username = st.text_input("Nome do Novo Usuário")
                new_password = st.text_input("Senha do Novo Usuário", type="password")
                is_admin_create = st.checkbox("Tornar este usuário um administrador?", key="is_admin_create")
                
                create_submitted = st.form_submit_button("Criar Usuário")
                if create_submitted:
                    if new_username and new_password:
                        role = "admin" if is_admin_create else "user"
                        if create_user(new_username, new_password, role):
                            st.success(f"Usuário '{new_username}' criado com sucesso com o cargo '{role}'!")
                        else:
                            st.error(f"Usuário '{new_username}' já existe.")
                    else:
                        st.warning("Por favor, preencha o nome de usuário e a senha.")

            st.markdown("---")

            # --- Formulário de Edição de Usuário ---
            st.subheader("Editar Usuário Existente")
            
            all_users = get_all_users()
            editable_users = [user for user in all_users if user != st.session_state.username] 
            
            if not editable_users:
                st.info("Não há outros usuários para editar.")
            else:
                selected_user = st.selectbox("Selecione um usuário para editar", options=editable_users)

                if selected_user:
                    user_details = get_user_details(selected_user)
                    if user_details:
                        with st.form(f"edit_user_form_{selected_user}", clear_on_submit=True):
                            st.markdown(f"**Editando:** `{selected_user}`")
                            
                            password_to_change = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"pw_{selected_user}")
                            
                            is_admin_edit = st.checkbox(
                                "É administrador?", 
                                value=(user_details['role'] == 'admin'), 
                                key=f"admin_{selected_user}"
                            )
                            
                            edit_submitted = st.form_submit_button("Atualizar Usuário")
                            if edit_submitted:
                                new_role = "admin" if is_admin_edit else "user"
                                password = password_to_change if password_to_change else None
                                
                                if update_user_by_admin(selected_user, password, new_role):
                                    st.success(f"Usuário '{selected_user}' atualizado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error(f"Falha ao atualizar o usuário '{selected_user}'.")
    
    st.sidebar.markdown("---")
    st.sidebar.info("Aplicação de acompanhamento de tarefas de Auditoria BIM.")
    
    # --- O RESTANTE DO SEU CÓDIGO DA APLICAÇÃO ---
    PROCESS_NAME_TO_FILTER = "Auditoria BIM"
    
    def fetch_data(url, method='GET', payload=None):
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
            if 'tasks' not in url: st.error(f"Erro ao buscar dados de {url}: {e}")
            return None
            
    def fetch_bpmn_xml(process_id):
        return fetch_data(f"https://app-api.holmesdoc.io/v1/admin/processes/{process_id}/troubleshooting/template")

    @st.cache_data(ttl=600)
    def fetch_instances_for_dropdown():
        instance_data_url = "https://app-api.holmesdoc.io/v1/entities/68597a8e0b52b4fa33e34995/instances/search"
        search_payload = {"query": {"from": 0, "size": 200, "order": "asc", "groups": [{"match_all": True, "terms": [{"field": "entity_id", "type": "is", "value": "68597a8e0b52b4fa33e34995"}]}],"sort": "8547a640-504b-11f0-a2c8-75d9e0938171"}}
        data = fetch_data(instance_data_url, method='POST', payload=search_payload)
        instance_map = {}
        if data and 'docs' in data:
            for doc in data['docs']:
                if doc.get('props') and len(doc['props']) > 0 and 'value' in doc['props'][0]:
                    display_name, instance_id = doc['props'][0]['value'], doc.get('instance_id')
                    if display_name and instance_id: instance_map[display_name] = instance_id
        return instance_map

    st.markdown(f"<style>{load_file_content('styles.css')}</style>", unsafe_allow_html=True)
    st.title('📋 Acompanhamento de Tarefas - Auditoria BIM')

    if 'creation_success_message' not in st.session_state:
        st.session_state.creation_success_message = None

    if st.session_state.creation_success_message:
        st.success(st.session_state.creation_success_message)
        st.session_state.creation_success_message = None

    API_URL = 'https://app-api.holmesdoc.io/v1/processes/'
    WORKFLOW_START_URL = "https://app-api.holmesdoc.io/v1/workflows/684b215594374c145b750317/start"

    with st.container():
        st.markdown('<div class="controls-wrapper">', unsafe_allow_html=True)
        with st.container():
            processes_data = fetch_data(API_URL)
            processes_base = processes_data.get('processes', []) if processes_data else []
            if PROCESS_NAME_TO_FILTER:
                processes_base = [p for p in processes_base if p.get('name') == PROCESS_NAME_TO_FILTER]

            filter_col, refresh_col, check_col, create_col = st.columns([6, 1, 2, 3])
            
            with check_col:
                include_closed = st.checkbox("Incluir", value=False, help="Incluir processos concluídos")
            
            if not include_closed:
                processes = [p for p in processes_base if p.get('status') != 'closed']
            else:
                processes = processes_base
            processes = [p for p in processes if p.get('status') != 'canceled']

            with filter_col:
                all_identifiers = sorted(list(set(p['identifier'] for p in processes)))
                filter_options = ["Todos os processos"] + all_identifiers
                selected_process = st.selectbox("Filtrar por processo:", options=filter_options, label_visibility="collapsed")
                
            with refresh_col:
                if st.button("🔄", help="Atualizar dados"):
                    st.rerun()

            with create_col:
                with st.popover("➕ Criar"):
                    instance_map = fetch_instances_for_dropdown()
                    with st.form("new_process_form_popover"):
                        st.write("Preencha os dados para iniciar um novo processo.")
                        prop_value_1 = st.text_input("Disciplina")
                        prop_value_2 = st.text_input("Etapa")
                        selected_instance_name = st.selectbox("Instância", options=[""] + list(instance_map.keys()), index=0)
                        
                        if st.form_submit_button("Iniciar Processo"):
                            if not all([prop_value_1.strip(), prop_value_2.strip(), selected_instance_name]):
                                st.error("Todos os campos são obrigatórios.")
                            else:
                                selected_instance_id = instance_map[selected_instance_name]
                                start_payload = {"workflow": {"start_event": "StartEvent_1","property_values": [{"id": "f59f23f0-4aec-11f0-83f5-4dfed4731510", "value": prop_value_1},{"id": "f1f6dc70-4aec-11f0-83f5-4dfed4731510", "value": prop_value_2}],"instance_id": selected_instance_id, "whats": "", "documents": [],"test": False, "run_automations": True, "run_triggers": True}}
                                response = fetch_data(WORKFLOW_START_URL, method='POST', payload=start_payload)
                                if response and response.get('id'):
                                    st.session_state.creation_success_message = f"Processo iniciado com sucesso! ID: {response.get('id')}"
                                    st.rerun()
                                else:
                                    st.error("Falha ao iniciar o processo.")
        st.markdown('</div>', unsafe_allow_html=True)

    process_id_map = {}
    all_tasks = {}
    history_payload = {"filters": [], "page": 1, "per_page": 100, "sortBy": ["created_at", "asc"]}

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
                    all_tasks[task_id] = {'process_id': process_id, 'process_identifier': process_identifier, 'task_name': props.get('task_name'), 'long_link': props.get('long_link'), 'task_id': task_id, 'created_at': hist.get('created_at', '')}

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

    col_pending, col_completed = st.columns(2)
    with col_pending:
        st.markdown(f'<div class="kanban-header kanban-header-pending">⏳ PENDENTE ({len(display_pending)})</div>', unsafe_allow_html=True)
        for task in display_pending:
            # CORREÇÃO: Lógica para montar o caption
            caption_parts = [
                f"📁 {task.get('process_identifier', 'N/A')}",
                f"📅 {format_date(task.get('created_at'))}"
            ]
            
            # Adiciona a data de vencimento apenas se ela existir
            if task.get('due_date'):
                due_date_formatted = format_date(task.get('due_date'), include_time=False)
                caption_parts.append(f"🎯 {due_date_formatted}")

            card_caption = " | ".join(caption_parts)
            
            card_html = f"""
            <a href="{task.get('long_link', '#')}" target="_blank" class="card-link-wrapper">
                <div class="custom-card pending-card">
                    <div class="card-title">{task.get('task_name', 'Tarefa sem nome')}</div>
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

    st.markdown("---")
    m_col1, m_col2, m_col3 = st.columns(3)
    total_tasks = len(display_pending) + len(display_completed)
    with m_col1: st.metric("📊 Total de Tarefas", total_tasks)
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
        final_html = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Componente BPMN</title><style>{load_file_content('styles.css')}</style><script src="https://unpkg.com/bpmn-js@17.0.2/dist/bpmn-navigated-viewer.production.min.js"></script></head><body>{bpmn_container_html}{js_data_script}<script>{main_js}</script></body></html>"""
        st.components.v1.html(final_html, height=510)

# --- Controle de Fluxo Principal ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    show_main_app()
else:
    show_login_page()
