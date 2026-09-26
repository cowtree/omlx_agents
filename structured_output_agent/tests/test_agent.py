"""Tests for StructuredOutputAgent, grouped by the six challenges it solves.

No LLM or server is needed: FakeClient (see conftest.py) returns scripted replies.
"""

import json
import logging

import openai
import pytest

from app.models import ArticalAnalysis, EntityExtraction
from conftest import auth_error, connection_error, rate_limit_error, timeout_error

VALID_ANALYSIS = json.dumps({
    "title": "Stock Market Downturn",
    "summary": "Major indices fell sharply today, worrying investors.",
    "sentiment": "negative",
    "confidence": 0.9,
})

VALID_ENTITIES = json.dumps({
    "people": ["Sam Altman"],
    "organizations": ["OpenAI", "Microsoft"],
    "locations": ["San Francisco"],
})


def analysis(**overrides):
    """VALID_ANALYSIS with some fields changed."""
    data = json.loads(VALID_ANALYSIS) | overrides
    return json.dumps(data)


class TestReliableOutputs:
    """A Pydantic model is the contract; its schema is part of the prompt."""

    def test_returns_instance_of_requested_model(self, make_agent):
        agent, _ = make_agent([VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert isinstance(result.data, ArticalAnalysis)
        assert result.data.sentiment == "negative"
        assert result.data.confidence == 0.9

    def test_same_agent_works_with_different_models(self, make_agent):
        agent, _ = make_agent([VALID_ANALYSIS, VALID_ENTITIES])

        article = agent.run("Analyze this article.", ArticalAnalysis)
        entities = agent.run("Extract the entities.", EntityExtraction)

        assert isinstance(article.data, ArticalAnalysis)
        assert isinstance(entities.data, EntityExtraction)
        assert entities.data.organizations == ["OpenAI", "Microsoft"]

    def test_prompt_contains_task_and_schema(self, make_agent):
        agent, client = make_agent([VALID_ANALYSIS])

        agent.run("Analyze this article.", ArticalAnalysis)

        prompt = client.prompt(0)
        assert "Analyze this article." in prompt
        # Field names, descriptions and allowed values all come from the model
        for text in ("sentiment", "confidence", "The overall sentiment of the article",
                     "positive", "negative", "neutral"):
            assert text in prompt


class TestSchemaValidation:
    """Every raw reply goes through model_validate_json(); bad replies never pass."""

    @pytest.mark.parametrize("bad_output", [
        pytest.param("This article is negative.", id="not JSON"),
        pytest.param("```json\n" + VALID_ANALYSIS + "\n```", id="wrapped in markdown"),
        pytest.param(json.dumps({"title": "T", "summary": "Long enough summary",
                                 "sentiment": "negative"}), id="missing field"),
        pytest.param(analysis(sentiment="sad"), id="value not in Literal"),
        pytest.param(analysis(confidence=1.5), id="number above le=1.0"),
        pytest.param(analysis(confidence=-0.1), id="number below ge=0.0"),
        pytest.param(analysis(summary="Too short"), id="string below min_length"),
        pytest.param(analysis(summary="x" * 501), id="string above max_length"),
    ])
    def test_invalid_output_is_rejected(self, make_agent, bad_output):
        agent, _ = make_agent([bad_output], max_retries=1)

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert not result.success
        assert result.data is None

    def test_valid_output_is_accepted(self, make_agent):
        agent, _ = make_agent([VALID_ANALYSIS], max_retries=1)

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success


class TestErrorHandling:
    """Validation failures and API failures are handled differently."""

    def test_validation_failure_returns_result_instead_of_raising(self, make_agent):
        agent, _ = make_agent(["not json"] * 3)

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success is False

    def test_api_failure_raises_after_all_api_retries(self, make_agent):
        agent, client = make_agent([connection_error()] * 3)

        with pytest.raises(openai.APIConnectionError):
            agent.run("Analyze this article.", ArticalAnalysis)

        assert len(client.calls) == 3

    def test_non_retryable_api_error_raises_immediately(self, make_agent, sleeps):
        agent, client = make_agent([auth_error()])

        with pytest.raises(openai.AuthenticationError):
            agent.run("Analyze this article.", ArticalAnalysis)

        assert len(client.calls) == 1
        assert sleeps == []


class TestRetryLogic:
    """API retries with backoff, and semantic repair of invalid replies."""

    def test_repair_succeeds_on_second_attempt(self, make_agent):
        agent, _ = make_agent([analysis(sentiment="sad"), VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success
        assert result.attempts == 2

    def test_repair_prompt_contains_previous_output_and_error(self, make_agent):
        bad_output = analysis(sentiment="sad")
        agent, client = make_agent([bad_output, VALID_ANALYSIS])

        agent.run("Analyze this article.", ArticalAnalysis)

        repair_prompt = client.prompt(1)
        assert "failed schema validation" in repair_prompt
        assert bad_output in repair_prompt
        assert "Input should be 'positive', 'negative' or 'neutral'" in repair_prompt

    def test_stops_after_max_retries(self, make_agent):
        agent, client = make_agent(["not json"] * 5, max_retries=2)

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert not result.success
        assert result.attempts == 2
        assert len(client.calls) == 2

    @pytest.mark.parametrize("error", [connection_error, timeout_error, rate_limit_error])
    def test_retryable_api_errors_are_retried(self, make_agent, error):
        agent, client = make_agent([error(), VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success
        assert len(client.calls) == 2

    def test_api_retry_uses_exponential_backoff(self, make_agent, sleeps):
        agent, _ = make_agent([connection_error(), timeout_error(), VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success
        assert sleeps == [1, 2]

    def test_api_retries_do_not_count_as_validation_attempts(self, make_agent):
        agent, _ = make_agent([connection_error(), connection_error(), VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.attempts == 1


class TestLogging:
    """Validation attempts and API attempts are logged separately."""

    def test_successful_run_logs_attempts(self, make_agent, caplog):
        agent, _ = make_agent([VALID_ANALYSIS])

        with caplog.at_level(logging.INFO, logger="app.agent"):
            agent.run("Analyze this article.", ArticalAnalysis)

        assert "Running agent: output_model=ArticalAnalysis" in caplog.text
        assert "Validation attempt 1/3" in caplog.text
        assert "Calling LLM: API attempt 1/3" in caplog.text
        assert "(10 prompt + 5 completion tokens)" in caplog.text
        assert "Validation passed on validation attempt 1" in caplog.text

    def test_validation_failure_logs_warning_then_error(self, make_agent, caplog):
        agent, _ = make_agent(["not json"] * 2, max_retries=2)

        with caplog.at_level(logging.INFO, logger="app.agent"):
            agent.run("Analyze this article.", ArticalAnalysis)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(warnings) == 2
        assert all("Validation failed" in r.getMessage() for r in warnings)
        assert errors[-1].getMessage() == "Giving up after 2 validation attempts"

    def test_api_retry_is_logged(self, make_agent, caplog):
        agent, _ = make_agent([connection_error(), VALID_ANALYSIS])

        with caplog.at_level(logging.INFO, logger="app.agent"):
            agent.run("Analyze this article.", ArticalAnalysis)

        assert "API call failed on attempt 1" in caplog.text
        assert "Retrying API call in 1 seconds" in caplog.text
        assert "Calling LLM: API attempt 2/3" in caplog.text

    def test_prompt_and_raw_output_logged_at_debug(self, make_agent, caplog):
        agent, _ = make_agent([VALID_ANALYSIS])

        with caplog.at_level(logging.DEBUG, logger="app.agent"):
            agent.run("Analyze this article.", ArticalAnalysis)

        debug = [r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG]
        assert any(m.startswith("Prompt:") for m in debug)
        assert any(m.startswith("Raw output:") and VALID_ANALYSIS in m for m in debug)


class TestContinueSafely:
    """run() returns an AgentResult, so one bad item doesn't stop a batch."""

    def test_failed_result_describes_what_went_wrong(self, make_agent):
        agent, _ = make_agent([analysis(sentiment="sad")] * 3)

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success is False
        assert result.data is None
        assert result.attempts == 3
        assert "ArticalAnalysis" in result.error
        assert "after 3 attempts" in result.error
        assert "sentiment" in result.error

    def test_successful_result_has_no_error(self, make_agent):
        agent, _ = make_agent([VALID_ANALYSIS])

        result = agent.run("Analyze this article.", ArticalAnalysis)

        assert result.success is True
        assert result.error is None
        assert result.attempts == 1

    def test_batch_continues_after_a_failed_item(self, make_agent):
        # Item 2 fails both attempts; items 1 and 3 succeed
        agent, _ = make_agent(
            [VALID_ANALYSIS, "not json", "still not json", VALID_ANALYSIS],
            max_retries=2,
        )

        results = [agent.run(f"Analyze article {i}.", ArticalAnalysis) for i in range(1, 4)]

        assert [r.success for r in results] == [True, False, True]
        assert results[2].data.sentiment == "negative"
