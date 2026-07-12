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


def main():
    parser = ArgumentParser()
    parser.add_argument("command", choices=["all", "xml", "text", "html", "validate", "release", "clean"])
    parser.add_argument("--revision")
    args = parser.parse_args()

    if args.command == "clean":
        shutil.rmtree(BUILD, ignore_errors=True)
        return

    if args.command == "release":
        if not args.revision or not re.fullmatch(r"\d{2}", args.revision):
            raise SystemExit("release requires --revision NN")
        docname = f"{BASE}-{args.revision}"
        output_dir = ROOT / "release" / args.revision
    else:
        docname = f"{BASE}-latest"
        output_dir = BUILD

    generate(docname, output_dir)
    if args.command in {"all", "validate", "release"}:
        validate_repository()


if __name__ == "__main__":
    main()
