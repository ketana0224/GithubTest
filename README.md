# GithubTest

`docs/spec.md` の要件を満たす最小アプリです。

- Azure AI Search を検索する
- 入力値は検索文
- 検索方法はハイブリッド検索
- ベクター化には Azure OpenAI を使う
- 検索数は 5 件（`--top` で変更可能）

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