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
    versions = re.findall(r"python-version: (\[.*\]|\"[\d.]+\")", workflow)
    tested = {v for line in versions for v in re.findall(r"\"([\d.]+)\"", line)}
    assert declared() in tested


# ==================================================
def test_classifiers_start_at_lowest_version():
    classifiers = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["classifiers"]
    versions = [c.split("::")[-1].strip() for c in classifiers if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)]
    assert min(versions, key=lambda v: int(v.split(".")[1])) == declared()


# ==================================================
def test_documents_tell_lowest_version():
    for file in ["docs/README.md", "docs/src/install.md"]:
        text = (ROOT / file).read_text()
        mentioned = set(re.findall(r"Python (?:>= ?|≥ ?)?(3\.\d+)", text))
        assert mentioned == {declared()}, file
