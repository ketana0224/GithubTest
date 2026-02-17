import argparse
import json
import os
import sys

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from openai import AzureOpenAI


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"環境変数 {name} が未設定です。")
    return value


def build_embedding_client() -> AzureOpenAI:
    endpoint = get_required_env("AZURE_OPENAI_ENDPOINT")
    normalized_endpoint = endpoint.rstrip("/")
    if "/openai" in normalized_endpoint:
        normalized_endpoint = normalized_endpoint.split("/openai", 1)[0]
    api_key = get_required_env("AZURE_OPENAI_API_KEY")
    api_version = get_required_env("AZURE_OPENAI_API_VERSION")
    return AzureOpenAI(azure_endpoint=normalized_endpoint, api_key=api_key, api_version=api_version)


def get_query_embedding(text: str) -> list[float]:
    embedding_model = get_required_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    client = build_embedding_client()
    response = client.embeddings.create(model=embedding_model, input=text)
    return response.data[0].embedding


def build_search_client() -> SearchClient:
    endpoint = get_required_env("AZURE_SEARCH_ENDPOINT")
    index_name = get_required_env("AZURE_SEARCH_INDEX_NAME")
    api_key = get_required_env("AZURE_SEARCH_API_KEY")
    return SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(api_key))


def hybrid_search(query_text: str, top: int = 5) -> list[dict]:
    vector_field = get_required_env("AZURE_SEARCH_VECTOR_FIELD")
    select_fields_raw = os.getenv("AZURE_SEARCH_SELECT_FIELDS", "")
    select_fields = [field.strip() for field in select_fields_raw.split(",") if field.strip()]

    query_vector = get_query_embedding(query_text)
    vector_query = VectorizedQuery(
        vector=query_vector,
        k=top,
        fields=vector_field,
        exhaustive=True,
    )

    client = build_search_client()
    results = client.search(
        search_text=query_text,
        vector_queries=[vector_query],
        top=top,
        select=select_fields if select_fields else None,
    )

    items: list[dict] = []
    for row in results:
        item = dict(row)
        item["@search.score"] = row.get("@search.score")
        items.append(item)
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Azure AI Search ハイブリッド検索アプリ")
    parser.add_argument("query", help="検索文")
    parser.add_argument("--top", type=int, default=5, help="取得件数（デフォルト: 5）")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    try:
        result = hybrid_search(query_text=args.query, top=args.top)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())