# Agent-Frameworks Integration

Multi-Agent-Framework-Integration im DARA-System.

## Übersicht

Das DARA-System ist primär auf **LangGraph** ausgerichtet, bietet aber auch Adapter für andere Multi-Agent-Frameworks:

- **LangGraph** (Primär-Stack): Vollständig implementiert
- **CrewAI** (Optional): Adapter-Implementierung
- **AutoGen** (Optional): Adapter-Implementierung

## Architektur

### Kern-Komponenten

1. **Agent Roles**: Definieren Agent-Funktionen und Capabilities
2. **Agent Tasks**: Repräsentieren Aufgaben für Agenten
3. **Agent Results**: Standardisierte Ergebnis-Struktur
4. **Agent Adapters**: Framework-spezifische Wrapper

### Abstrakte Agent-Schnittstelle

Alle Framework-Adapter implementieren die `AgentAdapter`-Basisklasse:

```python
class AgentAdapter(ABC):
    @abstractmethod
    def register_agent(self, role: AgentRole, executor: Callable) -> bool:
        """Registriert einen Agenten im Framework."""
        pass

    @abstractmethod
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Führt eine Aufgabe aus."""
        pass
```

## 1. LangGraph (Primär-Framework)

### Übersicht

LangGraph ist das primäre Framework für Orchestrierung im DARA-System.

Siehe auch: `src/dara_system/langgraph_orchestrator.py`

### Verwendung mit Adapter

```python
from dara_system.agent_adapters import (
    LangGraphAdapter,
    AgentRole,
    AgentTask,
    create_process_analysis_executor
)

# Erstelle Adapter
adapter = LangGraphAdapter()

# Definiere Agent-Rolle
analysis_role = AgentRole(
    name="process_analysis",
    description="Analysiert DARA-Prozessdaten",
    capabilities=["pattern_recognition", "anomaly_detection"]
)

# Erstelle Executor
executor = create_process_analysis_executor()

# Registriere Agent
adapter.register_agent(analysis_role, executor)

# Führe Task aus
task = AgentTask(
    task_id="task_001",
    task_type="process_analysis",
    description="Analysiere Proband 1-3",
    input_data={
        "aggregated_slices": [...],
        "primary_field": "value"
    },
    context={
        "baseline_threshold": 0.3,
        "peak_threshold": 0.8
    }
)

result = adapter.execute_task(task)
if result.success:
    print(result.output_data)
```

### LangGraph Node-Funktionen erstellen

Der Adapter kann DARA-Agenten in LangGraph-Nodes konvertieren:

```python
# Erstelle Node-Funktion
node_function = adapter.create_node_function(
    role=analysis_role,
    executor=executor
)

# Nutze in LangGraph
from langgraph.graph import StateGraph

workflow = StateGraph(state_schema)
workflow.add_node("process_analysis", node_function)
workflow.add_edge("load_data", "process_analysis")
```

### Vollständiges LangGraph-Beispiel

```python
from dara_system.langgraph_orchestrator import (
    LangGraphOrchestrator,
    OrchestratorConfig
)

# Konfiguration
config = OrchestratorConfig(
    primary_field="value",
    baseline_threshold=0.3,
    peak_threshold=0.8,
    create_notion_report=False
)

# Orchestrator erstellen
orchestrator = LangGraphOrchestrator(config)

# Pipeline ausführen
results = orchestrator.run_pipeline(
    csv_file_paths=["data/p1.csv", "data/p2.csv"],
    proband_ids=["P1", "P2"]
)
```

## 2. CrewAI (Optional)

### Status

**Adapter-Implementierung verfügbar** (Stub-Modus)

Für vollständige CrewAI-Integration:
1. Installiere: `pip install crewai`
2. Erweitere `CrewAIAdapter` in `agent_adapters.py`

### Verwendung

```python
from dara_system.agent_adapters import (
    CrewAIAdapter,
    AgentRole,
    create_process_analysis_executor,
    create_reporting_executor
)

# Erstelle Adapter
crew_adapter = CrewAIAdapter()

# Definiere Agent-Rollen
analysis_role = AgentRole(
    name="analyst",
    description="Analysiert DARA-Daten und erkennt Muster",
    capabilities=["data_analysis", "pattern_recognition"]
)

reporter_role = AgentRole(
    name="reporter",
    description="Erstellt Berichte aus Analyse-Ergebnissen",
    capabilities=["report_generation", "visualization"]
)

# Registriere Agenten
crew_adapter.register_agent(analysis_role, create_process_analysis_executor())
crew_adapter.register_agent(reporter_role, create_reporting_executor("notion"))

# Führe Tasks aus
analysis_task = AgentTask(
    task_id="analyze_001",
    task_type="analyst",
    description="Analysiere Experiment-Daten",
    input_data={...}
)

result = crew_adapter.execute_task(analysis_task)
```

### Echte CrewAI-Integration (Zukünftig)

```python
# Beispiel für echte CrewAI-Integration
from crewai import Agent, Task, Crew

# Erstelle CrewAI-Agenten
analyst_agent = Agent(
    role="DARA Data Analyst",
    goal="Analyze process data and identify patterns",
    backstory="Expert in DARA research data analysis",
    tools=[...]  # DARA-spezifische Tools
)

reporter_agent = Agent(
    role="Report Generator",
    goal="Create comprehensive reports",
    backstory="Technical writer specialized in research reports",
    tools=[...]
)

# Definiere Tasks
analysis_task = Task(
    description="Analyze synchronized CSV data from 3 probands",
    agent=analyst_agent
)

# Erstelle Crew
crew = Crew(
    agents=[analyst_agent, reporter_agent],
    tasks=[analysis_task, ...]
)

# Führe aus
result = crew.kickoff()
```

## 3. AutoGen (Optional)

### Status

**Adapter-Implementierung verfügbar** (Stub-Modus)

Für vollständige AutoGen-Integration:
1. Installiere: `pip install pyautogen`
2. Erweitere `AutoGenAdapter` in `agent_adapters.py`

### Verwendung

```python
from dara_system.agent_adapters import (
    AutoGenAdapter,
    AgentRole,
    create_process_analysis_executor
)

# Erstelle Adapter
autogen_adapter = AutoGenAdapter()

# Definiere Agent
analysis_role = AgentRole(
    name="dara_analyst",
    description="DARA Process Analyst",
    capabilities=["analysis", "reporting"]
)

# Registriere
autogen_adapter.register_agent(analysis_role, create_process_analysis_executor())

# Führe aus
task = AgentTask(
    task_id="autogen_001",
    task_type="dara_analyst",
    description="Analyze data",
    input_data={...}
)

result = autogen_adapter.execute_task(task)
```

### Echte AutoGen-Integration (Zukünftig)

```python
# Beispiel für echte AutoGen-Integration
import autogen

# Konfiguriere LLM
config_list = [{
    "model": "gpt-4",
    "api_key": "..."
}]

# Erstelle Agenten
analyst = autogen.AssistantAgent(
    name="analyst",
    llm_config={"config_list": config_list},
    system_message="You are a DARA data analyst..."
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER"
)

# Konversation
user_proxy.initiate_chat(
    analyst,
    message="Analyze the DARA experiment data..."
)
```

## Agent-Executor-Funktionen

### Vordefinierte Executors

Das System bietet vordefinierte Executor-Funktionen für DARA-Agenten:

#### 1. Process Analysis Executor

```python
from dara_system.agent_adapters import create_process_analysis_executor

executor = create_process_analysis_executor()

# Verwendung
output = executor(
    input_data={
        "aggregated_slices": [...],
        "primary_field": "value"
    },
    context={
        "baseline_threshold": 0.3,
        "peak_threshold": 0.8
    }
)

# Output: Dictionary mit 'summary', 'patterns', 'metrics'
```

#### 2. Reporting Executor

```python
from dara_system.agent_adapters import create_reporting_executor

# Notion Reporter
notion_executor = create_reporting_executor("notion")

# Google Drive Reporter
gdrive_executor = create_reporting_executor("gdrive")

# Verwendung
output = notion_executor(
    input_data={
        "analysis": analysis_result,
        "title": "DARA Experiment Report"
    },
    context={}
)
```

### Custom Executors erstellen

```python
def create_custom_executor():
    """Erstellt einen custom Agent-Executor."""

    def executor(input_data: dict, context: dict) -> dict:
        # Deine Agent-Logik hier
        data = input_data.get("data")

        # Verarbeitung
        result = process_data(data)

        return {
            "result": result,
            "metadata": {"processed": True}
        }

    return executor
```

## Framework-Auswahl

### Wann welches Framework?

#### LangGraph

**✅ Verwende LangGraph wenn**:
- State-basierte Orchestrierung benötigt wird
- Komplexe Workflows mit Conditional Branching
- Integration mit LangChain-Tools
- Streaming-Outputs erforderlich

**Beispiel-Use-Cases**:
- DARA End-to-End-Pipeline (Load → Aggregate → Analyze → Report)
- Multi-Step-Analysen mit Zwischenergebnissen
- Error-Handling und Retries

#### CrewAI

**✅ Verwende CrewAI wenn**:
- Rollenbasierte Agent-Zusammenarbeit
- Task-Delegation zwischen Agenten
- Hierarchische Agent-Strukturen
- LLM-basierte Agent-Kommunikation

**Beispiel-Use-Cases**:
- Multi-Agent-Analysen (verschiedene Analyseperspektiven)
- Kollaborative Report-Erstellung
- Research-Workflows mit mehreren Spezialisten

#### AutoGen

**✅ Verwende AutoGen wenn**:
- Konversations-basierte Workflows
- Human-in-the-Loop-Szenarien
- Code-Generierung und -Ausführung
- Iterative Problem-Lösung

**Beispiel-Use-Cases**:
- Interaktive Datenexploration
- Experimentelle Analyse-Scripts generieren
- Debugging und Optimierung

## Adapter-Factory

Einfache Erstellung von Adaptern:

```python
from dara_system.agent_adapters import AgentAdapterFactory

# LangGraph
lg_adapter = AgentAdapterFactory.create_adapter("langgraph")

# CrewAI
crew_adapter = AgentAdapterFactory.create_adapter("crewai")

# AutoGen
autogen_adapter = AgentAdapterFactory.create_adapter("autogen")
```

## Best Practices

### 1. Framework-Konsistenz

Nutze primär ein Framework pro Experiment:

```python
# ✅ Gut: Ein Framework
orchestrator = LangGraphOrchestrator(config)
results = orchestrator.run_pipeline(...)

# ❌ Vermeiden: Framework-Mischung in einem Workflow
```

### 2. Executor-Wiederverwendung

Definiere Executors einmal, nutze sie in mehreren Frameworks:

```python
# Definiere einmal
analysis_executor = create_process_analysis_executor()

# Nutze in verschiedenen Frameworks
lg_adapter.register_agent(role, analysis_executor)
crew_adapter.register_agent(role, analysis_executor)
```

### 3. Error-Handling

Prüfe immer `AgentResult.success`:

```python
result = adapter.execute_task(task)
if result.success:
    process_output(result.output_data)
else:
    logger.error(f"Task failed: {result.error}")
```

### 4. Kontext nutzen

Übergebe Konfiguration via `context`:

```python
task = AgentTask(
    task_id="...",
    task_type="...",
    input_data={...},
    context={
        "baseline_threshold": 0.3,
        "peak_threshold": 0.8,
        "experiment_id": "exp_001"
    }
)
```

## Troubleshooting

### Problem: "Agent nicht registriert"

**Lösung**: Registriere Agent vor Ausführung:

```python
adapter.register_agent(role, executor)
# DANN
result = adapter.execute_task(task)
```

### Problem: Framework-spezifische Features fehlen

**Lösung**: Die Adapter bieten Basislogik. Für vollständige Framework-Features:
1. Installiere Framework-Package
2. Erweitere Adapter-Implementierung
3. Nutze Framework direkt statt Adapter

### Problem: Executor gibt falsches Format zurück

**Lösung**: Executors sollten Dictionaries zurückgeben:

```python
def executor(input_data, context):
    # ✅ Richtig
    return {"result": ..., "metadata": ...}

    # ❌ Falsch
    return some_object  # Kein dict
```

## Siehe auch

- [ARCHITECTURE.md](ARCHITECTURE.md) für System-Überblick
- [AGENTS.md](AGENTS.md) für Agent-Beschreibungen
- `src/dara_system/agent_adapters.py` für Implementierung
- `src/dara_system/langgraph_orchestrator.py` für LangGraph-Orchestrator
