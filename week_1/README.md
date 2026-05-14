# Week 1 : Data Component

## Data Input & Processing Component

Build a robust, local data engineering pipeline that successfully extracts raw data from the `0_source` , processes and cleans it into a structured format, and stores it in a relational database (jobs.db).

The project follows best practices for:

- **Data Ingestion**
- **Data Cleaning & Processing**
- **Data Structuring**
- **Data Storage**
- **Data Profiling**
- **Orchestration**
- **Idempotency**
- **Medallion Architecture (Simplified):** A data design pattern used to logically organize data in a lakehouse, with the goal of incrementally and progressively improving the structure and quality of data.

---

# Architecture Reflection

The project is structured using a modular Python architecture to improve maintainability, scalability, and readability.

### Design Considerations

- **`src/` directory structure**
  - Separates source code from configuration and data files.
  - Makes the project easier to navigate and maintain.

- **Virtual Environment (`.venv`)**
  - Isolates project dependencies from the global Python installation.
  - Prevents package version conflicts.

- **`uv` Package Manager**
  - Chosen for faster dependency management and environment setup.
  - Simplifies Python version management and dependency installation.

- **`ruff`**
  - Used for linting and formatting to maintain consistent code quality.

- **`pydantic`**
  - Used for validation and structured data handling.

---

# Setup Instructions

## Prerequisites

Install the following tools before starting:

### Required Software

1. [VS Code](https://code.visualstudio.com/?utm_source=chatgpt.com)
2. [Git](https://git-scm.com/downloads?utm_source=chatgpt.com)
3. [Python 3.14](https://www.python.org/downloads/?utm_source=chatgpt.com)
4. [uv Package Manager](https://docs.astral.sh/uv/getting-started/installation/?utm_source=chatgpt.com)

---

## Recommended VS Code Extensions

1. [Error Lens by Alexander](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens&utm_source=chatgpt.com)  
   Syntax error highlighting

2. [Python by Microsoft](https://marketplace.visualstudio.com/items?itemName=ms-python.python&utm_source=chatgpt.com)  
   Python IntelliSense and debugging support

3. [SQLite3 Editor by yy0931](https://marketplace.visualstudio.com/items?itemName=yy0931.vscode-sqlite3-editor&utm_source=chatgpt.com)  
   SQLite database viewer

> Recommended: Use a dedicated VS Code profile for this project to avoid extension conflicts.

---

# Repository Setup

## 1. Clone Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

---

## 2. Configure Python Version

Create a `.python-version` file:

```txt
3.14
```

---

## 3. Install Python Environment

Run:

```bash
uv python install
uv init
uv venv
```

This will:
- Install the required Python version
- Initialize the project
- Create a virtual environment

---

## 5. Install Dependencies

Install required packages:

```bash
uv add bs4 ruff pydantic
```

Installed packages:
- `bs4` → HTML parsing with BeautifulSoup
- `ruff` → Linter and formatter
- `pydantic` → Data validation

Useful reference:

[uv Package Manager CRUD Cheat Sheet](https://www.notion.so/uv-Package-Manager-CRUD-Cheat-Sheet-35917c3c3ec08042b460ea9cc7838b49?pvs=21&utm_source=chatgpt.com)

---

## 6. Configure `.gitignore`

Create a `.gitignore` file at the root:

```gitignore
data/
src/__pycache__/
.ruff_cache/
.venv/
```

---

# Usage

## Running the Project

### Run Module 1

```bash
python main.py ingest
```

### Run Module 2

```bash
python main.py process
```

### Run Module 3

```bash
python main.py load
```

### Run Module 4

```bash
python main.py profiler
```

### Run All Module

```bash
python main.py all
```

---

# Recommended Project Structure

```text
project-root/
│
├── src/
│   ├── main.py
│   └── ...
│
├── data/
├── .venv/
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── .env
```

---

# Version Control Workflow

## Initialize Git

```bash
git init
```

## Commit Changes

```bash
git add .
git commit -m "Initial project setup"
```

## Push to GitHub

```bash
git push origin main
```

---

# Technical Reflections

## Module 1: The Extractor (Medallion & Lakehouses)
Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?

Answer:
- Keeping the original raw HTML files is important because they act as the true source for the pipeline. If extraction logic, parsing rules, or transformation steps contain errors, developers can always return to the original files and reprocess the data without needing to recollect it. This also improves reproducibility since every transformation can be traced back to the raw input. Storing raw files also makes debugging and recovery easier. For example, if corrupted or incomplete records appear in the database, developers can compare the processed output against the original HTML files to identify where the issue occurred. It also helps when business requirements change later, because the same raw data can be transformed again using updated logic instead of losing potentially useful information permanently.

---

## Module 2: Treatment Plant (ETL vs ELT & Scale)
Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?

Answer:
- Cloud systems prefer ELT because storage in modern cloud platforms is relatively cheap, while compute resources are scalable on demand. By loading raw data first, organizations preserve all incoming information and can apply different transformation rules later without re-ingesting the data. This provides flexibility for analytics, machine learning, auditing, and future business requirements. Sequential processing becomes inefficient when dealing with thousands or millions of files because each file is processed one at a time, increasing execution time significantly. Distributed processing frameworks like Apache Spark solve this by splitting workloads across multiple machines or cores, allowing many files to be processed in parallel. This improves scalability, speeds up pipelines, and reduces bottlenecks in large-scale data systems.

---

## Module 3: The Blueprint & The Vault (Storage & Contracts)
What should happen if an important field like `job_title` disappears? Why fail early instead of silently inserting `nulls` into DB? How does `INSERT` OR `IGNORE` help prevent duplicate records?

Answer:
- If an important field like `job_title` disappears, the pipeline should fail early and alert the developer instead of silently inserting `null` values into the database. Missing critical fields may indicate extraction errors, schema changes, or corrupted input data. Allowing invalid data into the warehouse can break dashboards, analytics, reporting, and downstream systems that depend on consistent data structures. `INSERT OR IGNORE` helps prevent duplicate records by skipping inserts when a record with the same unique identifier already exists. This supports idempotency, meaning the pipeline can safely rerun without creating repeated data. It improves reliability because accidental reruns or retries will not duplicate records inside the database.

---

## Module 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
What happens if processor.py crashes halfway? How are automated orchestration tools more reliable than manual retries with Python scripts?

Answer:
- If `processor.py` crashes halfway, the pipeline may stop in an inconsistent state where some files are processed while others are incomplete. Manual retries using Python scripts can be unreliable because developers may not know exactly which step failed or which files were already processed, increasing the risk of duplication or missing data. Automated orchestration tools like Airflow improve reliability by managing dependencies, retries, logging, monitoring, and scheduling automatically. They can restart failed tasks, track execution history, and ensure steps run in the correct order through Directed Acyclic Graphs (DAGs). This reduces human error and makes production pipelines more stable and maintainable.

# Notes

- Avoid editing SQLite databases directly unless necessary.
- Use SQL queries or application logic for database modifications.
- Keep dependencies updated regularly.
- Ensure `.venv/` and `.env` are excluded from version control.
