from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.groq_api_key)

# takes your 5 matched chunks and glues them into one big text block (context), -
# then wraps that plus your question into a single instruction the LLM will read as one message.
def build_prompt(question: str, matches: list[dict]) -> str:
    context = "\n\n".join(f"[Source: {m['source']}, page {m['page']}]\n{m['text']}" for m in matches)

    return f"""Answer the question using ONLY the context below. If the answer isn't in the context, say you don't know.
        Context:
        {context}

        Question: {question}
        Answer:"""


def get_answer(question: str, matches: list[dict]) -> str:
    prompt = build_prompt(question, matches)

    response = client.chat.completions.create(
        
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="openai/gpt-oss-20b",
    )

    return response.choices[0].message.content