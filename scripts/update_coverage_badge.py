"""Generate the repository coverage badge from coverage.py XML output."""

from __future__ import annotations

import pathlib

import defusedxml.ElementTree as ET

COVERAGE_XML = pathlib.Path("coverage.xml")
BADGE_SVG = pathlib.Path("media/coverage-badge.svg")
EXCELLENT_COVERAGE = 90
GOOD_COVERAGE = 80
FAIR_COVERAGE = 70
LOW_COVERAGE = 60


def _coverage_color(percent: float) -> str:
    if percent >= EXCELLENT_COVERAGE:
        return "#4c1"
    if percent >= GOOD_COVERAGE:
        return "#67ac09"
    if percent >= FAIR_COVERAGE:
        return "#dfb317"
    if percent >= LOW_COVERAGE:
        return "#fe7d37"
    return "#e05d44"


def _text_width(text: str) -> int:
    return 10 * len(text) + 3


def _render_badge(percent: float) -> str:
    label = "coverage"
    value = f"{percent:.2f}%"
    label_width = _text_width(label)
    value_width = _text_width(value)
    width = label_width + value_width
    label_x = label_width * 5
    value_x = label_width * 10 + value_width * 5
    color = _coverage_color(percent)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" '
        f'role="img" aria-label="{label}: {value}"><title>{label}: {value}</title>'
        '<filter id="blur"><feGaussianBlur stdDeviation="16"/></filter>'
        '<linearGradient id="s" x2="0" y2="100%">'
        '<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        '<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{width}" height="20" rx="3"/></clipPath>'
        f'<g clip-path="url(#r)"><rect width="{label_width}" height="20" fill="#555"/>'
        f'<rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>'
        f'<rect width="{width}" height="20" fill="url(#s)"/></g>'
        '<g fill="#fff" text-anchor="middle" '
        'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        'text-rendering="geometricPrecision" font-size="110">'
        '<g transform="scale(.1)"><g aria-hidden="true" fill="#010101">'
        f'<text x="{label_x}" y="150" fill-opacity=".8" filter="url(#blur)" '
        f'textLength="{label_width * 10 - 10}">{label}</text>'
        f'<text x="{label_x}" y="150" fill-opacity=".3" '
        f'textLength="{label_width * 10 - 10}">{label}</text></g>'
        f'<text x="{label_x}" y="140" textLength="{label_width * 10 - 10}">'
        f"{label}</text></g>"
        '<g transform="scale(.1)"><g aria-hidden="true" fill="#010101">'
        f'<text x="{value_x}" y="150" fill-opacity=".8" filter="url(#blur)" '
        f'textLength="{value_width * 10 - 10}">{value}</text>'
        f'<text x="{value_x}" y="150" fill-opacity=".3" '
        f'textLength="{value_width * 10 - 10}">{value}</text></g>'
        f'<text x="{value_x}" y="140" textLength="{value_width * 10 - 10}">'
        f"{value}</text></g></g></svg>"
    )


def main() -> None:
    line_rate = float(ET.parse(COVERAGE_XML).getroot().attrib["line-rate"])
    badge = _render_badge(line_rate * 100)

    if BADGE_SVG.exists() and BADGE_SVG.read_text() == badge:
        return

    BADGE_SVG.write_text(badge)


if __name__ == "__main__":
    main()
