from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from typing import TypeVar
from pydantic import BaseModel,ValidationError
import json
import logging
import time

from app.result import AgentResult

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class StructuredOutputAgent:

    def __init__(self, client: OpenAI, 
                model: str, 
                thinking: bool = False, 
                max_retries: int = 3
        ):
        
        self.client = client
        self.model = model
        self.thinking = thinking
        self.max_retries = max_retries
        self.api_retries = 3


    def run(
            self,
            prompt: str,
            output_model: type[T],
            ) -> AgentResult[T]:

        schema = output_model.model_json_schema()
        schema_json = json.dumps(schema, indent=4)

        initial_prompt = f"""

        {prompt}

        Your response MUST satisfy this JSON schema:
        {schema_json}

        Return ONLY valid JSON.
        Do not include markdown or explanations.
        """

        last_output = None
        last_error = None

        logger.info("Running agent: output_model=%s model=%s thinking=%s",
                    output_model.__name__, self.model, self.thinking)

        for attempt in range(1, self.max_retries + 1):

            logger.info(
                "Validation attempt %s/%s",
                attempt,
                self.max_retries,
            )


            # First attempt
            if attempt == 1:
                current_prompt = initial_prompt

            # Repair attempt
            else:
                current_prompt = f"""
                    Your previous response failed schema validation.

                    JSON schema:
                    {schema_json}

                    Previous response:
                    {last_output}

                    Validation error:
                    {last_error}

                    Fix the response so that it satisfies the JSON schema

                    Return ONLY the correct JSON
                """

            logger.debug("Prompt:\n%s", current_prompt)

            raw_output = self._call_llm(current_prompt)

            logger.debug("Raw output:\n%s", raw_output)

            try:
                result = output_model.model_validate_json(raw_output)
                logger.info("Validation passed on validation attempt %d", attempt)
                return AgentResult(
                        success=True,
                        data=result,
                        error=None,
                        attempts=attempt,
                    )

            except ValidationError as e:

                last_output = raw_output
                last_error = str(e)
                logger.warning("Validation failed on validation attempt %d (%d errors):\n%s",
                               attempt, e.error_count(), e)

        logger.error("Giving up after %d validation attempts", self.max_retries)
        return AgentResult(
                            success=False,
                            data=None,
                            error=(
                                f"Model failed to produce valid "
                                f"{output_model.__name__} output "
                                f"after {self.max_retries} attempts. "
                                f"Last error: {last_error}"
                            ),
                            attempts=self.max_retries,
                        )


    def _call_llm(self, prompt: str) -> str:

        for attempt in range(1, self.api_retries + 1):

            try:
                logger.info(
                    "Calling LLM: API attempt %s/%s",
                    attempt,
                    self.api_retries,
                )

                start = time.perf_counter()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You extract structured data from text and respond in JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    extra_body={"chat_template_kwargs": {"enable_thinking": self.thinking}},
                )

                elapsed = time.perf_counter() - start
                logger.info("LLM responded in %.1fs (%d prompt + %d completion tokens)",
                            elapsed, response.usage.prompt_tokens, response.usage.completion_tokens)

                return response.choices[0].message.content

            except (
                APIConnectionError,
                APITimeoutError,
                RateLimitError,
            ) as error:

                logger.warning(
                    "API call failed on attempt %s: %s",
                    attempt,
                    error,
                )

                if attempt == self.api_retries:
                    logger.error(
                        "API failed after %s attempts",
                        self.api_retries,
                    )
                    raise

                delay = 2 ** (attempt -1) 

                logger.info(
                    "Retrying API call in %s seconds",
                    delay
                )

                time.sleep(delay)

        raise RuntimeError("Unexpected API retry state.")

