import azure.functions as func
from dotenv import load_dotenv

from mcp_server import mcp


load_dotenv()
asgi_app = mcp.streamable_http_app()

app = func.AsgiFunctionApp(
    app=asgi_app,
    http_auth_level=func.AuthLevel.FUNCTION,
)