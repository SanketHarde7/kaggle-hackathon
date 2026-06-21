import * as http from 'http';

export class BackendClient {
    private baseUrl = 'http://localhost:8000';

    public async checkHealth(): Promise<boolean> {
        return new Promise((resolve) => {
            const req = http.get(`${this.baseUrl}/health`, (res) => {
                if (res.statusCode === 200) {
                    resolve(true);
                } else {
                    resolve(false);
                }
            });

            req.on('error', (e) => {
                console.error(`BackendClient health check error: ${e.message}`);
                resolve(false);
            });

            req.end();
        });
    }

    public async analyze(query: string, workspacePath: string, manualContext?: string): Promise<string> {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify({
                query,
                workspace_path: workspacePath,
                manual_context: manualContext
            });

            const options = {
                hostname: 'localhost',
                port: 8000,
                path: '/analyze',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(data)
                }
            };

            const req = http.request(options, (res) => {
                let responseData = '';
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                res.on('end', () => {
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        try {
                            const json = JSON.parse(responseData);
                            resolve(json.message);
                        } catch (e) {
                            reject(new Error('Failed to parse backend response'));
                        }
                    } else {
                        reject(new Error(`Backend returned status code ${res.statusCode}`));
                    }
                });
            });

            req.on('error', (e) => {
                reject(new Error(`Failed to connect to backend: ${e.message}`));
            });

            req.write(data);
            req.end();
        });
    }
}
