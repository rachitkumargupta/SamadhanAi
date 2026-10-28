
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PolicyDocument:
    policy_id: str
    title: str
    source: str
    text: str
    status: str = "UNVERIFIED"


def determine_policy_status(text: str) -> str:
    """
    Classify documents using their declared status.

    A declaration is not proof of authenticity. Official documents
    still require source and applicability verification.
    """
    normalized = text.upper()

    if (
        "DRAFT - NOT OFFICIAL MUNICIPAL POLICY" in normalized
        or "DRAFT - NOT OFFICIAL" in normalized
    ):
        return "DRAFT"

    if "DOCUMENT_STATUS: OFFICIAL_VERIFIED" in normalized:
        # This marker alone does not prove authenticity.
        # Only use it after the source has been independently verified.
        return "UNVERIFIED"

    return "UNVERIFIED"


def load_policy_documents(
    directory: str = "policies",
) -> list[PolicyDocument]:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    documents: list[PolicyDocument] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        try:
            if path.suffix.lower() == ".txt":
                text = path.read_text(encoding="utf-8")

            elif path.suffix.lower() == ".pdf":
                reader = PdfReader(str(path))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            else:
                # Ignore .gitkeep and unsupported file types.
                continue

        except Exception as exc:
            print(f"Could not read {path.name}: {exc}")
            continue

        text = text.strip()

        if not text:
            print(f"No extractable text found in {path.name}")
            continue

        first_lines = text.splitlines()[:10]
        header = "\n".join(first_lines)

        # Prefer a declared document ID; otherwise use the filename.
        policy_id = path.stem

        for line in header.splitlines():
            if line.strip().upper().startswith("DOCUMENT_ID:"):
                policy_id = line.split(":", 1)[1].strip()
                break

        # Prefer a declared title; otherwise derive one from the filename.
        title = path.stem.replace("_", " ")

        for line in header.splitlines():
            if line.strip().upper().startswith("TITLE:"):
                title = line.split(":", 1)[1].strip()
                break

        status = determine_policy_status(text)

        documents.append(
            PolicyDocument(
                policy_id=policy_id,
                title=title,
                source=str(path),
                text=text,
                status=status,
            )
        )

    return documents
