# GitHub Actions

`pr-risk` can produce PR-friendly reports from a GitHub Actions workflow. It is
a CLI tool, not a GitHub App, and does not post PR comments automatically.
Reports can appear on the workflow run page or be downloaded as artifacts.

## Basic PR workflow

Save this as `.github/workflows/pr-risk.yml` in the repository being analyzed:

```yaml
name: pr-risk
on:
  pull_request:

permissions:
  contents: read

jobs:
  pr-risk:
    runs-on: ubuntu-latest
    defaults:
      run:
        shell: bash
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install pr-risk
        run: >-
          python -m pip install
          "git+https://github.com/Tudoroku/pr-risk.git@v0.7.0"
      - name: Write Markdown summary
        shell: bash
        run: >-
          pr-risk analyze --repo . --base "origin/${{ github.base_ref }}"
          --format markdown | tee -a "$GITHUB_STEP_SUMMARY"
```

The package is not published on PyPI. The pinned installation requires the
`v0.7.0` tag, which will be published at the end of the release milestone.
Until then, this installation example cannot be used as written.

For integration into other C++/CMake repositories, install from the pinned
Git tag above. `python -m pip install -e .` is appropriate only when the
checked-out repository is `pr-risk` itself.

`fetch-depth: 0` fetches the history and branch refs needed for the comparison.
`github.base_ref` selects the PR's target branch instead of assuming its name.
Checkout uses GitHub's PR merge ref by default; the analysis compares that
checkout against the target branch. `pr-risk` uses `git diff BASE`, including
any tracked working-tree changes made before analysis.

`--format markdown` writes the report to stdout. `tee` both shows it in the job
log and appends it to `GITHUB_STEP_SUMMARY`, which GitHub renders on the run
summary page. Writing a summary requires no API call or additional token.
Explicit `shell: bash` enables `pipefail`, preserving analysis failures through
the pipeline to `tee`.

## CI thresholds and exit codes

To fail on HIGH risk, add this step after installation:

```yaml
- name: Enforce risk threshold
  run: >-
    pr-risk analyze --repo . --base "origin/${{ github.base_ref }}"
    --ci --fail-on high
```

`--ci` controls the exit status; it does not change the report format or run
build/test commands. The default format remains text. Add `--format markdown`
or `--format json` when needed. The report is emitted before the threshold
determines the exit status.

| Option | Fails for |
| --- | --- |
| `--fail-on never` | No risk level; analysis/configuration errors can still fail |
| `--fail-on medium` | MEDIUM and HIGH |
| `--fail-on high` | HIGH |

Without `--fail-on`, `--ci` reads `[ci].fail_on` from `.pr-risk.toml`, defaulting
to `never` when absent. An explicit `--fail-on` overrides that setting. Set the
threshold explicitly in the workflow to keep it independent of PR config.
`--fail-on` without `--ci` is rejected.

| Exit code | Meaning |
| --- | --- |
| `0` | Analysis succeeded and the selected threshold did not fail |
| `1` | Risk met or exceeded the threshold, or a handled Git/runner validation error occurred |
| `2` | Argument parsing/validation failed, including `--fail-on` without `--ci` |

Failed or timed-out configured build/test commands are execution evidence
used in risk scoring, not necessarily fatal CLI errors. With `--ci`, they
fail the CLI only when the final risk level reaches the selected threshold.
For example, a missing Docker executable is recorded as a failed command;
it does not automatically make `--ci --fail-on high` return `1`. Without
`--ci`, completed analysis returns `0` regardless of risk level or failed
configured checks.

Analysis/configuration failures follow separate error paths. Handled Git
errors and runner validation errors return `1` and write an error to stderr.
Invalid configuration currently raises an uncaught exception with a traceback
on stderr rather than a structured CLI error; other uncaught tool failures
may also behave separately. Inspect the report and stderr to distinguish
analysis failures from a risk threshold failure. Successful stdout contains
only the requested report; captured build/test stdout and stderr are neither
printed nor serialized into reports.

## Keep JSON artifacts when the threshold fails

Replace the summary step with the following steps, or add them after it.
Generate the JSON report before enforcing the threshold:

```yaml
- name: Write JSON report
  run: >-
    pr-risk analyze --repo . --base "origin/${{ github.base_ref }}"
    --format json > pr-risk.json
- name: Enforce risk threshold
  run: >-
    pr-risk analyze --repo . --base "origin/${{ github.base_ref }}"
    --ci --fail-on high
- name: Upload JSON report
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: pr-risk
    path: pr-risk.json
    if-no-files-found: warn
```

`if: always()` lets the upload run even when the earlier threshold step fails.
Without it, the existing report would not be uploaded when it matters most.
An artifact cannot provide a valid report if analysis itself failed before
producing one.

## Docker checks on trusted branches or internal PRs

Security warning: `.pr-risk.toml` is read from the PR's own checkout, so a PR
can define arbitrary build/test commands. Do not use `--run-checks` on
untrusted PRs, including forks. Never combine `--run-checks` with
`pull_request_target`. Use it only on trusted branches or internal PRs whose
authors and repository configuration you trust. Docker execution does not
make untrusted commands safe: the repository is mounted writable, and Docker
is not a complete security sandbox.

For a workflow restricted to trusted PRs, replace the summary step with:

```yaml
- name: Run trusted checks and write summary
  shell: bash
  run: |
    pr-risk analyze --repo . --base "origin/${{ github.base_ref }}" \
      --run-checks --executor docker --format markdown \
      --ci --fail-on high | tee -a "$GITHUB_STEP_SUMMARY"
```

This step has no trust filter of its own. Restrict the workflow to trusted
contributors before adding it; being an internal PR alone is not a security
guarantee.

GitHub-hosted `ubuntu-latest` runners provide Docker. Set `docker.image` in
`.pr-risk.toml`; the image must contain `sh`, CMake, the compiler, and every
other tool your configured build/test commands need. For example:

```toml
[commands]
build = "cmake -S . -B build && cmake --build build"
test = "ctest --test-dir build --output-on-failure"

[execution]
timeout_seconds = 300
executor = "docker"

[docker]
image = "my-cpp-cmake-image:latest"
workdir = "/workspace"
```

Replace the image name with your available build image. `pr-risk` does not
build images automatically. CLI `--executor docker` overrides the executor,
but does not supply or replace the image configuration. Failed or timed-out
checks contribute to the existing execution-aware risk score; `--ci` applies
the risk threshold to that final score.

## References

- [Checkout history and PR checkout behavior](https://github.com/actions/checkout)
- [GitHub job summaries](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary)
- [Workflow shell and failure behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub-hosted Ubuntu tools](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md)
