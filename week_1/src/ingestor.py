import email
import email.message
from pathlib import Path


def ingest_all_mhtml(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print(f"🥉 Bronze: {input_path} → {output_path}")

    # Idempotency: handle missing input directory gracefully
    if not input_path.exists():
        print(f"⚠️  Input directory not found: {input_dir}")
        print("\n📊 Bronze Summary:")
        print("Total: 0 | Extracted: 0 | Failed: 0")
        return

    mhtml_files = sorted(input_path.glob("*.mhtml"))

    if not mhtml_files:
        print(f"⚠️  No .mhtml files found in: {input_dir}")
        print("\n📊 Bronze Summary:")
        print("Total: 0 | Extracted: 0 | Failed: 0")
        return

    # Idempotency: create output directory if missing
    output_path.mkdir(parents=True, exist_ok=True)

    total = 0
    extracted = 0
    failed = 0

    for mhtml_file in mhtml_files:
        total += 1
        stem = mhtml_file.stem
        out_file = output_path / f"{stem}.html"

        html_content = _extract_html_from_mhtml(mhtml_file)

        if html_content is None:
            print(f"⚠️  No HTML content found in: {mhtml_file.name}")
            failed += 1
        else:
            out_file.write_text(html_content, encoding="utf-8")
            print(f"✅ Extracted: {mhtml_file.name}")
            extracted += 1

    print(f"\n📊 Bronze Summary:")
    print(f"Total: {total} | Extracted: {extracted} | Failed: {failed}")


def _extract_html_from_mhtml(mhtml_path: Path) -> str | None:
    """Parse an MHTML file and return the text/html payload as a decoded string."""
    raw = mhtml_path.read_bytes()

    # MHTML is a MIME multipart message — parse it like email
    msg = email.message_from_bytes(raw)

    html_part = _find_html_part(msg)
    if html_part is None:
        return None

    payload = html_part.get_payload(decode=True)  # decode=True handles base64 / QP
    if payload is None:
        return None

    charset = html_part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return payload.decode("utf-8", errors="replace")


def _find_html_part(msg) -> email.message.Message | None:
    """Recursively search a MIME message for the first text/html part."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part
    else:
        if msg.get_content_type() == "text/html":
            return msg
    return None