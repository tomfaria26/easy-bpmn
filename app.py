import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import base64

# Configuração da página
st.set_page_config(
    page_title="Acompanhamento de Tarefas",
    page_icon="📋",
    layout="wide"
)

def format_date(date_string):
    """Função para formatar data no padrão brasileiro com fuso horário de São Paulo"""
    if not date_string:
        return 'Data não disponível'
    try:
        from datetime import datetime, timezone, timedelta
        
        # Parse da data no formato ISO (2025-06-17T21:47:29.805Z)
        dt_utc = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        
        # Converter para fuso horário de São Paulo (UTC-3)
        # Nota: São Paulo pode ser UTC-2 durante horário de verão, mas vamos usar UTC-3 como padrão
        sao_paulo_offset = timedelta(hours=-3)
        dt_sao_paulo = dt_utc + sao_paulo_offset
        
        # Formato brasileiro: dd/MM/YYYY - HH:MM
        return dt_sao_paulo.strftime('%d/%m/%Y - %H:%M')
    except Exception as e:
        # Fallback manual se der erro
        try:
            # Extrair componentes da data diretamente
            if 'T' in date_string:
                date_part, time_part = date_string.split('T')
                time_part = time_part.replace('Z', '')
                if '.' in time_part:
                    time_part = time_part.split('.')[0]
                
                # Converter hora UTC para São Paulo (-3 horas)
                year, month, day = map(int, date_part.split('-'))
                hour, minute, second = map(int, time_part.split(':'))
                
                # Ajustar para fuso de São Paulo
                hour_sp = hour - 3
                
                # Ajustar dia se a hora ficar negativa
                if hour_sp < 0:
                    hour_sp += 24
                    day -= 1
                    if day <= 0:
                        # Simplificação: assumir mês anterior tem 30 dias
                        month -= 1
                        if month <= 0:
                            month = 12
                            year -= 1
                        day = 30
                
                return f"{day:02d}/{month:02d}/{year} - {hour_sp:02d}:{minute:02d}"
            else:
                return date_string
        except:
            return date_string

def load_css(file_name):
    """Carregar CSS externo"""
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo CSS '{file_name}' não encontrado. Usando estilos padrão.")
    except UnicodeDecodeError:
        # Tentar with encoding diferente se UTF-8 falhar
        try:
            with open(file_name, encoding='latin-1') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao carregar CSS: {e}")
            st.warning("Usando estilos padrão.")

def fetch_process_data():
    """Função para buscar dados dos processos"""
    headers = {'api_token': API_TOKEN}
    
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Processar dados dos processos
            if isinstance(data, dict):
                for key in ['results', 'data', 'items']:
                    if key in data:
                        data = data[key]
                        break
            if isinstance(data, dict) and 'processes' in data:
                data = data['processes']
            
            if isinstance(data, list):
                # Filtrar apenas processos não cancelados
                return [item for item in data if item.get('status') != 'canceled']
            
        return []
    except Exception as e:
        st.error(f"Erro ao buscar processos: {e}")
        return []

def fetch_process_history(process_id):
    """Função para buscar histórico de um processo específico"""
    headers = {'api_token': API_TOKEN}
    history_url = f"https://app-api.holmesdoc.io/v1/processes/{process_id}/history"
    
    try:
        response = requests.get(history_url, headers=headers)
        if response.status_code == 200:
            history_data = response.json()
            if isinstance(history_data, dict) and 'histories' in history_data:
                return history_data['histories']
        return []
    except Exception as e:
        return []

def fetch_bpmn_xml(process_id):
    """Função para buscar o XML BPMN de um processo específico"""
    headers = {'api_token': API_TOKEN}
    troubleshooting_url = f"https://app-api.holmesdoc.io/v1/admin/processes/{process_id}/troubleshooting/template"
    
    try:
        response = requests.get(troubleshooting_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('xml', None)
        else:
            return None
    except Exception as e:
        return None

def render_bpmn_viewer(xml_content, completed_tasks, pending_tasks):
    """Renderizar o visualizador BPMN usando bpmn-js com elementos coloridos"""
    # Codificar o XML em base64 para passar para o JavaScript
    xml_b64 = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
    
    # Preparar dados das tarefas para o JavaScript
    completed_task_names = [task['task_name'] for task in completed_tasks]
    pending_task_names = [task['task_name'] for task in pending_tasks]
    
    # Converter para JSON strings seguras
    import json
    completed_json = json.dumps(completed_task_names)
    pending_json = json.dumps(pending_task_names)
    
    bpmn_html = rf"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BPMN Viewer</title>
        <style>
            html, body, #canvas {{
                height: 100%;
                padding: 0;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            
            #canvas {{
                border: 1px solid #ddd;
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                width: 100% !important;
                height: 100% !important;
            }}
            
            .bjs-container {{
                width: 100% !important;
                height: 100% !important;
            }}
            
            .djs-container {{
                width: 100% !important;
                height: 100% !important;
            }}
            
            .error {{
                color: #d32f2f;
                padding: 20px;
                text-align: center;
                font-size: 16px;
                background: #ffebee;
                border-radius: 8px;
                margin: 20px;
            }}
            
            .loading {{
                color: #1976d2;
                padding: 20px;
                text-align: center;
                font-size: 16px;
                background: #e3f2fd;
                border-radius: 8px;
                margin: 20px;
            }}
            
            .controls {{
                position: absolute;
                bottom: 15px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 1000;
                background: rgba(255, 255, 255, 0.95);
                padding: 12px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
                display: flex;
                gap: 8px;
            }}
            
            .controls button {{
                margin: 0;
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s ease;
                white-space: nowrap;
            }}
            
            .controls button:hover {{
                background: #f5f5f5;
                border-color: #bbb;
                transform: translateY(-1px);
            }}
            
            .legend {{
                position: absolute;
                top: 15px;
                right: 15px;
                z-index: 1000;
                background: rgba(255, 255, 255, 0.95);
                padding: 12px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
                font-size: 12px;
                color: #666;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 4px 0;
            }}
            
            .legend-color {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                margin-right: 8px;
            }}
            
            .completed {{ background-color: #28a745; }}
            .pending {{ background-color: #ffc107; }}
            .default {{ background-color: #e9ecef; }}
        </style>
    </head>
    <body>
        <div class="loading" id="loading">🔄 Carregando diagrama BPMN...</div>
        <div class="controls" id="controls" style="display: none;">
            <button onclick="zoomIn()" title="Aumentar zoom">🔍 +</button>
            <button onclick="zoomOut()" title="Diminuir zoom">🔍 -</button>
            <button onclick="zoomFit()" title="Ajustar à tela">📐 Ajustar</button>
            <button onclick="resetZoom()" title="Zoom original">🔄 Reset</button>
        </div>
        <div class="legend" id="legend" style="display: none;">
            <div style="font-weight: bold; margin-bottom: 8px;">📊 Legenda</div>
            <div class="legend-item">
                <div class="legend-color completed"></div>
                <span>Concluído</span>
            </div>
            <div class="legend-item">
                <div class="legend-color pending"></div>
                <span>Pendente</span>
            </div>
            <div class="legend-item">
                <div class="legend-color default"></div>
                <span>Padrão</span>
            </div>
        </div>
        <div id="canvas" style="display: none;"></div>
        
        <script src="https://unpkg.com/bpmn-js@17.0.2/dist/bpmn-navigated-viewer.production.min.js"></script>
        
        <script>
            // Decodificar o XML do base64
            const xmlContent = atob('{xml_b64}');
            
            // Dados das tarefas
            const completedTasks = {completed_json};
            const pendingTasks = {pending_json};
            
            // Criar o viewer com configurações otimizadas
            const viewer = new BpmnJS({{
                container: '#canvas',
                width: '100%',
                height: '100%',
                additionalModules: [],
                moddleExtensions: {{}}
            }});
            
            let canvas;
            
            function findElementsByName(elementRegistry, taskName) {{
                const elements = elementRegistry.getAll();
                const matchedElements = [];
                
                // Normalizar o nome da tarefa para comparação
                const normalizedTaskName = taskName.toLowerCase().trim();
                
                elements.forEach(element => {{
                    if (element.businessObject && element.type !== 'bpmn:SequenceFlow') {{
                        let elementName = '';
                        
                        // Verificar o nome do elemento
                        if (element.businessObject.name) {{
                            elementName = element.businessObject.name.toLowerCase().trim();
                        }}
                        
                        // Correspondência exata ou muito próxima
                        if (elementName) {{
                            // Correspondência exata
                            if (elementName === normalizedTaskName) {{
                                matchedElements.push(element);
                                console.log('Correspondência exata encontrada:', elementName, '===', normalizedTaskName);
                                return;
                            }}
                            
                            // Correspondência com pelo menos 80% de similaridade
                            const similarity = calculateSimilarity(elementName, normalizedTaskName);
                            if (similarity >= 0.8) {{
                                matchedElements.push(element);
                                console.log('Correspondência por similaridade encontrada:', elementName, '~', normalizedTaskName, 'similaridade:', similarity);
                                return;
                            }}
                        }}
                    }}
                }});
                
                return matchedElements;
            }}
            
            function calculateSimilarity(str1, str2) {{
                // Função para calcular similaridade entre duas strings
                const longer = str1.length > str2.length ? str1 : str2;
                const shorter = str1.length > str2.length ? str2 : str1;
                
                if (longer.length === 0) {{
                    return 1.0;
                }}
                
                const distance = levenshteinDistance(longer, shorter);
                return (longer.length - distance) / longer.length;
            }}
            
            function levenshteinDistance(str1, str2) {{
                const matrix = [];
                
                for (let i = 0; i <= str2.length; i++) {{
                    matrix[i] = [i];
                }}
                
                for (let j = 0; j <= str1.length; j++) {{
                    matrix[0][j] = j;
                }}
                
                for (let i = 1; i <= str2.length; i++) {{
                    for (let j = 1; j <= str1.length; j++) {{
                        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {{
                            matrix[i][j] = matrix[i - 1][j - 1];
                        }} else {{
                            matrix[i][j] = Math.min(
                                matrix[i - 1][j - 1] + 1,
                                matrix[i][j - 1] + 1,
                                matrix[i - 1][j] + 1
                            );
                        }}
                    }}
                }}
                
                return matrix[str2.length][str1.length];
            }}
            
            function colorElements() {{
                const elementRegistry = viewer.get('elementRegistry');
                
                console.log('=== INICIANDO COLORAÇÃO ===');
                console.log('Tarefas concluídas:', completedTasks);
                console.log('Tarefas pendentes:', pendingTasks);
                
                // Primeiro, listar todos os elementos do BPMN para debug
                const allElements = elementRegistry.getAll();
                console.log('=== ELEMENTOS BPMN DISPONÍVEIS ===');
                allElements.forEach(element => {{
                    if (element.businessObject && element.type !== 'bpmn:SequenceFlow' && element.businessObject.name) {{
                        console.log('Elemento BPMN:', element.businessObject.name, '(tipo:', element.type, ')');
                    }}
                }});
                
                // Pintar elementos concluídos de verde
                console.log('=== PINTANDO CONCLUÍDAS ===');
                completedTasks.forEach(taskName => {{
                    console.log('Procurando elemento para tarefa concluída:', taskName);
                    const elements = findElementsByName(elementRegistry, taskName);
                    console.log('Elementos encontrados:', elements.length);
                    
                    if (elements.length === 0) {{
                        console.log('NENHUM elemento encontrado para:', taskName);
                    }}
                    
                    elements.forEach(element => {{
                        console.log('Pintando elemento de verde:', element.businessObject.name || element.businessObject.id);
                        const gfx = elementRegistry.getGraphics(element);
                        if (gfx) {{
                            const shape = gfx.querySelector('.djs-visual > *');
                            if (shape) {{
                                shape.style.fill = '#28a745';
                                shape.style.stroke = '#1e7e34';
                                shape.style.strokeWidth = '2px';
                            }}
                        }}
                    }});
                }});
                
                // Pintar elementos pendentes de laranja
                console.log('=== PINTANDO PENDENTES ===');
                pendingTasks.forEach(taskName => {{
                    console.log('Procurando elemento para tarefa pendente:', taskName);
                    const elements = findElementsByName(elementRegistry, taskName);
                    console.log('Elementos encontrados:', elements.length);
                    
                    if (elements.length === 0) {{
                        console.log('NENHUM elemento encontrado para:', taskName);
                    }}
                    
                    elements.forEach(element => {{
                        console.log('Pintando elemento de laranja:', element.businessObject.name || element.businessObject.id);
                        const gfx = elementRegistry.getGraphics(element);
                        if (gfx) {{
                            const shape = gfx.querySelector('.djs-visual > *');
                            if (shape) {{
                                shape.style.fill = '#ffc107';
                                shape.style.stroke = '#d39e00';
                                shape.style.strokeWidth = '2px';
                            }}
                        }}
                    }});
                }});
                
                console.log('=== COLORAÇÃO FINALIZADA ===');
            }}
            
            // Carregar o diagrama
            viewer.importXML(xmlContent)
                .then(function(result) {{
                    console.log('Diagrama BPMN carregado com sucesso!');
                    
                    // Obter o canvas para controles de zoom
                    canvas = viewer.get('canvas');
                    
                    // Mostrar o canvas e controles, esconder loading PRIMEIRO
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('canvas').style.display = 'block';
                    document.getElementById('controls').style.display = 'block';
                    document.getElementById('legend').style.display = 'block';
                    
                    // Aguardar renderização completa do DOM
                    setTimeout(function() {{
                        try {{
                            // Forçar redimensionamento do container
                            canvas.resized();
                            
                            // Obter todos os elementos para calcular bounds
                            const elementRegistry = viewer.get('elementRegistry');
                            const allElements = elementRegistry.getAll();
                            
                            if (allElements.length > 0) {{
                                // Calcular bounds de todos os elementos
                                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                                
                                allElements.forEach(element => {{
                                    if (element.x !== undefined && element.y !== undefined) {{
                                        minX = Math.min(minX, element.x);
                                        minY = Math.min(minY, element.y);
                                        maxX = Math.max(maxX, element.x + (element.width || 0));
                                        maxY = Math.max(maxY, element.y + (element.height || 0));
                                    }}
                                }});
                                
                                // Calcular centro do diagrama
                                const centerX = (minX + maxX) / 2;
                                const centerY = (minY + maxY) / 2;
                                
                                // Centralizar o viewbox no diagrama
                                const containerElement = document.getElementById('canvas');
                                const containerRect = containerElement.getBoundingClientRect();
                                
                                // Definir zoom adequado
                                const diagramWidth = maxX - minX;
                                const diagramHeight = maxY - minY;
                                const containerWidth = containerRect.width;
                                const containerHeight = containerRect.height;
                                
                                const scaleX = containerWidth / (diagramWidth + 100); // padding
                                const scaleY = containerHeight / (diagramHeight + 100); // padding
                                const scale = Math.min(scaleX, scaleY, 1); // não aumentar além de 100%
                                
                                // Aplicar zoom e centralização
                                canvas.zoom(scale);
                                canvas.viewbox({{
                                    x: centerX - (containerWidth / scale) / 2,
                                    y: centerY - (containerHeight / scale) / 2,
                                    width: containerWidth / scale,
                                    height: containerHeight / scale
                                }});
                                
                                console.log('Diagrama centralizado automaticamente');
                            }} else {{
                                // Fallback se não conseguir calcular bounds
                                canvas.zoom('fit-viewport');
                            }}
                            
                            // Colorir elementos baseado no status das tarefas
                            colorElements();
                            
                        }} catch (error) {{
                            console.error('Erro ao centralizar diagrama:', error);
                            // Fallback simples
                            canvas.zoom('fit-viewport');
                            colorElements();
                        }}
                    }}, 500); // Aumentei o delay para 500ms
                    
                    // Log de avisos se houver
                    if (result.warnings && result.warnings.length > 0) {{
                        console.warn('Avisos do BPMN:', result.warnings);
                    }}
                }})
                .catch(function(err) {{
                    console.error('Erro ao carregar diagrama BPMN:', err);
                    document.getElementById('loading').innerHTML = 
                        '<div class="error">❌ Erro ao carregar o diagrama BPMN: ' + err.message + '</div>';
                }});
            
            // Funções de controle de zoom
            function zoomIn() {{
                if (canvas) canvas.zoom(canvas.zoom() + 0.1);
            }}
            
            function zoomOut() {{
                if (canvas) canvas.zoom(Math.max(0.1, canvas.zoom() - 0.1));
            }}
            
            // Função melhorada para ajustar zoom
            function zoomFit() {{
                if (canvas) {{
                    try {{
                        canvas.zoom('fit-viewport');
                        console.log('Zoom ajustado via botão');
                    }} catch (error) {{
                        console.error('Erro ao ajustar zoom:', error);
                    }}
                }}
            }}
            
            function resetZoom() {{
                if (canvas) canvas.zoom(1);
            }}
            
            // Redimensionar quando a janela mudar
            window.addEventListener('resize', function() {{
                if (canvas) {{
                    canvas.resized();
                    // Reajustar o zoom após redimensionamento
                    setTimeout(function() {{
                        canvas.zoom('fit-viewport');
                    }}, 100);
                }}
            }});
            
            // Garantir que o diagrama seja visível ao carregar a página
            window.addEventListener('load', function() {{
                if (canvas) {{
                    setTimeout(function() {{
                        canvas.zoom('fit-viewport');
                    }}, 200);
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return bpmn_html

# Carregar estilos
load_css('styles.css')

st.title('📋 Acompanhamento de Tarefas - Auditoria BIM')

# Carregar variáveis de ambiente
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    st.error('⚠️ API_TOKEN não encontrado no .env!')
    st.stop()

API_URL = 'https://app-api.holmesdoc.io/v1/processes/'

# Carregamento dos dados
with st.spinner('Carregando tarefas...'):
    processes = fetch_process_data()

if not processes:
    st.error("Não foi possível carregar os dados.")
    st.stop()

# Criar um mapeamento de identifier para process_id
process_id_map = {}
for process in processes:
    if process.get('identifier') and process.get('id'):
        process_id_map[process.get('identifier')] = process.get('id')

# Processar dados para o Kanban
all_tasks = []

for process in processes:
    process_id = process.get('id')
    process_identifier = process.get('identifier')
    process_name = process.get('name')
    
    if not process_id:
        continue
    
    histories = fetch_process_history(process_id)
    
    # Criar um mapa de ações concluídas
    completed_actions = set()
    for hist in histories:
        message = hist.get('message', '')
        if 'tomou a ação' in message.lower() or 'tomou uma ação' in message.lower():
            # Extrair o nome da tarefa da mensagem
            if 'tarefa' in message.lower():
                parts = message.split('tarefa')
                if len(parts) > 1:
                    task_from_message = parts[1].strip()
                    completed_actions.add(task_from_message)
    
    for hist in histories:
        properties = hist.get('properties', {})
        long_link = properties.get('long_link', '')
        task_name = properties.get('task_name', '')
        created_at = hist.get('created_at', '')
        
        if long_link:  # Se tem long_link
            # Verificar se esta tarefa foi concluída
            is_completed = any(task_name in completed_task for completed_task in completed_actions)
            
            all_tasks.append({
                'process_identifier': process_identifier,
                'task_name': task_name,
                'long_link': long_link,
                'is_completed': is_completed,
                'created_at': created_at
            })

# Ordenar todas as tarefas por data de criação (mais recente primeiro)
all_tasks.sort(key=lambda x: x['created_at'], reverse=True)

# Separar tarefas por status
pending_tasks = [task for task in all_tasks if not task['is_completed']]
completed_tasks = [task for task in all_tasks if task['is_completed']]

# Filtro de processos com botão de atualizar ao lado
col1, col2 = st.columns([4, 1])
with col1:
    # Obter lista única de processos para o filtro
    all_process_identifiers = list(set([task['process_identifier'] for task in all_tasks]))
    all_process_identifiers.sort()  # Ordenar alfabeticamente
    
    # Adicionar opção "Todos"
    filter_options = ["Todos os processos"] + all_process_identifiers
    
    selected_process = st.selectbox(
        "🔍 Filtrar por processo:",
        options=filter_options,
        index=0
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento para alinhar com o selectbox
    if st.button("🔄 Atualizar"):
        st.rerun()

# Aplicar filtro nos dados
if selected_process != "Todos os processos":
    pending_tasks = [task for task in pending_tasks if task['process_identifier'] == selected_process]
    completed_tasks = [task for task in completed_tasks if task['process_identifier'] == selected_process]

# Layout Kanban
col_pending, col_completed = st.columns(2)

# Coluna Pendente
with col_pending:
    st.markdown(f"""
    <div class="kanban-header kanban-header-pending">
        ⏳ PENDENTE ({len(pending_tasks)})
    </div>
    """, unsafe_allow_html=True)
    
    for idx, task in enumerate(pending_tasks):
        formatted_date = format_date(task['created_at'])
        # Card clicável que abre o link em nova aba
        st.markdown(f"""
        <a href="{task['long_link']}" target="_blank" class="task-card-clickable">
            <div class="process-badge">📁 {task['process_identifier']}</div>
            <div class="task-title">{task['task_name']}</div>
            <div class="task-date">📅 {formatted_date}</div>
        </a>
        """, unsafe_allow_html=True)

# Coluna Concluída
with col_completed:
    st.markdown(f"""
    <div class="kanban-header kanban-header-completed">
        ✅ CONCLUÍDA ({len(completed_tasks)})
    </div>
    """, unsafe_allow_html=True)
    
    for idx, task in enumerate(completed_tasks):
        formatted_date = format_date(task['created_at'])
        st.markdown(f"""
        <div class="task-card task-card-completed">
            <div class="process-badge">📁 {task['process_identifier']}</div>
            <div class="task-title">{task['task_name']}</div>
            <div class="task-date">📅 {formatted_date}</div>
        </div>
        """, unsafe_allow_html=True)

# Resumo no rodapé das colunas
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Total de Tarefas", len(all_tasks))
with col2:
    st.metric("⏳ Pendentes", len(pending_tasks))
with col3:
    st.metric("✅ Concluídas", len(completed_tasks))

# SEÇÃO DO VISUALIZADOR BPMN
if selected_process != "Todos os processos":
    st.markdown("---")
    st.markdown(f"### 🔄 Diagrama BPMN")
    
    # Buscar o ID do processo selecionado
    selected_process_id = process_id_map.get(selected_process)
    
    if selected_process_id:
        with st.spinner(f'Carregando diagrama BPMN do processo {selected_process}...'):
            xml_content = fetch_bpmn_xml(selected_process_id)
        
        if xml_content:
            # Renderizar o visualizador BPMN com as tarefas coloridas
            bpmn_html = render_bpmn_viewer(xml_content, completed_tasks, pending_tasks)
            st.components.v1.html(bpmn_html, height=500, scrolling=False)
            
        else:
            st.warning(f"⚠️ Não foi possível carregar o diagrama BPMN para o processo **{selected_process}**. Verifique se o processo possui um template BPMN configurado.")
    else:
        st.error(f"❌ ID do processo **{selected_process}** não encontrado.")
else:
    st.markdown("---")
    st.info("🔍 **Selecione um processo específico** no filtro acima para visualizar seu diagrama BPMN.")

# Informações extras
if len(all_tasks) == 0:
    st.info("Nenhuma tarefa encontrada.")

# Rodapé com instruções
with st.expander("ℹ️ Como usar o sistema"):
    st.markdown("""
    ### 📋 Dashboard de Tarefas
    - **Filtre por processo** para ver tarefas específicas
    - **Clique no card** das tarefas pendentes para executá-las
    - **Use o botão 🔄 Atualizar** para recarregar os dados
    
    ### 🔄 Visualizador BPMN
    - **Selecione um processo** no filtro para ver seu diagrama BPMN
    - **Use os controles** no diagrama para navegar:
      - 🔍 + / 🔍 - : Zoom in/out
      - 📐 Ajustar : Ajustar à tela
      - 🔄 Reset : Zoom original
    - **Cores do diagrama**:
      - 🟢 Verde : Tarefas concluídas
      - 🟡 Laranja : Tarefas pendentes
      - ⚪ Cinza : Elementos padrão
    - **Navegue** clicando e arrastando no diagrama
    """)