from pr_risk.risk import RiskResult, calculate_risk


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

    assert result.score == 60
    assert result.level == "MEDIUM"
    assert result.reasons == [
        "Build system files changed",
        "Header/API files changed",
        "Source implementation files changed",
    ]


def test_build_system_files_add_expected_reason():
    result = calculate_risk(["src/CMakeLists.txt", "cmake/toolchain.cmake", "tests/build.py"])

    assert result.score == 25
    assert result.level == "LOW"
    assert result.reasons == ["Build system files changed"]


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

    assert result.score == 25
    assert result.level == "LOW"
    assert result.reasons == ["Header/API files changed"]


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

    assert result.score == 20
    assert result.level == "LOW"
    assert result.reasons == ["Source implementation files changed"]


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
    assert result.reasons == ["Source implementation files changed"]


def test_no_test_files_changed_adds_25_points():
    result = calculate_risk(["src/widget.cpp"])

    assert result.score == 30
    assert result.level == "LOW"
    assert result.reasons == [
        "Source implementation files changed",
        "No test files changed",
    ]


def test_tests_directory_counts_as_test_file_change():
    result = calculate_risk(["tests/widget.cpp"])

    assert result.score == 5
    assert result.level == "LOW"
    assert result.reasons == ["Source implementation files changed"]


def test_test_prefix_counts_as_test_file_change():
    result = calculate_risk(["src/test_widget.cpp"])

    assert result.score == 5
    assert result.level == "LOW"
    assert result.reasons == ["Source implementation files changed"]


def test_cpp_and_python_test_suffixes_count_as_test_file_changes():
    cpp_result = calculate_risk(["src/widget_test.cpp"])
    python_result = calculate_risk(["tools/widget_test.py"])

    assert cpp_result.score == 5
    assert cpp_result.level == "LOW"
    assert cpp_result.reasons == ["Source implementation files changed"]
    assert python_result.score == 0
    assert python_result.level == "NONE"
    assert python_result.reasons == []


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
