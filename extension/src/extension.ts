import * as vscode from 'vscode';
import { BackendClient } from './backendClient';
import { StackDecidePanel } from './panel';

export function activate(context: vscode.ExtensionContext) {
    const backendClient = new BackendClient();

    let disposable = vscode.commands.registerCommand('stackdecide.analyze', async () => {
        vscode.window.showInformationMessage('StackDecide activated — backend connection: [checking...]');

        const isHealthy = await backendClient.checkHealth();
        
        if (isHealthy) {
            vscode.window.showInformationMessage('StackDecide backend is connected successfully.');
            // Optionally open the panel
            StackDecidePanel.createOrShow(context.extensionUri);
        } else {
            vscode.window.showErrorMessage('Backend not running — start it with: uvicorn app.main:app');
        }
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}
