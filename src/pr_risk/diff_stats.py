from dataclasses import dataclass


@dataclass(frozen=True)
class DiffStats:
    files_changed: int
    lines_added: int
    lines_deleted: int
    total_churn: int
    binary_files_changed: int = 0


def parse_numstat(numstat_text: str) -> DiffStats:
    files_changed = 0
    lines_added = 0
    lines_deleted = 0
    binary_files_changed = 0

    for line in numstat_text.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t", maxsplit=2)
        if len(parts) != 3:
            continue

        added, deleted, _path = parts
        files_changed += 1

        if added == "-" and deleted == "-":
            binary_files_changed += 1
            continue

        lines_added += int(added)
        lines_deleted += int(deleted)

    return DiffStats(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        total_churn=lines_added + lines_deleted,
        binary_files_changed=binary_files_changed,
    )
