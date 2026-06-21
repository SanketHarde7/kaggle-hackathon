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

    public async analyze(query: string, workspacePath: string, manualContext?: string): Promise<any> {
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
                            resolve(json.brief);
                        } catch (e) {
                            reject(new Error('Failed to parse backend response'));
                        }
                    } else {
                        // Extract detailed error if possible
                        let errorMessage = `Backend returned status code ${res.statusCode}`;
                        try {
                            const errJson = JSON.parse(responseData);
                            if (errJson.detail) errorMessage = errJson.detail;
                        } catch(e) {}
                        
                        const error: any = new Error(errorMessage);
                        error.status = res.statusCode;
                        reject(error);
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

    public async saveSettings(provider: string, apiKey: string): Promise<boolean> {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify({ provider, api_key: apiKey });
            const options = {
                hostname: 'localhost',
                port: 8000,
                path: '/settings',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(data)
                }
            };

            const req = http.request(options, (res) => {
                let responseData = '';
                res.on('data', chunk => responseData += chunk);
                res.on('end', () => {
                    if (res.statusCode === 200) {
                        resolve(true);
                    } else {
                        let errorMessage = 'Failed to save settings';
                        try {
                            const errJson = JSON.parse(responseData);
                            if (errJson.detail) errorMessage = errJson.detail;
                        } catch(e) {}
                        reject(new Error(errorMessage));
                    }
                });
            });

            req.on('error', (e) => reject(new Error(`Failed to connect to backend: ${e.message}`)));
            req.write(data);
            req.end();
        });
    }

    public async getSettings(): Promise<{provider: string | null, configured: boolean}> {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: 'localhost',
                port: 8000,
                path: '/settings',
                method: 'GET'
            };

            const req = http.request(options, (res) => {
                let responseData = '';
                res.on('data', chunk => responseData += chunk);
                res.on('end', () => {
                    if (res.statusCode === 200) {
                        try {
                            resolve(JSON.parse(responseData));
                        } catch(e) {
                            reject(new Error('Failed to parse settings response'));
                        }
                    } else {
                        reject(new Error(`Failed to fetch settings, status: ${res.statusCode}`));
                    }
                });
            });

            req.on('error', (e) => reject(new Error(`Failed to connect to backend: ${e.message}`)));
            req.end();
        });
    }
}
