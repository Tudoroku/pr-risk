from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class PatchLine:
    file_path: str
    change_type: str
    content: str


def iter_changed_lines(patch_text: str) -> Iterable[PatchLine]:
    current_file = ""

    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            current_file = _parse_diff_git_path(line)
            continue

        if _is_metadata_line(line):
            continue

        if line.startswith("+"):
            yield PatchLine(current_file, "added", line[1:])
        elif line.startswith("-"):
            yield PatchLine(current_file, "removed", line[1:])


def _parse_diff_git_path(line: str) -> str:
    prefix = "diff --git a/"
    separator = " b/"

    if not line.startswith(prefix):
        return ""

    paths = line[len(prefix) :].split(separator, maxsplit=1)
    if len(paths) != 2:
        return ""

    return paths[1]


def _is_metadata_line(line: str) -> bool:
    return (
        line.startswith("+++ ")
        or line.startswith("--- ")
        or line.startswith("@@ ")
        or line.startswith("index ")
        or line.startswith("new file mode ")
        or line.startswith("deleted file mode ")
    )
