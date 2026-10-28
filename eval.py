import os
import re
import time

from openai import OpenAI

from agent import ask

CASES = [
    {"question": "Which courses did I take in semester 3?", "contains": ["Software Engineering", "Distributed Systems"]},
    {"question": "Which course has the highest grade?", "contains": ["Probability"]},
    {"question": "Which course has the lowest grade?", "contains": ["Computer Networks"]},
    {"question": "What is my average grade, weighted by ECTS?", "number": 5.35, "tolerance": 0.02},
    {"question": "How many courses are in the database?", "number": 8, "tolerance": 0},
    {"question": "How many ECTS credits do I have in total?", "number": 57, "tolerance": 0},
    {"question": "Which courses did I take in semester 1?", "contains": ["Algorithms", "Databases", "Probability"]},
]


def numbers_in(text):
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def is_correct(answer, case):
    if "contains" in case:
        return all(item.lower() in answer.lower() for item in case["contains"])
    return any(abs(n - case["number"]) <= case["tolerance"] for n in numbers_in(answer))


def main():
    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    model = os.environ["LLM_MODEL"]
    repeats = int(os.environ.get("EVAL_REPEATS", "3"))
    passed = 0
    total_runs = 0
    total_time = 0.0
    for case in CASES:
        case_passed = 0
        last_wrong = None
        for _ in range(repeats):
            start = time.time()
            try:
                answer = ask(case["question"], client, model, verbose=False)
            except Exception as exc:
                answer = f"ERROR: {exc}"
            total_time += time.time() - start
            total_runs += 1
            if is_correct(answer, case):
                case_passed += 1
            else:
                last_wrong = answer
        passed += case_passed
        print(f"[{case_passed}/{repeats}] {case['question']}")
        if last_wrong:
            print(f"        wrong answer example: {last_wrong[:120]}")
    print(f"\nModel: {model}")
    print(f"Correct: {passed}/{total_runs} ({100 * passed / total_runs:.0f}%)  |  average latency: {total_time / total_runs:.1f}s")


if __name__ == "__main__":
    main()
