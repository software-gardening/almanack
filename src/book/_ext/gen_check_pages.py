"""
Sphinx extension to help generate pages for each linting check
in the almanack metrics catalog.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader
from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


def generate_check_pages(app: Sphinx, config: Any) -> None:
    """Generate Markdown pages from the metrics.yml catalog.

    Expects metrics.yml of the form:

        metrics:
          - name: "repo-path"
            id: "SGA-META-0001"
            description: "…"
            fix-how: "How to fix"
            fix-why: "Why to fix"
            …

    This will render one `checks/<id>.md` per metric plus an `index.md`.
    """
    logger.warning(f"[DEBUG] generate_check_pages firing; confdir={app.confdir}")
    confdir = Path(app.confdir)
    srcdir = Path(app.srcdir)

    # locate your YAML
    project_root = confdir.parents[1]
    yaml_path = project_root / "src" / "almanack" / "metrics" / "metrics.yml"

    logger.warning(f"[DEBUG] loading YAML from {yaml_path}")
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # extract the list under `metrics`
    metrics_list: Any = raw.get("metrics")
    if not isinstance(metrics_list, list):
        raise RuntimeError(f"Expected 'metrics' to be a list in {yaml_path}")

    # normalize each entry
    checks: List[Dict[str, Any]] = []
    for entry in metrics_list:
        cid = entry.get("id")
        if not cid:
            raise RuntimeError(f"Metric missing `id`: {entry}")
        checks.append(
            {
                "id": cid,
                "name": entry.get("name", cid),
                "description": (entry.get("description") or "").strip(),
                "how": (entry.get("fix_how") or "").strip(),
                "why": (entry.get("fix_why") or "").strip(),
                "sustainability_correlation": entry.get(
                    "sustainability_correlation", 0
                ),
            }
        )

    # prepare Jinja
    template_dir = confdir / "_templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
        autoescape=True,
    )
    template = env.get_template("check_template.md.j2")

    # output directory
    out = srcdir / "checks"
    out.mkdir(parents=True, exist_ok=True)

    # render each metric → <id>.md
    checks = [check for check in checks if check.get("sustainability_correlation") != 0]
    for check in checks:
        rendered = template.render(check=check)
        (out / f"{check['id']}.md").write_text(rendered, encoding="utf-8")

    # write an index.md
    idx_lines = [
        "# Checks index",
        "",
        "This is an index of all checks in the Almanack metrics catalog.",
        "",
    ]
    for check in checks:
        idx_lines.append(f"- [{check['name']} ({check['id']})](./{check['id']}.md)")
    (out / "index.md").write_text("\n".join(idx_lines), encoding="utf-8")


def setup(app: Sphinx) -> None:
    # Hook on config-inited so pages exist before reading docs
    app.connect("config-inited", generate_check_pages)
