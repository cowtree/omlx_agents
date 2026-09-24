from openai import OpenAI
from pydantic import ValidationError

from app.models import ArticalAnalysis

class StructuredOutputAgent:
    def __init__(self, client: OpenAI, model: str, thinking: bool = False, max_retries: int = 3):
        self.client = client
        self.model = model
        self.thinking = thinking
        self.max_retries = max_retries

    def analyze_article(self, article_text: str):
        prompt = f"""
        Analyze this article.

        Return JSON containing exactly these fields:

        title
        summary
        sentiment

        sentiment must be one of: positive, negative, neutral

        Return only JSON

        ARTICLE:
        {article_text}

        """

        for attempt in range(1, self.max_retries + 1):

            print(f"Attempt {attempt} of {self.max_retries}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You analyze news articles and respond in JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                extra_body={"chat_template_kwargs": {"enable_thinking": self.thinking}},
            )

            raw_output = response.choices[0].message.content

            try:
                result = ArticalAnalysis.model_validate_json(raw_output)
                print("Valid successful response from LLM")
                return result

            except ValidationError as e:
                print("Invalid response from LLM:")
                print(e.json(indent=4))

        raise RuntimeError(f"Failed to get valid response from LLM after {self.max_retries} attempts.")
