import * as vscode from 'vscode';
import { BackendClient } from './backendClient';
import { StackDecidePanel } from './panel';
import { ensureBackendRunning, stopBackend } from './backendManager';
import { SidebarProvider } from './sidebarProvider';

export function activate(context: vscode.ExtensionContext) {
    const backendClient = new BackendClient();

    let disposable = vscode.commands.registerCommand('stackdecide.analyze', async () => {
        const isHealthy = await ensureBackendRunning(context, backendClient);
        
        if (isHealthy) {
            // Optionally open the panel
            StackDecidePanel.createOrShow(context.extensionUri);
        }
    });

    context.subscriptions.push(disposable);

    const sidebarProvider = new SidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("stackdecide.sidebarView", sidebarProvider)
    );
}

export function deactivate() {
    stopBackend();
}
