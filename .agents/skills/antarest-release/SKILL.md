---
name: antarest-release
description: Use when preparing, continuing or checking an Antares Web (AntaREST) release - a release/vX.Y.Z branch, version bump, docs/CHANGELOG.md, recette or production deployment through Jenkins, the master and dev merges, the GitHub release, antares-cd or the desktop build.
---

# Antares Web release

Runbook for a git-flow release of Antares Web. The tools do the mechanical work. The human
decides at every checkpoint (🛑) and keeps the two jobs no tool can do: testing recette and
reviewing the release PR.

Both tools run from the AntaREST repository root:

- `TOOL` = `python3 .agents/skills/antarest-release/scripts/release_tool.py`. Local only: it
  edits files and commits, it never pushes.
- `JENKINS` = `python3 .agents/skills/antarest-release/scripts/jenkins_tool.py`. It prints a plan
  and its checks, and launches a job only with `--confirm`.

## Prerequisite: a Jenkins API token

A release cannot be completed without one: the recette build (Phase 2), the tagged build and the
production tag (Phase 6) are Jenkins jobs, launched with the token of the person doing the
release. Check it first, in Phase 0, so the release does not stop halfway.

The user sets it up once, in their own terminal:

1. **Get the token.** In Jenkins, open the menu under your name (top right), then **Security**,
   then **API Token**: **Add new token**, give it a name, **Generate**. Copy it at once, Jenkins
   shows it only that time. A lost token is not recovered: revoke it there and generate another.
2. **Store it** in `~/.jenkins-netrc`, a file only its owner can read:

   ```bash
   touch ~/.jenkins-netrc && chmod 600 ~/.jenkins-netrc
   ```

   then, with an editor (not `echo`, which leaves the token in the shell history), one line:

   ```
   machine <jenkins host> login <jenkins user> password <api token>
   ```

   `<jenkins host>` is the server name alone, without `https://`: the same host as in the
   address bar when Jenkins is open. It is not written in this repository, which is public.
   Another location is possible with the `JENKINS_NETRC` environment variable.
3. **Check it:** `JENKINS whoami` must print `authenticated: True`. The tool refuses a file that
   others can read (`chmod 600`), a file with several `machine` lines, and a rejected token.

The token carries all the rights of its owner on Jenkins, which is why every launch is a
checkpoint. Never ask for it in the conversation, never print the file, never write it anywhere
else. If the file is missing, give the user these three steps and wait.

## Rules

1. **🛑 means stop and ask.** A 🛑 is either a decision only the human can take (inputs,
   changelog, recette) or a write to GitHub, GitLab or Jenkins. Show exactly what will happen
   (the command; for Jenkins, the whole plan printed without `--confirm`), then wait for an
   explicit go. One go covers one step: never chain two 🛑 on one approval, and "go ahead with
   the release" said earlier is not a go for a later step, even from a user who says they will
   be unreachable. In that case do the local work up to the next 🛑, leave the question ready,
   and say what is still waiting for them.
2. **A refusal is a finding, not an obstacle.** When a tool prints `[FAIL]` or exits with an
   error, report it and stop. Never do by hand (`curl`, manual edit, `git` plumbing) what a tool
   refused to do.
3. **Merge commits only, into AntaREST `master` and `dev`.** Never squash, never rebase. A squash
   gives the same release two different commits, and the next release PR conflicts on every
   version file (happened on 2.19.2 and 2.36.0).
4. **Exact messages.** `TOOL commit` and `TOOL cd-update` write theirs. The others are given
   literally below. Append nothing: no body, no `Co-Authored-By` trailer, no generated footer.
5. **Never `git commit -a` or `git add -A`.** The user may have unrelated work in the tree.
6. **Releases span days.** Start every session with `git fetch origin --tags` and
   `TOOL status X.Y.Z`: it prints what is done and the next step.
7. **Waits run in the background.** `JENKINS wait` and `gh run watch` are launched as background
   commands. Do not poll by hand, and do not relaunch a failed job without a new go.

## Checkpoints

| 🛑 | Before | The human validates |
|---|---|---|
| 1 | `TOOL prepare` | version, production date, cut point |
| 2 | `TOOL commit` and pushing the release branch | the changelog |
| 3 | the recette build | the Jenkins plan |
| 4 | opening the PR to `master` | recette, which they tested themselves |
| 5 | the back-merge to `dev` | the route: a PR, or a direct push |
| 6 | publishing the GitHub release | notes and target commit |
| 7 | pushing `antares-cd` | the diff |
| 8 | the tagged build | the Jenkins plan |
| 9 | Highway To Prod | the Jenkins plan: it creates the production tag |
| 10, 11 | the desktop PR, then the desktop release | submodule commit, then release |

The merge of the release PR is not in this table: a third person reviews and merges it.

A 🛑 covers everything listed on its line and nothing else: the go on the changelog covers the
release commit and its push, the go on the dev route covers restoring the release branch.

## Phase 0 - Inputs and preflight

```bash
git fetch origin --tags
TOOL preflight X.Y.Z
JENKINS whoami          # must print "authenticated: True"; otherwise see the prerequisite above
```

🛑 1. Three inputs. What the user already stated in their request counts; ask only for the rest:

- version `X.Y.Z`;
- planned **production date** `YYYY-MM-DD` (not today's date unless the user says so);
- cut point: the tip of `origin/dev`, printed by `preflight`, is what gets released. Tell the
  user which commit that is.

A `FAIL` blocks the release. `every release commit of origin/master is in origin/dev` means a
past release reached dev by squash: `prepare` refuses to run. Stop and ask the user. The repair
that keeps the history clean: create `release/vX.Y.Z` from `origin/dev` by hand, merge that one
commit into it (the commit itself, not `master`), then run `prepare` from that branch.

## Phase 1 - Branch, version, changelog

```bash
TOOL prepare X.Y.Z -d YYYY-MM-DD
```

It creates `release/vX.Y.Z` from `origin/dev`, bumps the version in 6 files, writes the changelog
draft into `docs/CHANGELOG.md`, runs `uv lock --check` and stages the 7 release files. It refuses
a tree with uncommitted changes: ask the user, do not stash for them.

🛑 2. Changelog review. Show the new section, and report what `prepare` printed (a block that
is not printed means there is none):

- `BREAKING CHANGES`: commits marked `!`; the badge is added automatically. List them. A
  `chore!` lands under Miscellaneous: ask whether it stays there.
- `NEEDS REVIEW`: subjects to place by hand.
- Entries are filed by commit type. Propose re-filing only where the type is misleading (a
  `chore` that is a refactoring, a `feat` that only fixes an unreleased feature). Do not reword
  descriptions and do not drop entries on your own.

Say that the go also pushes the branch. Edit `docs/CHANGELOG.md` as agreed, then:

```bash
TOOL commit X.Y.Z       # stages the 7 files again, commits "chore(release): vX.Y.Z (YYYY-MM-DD)"
git push -u origin release/vX.Y.Z
```

Report the commit that was pushed. Then wait for the `main` workflow, in the background:
`gh run watch "$(gh run list --branch release/vX.Y.Z --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status`

## Phase 2 - Recette

```bash
JENKINS recette X.Y.Z                 # plan and checks, launches nothing
```

🛑 3. After the go: `JENKINS recette X.Y.Z --confirm`. It prints the build number `N`; follow it
with `JENKINS wait icdc N` in the background (about 10 minutes). On failure, `wait` names the
failed downstream build: report it.

The user then tests recette. Wait for their verdict. If recette finds a bug, the written process
does not say how the fix reaches the release branch: ask.

## Phase 3 - Merge to master, then to dev

🛑 4. Only once the user says recette is validated:
`gh pr create --base master --head release/vX.Y.Z --title "chore(release): vX.Y.Z" --body ""`

A third person reviews version, date, changelog and overall coherence, then merges with
**Create a merge commit**, message exactly `vX.Y.Z`. Never merge this PR yourself. When the user
says it is merged, `git fetch origin && TOOL status X.Y.Z` must tick `merged into origin/master`.
A `PROBLEM` line means a squash: stop.

Then dev. 🛑 5. Ask the user which route they use, and say what their answer launches. Either
way, if GitHub deleted the release branch, restore it first (`git push origin release/vX.Y.Z`):
the same go covers it.

- a PR: `gh pr create --base dev --head release/vX.Y.Z --title "chore(release): vX.Y.Z" --body ""`,
  merged with a **merge commit** by someone allowed to bypass the rule (dev normally forbids
  merge commits); or
- locally, on a clean tree:

  ```bash
  git checkout dev && git pull
  git merge --no-ff origin/release/vX.Y.Z -m "Merge remote-tracking branch 'origin/release/vX.Y.Z' into dev"
  git push origin dev
  ```

`TOOL status X.Y.Z` must then tick `merged back into origin/dev`.

## Phase 4 - GitHub release

```bash
TOOL notes X.Y.Z --ref origin/master > release-notes.md    # in your scratch directory
git rev-parse origin/master                                # <sha> of the "vX.Y.Z" merge commit
```

🛑 6. `gh release create vX.Y.Z --target <sha> --title vX.Y.Z --notes-file release-notes.md`
(publishing creates the tag).

Assets: the written process attaches the Windows worker (artifact `AntaresWebWorker` of the
`worker` workflow run on master), but v2.33.0 to v2.36.0 were published without any asset. Ask.

## Phase 5 - antares-cd (GitLab, separate clone)

Before Phase 6. Ask for the clone path (often a sibling `../antares-cd`).

```bash
TOOL cd-update X.Y.Z --repo <path>
```

It requires a clean clone on an up-to-date `master` (if it is elsewhere, ask before switching
branch), sets the version and the full hash of the master merge commit in `docs/dt-devops.md`
and `application_description.yml`, prints the diff and commits `build: release vX.Y.Z (date)`.

New simulator version shipped? Ask; if so add it by hand to `solver_versions` in
`livraison/installation/inventory/group_vars/{prod,recette,integration}` and amend that commit.

🛑 7. `git -C <path> push origin master` (direct push to master, no review: say so when asking).

## Phase 6 - Production tag

```bash
JENKINS tag X.Y.Z                     # plan: builds origin/master, DOIT_TAGGER and RAPPORT_SONAR
```

The plan deploys nowhere (`ENVIRONNEMENT_CIBLE=Aucun`), as was done for 2.36.0. The written
process says to redeploy on recette instead. Say so in the ask; `--env recette` if they prefer.

🛑 8. `JENKINS tag X.Y.Z --confirm`, then `JENKINS wait icdc N` in the background. On success
the tag is `XX.YY.ZZ-devN`, `N` being the build number.

```bash
JENKINS promote X.Y.Z --build N       # plan: checks build N is a successful tagged build of master
```

🛑 9. State plainly that this creates the production tag `XX.YY.ZZ-prodNNN`. After the go:
`JENKINS promote X.Y.Z --build N --confirm`, then `JENKINS wait prod M`.

## Phase 7 - Desktop

Repository `AntaresSimulatorTeam/antares_desktop`. Rule 3 does not apply there: its `main`
history is squash-merged PRs. `<sha>` is the commit of tag `vX.Y.Z` (`git rev-list -n1 vX.Y.Z`).

```bash
gh repo clone AntaresSimulatorTeam/antares_desktop <scratch>/antares_desktop   # no submodule checkout needed
cd <scratch>/antares_desktop && git checkout -b release/X.Y
git update-index --cacheinfo 160000,<sha>,antares_web
git commit -m "vX.Y.Z" && git show --stat HEAD      # exactly one line: antares_web
```

Ask whether the desktop build needs other changes for this version (Python, Node or simulator
versions pinned in that repository's workflows), and add them to the same branch.

🛑 10. `git push -u origin release/X.Y && gh pr create --base main --title "vX.Y.Z" --body ""`.
A maintainer merges it.

🛑 11. Once merged:
`gh release create vX.Y.Z -R AntaresSimulatorTeam/antares_desktop --target main --title vX.Y.Z --notes "Desktop version of AntaresWeb vX.Y.Z"`
Publishing triggers the `release` workflow, which attaches `AntaresWeb-ubuntu-22.04-vX.Y.Z.zip`
and `AntaresWeb-windows-latest-vX.Y.Z.zip`. Watch it in the background, then check the assets.

## Jenkins: history and manual launch

`JENKINS history` lists the recent builds of both jobs with their parameters: use it to see what
was already launched for this release.

If the user prefers to launch a job by hand, or Jenkins is unreachable: job **10 - IC⚡DC** with
`VERSION_APP` zero-padded (`02.37.00`), `COMPOSANT_A_CONSTRUIRE` = `Sélection avancée`,
`COMPOSANTS_ET_BRANCHES` = `[antarest: <ref>, antarest-webapp: <ref>,]`, `DOIT_PUBLIER` checked;
`<ref>` = `origin/release/vX.Y.Z` and `ENVIRONNEMENT_CIBLE` = `recette` for Phase 2,
`origin/master` with `DOIT_TAGGER` and `RAPPORT_SONAR` checked for Phase 6. Then job
**11 - Highway To Prod**: `VERSION_A_PROMOUVOIR` = `XX.YY.ZZ-devN`, `VERSION_APP` = `XX.YY.ZZ`.

## Not covered

Hotfix releases (branch from master) are not described by the written process. Ask the user
instead of adapting this runbook.

## Common mistakes

| Mistake | Consequence |
|---|---|
| Treating an earlier go as covering the next 🛑 | A push, a deployment or the production tag nobody approved |
| `--confirm` on the first run, without showing the plan | The human validated nothing |
| Relaunching a failed Jenkins build on your own | A second deployment nobody asked for |
| Squash or rebase merge of the release into master or dev | Conflicts on all version files at the next release |
| Local dev merge without `--no-ff` | Fast-forward: no merge commit, message ignored |
| Today's date instead of the production date | Wrong `__date__` and changelog title |
| Tagged build launched before the PR is merged | The tag lands on the previous release; `JENKINS tag` refuses it |
| `git describe` to find the previous release | Tags live on master merge commits, unreachable from dev; use `TOOL preflight` |
| Short hash in `antares-cd` | The delivery procedure compares it with `/api/version`, which returns the full hash; `cd-update` writes the full one |

## Testing the tools

`uv run pytest .agents/skills/antarest-release/tests/test_release_tool.py` replays Phases 0 to 5
in a sandbox whose remotes are local bare repositories, so nothing can reach GitHub, GitLab or
Jenkins. Run it after any change to the tools. To watch an agent follow the runbook, run the same
file with `python3 <file> <sandbox dir>`: it only prepares a sandbox at Phase 0, then start your
agent inside `<sandbox dir>/work` with `GH_TOKEN=invalid`.
