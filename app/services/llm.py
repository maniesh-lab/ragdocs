from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def build_prompt(question: str, matches: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source: {m['source']}, page {m['page']}]\n{m['text']}" for m in matches
    )

    return f"""Answer the question using ONLY the context below. If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}
Answer:"""


def get_answer(question: str, matches: list[dict]) -> str:
    prompt = build_prompt(question, matches)

    interaction = client.interactions.create(
        model="gemini-3-flash-preview",
        input=prompt,
    )

    return interaction.steps[-1].content[0].text