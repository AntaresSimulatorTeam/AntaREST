"""
End-to-end test of `release_tool.py`: a whole release, from preflight to antares-cd, in a sandbox.

The sandbox only knows local bare repositories, so nothing here can reach GitHub, GitLab or Jenkins.
It is built from this clone (read, never written to) and releases the next minor version, today.
Jenkins, the GitHub release and the desktop build are external writes: they are not covered.

    uv run pytest .agents/skills/antarest-release/tests/test_release_tool.py     # run after any change to the tools
    python3 .agents/skills/antarest-release/tests/test_release_tool.py <dir>     # only build a sandbox, to run an agent in it
"""

import datetime
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[2]
TOOL = SKILL / "scripts" / "release_tool.py"

# What a release reads or edits: the sandbox checks out nothing else.
SPARSE_PATHS = [
    "/scripts/",
    "/docs/CHANGELOG.md",
    "/pyproject.toml",
    "/sonar-project.properties",
    "/uv.lock",
    "/antarest/__init__.py",
    "/webapp/package.json",
    "/webapp/package-lock.json",
    "/README.md",
]

ENV = {
    **os.environ,
    "GIT_LFS_SKIP_SMUDGE": "1",
    "GIT_AUTHOR_NAME": "release-test",
    "GIT_AUTHOR_EMAIL": "release-test@example.invalid",
    "GIT_COMMITTER_NAME": "release-test",
    "GIT_COMMITTER_EMAIL": "release-test@example.invalid",
}


def run(*cmd: str | Path, cwd: Path, check: bool = True) -> str:
    """Runs a command and returns what it printed (stdout and stderr together)."""
    done = subprocess.run(
        [str(c) for c in cmd], cwd=cwd, env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if check and done.returncode != 0:
        raise AssertionError(f"{' '.join(str(c) for c in cmd)} failed ({done.returncode}):\n{done.stdout}")
    return done.stdout


def git(*args: str | Path, cwd: Path) -> str:
    return run("git", *args, cwd=cwd).strip()


@dataclass
class Sandbox:
    work: Path  # AntaREST clone whose origin is a local bare repository
    antares_cd: Path  # stand-in for antares-cd, with the two files a release edits
    version: str  # next minor after the highest tag
    date: str  # today

    def tool(self, *args: str | Path, check: bool = True) -> str:
        return run(sys.executable, TOOL, *args, cwd=self.work, check=check)

    def status(self) -> str:
        git("fetch", "-q", "origin", "--tags", cwd=self.work)
        return self.tool("status", self.version)


def build_sandbox(box: Path) -> Sandbox:
    """Mirrors the real `origin/dev` and `origin/master` into local bare repositories under `box`."""
    box.mkdir(parents=True, exist_ok=True)
    latest_tag = git("tag", "--list", "v*", "--sort=-v:refname", cwd=REPO).splitlines()[0]
    major, minor, _ = latest_tag.removeprefix("v").split(".")
    version = f"{major}.{int(minor) + 1}.0"

    origin = box / "origin.git"
    git("clone", "-q", "--bare", "--shared", REPO, origin, cwd=box)
    for branch in ("dev", "master"):
        git("update-ref", f"refs/heads/{branch}", git("rev-parse", f"origin/{branch}", cwd=REPO), cwd=origin)
    git("symbolic-ref", "HEAD", "refs/heads/dev", cwd=origin)

    work = box / "work"
    git("clone", "-q", "--shared", "--no-checkout", origin, work, cwd=box)
    git("sparse-checkout", "init", "--no-cone", cwd=work)
    git("sparse-checkout", "set", *SPARSE_PATHS, cwd=work)
    git("checkout", "-q", "dev", cwd=work)

    cd_origin = box / "antares-cd.git"
    antares_cd = box / "antares-cd"
    git("init", "-q", "--bare", cd_origin, cwd=box)
    git("clone", "-q", cd_origin, antares_cd, cwd=box)
    git("checkout", "-q", "-b", "master", cwd=antares_cd)
    (antares_cd / "docs").mkdir()
    (antares_cd / "docs" / "dt-devops.md").write_text(
        f'Une page doit afficher :\n```json\n{{"version": "0.0.0", "gitcommit": "{"0" * 40}" }}\n```\n'
    )
    (antares_cd / "application_description.yml").write_text("application:\n  name: antares\n  version: 0.0.0\n")
    git("add", ".", cwd=antares_cd)
    git("commit", "-q", "-m", "init", cwd=antares_cd)
    git("push", "-q", "-u", "origin", "master", cwd=antares_cd)

    return Sandbox(work=work, antares_cd=antares_cd, version=version, date=datetime.date.today().isoformat())


def test_release_from_preflight_to_antares_cd(tmp_path: Path) -> None:
    box = build_sandbox(tmp_path)
    v, date, work = box.version, box.date, box.work
    branch = f"release/v{v}"

    # Phase 0: the history left by the previous releases must allow a new one.
    preflight = box.tool("preflight", v, check=False)
    assert "[OK] every release commit of origin/master is in origin/dev" in preflight

    # Phase 1: branch, version bump, changelog draft, release commit, push.
    box.tool("prepare", v, "-d", date)
    assert git("rev-parse", "--abbrev-ref", "HEAD", cwd=work) == branch
    box.tool("commit", v)
    assert git("log", "-1", "--format=%s%n%b", cwd=work) == f"chore(release): v{v} ({date})"
    assert git("status", "--short", cwd=work) == ""
    git("push", "-q", "-u", "origin", branch, cwd=work)
    assert "[x] release branch pushed" in box.status()

    # Phase 3: the reviewer merges the PR into master with a merge commit named after the version.
    git("checkout", "-q", "-b", "master", "origin/master", cwd=work)
    git("merge", "-q", "--no-ff", branch, "-m", f"v{v}", cwd=work)
    git("push", "-q", "origin", "master", cwd=work)
    assert "[x] merged into origin/master" in box.status()

    # Phase 3: back-merge into dev, local route of the runbook.
    git("checkout", "-q", "dev", cwd=work)
    git("pull", "-q", cwd=work)
    git(
        "merge",
        "-q",
        "--no-ff",
        f"origin/{branch}",
        "-m",
        f"Merge remote-tracking branch 'origin/{branch}' into dev",
        cwd=work,
    )
    git("push", "-q", "origin", "dev", cwd=work)
    assert "[x] merged back into origin/dev" in box.status()

    # Phase 4: release notes, then the tag that publishing the GitHub release would create.
    master = git("rev-parse", "origin/master", cwd=work)
    notes = box.tool("notes", v, "--ref", "origin/master")
    assert "\n* " in notes
    assert f"...v{v}" in notes.strip().splitlines()[-1]
    git("tag", f"v{v}", master, cwd=work)
    git("push", "-q", "origin", f"v{v}", cwd=work)
    assert f"[x] tag v{v}" in box.status()

    # Phase 5: antares-cd gets the version and the full hash of the master merge commit, once.
    box.tool("cd-update", v, "--repo", box.antares_cd)
    assert git("log", "-1", "--format=%s", cwd=box.antares_cd) == f"build: release v{v} ({date})"
    assert f"version: {v}" in (box.antares_cd / "application_description.yml").read_text()
    assert f'{{"version": "{v}", "gitcommit": "{master}" }}' in (box.antares_cd / "docs" / "dt-devops.md").read_text()
    commits = git("rev-list", "--count", "HEAD", cwd=box.antares_cd)
    assert "nothing to do" in box.tool("cd-update", v, "--repo", box.antares_cd)
    assert git("rev-list", "--count", "HEAD", cwd=box.antares_cd) == commits

    # The released master carries the version, the production date and the changelog title.
    init_py = git("show", "origin/master:antarest/__init__.py", cwd=work)
    assert f'__version__ = "{v}"' in init_py
    assert f'__date__ = "{date}"' in init_py
    assert f'\nversion = "{v}"' in git("show", "origin/master:pyproject.toml", cwd=work)
    assert f"\nv{v} ({date})\n" in git("show", "origin/master:docs/CHANGELOG.md", cwd=work)

    # The next release is not blocked: the release commit is the same in master and in dev.
    major, minor, _ = v.split(".")
    next_preflight = box.tool("preflight", f"{major}.{int(minor) + 1}.0", check=False)
    assert "[OK] every release commit of origin/master is in origin/dev" in next_preflight


if __name__ == "__main__":
    # Sandbox at Phase 0, with the skill inside, to watch an agent follow the runbook (use GH_TOKEN=invalid).
    if len(sys.argv) != 2:
        sys.exit(f"usage: {Path(__file__).name} <sandbox dir>")
    target = Path(sys.argv[1]).resolve()
    shutil.rmtree(target, ignore_errors=True)
    sandbox = build_sandbox(target)
    shutil.copytree(
        SKILL, sandbox.work / ".agents" / "skills" / SKILL.name, ignore=shutil.ignore_patterns("__pycache__")
    )
    with (sandbox.work / ".git" / "info" / "exclude").open("a") as exclude:
        exclude.write(".agents/\n")
    print(f"sandbox for v{sandbox.version} ready in {sandbox.work}, antares-cd stand-in in {sandbox.antares_cd}")
