import os
from dotenv import load_dotenv
from openai import OpenAI

from app.agent import StructuredOutputAgent

load_dotenv()

# Qwen "thinking" is slow but better for hard problems; toggle via OMLX_THINKING in .env
thinking = os.getenv("OMLX_THINKING", "false").lower() in ("1", "true", "yes", "on")

client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key=os.environ["OMLX_API_KEY"],
    )

agent = StructuredOutputAgent(
    client=client,
    model=os.environ["OMLX_MODEL"],
    thinking=thinking,
    max_retries=3,
)


article = """
The stock market experienced a significant downturn today, with major indices falling sharply. Investors are concerned about
"""

result = agent.analyze_article(article)

print("Analysis Result:")
print(result.model_dump_json(indent=4))
