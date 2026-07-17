"""PAMSPEC draft build tool.

Two build modes:

- Internal build (default): produces `draft-...-latest.{xml,txt,html}`
  in `build/`. Uses neutral candidate naming; MUST NOT be described
  as a numbered IETF revision.

- Submission candidate: produces a numbered rendering to be
  reviewed before actual Datatracker submission. Only allowed under
  an explicit `submission-candidate` command AND only for the
  revision number permitted by `pamspec-version.json` at the time.

Revision policy (enforced by this script):

- While `ietf_submission_status == "not_submitted"`, the only
  permitted submission-candidate revision is "00".
- After posted revisions exist (`posted_datatracker_revisions` is
  non-empty), the only permitted next revision is the successor
  of the highest posted revision (zero-padded to two digits).

Generating a submission candidate MUST NOT modify
`posted_datatracker_revisions`. Marking a revision as posted is a
separate manual step that follows actual Datatracker submission.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "draft-infantado-agent-memory-architecture.md"
BASE = "draft-infantado-agent-memory-architecture"
BUILD = ROOT / "build"
VERSION_MANIFEST = ROOT / "pamspec-version.json"


def tool(name: str):
    found = shutil.which(name)
    if found:
        return found
    candidates = [
        Path(r"C:\Ruby33-x64\bin") / f"{name}.bat",
        Path(sys.executable).parent / "Scripts" / f"{name}.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(f"required build tool not found: {name}")


def run(*args, stdout=None):
    subprocess.run(args, cwd=ROOT, check=True, stdout=stdout)


def source_for(docname: str):
    text = SOURCE.read_text(encoding="utf-8")
    text = re.sub(r"^docname: .+$", f"docname: {docname}", text, count=1, flags=re.MULTILINE)
    BUILD.mkdir(parents=True, exist_ok=True)
    temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".md",
        prefix=f"{BASE}-",
        delete=False,
        dir=BUILD,
        newline="\n",
    )
    with temp:
        temp.write(text)
    return Path(temp.name)


def generate(docname: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    source = source_for(docname)
    xml = output_dir / f"{docname}.xml"
    txt = output_dir / f"{docname}.txt"
    html = output_dir / f"{docname}.html"
    try:
        with xml.open("wb") as handle:
            run(tool("kramdown-rfc"), "--v3", str(source), stdout=handle)
        run(tool("xml2rfc"), "--v3", "--strict", str(xml), "--out", str(output_dir / f"{docname}.validated.xml"))
        run(tool("xml2rfc"), "--text", "--out", str(txt), str(xml))
        run(tool("xml2rfc"), "--html", "--out", str(html), str(xml))
        (output_dir / f"{docname}.validated.xml").unlink(missing_ok=True)
    finally:
        source.unlink(missing_ok=True)
    return xml, txt, html


def validate_repository():
    run(sys.executable, "scripts/validate_repository.py")
    run(sys.executable, "scripts/validate_test_vectors.py")


def permitted_submission_candidate_revision() -> str:
    """Compute the ONE revision number permitted for a submission
    candidate right now, from pamspec-version.json.
    """
    if not VERSION_MANIFEST.exists():
        raise SystemExit(
            "cannot determine permitted revision: pamspec-version.json missing"
        )
    try:
        manifest = json.loads(VERSION_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"pamspec-version.json is not valid JSON: {e}")

    status = manifest.get("ietf_submission_status")
    posted = manifest.get("posted_datatracker_revisions", [])
    if not isinstance(posted, list):
        raise SystemExit("posted_datatracker_revisions in manifest must be a list")

    if status == "not_submitted":
        if posted:
            raise SystemExit(
                "manifest inconsistent: ietf_submission_status is 'not_submitted' "
                "but posted_datatracker_revisions is non-empty"
            )
        return "00"

    if status == "submitted":
        if not posted:
            raise SystemExit(
                "manifest inconsistent: ietf_submission_status is 'submitted' "
                "but posted_datatracker_revisions is empty"
            )
        valid_revs = [r for r in posted if isinstance(r, str) and re.fullmatch(r"\d{2}", r)]
        if not valid_revs:
            raise SystemExit(
                "posted_datatracker_revisions must contain 'NN' strings only"
            )
        highest = max(int(r) for r in valid_revs)
        return f"{highest + 1:02d}"

    raise SystemExit(
        f"pamspec-version.json ietf_submission_status must be "
        f"'not_submitted' or 'submitted', got {status!r}"
    )


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["all", "xml", "text", "html", "validate", "submission-candidate", "release", "clean"],
        help="'all'/'xml'/'text'/'html'/'validate' build the neutral -latest "
             "internal artifact. 'submission-candidate' produces a numbered "
             "rendering for IETF submission review (revision guarded by "
             "manifest policy). 'release' is a deprecated alias that now "
             "requires the same guards as 'submission-candidate'.",
    )
    parser.add_argument(
        "--revision",
        help="Revision NN. REQUIRED for submission-candidate. MUST match the "
             "revision permitted by pamspec-version.json at build time.",
    )
    parser.add_argument(
        "--confirm-submission-candidate",
        action="store_true",
        help="Required acknowledgement for submission-candidate mode: "
             "confirms the caller understands this build is a candidate "
             "for IETF submission review, is not itself a submission, and "
             "will NOT be marked as posted in pamspec-version.json.",
    )
    args = parser.parse_args()

    if args.command == "clean":
        shutil.rmtree(BUILD, ignore_errors=True)
        return

    if args.command in {"submission-candidate", "release"}:
        if args.command == "release":
            print(
                "WARNING: 'release' is deprecated in favor of "
                "'submission-candidate'; the same guards apply.",
                file=sys.stderr,
            )
        if not args.confirm_submission_candidate:
            raise SystemExit(
                "submission-candidate requires --confirm-submission-candidate. "
                "This mode produces a numbered rendering for IETF submission "
                "review. It does NOT post the draft to Datatracker and does "
                "NOT update pamspec-version.json."
            )
        if not args.revision or not re.fullmatch(r"\d{2}", args.revision):
            raise SystemExit(
                "submission-candidate requires --revision NN (two-digit)"
            )
        permitted = permitted_submission_candidate_revision()
        if args.revision != permitted:
            raise SystemExit(
                f"submission-candidate revision {args.revision!r} is not "
                f"permitted right now. The manifest allows exactly one "
                f"revision: {permitted!r}. If a posting has occurred but the "
                f"manifest was not updated, update posted_datatracker_revisions "
                f"in pamspec-version.json first."
            )
        docname = f"{BASE}-{args.revision}"
        output_dir = ROOT / "submission-candidates" / args.revision
    else:
        docname = f"{BASE}-latest"
        output_dir = BUILD

    generate(docname, output_dir)
    if args.command in {"all", "validate", "submission-candidate", "release"}:
        validate_repository()


if __name__ == "__main__":
    main()
