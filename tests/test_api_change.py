from pr_risk.api_change import analyze_api_changes


def test_analyze_api_changes_detects_class_declaration():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1 @@
+class Widget;
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/widget.hpp"
    ]


def test_analyze_api_changes_detects_struct_declaration():
    patch = """diff --git a/include/config.h b/include/config.h
--- a/include/config.h
+++ b/include/config.h
@@ -1,0 +1 @@
+struct Config;
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/config.h"
    ]


def test_analyze_api_changes_detects_enum_declaration():
    patch = """diff --git a/include/mode.hh b/include/mode.hh
--- a/include/mode.hh
+++ b/include/mode.hh
@@ -1,0 +1 @@
+enum class Mode;
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/mode.hh"
    ]


def test_analyze_api_changes_detects_normal_function_declaration():
    patch = """diff --git a/include/math.hxx b/include/math.hxx
--- a/include/math.hxx
+++ b/include/math.hxx
@@ -1,0 +1 @@
+int calculate(int value);
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/math.hxx"
    ]


def test_analyze_api_changes_detects_trailing_return_type_function_declaration():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1 @@
+auto make_widget(const Config& config) -> std::unique_ptr<Widget>;
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/widget.hpp"
    ]


def test_analyze_api_changes_ignores_comments():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1,3 @@
+// class Widget
+/* struct Config;
+* enum class Mode;
"""

    assert analyze_api_changes(patch) == []


def test_analyze_api_changes_ignores_preprocessor_lines():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1,5 @@
+#include <vector>
+#pragma once
+#ifndef WIDGET_HPP
+#define WIDGET_HPP
+#endif
"""

    assert analyze_api_changes(patch) == []


def test_analyze_api_changes_ignores_implementation_like_lines_ending_with_brace():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1 @@
+void reset() {
"""

    assert analyze_api_changes(patch) == []


def test_analyze_api_changes_ignores_non_header_files():
    patch = """diff --git a/src/widget.cpp b/src/widget.cpp
--- a/src/widget.cpp
+++ b/src/widget.cpp
@@ -1,0 +1 @@
+class Widget;
"""

    assert analyze_api_changes(patch) == []


def test_analyze_api_changes_empty_patch_returns_empty_list():
    assert analyze_api_changes("") == []


def test_analyze_api_changes_deduplicates_per_file():
    patch = """diff --git a/include/widget.hpp b/include/widget.hpp
--- a/include/widget.hpp
+++ b/include/widget.hpp
@@ -1,0 +1,2 @@
+class Widget;
+void reset();
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/widget.hpp"
    ]


def test_analyze_api_changes_preserves_multiple_header_file_order():
    patch = """diff --git a/include/first.hpp b/include/first.hpp
--- a/include/first.hpp
+++ b/include/first.hpp
@@ -1,0 +1 @@
+class First;
diff --git a/include/second.h b/include/second.h
--- a/include/second.h
+++ b/include/second.h
@@ -1,0 +1 @@
+struct Second;
diff --git a/include/third.hxx b/include/third.hxx
--- a/include/third.hxx
+++ b/include/third.hxx
@@ -1,0 +1 @@
+enum class Third;
"""

    assert analyze_api_changes(patch) == [
        "API-like header change detected in include/first.hpp",
        "API-like header change detected in include/second.h",
        "API-like header change detected in include/third.hxx",
    ]
