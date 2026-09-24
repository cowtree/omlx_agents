import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

thinking = os.getenv("OMLX_THINKING", "false").lower() in ("1", "true", "yes", "on")

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.environ["OMLX_API_KEY"],
)

class ArticalAnalysis(BaseModel):
    title: str
    summary: str
    sentiment: Literal["positive", "negative", "neutral"]


article_text = """
AI transforms drug discovery. Researchers are increasingly using AI to identify
promising drug candidates in weeks instead of years. Early results show higher
success rates in clinical trials, although experts warn that the models still
depend heavily on the quality of the training data.
"""

pronpt = f"""
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

# Ask the LLM to analyze the article, constrained to the ArticalAnalysis JSON schema
response = client.chat.completions.create(
    model=os.environ["OMLX_MODEL"],
    messages=[
        {"role": "system", "content": "You analyze news articles and respond in JSON."},
        {"role": "user", "content": f"Analyze this article:\n{article_text}"},
    ],
    temperature=0.2,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "ArticalAnalysis",
            "schema": ArticalAnalysis.model_json_schema(),
        },
    },
    extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
)

llm_response = response.choices[0].message.content

try:
    article = ArticalAnalysis.model_validate_json(llm_response)

    print(" Valid response from LLM:")
    print(article.model_dump_json(indent=4))

except ValidationError as e:
    print("Invalid response from LLM:")
    print(e.json(indent=4))
