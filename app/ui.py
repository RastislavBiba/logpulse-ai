def get_dashboard_html() -> str:
    """Vráti vstavané HTML/CSS rozhranie pre NOTIX Incident Command Center."""
    return """<!DOCTYPE html>
<html lang="sk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOTIX s.r.o. | Incident Copilot & LogPulse</title>
    <style>
        :root {
            --bg: #0b1120;
            --card-bg: #151f32;
            --border: #233554;
            --cyan: #00e5ff;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --danger: #f87171;
            --warning: #fbbf24;
            --success: #34d399;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 2rem 1rem;
        }
        .container { max-width: 1050px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .brand-box { display: flex; align-items: center; gap: 0.85rem; }
        .logo-badge {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #00e5ff, #0077b6);
            color: #0b1120;
            font-weight: 900;
            font-size: 1.4rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            box-shadow: 0 4px 14px rgba(0, 229, 255, 0.25);
        }
        .brand-title { font-size: 1.5rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; }
        .brand-tag {
            font-size: 0.7rem;
            background: rgba(0, 229, 255, 0.1);
            color: var(--cyan);
            border: 1px solid rgba(0, 229, 255, 0.3);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
        }
        .subtitle { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }
        .live-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background: rgba(52, 211, 153, 0.1);
            border: 1px solid rgba(52, 211, 153, 0.3);
            color: var(--success);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.4rem 0.8rem;
            border-radius: 9999px;
        }
        .live-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
            box-shadow: 0 0 8px var(--success);
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }
        .input-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .label { font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }
        .chips-group { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
        .chips-label { font-size: 0.75rem; color: var(--text-muted); }
        .chip-btn {
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--cyan);
            font-size: 0.75rem;
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .chip-btn:hover { background: var(--border); color: #fff; }
        textarea {
            width: 100%;
            background: #070b14;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.8rem;
            color: var(--cyan);
            outline: none;
            resize: vertical;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            transition: border-color 0.2s;
        }
        textarea:focus { border-color: var(--cyan); }
        .input-bottom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .helper-text { font-size: 0.75rem; color: var(--text-muted); }
        .submit-btn {
            background: linear-gradient(135deg, var(--cyan), #0077b6);
            color: #0b1120;
            font-weight: 800;
            font-size: 0.9rem;
            padding: 0.75rem 1.6rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(0, 229, 255, 0.3);
        }
        .submit-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
        #loader { text-align: center; padding: 3rem 0; display: none; }
        .spinner {
            display: inline-block;
            width: 42px;
            height: 42px;
            border: 4px solid rgba(0, 229, 255, 0.2);
            border-top-color: var(--cyan);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loader-text { margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted); }
        #results { display: none; margin-bottom: 2rem; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
        }
        .metric-title { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em; }
        .metric-value { font-size: 1.2rem; font-weight: 800; margin-top: 0.3rem; }
        .two-cols {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .detail-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .card-title { font-size: 0.9rem; font-weight: 700; color: #fff; }
        .copy-btn {
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .copy-btn:hover { color: #fff; border-color: var(--cyan); }
        .code-block {
            background: #070b14;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.85rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.8rem;
            color: var(--warning);
            overflow-x: auto;
            word-break: break-all;
        }
        .client-card {
            background: linear-gradient(145deg, #151f32, #0d1527);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.25rem;
        }
        .summary-text { font-size: 0.9rem; font-style: italic; color: #cbd5e1; margin-top: 0.5rem; }
        footer {
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="brand-box">
                <div class="logo-badge">N</div>
                <div>
                    <div class="brand-title">
                        NOTIX <span class="brand-tag">s.r.o.</span>
                        <span style="color: var(--border); font-weight: 300;">|</span>
                        <span style="font-size: 1.15rem; color: #cbd5e1;">Incident Swarm & LogPulse</span>
                    </div>
                    <div class="subtitle">Enterprise Log Management, K8s Profylaxe & AI Multi-Agent Triage</div>
                </div>
            </div>
            <div class="live-badge">
                <span class="live-dot"></span> Azure Production Cluster
            </div>
        </header>

        <div class="card">
            <div class="input-top">
                <span class="label">Vstup incidentu (Stacktrace, Kibana / K8s / Kafka logy):</span>
                <div class="chips-group">
                    <span class="chips-label">Rýchle enterprise šablóny:</span>
                    <button type="button" class="chip-btn" onclick="setScenario('elastic')">Elastic Shards OOM</button>
                    <button type="button" class="chip-btn" onclick="setScenario('kafka')">Kafka Consumer Lag</button>
                    <button type="button" class="chip-btn" onclick="setScenario('k8s')">AKS CrashLoop</button>
                </div>
            </div>

            <textarea id="logInput" rows="6" placeholder="Sem vložte výpis logov z Kibany, kubectl logs alebo CI/CD..."></textarea>

            <div class="input-bottom">
                <span class="helper-text">⚡ Multi-agent orchestruje: Triage ➔ Root Cause ➔ Remediation ➔ Safety Check</span>
                <button id="runBtn" class="submit-btn" onclick="analyzeLog()">Analyzovať & Vyriešiť Incident</button>
            </div>
        </div>

        <div id="loader">
            <div class="spinner"></div>
            <div class="loader-text">NOTIX Sub-Agenti vyhodnocujú incident a SLA dopad...</div>
        </div>

        <div id="results">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">SEVERITY</div>
                    <div id="resSeverity" class="metric-value" style="color: var(--danger);">CRITICAL</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">STACK & KATEGÓRIA</div>
                    <div id="resCategory" class="metric-value" style="color: var(--cyan); font-size: 1rem;">Elastic Stack</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">SLA RISK</div>
                    <div id="resSla" class="metric-value" style="color: var(--warning);">HIGH</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">SAFETY VERDICT</div>
                    <div id="resSafety" class="metric-value" style="color: var(--success);">SAFE</div>
                </div>
            </div>

            <div class="two-cols">
                <div class="detail-card">
                    <div>
                        <div class="card-header">
                            <span class="card-title">🔍 Root Cause Analyzer</span>
                            <span id="resComponent" style="font-size: 0.75rem; background: #0f172a; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace;"></span>
                        </div>
                        <p id="resRootCause" style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;"></p>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 1rem; border-top: 1px solid var(--border); padding-top: 0.5rem;">
                        Model: <span id="resModel" style="color: var(--cyan); font-family: monospace;"></span>
                    </div>
                </div>

                <div class="detail-card">
                    <div>
                        <div class="card-header">
                            <span class="card-title">⚙️ Auto-Remediation Runbook</span>
                            <button class="copy-btn" onclick="copyCode()">Kopírovať</button>
                        </div>
                        <div class="code-block"><code id="resCmd"></code></div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--success); margin-top: 1rem;">
                        ✓ Overené Safety Auditorom pred spustením.
                    </div>
                </div>
            </div>

            <div class="client-card">
                <div class="card-header">
                    <span class="card-title">📋 NOTIX Client & Ticket Summary (Jira / SLA)</span>
                    <button class="copy-btn" onclick="copySummary()">Kopírovať report</button>
                </div>
                <p id="resSummary" class="summary-text"></p>
            </div>
        </div>

        <footer>
            <div>Navrhnuté pre enterprise infraštruktúru a konzultácie <strong style="color: #fff;">NOTIX s.r.o.</strong></div>
            <div>Elastic & SIEM • Cloud & DevOps • Integrations</div>
        </footer>
    </div>

    <script>
        function setScenario(type) {
            if(type === 'elastic') {
                document.getElementById('logInput').value = "[2026-11-04T08:30:15,112][WARN ][o.e.c.r.a.AllocationService] [data-node-02] high disk watermark [92%] exceeded on [node-02], shards will be relocated\\n[2026-11-04T08:30:22,890][ERROR][o.e.x.m.e.l.LocalExporter] [data-node-02] fatal error in Elasticsearch thread [elasticsearch[data-node-02][write]]: java.lang.OutOfMemoryError: Java heap space";
            } else if(type === 'kafka') {
                document.getElementById('logInput').value = "2026-11-04 08:42:01.401 WARN [notix-order-service,3f9a,c21b] 18 --- [consumer-thread] o.a.k.c.c.internals.ConsumerCoordinator : [Consumer clientId=order-sync-1, groupId=order-processing-group] Offset commit failed on partition orders-2 at offset 849201: The coordinator is not aware of this member (CommitFailedException). Group rebalance in progress.";
            } else {
                document.getElementById('logInput').value = "Events:\\n  Type     Reason     Age               From               Message\\n  ----     ------     ----              ----               -------\\n  Warning  Unhealthy  2m (x4 over 3m)   kubelet            Liveness probe failed: HTTP probe failed with statuscode: 503\\n  Warning  BackOff    45s (x8 over 4m)  kubelet            Back-off restarting failed container notix-api-gateway in pod notix-api-gateway-7b99c8f94-vx82d_prod(AKS)";
            }
        }

        async function analyzeLog() {
            const text = document.getElementById('logInput').value;
            if(!text || text.length < 5) {
                alert("Zadajte prosím platný log (aspoň 5 znakov).");
                return;
            }

            document.getElementById('loader').style.display = 'block';
            document.getElementById('results').style.display = 'none';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ log_text: text })
                });

                if(!response.ok) throw new Error("Chyba spracovania: " + response.statusText);
                const data = await response.json();

                document.getElementById('resSeverity').innerText = data.severity;
                document.getElementById('resCategory').innerText = data.stack_category;
                document.getElementById('resComponent').innerText = data.component;
                document.getElementById('resSla').innerText = data.sla_risk;
                document.getElementById('resSafety').innerText = data.safety_verdict;
                document.getElementById('resModel').innerText = data.model_used;
                document.getElementById('resRootCause').innerText = data.root_cause;
                document.getElementById('resCmd').innerText = data.remediation_cmd;
                document.getElementById('resSummary').innerText = data.client_summary;

                document.getElementById('results').style.display = 'block';
            } catch(e) {
                alert("Chyba: " + e.message);
            } finally {
                document.getElementById('loader').style.display = 'none';
            }
        }

        function copyCode() {
            const code = document.getElementById('resCmd').innerText;
            navigator.clipboard.writeText(code);
            alert("Remediation príkaz bol skopírovaný!");
        }

        function copySummary() {
            const text = document.getElementById('resSummary').innerText;
            navigator.clipboard.writeText(text);
            alert("Zhrnutie pre ticket/klienta bolo skopírované!");
        }
    </script>
</body>
</html>"""
