from pr_risk.risk import RiskResult, calculate_risk


def test_no_changed_files_has_no_tests_risk():
    result = calculate_risk([])

    assert result == RiskResult(
        score=25,
        level="LOW",
        reasons=["No test files changed"],
    )


def test_cmake_header_and_source_files_add_expected_score():
    result = calculate_risk(
        [
            "CMakeLists.txt",
            "include/widget.hpp",
            "src/widget.cpp",
            "tests/test_widget.cpp",
        ]
    )

    assert result.score == 60
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Changed CMake files",
        "Changed header files",
        "Changed source files: 2",
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

    assert result.score == 25
    assert result.level == "LOW"
    assert result.reasons == ["Changed source files: 7"]


def test_no_test_files_changed_adds_25_points():
    result = calculate_risk(["src/widget.cpp"])

    assert result.score == 30
    assert result.level == "LOW"
    assert result.reasons == [
        "Changed source files: 1",
        "No test files changed",
    ]


def test_test_directory_counts_as_test_file_change():
    result = calculate_risk(["test/widget_test.cpp"])

    assert result.score == 5
    assert result.level == "LOW"
    assert result.reasons == ["Changed source files: 1"]


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
        "Changed CMake files",
        "Changed header files",
        "Changed source files: 5",
        "No test files changed",
    ]


def test_level_boundaries():
    assert calculate_risk(["tests/test_only.py"]).level == "NONE"
    assert calculate_risk(["src/a.cpp", "tests/test_a.cpp"]).level == "LOW"
    assert (
        calculate_risk(["CMakeLists.txt", "include/a.hpp", "tests/test_a.py"]).level
        == "MEDIUM"
    )
    assert calculate_risk(["CMakeLists.txt", "include/a.hpp", "src/a.cpp"]).level == "HIGH"
