#!/usr/bin/env python3
import re
import subprocess
import typing as t
from collections import defaultdict

# Adjust if your main branch is named differently
BASE_BRANCH = "origin/master"
TARGET_BRANCH = "HEAD"
REPO_URL = "https://github.com/AntaresSimulatorTeam/AntaREST"


ChangelogEntry: t.TypeAlias = t.Tuple[str, str, str, bool]  # (scope, message, pr_number, is_breaking)
ChangeLogByCategory: t.TypeAlias = t.Dict[str, list[ChangelogEntry]]


def run_git(*args: str) -> str:
    """Run a git command and return its output."""
    """Run a git command and return its output. Raises a detailed error if the command fails."""
    try:
        result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        cmd_str = "git " + " ".join(args)
        error_msg = (
            f"Git command failed: {cmd_str}\nReturn code: {e.returncode}\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}"
        )
        raise RuntimeError(error_msg) from e


def fetch_branches() -> None:
    """Fetch the latest changes from origin for master and dev branches."""
    subprocess.run(["git", "fetch", "origin", "master", "dev"], capture_output=True, check=True)


def extract_pr_number(subject: str) -> t.Optional[str]:
    """Extract PR number from commit subject"""
    pattern = r"\(#(\d+)\)"  # PR number pattern
    if match := re.search(pattern, subject):
        return match.group(1)
    return None


def get_commits(base_branch: str, target_branch: str) -> list[str]:
    """Get commits in target_branch that are not in base_branch."""
    log_format = "%H|%s|%an"  # Commit hash | Subject | Author name
    output = run_git("log", f"{base_branch}..{target_branch}", f"--pretty=format:{log_format}")
    return output.splitlines() if output else []


def get_commits_for_release() -> t.Iterator[str]:
    """Generate formatted commit messages with PR links."""
    fetch_branches()
    commits = get_commits(BASE_BRANCH, TARGET_BRANCH)

    if not commits:
        print(f"No commits found in {TARGET_BRANCH} that are not in {BASE_BRANCH}.")
        raise ValueError("No commits to generate changelog from.")

    for line in commits:
        parts = line.split("|", 2)
        if len(parts) < 3:
            raise ValueError(f"Unexpected commit format: {line}", commits)
        _, subject, author = parts
        pr = extract_pr_number(subject)
        subject_without_pr = subject.replace(f"(#{pr})", "").strip()
        pr_link = f"{REPO_URL}/pull/{pr}" if pr else "(no PR link)"
        yield f"* {subject_without_pr} by @{author} in {pr_link}"


def parse_changes(release_commits_list: list[str]) -> ChangeLogByCategory:
    """Parse commit messages and group by category (conventional commits format)."""
    CATEGORY_MAP = {
        "feat": "Features",
        "fix": "Bug fixes",
        "refactor": "Refactorings",
        "perf": "Performances",
        "doc": "Documentation",
        "docs": "Documentation",
        "test": "Tests",
        "build": "Build",
        "chore": "Chore",
    }
    grouped_changes: ChangeLogByCategory = defaultdict(list[ChangelogEntry])
    unmatched_commits = []

    # Regex pattern to match conventional commits with optional breaking change indicator.
    # Pattern breakdown:
    #   \* (?P<kind>\w+)           - Commit type (feat, fix, etc.) after '* '
    #   \((?P<scope>[^)]+)\)       - Scope inside parentheses
    #   (?P<breaking>!?)           - Optional '!' for breaking changes
    #   : (?P<message>.*?)         - Commit message (non-greedy, up to ' by @')
    #   by @.+ in .+/(?P<pr_number>\d+) - Author and PR number at the end
    # Note: The message group is non-greedy to avoid over-matching if ' by @' appears in the message.
    pattern = (
        r"\* "
        r"(?P<kind>\w+)"
        r"\((?P<scope>[^)]+)\)"
        r"(?P<breaking>!?): "
        r"(?P<message>.+?)"
        r" by @.+ in .+/"
        r"(?P<pr_number>\d+)"
    )
    for line in release_commits_list:
        match = re.match(pattern, line.strip())
        if not match:
            unmatched_commits.append(line)
            continue
        kind = match.group("kind")
        scope = match.group("scope")
        breaking_indicator = match.group("breaking")
        message = match.group("message")
        pr_number = match.group("pr_number")

        category = CATEGORY_MAP.get(kind, "Other")
        is_breaking = breaking_indicator == "!"
        grouped_changes[category].append((scope, message, pr_number, is_breaking))

    if unmatched_commits:
        error_msg = (
            f"The following {len(unmatched_commits)} commit(s) do not follow the conventional commit format:\n"
            + "\n".join(f"  - {commit}" for commit in unmatched_commits)
        )
        raise ValueError(error_msg)

    return grouped_changes


def mk_changelog_str(grouped_changes: t.Dict[str, list[ChangelogEntry]]) -> str:
    """Generate a formatted changelog string from grouped changes."""
    changelog = []
    # Define the order of categories
    category_order = [
        "Features",
        "Bug fixes",
        "Performances",
        "Refactorings",
        "Documentation",
        "Tests",
        "Build",
        "Chore",
        "Other",
    ]

    for category in category_order:
        if category in grouped_changes:
            changelog.append(f"### {category}\n")
            for scope, message, pr_number, is_breaking in grouped_changes[category]:
                badge = (
                    " ![Breaking change](https://img.shields.io/badge/-Breaking%20Change-red.svg)"
                    if is_breaking
                    else ""
                )
                pr_link = f"{REPO_URL}/pull/{pr_number}"
                changelog.append(f"* **{scope}**: {message} [`#{pr_number}`]({pr_link}){badge}")
            changelog.append("")  # Add blank line between categories

    return "\n".join(changelog)


def generate_changelog() -> str:
    """Generate the complete changelog."""
    release_commits_list = list(get_commits_for_release())

    if not release_commits_list:
        return "No changes to report."

    changes_by_category = parse_changes(release_commits_list)
    if not changes_by_category:
        raise ValueError("No conventional commits found to generate changelog.")
    return mk_changelog_str(changes_by_category)


if __name__ == "__main__":
    print(generate_changelog())
