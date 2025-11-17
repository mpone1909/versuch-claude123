# MCP-Integration

Model Context Protocol (MCP) Integration im DARA-System.

## Übersicht

Das DARA-System bietet MCP-ähnliche Schnittstellen für den Zugriff auf verschiedene Ressourcen:

- **Filesystem**: Zugriff auf lokale Dateien
- **GitHub**: Repository-Operationen (Stub)
- **Vector Store**: Vektor-Datenbank-Operationen
- **Google Drive**: Cloud-Speicher (Stub)

**Wichtig**: Die aktuelle Implementierung bietet MCP-ähnliche Interfaces, die auch ohne echte MCP-Server lauffähig sind. Für vollständige MCP-Integration können die Clients später mit echten MCP-Servern verbunden werden.

## Module

### `mcp_clients.py`

Enthält MCP-Client-Implementierungen für verschiedene Ressourcentypen.

## Verfügbare Clients

### 1. FilesystemMCPClient

Ermöglicht MCP-ähnlichen Zugriff auf das Dateisystem.

#### Verwendung

```python
from dara_system.mcp_clients import FilesystemMCPClient

# Erstelle Client
client = FilesystemMCPClient(
    base_path="data",
    allowed_extensions=[".csv", ".txt", ".json"]
)

# Liste Ressourcen
resources = client.list_resources(pattern="**/*.csv")
for resource in resources:
    print(f"URI: {resource.uri}")
    print(f"Name: {resource.name}")
    print(f"Type: {resource.resource_type}")

# Lese Datei
result = client.read_resource("file://data/proband_1.csv")
if result.success:
    content = result.data
    print(content)

# Schreibe Datei
result = client.write_resource(
    uri="file://output/report.txt",
    data="Experiment-Ergebnis..."
)
```

#### Features

- Glob-Pattern-Suche
- Filter nach Dateiendungen
- Automatisches Erstellen von Verzeichnissen
- Metadata (Dateigröße, Pfad, etc.)

### 2. VectorStoreMCPClient

Ermöglicht MCP-ähnlichen Zugriff auf den Vector Store.

#### Verwendung

```python
from dara_system.mcp_clients import VectorStoreMCPClient
from dara_system.vector_store import InMemoryVectorStore

# Erstelle Vector Store
vector_store = InMemoryVectorStore(embedding_dim=384)

# Erstelle MCP-Client
client = VectorStoreMCPClient(vector_store_instance=vector_store)

# Liste Vektoren
resources = client.list_resources()
for resource in resources:
    print(f"Vector ID: {resource.name}")
    print(f"Metadata: {resource.metadata}")

# Lese Vektor
result = client.read_resource("vector://some-id")
if result.success:
    vector_data = result.data
    print(f"Vector: {vector_data['vector'][:5]}...")
    print(f"Text: {vector_data['text']}")

# Schreibe Vektor
result = client.write_resource(
    uri="vector://new-entry",
    data={
        "vector": [0.1, 0.2, 0.3, ...],  # 384-dim
        "text": "Example text",
        "metadata": {"source": "experiment_1"}
    }
)
```

### 3. GitHubMCPClient (Stub)

**Status**: Stub-Implementierung

Für echte GitHub-Integration:
- Installiere `PyGithub`: `pip install PyGithub`
- Setze `GITHUB_TOKEN` Umgebungsvariable
- Erweitere die Stub-Implementierung

```python
from dara_system.mcp_clients import GitHubMCPClient

client = GitHubMCPClient(
    repo_owner="mpone1909",
    repo_name="versuch-claude123",
    access_token="your_token_here"
)

# Stub-Operationen (noch nicht voll funktional)
resources = client.list_resources()
```

### 4. GoogleDriveMCPClient (Stub)

**Status**: Stub-Implementierung

Für echte Google Drive-Integration:
- Installiere `google-auth` und `google-api-python-client`
- Erstelle Google Cloud Projekt und Credentials
- Setze `GOOGLE_CREDENTIALS_PATH`
- Erweitere die Stub-Implementierung

```python
from dara_system.mcp_clients import GoogleDriveMCPClient

client = GoogleDriveMCPClient(
    credentials_path="/path/to/credentials.json"
)

# Stub-Operationen
resources = client.list_resources(folder_id="your_folder_id")
```

## MCP-Client Factory

Für einfache Client-Erstellung:

```python
from dara_system.mcp_clients import MCPClientFactory

# Erstelle Filesystem-Client
fs_client = MCPClientFactory.create_client(
    "filesystem",
    base_path="data"
)

# Erstelle VectorStore-Client
vs_client = MCPClientFactory.create_client(
    "vector_store",
    vector_store_instance=my_vector_store
)
```

## Abstrakte Schnittstelle

Alle MCP-Clients implementieren die abstrakte `MCPClient`-Basisklasse:

```python
from abc import ABC, abstractmethod

class MCPClient(ABC):
    @abstractmethod
    def list_resources(self, **kwargs) -> List[MCPResource]:
        """Listet verfügbare Ressourcen auf."""
        pass

    @abstractmethod
    def read_resource(self, uri: str, **kwargs) -> MCPOperation:
        """Liest eine Ressource."""
        pass

    @abstractmethod
    def write_resource(self, uri: str, data: Any, **kwargs) -> MCPOperation:
        """Schreibt/aktualisiert eine Ressource."""
        pass
```

## Integration in DARA-Workflows

### Beispiel: Filesystem-Client in Orchestrator

```python
from dara_system.langgraph_orchestrator import LangGraphOrchestrator
from dara_system.mcp_clients import FilesystemMCPClient

# Erstelle Client
fs_client = FilesystemMCPClient(base_path="data/experiments")

# Finde CSV-Dateien
csv_resources = fs_client.list_resources(pattern="proband_*.csv")
csv_paths = [r.uri.replace("file://", "") for r in csv_resources]

# Nutze in Orchestrator
orchestrator = LangGraphOrchestrator(config)
results = orchestrator.run_pipeline(
    csv_file_paths=csv_paths,
    proband_ids=["P1", "P2", "P3"]
)

# Schreibe Ergebnisse mit MCP-Client
output_client = FilesystemMCPClient(base_path="results")
output_client.write_resource(
    uri="file://experiment_results.json",
    data=json.dumps(results, indent=2)
)
```

### Beispiel: Vector Store Integration

```python
from dara_system.vector_store import InMemoryVectorStore
from dara_system.mcp_clients import VectorStoreMCPClient
from dara_system.embeddings import EmbeddingProvider

# Setup
vector_store = InMemoryVectorStore(embedding_dim=384)
mcp_client = VectorStoreMCPClient(vector_store_instance=vector_store)
embedding_provider = EmbeddingProvider(embedding_dim=384)

# Texte einbetten und speichern
texts = ["DARA Proband 1 Analyse", "DARA Proband 2 Analyse"]
embeddings = embedding_provider.get_embeddings(texts)

for i, (text, embedding) in enumerate(zip(texts, embeddings)):
    mcp_client.write_resource(
        uri=f"vector://analysis_{i}",
        data={
            "vector": embedding,
            "text": text,
            "metadata": {"proband": i+1}
        }
    )

# Später: Suche via Vector Store
query_text = "Proband Analyse"
query_embedding = embedding_provider.get_embeddings([query_text])[0]
results = vector_store.similarity_search(query_embedding, k=2)
```

## Konfiguration

MCP-Features können via `.env` aktiviert/deaktiviert werden:

```bash
# In .env
MCP_ENABLED=false
MCP_SERVER_URL=http://localhost:3000

# GitHub
GITHUB_TOKEN=your_github_token

# Google Drive
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
GDRIVE_FOLDER_ID=your_folder_id
```

## Echte MCP-Server-Integration (Zukünftig)

Für die Integration mit echten MCP-Servern:

### 1. MCP-Server starten

```bash
# Beispiel: Filesystem MCP Server
npx @modelcontextprotocol/server-filesystem /path/to/data
```

### 2. Client-Implementierung erweitern

```python
# Zukünftige Implementierung
class RemoteMCPClient(MCPClient):
    def __init__(self, server_url: str):
        self.server_url = server_url
        # Verbinde zu MCP-Server via WebSocket/HTTP
        self.connection = connect_to_mcp_server(server_url)

    def list_resources(self, **kwargs):
        # Sende MCP-Request an Server
        response = self.connection.send({
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": kwargs
        })
        return parse_mcp_response(response)
```

### 3. Konfiguration

```python
from dara_system.config import get_config

config = get_config()

if config.mcp.enabled:
    # Nutze Remote-MCP-Client
    client = RemoteMCPClient(config.mcp.server_url)
else:
    # Nutze lokale Implementierung
    client = FilesystemMCPClient()
```

## Best Practices

### 1. Error Handling

Prüfe immer `MCPOperation.success`:

```python
result = client.read_resource(uri)
if result.success:
    data = result.data
else:
    logger.error(f"Fehler: {result.error}")
```

### 2. URI-Format

Nutze konsistente URI-Formate:

- Filesystem: `file:///absolute/path` oder `file://relative/path`
- Vector Store: `vector://entry-id`
- GitHub: `github://owner/repo/path`
- Google Drive: `gdrive://file-id`

### 3. Metadata nutzen

Nutze Metadata für Kontext:

```python
result = client.write_resource(
    uri="file://output.json",
    data=json_data,
    metadata={"experiment": "exp_001", "timestamp": "2024-01-15"}
)
```

## Troubleshooting

### Problem: "Kein Vector Store verfügbar"

**Lösung**: Übergebe Vector Store-Instanz an Client:

```python
from dara_system.vector_store import InMemoryVectorStore

store = InMemoryVectorStore(embedding_dim=384)
client = VectorStoreMCPClient(vector_store_instance=store)
```

### Problem: GitHub-/GDrive-Clients sind Stubs

**Lösung**: Diese Clients sind als Placeholder implementiert. Für echte Integration:
1. Installiere entsprechende Packages
2. Konfiguriere Credentials
3. Erweitere die Implementierung in `mcp_clients.py`

### Problem: Dateien werden nicht gefunden

**Lösung**: Prüfe `base_path` und verwende absolute oder korrekte relative Pfade:

```python
from pathlib import Path

base_path = Path(__file__).parent.parent / "data"
client = FilesystemMCPClient(base_path=str(base_path))
```

## Siehe auch

- [ARCHITECTURE.md](ARCHITECTURE.md) für System-Überblick
- [CONFIG.md](CONFIG.md) für Konfigurationsdetails
- `src/dara_system/mcp_clients.py` für Implementierung
