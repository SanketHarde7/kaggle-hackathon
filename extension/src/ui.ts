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
        
        /* Buttons & Inputs */
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
        .icon-btn:hover {
            background: var(--vscode-toolbar-hoverBackground);
        }

        /* Views */
        #settings-view { display: none; }
        
        /* Spinner */
        .spinner {
            display: none;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid var(--vscode-button-background);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* Messages */
        .error { color: var(--vscode-errorForeground); margin-bottom: 12px; font-weight: bold; }
        .success { color: var(--vscode-testing-iconPassed); margin-bottom: 12px; font-weight: bold; }
        .warning-box {
            background-color: var(--vscode-inputValidation-warningBackground);
            border: 1px solid var(--vscode-inputValidation-warningBorder);
            padding: 12px;
            margin-bottom: 16px;
            border-radius: 4px;
            color: var(--vscode-editor-foreground);
        }

        /* Results */
        #results-container { display: none; margin-top: 20px; }
        .chip {
            display: inline-block;
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            margin: 0 6px 6px 0;
        }
        .recommendation {
            background-color: var(--vscode-textBlockQuote-background);
            border-left: 4px solid var(--vscode-textBlockQuote-border);
            padding: 12px;
            margin: 16px 0;
        }
        details {
            background: var(--vscode-editorWidget-background);
            border: 1px solid var(--vscode-widget-border);
            margin-bottom: 8px;
            border-radius: 4px;
        }
        summary {
            padding: 10px;
            cursor: pointer;
            font-weight: 600;
            user-select: none;
            background: var(--vscode-editorGroupHeader-tabsBackground);
        }
        .angle-content { padding: 12px; }
        .tradeoffs-list {
            padding-left: 20px;
        }
        .tradeoffs-list li { margin-bottom: 6px; }

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
        <textarea id="query-input" placeholder="e.g. Should I use Zustand or Redux for state management?"></textarea>

        <label for="manual-context-input">Additional Context (Optional)</label>
        <textarea id="manual-context-input" placeholder="e.g. Our team mostly knows React..." style="min-height: 50px;"></textarea>

        <div class="spinner" id="loading-spinner"></div>
        <button id="submit-btn" style="width: 100%;">Analyze Decision</button>

        <div id="results-container">
            <div id="options-chips"></div>
            
            <div id="mismatch-warning-container" style="display:none;"></div>

            <div class="recommendation" style="position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3 style="margin-top:0;">Recommendation</h3>
                    <button id="copy-prompt-btn" style="font-size: 0.85em; padding: 4px 8px; display: none;">Copy Codex Prompt</button>
                </div>
                <p id="res-recommendation"></p>
                <p id="res-reasoning" style="opacity:0.9; font-size:0.95em;"></p>
            </div>

            <h3 style="margin-top:24px;">Critique Angles</h3>
            <div id="angles-container"></div>

            <h3 style="margin-top:24px;">Tradeoffs</h3>
            <ul class="tradeoffs-list" id="tradeoffs-list"></ul>
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

        <label for="api-key-input">API Key</label>
        <input type="password" id="api-key-input" placeholder="Enter API Key">

        <button id="save-settings-btn" style="width: 100%; margin-top: 12px;">Save Settings</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        // Elements
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

        const resultsContainer = document.getElementById('results-container');
        const copyPromptBtn = document.getElementById('copy-prompt-btn');

        let isSettingsOpen = false;
        let currentBrief = null;
        let currentQuery = '';

        // Toggle Views
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

        // Messages from Extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'analysisResult':
                    showResults(message.brief);
                    stopLoading();
                    break;
                case 'analysisError':
                    showError(message.error);
                    stopLoading();
                    break;
                case 'settingsLoaded':
                    if (message.provider) {
                        providerSelect.value = message.provider;
                    }
                    if (message.configured) {
                        apiKeyInput.placeholder = '•••••••• (Key Configured)';
                    }
                    break;
                case 'settingsSaved':
                    showSuccess('Settings saved successfully!');
                    apiKeyInput.value = '';
                    apiKeyInput.placeholder = '•••••••• (Key Configured)';
                    break;
                case 'settingsError':
                    showError(message.error);
                    break;
            }
        });

        // Submit Query
        submitBtn.addEventListener('click', () => {
            const query = queryInput.value.trim();
            const manualContext = manualContextInput.value.trim();
            if (!query) {
                showError("Please enter a decision query.");
                return;
            }
            currentQuery = query;
            startLoading();
            vscode.postMessage({
                command: 'analyze',
                query: query,
                manualContext: manualContext
            });
        });

        // Save Settings
        saveSettingsBtn.addEventListener('click', () => {
            const provider = providerSelect.value;
            const apiKey = apiKeyInput.value.trim();
            clearMessages();
            vscode.postMessage({
                command: 'saveSettings',
                provider: provider,
                apiKey: apiKey
            });
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

        // Render Results
        function showResults(brief) {
            currentBrief = brief;
            resultsContainer.style.display = 'block';
            copyPromptBtn.style.display = 'block';

            // Options
            const chipsHtml = (brief.options_considered || []).map(opt => \`<span class="chip">\${opt}</span>\`).join('');
            document.getElementById('options-chips').innerHTML = chipsHtml;

            // Warning
            const warningContainer = document.getElementById('mismatch-warning-container');
            if (brief.context_mismatch_warning) {
                warningContainer.style.display = 'block';
                warningContainer.innerHTML = \`<div class="warning-box"><strong>&#9888; Context Mismatch:</strong><br>\${brief.context_mismatch_warning}</div>\`;
                copyPromptBtn.innerText = 'Copy Clarification Prompt';
            } else {
                warningContainer.style.display = 'none';
                copyPromptBtn.innerText = 'Copy Codex Prompt';
            }

            // Recommendation
            document.getElementById('res-recommendation').innerText = brief.final_recommendation || '';
            document.getElementById('res-reasoning').innerText = brief.reasoning_summary || '';

            // Angles
            const anglesContainer = document.getElementById('angles-container');
            anglesContainer.innerHTML = '';
            if (brief.angle_breakdown) {
                for (const [angle, text] of Object.entries(brief.angle_breakdown)) {
                    // Format angle title
                    const title = angle.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                    anglesContainer.innerHTML += \`
                        <details>
                            <summary>\${title}</summary>
                            <div class="angle-content">\${text}</div>
                        </details>
                    \`;
                }
            }

            // Tradeoffs
            const tradeoffsList = document.getElementById('tradeoffs-list');
            tradeoffsList.innerHTML = (brief.tradeoffs || []).map(t => \`<li>\${t}</li>\`).join('');
        }

        copyPromptBtn.addEventListener('click', () => {
            if (!currentBrief) return;
            const promptText = generateCodexPrompt(currentBrief, currentQuery);
            vscode.postMessage({ command: 'copyToClipboard', text: promptText });
            
            const origText = copyPromptBtn.innerText;
            copyPromptBtn.innerText = 'Copied!';
            setTimeout(() => {
                copyPromptBtn.innerText = origText;
            }, 2000);
        });

        function generateCodexPrompt(brief, originalQuery) {
            const lines = [];
            
            if (brief.context_mismatch_warning) {
                lines.push('I asked: "' + originalQuery + '"');
                lines.push("");
                lines.push("StackDecide flagged a context mismatch before producing a recommendation:");
                lines.push(brief.context_mismatch_warning);
                lines.push("");
                lines.push("This means the analysis above may not be directly actionable as a coding task yet. Before implementing anything, please clarify: is there a specific part of the project I should point StackDecide at instead?");
                return lines.join('\\n');
            }
            
            lines.push("I need you to implement a technical decision for my project.");
            lines.push("");
            
            lines.push("ORIGINAL QUESTION / DECISION:");
            lines.push(originalQuery);
            lines.push("");
            
            lines.push("FINAL RECOMMENDATION:");
            lines.push(brief.final_recommendation);
            lines.push("");
            
            lines.push("KEY REASONING:");
            lines.push(brief.reasoning_summary);
            lines.push("");
            
            if (brief.tradeoffs && brief.tradeoffs.length > 0) {
                lines.push("IMPORTANT TRADEOFFS:");
                brief.tradeoffs.slice(0, 2).forEach(t => {
                    lines.push("- " + t);
                });
                lines.push("");
            }
            
            lines.push("Please implement this using the above decision as the foundation. Follow clean, maintainable patterns and avoid introducing dependencies not justified by this decision.");
            
            return lines.join('\\n');
        }

        // On Load: request settings
        vscode.postMessage({ command: 'getSettings' });

    </script>
</body>
</html>`;
}
