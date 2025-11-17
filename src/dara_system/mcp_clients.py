"""
MCP Clients Module

Model Context Protocol (MCP) Client-Implementierungen.
Kapselt MCP-ähnliche Funktionalität für verschiedene Ressourcen.

HINWEIS: Diese Implementierung bietet MCP-ähnliche Schnittstellen,
die auch ohne echte MCP-Server lauffähig sind (Stub/Mock-Betrieb).
Für echte MCP-Integration können die Interfaces später erweitert werden.
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import os
import json

logger = logging.getLogger(__name__)


@dataclass
class MCPResource:
    """Repräsentiert eine MCP-Ressource."""
    uri: str
    name: str
    resource_type: str
    metadata: Dict[str, Any]


@dataclass
class MCPOperation:
    """Repräsentiert das Ergebnis einer MCP-Operation."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPClient(ABC):
    """
    Abstrakte Basisklasse für MCP-Clients.

    Definiert die Schnittstelle für MCP-ähnliche Operationen.
    """

    def __init__(self, client_name: str, **config):
        """
        Initialisiert den MCP-Client.

        Args:
            client_name: Name des Clients
            **config: Client-spezifische Konfiguration
        """
        self.client_name = client_name
        self.config = config
        logger.info(f"{self.__class__.__name__} '{client_name}' initialisiert")

    @abstractmethod
    def list_resources(self, **kwargs) -> List[MCPResource]:
        """
        Listet verfügbare Ressourcen auf.

        Returns:
            Liste von MCPResource-Objekten
        """
        pass

    @abstractmethod
    def read_resource(self, uri: str, **kwargs) -> MCPOperation:
        """
        Liest eine Ressource.

        Args:
            uri: URI der Ressource

        Returns:
            MCPOperation mit Ressourcen-Daten
        """
        pass

    @abstractmethod
    def write_resource(self, uri: str, data: Any, **kwargs) -> MCPOperation:
        """
        Schreibt/aktualisiert eine Ressource.

        Args:
            uri: URI der Ressource
            data: Zu schreibende Daten

        Returns:
            MCPOperation mit Ergebnis
        """
        pass

    def get_client_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über den Client zurück.

        Returns:
            Dictionary mit Client-Informationen
        """
        return {
            "client_name": self.client_name,
            "client_type": self.__class__.__name__,
            "config": self.config
        }


class FilesystemMCPClient(MCPClient):
    """
    MCP-Client für Filesystem-Operationen.

    Ermöglicht MCP-ähnlichen Zugriff auf lokale Dateien.
    """

    def __init__(
        self,
        client_name: str = "filesystem",
        base_path: Optional[str] = None,
        allowed_extensions: Optional[List[str]] = None
    ):
        """
        Initialisiert den Filesystem-Client.

        Args:
            client_name: Name des Clients
            base_path: Basis-Pfad für Operationen (default: aktuelles Verzeichnis)
            allowed_extensions: Liste erlaubter Dateiendungen (None = alle)
        """
        super().__init__(client_name, base_path=base_path, allowed_extensions=allowed_extensions)

        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.allowed_extensions = allowed_extensions

    def list_resources(
        self,
        pattern: str = "**/*",
        resource_type: Optional[str] = None
    ) -> List[MCPResource]:
        """
        Listet Dateien im Filesystem auf.

        Args:
            pattern: Glob-Pattern für Dateisuche
            resource_type: Filter nach Ressourcentyp

        Returns:
            Liste von MCPResource-Objekten
        """
        resources = []

        try:
            for path in self.base_path.glob(pattern):
                if not path.is_file():
                    continue

                # Filter nach erlaubten Endungen
                if self.allowed_extensions and path.suffix not in self.allowed_extensions:
                    continue

                resource = MCPResource(
                    uri=f"file://{path}",
                    name=path.name,
                    resource_type="file",
                    metadata={
                        "size": path.stat().st_size,
                        "extension": path.suffix,
                        "parent": str(path.parent)
                    }
                )
                resources.append(resource)

            logger.info(f"Gefunden: {len(resources)} Ressourcen mit Pattern '{pattern}'")

        except Exception as e:
            logger.error(f"Fehler beim Auflisten von Ressourcen: {e}")

        return resources

    def read_resource(self, uri: str, encoding: str = "utf-8") -> MCPOperation:
        """
        Liest eine Datei.

        Args:
            uri: URI der Datei (file://...)
            encoding: Textcodierung

        Returns:
            MCPOperation mit Dateiinhalt
        """
        try:
            # Extrahiere Pfad aus URI
            if uri.startswith("file://"):
                file_path = Path(uri[7:])
            else:
                file_path = Path(uri)

            if not file_path.exists():
                return MCPOperation(
                    success=False,
                    data=None,
                    error=f"Datei nicht gefunden: {file_path}"
                )

            # Lese Datei
            content = file_path.read_text(encoding=encoding)

            return MCPOperation(
                success=True,
                data=content,
                metadata={"path": str(file_path), "size": len(content)}
            )

        except Exception as e:
            logger.error(f"Fehler beim Lesen von {uri}: {e}")
            return MCPOperation(success=False, data=None, error=str(e))

    def write_resource(
        self,
        uri: str,
        data: Any,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> MCPOperation:
        """
        Schreibt eine Datei.

        Args:
            uri: URI der Datei
            data: Zu schreibende Daten (String)
            encoding: Textcodierung
            create_dirs: Verzeichnisse erstellen, falls nicht vorhanden

        Returns:
            MCPOperation mit Ergebnis
        """
        try:
            # Extrahiere Pfad
            if uri.startswith("file://"):
                file_path = Path(uri[7:])
            else:
                file_path = Path(uri)

            # Erstelle Verzeichnisse
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Schreibe Datei
            file_path.write_text(str(data), encoding=encoding)

            return MCPOperation(
                success=True,
                data={"written_bytes": len(str(data))},
                metadata={"path": str(file_path)}
            )

        except Exception as e:
            logger.error(f"Fehler beim Schreiben von {uri}: {e}")
            return MCPOperation(success=False, data=None, error=str(e))


class GitHubMCPClient(MCPClient):
    """
    MCP-Client für GitHub-Operationen (Stub).

    HINWEIS: Dies ist eine Stub-Implementierung.
    Für echte GitHub-Integration: Nutze PyGithub oder GitHub REST API.
    """

    def __init__(
        self,
        client_name: str = "github",
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        access_token: Optional[str] = None
    ):
        """
        Initialisiert den GitHub-Client.

        Args:
            client_name: Name des Clients
            repo_owner: GitHub Repository Owner
            repo_name: Repository Name
            access_token: GitHub Access Token
        """
        super().__init__(
            client_name,
            repo_owner=repo_owner,
            repo_name=repo_name
        )

        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.access_token = access_token or os.getenv("GITHUB_TOKEN")

        if not self.access_token:
            logger.warning("Kein GitHub Access Token - Client im Stub-Modus")

    def list_resources(self, path: str = "", **kwargs) -> List[MCPResource]:
        """
        Listet Repository-Inhalte auf (Stub).

        Args:
            path: Pfad im Repository

        Returns:
            Liste von MCPResource-Objekten (Stub-Daten)
        """
        logger.warning("GitHubMCPClient.list_resources() ist ein Stub")

        # Stub-Daten
        return [
            MCPResource(
                uri=f"github://{self.repo_owner}/{self.repo_name}/README.md",
                name="README.md",
                resource_type="file",
                metadata={"path": "README.md", "stub": True}
            )
        ]

    def read_resource(self, uri: str, **kwargs) -> MCPOperation:
        """
        Liest Datei aus Repository (Stub).

        Args:
            uri: URI der Ressource

        Returns:
            MCPOperation (Stub)
        """
        logger.warning("GitHubMCPClient.read_resource() ist ein Stub")

        return MCPOperation(
            success=True,
            data="[STUB] GitHub file content would be here",
            metadata={"uri": uri, "stub": True}
        )

    def write_resource(self, uri: str, data: Any, **kwargs) -> MCPOperation:
        """
        Schreibt/aktualisiert Datei im Repository (Stub).

        Args:
            uri: URI der Ressource
            data: Zu schreibende Daten

        Returns:
            MCPOperation (Stub)
        """
        logger.warning("GitHubMCPClient.write_resource() ist ein Stub - keine echte Änderung")

        return MCPOperation(
            success=False,
            data=None,
            error="GitHub write operations not implemented (stub mode)"
        )


class VectorStoreMCPClient(MCPClient):
    """
    MCP-Client für Vector Store Operationen.

    Ermöglicht MCP-ähnlichen Zugriff auf den Vector Store.
    """

    def __init__(
        self,
        client_name: str = "vector_store",
        vector_store_instance: Optional[Any] = None
    ):
        """
        Initialisiert den VectorStore-Client.

        Args:
            client_name: Name des Clients
            vector_store_instance: Instanz des Vector Stores (aus vector_store.py)
        """
        super().__init__(client_name)

        self.vector_store = vector_store_instance

        if not self.vector_store:
            logger.warning("Kein Vector Store bereitgestellt - Client im Stub-Modus")

    def list_resources(self, **kwargs) -> List[MCPResource]:
        """
        Listet gespeicherte Vektoren auf.

        Returns:
            Liste von MCPResource-Objekten
        """
        if not self.vector_store:
            return []

        resources = []

        for entry_id, entry in self.vector_store.entries.items():
            resource = MCPResource(
                uri=f"vector://{entry_id}",
                name=entry_id,
                resource_type="vector",
                metadata={
                    "text": entry.text[:100] if entry.text else None,
                    "metadata": entry.metadata,
                    "dimension": len(entry.vector)
                }
            )
            resources.append(resource)

        return resources

    def read_resource(self, uri: str, **kwargs) -> MCPOperation:
        """
        Liest einen Vektor-Eintrag.

        Args:
            uri: URI des Eintrags (vector://...)

        Returns:
            MCPOperation mit Vektor-Daten
        """
        if not self.vector_store:
            return MCPOperation(success=False, data=None, error="Kein Vector Store verfügbar")

        # Extrahiere ID
        entry_id = uri.replace("vector://", "")

        entry = self.vector_store.get_by_id(entry_id)

        if not entry:
            return MCPOperation(success=False, data=None, error=f"Eintrag nicht gefunden: {entry_id}")

        return MCPOperation(
            success=True,
            data={
                "id": entry.id,
                "vector": entry.vector,
                "text": entry.text,
                "metadata": entry.metadata
            }
        )

    def write_resource(self, uri: str, data: Any, **kwargs) -> MCPOperation:
        """
        Schreibt/aktualisiert einen Vektor-Eintrag.

        Args:
            uri: URI des Eintrags
            data: Dictionary mit 'vector', 'text', 'metadata'

        Returns:
            MCPOperation mit Ergebnis
        """
        if not self.vector_store:
            return MCPOperation(success=False, data=None, error="Kein Vector Store verfügbar")

        try:
            # Extrahiere ID
            entry_id = uri.replace("vector://", "")

            # Füge Vektor hinzu
            vector = data.get("vector")
            text = data.get("text")
            metadata = data.get("metadata", {})

            added_ids = self.vector_store.add_vectors(
                vectors=[vector],
                texts=[text] if text else None,
                metadata=[metadata],
                ids=[entry_id]
            )

            return MCPOperation(
                success=True,
                data={"added_ids": added_ids}
            )

        except Exception as e:
            logger.error(f"Fehler beim Schreiben von Vector: {e}")
            return MCPOperation(success=False, data=None, error=str(e))


class GoogleDriveMCPClient(MCPClient):
    """
    MCP-Client für Google Drive (Stub).

    HINWEIS: Stub-Implementierung.
    Für echte Integration: Nutze Google Drive API und google-auth.
    """

    def __init__(
        self,
        client_name: str = "gdrive",
        credentials_path: Optional[str] = None
    ):
        """
        Initialisiert den Google Drive Client.

        Args:
            client_name: Name des Clients
            credentials_path: Pfad zu Google Credentials JSON
        """
        super().__init__(client_name, credentials_path=credentials_path)

        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH")

        if not self.credentials_path:
            logger.warning("Keine Google Credentials - Client im Stub-Modus")

    def list_resources(self, folder_id: Optional[str] = None, **kwargs) -> List[MCPResource]:
        """Listet Dateien in Google Drive (Stub)."""
        logger.warning("GoogleDriveMCPClient.list_resources() ist ein Stub")
        return []

    def read_resource(self, uri: str, **kwargs) -> MCPOperation:
        """Liest Datei von Google Drive (Stub)."""
        logger.warning("GoogleDriveMCPClient.read_resource() ist ein Stub")
        return MCPOperation(success=False, data=None, error="Stub mode")

    def write_resource(self, uri: str, data: Any, **kwargs) -> MCPOperation:
        """Schreibt Datei zu Google Drive (Stub)."""
        logger.warning("GoogleDriveMCPClient.write_resource() ist ein Stub")
        return MCPOperation(success=False, data=None, error="Stub mode")


# Factory

class MCPClientFactory:
    """Factory für MCP-Clients."""

    @staticmethod
    def create_client(client_type: str, **kwargs) -> MCPClient:
        """
        Erstellt einen MCP-Client.

        Args:
            client_type: Typ des Clients ("filesystem", "github", "vector_store", "gdrive")
            **kwargs: Client-spezifische Parameter

        Returns:
            MCPClient-Instanz
        """
        client_type = client_type.lower()

        if client_type == "filesystem":
            return FilesystemMCPClient(**kwargs)
        elif client_type == "github":
            return GitHubMCPClient(**kwargs)
        elif client_type == "vector_store":
            return VectorStoreMCPClient(**kwargs)
        elif client_type == "gdrive":
            return GoogleDriveMCPClient(**kwargs)
        else:
            raise ValueError(f"Unbekannter Client-Typ: {client_type}")


if __name__ == "__main__":
    # Beispiele
    logging.basicConfig(level=logging.INFO)

    print("=== MCP Clients Beispiele ===\n")

    # Filesystem
    print("1. Filesystem MCP Client:")
    fs_client = FilesystemMCPClient(base_path=".")
    resources = fs_client.list_resources(pattern="*.md")
    print(f"   Gefundene Markdown-Dateien: {len(resources)}")

    # VectorStore (ohne echten Store)
    print("\n2. VectorStore MCP Client:")
    vs_client = VectorStoreMCPClient()
    print(f"   Client Info: {vs_client.get_client_info()}")
