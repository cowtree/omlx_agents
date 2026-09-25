import os
from dotenv import load_dotenv
from openai import OpenAI

from app.agent import StructuredOutputAgent
from app.models import ArticalAnalysis,EntityExtraction

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
A biotechnology company announced positive results from a clinical
trial of its new cancer treatment.

The company reported that patients receiving the treatment showed
improved outcomes compared with the control group.
"""

prompt = f"""
Analyze the following article.

ARTICLE:
{article}
"""

result = agent.run(
    prompt=prompt,
    output_model=ArticalAnalysis
)

print("Analysis Result:")
print(result.model_dump_json(indent=4))


text = """
Sam Altman spoke at an OpenAI event in San Francisco.
Several researchers from Microsoft also attended.
"""

entities = agent.run(
    prompt=f"""
Extract the entities from this text:

{text}
""",
    output_model=EntityExtraction,
)


print("\nENTITIES")
print(entities.model_dump_json(indent=2))
