import re

#!/usr/bin/env python3
import subprocess
from collections import defaultdict

# Adjust if your main branch is named differently
BASE_BRANCH = "origin/master"
TARGET_BRANCH = "origin/dev"
REPO_URL = "https://github.com/AntaresSimulatorTeam/AntaREST"


def run_git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def fetch_branches():
    subprocess.run(["git", "fetch", "origin", "master", "dev"], check=True)


def extract_pr_number(subject, body):
    # Match PR numbers in "Merge pull request #1234" or "(#1234)" or "#1234"
    patterns = [r"Merge pull request #(\d+)", r"\(#(\d+)\)", r"#(\d+)"]
    text = f"{subject}\n{body}"
    for pattern in patterns:
        if m := re.search(pattern, text):
            return m.group(1)
    return None


def get_commits(base_branch, target_branch):
    log_format = "%H|%s|%an|%b"
    output = run_git("log", f"{base_branch}..{target_branch}", f"--pretty=format:{log_format}")
    return output.splitlines() if output else []


def get_commit_for_release():
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
        yield (f"* {subject} by @{author} in {pr_link}")


def parse_changes(release_commits_list):
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

    # Parse each line
    for line in release_commits_list:
        match = re.match(r"\* (\w+)\(([^)]+)\)!?: (.*?) by @.+ in .+/(\d+)", line.strip())
        if not match:
            continue
        match_breaking_change = re.match(r"\* (\w+)\(([^)]+)\)!: (.*?) by @.+ in .+/(\d+)", line.strip())
        kind, scope, message, pr_number = match.groups()
        category = CATEGORY_MAP.get(kind, "Other")
        grouped_changes[category].append((scope, message, pr_number, bool(match_breaking_change)))

    return grouped_changes


def mk_changelog_str(grouped_changes):
    changelog = []
    for category in ["Features", "Bug fixes", "Performances", "Refactorings", "Chore", "Other"]:
        if category in grouped_changes:
            changelog += [f"### {category}\n"]
            for scope, message, pr_number, mbr in grouped_changes[category]:
                if mbr:
                    badge = " ![Breaking change](https://img.shields.io/badge/-Breaking%20Change-red.svg)"
                else:
                    badge = ""
                changelog += [
                    f"* **{scope}**: {message} [`{pr_number}`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/{pr_number}){badge}"
                ]
    return "\n".join(changelog)


def generate_changelog():
    release_commits_list = get_commit_for_release()

    changes_by_category = parse_changes(release_commits_list)

    return mk_changelog_str(changes_by_category)


if __name__ == "__main__":
    print(generate_changelog())
