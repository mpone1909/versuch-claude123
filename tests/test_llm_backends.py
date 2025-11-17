"""Tests for llm_backends module."""

import pytest
import os

from dara_system.llm_backends import (
    LLMMessage,
    LLMResponse,
    FakeLLMBackend,
    LocalHTTPBackend,
    CloudBackend,
    LLMBackendFactory,
    get_default_backend
)


def test_llm_message():
    """Test LLMMessage dataclass."""
    msg = LLMMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_llm_response():
    """Test LLMResponse dataclass."""
    response = LLMResponse(
        content="Test response",
        model="test-model",
        usage={"tokens": 10}
    )
    assert response.content == "Test response"
    assert response.model == "test-model"
    assert response.usage["tokens"] == 10


def test_fake_backend_generate():
    """Test FakeLLMBackend.generate()."""
    backend = FakeLLMBackend(model_name="fake-test")

    response = backend.generate("Test prompt")

    assert isinstance(response, LLMResponse)
    assert "Test prompt" in response.content
    assert response.model == "fake-test"
    assert response.usage is not None


def test_fake_backend_chat():
    """Test FakeLLMBackend.chat()."""
    backend = FakeLLMBackend()

    messages = [
        LLMMessage(role="system", content="You are helpful"),
        LLMMessage(role="user", content="Hello")
    ]

    response = backend.chat(messages)

    assert isinstance(response, LLMResponse)
    assert "Hello" in response.content or "No user message" not in response.content
    assert response.metadata["backend"] == "fake"


def test_fake_backend_custom_template():
    """Test FakeLLMBackend with custom template."""
    backend = FakeLLMBackend(
        response_template="Custom: {prompt}"
    )

    response = backend.generate("Test")

    assert response.content.startswith("Custom:")


def test_local_http_backend_initialization():
    """Test LocalHTTPBackend initialization."""
    backend = LocalHTTPBackend(
        model_name="llama-2",
        base_url="http://localhost:8000"
    )

    assert backend.model_name == "llama-2"
    assert backend.base_url == "http://localhost:8000"


def test_local_http_backend_stub():
    """Test LocalHTTPBackend stub behavior."""
    backend = LocalHTTPBackend(model_name="test")

    response = backend.generate("Test prompt")

    assert isinstance(response, LLMResponse)
    assert response.metadata["stub"] is True
    assert "LOCAL LLM" in response.content


def test_cloud_backend_initialization():
    """Test CloudBackend initialization."""
    backend = CloudBackend(
        model_name="gpt-4",
        provider="openai",
        api_key="test-key"
    )

    assert backend.model_name == "gpt-4"
    assert backend.provider == "openai"
    assert backend.api_key == "test-key"


def test_cloud_backend_stub():
    """Test CloudBackend stub behavior."""
    backend = CloudBackend(
        model_name="gpt-4",
        provider="openai"
    )

    response = backend.generate("Test")

    assert isinstance(response, LLMResponse)
    assert response.metadata["stub"] is True
    assert "CLOUD" in response.content


def test_backend_factory_fake():
    """Test LLMBackendFactory creating FakeLLMBackend."""
    backend = LLMBackendFactory.create_backend(
        "fake",
        "test-model"
    )

    assert isinstance(backend, FakeLLMBackend)
    assert backend.model_name == "test-model"


def test_backend_factory_local_http():
    """Test LLMBackendFactory creating LocalHTTPBackend."""
    backend = LLMBackendFactory.create_backend(
        "local_http",
        "llama-2",
        base_url="http://localhost:8080"
    )

    assert isinstance(backend, LocalHTTPBackend)
    assert backend.model_name == "llama-2"


def test_backend_factory_cloud():
    """Test LLMBackendFactory creating CloudBackend."""
    backend = LLMBackendFactory.create_backend(
        "cloud",
        "gpt-4",
        provider="openai"
    )

    assert isinstance(backend, CloudBackend)
    assert backend.provider == "openai"


def test_backend_factory_invalid_type():
    """Test LLMBackendFactory with invalid type."""
    with pytest.raises(ValueError, match="Unbekannter Backend-Typ"):
        LLMBackendFactory.create_backend("invalid", "model")


def test_backend_factory_from_config():
    """Test LLMBackendFactory.create_from_config()."""
    config = {
        "type": "fake",
        "model_name": "test-model",
        "response_template": "Test: {prompt}"
    }

    backend = LLMBackendFactory.create_from_config(config)

    assert isinstance(backend, FakeLLMBackend)
    assert backend.model_name == "test-model"


def test_get_default_backend():
    """Test get_default_backend()."""
    backend = get_default_backend()

    assert isinstance(backend, FakeLLMBackend)


def test_backend_get_model_info():
    """Test get_model_info() method."""
    backend = FakeLLMBackend(model_name="test-model")

    info = backend.get_model_info()

    assert info["model_name"] == "test-model"
    assert info["backend_type"] == "FakeLLMBackend"
    assert "config" in info


def test_chat_with_multiple_messages():
    """Test chat with multiple messages."""
    backend = FakeLLMBackend()

    messages = [
        LLMMessage(role="system", content="System prompt"),
        LLMMessage(role="user", content="First question"),
        LLMMessage(role="assistant", content="First answer"),
        LLMMessage(role="user", content="Second question")
    ]

    response = backend.chat(messages)

    assert isinstance(response, LLMResponse)
    assert response.metadata["num_messages"] == 4
