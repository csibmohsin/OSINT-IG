"""Guards against the documentation drifting away from the code."""
import re
from pathlib import Path

import pytest

import osint_ig.api.app as appmod
import osint_ig.ai.gemini_analyzer as gemini_svc
from osint_ig.engine.modules import tool_specs

GUIDE = Path(__file__).resolve().parent.parent.parent / "docs" / "operator-guide.md"
SOURCES = [
    "osint_ig/engine/runner.py",
    "osint_ig/api/app.py",
    "osint_ig/ai/gemini_analyzer.py",
    "osint_ig/instagram/auth.py",
]


@pytest.fixture(scope="module")
def guide():
    return GUIDE.read_text(encoding="utf-8")


def test_the_guide_exists_and_the_readme_links_to_it(guide):
    readme = (GUIDE.parent.parent / "README.md").read_text(encoding="utf-8")
    assert "docs/operator-guide.md" in readme
    assert "OSINT IG" in readme
    assert len(guide.splitlines()) > 50


def test_every_environment_variable_is_documented(guide):
    root = GUIDE.parent.parent
    code = "".join((root / path).read_text(encoding="utf-8") for path in SOURCES)
    variables = set(re.findall(r'os\.getenv\("([A-Z][A-Z0-9_]+)"', code))
    assert variables
    assert sorted(v for v in variables if v not in guide) == []


def test_the_command_count_is_current(guide):
    assert f"{len(tool_specs())} commands" in guide


def test_every_command_is_mentioned_by_its_ui_name(guide):
    app_js = (GUIDE.parent.parent / "frontend/js/app.js").read_text(encoding="utf-8")
    labels = dict(re.findall(r'^\s{4}(\w+):\s*"([^"]+)"', app_js, re.M))
    assert len(labels) >= len(tool_specs()), "could not read TOOL_LABELS from app.js"
    missing = sorted(labels[s["name"]] for s in tool_specs() if s["name"] in labels and labels[s["name"]] not in guide)
    assert missing == []


def test_internal_anchors_resolve(guide):
    def slug(heading):
        return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", heading.strip().lower())).strip("-")

    headings = {slug(m.group(2)) for m in re.finditer(r"^(#{1,6})\s+(.*)$", guide, re.M)}
    broken = [link for link in re.findall(r"\]\(#([^)]+)\)", guide) if link not in headings]
    assert broken == []


def test_documented_defaults_match_the_code(guide):
    assert f"`{gemini_svc.DEFAULT_MODEL}`" in guide
    assert f"`{appmod.CACHE_PATH}`" in guide
    for spec in tool_specs():
        for param in spec["params"]:
            if param["name"] == "limit" and spec["name"] == "get_followers":
                assert f"`limit` ({param['default']})" in guide
