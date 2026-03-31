import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_RE_TK_HEADER = re.compile(r"^###\s*ТК-(\d+)\.\s*")


def _project_root() -> Path:
    # tests/utils -> tests -> pythonProject
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=None)
def _load_checks_md(entity: str) -> str:
    path = _project_root() / "docs" / entity / "checks_smoke.md"
    if not path.is_file():
        raise FileNotFoundError(f"Не найден файл с описаниями smoke: {path}")
    return path.read_text(encoding="utf-8")


def _extract_table_row_for_tk(md: str, tk_num: int) -> Optional[Tuple[str, str, str]]:
    """
    Returns (title, what_checked, expected) from the markdown table.
    If parsing fails, returns None.
    """
    # Table rows look like: | 1 | Smoke: PUT ... | ... | 200, ... |
    # We keep it simple: split by lines and regex for the first 4 columns.
    pattern = re.compile(rf"^\|\s*{tk_num}\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
    for line in md.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        title = m.group(1).strip()
        what_checked = m.group(2).strip()
        expected = m.group(3).strip()
        return title, what_checked, expected
    return None


def _parse_detailed_tk_block(lines: List[str]) -> Tuple[str, List[str], str]:
    """
    Parse a single TK block and return:
    - preconditions text
    - steps lines (already numbered lines with possible continuations)
    - expected result text
    """
    preconditions_parts: List[str] = []
    steps_parts: List[str] = []
    expected_parts: List[str] = []

    state: Optional[str] = None

    for raw in lines:
        line = raw.rstrip("\n")

        if "**Предусловия:**" in line:
            state = "pre"
            after = line.split("**Предусловия:**", 1)[1].strip()
            if after:
                preconditions_parts.append(after)
            continue

        if "**Шаги:**" in line:
            state = "steps"
            after = line.split("**Шаги:**", 1)[1].strip()
            if after:
                steps_parts.append(after)
            continue

        if "**Ожидаемый результат:**" in line:
            state = "expected"
            after = line.split("**Ожидаемый результат:**", 1)[1].strip()
            if after:
                expected_parts.append(after)
            continue

        # Ignore empty lines outside the steps section to keep output compact.
        if state == "pre":
            if line.strip():
                preconditions_parts.append(line.strip())
        elif state == "steps":
            if line.strip():
                steps_parts.append(line.strip())
        elif state == "expected":
            if line.strip():
                expected_parts.append(line.strip())

    pre = " ".join(preconditions_parts).strip()

    # Normalize steps: keep numbered lines, merge continuations into previous step.
    merged_steps: List[str] = []
    for s in steps_parts:
        if re.match(r"^\d+\.\s+", s):
            merged_steps.append(s)
        elif merged_steps:
            merged_steps[-1] = f"{merged_steps[-1]} {s}".strip()
        else:
            merged_steps.append(s)

    expected = " ".join(expected_parts).strip()
    return pre, merged_steps, expected


def _build_description_from_block(pre: str, steps: List[str], expected: str, *, title: Optional[str] = None) -> str:
    title_part = f"{title}\n\n" if title else ""
    steps_part = "\n".join(steps)
    return (
        f"{title_part}Предусловия:\n{pre or '-'}\n\n"
        f"Шаги:\n{steps_part or '-'}\n\n"
        f"Ожидаемый результат:\n{expected or '-'}"
    )


@lru_cache(maxsize=None)
def get_smoke_tc_description(entity: str, tk_num: int) -> str:
    """
    Get detailed description for smoke test case TK-<tk_num> from docs/<entity>/checks_smoke.md.
    If detailed block is missing (e.g. ТК-3…ТК-9 merged), falls back to the table row.
    """
    md = _load_checks_md(entity)
    lines = md.splitlines()

    # Find block start for "### ТК-<n>."
    start_idx: Optional[int] = None
    for i, line in enumerate(lines):
        m = _RE_TK_HEADER.match(line.strip())
        if m and int(m.group(1)) == tk_num:
            start_idx = i
            break
    if start_idx is not None:
        # End is the next "### ТК-" header (any format: "ТК-3.", "ТК-3…ТК-9", etc).
        # This prevents "ТК-2" from consuming text that actually belongs to a merged range.
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if lines[j].strip().startswith("### ТК-"):
                end_idx = j
                break

        block_lines = lines[start_idx:end_idx]

        # Title in header line (after the dot)
        header_line = block_lines[0].strip()
        title_after = header_line.split(".", 1)[1].strip() if "." in header_line else header_line

        pre, steps, expected = _parse_detailed_tk_block(block_lines)
        return _build_description_from_block(pre, steps, expected, title=title_after)

    # Fallback: table row (shorter)
    row = _extract_table_row_for_tk(md, tk_num)
    if row:
        title, what_checked, expected = row
        return (
            f"{title}\n\n"
            f"Что проверяется:\n{what_checked}\n\n"
            f"Ожидаемый результат:\n{expected}"
        )

    # Last resort
    return f"ТК-{tk_num}. Описание в {entity}/checks_smoke.md не найдено."

