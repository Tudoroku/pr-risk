from pr_risk.diff_stats import DiffStats, parse_numstat


def test_parse_numstat_empty_output_returns_zeros():
    assert parse_numstat("") == DiffStats(
        files_changed=0,
        lines_added=0,
        lines_deleted=0,
        total_churn=0,
        binary_files_changed=0,
    )


def test_parse_numstat_one_text_file():
    assert parse_numstat("12\t3\tsrc/widget.cpp\n") == DiffStats(
        files_changed=1,
        lines_added=12,
        lines_deleted=3,
        total_churn=15,
        binary_files_changed=0,
    )


def test_parse_numstat_multiple_text_files():
    assert parse_numstat("12\t3\tsrc/widget.cpp\n4\t8\tinclude/widget.hpp\n") == DiffStats(
        files_changed=2,
        lines_added=16,
        lines_deleted=11,
        total_churn=27,
        binary_files_changed=0,
    )


def test_parse_numstat_binary_file_output():
    assert parse_numstat("-\t-\tassets/logo.png\n") == DiffStats(
        files_changed=1,
        lines_added=0,
        lines_deleted=0,
        total_churn=0,
        binary_files_changed=1,
    )


def test_parse_numstat_file_path_containing_spaces():
    assert parse_numstat("2\t1\tsrc/file with spaces.cpp\n") == DiffStats(
        files_changed=1,
        lines_added=2,
        lines_deleted=1,
        total_churn=3,
        binary_files_changed=0,
    )
