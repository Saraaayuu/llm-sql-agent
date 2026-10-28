# SQL Question Agent

A small command-line agent that answers questions about a SQLite database in plain language. The language model decides when to call a `run_sql` tool, the program runs the query, and the model writes the answer from the result. It runs locally with Ollama, and works with any OpenAI-compatible API.

## How it works

1. The user asks a question, for example "Which courses did I take in semester 3?".
2. The model receives the question and the description of the `run_sql` tool (tool calling, OpenAI-compatible format).
3. The model replies with a tool call containing a SQL query.
4. The program checks the query (a single `SELECT` statement only), runs it on a read-only database connection and sends the rows back to the model.
5. The model writes the final answer. The loop stops after 5 steps at most.

## Safety

- Only one `SELECT` statement is accepted per call.
- The database is opened in read-only mode.
- At most 50 rows are returned to the model.

## Setup

```
pip install -r requirements.txt
python make_db.py
```

Set three environment variables. Example for a local Ollama server:

```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
```

## Run

```
python agent.py "What is my average grade, weighted by ECTS?"
```

The program prints every tool call and tool result, then the final answer.

## Evaluation

`eval.py` asks 7 questions with known answers (checked against the database), repeats each one 3 times and reports the share of correct answers and the average latency.

```
python eval.py
```

Results with `llama3.2` (3B parameters) running locally through Ollama:

| Step | Change | Result |
| --- | --- | --- |
| 1 | Baseline, single run per question | 6/7 |
| 2 | Temperature 0, 3 runs per question, rule "always call the tool, never write SQL in the reply" | 18/21 |
| 3 | Added an exact formula for weighted averages | 18/21 (weighted average fixed, "lowest grade" broke) |
| 4 | Added rules: select the name column, run another query if the result is incomplete, never state values missing from the tool results | 21/21, average latency 0.5 s |

What I learned from the failures:

- The first wrong answer came from the model writing `AVG(grade*ects)` instead of `SUM(grade*ects) / SUM(ects)`. The tool worked, the query was wrong.
- A prompt change that fixed one question broke another one. The test set made this visible right away.
- When a query returned only a number (`SELECT MIN(grade)`), the model invented the missing course name instead of asking for it. A rule against stating values that are not in the tool results fixed it.

## Limitations

- The test set is small (7 questions) and I tuned the prompt on the same questions, so 100% is an optimistic estimate. A separate held-out set would give a fairer number.
- The exact weighted-average formula in the prompt is specific to this table. A more general solution is a dedicated tool (for example `weighted_average`) or several worked examples in the prompt.
- Results depend on the model. A larger model would likely need fewer prompt rules.

## Possible extensions

- Compare several model sizes (3B vs 8B) on accuracy and latency.
- Add a second tool, for example one that plots grades by semester.
- Add a held-out question set and log token usage per question.
