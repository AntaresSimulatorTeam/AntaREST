#!/usr/bin/env python3
import re
import subprocess
from collections import defaultdict

# Adjust if your main branch is named differently
BASE_BRANCH = "origin/master"
TARGET_BRANCH = "origin/dev"
REPO_URL = "https://github.com/AntaresSimulatorTeam/AntaREST"


def run_git(*args):
    """Run a git command and return its output."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def fetch_branches():
    """Fetch the latest changes from origin for master and dev branches."""
    subprocess.run(["git", "fetch", "origin", "master", "dev"], capture_output=True, check=True)


def extract_pr_number(subject, body):
    """Extract PR number from commit subject or body."""
    patterns = [r"Merge pull request #(\d+)", r"\(#(\d+)\)", r"#(\d+)"]
    text = f"{subject}\n{body}"
    for pattern in patterns:
        if match := re.search(pattern, text):
            return match.group(1)
    return None


def get_commits(base_branch, target_branch):
    """Get commits in target_branch that are not in base_branch."""
    log_format = "%H|%s|%an|%b"
    output = run_git("log", f"{base_branch}..{target_branch}", f"--pretty=format:{log_format}")
    return output.splitlines() if output else []


def get_commits_for_release():
    """Generate formatted commit messages with PR links."""
    fetch_branches()
    commits = get_commits(BASE_BRANCH, TARGET_BRANCH)

    if not commits:
        print(f"No commits found in {TARGET_BRANCH} that are not in {BASE_BRANCH}.")
        return

    for line in commits:
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        sha, subject, author, body = parts
        pr = extract_pr_number(subject, body)
        pr_link = f"{REPO_URL}/pull/{pr}" if pr else "(no PR link)"
        yield f"* {subject} by @{author} in {pr_link}"


def parse_changes(release_commits_list):
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
    grouped_changes = defaultdict(list)

    # Regex pattern to match conventional commits with optional breaking change indicator
    pattern = r"\* (\w+)\(([^)]+)\)(!?): (.*?) by @.+ in .+/(\d+)"

    for line in release_commits_list:
        match = re.match(pattern, line.strip())
        if not match:
            continue

        kind, scope, breaking_indicator, message, pr_number = match.groups()
        category = CATEGORY_MAP.get(kind, "Other")
        is_breaking = breaking_indicator == "!"
        grouped_changes[category].append((scope, message, pr_number, is_breaking))

    return grouped_changes


def mk_changelog_str(grouped_changes):
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


def generate_changelog():
    """Generate the complete changelog."""
    release_commits_list = list(get_commits_for_release())

    if not release_commits_list:
        return "No changes to report."

    changes_by_category = parse_changes(release_commits_list)
    return mk_changelog_str(changes_by_category)


if __name__ == "__main__":
    print(generate_changelog())
