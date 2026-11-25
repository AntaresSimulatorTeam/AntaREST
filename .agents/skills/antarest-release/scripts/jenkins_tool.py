#!/usr/bin/env python3
"""
Jenkins side of the Antares Web release runbook.

A launching subcommand prints its plan and its checks, then stops. It launches
only with `--confirm`, which is passed once the user approved that exact plan.

    jenkins_tool.py whoami
    jenkins_tool.py history                                # recent builds of both jobs
    jenkins_tool.py recette X.Y.Z [--confirm]              # release branch -> recette
    jenkins_tool.py tag X.Y.Z [--env recette] [--confirm]  # tagged build of master
    jenkins_tool.py promote X.Y.Z --build N [--confirm]    # production tag
    jenkins_tool.py wait {icdc,prod} N                     # follow a build until it ends

Credentials: a netrc file readable by its owner only (default ~/.jenkins-netrc,
or $JENKINS_NETRC) holding one line:

    machine <jenkins host> login <user> password <api token>

The host of that line is the Jenkins server, so no internal address is stored
in this repository. Requests never go through the internet proxy.
"""

import argparse
import base64
import datetime
import json
import netrc
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

JOBS = {"icdc": "antares/IC_DC", "prod": "antares/HighwayToProd"}
HISTORY_BUILDS = 6
WAIT_MINUTES = 45
GITHUB_REPO = "AntaresSimulatorTeam/AntaREST"
VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
ENVIRONMENTS = ["Aucun", "integration", "recette"]
PARAMETERS_TREE = "property[parameterDefinitions[name,choices,defaultParameterValue[value]]]"
BUILD_TREE = "number,result,building,timestamp,duration,actions[parameters[name,value]]"


class JenkinsError(Exception):
    pass


class Jenkins:
    def __init__(self, base: str = "", login: str = "", token: str = "") -> None:
        if not base:
            base, login, token = self._credentials()
        self.base = base.rstrip("/")
        basic = base64.b64encode(f"{login}:{token}".encode()).decode()
        self._headers = {"Authorization": f"Basic {basic}", "User-Agent": "antarest-release"}
        # Jenkins is an internal host: the internet proxy of the environment cannot reach it.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @staticmethod
    def _credentials() -> tuple[str, str, str]:
        path = Path(os.environ.get("JENKINS_NETRC", "~/.jenkins-netrc")).expanduser()
        if not path.is_file():
            raise JenkinsError(f"{path} not found. The user creates it once, see the prerequisite section of SKILL.md.")
        if path.stat().st_mode & 0o077:
            raise JenkinsError(f"{path} is readable by others: chmod 600 {path}")
        hosts = netrc.netrc(str(path)).hosts
        if len(hosts) != 1:
            raise JenkinsError(f"{path} must hold exactly one `machine` entry, found {len(hosts)}")
        host, (login, _, token) = next(iter(hosts.items()))
        if not login or not token:
            raise JenkinsError(f"{path}: login or password missing")
        return f"https://{host}", login, token

    def job_url(self, job: str) -> str:
        return self.base + "".join(f"/job/{urllib.parse.quote(part)}" for part in job.split("/"))

    def _open(self, url: str, data: bytes | None = None) -> tuple[bytes, Any]:
        if not url.startswith(self.base + "/"):
            raise JenkinsError(f"Refusing to send the credentials to {url}")
        request = urllib.request.Request(
            url, data=data, headers=self._headers, method="POST" if data is not None else "GET"
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                return response.read(), response.headers
        except urllib.error.HTTPError as exc:
            hint = " (check the token in the netrc file)" if exc.code in (401, 403) else ""
            raise JenkinsError(f"HTTP {exc.code} on {url.split('?')[0]}{hint}") from exc
        except urllib.error.URLError as exc:
            raise JenkinsError(f"Cannot reach Jenkins: {exc.reason}") from exc

    def get_json(self, url: str, tree: str = "") -> Any:
        query = f"?tree={urllib.parse.quote(tree, safe='[],')}" if tree else ""
        return json.loads(self._open(f"{url.rstrip('/')}/api/json{query}")[0])

    def get_text(self, url: str) -> str:
        return self._open(url)[0].decode("utf-8", errors="replace")

    def launch(self, job: str, params: dict[str, str], queue_timeout: int = 300) -> int:
        """Queues a parameterized build and returns its number once an executor picked it up."""
        _, headers = self._open(f"{self.job_url(job)}/buildWithParameters", urllib.parse.urlencode(params).encode())
        queue_url = headers.get("Location")
        if not queue_url:
            raise JenkinsError("Jenkins accepted the request without a queue location: check the job page")
        print(f"queued: {queue_url}")
        deadline = time.monotonic() + queue_timeout
        while True:
            item = self.get_json(queue_url, "cancelled,why,executable[number]")
            if item.get("cancelled"):
                raise JenkinsError("The queued build was cancelled")
            if item.get("executable"):
                return int(item["executable"]["number"])
            if time.monotonic() > deadline:
                raise JenkinsError(f"Still queued after {queue_timeout}s ({item.get('why')}): follow {queue_url}")
            time.sleep(5)


def parse_version(text: str) -> tuple[int, int, int]:
    mo = VERSION_RE.fullmatch(text)
    if mo is None:
        sys.exit(f"Invalid version '{text}': expected X.Y.Z")
    return int(mo[1]), int(mo[2]), int(mo[3])


def padded(version: tuple[int, int, int]) -> str:
    """Jenkins wants two digits per component: 2.37.0 -> 02.37.00."""
    return "{:02d}.{:02d}.{:02d}".format(*version)


def git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], capture_output=True, text=True)


def build_parameters(build: Any) -> dict[str, str]:
    return {p["name"]: str(p.get("value")) for a in build.get("actions", []) for p in a.get("parameters") or []}


def when(build: Any) -> str:
    return datetime.datetime.fromtimestamp(build["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M")


def outcome(build: Any) -> str:
    return "RUNNING" if build.get("building") else str(build.get("result"))


class Plan:
    """What would be launched, and whether it may be."""

    def __init__(self, jenkins: Jenkins, alias: str, title: str) -> None:
        self.jenkins = jenkins
        self.alias = alias
        self.job = JOBS[alias]
        self.title = title
        self.params: dict[str, str] = {}
        self.failures = 0
        self._declared: dict[str, Any] = {}

    def check(self, ok: bool, label: str, hint: str = "") -> None:
        print(f"[{'OK' if ok else 'FAIL'}] {label}")
        if not ok:
            self.failures += 1
            if hint:
                print(f"       {hint}")

    def common_checks(self) -> None:
        origin = git("remote", "get-url", "origin").stdout.strip()
        self.check(
            GITHUB_REPO.lower() in origin.lower(),
            "this clone's origin is the real AntaREST repository",
            "sandbox clone: Jenkins launches are disabled here",
        )
        job = self.jenkins.get_json(
            self.jenkins.job_url(self.job), f"buildable,inQueue,lastBuild[number,building],{PARAMETERS_TREE}"
        )
        last = job.get("lastBuild") or {}
        self.check(bool(job.get("buildable")), "the job is buildable")
        self.check(
            not job.get("inQueue") and not last.get("building"),
            "no build of this job is queued or running",
            f"build #{last.get('number')} is in progress: wait for it, never launch a second one",
        )
        declared = {d["name"]: d for p in job.get("property", []) for d in p.get("parameterDefinitions") or []}
        unknown = sorted(set(self.params) - set(declared))
        self.check(
            not unknown,
            "every parameter sent is declared by the job",
            f"unknown: {unknown}. The job changed: ask the user.",
        )
        for name, value in self.params.items():
            choices = (declared.get(name) or {}).get("choices")
            if choices and value not in choices:
                self.check(False, f"{name}={value!r} is an allowed choice", f"allowed: {choices}")
        self._declared = declared

    def show(self) -> None:
        print(f"\n{self.title}")
        print(f"job: {self.jenkins.job_url(self.job)}")
        width = max(len(name) for name in self._declared) if self._declared else 0
        for name, definition in self._declared.items():
            if name in self.params:
                print(f"  {name:<{width}}  {self.params[name]}")
            else:
                default = (definition.get("defaultParameterValue") or {}).get("value")
                print(f"  {name:<{width}}  {default}   (job default, not sent)")

    def finish(self, confirm: bool, after: str) -> int:
        self.show()
        if self.failures:
            print(f"\n{self.failures} check(s) failed: nothing can be launched. Report this to the user.")
            return 1
        if not confirm:
            print(
                "\nPLAN ONLY, nothing was launched. Show this plan to the user; after their go, re-run with --confirm."
            )
            return 0
        number = self.jenkins.launch(self.job, self.params)
        print(f"\nLAUNCHED: {self.jenkins.job_url(self.job)}/{number}/")
        print(f"build number: {number}")
        print(after.format(n=number, alias=self.alias))
        return 0


def icdc_parameters(version: tuple[int, int, int], ref: str, environment: str, tagged: bool) -> dict[str, str]:
    flag = "true" if tagged else "false"
    return {
        "VERSION_APP": padded(version),
        "COMPOSANT_A_CONSTRUIRE": "Sélection avancée",
        # Exact format of the previous releases, trailing comma included.
        "COMPOSANTS_ET_BRANCHES": f"[antarest: {ref}, antarest-webapp: {ref},]",
        "ENVIRONNEMENT_CIBLE": environment,
        "DOIT_PUBLIER": "true",
        "DOIT_TAGGER": flag,
        "RAPPORT_SONAR": flag,
    }


def cmd_whoami(jenkins: Jenkins, args: argparse.Namespace) -> int:
    me = jenkins.get_json(f"{jenkins.base}/whoAmI")
    print(f"authenticated: {me.get('authenticated')} as {me.get('name')}")
    return 0 if me.get("authenticated") and not me.get("anonymous") else 1


def cmd_history(jenkins: Jenkins, args: argparse.Namespace) -> int:
    shown = {
        "icdc": [
            "VERSION_APP",
            "COMPOSANTS_ET_BRANCHES",
            "ENVIRONNEMENT_CIBLE",
            "DOIT_PUBLIER",
            "DOIT_TAGGER",
            "RAPPORT_SONAR",
        ],
        "prod": ["VERSION_A_PROMOUVOIR", "VERSION_APP", "DRY_RUN"],
    }
    for alias, names in shown.items():
        job = jenkins.get_json(jenkins.job_url(JOBS[alias]), f"displayName,builds[{BUILD_TREE}]{{0,{HISTORY_BUILDS}}}")
        print(f"== {alias}: {job.get('displayName')}")
        for build in job.get("builds", []):
            params = build_parameters(build)
            values = ", ".join(f"{name}={params.get(name)}" for name in names)
            print(f"#{build['number']} {when(build)} {outcome(build)} | {values}")
        print()
    return 0


def cmd_recette(jenkins: Jenkins, args: argparse.Namespace) -> int:
    version = parse_version(args.version)
    branch = "release/v{}.{}.{}".format(*version)
    plan = Plan(jenkins, "icdc", f"Recette deployment of {branch}")
    plan.params = icdc_parameters(version, f"origin/{branch}", "recette", tagged=False)

    remote = git("ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{branch}")
    tip = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout else ""
    plan.check(
        bool(tip), f"{branch} is pushed to origin{' at ' + tip[:9] if tip else ''}", "push the release branch first"
    )
    plan.common_checks()
    return plan.finish(
        args.confirm, "next: `jenkins_tool.py wait {alias} {n}` in the background, then the user tests recette."
    )


def cmd_tag(jenkins: Jenkins, args: argparse.Namespace) -> int:
    version = parse_version(args.version)
    dotted = "{}.{}.{}".format(*version)
    plan = Plan(jenkins, "icdc", f"Tagged build of master for v{dotted} (creates the tag {padded(version)}-devN)")
    plan.params = icdc_parameters(version, "origin/master", args.env, tagged=True)

    remote = git("ls-remote", "--exit-code", "origin", "refs/heads/master")
    tip = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout else ""
    described = git("log", "-1", "--format=%s%n%P", tip) if tip else None
    subject, parents = "", 0
    if described is not None and described.returncode == 0:
        subject, _, parent_line = described.stdout.strip().partition("\n")
        parents = len(parent_line.split())
    is_release = bool(re.search(rf"(?:^|\s)v{re.escape(dotted)}(?:\s|$)", subject)) and parents == 2
    plan.check(
        is_release,
        f"origin/master is the v{dotted} merge commit{' (' + tip[:9] + ' ' + subject + ')' if subject else ''}",
        "merge the release PR first, then `git fetch origin`" if tip else "cannot read origin/master",
    )
    plan.common_checks()
    return plan.finish(
        args.confirm,
        "next: `jenkins_tool.py wait {alias} {n}` in the background. On success the tag is "
        + padded(version)
        + "-dev{n}; then `jenkins_tool.py promote "
        + dotted
        + " --build {n}`.",
    )


def cmd_promote(jenkins: Jenkins, args: argparse.Namespace) -> int:
    version = parse_version(args.version)
    dev_tag = f"{padded(version)}-dev{args.build}"
    plan = Plan(jenkins, "prod", f"PRODUCTION TAG: promotes {dev_tag} (creates {padded(version)}-prodNNN)")
    plan.params = {"VERSION_A_PROMOUVOIR": dev_tag, "VERSION_APP": padded(version)}

    try:
        build = jenkins.get_json(f"{jenkins.job_url(JOBS['icdc'])}/{args.build}", BUILD_TREE)
    except JenkinsError as exc:
        build = None
        plan.check(False, f"build #{args.build} of {JOBS['icdc']} can be read", str(exc))
    if build is not None:
        params = build_parameters(build)
        plan.check(outcome(build) == "SUCCESS", f"build #{args.build} succeeded ({outcome(build)}, {when(build)})")
        plan.check(params.get("DOIT_TAGGER") == "True", f"build #{args.build} was a tagged build (DOIT_TAGGER)")
        plan.check(
            params.get("VERSION_APP") == padded(version),
            f"build #{args.build} was built as {padded(version)} (found {params.get('VERSION_APP')})",
        )
        plan.check(
            "origin/master" in params.get("COMPOSANTS_ET_BRANCHES", ""),
            f"build #{args.build} was built from origin/master ({params.get('COMPOSANTS_ET_BRANCHES')})",
        )
    plan.common_checks()
    return plan.finish(args.confirm, "next: `jenkins_tool.py wait {alias} {n}` in the background.")


def cmd_wait(jenkins: Jenkins, args: argparse.Namespace) -> int:
    job = JOBS.get(args.job, args.job)
    url = f"{jenkins.job_url(job)}/{args.build}"
    deadline = time.monotonic() + WAIT_MINUTES * 60
    while True:
        build = jenkins.get_json(url, BUILD_TREE)
        if not build.get("building"):
            break
        if time.monotonic() > deadline:
            print(f"still running after {WAIT_MINUTES} min: {url}/")
            return 2
        time.sleep(20)

    minutes = round(build.get("duration", 0) / 60000, 1)
    print(f"{job} #{args.build}: {build.get('result')} in {minutes} min ({url}/)")
    params = build_parameters(build)
    if build.get("result") == "SUCCESS":
        if job == JOBS["icdc"] and params.get("DOIT_TAGGER") == "True":
            print(f"tag created: {params.get('VERSION_APP')}-dev{args.build}")
        return 0

    console = jenkins.get_text(f"{url}/consoleText").splitlines()
    # The release jobs delegate to one job per component: "Build <folder> » <job> #<n> completed: FAILURE".
    downstream = [line.strip() for line in console if re.search(r"^Build .+ #\d+ completed: ", line)]
    if downstream:
        print("downstream builds (read the console of the failed one with `wait <folder>/<job> <n>`):")
        for line in downstream:
            print(f"  {line}")
    print("end of the console:")
    for line in console[-15:]:
        print(f"  {line[:200]}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="check the credentials").set_defaults(func=cmd_whoami)

    sub.add_parser("history", help="recent builds of the two release jobs").set_defaults(func=cmd_history)

    def launching(p: argparse.ArgumentParser) -> None:
        p.add_argument("--confirm", action="store_true", help="launch; only after the user approved the plan")

    p_recette = sub.add_parser("recette", help="deploy the release branch on recette")
    p_recette.add_argument("version", help="version being released, X.Y.Z")
    launching(p_recette)
    p_recette.set_defaults(func=cmd_recette)

    p_tag = sub.add_parser("tag", help="tagged build of master, with the Sonar report")
    p_tag.add_argument("version", help="released version, X.Y.Z")
    p_tag.add_argument(
        "--env", choices=ENVIRONMENTS, default="Aucun", help="target environment (default: no deployment)"
    )
    launching(p_tag)
    p_tag.set_defaults(func=cmd_tag)

    p_promote = sub.add_parser("promote", help="create the production tag from a tagged build")
    p_promote.add_argument("version", help="released version, X.Y.Z")
    p_promote.add_argument("--build", type=int, required=True, help="number of the tagged build to promote")
    launching(p_promote)
    p_promote.set_defaults(func=cmd_promote)

    p_wait = sub.add_parser("wait", help="follow a build until it ends")
    p_wait.add_argument("job", help="icdc, prod, or a job path such as folder/name")
    p_wait.add_argument("build", type=int, help="build number")
    p_wait.set_defaults(func=cmd_wait)

    args = parser.parse_args()
    try:
        return int(args.func(Jenkins(), args))
    except JenkinsError as exc:
        print(f"jenkins: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
