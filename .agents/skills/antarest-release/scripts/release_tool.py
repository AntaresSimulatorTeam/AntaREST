#!/usr/bin/env python3
"""
Local helpers for the Antares Web release runbook.

Nothing here writes to a remote. `preflight`, `status` and `notes` only read. `prepare`, `commit` and `cd-update` change local files and local git
history; they never push.

    release_tool.py preflight X.Y.Z                 # derived values + blocking checks
    release_tool.py status X.Y.Z                    # where the release stands, next step
    release_tool.py prepare X.Y.Z -d YYYY-MM-DD     # branch, version bump, changelog draft, staging
    release_tool.py commit X.Y.Z                    # the release commit, exact message
    release_tool.py notes X.Y.Z                     # changelog section, for the GitHub release
    release_tool.py cd-update X.Y.Z --repo PATH     # version and commit hash in antares-cd
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/AntaresSimulatorTeam/AntaREST"
CHANGELOG = "docs/CHANGELOG.md"
INIT_FILE = "antarest/__init__.py"

# What `scripts/update_version.py` touches: the release commit holds exactly these.
RELEASE_FILES = [
    INIT_FILE,
    CHANGELOG,
    "pyproject.toml",
    "sonar-project.properties",
    "uv.lock",
    "webapp/package.json",
    "webapp/package-lock.json",
]

# Section order and titles follow the most recent releases in docs/CHANGELOG.md.
SECTIONS = ["Features", "Bug fixes", "Performances", "Refactorings", "Miscellaneous"]
TYPE_TO_SECTION = {
    "feat": "Features",
    "fix": "Bug fixes",
    "perf": "Performances",
    "refactor": "Refactorings",
}
DEFAULT_SECTION = "Miscellaneous"  # chore, docs, test, build, ci, style

SUBJECT_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<desc>.+?) \(#(?P<pr>\d+)\)$")
# Appended to entries whose commit subject carries the conventional-commit `!` marker.
BREAKING_BADGE = " ![Breaking change](https://img.shields.io/badge/-Breaking%20Change-red.svg)"
VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
RELEASE_TITLE_RE = re.compile(r"^v\d+(?:\.\d+)+ \(\d{4}-\d{2}-\d{2}\)$")

# antares-cd: the two places that carry the released version.
CD_DEVOPS_DOC = "docs/dt-devops.md"
CD_DESCRIPTION = "application_description.yml"
CD_GITCOMMIT_RE = re.compile(r'^\{"version": "[^"]*", "gitcommit": "[0-9a-f]{40}" ?\}$', re.MULTILINE)
CD_VERSION_RE = re.compile(r"^(?P<key>[ \t]+version: )\d+(?:\.\d+)+[ \t]*$", re.MULTILINE)


def run(*cmd: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(list(cmd), cwd=cwd, env=env, capture_output=True, text=True)


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def git_ok(*args: str, cwd: Path | None = None) -> bool:
    return run("git", *args, cwd=cwd).returncode == 0


def repo_root() -> Path:
    return Path(git("rev-parse", "--show-toplevel"))


def parse_version(text: str) -> tuple[int, int, int]:
    mo = VERSION_RE.fullmatch(text)
    if mo is None:
        sys.exit(f"Invalid version '{text}': expected X.Y.Z")
    return int(mo[1]), int(mo[2]), int(mo[3])


def dotted(version: tuple[int, int, int]) -> str:
    return "{}.{}.{}".format(*version)


def latest_tag() -> str:
    """
    Highest `vX.Y.Z` tag.

    Tags sit on master merge commits, which dev never contains, so
    `git describe` from dev cannot find them: sort by version instead.
    """
    tags = [t for t in git("tag", "--list", "v*", "--sort=-v:refname").splitlines() if VERSION_RE.fullmatch(t)]
    if not tags:
        sys.exit("No vX.Y.Z tag found: run `git fetch origin --tags` first.")
    return tags[0]


def ref_exists(ref: str, cwd: Path | None = None) -> bool:
    return git_ok("rev-parse", "-q", "--verify", f"{ref}^{{commit}}", cwd=cwd)


def find_master_merge(version: str, master: str) -> str:
    """
    Commit of `master` (first-parent history) that brought release `version`, or "".

    Past subjects: "v2.36.0", "v2.35.0 (#3401)", "chore(release): v2.34.0 (#3350)".
    """
    pattern = re.compile(rf"(?:^|\s)v{re.escape(version)}(?:\s|$)")
    for line in git("log", "--first-parent", "-n", "60", "--format=%H %s", master).splitlines():
        sha, _, subject = line.partition(" ")
        if pattern.search(subject):
            return sha
    return ""


def parent_count(sha: str) -> int:
    return len(git("log", "-1", "--format=%P", sha).split())


def find_release_commit(version: str, ref: str) -> str:
    """The `chore(release): vX.Y.Z (date)` commit near the tip of `ref`, or ""."""
    for line in git("log", "--no-merges", "-n", "50", "--format=%H %s", ref).splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith(f"chore(release): v{version}"):
            return sha
    return ""


def metadata_at(ref: str) -> tuple[str, str]:
    """(`__version__`, `__date__`) of antarest/__init__.py, from a git ref or from the working tree if ref is ""."""
    text = git("show", f"{ref}:{INIT_FILE}") if ref else (repo_root() / INIT_FILE).read_text(encoding="utf-8")
    version = re.search(r'^__version__ = "([^"]+)"', text, re.MULTILINE)
    date = re.search(r'^__date__ = "([^"]+)"', text, re.MULTILINE)
    if version is None or date is None:
        sys.exit(f"Cannot read __version__ / __date__ in {INIT_FILE}")
    return version[1], date[1]


# ---------------------------------------------------------------- changelog


def collect(since: str, until: str) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """Returns (entries by section, subjects needing review, subjects skipped as already listed)."""
    known = set(re.findall(r"\[`#(\d+)`\]", (repo_root() / CHANGELOG).read_text(encoding="utf-8")))

    by_section: dict[str, list[str]] = {name: [] for name in SECTIONS}
    review: list[str] = []
    skipped: list[str] = []
    for subject in git("log", "--no-merges", "--reverse", "--format=%s", f"{since}..{until}").splitlines():
        mo = SUBJECT_RE.match(subject)
        if mo is None:
            if not subject.startswith("chore(release)"):
                review.append(subject)
            continue
        if mo["type"] == "chore" and mo["scope"] == "release":
            continue
        if mo["pr"] in known:
            skipped.append(subject)
            continue
        scope = f"**{mo['scope']}**: " if mo["scope"] else ""
        if not mo["scope"]:
            review.append(subject)
        section = TYPE_TO_SECTION.get(mo["type"], DEFAULT_SECTION)
        badge = BREAKING_BADGE if mo["bang"] else ""
        desc = " ".join(mo["desc"].split())
        by_section[section].append(f"* {scope}{desc} [`#{mo['pr']}`]({REPO_URL}/pull/{mo['pr']}){badge}")
    return by_section, review, skipped


def render(by_section: dict[str, list[str]]) -> str:
    return "\n\n".join(f"### {name}\n\n" + "\n".join(lines) for name, lines in by_section.items() if lines)


def report_draft(
    since: str, until: str, by_section: dict[str, list[str]], review: list[str], skipped: list[str]
) -> None:
    out = sys.stderr
    counts = ", ".join(f"{name}: {len(lines)}" for name, lines in by_section.items() if lines)
    print(f"Range {since}..{until} -> {counts or 'no entry'}", file=out)
    if skipped:
        print(f"Skipped {len(skipped)} PR(s) already present in {CHANGELOG}:", file=out)
        for subject in skipped:
            print(f"  - {subject}", file=out)
    breaking = [line for lines in by_section.values() for line in lines if line.endswith(BREAKING_BADGE)]
    if breaking:
        print("BREAKING CHANGES (badge added, tell the user):", file=out)
        for line in breaking:
            print(f"  - {line[: line.index(' [`#')]}", file=out)
    if review:
        print("NEEDS REVIEW (not a `type(scope): desc (#PR)` subject, place by hand):", file=out)
        for subject in review:
            print(f"  - {subject}", file=out)


def release_section(lines: list[str], version: str) -> list[str]:
    """Body lines of the `vX.Y.Z (date)` section of a changelog."""
    prefix = f"v{version} ("
    body: list[str] = []
    inside = False
    for i, line in enumerate(lines):
        is_title = RELEASE_TITLE_RE.match(line) is not None and i + 1 < len(lines) and lines[i + 1].startswith("---")
        if is_title:
            if inside:
                break
            inside = line.startswith(prefix)
            continue
        if inside and not (line.startswith("---") and not body):
            body.append(line)
    return body


def cmd_notes(args: argparse.Namespace) -> int:
    new = parse_version(args.version)
    version = dotted(new)
    if args.ref:
        lines = git("show", f"{args.ref}:{CHANGELOG}").splitlines()
    else:
        lines = (repo_root() / CHANGELOG).read_text(encoding="utf-8").splitlines()

    text = "\n".join(release_section(lines, version)).strip()
    if not text:
        print(f"No changelog content found for v{version} in {CHANGELOG}", file=sys.stderr)
        return 1
    print(text)

    # Same trailer as the notes GitHub generates for the previous releases.
    older = [
        tag
        for tag in git("tag", "--list", "v*", "--sort=-v:refname").splitlines()
        if VERSION_RE.fullmatch(tag) and parse_version(tag) < new
    ]
    if older:
        print(f"\n**Full Changelog**: {REPO_URL}/compare/{older[0]}...v{version}")
    return 0


# ---------------------------------------------------------------- preflight


def missing_release_commits(base: str, master: str) -> list[str]:
    """
    Non-merge commits of master that dev does not contain.

    In a healthy git-flow history, master only holds merge commits on top of
    what dev already contains. Any other commit means a past release reached
    dev by squash or rebase: the next release PR will conflict on every
    version file.
    """
    return git("rev-list", "--no-merges", f"{base}..{master}").splitlines()


def cmd_preflight(args: argparse.Namespace) -> int:
    new = parse_version(args.version)
    version = dotted(new)
    previous = latest_tag()

    print(f"version        : {version}")
    print(f"tag            : v{version}")
    print(f"release branch : release/v{version}")
    print("jenkins version: {:02d}.{:02d}.{:02d}".format(*new))
    print(f"previous tag   : {previous}")
    print(f"cut point      : {git('log', '-1', '--format=%h %s (%ad)', '--date=short', args.base)}")
    print()

    failures = 0

    def check(ok: bool, label: str, hint: str = "") -> None:
        nonlocal failures
        print(f"[{'OK' if ok else 'FAIL'}] {label}")
        if not ok:
            failures += 1
            if hint:
                print(f"       {hint}")

    check(new > parse_version(previous), f"v{version} is greater than {previous}")
    check(not git("tag", "--list", f"v{version}"), f"tag v{version} does not exist yet")

    missing = missing_release_commits(args.base, args.master)
    newest = git("log", "-1", "--format=%h %s", missing[0]) if missing else ""
    check(
        not missing,
        f"every release commit of {args.master} is in {args.base}",
        f"{len(missing)} commit(s) missing, newest: {newest}\n"
        "       -> a past release reached dev by squash or rebase: `prepare` refuses to run.\n"
        "          Stop and ask the user how to repair it.",
    )

    by_section, review, _ = collect(previous, args.base)
    total = sum(len(lines) for lines in by_section.values())
    check(total > 0, f"{total} PR(s) to release in {previous}..{args.base}")
    if review:
        print(f"[WARN] {len(review)} commit subject(s) need manual placement in the changelog")
    if git("status", "--porcelain", "--untracked-files=no"):
        print("[WARN] tracked files have uncommitted changes: `prepare` will refuse to run")

    return 1 if failures else 0


# ---------------------------------------------------------------- status


def cmd_status(args: argparse.Namespace) -> int:
    version = dotted(parse_version(args.version))
    tag, branch = f"v{version}", f"release/v{version}"

    local = ref_exists(f"refs/heads/{branch}")
    remote = ref_exists(f"refs/remotes/origin/{branch}")
    ref = branch if local else f"origin/{branch}" if remote else ""
    release_commit = find_release_commit(version, ref) if ref else ""
    pushed = remote and (not local or git("rev-parse", branch) == git("rev-parse", f"origin/{branch}"))

    merge = find_master_merge(version, args.master)
    true_merge = bool(merge) and parent_count(merge) == 2
    in_dev = true_merge and git_ok("merge-base", "--is-ancestor", f"{merge}^2", args.base)
    tagged = bool(git("tag", "--list", tag))
    tag_on_merge = tagged and bool(merge) and git("rev-list", "-n", "1", tag) == merge

    def line(done: bool, label: str) -> None:
        print(f"[{'x' if done else ' '}] {label}")

    where = "local + origin" if local and remote else "local only" if local else "origin only" if remote else "absent"
    line(bool(ref), f"branch {branch} ({where})")
    line(
        bool(release_commit),
        f"release commit{': ' + git('log', '-1', '--format=%h %s', release_commit) if release_commit else ''}",
    )
    line(bool(pushed), "release branch pushed, origin up to date with local")
    line(true_merge, f"merged into {args.master}{': ' + git('log', '-1', '--format=%h %s', merge) if merge else ''}")
    line(bool(in_dev), f"merged back into {args.base}")
    line(tagged, f"tag {tag} (GitHub release)")
    print()

    if merge and not true_merge:
        print(f"PROBLEM: {merge[:9]} on {args.master} is not a merge commit (squash or rebase).")
        print("Stop and tell the user: the next release will conflict on every version file.")
        return 1
    if tagged and not tag_on_merge:
        print(f"PROBLEM: tag {tag} does not point at the {args.master} merge commit. Stop and tell the user.")
        return 1

    if tagged:
        nxt = "Phase 5 onward (antares-cd, production tag, desktop): ask what is done; see `jenkins_tool.py history`."
    elif true_merge and in_dev:
        nxt = "Phase 4: GitHub release."
    elif true_merge:
        nxt = f"Phase 3: merge the release back into {args.base}."
    elif pushed and release_commit:
        nxt = "Phase 2 (recette) or Phase 3 (PR to master): see `jenkins_tool.py history`, ask whether recette is validated."
    elif release_commit:
        nxt = "Phase 1, last step: push the release branch (covered by the changelog go)."
    elif ref:
        nxt = "Phase 1: changelog review, then `commit`."
    else:
        nxt = "Phase 0: `preflight`, then `prepare`."
    print(f"next: {nxt}")
    return 0


# ---------------------------------------------------------------- prepare / commit


def insert_changelog(version: str, date: str, draft: str) -> bool:
    """Puts `draft` under the empty `vX.Y.Z (date)` title. Returns False if that section already has content."""
    path = repo_root() / CHANGELOG
    text = path.read_text(encoding="utf-8")
    title = f"v{version} ({date})"
    marker = f"{title}\n{'-' * len(title)}\n"
    if text.count(marker) != 1:
        sys.exit(f"Expected exactly one '{title}' title in {CHANGELOG}, found {text.count(marker)}")
    head, rest = text.split(marker)
    following = rest.lstrip("\n").split("\n", 1)[0]
    if RELEASE_TITLE_RE.match(following) is None:
        return False
    path.write_text(f"{head}{marker}\n{draft}\n{rest}", encoding="utf-8")
    return True


def cmd_prepare(args: argparse.Namespace) -> int:
    new = parse_version(args.version)
    version = dotted(new)
    if DATE_RE.fullmatch(args.date) is None:
        sys.exit(f"Invalid date '{args.date}': expected YYYY-MM-DD")
    root = repo_root()
    os.chdir(root)
    branch = f"release/v{version}"
    previous = latest_tag()

    if new <= parse_version(previous):
        sys.exit(f"v{version} is not greater than {previous}")
    if git("tag", "--list", f"v{version}"):
        sys.exit(f"Tag v{version} already exists")
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("Tracked files have uncommitted changes. Stop and ask the user how to handle them.")

    on_branch = git("branch", "--show-current") == branch
    start = "HEAD" if on_branch else args.base
    missing = missing_release_commits(start, args.master)
    if missing:
        sys.exit(
            f"{len(missing)} commit(s) of {args.master} are missing from {start}, newest {missing[0][:9]}: "
            "a past release reached dev by squash or rebase. Nothing was changed. Stop and ask the user."
        )

    if on_branch:
        if find_release_commit(version, "HEAD"):
            sys.exit(f"{branch} already has its release commit: run `status {version}`")
        print(f"already on {branch}")
    else:
        if ref_exists(f"refs/heads/{branch}") or ref_exists(f"refs/remotes/origin/{branch}"):
            sys.exit(f"{branch} already exists: check it out and run `status {version}` instead")
        git("checkout", "-q", "--no-track", "-b", branch, args.base)
        print(f"created {branch} from {args.base} ({git('log', '-1', '--format=%h %s')})")

    bump = run(sys.executable, "-m", "scripts.update_version", f"v{version}", "-d", args.date)
    if bump.returncode != 0:
        sys.exit(f"scripts.update_version failed:\n{bump.stdout}{bump.stderr}")
    print(f"version bumped to {version}, release date {args.date}")

    by_section, review, skipped = collect(previous, "HEAD")
    total = sum(len(lines) for lines in by_section.values())
    if insert_changelog(version, args.date, render(by_section)):
        print(f"changelog draft written to {CHANGELOG}: {total} entries")
    else:
        print(f"[WARN] the v{version} section of {CHANGELOG} already has content: left untouched")

    lock_ok = True
    if shutil.which("uv"):
        lock_ok = run("uv", "lock", "--check").returncode == 0
        print(f"[{'OK' if lock_ok else 'FAIL'}] uv lock --check")
    else:
        print("[WARN] uv not found: `uv lock --check` skipped")

    git("add", "--", *RELEASE_FILES)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    files_ok = staged == set(RELEASE_FILES)
    print(
        f"[{'OK' if files_ok else 'FAIL'}] staged files: {len(staged)} (expected exactly the {len(RELEASE_FILES)} release files)"
    )
    if not files_ok:
        for name in sorted(staged ^ set(RELEASE_FILES)):
            print(f"       {'unexpected' if name in staged else 'not modified'}: {name}")

    print()
    report_draft(previous, "HEAD", by_section, review, skipped)
    print(f"\nnext: changelog review with the user (checkpoint), then `commit {version}`.")
    return 0 if lock_ok and files_ok else 1


def cmd_commit(args: argparse.Namespace) -> int:
    version = dotted(parse_version(args.version))
    os.chdir(repo_root())
    branch = f"release/v{version}"
    if git("branch", "--show-current") != branch:
        sys.exit(f"Not on {branch}")
    if find_release_commit(version, "HEAD"):
        sys.exit(f"{branch} already has its release commit")

    file_version, date = metadata_at("")
    if file_version != version:
        sys.exit(f"{INIT_FILE} says {file_version}, not {version}: run `prepare` first")
    changelog = (Path(CHANGELOG)).read_text(encoding="utf-8").splitlines()
    if f"v{version} ({date})" not in changelog:
        sys.exit(f"No 'v{version} ({date})' title in {CHANGELOG}: the date differs from {INIT_FILE}")
    entries = [line for line in release_section(changelog, version) if line.startswith("* ")]
    if not entries:
        sys.exit(f"The v{version} section of {CHANGELOG} is empty")

    # Picks up the changelog edits made during the review; nothing else is staged.
    git("add", "--", *RELEASE_FILES)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    extra = sorted(staged - set(RELEASE_FILES))
    if extra:
        sys.exit("Other files are staged, the release commit must not carry them:\n  " + "\n  ".join(extra))
    absent = sorted(set(RELEASE_FILES) - staged)
    if absent:
        sys.exit("Release files without change, the version bump is incomplete:\n  " + "\n  ".join(absent))

    message = f"chore(release): v{version} ({date})"
    done = run("git", "commit", "-q", "-m", message)
    if done.returncode != 0:
        sys.exit(f"git commit failed:\n{done.stdout}{done.stderr}")
    body = git("log", "-1", "--format=%b").strip()
    print(git("log", "-1", "--format=%h %s"))
    print(git("show", "--stat", "--format=", "HEAD"))
    print(f"changelog entries: {len(entries)}")
    if body:
        print("[WARN] a hook added a commit body or trailer; the release commit must have none:")
        print(body)
        return 1
    print(f"\nnext: `git push -u origin {branch}` (covered by the changelog go).")
    return 0


# ---------------------------------------------------------------- antares-cd


def cmd_cd_update(args: argparse.Namespace) -> int:
    version = dotted(parse_version(args.version))
    cd = Path(args.repo).expanduser().resolve()

    merge = find_master_merge(version, args.master)
    if not merge:
        sys.exit(f"No v{version} merge commit on {args.master}: fetch, or the release is not merged yet")
    sha = git("rev-parse", f"{merge}^{{commit}}")
    if parent_count(sha) != 2:
        sys.exit(f"{sha[:9]} is not a merge commit: antares-cd must reference the master merge of the release")
    released, date = metadata_at(sha)
    if released != version:
        sys.exit(f"{sha[:9]} carries version {released}, not {version}")

    if not (cd / ".git").exists():
        sys.exit(f"{cd} is not a git clone")
    if "antares-cd" not in git("remote", "get-url", "origin", cwd=cd):
        sys.exit(f"{cd} is not a clone of antares-cd")
    if git("status", "--porcelain", "--untracked-files=no", cwd=cd):
        sys.exit(f"{cd} has uncommitted changes. Stop and ask the user.")
    current = git("branch", "--show-current", cwd=cd)
    if current != "master":
        sys.exit(f"{cd} is on '{current}'. Ask the user, then: git -C {cd} checkout master && git -C {cd} pull")
    fetched = run("git", "fetch", "-q", "origin", "master", cwd=cd, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if fetched.returncode != 0:
        print("[WARN] could not fetch antares-cd: cannot tell whether master is up to date")
    elif not git_ok("merge-base", "--is-ancestor", "origin/master", "HEAD", cwd=cd):
        # Being ahead is fine (a release commit waiting for its push); being behind is not.
        sys.exit(f"{cd} master is behind origin/master: git -C {cd} pull")

    edits = [
        (CD_DEVOPS_DOC, CD_GITCOMMIT_RE, f'{{"version": "{version}", "gitcommit": "{sha}" }}'),
        (CD_DESCRIPTION, CD_VERSION_RE, rf"\g<key>{version}"),
    ]
    for name, pattern, replacement in edits:
        path = cd / name
        text = path.read_text(encoding="utf-8")
        found = len(pattern.findall(text))
        if found != 1:
            sys.exit(f"{name}: expected exactly one line to update, found {found}. Nothing committed; ask the user.")
        path.write_text(pattern.sub(replacement, text), encoding="utf-8")

    git("add", "--", CD_DEVOPS_DOC, CD_DESCRIPTION, cwd=cd)
    diff = git("diff", "--cached", "-U0", cwd=cd)
    if not diff:
        print(f"antares-cd already references v{version} at {sha}: nothing to do")
        return 0
    print(diff)
    message = f"build: release v{version} ({date})"
    done = run("git", "commit", "-q", "-m", message, cwd=cd)
    if done.returncode != 0:
        sys.exit(f"git commit failed in {cd}:\n{done.stdout}{done.stderr}")
    print(f"\ncommitted in {cd}: {git('log', '-1', '--format=%h %s', cwd=cd)}")
    print(f"next: checkpoint, then `git -C {cd} push origin master` (direct push to master, no review).")
    return 0


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def with_refs(p: argparse.ArgumentParser) -> None:
        p.add_argument("--base", default="origin/dev", help="ref the release branch starts from")
        p.add_argument("--master", default="origin/master", help="production ref")

    p_pre = sub.add_parser("preflight", help="print derived values and run blocking checks")
    p_pre.add_argument("version", help="version to release, X.Y.Z")
    with_refs(p_pre)
    p_pre.set_defaults(func=cmd_preflight)

    p_status = sub.add_parser("status", help="show how far the release went and the next step")
    p_status.add_argument("version", help="version being released, X.Y.Z")
    with_refs(p_status)
    p_status.set_defaults(func=cmd_status)

    p_prep = sub.add_parser("prepare", help="create the branch, bump the version, draft the changelog, stage")
    p_prep.add_argument("version", help="version to release, X.Y.Z")
    p_prep.add_argument("-d", "--date", required=True, help="planned production date, YYYY-MM-DD")
    with_refs(p_prep)
    p_prep.set_defaults(func=cmd_prepare)

    p_commit = sub.add_parser("commit", help="create the release commit with its exact message")
    p_commit.add_argument("version", help="version being released, X.Y.Z")
    p_commit.set_defaults(func=cmd_commit)

    p_notes = sub.add_parser("notes", help="print the changelog section of a version")
    p_notes.add_argument("version", help="released version, X.Y.Z")
    p_notes.add_argument("--ref", help=f"read {CHANGELOG} from this git ref instead of the working tree")
    p_notes.set_defaults(func=cmd_notes)

    p_cd = sub.add_parser("cd-update", help="set the released version and commit hash in an antares-cd clone")
    p_cd.add_argument("version", help="released version, X.Y.Z")
    p_cd.add_argument("--repo", required=True, help="path of the antares-cd clone")
    p_cd.add_argument("--master", default="origin/master", help="production ref of AntaREST")
    p_cd.set_defaults(func=cmd_cd_update)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except subprocess.CalledProcessError as exc:
        print(f"command failed: {' '.join(exc.cmd)}\n{(exc.stderr or '').strip()}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
