import os

from dotenv import load_dotenv
from openai import OpenAI

from app.agent import StructuredOutputAgent
from app.logging_config import setup_logging
from app.models import ArticalAnalysis, EntityExtraction
from app.result import AgentResult


def create_agent() -> StructuredOutputAgent:
    # Qwen "thinking" is slow but better for hard problems; toggle via OMLX_THINKING in .env
    thinking = os.getenv("OMLX_THINKING", "false").lower() in ("1", "true", "yes", "on")

    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key=os.environ["OMLX_API_KEY"],
    )

    return StructuredOutputAgent(
        client=client,
        model=os.environ["OMLX_MODEL"],
        thinking=thinking,
        max_retries=3,
    )


def print_result(title: str, result: AgentResult) -> None:
    if result.success:
        print(f"\n{title}: SUCCESS after {result.attempts} attempt(s)")
        print(result.data.model_dump_json(indent=2))
    else:
        print(f"\n{title}: FAILED after {result.attempts} attempt(s)")
        print(result.error)


def main() -> None:
    load_dotenv()
    setup_logging()

    agent = create_agent()

    # 1. Article analysis
    article = """
    A biotechnology company announced positive results from a clinical
    trial of its new cancer treatment.

    The company reported that patients receiving the treatment showed
    improved outcomes compared with the control group.
    """

    result = agent.run(
        prompt=f"Analyze the following article.\n\nARTICLE:\n{article}",
        output_model=ArticalAnalysis,
    )
    print_result("ARTICLE ANALYSIS", result)

    # 2. Entity extraction
    text = """
    Sam Altman spoke at an OpenAI event in San Francisco.
    Several researchers from Microsoft also attended.
    """

    result = agent.run(
        prompt=f"Extract the entities from this text:\n\n{text}",
        output_model=EntityExtraction,
    )
    print_result("ENTITIES", result)

    # 3. Batch: analyze several articles; a failed one is reported and the loop continues
    articles = [
        # Clearly positive
        """Apple unveiled its new MacBook lineup in Cupertino on Tuesday. Early reviews
        praise the longer battery life and faster chips, and pre-orders sold out within hours.""",

        # Clearly negative
        """Global stock markets fell sharply on Monday after weaker-than-expected jobs data.
        The S&P 500 dropped 3%, its worst day this year, and analysts warn of further losses.""",

        # Neutral, factual
        """The European Space Agency published the schedule for its next three launches.
        The missions will take place from French Guiana between March and September.""",

        # Mixed: good and bad news in one article
        """Pfizer reported record quarterly revenue driven by its new vaccine, but also
        announced 2,000 layoffs and the cancellation of two late-stage drug trials.""",

        # Almost no content to analyze
        """Update: more details to follow.""",
    ]

    succeeded = 0
    for i, article in enumerate(articles, start=1):
        result = agent.run(
            prompt=f"Analyze the following article.\n\nARTICLE:\n{article}",
            output_model=ArticalAnalysis,
        )
        print_result(f"BATCH {i}/{len(articles)}", result)
        succeeded += result.success

    print(f"\nBATCH DONE: {succeeded}/{len(articles)} succeeded")


if __name__ == "__main__":
    main()
