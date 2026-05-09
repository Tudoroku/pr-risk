from pr_risk.patch import iter_changed_lines


_CMAKE_SIGNALS = (
    ("add_library", "Library target changed"),
    ("add_executable", "Executable target changed"),
    ("target_link_libraries", "Link dependencies changed"),
    ("target_include_directories", "Include directories changed"),
    ("target_compile_options", "Compile options changed"),
    ("target_compile_definitions", "Compile definitions changed"),
    ("find_package", "Package dependency changed"),
)


def analyze_cmake_changes(patch_text: str) -> list[str]:
    signals: list[str] = []
    seen: set[str] = set()

    for changed_line in iter_changed_lines(patch_text):
        if not _is_cmake_file(changed_line.file_path):
            continue

        content = changed_line.content.lstrip()
        if content.startswith("#"):
            continue

        for command, signal in _CMAKE_SIGNALS:
            if command in content and signal not in seen:
                signals.append(signal)
                seen.add(signal)

    return signals


def _is_cmake_file(file_path: str) -> bool:
    return file_path == "CMakeLists.txt" or file_path.endswith(".cmake")
