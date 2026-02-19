# GithubTest

`docs/spec.md` の要件を満たす最小アプリです。

- Azure AI Search を検索する
- 入力値は検索文
- 検索方法はハイブリッド検索
- ベクター化には Azure OpenAI を使う
- 検索数は 5 件（`--top` で変更可能）

## 構成ファイル

- `app.py`: ハイブリッド検索の実行ロジック（CLIエントリポイント）
- `mcp_server.py`: MCPサーバー定義（Streamable HTTP）
- `function_app.py`: Azure Functions 用エントリポイント
- `host.json`: Azure Functions ホスト設定（`routePrefix` など）
- `requirements.txt`: Python 依存関係
- `.env.example`: 環境変数テンプレート
- `.env`: ローカル実行用の実環境変数（各自設定）
- `docs/spec-01.md`: アプリ要件メモ
- `docs/spec-02_mcp.md`: MCP化要件メモ
- `docs/spec-03_azure_deploy.md`: Azure デプロイ要件メモ
- `README.md`: セットアップ・実行・デプロイ手順

## セットアップ

1. 依存関係インストール

```bash
pip install -r requirements.txt
```

2. 環境変数設定

`.env.example` を `.env` にコピーして値を設定します。

```bash
cp .env.example .env
```

Windows PowerShell の場合:

```powershell
Copy-Item .env.example .env
```

## 実行

```bash
python app.py "ホテルから徒歩圏のレストランを探したい"
```

`top=5` がデフォルトです。変更する場合:

```bash
python app.py "ホテルから徒歩圏のレストランを探したい" --top 5
```

## MCPサーバーとして実行

このアプリはMCPサーバーとしても起動できます（Streamable HTTP）。

```bash
python mcp_server.py
```

デフォルトのエンドポイント:

- `http://127.0.0.1:8000/mcp`

必要に応じて以下で変更できます:

- `MCP_HOST`（デフォルト: `127.0.0.1`）
- `MCP_PORT`（デフォルト: `8000`）
- `MCP_PATH`（デフォルト: `/mcp`）

公開されるツール:

- `hybrid_search_tool(query: str, top: int = 5)`

## Azure Functions へデプロイ

このリポジトリは Azure Functions (Python) にそのままデプロイできます。

- エントリポイント: `function_app.py`
- MCP エンドポイント: `/mcp`
- 認証レベル: `FUNCTION`（Function Key 必須）

### 前提

- Azure Functions Core Tools
- Azure CLI ログイン済み（`az login`）
- デプロイ先は Linux の Function App（推奨: Flex Consumption `FC1`）

### アプリ設定（Function App）

以下を Function App の Application Settings に設定します（`.env` と同じ値）。

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_VECTOR_FIELD`
- `AZURE_SEARCH_SELECT_FIELDS`
- `MCP_HOST`（`<YOUR_FUNCTION_APP_NAME>.azurewebsites.net` を推奨）
- `MCP_STATELESS_HTTP`（推奨: `true`）

### デプロイ

```bash
func azure functionapp publish <YOUR_FUNCTION_APP_NAME> --python
```

## GitHub Actions で CI/CD

このリポジトリには GitHub Actions workflow が含まれています。

- workflow: `.github/workflows/main_func-ketana-ext-python-mcp.yml`
- `pull_request`（`main` 向け）: CI のみ実行（依存関係インストール＋構文チェック）
- `push`（`main`）: CI 成功後に Azure Functions へ自動デプロイ

### GitHub Secrets（必須）

Repository Settings > Secrets and variables > Actions に以下を設定してください。

- `AZUREAPPSERVICE_CLIENTID_9BAE7E1EB8E54CA0AA27BBDD81AF6DD1`
- `AZUREAPPSERVICE_TENANTID_DEB6344B76F34571A8855EE183600A26`
- `AZUREAPPSERVICE_SUBSCRIPTIONID_F452193695A9463D9248339D6EC15FB4`

上記 3 つは `azure/login@v2` の OIDC ログインに使います。
（Federated Credential が設定済みの Service Principal/App Registration が必要です）

デプロイ後の URL 例:

- `https://<YOUR_FUNCTION_APP_NAME>.azurewebsites.net/mcp`

`FUNCTION` 認証のため、呼び出し時は Function Key を付与してください。

`?code=<FUNCTION_KEY>` のクエリ方式だけでなく、`x-functions-key` ヘッダー方式も利用できます。
URLにキーを含めたくない場合は、`x-functions-key` ヘッダーを使ってください。

`Invoke-RestMethod` で `Invalid Host header` が出る場合は、`MCP_HOST` の値が受信ホストと一致しているか確認してください。

`Bad Request: Missing session ID` / `Session not found` が出る場合は、`MCP_STATELESS_HTTP=true` でデプロイしてください。

PowerShell で `tools/list` を呼ぶ例:

```powershell
$uri = "https://<YOUR_FUNCTION_APP_NAME>.azurewebsites.net/mcp"
$body = '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
Invoke-WebRequest -Method Post -Uri $uri -Headers @{ Accept = "application/json, text/event-stream"; "x-functions-key" = "<FUNCTION_KEY>" } -ContentType "application/json" -Body $body
```

PowerShell で `hybrid_search_tool` を呼ぶ例:

```powershell
$uri = "https://<YOUR_FUNCTION_APP_NAME>.azurewebsites.net/mcp"
$body = '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"hybrid_search_tool","arguments":{"query":"ホテルから徒歩圏のレストランを探したい","top":5}}}'
Invoke-WebRequest -Method Post -Uri $uri -Headers @{ Accept = "application/json, text/event-stream"; "x-functions-key" = "<FUNCTION_KEY>" } -ContentType "application/json" -Body $body
```

MCP Inspector で接続する場合:

- Transport Type: `Streamable HTTP`
- URL: `https://<YOUR_FUNCTION_APP_NAME>.azurewebsites.net/mcp`
- Authentication > API Token Authentication:
	- Header Name: `x-functions-key`
	- Bearer Token: `<FUNCTION_KEY>`