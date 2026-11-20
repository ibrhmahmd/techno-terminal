# Branch protection

How `main` and `staging` are protected in `ibrhmahmd/techno_terminal_UI`, and how to apply the same setup to another repo (e.g. the backend `ibrhmahmd/techno-terminal`).

## The flow

```
short branch (fix/…, feat/…) ──PR──▶ staging ──PR──▶ main
                                       │               │
                              preview / staging    production
```

- All work lands on `staging` through a PR. `staging` must always contain all of `main` (merge `main` → `staging`, never the reverse locally).
- `main` changes only through a PR **from `staging`**, and only when the owner decides to release.

## What is enforced, and where

| Layer | Rule | Where it lives |
|---|---|---|
| GitHub ruleset `protect-main` | PR required (0 approvals, conversations resolved), merge commits only, required checks `checks` + `source-branch`, branch up to date, no force-push, no deletion | repo Settings → Rules → Rulesets |
| GitHub ruleset `protect-staging` | PR required (0 approvals, conversations resolved), merge commits only, required check `checks`, no force-push, no deletion | same |
| CI job `source-branch` | fails any PR into `main` whose head branch isn't `staging` | `.github/workflows/ci.yml` |
| Repo security | secret scanning + push protection, Dependabot alerts | Settings → Code security |
| Local git hook | refuses any push to `main` (bypass: `--no-verify`) | `.git/hooks/pre-push` (per clone, not committed) |
| Agent deny rules | Claude can't push/checkout `main`, merge PRs, delete rulesets, or use `--no-verify` | `.claude/settings.json` |

Approvals are 0 because a solo owner can't approve their own PR. The PR + CI requirement is the gate. Signed commits are **not** required yet: turn that on only after commit signing is set up locally, or it blocks every unsigned commit.

## Apply to another repo

Needs `gh` logged in as a repo admin. Set the two variables first:

- `REPO`: `owner/name`
- `CHECK`: the name of the CI **job** that must pass (UI: `checks`; backend: `test`, from `tests.yml`). The job must have run at least once so GitHub knows it.

### 1. Add the `source-branch` job to CI

Add this job to the workflow that runs on `pull_request` to `main` (backend: `.github/workflows/tests.yml`). Pass the branch name through `env`, never `${{ }}` inside `run:`; a branch name is attacker-controlled text.

```yaml
  # main only accepts PRs from staging (all work lands on staging first).
  source-branch:
    name: source-branch
    if: github.event_name == 'pull_request' && github.base_ref == 'main'
    runs-on: ubuntu-latest
    steps:
      - env:
          HEAD_REF: ${{ github.head_ref }}
        run: |
          if [ "$HEAD_REF" != "staging" ]; then
            echo "PRs into main must come from staging (got: $HEAD_REF)." >&2
            exit 1
          fi
```

Merge it into `staging` first. Only require `source-branch` on `main` once it exists on `staging`, or the release PR is blocked.

### 2. Rulesets

```bash
REPO=ibrhmahmd/techno-terminal
CHECK=test

ruleset() { # name branch strict check...
  local name=$1 branch=$2 strict=$3; shift 3
  local checks; checks=$(printf '{"context":"%s","integration_id":15368},' "$@"); checks="[${checks%,}]"
  gh api -X POST "repos/$REPO/rulesets" --input - <<EOF
{
  "name": "$name", "target": "branch", "enforcement": "active",
  "conditions": {"ref_name": {"include": ["refs/heads/$branch"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "pull_request", "parameters": {
      "allowed_merge_methods": ["merge"],
      "required_approving_review_count": 0,
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_review_thread_resolution": true}},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": $strict,
      "do_not_enforce_on_create": false,
      "required_status_checks": $checks}}
  ]
}
EOF
}

ruleset protect-staging staging false "$CHECK"
ruleset protect-main    main    true  "$CHECK" source-branch   # after step 1 is on staging
```

`15368` is the GitHub Actions app id, so only a check from Actions satisfies the rule, not a status anyone could post.

Check: `gh api repos/$REPO/rulesets --jq '.[].name'`. Rulesets and old classic branch protection both apply (the stricter wins). Once the rulesets are active, the classic rules can be removed in Settings → Branches.

### 3. Security settings

```bash
gh api -X PATCH "repos/$REPO" --input - <<'EOF'
{"security_and_analysis": {
  "secret_scanning": {"status": "enabled"},
  "secret_scanning_push_protection": {"status": "enabled"}}}
EOF
gh api -X PUT "repos/$REPO/vulnerability-alerts"   # Dependabot alerts
```

### 4. Local guards (each clone)

`.git/hooks/pre-push` (then `chmod +x .git/hooks/pre-push`):

```sh
#!/bin/sh
# Local guard: refuse any push that updates or deletes main on any remote.
# Bypass deliberately (only when you mean it): git push --no-verify ...
while read local_ref local_sha remote_ref remote_sha; do
  if [ "$remote_ref" = "refs/heads/main" ]; then
    echo "pre-push: pushing to main is blocked on this machine. Open a PR from staging instead." >&2
    exit 1
  fi
done
exit 0
```

`.claude/settings.json` (commit it):

```json
{
  "permissions": {
    "deny": [
      "Bash(git push * main)",
      "Bash(git push * main *)",
      "Bash(git push *:main)",
      "Bash(git push *:main *)",
      "Bash(git push *:refs/heads/main*)",
      "Bash(git push --no-verify*)",
      "Bash(git push * --no-verify*)",
      "Bash(git checkout main)",
      "Bash(git checkout main *)",
      "Bash(git switch main)",
      "Bash(git switch main *)",
      "Bash(gh pr merge*)",
      "Bash(gh api * rulesets*-X DELETE*)",
      "Bash(gh api * -X DELETE * rulesets*)"
    ]
  }
}
```

Add a line to the repo's `AGENTS.md` so other agents (OpenCode) follow the same rules: work lands on `staging`; never push or merge into `main`.
