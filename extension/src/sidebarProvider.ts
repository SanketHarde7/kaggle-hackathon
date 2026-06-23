import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'launch': {
                    vscode.commands.executeCommand('stackdecide.analyze');
                    // Automatically close the sidebar so it acts purely as a launcher
                    vscode.commands.executeCommand('workbench.action.closeSidebar');
                    break;
                }
            }
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>StackDecide</title>
                <style>
                    body {
                        font-family: var(--vscode-font-family);
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        padding: 20px;
                        text-align: center;
                    }
                    p {
                        margin-bottom: 20px;
                        font-size: 14px;
                        color: var(--vscode-foreground);
                        opacity: 0.8;
                    }
                </style>
            </head>
            <body>
                <h2>StackDecide</h2>
                <p>StackDecide is launching in the main editor panel.</p>
                <script>
                    const vscode = acquireVsCodeApi();
                    // Auto-launch the command immediately when the sidebar is opened
                    vscode.postMessage({ type: 'launch' });
                </script>
            </body>
            </html>`;
    }
}
