import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { BackendClient } from './backendClient';

let serverProcess: cp.ChildProcess | undefined;
const outputChannel = vscode.window.createOutputChannel("StackDecide Backend");

export async function ensureBackendRunning(context: vscode.ExtensionContext, backendClient: BackendClient): Promise<boolean> {
    const isHealthy = await backendClient.checkHealth();
    if (isHealthy) {
        outputChannel.appendLine("Backend is already running.");
        return true;
    }

    return await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "StackDecide",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Checking backend server..." });

        const backendDir = path.join(context.extensionPath, 'backend');
        const venvDir = path.join(backendDir, 'venv');
        const isWindows = process.platform === 'win32';
        
        let pythonExec = isWindows ? path.join(venvDir, 'Scripts', 'python.exe') : path.join(venvDir, 'bin', 'python');
        
        if (!fs.existsSync(pythonExec)) {
            progress.report({ message: "Setting up Python environment (this may take a minute)..." });
            
            // Check if global python is available and >= 3.10
            let systemPython: string | null = null;
            const pythonCmds = isWindows ? ['python', 'py -3', 'py -3.11', 'py -3.10', 'python3'] : ['python3', 'python3.11', 'python3.10', 'python'];
            
            for (const cmd of pythonCmds) {
                try {
                    const versionOut = await execPromise(`${cmd} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`);
                    const versionMatch = versionOut.trim();
                    const [major, minor] = versionMatch.split('.').map(Number);
                    if (major === 3 && minor >= 10) {
                        systemPython = cmd;
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }

            if (!systemPython) {
                vscode.window.showErrorMessage("StackDecide requires Python 3.10+ to run its local backend. Please ensure a compatible Python version is installed and in your PATH.");
                return false;
            }

            try {
                outputChannel.appendLine("Creating virtual environment...");
                await execPromise(`${systemPython} -m venv venv`, { cwd: backendDir });
                const pipExec = isWindows ? path.join(venvDir, 'Scripts', 'pip.exe') : path.join(venvDir, 'bin', 'pip');
                outputChannel.appendLine("Installing dependencies...");
                await execPromise(`"${pipExec}" install -r requirements.txt`, { cwd: backendDir });
                outputChannel.appendLine("Dependencies installed successfully.");
            } catch (e: any) {
                outputChannel.appendLine(`Setup failed: ${e.message}`);
                vscode.window.showErrorMessage(`Failed to set up backend: ${e.message}`);
                return false;
            }
        }

        progress.report({ message: "Launching server..." });
        
        serverProcess = cp.spawn(pythonExec, ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
            cwd: backendDir,
            env: { ...process.env, PYTHONPATH: backendDir }
        });

        serverProcess.stdout?.on('data', (data) => outputChannel.append(data.toString()));
        serverProcess.stderr?.on('data', (data) => outputChannel.append(data.toString()));

        // Poll for health
        for (let i = 0; i < 20; i++) {
            await new Promise(resolve => setTimeout(resolve, 500));
            if (await backendClient.checkHealth()) {
                outputChannel.appendLine("Backend started successfully.");
                return true;
            }
        }

        vscode.window.showErrorMessage("StackDecide backend failed to start within expected time. Check Output > StackDecide Backend for logs.");
        return false;
    });
}

export function stopBackend() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = undefined;
        outputChannel.appendLine("Backend stopped.");
    }
}

function execPromise(command: string, options: cp.ExecOptions = {}): Promise<string> {
    return new Promise((resolve, reject) => {
        cp.exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject(error);
                return;
            }
            resolve(stdout.toString());
        });
    });
}
