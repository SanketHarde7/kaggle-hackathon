import * as vscode from 'vscode';
import { getWebviewContent } from './ui';
import { BackendClient } from './backendClient';

/**
 * Interface representing the structure of messages sent from the Webview UI to the extension.
 */
interface WebviewMessage {
    command: 'analyze' | 'saveSettings' | 'getSettings' | 'copyToClipboard';
    query?: string;
    manualContext?: string;
    proceed_anyway?: boolean;
    provider?: string;
    apiKey?: string;
    tavilyApiKey?: string;
    text?: string;
}

/**
 * Manages the StackDecide Webview Panel.
 * Handles UI rendering, lifecycle events, and IPC communication with the Webview.
 */
export class StackDecidePanel {
    public static currentPanel: StackDecidePanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    private _backendClient: BackendClient;

    /**
     * Private constructor used to instantiate the panel singleton.
     * @param {vscode.WebviewPanel} panel The VS Code Webview panel instance.
     */
    private constructor(panel: vscode.WebviewPanel) {
        this._panel = panel;
        this._backendClient = new BackendClient();
        
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.options = { enableScripts: true };
        this._panel.webview.html = this._getHtmlForWebview();

        this._setWebviewMessageListener(this._panel.webview);
    }

    /**
     * Creates or shows the existing StackDecide panel.
     * @param {vscode.Uri} extensionUri The URI of the extension directory.
     */
    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (StackDecidePanel.currentPanel) {
            StackDecidePanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'stackDecide',
            'StackDecide',
            column || vscode.ViewColumn.One,
            {}
        );

        StackDecidePanel.currentPanel = new StackDecidePanel(panel);
    }

    /**
     * Disposes of the panel and cleans up resources.
     */
    public dispose() {
        StackDecidePanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    /**
     * Retrieves the HTML content for the Webview.
     * @returns {string} The HTML string.
     */
    private _getHtmlForWebview(): string {
        return getWebviewContent();
    }

    /**
     * Sets up the listener for messages originating from the Webview frontend.
     * @param {vscode.Webview} webview The Webview instance to listen to.
     */
    private _setWebviewMessageListener(webview: vscode.Webview) {
        webview.onDidReceiveMessage(
            async (message: WebviewMessage) => {
                switch (message.command) {
                    case 'analyze':
                        const query = message.query;
                        const manualContext = message.manualContext || undefined;
                        const proceedAnyway = message.proceed_anyway || false;
                        
                        const workspaceFolders = vscode.workspace.workspaceFolders;
                        if (!workspaceFolders || workspaceFolders.length === 0) {
                            webview.postMessage({
                                command: 'analysisError',
                                error: 'Open a project folder in VS Code to use StackDecide.'
                            });
                            return;
                        }
                        
                        const workspacePath = workspaceFolders[0].uri.fsPath;

                        try {
                            const result = await this._backendClient.analyze(query || '', workspacePath, manualContext, proceedAnyway);
                            if (result && result.requires_approval) {
                                webview.postMessage({
                                    command: 'approvalRequired',
                                    decision_count: result.decision_count,
                                    decisions: result.decisions,
                                });
                            } else {
                                webview.postMessage({ command: 'analysisResult', brief: result });
                            }
                        } catch (err: any) {
                            let errMsg = err.message || "An unknown error occurred.";
                            if (err.status === 401) {
                                errMsg = "Your API key was rejected — check it in Settings.";
                            } else if (err.status === 422) {
                                errMsg = "The backend failed to produce a valid DecisionBrief JSON.";
                            }
                            webview.postMessage({ command: 'analysisError', error: errMsg });
                        }
                        return;


                    case 'saveSettings':
                        try {
                            if (!message.provider) {
                                throw new Error("Provider must be specified");
                            }
                            await this._backendClient.saveSettings(message.provider, message.apiKey, message.tavilyApiKey);
                            webview.postMessage({ command: 'settingsSaved' });
                        } catch (err: any) {
                            webview.postMessage({ command: 'settingsError', error: err.message || 'Failed to save settings' });
                        }
                        return;

                    case 'getSettings':
                        try {
                            const settings = await this._backendClient.getSettings();
                            webview.postMessage({ 
                                command: 'settingsLoaded', 
                                provider: settings.provider, 
                                configured: settings.configured,
                                tavilyConfigured: settings.tavily_configured
                            });
                        } catch (err) {
                            console.error("Failed to load settings from backend", err);
                        }
                        return;

                    case 'copyToClipboard':
                        if (message.text) {
                            vscode.env.clipboard.writeText(message.text);
                        }
                        return;
                }
            },
            undefined,
            this._disposables
        );
    }
}
