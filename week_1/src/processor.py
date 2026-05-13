from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError


# ── Data Contract ──────────────────────────────────────────────────────────────

class JobListing(BaseModel):
    source_id: str
    job_title: str
    company: str
    description: str


# ── Main Entry Point ───────────────────────────────────────────────────────────

def process_all_html(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print(f"🥈 Silver: {input_path} → {output_path}")

    # Idempotency: handle missing input directory gracefully
    if not input_path.exists():
        print(f"⚠️  Input directory not found: {input_dir}")
        print("\n📊 Silver Summary:")
        print("Total: 0 | Processed: 0 | Skipped: 0")
        return

    html_files = sorted(input_path.glob("*.html"))

    if not html_files:
        print(f"⚠️  No .html files found in: {input_dir}")
        print("\n📊 Silver Summary:")
        print("Total: 0 | Processed: 0 | Skipped: 0")
        return

    # Idempotency: create output directory if missing
    output_path.mkdir(parents=True, exist_ok=True)

    total = 0
    processed = 0
    skipped = 0

    for html_file in html_files:
        total += 1
        result = _process_file(html_file)

        if isinstance(result, str):
            # result is an error message
            print(f"⚠️  {result} in: {html_file.name}")
            skipped += 1
        else:
            # result is a validated JobListing — overwrite to ensure idempotency
            out_file = output_path / f"{html_file.stem}.json"
            out_file.write_text(
                result.model_dump_json(indent=2),
                encoding="utf-8"
            )
            print(f"✅ Processed: {html_file.name}")
            processed += 1

    print(f"\n📊 Silver Summary:")
    print(f"Total: {total} | Processed: {processed} | Skipped: {skipped}")


# ── File Processor ─────────────────────────────────────────────────────────────

def _process_file(html_file: Path) -> JobListing | str:
    """Parse one HTML file and return a JobListing or an error string."""
    html = html_file.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    source_id = _extract_source_id(soup)
    job_title = _extract_job_title(soup)
    company = _extract_company(soup)
    description = _extract_description(soup)

    # Skip processing if any required field is missing.
    required_fields = {
        "source_id": source_id,
        "job_title": job_title,
        "company": company,
        "description": description,
    }
    missing_fields = [name for name, value in required_fields.items() if not value]
    if missing_fields:
        return f"Missing required field(s): {', '.join(missing_fields)}"

    try:
        return JobListing(
            source_id=source_id,
            job_title=job_title,
            company=company,
            description=description,
        )
    except ValidationError as e:
        return f"Validation error: {e}"


# ── Field Extractors ───────────────────────────────────────────────────────────

def _extract_source_id(soup: BeautifulSoup) -> str:
    """Extract source_id from og:url meta tag — take the last path segment."""
    og_url = soup.find("meta", property="og:url")
    if og_url:
        url = og_url.get("content", "").rstrip("/")
        if url:
            return url.split("/")[-1]

    # Fallback: canonical link tag
    canonical = soup.find("link", rel="canonical")
    if canonical:
        url = canonical.get("href", "").rstrip("/")
        if url:
            return url.split("/")[-1]

    return ""

def _extract_job_title(soup: BeautifulSoup) -> str:
    tag = soup.find(attrs={"data-automation": "job-detail-title"})
    if tag:
        return _clean(tag.get_text(separator=" ", strip=True))
    return ""
    

def _extract_company(soup: BeautifulSoup) -> str:
    tag = soup.find(attrs={"data-automation": "advertiser-name"})
    if tag:
        return _clean(tag.get_text(separator=" ", strip=True))
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    tag = soup.find(attrs={"data-automation": "jobAdDetails"})
    if tag:
        return _clean(tag.get_text(separator=" ", strip=True))
    return ""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    return " ".join(text.split()).strip()