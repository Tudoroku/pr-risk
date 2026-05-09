import subprocess


class GitDiffError(Exception):
    pass


def get_changed_files(repo: str, base: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", repo, "diff", "--name-only", base],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitDiffError("git executable was not found") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "failed to read git diff"
        raise GitDiffError(message) from exc

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_diff_numstat(repo: str, base: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", repo, "diff", "--numstat", base],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitDiffError("git executable was not found") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "failed to read git diff"
        raise GitDiffError(message) from exc

    return result.stdout
