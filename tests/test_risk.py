from pr_risk.diff_stats import DiffStats
from pr_risk.risk import RiskResult, calculate_risk


class ExecutionResultStub:
    def __init__(self, build=None, test=None):
        self.build = build
        self.test = test


class CommandResultStub:
    def __init__(self, exit_code=None, timed_out=False):
        self.exit_code = exit_code
        self.timed_out = timed_out


def test_no_changed_files_has_no_tests_risk():
    result = calculate_risk([])

    assert result == RiskResult(
        score=0,
        level="LOW",
        reasons=["No changed files"],
    )
    assert "No test files changed" not in result.reasons


def test_cmake_header_and_source_files_add_expected_score():
    result = calculate_risk(
        [
            "CMakeLists.txt",
            "include/widget.hpp",
            "src/widget.cpp",
            "tests/test_widget.cpp",
        ]
    )

    assert result.score == 80
    assert result.level == "HIGH"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
        "Production code changed",
        "Public API directory changed",
    ]


def test_build_system_files_add_expected_reason():
    result = calculate_risk(["src/CMakeLists.txt", "cmake/toolchain.cmake", "tests/build.py"])

    assert result.score == 45
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Build system files changed",
        "Production code changed",
        "Build configuration directory changed",
    ]


def test_header_api_files_add_expected_reason():
    result = calculate_risk(
        [
            "include/a.h",
            "include/b.hpp",
            "include/c.hh",
            "include/d.hxx",
            "tests/test_headers.py",
        ]
    )

    assert result.score == 35
    assert result.level == "LOW"
    assert result.reasons == [
        "Header/API files changed",
        "Public API directory changed",
    ]


def test_source_implementation_files_add_expected_reason():
    result = calculate_risk(
        [
            "src/a.c",
            "src/b.cc",
            "src/c.cpp",
            "src/d.cxx",
            "tests/test_sources.py",
        ]
    )

    assert result.score == 30
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
    ]


def test_source_file_score_is_capped_at_25():
    result = calculate_risk(
        [
            "src/a.cpp",
            "src/b.cc",
            "src/c.cxx",
            "src/d.c",
            "src/e.cpp",
            "src/f.cpp",
            "tests/test_sources.cpp",
        ]
    )

    assert result.score == 35
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
    ]


def test_no_test_files_changed_adds_25_points():
    result = calculate_risk(["src/widget.cpp"])

    assert result.score == 40
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "No test files changed",
    ]


def test_non_empty_low_risk_files_return_low_with_reason():
    result = calculate_risk(["tests/test_only.py"])

    assert result.score == 0
    assert result.level == "LOW"
    assert result.reasons == ["Only low-risk files changed"]


def test_production_directories_add_expected_reason():
    result = calculate_risk(["lib/widget.txt", "tests/test_widget.py"])

    assert result.score == 10
    assert result.level == "LOW"
    assert result.reasons == ["Production code changed"]


def test_public_api_directory_adds_expected_reason():
    result = calculate_risk(["include/api.txt", "tests/test_api.py"])

    assert result.score == 10
    assert result.level == "LOW"
    assert result.reasons == ["Public API directory changed"]


def test_build_configuration_directory_adds_expected_reason():
    result = calculate_risk(["cmake/presets.txt", "tests/test_build.py"])

    assert result.score == 10
    assert result.level == "LOW"
    assert result.reasons == ["Build configuration directory changed"]


def test_vendor_dependency_directories_add_expected_reason():
    result = calculate_risk(["third_party/package.txt", "vendor/lib.txt", "tests/test_deps.py"])

    assert result.score == 10
    assert result.level == "LOW"
    assert result.reasons == ["Vendor/dependency files changed"]


def test_docs_only_changes_stay_low_without_missing_test_reason():
    result = calculate_risk(["docs/guide.txt", "README", "notes.md", "nested/readme.markdown"])

    assert result.score == 0
    assert result.level == "LOW"
    assert result.reasons == ["Only documentation files changed"]
    assert "No test files changed" not in result.reasons


def test_docs_only_changes_stay_low_with_churn_stats():
    result = calculate_risk(
        ["docs/guide.md", "README.md"],
        DiffStats(files_changed=2, lines_added=900, lines_deleted=100, total_churn=1000),
    )

    assert result.score == 0
    assert result.level == "LOW"
    assert result.reasons == ["Only documentation files changed"]


def test_no_patch_signals_preserves_existing_behavior():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        cmake_signals=[],
        api_signals=[],
    )

    assert result.score == 20
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
    ]


def test_one_non_sensitive_cmake_signal_adds_category_score():
    result = calculate_risk(["tests/test_only.py"], cmake_signals=["CMake minimum version changed"])

    assert result.score == 15
    assert result.level == "LOW"
    assert result.reasons == ["CMake patch signals detected"]


def test_multiple_non_sensitive_cmake_signals_are_not_overcounted():
    result = calculate_risk(
        ["tests/test_only.py"],
        cmake_signals=[
            "CMake minimum version changed",
            "Compiler options changed",
            "Install rules changed",
        ],
    )

    assert result.score == 15
    assert result.reasons == ["CMake patch signals detected"]


def test_one_sensitive_cmake_signal_adds_category_and_sensitive_score():
    result = calculate_risk(["tests/test_only.py"], cmake_signals=["Link dependencies changed"])

    assert result.score == 35
    assert result.level == "LOW"
    assert result.reasons == [
        "CMake patch signals detected",
        "Build/link/package configuration changed",
    ]


def test_multiple_sensitive_cmake_signals_are_not_overcounted():
    result = calculate_risk(
        ["tests/test_only.py"],
        cmake_signals=[
            "Library target changed",
            "Executable target changed",
            "Link dependencies changed",
            "Package dependency changed",
        ],
    )

    assert result.score == 35
    assert result.reasons == [
        "CMake patch signals detected",
        "Build/link/package configuration changed",
    ]


def test_one_api_signal_adds_category_score():
    result = calculate_risk(
        ["tests/test_only.py"],
        api_signals=["API-like header change detected in include/widget.hpp"],
    )

    assert result.score == 15
    assert result.level == "LOW"
    assert result.reasons == ["API-like header changes detected"]


def test_multiple_api_signals_are_not_overcounted():
    result = calculate_risk(
        ["tests/test_only.py"],
        api_signals=[
            "API-like header change detected in include/widget.hpp",
            "API-like header change detected in include/gadget.hpp",
            "API-like header change detected in include/detail.hpp",
        ],
    )

    assert result.score == 15
    assert result.reasons == ["API-like header changes detected"]


def test_cmake_and_api_signals_score_together():
    result = calculate_risk(
        ["tests/test_only.py"],
        cmake_signals=["Link dependencies changed"],
        api_signals=["API-like header change detected in include/widget.hpp"],
    )

    assert result.score == 50
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "CMake patch signals detected",
        "Build/link/package configuration changed",
        "API-like header changes detected",
    ]


def test_score_cap_still_applies_with_patch_signal_scoring():
    result = calculate_risk(
        [
            "cmake/toolchain.cmake",
            "include/widget.h",
            "src/a.cpp",
            "src/b.cpp",
            "src/c.cpp",
            "src/d.cpp",
            "src/e.cpp",
        ],
        cmake_signals=["Link dependencies changed"],
        api_signals=["API-like header change detected in include/widget.h"],
    )

    assert result.score == 100
    assert result.level == "HIGH"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
        "Production code changed",
        "Public API directory changed",
        "Build configuration directory changed",
        "No test files changed",
        "CMake patch signals detected",
        "Build/link/package configuration changed",
        "API-like header changes detected",
    ]


def test_empty_diff_ignores_patch_signals():
    result = calculate_risk(
        [],
        cmake_signals=["Link dependencies changed"],
        api_signals=["API-like header change detected in include/widget.hpp"],
    )

    assert result == RiskResult(score=0, level="LOW", reasons=["No changed files"])


def test_docs_only_changes_stay_low_with_patch_signals():
    result = calculate_risk(
        ["README.md", "docs/guide.md"],
        cmake_signals=["Link dependencies changed"],
        api_signals=["API-like header change detected in include/widget.hpp"],
    )

    assert result.score == 0
    assert result.level == "LOW"
    assert result.reasons == ["Only documentation files changed"]


def test_tests_directory_counts_as_test_file_change():
    result = calculate_risk(["tests/widget.cpp"])

    assert result.score == 5
    assert result.level == "LOW"
    assert result.reasons == ["Source implementation files changed"]


def test_test_prefix_counts_as_test_file_change():
    result = calculate_risk(["src/test_widget.cpp"])

    assert result.score == 15
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
    ]


def test_test_suffixes_count_as_test_file_changes():
    cases = [
        ("src/widget_test.c", 15, "LOW", ["Source implementation files changed", "Production code changed"]),
        ("src/widget_test.cc", 15, "LOW", ["Source implementation files changed", "Production code changed"]),
        ("src/widget_test.cpp", 15, "LOW", ["Source implementation files changed", "Production code changed"]),
        ("src/widget_test.cxx", 15, "LOW", ["Source implementation files changed", "Production code changed"]),
        ("include/widget_test.h", 35, "LOW", ["Header/API files changed", "Public API directory changed"]),
        ("include/widget_test.hpp", 35, "LOW", ["Header/API files changed", "Public API directory changed"]),
        ("include/widget_test.hh", 35, "LOW", ["Header/API files changed", "Public API directory changed"]),
        ("include/widget_test.hxx", 35, "LOW", ["Header/API files changed", "Public API directory changed"]),
        ("tools/widget_test.py", 0, "LOW", ["Only low-risk files changed"]),
    ]

    for path, score, level, reasons in cases:
        result = calculate_risk([path])

        assert result.score == score
        assert result.level == level
        assert result.reasons == reasons
        assert "No test files changed" not in result.reasons


def test_singular_test_directory_does_not_count_as_test_file_change():
    result = calculate_risk(["test/widget.cpp"])

    assert result.score == 30
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "No test files changed",
    ]


def test_score_is_capped_at_100_and_high_risk():
    result = calculate_risk(
        [
            "cmake/toolchain.cmake",
            "include/widget.h",
            "src/a.cpp",
            "src/b.cpp",
            "src/c.cpp",
            "src/d.cpp",
            "src/e.cpp",
        ]
    )

    assert result.score == 100
    assert result.level == "HIGH"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
        "Production code changed",
        "Public API directory changed",
        "Build configuration directory changed",
        "No test files changed",
    ]


def test_total_churn_thresholds_are_tiered():
    cases = [
        (99, 20, ["Source implementation files changed", "Production code changed"]),
        (
            100,
            30,
            [
                "Source implementation files changed",
                "Production code changed",
                "Large diff: 100 changed lines",
            ],
        ),
        (
            300,
            40,
            [
                "Source implementation files changed",
                "Production code changed",
                "Large diff: 300 changed lines",
            ],
        ),
        (
            700,
            50,
            [
                "Source implementation files changed",
                "Production code changed",
                "Large diff: 700 changed lines",
            ],
        ),
    ]

    for total_churn, expected_score, expected_reasons in cases:
        result = calculate_risk(
            ["src/widget.cpp", "tests/test_widget.cpp"],
            DiffStats(files_changed=2, lines_added=total_churn, lines_deleted=0, total_churn=total_churn),
        )

        assert result.score == expected_score
        assert result.reasons == expected_reasons


def test_total_churn_thresholds_are_not_cumulative():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        DiffStats(files_changed=2, lines_added=800, lines_deleted=0, total_churn=800),
    )

    assert result.score == 50
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Large diff: 800 changed lines",
    ]


def test_files_changed_thresholds_are_tiered():
    cases = [
        (9, 0, ["Only low-risk files changed"]),
        (
            10,
            15,
            [
                "Many files changed: 10 files",
            ],
        ),
        (
            25,
            25,
            [
                "Many files changed: 25 files",
            ],
        ),
    ]

    for files_changed, expected_score, expected_reasons in cases:
        result = calculate_risk(
            ["tests/test_only.py"],
            DiffStats(files_changed=files_changed, lines_added=1, lines_deleted=0, total_churn=1),
        )

        assert result.score == expected_score
        assert result.reasons == expected_reasons


def test_files_changed_thresholds_are_not_cumulative():
    result = calculate_risk(
        ["tests/test_only.py"],
        DiffStats(files_changed=30, lines_added=1, lines_deleted=0, total_churn=1),
    )

    assert result.score == 25
    assert result.reasons == ["Many files changed: 30 files"]


def test_score_cap_still_applies_with_churn_scoring():
    result = calculate_risk(
        [
            "cmake/toolchain.cmake",
            "include/widget.h",
            "src/a.cpp",
            "src/b.cpp",
            "src/c.cpp",
            "src/d.cpp",
            "src/e.cpp",
        ],
        DiffStats(files_changed=30, lines_added=800, lines_deleted=0, total_churn=800),
    )

    assert result.score == 100
    assert result.level == "HIGH"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
        "Production code changed",
        "Public API directory changed",
        "Build configuration directory changed",
        "No test files changed",
        "Large diff: 800 changed lines",
        "Many files changed: 30 files",
    ]


def test_build_failure_increases_score():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(exit_code=1),
        ),
    )

    assert result.score == 50
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Build failed",
    ]


def test_test_failure_increases_score():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            test=CommandResultStub(exit_code=1),
        ),
    )

    assert result.score == 45
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Tests failed",
    ]


def test_build_timeout_increases_score():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(timed_out=True),
        ),
    )

    assert result.score == 40
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Build command timed out",
    ]


def test_test_timeout_increases_score():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            test=CommandResultStub(timed_out=True),
        ),
    )

    assert result.score == 40
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Test command timed out",
    ]


def test_timeout_is_not_double_counted_as_failure():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(exit_code=1, timed_out=True),
            test=CommandResultStub(exit_code=1, timed_out=True),
        ),
    )

    assert result.score == 60
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Build command timed out",
        "Test command timed out",
    ]


def test_build_passes_and_test_times_out_adds_timeout_only():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(exit_code=0),
            test=CommandResultStub(timed_out=True),
        ),
    )

    assert result.score == 40
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Test command timed out",
    ]


def test_build_times_out_and_test_skipped_adds_build_timeout_only():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(timed_out=True),
            test=None,
        ),
    )

    assert result.score == 40
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Build command timed out",
    ]


def test_test_skipped_because_build_failed_does_not_add_test_penalty():
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(exit_code=1),
            test=None,
        ),
    )

    assert result.score == 50
    assert result.reasons == [
        "Source implementation files changed",
        "Production code changed",
        "Build failed",
    ]


def test_execution_result_none_leaves_score_unchanged():
    baseline = calculate_risk(["src/widget.cpp", "tests/test_widget.cpp"])
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=None,
    )

    assert result == baseline


def test_no_commands_configured_leaves_score_unchanged():
    baseline = calculate_risk(["src/widget.cpp", "tests/test_widget.cpp"])
    result = calculate_risk(
        ["src/widget.cpp", "tests/test_widget.cpp"],
        execution_result=ExecutionResultStub(build=None, test=None),
    )

    assert result == baseline


def test_score_cap_still_applies_with_execution_scoring():
    result = calculate_risk(
        [
            "cmake/toolchain.cmake",
            "include/widget.h",
            "src/a.cpp",
            "src/b.cpp",
            "src/c.cpp",
            "src/d.cpp",
            "src/e.cpp",
        ],
        execution_result=ExecutionResultStub(
            build=CommandResultStub(exit_code=1),
            test=CommandResultStub(exit_code=1),
        ),
    )

    assert result.score == 100
    assert result.level == "HIGH"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
        "Production code changed",
        "Public API directory changed",
        "Build configuration directory changed",
        "No test files changed",
        "Build failed",
        "Tests failed",
    ]


def test_level_boundaries():
    assert calculate_risk(["tests/test_only.py"]).level == "LOW"
    assert calculate_risk(["src/a.cpp", "tests/test_a.cpp"]).level == "LOW"
    assert (
        calculate_risk(["CMakeLists.txt", "include/a.hpp", "tests/test_a.py"]).level
        == "MEDIUM"
    )
    assert calculate_risk(["CMakeLists.txt", "include/a.hpp", "src/a.cpp"]).level == "HIGH"
