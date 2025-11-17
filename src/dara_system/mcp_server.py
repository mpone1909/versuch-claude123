"""
MCP Server Module

Model Context Protocol (MCP) Server-Schnittstelle.
Bereitet die Integration mit MCP-Framework vor und definiert Tool-Schnittstellen.

HINWEIS: Dies ist eine strukturelle Vorbereitung.
Vollständige MCP-Integration erfolgt später mit echtem MCP SDK.
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Repräsentiert ein MCP-kompatibles Tool."""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    handler: Callable
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MCPServerError(Exception):
    """Fehler im MCP Server"""
    pass


class MCPServer:
    """
    MCP (Model Context Protocol) Server.

    Verwaltet Tools und stellt sie für Agents und externe Systeme bereit.
    Aktuell: Grundstruktur und lokale Tool-Registry.
    Zukünftig: Integration mit offiziellem MCP SDK.
    """

    def __init__(self, server_name: str = "dara-mcp-server"):
        """
        Initialisiert den MCP Server.

        Args:
            server_name: Name dieses MCP Servers
        """
        self.server_name = server_name
        self.tools: Dict[str, MCPTool] = {}
        logger.info(f"MCPServer '{server_name}' initialisiert")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        handler: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registriert ein neues Tool.

        Args:
            name: Eindeutiger Name des Tools
            description: Beschreibung des Tools
            parameters_schema: JSON Schema für Tool-Parameter
            handler: Funktion die das Tool implementiert
            metadata: Optionale zusätzliche Metadaten

        Raises:
            MCPServerError: Wenn Tool-Name bereits existiert
        """
        if name in self.tools:
            raise MCPServerError(f"Tool '{name}' ist bereits registriert")

        tool = MCPTool(
            name=name,
            description=description,
            parameters_schema=parameters_schema,
            handler=handler,
            metadata=metadata or {}
        )

        self.tools[name] = tool
        logger.info(f"Tool registriert: '{name}'")

    def unregister_tool(self, name: str) -> bool:
        """
        Entfernt ein Tool aus der Registry.

        Args:
            name: Name des zu entfernenden Tools

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Tool entfernt: '{name}'")
            return True
        return False

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Ruft ein registriertes Tool auf.

        Args:
            tool_name: Name des Tools
            parameters: Parameter für das Tool

        Returns:
            Ergebnis des Tool-Aufrufs

        Raises:
            MCPServerError: Wenn Tool nicht gefunden oder Aufruf fehlschlägt
        """
        if tool_name not in self.tools:
            raise MCPServerError(f"Tool '{tool_name}' nicht gefunden")

        tool = self.tools[tool_name]

        try:
            logger.info(f"Rufe Tool auf: '{tool_name}'")
            result = tool.handler(**parameters)
            return result
        except Exception as e:
            logger.error(f"Fehler beim Aufruf von Tool '{tool_name}': {e}")
            raise MCPServerError(f"Tool-Aufruf fehlgeschlagen: {e}") from e

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Listet alle registrierten Tools.

        Returns:
            Liste von Tool-Informationen
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
                "metadata": tool.metadata,
            }
            for tool in self.tools.values()
        ]

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Gibt Informationen zu einem spezifischen Tool zurück.

        Args:
            tool_name: Name des Tools

        Returns:
            Tool-Informationen oder None wenn nicht gefunden
        """
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters_schema": tool.parameters_schema,
            "metadata": tool.metadata,
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Exportiert alle Tools als JSON Schema (MCP-kompatibel).

        Returns:
            JSON Schema mit allen Tools
        """
        return {
            "server_name": self.server_name,
            "tools": self.list_tools(),
        }


class ToolRegistry:
    """
    Globale Tool-Registry für MCP Tools.
    Singleton-Pattern für zentrale Verwaltung.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.servers: Dict[str, MCPServer] = {}
        return cls._instance

    def register_server(self, server: MCPServer) -> None:
        """
        Registriert einen MCP Server.

        Args:
            server: MCPServer Instanz
        """
        self.servers[server.server_name] = server
        logger.info(f"MCP Server registriert: '{server.server_name}'")

    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """
        Holt einen registrierten Server.

        Args:
            server_name: Name des Servers

        Returns:
            MCPServer oder None
        """
        return self.servers.get(server_name)

    def list_servers(self) -> List[str]:
        """
        Listet alle registrierten Server.

        Returns:
            Liste von Server-Namen
        """
        return list(self.servers.keys())
