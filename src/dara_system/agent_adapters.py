"""
Agent Adapters Module

Adapter für verschiedene Multi-Agent-Frameworks.
Ermöglicht Integration von DARA-Agenten in unterschiedliche Frameworks.

Primär-Stack: LangGraph (siehe langgraph_orchestrator.py)
Optional: CrewAI, AutoGen, andere Frameworks
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentRole:
    """Definiert eine Agent-Rolle im System."""
    name: str
    description: str
    capabilities: List[str]
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


@dataclass
class AgentTask:
    """Repräsentiert eine Aufgabe für einen Agenten."""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@dataclass
class AgentResult:
    """Repräsentiert das Ergebnis einer Agent-Ausführung."""
    task_id: str
    success: bool
    output_data: Any
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentAdapter(ABC):
    """
    Abstrakte Basisklasse für Agent-Adapter.

    Ermöglicht Integration von DARA-Funktionalität in verschiedene
    Multi-Agent-Frameworks.
    """

    def __init__(self, adapter_name: str, **config):
        """
        Initialisiert den Adapter.

        Args:
            adapter_name: Name des Adapters
            **config: Framework-spezifische Konfiguration
        """
        self.adapter_name = adapter_name
        self.config = config
        logger.info(f"{self.__class__.__name__} '{adapter_name}' initialisiert")

    @abstractmethod
    def register_agent(self, role: AgentRole, executor: Callable) -> bool:
        """
        Registriert einen Agenten im Framework.

        Args:
            role: AgentRole-Definition
            executor: Callable, der die Agent-Logik ausführt

        Returns:
            True bei Erfolg
        """
        pass

    @abstractmethod
    def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Führt eine Aufgabe aus.

        Args:
            task: AgentTask-Objekt

        Returns:
            AgentResult
        """
        pass

    def get_adapter_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über den Adapter zurück.

        Returns:
            Dictionary mit Adapter-Informationen
        """
        return {
            "adapter_name": self.adapter_name,
            "adapter_type": self.__class__.__name__,
            "config": self.config
        }


class LangGraphAdapter(AgentAdapter):
    """
    Adapter für LangGraph (Primär-Framework).

    Wraps DARA-Agenten für LangGraph-Integration.
    """

    def __init__(self, adapter_name: str = "langgraph", **config):
        """
        Initialisiert den LangGraph-Adapter.

        Args:
            adapter_name: Name des Adapters
            **config: LangGraph-spezifische Konfiguration
        """
        super().__init__(adapter_name, **config)
        self.registered_agents: Dict[str, Callable] = {}

    def register_agent(self, role: AgentRole, executor: Callable) -> bool:
        """
        Registriert einen Agenten für LangGraph.

        Args:
            role: AgentRole-Definition
            executor: Callable(input_data, context) -> output_data

        Returns:
            True bei Erfolg
        """
        self.registered_agents[role.name] = {
            "role": role,
            "executor": executor
        }
        logger.info(f"Agent '{role.name}' in LangGraph registriert")
        return True

    def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Führt eine Aufgabe mit dem registrierten Agenten aus.

        Args:
            task: AgentTask-Objekt

        Returns:
            AgentResult
        """
        agent_name = task.task_type

        if agent_name not in self.registered_agents:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=f"Agent '{agent_name}' nicht registriert"
            )

        try:
            agent_info = self.registered_agents[agent_name]
            executor = agent_info["executor"]

            # Führe Agent-Logik aus
            output = executor(task.input_data, task.context or {})

            return AgentResult(
                task_id=task.task_id,
                success=True,
                output_data=output,
                metadata={"framework": "langgraph", "agent": agent_name}
            )

        except Exception as e:
            logger.error(f"Fehler bei Agent-Ausführung '{agent_name}': {e}")
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=str(e)
            )

    def create_node_function(self, role: AgentRole, executor: Callable) -> Callable:
        """
        Erstellt eine LangGraph Node-Funktion aus einem DARA-Agenten.

        Args:
            role: AgentRole
            executor: Agent-Executor

        Returns:
            Funktion, die als LangGraph Node verwendet werden kann
        """
        def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            """LangGraph Node-Funktion."""
            logger.info(f"Executing LangGraph node: {role.name}")

            # Extrahiere Input aus State
            input_data = state.get("input_data", {})
            context = state.get("context", {})

            # Führe Agent aus
            output = executor(input_data, context)

            # Update State
            updated_state = state.copy()
            updated_state[f"{role.name}_output"] = output
            updated_state["last_agent"] = role.name

            return updated_state

        return node_function


class CrewAIAdapter(AgentAdapter):
    """
    Adapter für CrewAI (Optional).

    HINWEIS: Dies ist eine Beispiel-Implementierung.
    Für echte CrewAI-Integration: Installiere crewai-Paket.
    """

    def __init__(self, adapter_name: str = "crewai", **config):
        """Initialisiert den CrewAI-Adapter."""
        super().__init__(adapter_name, **config)
        self.crew_agents: List[Dict[str, Any]] = []

    def register_agent(self, role: AgentRole, executor: Callable) -> bool:
        """
        Registriert einen Agenten für CrewAI.

        Args:
            role: AgentRole
            executor: Agent-Executor

        Returns:
            True bei Erfolg
        """
        # In echter CrewAI: Erstelle crew.Agent-Objekt
        # Hier: Speichere Mapping
        agent_config = {
            "role_name": role.name,
            "description": role.description,
            "capabilities": role.capabilities,
            "executor": executor
        }
        self.crew_agents.append(agent_config)

        logger.info(f"Agent '{role.name}' für CrewAI vorbereitet (Stub)")
        return True

    def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Führt Task im CrewAI-Stil aus (Stub).

        Args:
            task: AgentTask

        Returns:
            AgentResult
        """
        logger.warning("CrewAIAdapter.execute_task() ist ein Stub")

        # Finde passenden Agent
        matching_agent = next(
            (a for a in self.crew_agents if a["role_name"] == task.task_type),
            None
        )

        if not matching_agent:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=f"Kein Agent für '{task.task_type}' gefunden"
            )

        try:
            executor = matching_agent["executor"]
            output = executor(task.input_data, task.context or {})

            return AgentResult(
                task_id=task.task_id,
                success=True,
                output_data=output,
                metadata={"framework": "crewai", "stub": True}
            )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=str(e)
            )


class AutoGenAdapter(AgentAdapter):
    """
    Adapter für Microsoft AutoGen (Optional, Stub).

    HINWEIS: Beispiel-Implementierung.
    Für echte AutoGen-Integration: Installiere pyautogen.
    """

    def __init__(self, adapter_name: str = "autogen", **config):
        """Initialisiert den AutoGen-Adapter."""
        super().__init__(adapter_name, **config)
        self.autogen_agents: Dict[str, Any] = {}

    def register_agent(self, role: AgentRole, executor: Callable) -> bool:
        """Registriert Agent für AutoGen (Stub)."""
        self.autogen_agents[role.name] = {
            "role": role,
            "executor": executor
        }
        logger.info(f"Agent '{role.name}' für AutoGen vorbereitet (Stub)")
        return True

    def execute_task(self, task: AgentTask) -> AgentResult:
        """Führt Task im AutoGen-Stil aus (Stub)."""
        logger.warning("AutoGenAdapter.execute_task() ist ein Stub")

        if task.task_type not in self.autogen_agents:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=f"Agent '{task.task_type}' nicht gefunden"
            )

        try:
            agent_info = self.autogen_agents[task.task_type]
            executor = agent_info["executor"]
            output = executor(task.input_data, task.context or {})

            return AgentResult(
                task_id=task.task_id,
                success=True,
                output_data=output,
                metadata={"framework": "autogen", "stub": True}
            )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output_data=None,
                error=str(e)
            )


# Helper-Funktionen für DARA-Agenten

def create_process_analysis_executor():
    """
    Erstellt einen Executor für den Process Analysis Agent.

    Returns:
        Callable, der mit AgentAdapters verwendet werden kann
    """
    from .process_analysis_agent import ProcessAnalysisAgent

    def executor(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Prozessanalyse durch.

        Args:
            input_data: Dictionary mit 'aggregated_slices', 'primary_field'
            context: Zusätzlicher Kontext

        Returns:
            Dictionary mit Analyse-Ergebnissen
        """
        aggregated_slices = input_data.get("aggregated_slices", [])
        primary_field = input_data.get("primary_field", "value")

        # Konfiguration aus Context oder Defaults
        baseline_threshold = context.get("baseline_threshold", 0.3)
        peak_threshold = context.get("peak_threshold", 0.8)

        # Erstelle Agent
        agent = ProcessAnalysisAgent(
            baseline_threshold=baseline_threshold,
            peak_threshold=peak_threshold
        )

        # Führe Analyse durch
        analysis = agent.analyze_aggregated_slices(aggregated_slices, primary_field)

        return {
            "summary": analysis.summary,
            "patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "time_range": p.time_range
                }
                for p in analysis.patterns
            ],
            "metrics": analysis.metrics
        }

    return executor


def create_reporting_executor(reporter_type: str = "notion"):
    """
    Erstellt einen Executor für Reporter-Agenten.

    Args:
        reporter_type: "notion" oder "gdrive"

    Returns:
        Callable für Reporter
    """
    if reporter_type == "notion":
        from .notion_reporter import NotionReporter
        reporter = NotionReporter()
    elif reporter_type == "gdrive":
        from .gdrive_reporter import GDriveReporter
        reporter = GDriveReporter()
    else:
        raise ValueError(f"Unbekannter Reporter-Typ: {reporter_type}")

    def executor(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erstellt Report.

        Args:
            input_data: Dictionary mit 'analysis' und 'title'
            context: Zusätzlicher Kontext

        Returns:
            Dictionary mit Report-Informationen
        """
        analysis = input_data.get("analysis")
        title = input_data.get("title", "DARA Report")

        if reporter_type == "notion":
            result = reporter.send_analysis_report(analysis, title=title)
        else:  # gdrive
            result = reporter.create_doc_report(analysis, title=title)

        return {
            "success": result.get("success", False),
            "reporter_type": reporter_type,
            "output": result
        }

    return executor


# Factory

class AgentAdapterFactory:
    """Factory für Agent-Adapter."""

    @staticmethod
    def create_adapter(framework: str, **config) -> AgentAdapter:
        """
        Erstellt einen Agent-Adapter.

        Args:
            framework: Framework-Name ("langgraph", "crewai", "autogen")
            **config: Framework-spezifische Konfiguration

        Returns:
            AgentAdapter-Instanz
        """
        framework = framework.lower()

        if framework == "langgraph":
            return LangGraphAdapter(**config)
        elif framework == "crewai":
            return CrewAIAdapter(**config)
        elif framework == "autogen":
            return AutoGenAdapter(**config)
        else:
            raise ValueError(f"Unbekanntes Framework: {framework}")


if __name__ == "__main__":
    # Beispiele
    logging.basicConfig(level=logging.INFO)

    print("=== Agent Adapters Beispiele ===\n")

    # LangGraph Adapter
    print("1. LangGraph Adapter:")
    lg_adapter = LangGraphAdapter()

    # Definiere Agent-Rolle
    analysis_role = AgentRole(
        name="process_analysis",
        description="Analysiert DARA-Prozessdaten",
        capabilities=["pattern_recognition", "anomaly_detection"]
    )

    # Registriere Agent
    executor = create_process_analysis_executor()
    lg_adapter.register_agent(analysis_role, executor)

    print(f"   Adapter Info: {lg_adapter.get_adapter_info()}\n")

    # CrewAI Adapter
    print("2. CrewAI Adapter:")
    crew_adapter = CrewAIAdapter()
    crew_adapter.register_agent(analysis_role, executor)
    print(f"   Registrierte Agents: {len(crew_adapter.crew_agents)}\n")

    # Factory
    print("3. Via Factory:")
    adapter = AgentAdapterFactory.create_adapter("langgraph")
    print(f"   Erstellt: {adapter.__class__.__name__}")
