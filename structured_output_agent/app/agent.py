from openai import OpenAI
from typing import TypeVar
from pydantic import BaseModel,ValidationError
import json

T = TypeVar("T", bound=BaseModel)

class StructuredOutputAgent:

    def __init__(self, client: OpenAI, 
                model: str, 
                thinking: bool = False, 
                max_retries: int = 3):
        self.client = client
        self.model = model
        self.thinking = thinking
        self.max_retries = max_retries

    def run(self,
            prompt: str,
            output_model: type[T],
            ) -> T:

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

        for attempt in range(1, self.max_retries + 1):

            print(f"Attempt {attempt} of {self.max_retries}...")


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


            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract structured data from text and respond in JSON."},
                    {"role": "user", "content": current_prompt},
                ],
                temperature=0.2,
                extra_body={"chat_template_kwargs": {"enable_thinking": self.thinking}},
            )

            raw_output = response.choices[0].message.content

            try:
                result = output_model.model_validate_json(raw_output)
                print("Valid successful response from LLM")
                return result

            except ValidationError as e:

                last_output = raw_output
                last_error = str(e)
                print("Invalid response from LLM:")
                print(e.json(indent=4))

        raise RuntimeError(f"Failed to get valid response from LLM after "
                            f"{self.max_retries} attempts.")

