"""Punto de entrada principal para ejecutar el servidor MCP SIBOM vía stdio."""
from .server import mcp_server

if __name__ == "__main__":
    mcp_server.run()
