import re

from pr_risk.patch import iter_changed_lines


HEADER_EXTENSIONS = (".h", ".hh", ".hpp", ".hxx")
API_SIGNAL_TEMPLATE = "API-like header change detected in {file_path}"

CLASS_DECLARATION = re.compile(r"^(class|struct)\s+\w+(?:\s*[:;]|$)")
ENUM_DECLARATION = re.compile(r"^enum(?:\s+class)?\s+\w+(?:\s*[:;{]|$)")
FUNCTION_DECLARATION = re.compile(
    r"^(?!.*\boperator\b)(?:[\w:<>~*&,\s]+)\s+\w+\s*\([^{};]*\)\s*;"
)
TRAILING_RETURN_DECLARATION = re.compile(
    r"^auto\s+\w+\s*\([^{};]*\)\s*->\s*[^{};]+;"
)


def analyze_api_changes(patch_text: str) -> list[str]:
    signals = []
    seen_files = set()

    for changed_line in iter_changed_lines(patch_text):
        file_path = changed_line.file_path
        if file_path in seen_files:
            continue
        if not _is_header_file(file_path):
            continue
        if not _is_api_like_declaration(changed_line.content):
            continue

        seen_files.add(file_path)
        signals.append(API_SIGNAL_TEMPLATE.format(file_path=file_path))

    return signals


def _is_header_file(file_path: str) -> bool:
    return file_path.lower().endswith(HEADER_EXTENSIONS)


def _is_api_like_declaration(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _is_ignored_line(stripped):
        return False
    if stripped.endswith("{"):
        return False

    return (
        CLASS_DECLARATION.match(stripped) is not None
        or ENUM_DECLARATION.match(stripped) is not None
        or FUNCTION_DECLARATION.match(stripped) is not None
        or TRAILING_RETURN_DECLARATION.match(stripped) is not None
    )


def _is_ignored_line(stripped: str) -> bool:
    return (
        stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
        or stripped.startswith("#")
    )
