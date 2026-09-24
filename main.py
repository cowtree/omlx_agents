import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Qwen "thinking" is slow but better for hard problems; toggle via OMLX_THINKING in .env
thinking = os.getenv("OMLX_THINKING", "false").lower() in ("1", "true", "yes", "on")

# Initialize the client pointing to your local oMLX instance
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.environ["OMLX_API_KEY"],
)

response = client.chat.completions.create(
    model=os.environ["OMLX_MODEL"],
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a python function to merge two dictionaries."}
    ],
    temperature=0.2,
    extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
)

message = response.choices[0].message
if thinking:
    print("--- thinking ---")
    print((message.model_extra or {}).get("reasoning_content", ""))
    print("--- answer ---")
print(message.content)
