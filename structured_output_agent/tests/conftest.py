from types import SimpleNamespace

import httpx2
import openai
import pytest

from app.agent import StructuredOutputAgent

REQUEST = httpx2.Request("POST", "http://localhost:8000/v1/chat/completions")


def connection_error():
    return openai.APIConnectionError(request=REQUEST)


def timeout_error():
    return openai.APITimeoutError(request=REQUEST)


def rate_limit_error():
    return openai.RateLimitError(
        "Too many requests", response=httpx2.Response(429, request=REQUEST), body=None
    )


def auth_error():
    return openai.AuthenticationError(
        "Invalid API key", response=httpx2.Response(401, request=REQUEST), body=None
    )


class FakeClient:
    """Stands in for OpenAI: returns scripted outputs instead of calling a server.

    Each item in `outputs` is either a string (the model's reply) or an
    exception instance (raised instead of replying). Every call is recorded.
    """

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=output))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )

    def prompt(self, call_index):
        """The user prompt sent in the given call."""
        return self.calls[call_index]["messages"][-1]["content"]


@pytest.fixture
def make_agent():
    def _make(outputs, max_retries=3):
        client = FakeClient(outputs)
        agent = StructuredOutputAgent(client=client, model="test-model", max_retries=max_retries)
        return agent, client

    return _make


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    """Skip real backoff waits and record how long the agent asked to sleep."""
    delays = []
    monkeypatch.setattr("app.agent.time.sleep", delays.append)
    return delays
