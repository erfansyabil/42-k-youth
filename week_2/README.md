# Week 2: Job Skills Gap Analysis

## Project Overview

This project automates the process of extracting technical skill requirements from job descriptions and comparing them against a candidate's resume. It consists of two main components:

1. **Job Tagging (`tag_data.py`)** – Uses a local LLM (Ollama) to parse job descriptions and populate a `tech_stack` column in an SQLite database.
2. **Skill Gap Analysis (`find_skill_gaps.py`)** – Extracts technical skills from a resume, aggregates all required skills from the database, and returns a sorted list of missing skills.

The goal is to help job seekers identify which technologies they need to learn to match current job market demands.

---

## Setup Instructions

### Prerequisites

- **Python** 3.9 or higher
- **Ollama** installed and running (for local LLM inference)
- **SQLite3** (built into Python)
- **uv** (recommended) or pip for dependency management

### Installation Steps

1. **Clone the repository** and navigate to the project folder:
   ```bash
   git clone <your-repo-url>
   cd week_2P

2. Install Python dependencies using uv
    ```bash
    uv add pydantic requests

3. **Install and start Ollama:**
    - Download from ollama.ai
    - Pull a model (e.g., phi3:latest):
        ```bash
        ollama pull phi3:latest
        Start the Ollama server:
    - Start the Ollama server:
        ```bash
        ollama serve
    Keep this terminal open while running the scripts.

4. **Prepare the database:**
- Ensure you have a SQLite database (e.g., jobs_d1.db) with a jobs table containing at least:

    - source_id (INTEGER PRIMARY KEY)

    - description (TEXT) – the full job description

    - tech_stack (TEXT) – initially NULL or empty

- If coming from Week 1, your jobs.db should already have this schema.

## Usage

### 1. Tag Job Descriptions ```(tag_data.py)```
Populate the tech_stack column by analyzing job descriptions:
```bash
uv run tag_data.py
```
Expected output (first few lines):

```text
Using database: jobs.db
Using Ollama model: phi3:latest
✓ Ollama server is running
Found columns: ['source_id', 'job_title', 'company', 'description', 'tech_stack']
Found 84 valid jobs to process...

[Batch 0] Processing 5 jobs...
Analyzed Job 91237386: python, sql, java, aws, docker
Analyzed Job 91360026: machine learning, pytorch, tensorflow, scikit-learn
...
==================================================
Total tokens used: 12450, took 63200.00ms
Processed 84 out of 84 jobs
```
**Reset** the ```tech_stack``` column (to re-run tagging):

```bash
sqlite3 jobs.db "UPDATE jobs SET tech_stack = NULL;"
```

### 2. Find Skill Gaps ```(find_skill_gaps.py)```
Compare your resume against all job skills:
```bash
uv run find_skill_gaps.py
```

Expected output:
```text
gaps=['a/b testing', 'alibaba cloud', 'api integration', 'aws', 'ci/cd', ...] time=67 tokens=6969
```

The output is a JSON-like representation of the SkillGapResult object, showing:

- `gaps`: sorted list of missing skills (lowercase, exact matches)

- `time_ms`: execution time in milliseconds

- `tokens_used`: estimated token count

## API / Function Reference

`tag_data.py`
`tag_data(db_url: str = None) -> Tuple[int, float, dict]`
- Purpose: Populate the tech_stack column using Ollama.

- Input: Optional path to SQLite database (defaults to jobs.db).

- Output: Tuple of (total_tokens, elapsed_ms, quality_metrics).

- Behavior: Reads descriptions, skips invalid ones (length<20 or placeholders), calls Ollama with temperature=0.1, updates database in batches.

**Helper functions**

- `is_valid_description(description: str)` -> bool – validates description length and content.

- `extract_tech_stack(description, token_counter)` -> (tech_stack, should_stop) – calls Ollama API.

`find_skill_gaps.py`
`find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult`
- Purpose: Identify skills missing from the resume relative to all job requirements.

- Inputs:

    - input_file_path – path to resume text file.

    - db_url – path to SQLite database.

- Output: SkillGapResult Pydantic model with:

    - gaps: List[str] – sorted missing skills (lowercase)

    - tokens_used: int – estimated tokens (4 chars/token)

    - time_ms: float – execution time

Helper functions

- `normalize_skill(skill: str) -> str` – lowercases, strips, normalizes slashes (e.g., c/c++).

- `extract_skills_from_resume(resume_text: str) -> Set[str]` – uses Ollama (temperature=0.0) to extract technical skills.

- `get_job_skills_from_db(db_url: str) -> Set[str]` – reads all tech_stack entries, splits by comma, normalizes.

## Data / Assumptions

### Database Schema

Assumes a `jobs` table with at least:

```sql
    CREATE TABLE jobs (
    source_id INTEGER PRIMARY KEY,
    description TEXT,
    tech_stack TEXT
);
```

Other columns (`job_title`, `company`, etc.) are ignored.

### Input Files

- `resume.txt` – plain text, UTF-8 encoded. Any formatting (markdown, HTML) may reduce extraction accuracy.

- `jobs.db` – SQLite file with populated `description` column.

### Assumptions & Simplifications

1. Technical skills only – Soft skills (leadership, management) and certifications are ignored.

2. Exact matching – Skills are compared after normalization (lowercase, trimmed, slashes normalized). No fuzzy or synonym matching.

3. LLM determinism – Ollama with `temperature=0.0` guarantees identical outputs for the same input.

4. Empty/invalid descriptions – Skipped (no API call), `tech_stack` set to empty string.

5. Skill granularity – Each comma-separated item in `tech_stack` is treated as a single skill (e.g., `"Spring Boot"` is one skill).

6. Token estimation – 4 characters per token (rough estimate, not exact).

### Data Flow

The system processes job descriptions and a resume through two main scripts. Below is the step-by-step data flow.

1. `tag_data.py` – Populating `tech_stack` from job descriptions.

```text
jobs.db (jobs table) 
    │
    ├─> Read rows where tech_stack IS NULL OR ''
    │   (columns: source_id, description)
    │
    ▼
[Batch processing] (BATCH_SIZE=5)
    │
    ├─> For each job description:
    │   • Validate description (length >=20, not placeholder)
    │   • If invalid → set tech_stack = '' directly
    │   • If valid → send to Ollama API (prompt + description)
    │
    ▼
Ollama (local LLM)
    │
    │   prompt: "Extract technologies... return comma-separated list"
    │   temperature=0.1
    │
    ▼
Extracted tech_stack string (e.g., "python, sql, java")
    │
    ├─> Clean response (remove markdown, trim)
    │
    ▼
Update jobs table: SET tech_stack = cleaned_string WHERE source_id = ?
    │
    └─> Commit after each job (to avoid losing progress)

Output: Updated database + console logs + token/time metrics
```

2. `find_skill_gaps.py` – Analyzing resume vs aggregated skills

```text
resume.txt                 jobs.db
    │                          │
    │ read UTF-8 text          │ read all tech_stack columns
    ▼                          ▼
Raw resume string         Fetch all non-empty tech_stack rows
    │                          │
    │                          ▼
    │                   Split each by comma → normalize (lowercase, strip)
    │                          │
    │                          ▼
    │                   Set of all required job skills (job_skills)
    │                          │
    ▼                          │
Send resume to Ollama          │
(prompt + resume)              │
temperature=0.0                │
    │                          │
    ▼                          │
Extracted resume skills        │
(comma-separated, cleaned)     │
    │                          │
    ▼                          ▼
Set of resume skills (resume_skills)   Set of job skills (job_skills)
    │                          │
    └────────────┬─────────────┘
                 ▼
        Set difference: gaps = job_skills - resume_skills
                 │
                 ▼
        Sort gaps alphabetically
                 │
                 ▼
        Return SkillGapResult(gaps, tokens_used, time_ms)
```

3. Error and exception flow

- Database errors: Catch → print message → return empty result (gap analysis) or stop tagging (graceful exit).

- Ollama connection errors: Detect → print "Ollama not running" → exit with code 0 (no stack trace).

- File not found (resume): Catch → print error → return empty gaps.

- API failures (timeout, 500): Retry up to MAX_RETRIES with exponential backoff; if all fail, set tech_stack = '' and continue.

4. Data persistence

- `jobs.db` is the only persistent store. It is updated atomically per job.

- No intermediate caching or temporary files are used (simplicity).

- Token counts and execution times are computed in memory and returned, not saved.

5. Determinism control

- Ollama `temperature=0.0` in `find_skill_gaps.p`y ensures identical skill extraction for the same resume.

- tag_data.py uses `temperature=0.1` (slight variation allowed per requirements), but still low.

- Normalization functions (n`ormalize_skill`, `is_valid_description`) are purely deterministic.

This flow ensures that data moves from raw input (database, resume) through the LLM, gets cleaned, stored, and finally compared to produce a sorted list of missing skills.

## Testing

### Test Cases

- Empty description – Script should skip and mark as empty.

- Placeholder description (e.g., "No description") – Skipped.

- Very short description (<20 chars) – Skipped.

- Normal job description – Should extract reasonable tech stack.

- Resume with no technical skills – Should return all job skills as gaps.

- Resume with all skills – Should return empty gap list.

### Determinism Validation

Run the same job twice with temperature=0.0 – the extracted tech_stack should be identical. Verified manually.

### Error Handling Tests

- Ollama not running → prints friendly error, exits.

- Database missing → prints error, returns empty result.

- Resume file not found → prints error, returns empty result.

### Reproducing Tests

```bash
# Reset database
sqlite3 jobs.db "UPDATE jobs SET tech_stack = NULL;"

# Run tagging
uv run tag_data.py

# Run gap analysis
uv run find_skill_gaps.py
```

## Limitations

- LLM accuracy – The local model may miss niche technologies or incorrectly classify non-technical terms.

- No fuzzy matching – "JavaScript" vs "JS" are treated as different skills. This can be improved with synonym mapping.

- Token counting – Only an estimate; actual token usage may differ.

- Performance – Ollama processes 1-2 jobs per second on average hardware; processing 84 jobs takes ~1-2 minutes.

- No incremental updates – The database is fully re-tagged each run; no delta processing.

- Single resume – Only one resume file is supported at a time.

- No caching – Repeated runs re-query the LLM and database.

## Architecture Reflection

### Design Choices

1. Local LLM over API – Using Ollama eliminates API rate limits, costs, and privacy concerns. It also ensures determinism (temperature fixed to 0.0). The trade-off is slower inference on CPU, but acceptable for batch sizes of <100 jobs.

2. Batch processing – Jobs are processed in small batches (BATCH_SIZE=5) to allow checkpointing and reduce memory usage. If interrupted, only unprocessed jobs remain.

3. Separation of concerns – Two independent scripts (`tag_data.py` and `find_skill_gaps.py`) follow the Unix philosophy: each does one thing well. This makes testing and modification easier.

4. Pydantic for result validation – `SkillGapResult` ensures output structure is consistent, which is important for potential integration into larger systems.

5. Exact matching with normalization – Lowercasing and slash normalization (e.g., `c/c++`) prevents trivial mismatches while avoiding the complexity of synonym resolution.

6. Determinism – Setting `temperature=0.0` and using a fixed prompt guarantees that the same input always produces the same output, fulfilling the assignment requirement.

## Trade-offs

- Speed vs. Accuracy – `phi3:latest` is a 2.2GB model that balances speed and accuracy. deepseek-r1:1.5b is faster but less accurate; llama3.1:latest is slower but more accurate. The default choice (phi3) is a pragmatic trade-off.

- Simplicity vs. Robustness – No retry queue or persistent job state; if the script crashes, you restart from scratch. For a small dataset (84 jobs), this is acceptable.

- Token estimation vs. Exact counting – We estimated tokens (4 chars/token) to avoid calling an external tokenizer. This is sufficient for the bonus requirements but not precise.

## Potential Improvements

- Incremental updates – Track a last_updated timestamp in the database to avoid re-tagging unchanged jobs.

- Parallel processing – Use asyncio.gather to process multiple jobs concurrently (but careful with Ollama resource limits).

- Better token counting – Integrate tiktoken library for exact token counts.

- Prompt optimization – Few-shot examples could be improved based on error analysis.