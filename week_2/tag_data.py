import sqlite3
import time
import re
import os
import requests

# ----------------- Configuration -----------------
BATCH_SIZE = 5
RETRY_DELAY = 2
MAX_RETRIES = 3
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:latest"
SKIP_SENTINEL = "__skip__"
MIN_DESC_LENGTH = 50
# -------------------------------------------------

PROMPT_TEMPLATE = """Extract the technical stack (programming languages, frameworks, tools, databases, cloud services, etc.) from the job description below. Return only a comma-separated list of technologies, all in lowercase. If none, return an empty string.

Description:
{description}
"""

# Patterns that strongly suggest technical content
TECH_PATTERNS = [
    r'\b\w+\.js\b',                        # Node.js, Vue.js, Next.js, Express.js
    r'\b\w+\.py\b',                        # script.py style references
    r'\b\w+\.net\b',                       # ASP.NET, .NET
    r'\b\w+\.ts\b',                        # TypeScript files
    r'\b[A-Z]{2,}\b',                      # AWS, SQL, GCP, CI, CD, REST, API, SDK
    r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b',   # CamelCase: PostgreSQL, MongoDB, GraphQL
    r'\bv?\d+\.\d+(?:\.\d+)?\b',          # version numbers: v3.9, 18.0, 2.1.4
    r'\b\w+(?:JS|DB|QL|OS|ML|AI|CD|CI)\b',# suffixes: GraphQL, MongoDB, macOS, DevOps
    r'\b\w+[-/]\w+\b',                     # hyphenated/slash tech: CI/CD, React/Node, open-source
    r'\b(?:framework|library|runtime|sdk|api|cli|orm|ide|vm|container|cluster)\b',  # generic tech nouns
    r'\b(?:deploy|containerize|automate|integrate|architect|configure|provision)\b', # technical verbs
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TECH_PATTERNS]


class TokenCounter:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def add_estimate(self, input_text: str, output_text: str):
        self.input_tokens += self.estimate_tokens(input_text)
        self.output_tokens += self.estimate_tokens(output_text)

    def get_total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def get_elapsed_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


def is_technical_description(desc: str) -> bool:
    """
    Returns True if the description looks technical based on regex heuristics.
    Requires at least 2 distinct pattern types to match, reducing false positives.
    """
    if not desc or len(desc.strip()) < MIN_DESC_LENGTH:
        return False

    matched_patterns = sum(1 for p in COMPILED_PATTERNS if p.search(desc))
    return matched_patterns >= 2  # at least 2 different heuristics must fire


def extract_tech_stack(description: str):
    """Returns (tech_stack_str, should_stop)."""
    prompt = PROMPT_TEMPLATE.format(description=description[:2000])

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 150},
                },
                timeout=30,
            )
            if resp.status_code != 200:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                continue

            raw = resp.json().get("response", "").strip()
            cleaned = re.sub(r'^```\w*\n?', '', raw)
            cleaned = re.sub(r'\n?```$', '', cleaned)
            cleaned = re.sub(r'^(assistant|llama|phi):\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[.,;:]$', '', cleaned.strip())

            if cleaned.lower() in ("none", "no technologies", "empty", ""):
                return "", False

            extracted_terms = [t.strip() for t in cleaned.split(',') if t.strip()]
            if not extracted_terms:
                return "", False

            # Hallucination guard: at least 50% of extracted terms must appear in description
            desc_lower = description.lower()
            matched = sum(1 for t in extracted_terms if len(t) >= 2 and t.lower() in desc_lower)
            if matched / len(extracted_terms) < 0.5:
                return "", False

            return cleaned, False

        except requests.exceptions.ConnectionError:
            print("\n❌ Ollama is not running. Start with: ollama serve")
            return "", True
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return "", False


def pre_filter_rows(conn: sqlite3.Connection):
    """Mark non-technical rows with sentinel using regex heuristics."""
    cursor = conn.cursor()

    # Fast DB-side elimination: too short or null
    cursor.execute(
        f"UPDATE jobs SET tech_stack = '{SKIP_SENTINEL}' "
        f"WHERE tech_stack IS NULL AND (description IS NULL OR length(trim(description)) < {MIN_DESC_LENGTH})"
    )

    # Regex heuristic filter in Python for remaining rows
    cursor.execute("SELECT source_id, description FROM jobs WHERE tech_stack IS NULL")
    rows = cursor.fetchall()

    skip_ids = [
        row["source_id"] for row in rows
        if not is_technical_description(row["description"])
    ]

    if skip_ids:
        cursor.executemany(
            f"UPDATE jobs SET tech_stack = '{SKIP_SENTINEL}' WHERE source_id = ?",
            [(sid,) for sid in skip_ids]
        )

    conn.commit()

    total = len(rows)
    skipped = len(skip_ids)
    print(f"Pre-filter: {skipped}/{total} rows skipped as non-technical, {total - skipped} queued for LLM.")


def tag_data(db_path: str):
    if not os.path.exists(db_path):
        alt = os.path.join("data", db_path)
        if os.path.exists(alt):
            db_path = alt

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"Database connection error: {e}")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    if not cursor.fetchone():
        print("Error: 'jobs' table not found.")
        conn.close()
        return

    pre_filter_rows(conn)

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE tech_stack IS NULL")
    total_pending = cursor.fetchone()[0]
    if total_pending == 0:
        print("No data to tag.")
        conn.close()
        return

    print(f"Jobs to process with LLM: {total_pending}\n")

    token_counter = TokenCounter()
    token_counter.start()
    processed = 0

    while True:
        cursor.execute(
            "SELECT source_id, description FROM jobs WHERE tech_stack IS NULL LIMIT ?",
            (BATCH_SIZE,)
        )
        batch = cursor.fetchall()
        if not batch:
            break

        batch_num = processed // BATCH_SIZE + 1
        print(f"[Batch {batch_num}] {processed}/{total_pending} done — processing {len(batch)} jobs...")

        for row in batch:
            job_id = row["source_id"]
            description = row["description"]

            tech_stack, stop = extract_tech_stack(description)
            if stop:
                conn.close()
                return

            prompt_text = PROMPT_TEMPLATE.format(description=description[:2000])
            token_counter.add_estimate(prompt_text, tech_stack)

            final_value = tech_stack if tech_stack else SKIP_SENTINEL
            cursor.execute("UPDATE jobs SET tech_stack = ? WHERE source_id = ?", (final_value, job_id))
            conn.commit()

            label = tech_stack if tech_stack else "(no technologies detected)"
            print(f"  Job {job_id}: {label}  [{processed + 1}/{total_pending}]")
            processed += 1
            time.sleep(0.5)

    conn.close()
    token_counter.stop()
    print(f"\n✅ Done. Processed {processed} jobs.")
    print(f"Estimated tokens: {token_counter.get_total_tokens()}, elapsed: {token_counter.get_elapsed_ms():.1f}ms")


if __name__ == "__main__":
    tag_data("data/jobs_d1.db")