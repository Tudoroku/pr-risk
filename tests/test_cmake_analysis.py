from pr_risk.cmake_analysis import analyze_cmake_changes


def _patch(file_path: str, changed_lines: list[str]) -> str:
    body = "\n".join(changed_lines)
    return f"""diff --git a/{file_path} b/{file_path}
--- a/{file_path}
+++ b/{file_path}
@@ -1,0 +1,{len(changed_lines)} @@
{body}
"""


def test_analyze_cmake_changes_detects_add_library():
    patch = _patch("CMakeLists.txt", ["+add_library(core src/core.cpp)"])

    assert analyze_cmake_changes(patch) == ["Library target changed"]


def test_analyze_cmake_changes_detects_add_executable():
    patch = _patch("CMakeLists.txt", ["+add_executable(app src/main.cpp)"])

    assert analyze_cmake_changes(patch) == ["Executable target changed"]


def test_analyze_cmake_changes_detects_target_link_libraries():
    patch = _patch("CMakeLists.txt", ["+target_link_libraries(app PRIVATE core)"])

    assert analyze_cmake_changes(patch) == ["Link dependencies changed"]


def test_analyze_cmake_changes_detects_target_include_directories():
    patch = _patch("CMakeLists.txt", ["+target_include_directories(app PRIVATE include)"])

    assert analyze_cmake_changes(patch) == ["Include directories changed"]


def test_analyze_cmake_changes_detects_target_compile_options():
    patch = _patch("CMakeLists.txt", ["+target_compile_options(app PRIVATE -Wall)"])

    assert analyze_cmake_changes(patch) == ["Compile options changed"]


def test_analyze_cmake_changes_detects_target_compile_definitions():
    patch = _patch("CMakeLists.txt", ["+target_compile_definitions(app PRIVATE ENABLED)"])

    assert analyze_cmake_changes(patch) == ["Compile definitions changed"]


def test_analyze_cmake_changes_detects_find_package():
    patch = _patch("cmake/deps.cmake", ["+find_package(Threads REQUIRED)"])

    assert analyze_cmake_changes(patch) == ["Package dependency changed"]


def test_analyze_cmake_changes_ignores_non_cmake_files():
    patch = _patch("src/main.cpp", ["+add_library(core src/core.cpp)"])

    assert analyze_cmake_changes(patch) == []


def test_analyze_cmake_changes_ignores_cmake_comments():
    patch = _patch("CMakeLists.txt", ["+# add_library(core src/core.cpp)"])

    assert analyze_cmake_changes(patch) == []


def test_analyze_cmake_changes_deduplicates_signals_in_stable_order():
    patch = _patch(
        "CMakeLists.txt",
        [
            "+target_link_libraries(app PRIVATE core)",
            "+add_library(core src/core.cpp)",
            "+target_link_libraries(core PRIVATE Threads::Threads)",
        ],
    )

    assert analyze_cmake_changes(patch) == [
        "Link dependencies changed",
        "Library target changed",
    ]


def test_analyze_cmake_changes_empty_patch_returns_no_signals():
    assert analyze_cmake_changes("") == []
