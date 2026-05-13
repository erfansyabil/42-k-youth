import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = PROJECT_ROOT / "data" / "3_gold"
DB_PATH = GOLD_DIR / "jobs.db"

def run_data_profile(db_path):
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"❌ Database not found at {db_file}")
        return

    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                COUNT(*) AS total_records,
                SUM(CASE WHEN job_title IS NULL THEN 1 ELSE 0 END) AS missing_job_title,
                SUM(CASE WHEN company IS NULL THEN 1 ELSE 0 END) AS missing_company,
                SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END) AS missing_description,
                AVG(LENGTH(description)) AS avg_description_length
            FROM jobs
            """
        )
        total_records, missing_job_title, missing_company, missing_description, avg_description_length = cur.fetchone()

        cur.execute(
            """
            SELECT source_id, job_title, LENGTH(description) AS description_length
            FROM jobs
            WHERE description IS NOT NULL
            ORDER BY description_length ASC, source_id ASC
            LIMIT 1
            """
        )
        shortest_row = cur.fetchone()

        cur.execute(
            """
            SELECT source_id, job_title, LENGTH(description) AS description_length
            FROM jobs
            WHERE description IS NOT NULL
            ORDER BY description_length DESC, source_id ASC
            LIMIT 1
            """
        )
        longest_row = cur.fetchone()

    avg_description_length = int(round(avg_description_length)) if avg_description_length is not None else 0

    shortest_length = shortest_row[2] if shortest_row else 0
    shortest_source_id = shortest_row[0] if shortest_row else "N/A"
    shortest_job_title = shortest_row[1] if shortest_row else "N/A"

    longest_length = longest_row[2] if longest_row else 0
    longest_source_id = longest_row[0] if longest_row else "N/A"
    longest_job_title = longest_row[1] if longest_row else "N/A"


# Use print() statements for a simple console report
    print("--- 🔍 DATA QUALITY REPORT ---")
    print(f"📈 Total Records: {total_records}")
    print(
        "❓ Missing Values -> "
        f"job_title: {missing_job_title}, company: {missing_company}, description: {missing_description}"
    )
    print(f"📝 Avg Description Length: {avg_description_length} chars")
    print(f"⚠️  Shortest Description: {shortest_length} chars")
    print(f"   ↳ source_id: {shortest_source_id} | job_title: {shortest_job_title}")
    print(f"🚨 Longest Description: {longest_length} chars")
    print(f"   ↳ source_id: {longest_source_id} | job_title: {longest_job_title}")
