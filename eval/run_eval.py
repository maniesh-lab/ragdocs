import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vectorstore import query_chunks
from app.services.llm import get_answer

DOCUMENT_ID = "geron-ml-book"
RESULTS_PATH = "eval/results/raw_results.json"

with open("eval/test_set.json") as f:
    test_set = json.load(f)

if os.path.exists(RESULTS_PATH):
    with open(RESULTS_PATH) as f:
        results = json.load(f)
else:
    results = []

already_done = {r["question"] for r in results}


def get_answer_with_retry(question, matches, max_retries=6):
    for attempt in range(max_retries):
        try:
            return get_answer(question, matches)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")


for item in test_set:
    question = item["question"]

    if question in already_done:
        print(f"Skipping (already done): {question}")
        continue

    reference = item["reference_answer"]
    matches = query_chunks(question, DOCUMENT_ID)
    contexts = [m["text"] for m in matches]
    answer = get_answer_with_retry(question, matches)

    results.append({
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "ground_truth": reference,
    })

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Done: {question}")
    time.sleep(20)

print(f"\nProcessed {len(results)} questions. Saved to {RESULTS_PATH}")