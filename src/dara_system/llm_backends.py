"""
LLM Backends Module

Abstraktion für verschiedene LLM-Backends (lokal, Cloud, Fake für Tests).
Ermöglicht flexible Integration verschiedener LLM-Anbieter.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Repräsentiert eine Nachricht in einem Chat-Dialog."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Repräsentiert eine LLM-Antwort."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMBackendError(Exception):
    """Fehler bei LLM-Backend-Operationen."""
    pass


class LLMBackend(ABC):
    """
    Abstrakte Basisklasse für LLM-Backends.

    Definiert die Schnittstelle, die alle LLM-Backends implementieren müssen.
    """

    def __init__(self, model_name: str, **kwargs):
        """
        Initialisiert das Backend.

        Args:
            model_name: Name/ID des zu verwendenden Modells
            **kwargs: Backend-spezifische Parameter
        """
        self.model_name = model_name
        self.config = kwargs
        logger.info(f"{self.__class__.__name__} initialisiert: {model_name}")

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generiert eine Antwort auf einen Prompt.

        Args:
            prompt: Eingabe-Prompt
            **kwargs: Weitere Parameter (temperature, max_tokens, etc.)

        Returns:
            LLMResponse-Objekt

        Raises:
            LLMBackendError: Bei Fehlern in der Generierung
        """
        pass

    @abstractmethod
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Führt eine Chat-Konversation durch.

        Args:
            messages: Liste von LLMMessage-Objekten
            **kwargs: Weitere Parameter

        Returns:
            LLMResponse-Objekt

        Raises:
            LLMBackendError: Bei Fehlern
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über das Modell zurück.

        Returns:
            Dictionary mit Modell-Informationen
        """
        return {
            "model_name": self.model_name,
            "backend_type": self.__class__.__name__,
            "config": self.config
        }


class FakeLLMBackend(LLMBackend):
    """
    Fake-Backend für Tests und Entwicklung.

    Generiert deterministische, einfache Antworten ohne echtes LLM.
    """

    def __init__(self, model_name: str = "fake-model", response_template: Optional[str] = None):
        """
        Initialisiert das Fake-Backend.

        Args:
            model_name: Name des Fake-Modells
            response_template: Template für Antworten (default: einfache Echo-Antwort)
        """
        super().__init__(model_name)
        self.response_template = response_template or "Fake response to: {prompt}"

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generiert eine Fake-Antwort."""
        content = self.response_template.format(prompt=prompt[:100])

        return LLMResponse(
            content=content,
            model=self.model_name,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(content)},
            metadata={"backend": "fake"}
        )

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Führt einen Fake-Chat durch."""
        last_user_message = next(
            (msg.content for msg in reversed(messages) if msg.role == "user"),
            "No user message"
        )

        content = self.response_template.format(prompt=last_user_message[:100])

        return LLMResponse(
            content=content,
            model=self.model_name,
            usage={"prompt_tokens": sum(len(m.content) for m in messages), "completion_tokens": len(content)},
            metadata={"backend": "fake", "num_messages": len(messages)}
        )


class LocalHTTPBackend(LLMBackend):
    """
    Backend für lokale LLM-Server (z.B. llama.cpp, text-generation-webui, etc.).

    Kommuniziert via HTTP mit einem lokal laufenden LLM-Server.
    """

    def __init__(
        self,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialisiert das Local HTTP Backend.

        Args:
            model_name: Name des Modells
            base_url: URL des lokalen Servers (default: aus Umgebungsvariable LLM_BACKEND_URL)
            api_key: Optional, API-Key für den Server
            **kwargs: Weitere Parameter
        """
        super().__init__(model_name, **kwargs)

        self.base_url = base_url or os.getenv("LLM_BACKEND_URL", "http://localhost:8080")
        self.api_key = api_key or os.getenv("LLM_API_KEY")

        logger.info(f"LocalHTTPBackend konfiguriert für: {self.base_url}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generiert eine Antwort via lokaler HTTP-API.

        HINWEIS: Dies ist eine Stub-Implementierung!
        In Produktion: Implementiere echte HTTP-Requests mit requests/httpx.
        """
        logger.warning("LocalHTTPBackend.generate() ist ein Stub - keine echte HTTP-Kommunikation")

        # Stub-Implementierung (für echte Nutzung: HTTP POST-Request)
        response_content = f"[LOCAL LLM RESPONSE] Generated for prompt: {prompt[:50]}..."

        return LLMResponse(
            content=response_content,
            model=self.model_name,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(response_content)},
            metadata={
                "backend": "local_http",
                "base_url": self.base_url,
                "stub": True
            }
        )

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Führt Chat via lokaler HTTP-API durch.

        HINWEIS: Stub-Implementierung.
        """
        logger.warning("LocalHTTPBackend.chat() ist ein Stub")

        last_user_message = next(
            (msg.content for msg in reversed(messages) if msg.role == "user"),
            "No message"
        )

        response_content = f"[LOCAL LLM CHAT] Response to: {last_user_message[:50]}..."

        return LLMResponse(
            content=response_content,
            model=self.model_name,
            metadata={"backend": "local_http", "stub": True}
        )

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hilfsfunktion für HTTP-Requests (Stub).

        In Produktion: Implementiere mit requests/httpx:
            import requests
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = requests.post(f"{self.base_url}/{endpoint}", json=payload, headers=headers)
            return response.json()
        """
        raise NotImplementedError("HTTP-Requests sind in dieser Stub-Version nicht implementiert")


class CloudBackend(LLMBackend):
    """
    Backend für Cloud-LLM-APIs (OpenAI, Anthropic, etc.).

    HINWEIS: Dies ist eine Placeholder-Implementierung.
    Für echte Cloud-APIs: Nutze offizielle SDKs (openai, anthropic, etc.).
    """

    def __init__(
        self,
        model_name: str,
        provider: str = "openai",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialisiert das Cloud Backend.

        Args:
            model_name: Name des Cloud-Modells
            provider: Cloud-Provider ("openai", "anthropic", etc.)
            api_key: API-Key (default: aus Umgebungsvariablen)
            **kwargs: Weitere Parameter
        """
        super().__init__(model_name, **kwargs)

        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if not self.api_key:
            logger.warning(f"Kein API-Key für {provider} gefunden - Backend im Stub-Modus")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generiert via Cloud-API.

        HINWEIS: Stub-Implementierung.
        """
        logger.warning("CloudBackend.generate() ist ein Stub")

        response_content = f"[CLOUD {self.provider.upper()} RESPONSE] For: {prompt[:50]}..."

        return LLMResponse(
            content=response_content,
            model=self.model_name,
            metadata={"backend": "cloud", "provider": self.provider, "stub": True}
        )

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Chat via Cloud-API.

        HINWEIS: Stub-Implementierung.
        """
        logger.warning("CloudBackend.chat() ist ein Stub")

        last_msg = messages[-1].content if messages else "No message"
        response_content = f"[CLOUD {self.provider.upper()} CHAT] Response to: {last_msg[:50]}..."

        return LLMResponse(
            content=response_content,
            model=self.model_name,
            metadata={"backend": "cloud", "provider": self.provider, "stub": True}
        )


class LLMBackendFactory:
    """
    Factory für LLM-Backends.

    Ermöglicht einfache Erstellung von Backends basierend auf Konfiguration.
    """

    @staticmethod
    def create_backend(
        backend_type: str,
        model_name: str,
        **kwargs
    ) -> LLMBackend:
        """
        Erstellt ein LLM-Backend.

        Args:
            backend_type: Typ des Backends ("fake", "local_http", "cloud")
            model_name: Name des Modells
            **kwargs: Backend-spezifische Parameter

        Returns:
            LLMBackend-Instanz

        Raises:
            ValueError: Bei unbekanntem Backend-Typ
        """
        backend_type = backend_type.lower()

        if backend_type == "fake":
            return FakeLLMBackend(model_name, **kwargs)
        elif backend_type == "local_http":
            return LocalHTTPBackend(model_name, **kwargs)
        elif backend_type == "cloud":
            return CloudBackend(model_name, **kwargs)
        else:
            raise ValueError(f"Unbekannter Backend-Typ: {backend_type}")

    @staticmethod
    def create_from_config(config_dict: Dict[str, Any]) -> LLMBackend:
        """
        Erstellt Backend aus Konfigurations-Dictionary.

        Args:
            config_dict: Dictionary mit Backend-Konfiguration
                Beispiel: {"type": "fake", "model_name": "test-model"}

        Returns:
            LLMBackend-Instanz
        """
        backend_type = config_dict.pop("type", "fake")
        model_name = config_dict.pop("model_name", "default-model")

        return LLMBackendFactory.create_backend(backend_type, model_name, **config_dict)


# Helper-Funktionen

def get_default_backend() -> LLMBackend:
    """
    Gibt ein Default-Backend zurück (Fake für Tests).

    Returns:
        FakeLLMBackend-Instanz
    """
    return FakeLLMBackend()


def create_backend_from_env() -> LLMBackend:
    """
    Erstellt Backend basierend auf Umgebungsvariablen.

    Umgebungsvariablen:
        LLM_BACKEND_TYPE: "fake", "local_http", oder "cloud"
        LLM_MODEL_NAME: Name des Modells
        LLM_BACKEND_URL: URL für local_http
        LLM_PROVIDER: Provider für cloud (openai, anthropic, etc.)

    Returns:
        LLMBackend-Instanz
    """
    backend_type = os.getenv("LLM_BACKEND_TYPE", "fake")
    model_name = os.getenv("LLM_MODEL_NAME", "default-model")

    kwargs = {}
    if backend_type == "local_http":
        kwargs["base_url"] = os.getenv("LLM_BACKEND_URL")
    elif backend_type == "cloud":
        kwargs["provider"] = os.getenv("LLM_PROVIDER", "openai")

    return LLMBackendFactory.create_backend(backend_type, model_name, **kwargs)


if __name__ == "__main__":
    # Beispiele
    logging.basicConfig(level=logging.INFO)

    print("=== LLM Backend Beispiele ===\n")

    # Fake Backend
    print("1. Fake Backend:")
    fake_backend = FakeLLMBackend()
    response = fake_backend.generate("Was ist DARA?")
    print(f"   Response: {response.content}\n")

    # Local HTTP Backend (Stub)
    print("2. Local HTTP Backend:")
    local_backend = LocalHTTPBackend("llama-2-7b", base_url="http://localhost:8080")
    response = local_backend.generate("Erkläre Prozessanalyse")
    print(f"   Response: {response.content}\n")

    # Cloud Backend (Stub)
    print("3. Cloud Backend:")
    cloud_backend = CloudBackend("gpt-4", provider="openai")
    messages = [
        LLMMessage(role="system", content="Du bist ein hilfreicher Assistent."),
        LLMMessage(role="user", content="Hallo!")
    ]
    response = cloud_backend.chat(messages)
    print(f"   Response: {response.content}\n")

    # Factory
    print("4. Via Factory:")
    backend = LLMBackendFactory.create_backend("fake", "test-model")
    print(f"   Backend Info: {backend.get_model_info()}")
