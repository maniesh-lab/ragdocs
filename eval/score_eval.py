import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = "eval/results/raw_results.json"
SCORES_PATH = "eval/results/scores.json"
DETAIL_PATH = "eval/results/scores_detail.json"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

with open(RESULTS_PATH) as f:
    raw_results = json.load(f)

if os.path.exists(DETAIL_PATH):
    with open(DETAIL_PATH) as f:
        scored = json.load(f)
else:
    scored = []

already_done = {s["question"] for s in scored}

for i, item in enumerate(raw_results):
    if item["question"] in already_done:
        print(f"Skipping (already scored): {item['question'][:50]}...")
        continue

    context = "\n\n".join(item["contexts"])

    judge_prompt = f"""You are grading a RAG system's answer. Score each on 0.0-1.0.

Context:
{context}

Question: {item['question']}
Answer given: {item['answer']}
Reference (correct) answer: {item['ground_truth']}

Score these, respond with ONLY valid JSON, no other text:
{{
  "faithfulness": <0.0-1.0, does the answer only claim things supported by the context>,
  "relevancy": <0.0-1.0, does the answer actually address the question>,
  "correctness": <0.0-1.0, does the answer match the reference answer's meaning>
}}"""

    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": judge_prompt}],
            )
            raw = response.choices[0].message.content
            raw = raw.strip().strip("```json").strip("```").strip()
            scores = json.loads(raw)
            break
        except Exception as e:
            print(f"  Retry {attempt+1}: {e}")
            time.sleep(5)
    else:
        scores = {"faithfulness": None, "relevancy": None, "correctness": None}

    scored.append({"question": item["question"], **scores})
    print(f"Scored {len(scored)}/{len(raw_results)}: {item['question'][:50]}... -> {scores}")

    with open(DETAIL_PATH, "w") as f:
        json.dump(scored, f, indent=2)

    time.sleep(2)

valid = [s for s in scored if s["faithfulness"] is not None]
summary = {
    "num_questions": len(scored),
    "num_scored_successfully": len(valid),
    "faithfulness": sum(s["faithfulness"] for s in valid) / len(valid),
    "relevancy": sum(s["relevancy"] for s in valid) / len(valid),
    "correctness": sum(s["correctness"] for s in valid) / len(valid),
}

with open(SCORES_PATH, "w") as f:
    json.dump(summary, f, indent=2)

print("\nSummary:")
print(json.dumps(summary, indent=2))