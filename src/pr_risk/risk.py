from dataclasses import dataclass

from pr_risk.diff_stats import DiffStats


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
LARGE_DIFF_SCORE_100 = 10
LARGE_DIFF_SCORE_300 = 20
LARGE_DIFF_SCORE_700 = 30
MANY_FILES_SCORE_10 = 15
MANY_FILES_SCORE_25 = 25
CMAKE_PATCH_SIGNAL_SCORE = 15
SENSITIVE_CMAKE_PATCH_SIGNAL_SCORE = 20
API_PATCH_SIGNAL_SCORE = 15
BUILD_FAILURE_SCORE = 30
TEST_FAILURE_SCORE = 25
BUILD_TIMEOUT_SCORE = 20
TEST_TIMEOUT_SCORE = 20
MAX_RISK_SCORE = 100
LOW_RISK_MAX_SCORE = 39
MEDIUM_RISK_MAX_SCORE = 69
SENSITIVE_CMAKE_SIGNALS = {
    "Library target changed",
    "Executable target changed",
    "Link dependencies changed",
    "Package dependency changed",
}


@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    reasons: list[str]


def calculate_risk(
    changed_files: list[str],
    diff_stats: DiffStats | None = None,
    cmake_signals: list[str] | None = None,
    api_signals: list[str] | None = None,
    execution_result: object | None = None,
) -> RiskResult:
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

    if cmake_signals:
        score += CMAKE_PATCH_SIGNAL_SCORE
        reasons.append("CMake patch signals detected")

        if any(signal in SENSITIVE_CMAKE_SIGNALS for signal in cmake_signals):
            score += SENSITIVE_CMAKE_PATCH_SIGNAL_SCORE
            reasons.append("Build/link/package configuration changed")

    if api_signals:
        score += API_PATCH_SIGNAL_SCORE
        reasons.append("API-like header changes detected")

    if diff_stats is not None:
        churn_score = _total_churn_score(diff_stats.total_churn)
        if churn_score:
            score += churn_score
            reasons.append(f"Large diff: {diff_stats.total_churn} changed lines")

        files_score = _files_changed_score(diff_stats.files_changed)
        if files_score:
            score += files_score
            reasons.append(f"Many files changed: {diff_stats.files_changed} files")

    execution_score, execution_reasons = _execution_score(execution_result)
    score += execution_score
    reasons.extend(execution_reasons)

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


def _total_churn_score(total_churn: int) -> int:
    if total_churn >= 700:
        return LARGE_DIFF_SCORE_700
    if total_churn >= 300:
        return LARGE_DIFF_SCORE_300
    if total_churn >= 100:
        return LARGE_DIFF_SCORE_100
    return 0


def _files_changed_score(files_changed: int) -> int:
    if files_changed >= 25:
        return MANY_FILES_SCORE_25
    if files_changed >= 10:
        return MANY_FILES_SCORE_10
    return 0


def _execution_score(execution_result: object | None) -> tuple[int, list[str]]:
    if execution_result is None:
        return 0, []

    score = 0
    reasons: list[str] = []
    build_result = getattr(execution_result, "build", None)
    test_result = getattr(execution_result, "test", None)

    if build_result is not None:
        if _command_timed_out(build_result):
            score += BUILD_TIMEOUT_SCORE
            reasons.append("Build command timed out")
        elif _command_failed(build_result):
            score += BUILD_FAILURE_SCORE
            reasons.append("Build failed")

    if test_result is not None:
        if _command_timed_out(test_result):
            score += TEST_TIMEOUT_SCORE
            reasons.append("Test command timed out")
        elif _command_failed(test_result):
            score += TEST_FAILURE_SCORE
            reasons.append("Tests failed")

    return score, reasons


def _command_timed_out(command_result: object) -> bool:
    return getattr(command_result, "timed_out", False) is True


def _command_failed(command_result: object) -> bool:
    exit_code = getattr(command_result, "exit_code", None)
    return exit_code is not None and exit_code != 0


def _risk_level(score: int) -> str:
    if score == 0:
        return "LOW"
    if score <= LOW_RISK_MAX_SCORE:
        return "LOW"
    if score <= MEDIUM_RISK_MAX_SCORE:
        return "MEDIUM"
    return "HIGH"
