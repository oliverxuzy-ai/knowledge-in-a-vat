"""vault-mcp: Personal knowledge vault MCP server."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("vault-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
