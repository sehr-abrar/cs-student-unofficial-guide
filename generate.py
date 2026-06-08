"""
generate.py — Grounded generation with Groq (Milestone 5)

Connects retrieve() to llama-3.3-70b-versatile via the Groq API.
The system prompt hard-enforces grounding: the model is only allowed to
answer from the retrieved chunks passed in the prompt; it must decline
(not hallucinate) when those chunks don't cover the question.

Source attribution is programmatic — the retrieved source filenames are
always appended to the response regardless of what the LLM says.

Usage:
    from generate import ask
    result = ask("What are Prof. Chen's office hours like?")
    print(result["answer"])
    print(result["sources"])
"""

import os
from groq import Groq
from dotenv import load_dotenv
from retrieve import retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 4

SYSTEM_PROMPT = """You are a helpful assistant for an Unofficial CS Student Survival Guide.
You answer questions about CS courses, professors, study strategies, internships, and campus resources.

CRITICAL RULES:
1. Answer ONLY using information explicitly stated in the DOCUMENTS section below.
2. Do NOT use your general training knowledge, even if you think you know the answer.
3. Do NOT make up details, infer information, or fill gaps with plausible-sounding content.
4. If the provided documents do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in my documents to answer that."
5. When the documents do contain the answer, be specific and quote or closely paraphrase
   what they say. Keep your answer concise and direct."""


def format_context(hits: list[dict]) -> str:
    """Build a numbered context block from retrieved chunks."""
    parts = []
    for i, hit in enumerate(hits, 1):
        parts.append(f"[{i}] (source: {hit['source']})\n{hit['text']}")
    return "\n\n".join(parts)


def ask(question: str, k: int = TOP_K) -> dict:
    """
    Full RAG pipeline: retrieve → generate → return grounded answer.

    Returns:
        {
            "answer":  str,         # LLM response grounded in retrieved chunks
            "sources": list[str],   # unique source filenames, always programmatic
            "chunks":  list[dict],  # raw retrieved chunks for inspection
        }
    """
    hits = retrieve(question, k=k)
    context = format_context(hits)

    user_message = f"""DOCUMENTS:
{context}

QUESTION: {question}

Answer using only the documents above. Cite the source number(s) in brackets, e.g. [1], [2]."""

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()

    # Programmatic source attribution — always include retrieved sources
    # regardless of what the model chose to cite.
    unique_sources = list(dict.fromkeys(h["source"] for h in hits))

    return {
        "answer": answer,
        "sources": unique_sources,
        "chunks": hits,
    }


if __name__ == "__main__":
    test_queries = [
        # Covered by documents
        "What do students say about Prof. Chen's office hours in Algorithms?",
        "What is the recruiting timeline for big tech summer internships?",
        "Can I use AI tools like GitHub Copilot on my CS assignments?",
        # NOT covered — system should decline
        "Where is the best sushi restaurant near campus?",
    ]

    for query in test_queries:
        result = ask(query)
        print(f"\n{'='*60}")
        print(f"Q: {query}")
        print(f"{'='*60}")
        print(f"A: {result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}")
