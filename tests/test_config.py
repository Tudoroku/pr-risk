import pytest

from pr_risk.config import ConfigError, ExecutionConfig, load_config


def _write_config(tmp_path, contents):
    config_path = tmp_path / ".pr-risk.toml"
    config_path.write_text(contents, encoding="utf-8")
    return config_path


def test_load_config_defaults_when_no_config_file(tmp_path):
    assert load_config(tmp_path) == ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=300,
    )


def test_load_config_reads_build_command_only(tmp_path):
    _write_config(
        tmp_path,
        '[commands]\nbuild = "cmake --build build"\n',
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command="cmake --build build",
        test_command=None,
        timeout_seconds=300,
    )


def test_load_config_reads_test_command_only(tmp_path):
    _write_config(
        tmp_path,
        '[commands]\ntest = "ctest --test-dir build --output-on-failure"\n',
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command=None,
        test_command="ctest --test-dir build --output-on-failure",
        timeout_seconds=300,
    )


def test_load_config_reads_both_commands(tmp_path):
    _write_config(
        tmp_path,
        "[commands]\n"
        'build = "cmake --build build"\n'
        'test = "ctest --test-dir build --output-on-failure"\n',
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command="cmake --build build",
        test_command="ctest --test-dir build --output-on-failure",
        timeout_seconds=300,
    )


def test_load_config_reads_custom_timeout(tmp_path):
    _write_config(
        tmp_path,
        "[execution]\n"
        "timeout_seconds = 120\n",
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=120,
    )


def test_load_config_allows_missing_commands_section(tmp_path):
    _write_config(
        tmp_path,
        "[execution]\n"
        "timeout_seconds = 60\n",
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=60,
    )


def test_load_config_allows_missing_execution_section(tmp_path):
    _write_config(
        tmp_path,
        "[commands]\n"
        'build = "cmake --build build"\n',
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command="cmake --build build",
        test_command=None,
        timeout_seconds=300,
    )


def test_load_config_raises_config_error_for_invalid_toml(tmp_path):
    _write_config(tmp_path, "[commands\n")

    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_load_config_raises_config_error_for_zero_timeout(tmp_path):
    _write_config(
        tmp_path,
        "[execution]\n"
        "timeout_seconds = 0\n",
    )

    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_load_config_raises_config_error_for_negative_timeout(tmp_path):
    _write_config(
        tmp_path,
        "[execution]\n"
        "timeout_seconds = -1\n",
    )

    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_load_config_treats_blank_command_strings_as_missing(tmp_path):
    _write_config(
        tmp_path,
        "[commands]\n"
        'build = "   "\n'
        'test = ""\n',
    )

    assert load_config(tmp_path) == ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=300,
    )
