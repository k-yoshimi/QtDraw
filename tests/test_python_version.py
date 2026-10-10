"""
The lowest Python version declared in the package is the one in the documents, and it is tested.
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def declared():
    requires = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["requires-python"]
    return re.fullmatch(r">=(3\.\d+)", requires).group(1)


# ==================================================
def test_lowest_version_is_tested():
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text()
    workflow = re.sub(r"#.*", "", workflow)  # not commented-out entries.
    versions = re.findall(r"python-version:[ \t]+(\[.*\]|[\"'][\d.]+[\"'])", workflow)
    tested = {v for line in versions for v in re.findall(r"[\"']([\d.]+)[\"']", line)}
    assert declared() in tested


# ==================================================
def test_classifiers_start_at_lowest_version():
    classifiers = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["classifiers"]
    versions = [c.split("::")[-1].strip() for c in classifiers if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)]
    assert min(versions, key=lambda v: int(v.split(".")[1])) == declared()


# ==================================================
def test_documents_tell_lowest_version():
    lowest = int(declared().split(".")[1])
    for file in ["docs/README.md", "docs/src/install.md"]:
        text = (ROOT / file).read_text()
        # the lowest version: "Python >= 3.x", "Python ≥ 3.x" or "Python 3.x or later".
        minimum = r"python\s*(?:>=|≥)\s*3\.(\d+)|python\s*3\.(\d+)\s+or\s+later"
        stated = {int(a or b) for a, b in re.findall(minimum, text, flags=re.IGNORECASE)}
        assert stated == {lowest}, file
        # other versions, e.g. "brew install python@3.13", are not lower.
        mentioned = re.findall(r"python\s*[@>=≥]*\s*3\.(\d+)", text, flags=re.IGNORECASE)
        assert all(int(v) >= lowest for v in mentioned), file
