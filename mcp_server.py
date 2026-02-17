import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from app import hybrid_search


def build_mcp_server() -> FastMCP:
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    streamable_http_path = os.getenv("MCP_PATH", "/mcp")
    return FastMCP(
        "azure-hybrid-search",
        host=host,
        port=port,
        streamable_http_path=streamable_http_path,
    )


mcp = build_mcp_server()


@mcp.tool(description="Azure AI Searchのハイブリッド検索を実行して上位結果を返します")
def hybrid_search_tool(query: str, top: int = 5) -> list[dict]:
    if top <= 0:
        raise ValueError("top は1以上を指定してください。")
    return hybrid_search(query_text=query, top=top)


if __name__ == "__main__":
    load_dotenv()
    mcp.run(transport="streamable-http")