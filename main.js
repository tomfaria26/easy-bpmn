window.addEventListener('load', function() {

    // --- LÓGICA DE ATUALIZAÇÃO AUTOMÁTICA ---
    setInterval(() => {
        // Encontra o botão de atualização pelo seu conteúdo (emoji)
        // A busca é feita no 'parent.document' porque o componente Streamlit roda num iframe.
        const buttons = window.parent.document.querySelectorAll('button');
        let refreshButton = null;
        buttons.forEach(button => {
            if (button.textContent.includes('🔄')) {
                refreshButton = button;
            }
        });

        if (refreshButton) {
            console.log('Auto-refresh: Clicando no botão de atualização.');
            refreshButton.click();
        } else {
            console.log('Auto-refresh: Botão de atualização não encontrado.');
        }
    }, 60000); // 60000ms = 60 segundos


    // --- LÓGICA DO DIAGRAMA BPMN (existente, sem alterações) ---
    if (window.bpmnData && window.bpmnData.xmlB64) {
        
        const bpmnContainer = document.getElementById('canvas');
        if (!bpmnContainer) return;
        
        const loadingDiv = document.getElementById('loading');
        loadingDiv.textContent = '🔄 Carregando diagrama...';

        const viewer = new BpmnJS({ container: bpmnContainer });

        window.bpmnViewer = {
            zoomIn: () => viewer.get('canvas').zoom(viewer.get('canvas').zoom() + 0.1),
            zoomOut: () => viewer.get('canvas').zoom(viewer.get('canvas').zoom() - 0.1),
            zoomFit: () => viewer.get('canvas').zoom('fit-viewport'),
            resetZoom: () => viewer.get('canvas').zoom(1)
        };
        
        function normalizeString(str) {
            if (typeof str !== 'string') return '';
            return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
        }

        function findElementsByName(registry, nameToFind) {
            const normalizedNameToFind = normalizeString(nameToFind);
            return registry.filter(el => {
                if (el.businessObject && el.businessObject.name) {
                    const normalizedElementName = normalizeString(el.businessObject.name);
                    return normalizedElementName === normalizedNameToFind;
                }
                return false;
            });
        }

        function colorElements() {
            const elementRegistry = viewer.get('elementRegistry');
            const { completedTasks, pendingTasks } = window.bpmnData;
            completedTasks.forEach(name => {
                const elements = findElementsByName(elementRegistry, name);
                elements.forEach(element => {
                    const gfx = elementRegistry.getGraphics(element);
                    if (gfx) { const visual = gfx.querySelector('.djs-visual > *'); if (visual) { visual.style.fill = '#d4edda'; visual.style.stroke = '#155724'; }}
                });
            });
            pendingTasks.forEach(name => {
                const elements = findElementsByName(elementRegistry, name);
                elements.forEach(element => {
                    const gfx = elementRegistry.getGraphics(element);
                    if (gfx) { const visual = gfx.querySelector('.djs-visual > *'); if (visual) { visual.style.fill = '#fff3cd'; visual.style.stroke = '#856404'; }}
                });
            });
        }
        
        async function importDiagram() {
            try {
                const base64ToUtf8 = (str) => {
                    const binaryString = atob(str);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    return new TextDecoder('utf-8').decode(bytes);
                };
                const xml = base64ToUtf8(window.bpmnData.xmlB64);
                await viewer.importXML(xml);
                
                document.getElementById('controls').style.display = 'flex';
                document.getElementById('legend').style.display = 'block';
                loadingDiv.style.display = 'none';

                function safeInitializeView() {
                    if (bpmnContainer && bpmnContainer.clientWidth > 0) {
                        try { viewer.get('canvas').zoom('fit-viewport'); colorElements(); } catch (e) { console.error("Erro no zoom/cor:", e); }
                    } else { setTimeout(safeInitializeView, 50); }
                }
                safeInitializeView();
            } catch (err) {
                console.error('Erro ao importar o diagrama BPMN:', err);
                loadingDiv.textContent = '❌ Erro ao carregar o diagrama.';
            }
        }
        importDiagram();
        window.addEventListener('resize', () => window.bpmnViewer.zoomFit());
    }
});
