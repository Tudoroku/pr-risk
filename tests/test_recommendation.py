from pr_risk.recommendation import recommend_review
from pr_risk.risk import RiskResult
from pr_risk.runner import CommandResult, ExecutionResult


def test_low_risk_gets_normal_review():
    assert recommend_review(_risk_result("LOW")) == "normal_review"


def test_medium_risk_gets_careful_review():
    assert recommend_review(_risk_result("MEDIUM")) == "careful_review"


def test_high_risk_gets_senior_review():
    assert recommend_review(_risk_result("HIGH")) == "require_senior_review"


def test_build_failed_overrides_score_level_recommendation():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(build=_command_result(exit_code=1), test=None),
    )

    assert recommendation == "do_not_merge_until_build_passes"


def test_build_failed_overrides_score_level_recommendation_with_docker_executor():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(build=_command_result(exit_code=1), test=None, executor="docker"),
    )

    assert recommendation == "do_not_merge_until_build_passes"


def test_tests_failed_overrides_score_level_recommendation():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(build=_command_result(exit_code=0), test=_command_result(exit_code=1)),
    )

    assert recommendation == "do_not_merge_until_tests_pass"


def test_timeout_recommendation_works():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(build=_command_result(exit_code=0), test=_command_result(timed_out=True)),
    )

    assert recommendation == "investigate_execution_timeout"


def test_build_timeout_with_skipped_test_gives_timeout_recommendation():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(
            build=_command_result(timed_out=True),
            test=None,
            test_skipped=True,
            test_skip_reason="Build timed out",
        ),
    )

    assert recommendation == "investigate_execution_timeout"


def test_skipped_tests_because_build_failed_gives_build_recommendation():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(
            build=_command_result(exit_code=1),
            test=None,
            test_skipped=True,
            test_skip_reason="Build failed",
        ),
    )

    assert recommendation == "do_not_merge_until_build_passes"


def test_execution_result_none_still_gives_score_level_recommendation():
    assert recommend_review(_risk_result("HIGH"), execution_result=None) == "require_senior_review"


def test_no_commands_configured_still_gives_score_level_recommendation():
    recommendation = recommend_review(
        _risk_result("MEDIUM"),
        ExecutionResult(build=None, test=None),
    )

    assert recommendation == "careful_review"


def test_timeout_is_not_treated_as_failure():
    recommendation = recommend_review(
        _risk_result("LOW"),
        ExecutionResult(
            build=_command_result(exit_code=1, timed_out=True),
            test=_command_result(exit_code=1, timed_out=True),
        ),
    )

    assert recommendation == "investigate_execution_timeout"


def _risk_result(level: str) -> RiskResult:
    return RiskResult(score=0, level=level, reasons=[])


def _command_result(exit_code: int | None = 0, timed_out: bool = False) -> CommandResult:
    return CommandResult(
        name="command",
        command="command",
        exit_code=exit_code,
        stdout="",
        stderr="",
        timed_out=timed_out,
        duration_seconds=1.0,
    )
