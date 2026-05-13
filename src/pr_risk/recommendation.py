from pr_risk.risk import RiskResult
from pr_risk.runner import ExecutionResult


DO_NOT_MERGE_UNTIL_BUILD_PASSES = "do_not_merge_until_build_passes"
DO_NOT_MERGE_UNTIL_TESTS_PASS = "do_not_merge_until_tests_pass"
INVESTIGATE_EXECUTION_TIMEOUT = "investigate_execution_timeout"
REQUIRE_SENIOR_REVIEW = "require_senior_review"
CAREFUL_REVIEW = "careful_review"
NORMAL_REVIEW = "normal_review"


def recommend_review(
    risk_result: RiskResult,
    execution_result: ExecutionResult | None = None,
) -> str:
    if execution_result is not None:
        build_result = execution_result.build
        test_result = execution_result.test

        if _command_failed(build_result):
            return DO_NOT_MERGE_UNTIL_BUILD_PASSES

        if _command_failed(test_result):
            return DO_NOT_MERGE_UNTIL_TESTS_PASS

        if _command_timed_out(build_result) or _command_timed_out(test_result):
            return INVESTIGATE_EXECUTION_TIMEOUT

    if risk_result.level == "HIGH":
        return REQUIRE_SENIOR_REVIEW

    if risk_result.level == "MEDIUM":
        return CAREFUL_REVIEW

    return NORMAL_REVIEW


def _command_failed(command_result: object | None) -> bool:
    if command_result is None:
        return False

    if _command_timed_out(command_result):
        return False

    exit_code = getattr(command_result, "exit_code", None)
    return exit_code is not None and exit_code != 0


def _command_timed_out(command_result: object | None) -> bool:
    if command_result is None:
        return False

    return getattr(command_result, "timed_out", False) is True
