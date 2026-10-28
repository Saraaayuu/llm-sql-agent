import json
import os
import re
import sqlite3
import sys

from openai import OpenAI

DB_PATH = "courses.db"
MAX_ROWS = 50
MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You answer questions about a student's courses stored in a SQLite database. "
    "Table courses(id, name, ects, semester, grade). Grades are on a 1 to 6 scale. "
    "Use the run_sql tool to query the data. Only use SELECT statements. "
    "For a weighted average use exactly: SELECT SUM(grade*ects) * 1.0 / SUM(ects) FROM courses. Never use AVG for a weighted average. "
    "When asked which course, select the name column. If a tool result does not contain what you need, run another query. Never state values that are not in the tool results. "
    "Always call the run_sql tool before answering, never write SQL in your reply. "
    "Base your answer only on the tool results."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run one read-only SELECT query on the courses database and return the rows as JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A single SQL SELECT statement."}
                },
                "required": ["query"],
            },
        },
    }
]


def run_sql(query, db_path=DB_PATH):
    statement = query.strip().rstrip(";").strip()
    if ";" in statement:
        return json.dumps({"error": "Only one statement is allowed."})
    if not re.match(r"(?is)^select\b", statement):
        return json.dumps({"error": "Only SELECT statements are allowed."})
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.execute(statement)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS)
        conn.close()
    except sqlite3.Error as exc:
        return json.dumps({"error": str(exc)})
    return json.dumps({"columns": columns, "rows": rows})


def ask(question, client, model, db_path=DB_PATH, verbose=True):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, temperature=0)
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            if verbose:
                print(f"[tool call] {call.function.name}: {args.get('query')}")
            result = run_sql(args.get("query", ""), db_path) if call.function.name == "run_sql" else json.dumps({"error": "Unknown tool."})
            if verbose:
                print(f"[tool result] {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Stopped: too many tool steps."


def main():
    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    model = os.environ["LLM_MODEL"]
    question = " ".join(sys.argv[1:]) or "What is my average grade, weighted by ECTS?"
    print(ask(question, client, model))


if __name__ == "__main__":
    main()
