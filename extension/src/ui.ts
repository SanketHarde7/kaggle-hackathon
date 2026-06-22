export function getWebviewContent() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StackDecide</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 16px;
            margin: 0;
            line-height: 1.5;
        }
        h1, h2, h3, h4 { color: var(--vscode-editor-foreground); }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }
        .header h2 { margin: 0; font-size: 1.2em; }

        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 2px;
            font-size: 1em;
        }
        button:hover { background-color: var(--vscode-button-hoverBackground); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }

        textarea, input, select {
            width: 100%;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            padding: 8px;
            margin-bottom: 12px;
            box-sizing: border-box;
            border-radius: 2px;
            font-family: var(--vscode-font-family);
        }
        textarea { resize: vertical; min-height: 80px; }
        label {
            display: block;
            margin-bottom: 4px;
            font-weight: 600;
            font-size: 0.9em;
        }

        .icon-btn {
            background: none;
            color: var(--vscode-foreground);
            border: 1px solid var(--vscode-panel-border);
            padding: 6px 10px;
            font-size: 1.2em;
        }
        .icon-btn:hover { background: var(--vscode-toolbar-hoverBackground); }

        #settings-view { display: none; }

        .spinner {
            display: none;
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid var(--vscode-button-background);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px auto;
        }
        @keyframes spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }

        .error { color: var(--vscode-errorForeground); margin-bottom: 12px; font-weight: bold; }
        .success { color: var(--vscode-testing-iconPassed); margin-bottom: 12px; font-weight: bold; }

        .warning-box {
            background-color: var(--vscode-inputValidation-warningBackground);
            border: 1px solid var(--vscode-inputValidation-warningBorder);
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 4px;
        }

        .approval-box {
            background-color: var(--vscode-inputValidation-infoBackground);
            border: 1px solid var(--vscode-inputValidation-infoBorder);
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 4px;
        }

        #results-container { display: none; margin-top: 20px; }

        /* Decision card */
        .decision-card {
            border: 1px solid var(--vscode-widget-border);
            border-radius: 4px;
            margin-bottom: 16px;
            overflow: hidden;
        }
        .decision-header {
            background: var(--vscode-editorGroupHeader-tabsBackground);
            padding: 10px 12px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .decision-pick {
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85em;
            font-weight: normal;
        }
        .decision-body { padding: 12px; }

        /* Score table */
        .score-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88em;
            margin-bottom: 10px;
        }
        .score-table th {
            text-align: left;
            background: var(--vscode-editorWidget-background);
            padding: 6px 8px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        .score-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.07));
        }
        .score-table tr.best-row td { font-weight: 600; }
        .score-num {
            text-align: center;
            font-variant-numeric: tabular-nums;
        }
        .score-total { font-weight: 700; }
        .why-text {
            font-size: 0.85em;
            opacity: 0.85;
            margin-top: 2px;
            padding: 4px 8px 8px;
            border-bottom: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.07));
        }
        .why-label { font-weight: 600; font-size: 0.8em; text-transform: uppercase; opacity: 0.6; }

        .copy-btn-row {
            display: flex;
            justify-content: flex-end;
            margin-top: 12px;
        }
    </style>
</head>
<body>

    <div class="header">
        <h2>StackDecide</h2>
        <button class="icon-btn" id="toggle-settings-btn" title="Settings">&#9881;</button>
    </div>

    <div id="error-msg" class="error"></div>
    <div id="success-msg" class="success"></div>

    <!-- Analysis View -->
    <div id="analysis-view">
        <label for="query-input">Decision Query</label>
        <textarea id="query-input" placeholder="e.g. Should I use Zustand or Redux? Or paste a full spec with multiple decisions."></textarea>

        <label for="manual-context-input">Additional Context (Optional)</label>
        <textarea id="manual-context-input" placeholder="e.g. Our team mostly knows React..." style="min-height: 50px;"></textarea>

        <div class="spinner" id="loading-spinner"></div>
        <button id="submit-btn" style="width: 100%;">Analyze Decision</button>

        <!-- Approval checkpoint (shown when >10 decisions detected) -->
        <div id="approval-container" style="display:none; margin-top:12px;">
            <div class="approval-box">
                <strong>&#8505; Approval Required</strong><br>
                StackDecide detected <span id="approval-count">N</span> distinct decisions. Do you want to analyze all of them?
                <div id="approval-decisions" style="margin-top:8px; font-size:0.9em; opacity:0.85;"></div>
                <button id="approval-confirm-btn" style="margin-top:10px; width:100%;">Yes, Analyze All</button>
            </div>
        </div>

        <div id="results-container">
            <div id="decisions-list"></div>
            <div class="copy-btn-row">
                <button id="copy-annotated-btn" style="display:none; font-size:0.85em; padding:4px 10px;">Copy Annotated Prompt</button>
            </div>
        </div>
    </div>

    <!-- Settings View -->
    <div id="settings-view">
        <h3>Settings</h3>

        <label for="provider-select">LLM Provider</label>
        <select id="provider-select">
            <option value="gemini">Gemini</option>
            <option value="claude">Claude</option>
            <option value="gpt">GPT</option>
            <option value="grok">Grok</option>
            <option value="groq">Groq</option>
            <option value="openrouter">OpenRouter</option>
        </select>

        <label for="api-key-input">LLM API Key</label>
        <input type="password" id="api-key-input" placeholder="Enter LLM API Key">

        <label for="tavily-api-key-input" style="margin-top:12px;">Tavily Search API Key</label>
        <div style="font-size:0.85em; opacity:0.8; margin-bottom:4px;">Get a free key at tavily.com (no card required)</div>
        <input type="password" id="tavily-api-key-input" placeholder="Enter Tavily API Key">

        <button id="save-settings-btn" style="width:100%; margin-top:12px;">Save Settings</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        const analysisView = document.getElementById('analysis-view');
        const settingsView = document.getElementById('settings-view');
        const toggleSettingsBtn = document.getElementById('toggle-settings-btn');
        const submitBtn = document.getElementById('submit-btn');
        const saveSettingsBtn = document.getElementById('save-settings-btn');
        const spinner = document.getElementById('loading-spinner');
        const errorMsg = document.getElementById('error-msg');
        const successMsg = document.getElementById('success-msg');
        const queryInput = document.getElementById('query-input');
        const manualContextInput = document.getElementById('manual-context-input');
        const providerSelect = document.getElementById('provider-select');
        const apiKeyInput = document.getElementById('api-key-input');
        const tavilyApiKeyInput = document.getElementById('tavily-api-key-input');
        const resultsContainer = document.getElementById('results-container');
        const copyAnnotatedBtn = document.getElementById('copy-annotated-btn');
        const approvalContainer = document.getElementById('approval-container');
        const approvalCount = document.getElementById('approval-count');
        const approvalDecisions = document.getElementById('approval-decisions');
        const approvalConfirmBtn = document.getElementById('approval-confirm-btn');

        let isSettingsOpen = false;
        let currentAnnotatedPrompt = '';
        let pendingApprovalQuery = '';
        let pendingApprovalContext = '';

        toggleSettingsBtn.addEventListener('click', () => {
            isSettingsOpen = !isSettingsOpen;
            if (isSettingsOpen) {
                analysisView.style.display = 'none';
                settingsView.style.display = 'block';
                toggleSettingsBtn.innerHTML = '&#8592; Back';
            } else {
                settingsView.style.display = 'none';
                analysisView.style.display = 'block';
                toggleSettingsBtn.innerHTML = '&#9881;';
                clearMessages();
            }
        });

        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'analysisResult':
                    showResults(message.brief);
                    stopLoading();
                    break;
                case 'approvalRequired':
                    stopLoading();
                    showApproval(message.decision_count, message.decisions);
                    break;
                case 'analysisError':
                    showError(message.error);
                    stopLoading();
                    break;
                case 'settingsLoaded':
                    if (message.provider) providerSelect.value = message.provider;
                    if (message.configured) apiKeyInput.placeholder = '•••••••• (Key Configured)';
                    if (message.tavilyConfigured) tavilyApiKeyInput.placeholder = '•••••••• (Key Configured)';
                    break;
                case 'settingsSaved':
                    showSuccess('Settings saved successfully!');
                    apiKeyInput.value = '';
                    apiKeyInput.placeholder = '•••••••• (Key Configured)';
                    if (tavilyApiKeyInput.value) {
                        tavilyApiKeyInput.value = '';
                        tavilyApiKeyInput.placeholder = '•••••••• (Key Configured)';
                    }
                    break;
                case 'settingsError':
                    showError(message.error);
                    break;
            }
        });

        submitBtn.addEventListener('click', () => {
            const query = queryInput.value.trim();
            const manualContext = manualContextInput.value.trim();
            if (!query) { showError("Please enter a decision query."); return; }
            pendingApprovalQuery = query;
            pendingApprovalContext = manualContext;
            approvalContainer.style.display = 'none';
            startLoading();
            vscode.postMessage({ command: 'analyze', query, manualContext });
        });

        approvalConfirmBtn.addEventListener('click', () => {
            approvalContainer.style.display = 'none';
            startLoading();
            vscode.postMessage({
                command: 'analyze',
                query: pendingApprovalQuery,
                manualContext: pendingApprovalContext,
                proceed_anyway: true
            });
        });

        saveSettingsBtn.addEventListener('click', () => {
            const provider = providerSelect.value;
            const apiKey = apiKeyInput.value.trim();
            const tavilyApiKey = tavilyApiKeyInput.value.trim();
            clearMessages();
            vscode.postMessage({
                command: 'saveSettings',
                provider: provider,
                apiKey: apiKey || undefined,
                tavilyApiKey: tavilyApiKey || undefined
            });
        });

        copyAnnotatedBtn.addEventListener('click', () => {
            if (!currentAnnotatedPrompt) return;
            vscode.postMessage({ command: 'copyToClipboard', text: currentAnnotatedPrompt });
            const orig = copyAnnotatedBtn.innerText;
            copyAnnotatedBtn.innerText = 'Copied!';
            setTimeout(() => { copyAnnotatedBtn.innerText = orig; }, 2000);
        });

        function startLoading() {
            submitBtn.disabled = true;
            spinner.style.display = 'block';
            resultsContainer.style.display = 'none';
            clearMessages();
        }
        function stopLoading() {
            submitBtn.disabled = false;
            spinner.style.display = 'none';
        }
        function clearMessages() {
            errorMsg.innerText = '';
            successMsg.innerText = '';
        }
        function showError(msg) {
            errorMsg.innerText = msg;
            successMsg.innerText = '';
        }
        function showSuccess(msg) {
            successMsg.innerText = msg;
            errorMsg.innerText = '';
        }

        function showApproval(count, decisions) {
            approvalCount.innerText = count;
            approvalDecisions.innerHTML = decisions.map((d, i) => \`<div>\${i+1}. \${d}</div>\`).join('');
            approvalContainer.style.display = 'block';
        }

        function escapeHtml(str) {
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }

        function showResults(brief) {
            resultsContainer.style.display = 'block';
            currentAnnotatedPrompt = brief.annotated_prompt || '';
            copyAnnotatedBtn.style.display = currentAnnotatedPrompt ? 'inline-block' : 'none';

            const list = document.getElementById('decisions-list');
            list.innerHTML = '';

            for (const res of (brief.results || [])) {
                const card = document.createElement('div');
                card.className = 'decision-card';

                const topic = escapeHtml(res.decision_topic || 'Decision');
                if (res.mismatch_warning) {
                    card.innerHTML = \`
                        <div class="decision-header">\${topic}</div>
                        <div class="decision-body">
                            <div class="warning-box"><strong>&#9888; Context Mismatch:</strong><br>\${escapeHtml(res.mismatch_warning)}</div>
                        </div>\`;
                } else {
                    const pick = escapeHtml(res.final_pick || '—');
                    let tableRows = '';
                    for (const sc of (res.scores || [])) {
                        const isBest = sc.option_name === res.final_pick;
                        tableRows += \`
                            <tr class="\${isBest ? 'best-row' : ''}">
                                <td>\${escapeHtml(sc.option_name)}\${isBest ? ' &#9733;' : ''}</td>
                                <td class="score-num">\${sc.performance}</td>
                                <td class="score-num">\${sc.maintainability}</td>
                                <td class="score-num">\${sc.cost}</td>
                                <td class="score-num">\${sc.project_fit}</td>
                                <td class="score-num score-total">\${sc.total_score}</td>
                            </tr>
                            <tr><td colspan="6" class="why-text">
                                <span class="why-label">vs others: </span>\${escapeHtml(sc.why_chosen_over_others)}
                            </td></tr>\`;
                    }

                    card.innerHTML = \`
                        <div class="decision-header">
                            \${topic}
                            <span class="decision-pick">&#10003; \${pick}</span>
                        </div>
                        <div class="decision-body">
                            <table class="score-table">
                                <thead><tr>
                                    <th>Option</th>
                                    <th class="score-num">Perf</th>
                                    <th class="score-num">Maint</th>
                                    <th class="score-num">Cost</th>
                                    <th class="score-num">Fit</th>
                                    <th class="score-num">Total</th>
                                </tr></thead>
                                <tbody>\${tableRows}</tbody>
                            </table>
                        </div>\`;
                }
                list.appendChild(card);
            }
        }

        vscode.postMessage({ command: 'getSettings' });
    </script>
</body>
</html>`;
}
