import * as http from 'http';

/**
 * Structure of the response returned by the backend for analysis requests.
 */
export interface AnalysisResponse {
    requires_approval?: boolean;
    decision_count?: number;
    decisions?: string[];
    brief?: Record<string, any>; // Complex brief structure
}

/**
 * Client for communicating with the StackDecide Python backend via HTTP.
 * Handles making requests for analysis, health checks, and settings management.
 */
export class BackendClient {
    private baseUrl = 'http://localhost:8000';

    /**
     * Checks if the local backend server is running and healthy.
     * @returns {Promise<boolean>} True if the server returns a 200 status code.
     */
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

    /**
     * Sends a decision query to the backend for analysis.
     * @param {string} query The user's decision request.
     * @param {string} workspacePath The path to the active VS Code workspace.
     * @param {string} [manualContext] Additional context provided by the user.
     * @param {boolean} [proceedAnyway] If true, bypasses the approval check for large decision counts.
     * @returns {Promise<AnalysisResponse>} The analysis result or an approval requirement payload.
     */
    public async analyze(query: string, workspacePath: string, manualContext?: string, proceedAnyway?: boolean): Promise<AnalysisResponse> {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify({
                query,
                workspace_path: workspacePath,
                manual_context: manualContext,
                proceed_anyway: proceedAnyway || false,
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
                            // If it's an approval-required response, return it as-is
                            if (json.requires_approval) {
                                resolve(json);
                            } else {
                                resolve(json.brief);
                            }
                        } catch (e) {
                            reject(new Error('Failed to parse backend response'));
                        }
                    } else {
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

    /**
     * Saves the LLM and Tavily API keys to the backend settings.
     * @param {string} [provider] The LLM provider (e.g., 'gemini', 'openai').
     * @param {string} [apiKey] The API key for the LLM provider.
     * @param {string} [tavilyApiKey] The API key for the Tavily Search API.
     * @returns {Promise<boolean>} True if the save was successful.
     */
    public async saveSettings(provider?: string, apiKey?: string, tavilyApiKey?: string): Promise<boolean> {
        return new Promise((resolve, reject) => {
            const payload: Record<string, string> = {};
            if (provider) payload.provider = provider;
            if (apiKey) payload.api_key = apiKey;
            if (tavilyApiKey) payload.tavily_api_key = tavilyApiKey;
            
            const data = JSON.stringify(payload);
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

    /**
     * Retrieves the current configuration status from the backend.
     * Keys themselves are never returned, only boolean flags indicating their presence.
     * @returns {Promise<{provider: string | null, configured: boolean, tavily_configured?: boolean}>}
     */
    public async getSettings(): Promise<{provider: string | null, configured: boolean, tavily_configured?: boolean}> {
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
