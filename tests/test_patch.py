from pr_risk.patch import PatchLine, iter_changed_lines


def test_iter_changed_lines_extracts_added_line():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +2 @@
+class Widget;
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine(
            file_path="include/widget.hpp",
            change_type="added",
            content="class Widget;",
        )
    ]


def test_iter_changed_lines_extracts_removed_line():
    patch = """diff --git a/src/widget.cpp b/src/widget.cpp
--- a/src/widget.cpp
+++ b/src/widget.cpp
@@ -1 +0,0 @@
-int old_value();
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine(
            file_path="src/widget.cpp",
            change_type="removed",
            content="int old_value();",
        )
    ]


def test_iter_changed_lines_tracks_current_file():
    patch = """diff --git a/src/widget.cpp b/src/widget.cpp
--- a/src/widget.cpp
+++ b/src/widget.cpp
@@ -1 +1 @@
-int old_value();
+int new_value();
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine("src/widget.cpp", "removed", "int old_value();"),
        PatchLine("src/widget.cpp", "added", "int new_value();"),
    ]


def test_iter_changed_lines_ignores_patch_metadata_lines():
    patch = """diff --git a/src/widget.cpp b/src/widget.cpp
index 1111111..2222222 100644
new file mode 100644
deleted file mode 100644
--- a/src/widget.cpp
+++ b/src/widget.cpp
@@ -1,0 +1 @@
+int value();
 context line
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine("src/widget.cpp", "added", "int value();")
    ]


def test_iter_changed_lines_handles_multiple_files():
    patch = """diff --git a/src/widget.cpp b/src/widget.cpp
--- a/src/widget.cpp
+++ b/src/widget.cpp
@@ -1 +1 @@
-int old_value();
+int new_value();
diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1 @@
+class Widget;
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine("src/widget.cpp", "removed", "int old_value();"),
        PatchLine("src/widget.cpp", "added", "int new_value();"),
        PatchLine("include/widget.hpp", "added", "class Widget;"),
    ]


def test_iter_changed_lines_empty_patch_yields_no_lines():
    assert list(iter_changed_lines("")) == []


def test_iter_changed_lines_handles_path_with_spaces():
    patch = """diff --git a/src/file with spaces.cpp b/src/file with spaces.cpp
--- a/src/file with spaces.cpp
+++ b/src/file with spaces.cpp
@@ -1,0 +1 @@
+int value();
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine("src/file with spaces.cpp", "added", "int value();")
    ]


def test_iter_changed_lines_deleted_file_keeps_original_path():
    patch = """diff --git a/src/removed.cpp b/src/removed.cpp
deleted file mode 100644
--- a/src/removed.cpp
+++ /dev/null
@@ -1 +0,0 @@
-int removed();
"""

    assert list(iter_changed_lines(patch)) == [
        PatchLine("src/removed.cpp", "removed", "int removed();")
    ]
