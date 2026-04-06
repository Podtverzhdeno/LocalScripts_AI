import * as vscode from 'vscode';
import axios from 'axios';

interface GenerateRequest {
    task: string;
    max_iterations?: number;
    sandbox?: string;
}

interface GenerateResponse {
    session_id: string;
    status: string;
    code?: string;
    iterations?: number;
    errors?: string;
}

export function activate(context: vscode.ExtensionContext) {
    console.log('LocalScript extension activated');

    // Register command: Ctrl+Shift+L
    const generateCommand = vscode.commands.registerCommand(
        'localscript.generateCode',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showWarningMessage('Please select a comment or task description');
                return;
            }

            // Clean comment markers
            const task = cleanTask(selectedText);

            await generateAndInsertCode(editor, selection, task);
        }
    );

    // Register completion provider
    const config = vscode.workspace.getConfiguration('localscript');
    if (config.get('enableCompletion')) {
        const completionProvider = vscode.languages.registerCompletionItemProvider(
            'lua',
            new LocalScriptCompletionProvider(),
            '-', ' '
        );
        context.subscriptions.push(completionProvider);
    }

    context.subscriptions.push(generateCommand);
}

function cleanTask(text: string): string {
    // Remove Lua comment markers
    return text
        .split('\n')
        .map(line => line.replace(/^[\s]*--[\s]*/, ''))
        .join('\n')
        .trim();
}

async function generateAndInsertCode(
    editor: vscode.TextEditor,
    selection: vscode.Selection,
    task: string
) {
    const config = vscode.workspace.getConfiguration('localscript');
    const apiUrl = config.get<string>('apiUrl', 'http://127.0.0.1:8000');
    const maxIterations = config.get<number>('maxIterations', 3);
    const sandboxMode = config.get<string>('sandboxMode', 'lua');
    const timeout = config.get<number>('timeout', 60) * 1000;

    // Show progress
    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'LocalScript',
            cancellable: true
        },
        async (progress, token) => {
            progress.report({ message: 'Generating code...' });

            try {
                const response = await axios.post<GenerateResponse>(
                    `${apiUrl}/generate`,
                    {
                        task,
                        max_iterations: maxIterations,
                        sandbox: sandboxMode
                    } as GenerateRequest,
                    {
                        timeout,
                        onDownloadProgress: (progressEvent) => {
                            // Update progress if server sends updates
                            progress.report({ message: 'Processing...' });
                        }
                    }
                );

                if (token.isCancellationRequested) {
                    return;
                }

                const result = response.data;

                if (result.status === 'done' && result.code) {
                    // Insert generated code
                    await editor.edit(editBuilder => {
                        editBuilder.replace(selection, result.code!);
                    });

                    vscode.window.showInformationMessage(
                        `✓ Code generated in ${result.iterations} iteration(s)`
                    );
                } else {
                    vscode.window.showErrorMessage(
                        `Failed to generate code: ${result.errors || 'Unknown error'}`
                    );
                }
            } catch (error) {
                if (axios.isAxiosError(error)) {
                    if (error.code === 'ECONNREFUSED') {
                        vscode.window.showErrorMessage(
                            'Cannot connect to LocalScript API. Make sure the server is running:\n' +
                            'python api/server.py'
                        );
                    } else if (error.response) {
                        vscode.window.showErrorMessage(
                            `API error: ${error.response.data.detail || error.message}`
                        );
                    } else {
                        vscode.window.showErrorMessage(`Request failed: ${error.message}`);
                    }
                } else {
                    vscode.window.showErrorMessage(`Error: ${error}`);
                }
            }
        }
    );
}

// LSP-style completion provider
class LocalScriptCompletionProvider implements vscode.CompletionItemProvider {
    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.CompletionItem[]> {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);

        // Trigger on comment lines
        if (!linePrefix.trim().startsWith('--')) {
            return [];
        }

        const task = linePrefix.replace(/^[\s]*--[\s]*/, '').trim();

        // Only suggest if comment is meaningful
        if (task.length < 10) {
            return [];
        }

        const item = new vscode.CompletionItem(
            'Generate code from comment',
            vscode.CompletionItemKind.Snippet
        );

        item.detail = 'LocalScript AI';
        item.documentation = new vscode.MarkdownString(
            `Generate Lua code for: "${task}"\n\n` +
            `Press **Ctrl+Shift+L** or select this completion to generate code.`
        );

        // Insert command to trigger generation
        item.command = {
            command: 'localscript.generateCode',
            title: 'Generate Code'
        };

        return [item];
    }
}

export function deactivate() {
    console.log('LocalScript extension deactivated');
}
