import json
import sqlite3
from pathlib import Path


def load_all_jsons(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print(f"🥇 Gold: {input_path} → {output_path}")

    # Idempotency: handle missing input directory gracefully
    if not input_path.exists():
        print(f"⚠️  Input directory not found: {input_dir}")
        print("\n📊 Gold Summary:")
        print("Total: 0 | Inserted: 0 | Skipped: 0")
        return

    json_files = sorted(input_path.glob("*.json"))

    if not json_files:
        print(f"⚠️  No .json files found in: {input_dir}")
        print("\n📊 Gold Summary:")
        print("Total: 0 | Inserted: 0 | Skipped: 0")
        return

    # Ensure output directory (where DB will live) exists
    output_path.mkdir(parents=True, exist_ok=True)

    db_path = output_path / "jobs.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Create table with schema enforcement and primary key for idempotency
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs(
            source_id TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            company TEXT,
            description TEXT,
            tech_stack TEXT
        )
        """
    )
    conn.commit()

    total = 0
    inserted = 0
    skipped = 0

    for jf in json_files:
        total += 1
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Failed to read/parse: {jf.name} — {e}")
            continue

        # Basic validation
        source_id = data.get("source_id")
        job_title = data.get("job_title")
        company = data.get("company")
        description = data.get("description")

        if not source_id or not job_title or not description:
            print(f"⚠️  Missing required fields: {jf.name}")
            continue

        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO jobs (source_id, job_title, company, description, tech_stack)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source_id, job_title, company, description, None),
            )

            # Determine whether row was inserted or ignored
            if cur.rowcount == 1:
                inserted += 1
                print(f"✅ Inserted: {jf.name}")
            else:
                skipped += 1
                print(f"⏭️ Skipped (duplicate): {jf.name}")

            conn.commit()

        except Exception as e:
            print(f"❌ Failed: {jf.name} — {e}")

    print(f"\n📊 Gold Summary:")
    print(f"Total: {total} | Inserted: {inserted} | Skipped: {skipped}")

    conn.close()
    