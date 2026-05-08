from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    reasons: list[str]


def calculate_risk(changed_files: list[str]) -> RiskResult:
    reasons: list[str] = []
    score = 0

    if not changed_files:
        return RiskResult(score=0, level="LOW", reasons=["No changed files"])

    if any(_is_cmake_file(path) for path in changed_files):
        score += 25
        reasons.append("Build system files changed")

    if any(_is_header_file(path) for path in changed_files):
        score += 25
        reasons.append("Header/API files changed")

    source_count = sum(1 for path in changed_files if _is_source_file(path))
    if source_count:
        source_score = min(source_count * 5, 25)
        score += source_score
        reasons.append("Source implementation files changed")

    if not any(_is_test_file(path) for path in changed_files):
        score += 25
        reasons.append("No test files changed")

    score = min(score, 100)
    return RiskResult(score=score, level=_risk_level(score), reasons=reasons)


def _is_cmake_file(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return (
        normalized.endswith("/cmakelists.txt")
        or normalized == "cmakelists.txt"
        or normalized.endswith(".cmake")
    )


def _is_header_file(path: str) -> bool:
    return _extension(path) in {".h", ".hh", ".hpp", ".hxx"}


def _is_source_file(path: str) -> bool:
    return _extension(path) in {".c", ".cc", ".cpp", ".cxx"}


def _is_test_file(path: str) -> bool:
    parts = path.replace("\\", "/").lower().split("/")
    filename = parts[-1]
    return (
        "tests" in parts
        or filename.startswith("test_")
        or filename.endswith("_test.cpp")
        or filename.endswith("_test.py")
    )


def _extension(path: str) -> str:
    filename = path.replace("\\", "/").rsplit("/", maxsplit=1)[-1].lower()
    dot_index = filename.rfind(".")
    if dot_index == -1:
        return ""
    return filename[dot_index:]


def _risk_level(score: int) -> str:
    if score == 0:
        return "NONE"
    if score <= 39:
        return "LOW"
    if score <= 69:
        return "MEDIUM"
    return "HIGH"
