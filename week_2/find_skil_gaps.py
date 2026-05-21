import sqlite3
import time
import re
import os
from typing import List, Set
from pydantic import BaseModel
import requests

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:latest"  # or "deepseek-r1:1.5b" (faster)
RETRY_DELAY = 1
MAX_RETRIES = 3

# Super‑short prompt for speed
EXTRACT_SKILLS_PROMPT = """Extract technical skills from resume. Return lowercase comma-separated. Ignore soft skills, certs.
Resume:
{resume_text}"""

class SkillGapResult(BaseModel):
    gaps: List[str]
    tokens_used: int = 0
    time_ms: float = 0.0

def normalize_skill(skill: str) -> str:
    skill = skill.strip().lower()
    skill = re.sub(r'[.,;:]$', '', skill)
    skill = re.sub(r'\s*/\s*', '/', skill)
    return skill

def extract_skills_from_resume(resume_text: str) -> Set[str]:
    # Limit input length for speed
    prompt = EXTRACT_SKILLS_PROMPT.format(resume_text=resume_text[:1000])
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 200,
                        "top_k": 1,
                        "top_p": 0.9,
                    }
                },
                timeout=15
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                # Clean up
                text = re.sub(r'^.*?:', '', text)  # remove "assistant:" etc.
                text = re.sub(r'[^\w\s/,+.-]', '', text)
                skills = [normalize_skill(s) for s in text.split(',') if s.strip() and len(s.strip()) > 1]
                return set(skills)
            else:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            print("Ollama not running. Please start: ollama serve")
            return set()
        except Exception:
            time.sleep(RETRY_DELAY)
    return set()

def get_job_skills_from_db(db_url: str) -> Set[str]:
    job_skills = set()
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND tech_stack != ''")
        for row in cursor.fetchall():
            if row[0]:
                skills = [normalize_skill(s) for s in row[0].split(',')]
                job_skills.update(skills)
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    return job_skills

def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    start = time.time()

    # Handle missing data/ prefix gracefully
    if not os.path.exists(input_file_path):
        alt_path = os.path.join("data", os.path.basename(input_file_path))
        if os.path.exists(alt_path):
            input_file_path = alt_path

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            resume = f.read()
    except Exception as e:
        print(f"Error reading resume: {e}")
        return SkillGapResult(gaps=[])

    job_skills = get_job_skills_from_db(db_url)
    if not job_skills:
        return SkillGapResult(gaps=[])

    resume_skills = extract_skills_from_resume(resume)
    gaps = sorted(job_skills - resume_skills)
    elapsed_ms = (time.time() - start) * 1000

    # Rough token estimate
    total_chars = len(resume[:1000]) + sum(len(g) for g in gaps)
    estimated_tokens = total_chars // 4

    return SkillGapResult(gaps=gaps, tokens_used=estimated_tokens, time_ms=elapsed_ms)

if __name__ == "__main__":
    result = find_skill_gaps("resume_d3.txt", "data/jobs_d1.db")
    print(f"gaps={result.gaps} time={result.time_ms:.0f} tokens={result.tokens_used}")