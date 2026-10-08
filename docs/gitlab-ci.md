# GitLab CI

`pr-risk` produces deterministic reports in GitLab merge request pipelines.
It is a CLI tool, not a GitLab App. It does not post MR comments automatically.

## Basic merge request job

Add this job to `.gitlab-ci.yml` in the C++/CMake repository being analyzed:

```yaml
pr-risk:
  image: python:3.13
  variables:
    GIT_DEPTH: "0"
  before_script:
    - git --version
    - >-
      git fetch origin
      "+refs/heads/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME:refs/remotes/origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
    - >-
      python -m pip install
      "git+https://github.com/Tudoroku/pr-risk.git@v0.7.0"
  script:
    - >-
      pr-risk analyze --repo .
      --base "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
      --format markdown > pr-risk.md
  artifacts:
    when: always
    paths:
      - pr-risk.md
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

Python 3.13 satisfies the package's Python requirement of 3.11 or newer.
Use a Linux runner that supports job images, such as a Docker executor runner.
Git must be installed in the job image for both analysis and the Git-based
package installation. The full `python:3.13` image is used here; do not assume
a slim or custom image has Git. The first command checks that prerequisite.
For a custom image, install Git and CA certificates when preparing the image.

The package is not published on PyPI. The pinned Git installation is intended
for use after the `v0.7.0` release tag is published; it is unavailable until
then. `python -m pip install -e .` applies only when the checked-out repository
is `pr-risk` itself, not when analyzing another repository.

`rules` selects merge request pipelines. `GIT_DEPTH: "0"` requests full Git
history. The explicit fetch refspec creates or updates the remote-tracking
target branch even if the runner originally fetched only the MR ref.

`--base origin/main` means compare the checkout against the locally available
remote-tracking `main` branch; it does not fetch that branch. It is appropriate
only when `main` is the actual target. The job instead uses
`origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME`, so MRs targeting `develop` or a
release branch compare against that branch automatically.

These examples assume `origin` points to the MR's target project, as in a
same-project MR. In a fork pipeline, `origin` may point to the fork. Fetch
from the actual target project's Git URL instead of `origin`, keeping the
same explicit destination refspec. Private target projects also require
authorized read access; do not expose parent-project credentials to
untrusted forks.

Ordinary MR pipelines check out the source branch, rather than a merged
result. `pr-risk` uses `git diff BASE`, including tracked working-tree changes,
so run analysis before build steps that modify tracked files if those changes
should not enter the report.

The Markdown report is saved as `pr-risk.md` for download. GitLab has no
equivalent of GitHub's `GITHUB_STEP_SUMMARY` for these reports: use artifacts
or job logs. To print Markdown directly in the log, remove `> pr-risk.md`;
that does not create the file for the artifact. Direct redirection preserves
the CLI exit status without a pipeline through `tee`.

## JSON artifacts and CI thresholds

Use this complete alternative job to keep JSON evidence when HIGH risk fails
the job. Use one of these jobs, rather than defining `pr-risk` twice:

```yaml
pr-risk:
  image: python:3.13
  variables:
    GIT_DEPTH: "0"
  before_script:
    - git --version
    - >-
      git fetch origin
      "+refs/heads/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME:refs/remotes/origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
    - >-
      python -m pip install
      "git+https://github.com/Tudoroku/pr-risk.git@v0.7.0"
  script:
    - >-
      pr-risk analyze --repo .
      --base "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
      --format json > pr-risk.json
    - >-
      pr-risk analyze --repo .
      --base "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
      --ci --fail-on high
  artifacts:
    when: always
    paths:
      - pr-risk.json
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

JSON generation happens before threshold enforcement. The final command's
nonzero exit status fails the job; do not add `|| true` or `allow_failure: true`
if this job should gate CI. `artifacts: when: always` uploads an existing
report after a threshold failure, although GitLab excludes jobs that time out
from this guarantee. An artifact cannot contain a valid report if analysis
failed before producing one; redirection alone can leave an empty file.

`--ci` applies a failure threshold to the final risk level. It keeps the
selected output format (text by default) and does not run build/test commands.
Those require `--run-checks`. Threshold priority is:

1. Explicit CLI `--fail-on`.
2. `[ci].fail_on` in `.pr-risk.toml` when no CLI threshold is supplied.
3. `never` when neither is specified.

Set the threshold explicitly in CI so MR-controlled config cannot choose it.
`--fail-on` requires `--ci`; using it alone is an argument validation error.

| Threshold | Risk levels that fail CI |
| --- | --- |
| `never` | None; analysis/configuration errors can still fail |
| `medium` | MEDIUM and HIGH |
| `high` | HIGH |

| Exit code | Meaning |
| --- | --- |
| `0` | Completed analysis without a threshold failure |
| `1` | Risk reached the threshold, or a handled Git/runner validation error occurred |
| `2` | Argument parsing/validation failed |

Tool/configuration failures follow separate error paths. Handled Git and
runner validation errors write to stderr; invalid configuration currently
raises an uncaught exception with a traceback on stderr. Other uncaught
failures may also behave separately. Inspect the report and stderr to
distinguish analysis errors from a risk threshold failure.

Failed or timed-out configured build/test commands are execution evidence
used in scoring, not necessarily fatal CLI errors. For example, a missing
Docker executable is recorded as a failed command. A failed check does not
automatically return `1` with `--ci --fail-on high`: the final score must reach
HIGH. Without `--ci`, completed analysis returns `0` even if checks failed.

## Docker execution: advanced runner setup

`--run-checks --executor docker` runs configured commands through Docker.
Using `image: python:3.13` does not by itself provide the Docker CLI or access
to a Docker daemon. Before enabling this mode, arrange all of the following:

- A job environment with Python, Git, and the Docker CLI.
- Access to a working Docker daemon, for example Docker-in-Docker on an
  appropriately configured privileged runner, or a runner with the Docker
  socket mounted. Follow GitLab's runner, connection, and TLS setup guidance.
- A checkout path available to the daemon at the same absolute path used by
  the job. `pr-risk` bind-mounts the repository; socket binding and a separate
  Docker-in-Docker service need compatible workspace mounts. A successful
  `docker info` alone does not prove the checkout is accessible.
- `docker.image` configured in `.pr-risk.toml`. That image must contain `sh`,
  CMake, the compiler, and every tool the build/test commands require.

Once this environment is configured and the MR is trusted, the following
`script` can replace the basic job's `script`. It retains the existing
Markdown artifact and makes the analysis command's status the job status:

```yaml
script:
  - >-
    pr-risk analyze --repo .
    --base "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
    --run-checks --executor docker --format markdown
    --ci --fail-on high > pr-risk.md
```

This is a job fragment, not a complete Docker runner configuration or a trust
filter. For `--executor local`, commands run in the job environment itself,
which must contain CMake and the other build/test tools.

## Security and limitations

Security warning: `.pr-risk.toml` comes from the MR's own checkout, so the MR
can define arbitrary build/test commands. Strongly avoid `--run-checks` on
untrusted MRs, including forks; use it only for trusted branches or internal
MRs whose authors and configuration you trust. Internal origin alone is not
a trust guarantee.

Docker does not make untrusted code safe. The repository mount is writable;
privileged runners and Docker socket access can expose the runner host.
Review MR-controlled CI configuration before running a fork pipeline in the
parent project, where it can use parent-project resources. Restrict runner
and secret access according to your project's trust policy.

Current limitations:

- No GitLab App or automatic MR comments.
- No OAuth, webhooks, or hosted service.
- No automatic Docker image building.
- No serialization of captured build/test stdout or stderr in reports.
- No LLM features.

## Official references

- [Merge request pipelines and fork security](https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/)
- [MR target branch variables](https://docs.gitlab.com/ci/variables/predefined_variables/)
- [Runner Git history configuration](https://docs.gitlab.com/ci/runners/configure_runners/#shallow-cloning)
- [CI YAML and artifact failure handling](https://docs.gitlab.com/ci/yaml/#artifactswhen)
- [Docker runner setup and bind-mount caveats](https://docs.gitlab.com/ci/docker/using_docker_build/)
- [GitLab CI Lint](https://docs.gitlab.com/ci/yaml/lint/)
