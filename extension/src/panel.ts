import * as vscode from 'vscode';

export class StackDecidePanel {
    public static currentPanel: StackDecidePanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel) {
        this._panel = panel;
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.html = this._getHtmlForWebview();
    }

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

    private _getHtmlForWebview() {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>StackDecide</title>
            </head>
            <body>
                <h1>StackDecide</h1>
                <p>Coming soon</p>
            </body>
            </html>`;
    }
}
