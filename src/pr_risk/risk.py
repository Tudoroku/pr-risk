from dataclasses import dataclass


TEST_FILE_SUFFIXES = (
    "_test.c",
    "_test.cc",
    "_test.cpp",
    "_test.cxx",
    "_test.h",
    "_test.hpp",
    "_test.hh",
    "_test.hxx",
    "_test.py",
)
CMAKE_BUILD_FILE_SCORE = 25
HEADER_API_FILE_SCORE = 25
PER_SOURCE_FILE_SCORE = 5
MAX_SOURCE_FILE_SCORE = 25
DIRECTORY_RISK_SCORE = 10
MISSING_TESTS_SCORE = 25
MAX_RISK_SCORE = 100
LOW_RISK_MAX_SCORE = 39
MEDIUM_RISK_MAX_SCORE = 69


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

    if all(_is_documentation_file(path) for path in changed_files):
        return RiskResult(
            score=0,
            level="LOW",
            reasons=["Only documentation files changed"],
        )

    if any(_is_cmake_file(path) for path in changed_files):
        score += CMAKE_BUILD_FILE_SCORE
        reasons.append("Build system files changed")

    if any(_is_header_file(path) for path in changed_files):
        score += HEADER_API_FILE_SCORE
        reasons.append("Header/API files changed")

    source_count = sum(1 for path in changed_files if _is_source_file(path))
    if source_count:
        source_score = min(source_count * PER_SOURCE_FILE_SCORE, MAX_SOURCE_FILE_SCORE)
        score += source_score
        reasons.append("Source implementation files changed")

    if any(_is_under_directory(path, {"src", "lib"}) for path in changed_files):
        score += DIRECTORY_RISK_SCORE
        reasons.append("Production code changed")

    if any(_is_under_directory(path, {"include"}) for path in changed_files):
        score += DIRECTORY_RISK_SCORE
        reasons.append("Public API directory changed")

    if any(_is_under_directory(path, {"cmake"}) for path in changed_files):
        score += DIRECTORY_RISK_SCORE
        reasons.append("Build configuration directory changed")

    if any(_is_under_directory(path, {"third_party", "vendor"}) for path in changed_files):
        score += DIRECTORY_RISK_SCORE
        reasons.append("Vendor/dependency files changed")

    if not any(_is_test_file(path) for path in changed_files):
        score += MISSING_TESTS_SCORE
        reasons.append("No test files changed")

    if not reasons:
        reasons.append("Only low-risk files changed")

    score = min(score, MAX_RISK_SCORE)
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
        or filename.endswith(TEST_FILE_SUFFIXES)
    )


def _is_documentation_file(path: str) -> bool:
    normalized = path.replace("\\", "/").lower().lstrip("./")
    filename = normalized.rsplit("/", maxsplit=1)[-1]
    return (
        _is_under_directory(normalized, {"docs"})
        or filename == "readme"
        or filename.startswith("readme.")
        or _extension(normalized) in {".md", ".markdown"}
    )


def _is_under_directory(path: str, directories: set[str]) -> bool:
    parts = path.replace("\\", "/").lower().lstrip("./").split("/")
    return len(parts) > 1 and parts[0] in directories


def _extension(path: str) -> str:
    filename = path.replace("\\", "/").rsplit("/", maxsplit=1)[-1].lower()
    dot_index = filename.rfind(".")
    if dot_index == -1:
        return ""
    return filename[dot_index:]


def _risk_level(score: int) -> str:
    if score == 0:
        return "LOW"
    if score <= LOW_RISK_MAX_SCORE:
        return "LOW"
    if score <= MEDIUM_RISK_MAX_SCORE:
        return "MEDIUM"
    return "HIGH"
