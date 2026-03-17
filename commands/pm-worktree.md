---
name: pm-worktree
description: Create a git worktree with isolated environment. Scans project for env files, compose/stack files, and config — lets user pick what to copy, then auto-remaps ports and database names to avoid conflicts.
allowed-tools: "*"
---

# Create Isolated Worktree

Setting up worktree for: `$ARGUMENTS`

## Step 1: Parse Arguments

Parse `$ARGUMENTS` for:
- **branch-name** (optional): Name for the new branch. If empty, ask the user via AskUserQuestion.
- **path** (optional): Where to create the worktree. Default: `../<repo-name>-<branch-name>`

If no branch name given, ask:
> What should the branch be called?

## Step 2: Validate

1. Confirm we're in a git repository (`git rev-parse --git-dir`)
2. Check the branch name doesn't already exist (`git branch --list <name>`)
3. Check the target path doesn't already exist
4. If conflicts found, report them and ask the user how to proceed

## Step 3: Scan Project

Scan the project root for files that typically need copying or adapting. Search for:

**Environment files** (glob patterns):
- `.env*` (`.env`, `.env.local`, `.env.development`, `.env.production`, etc.)
- `*.env`

**Container/orchestration files:**
- `docker-compose*.yml` / `docker-compose*.yaml`
- `compose*.yml` / `compose*.yaml`
- `Dockerfile*`
- `devcontainer.json` / `.devcontainer/`

**Config files with potential port/DB references:**
- `config/*.yml` / `config/*.yaml` / `config/*.json`
- `*.config.js` / `*.config.ts` / `*.config.mjs`
- `Procfile`
- `Makefile` (check for port references)
- `.flaskenv`
- `settings.py` / `local_settings.py`

**Package/dependency files** (for reference, not copying):
- `package.json` (check `scripts` for hardcoded ports)
- `pyproject.toml` / `setup.cfg`

For each file found, extract:
- **Ports**: any number matching common port patterns (e.g. `PORT=3000`, `- "8080:8080"`, `localhost:5432`, `--port 3000`)
- **Database names**: `DB_NAME=`, `DATABASE_URL=`, `POSTGRES_DB=`, container volume names
- **Service names**: from compose files (`services:` keys)
- **Volume names**: from compose files (`volumes:` keys)

## Step 4: Present Findings

Show the user a structured summary:

```
📁 Scanned <repo-name> — found <N> files with environment/config data:

Environment files:
  ☐ .env (ports: 3000, 5432 | db: myapp_dev)
  ☐ .env.local (ports: 3000)

Compose files:
  ☐ docker-compose.yml (services: web, db, redis | ports: 3000, 5432, 6379)
  ☐ docker-compose.override.yml

Config files:
  ☐ config/database.yml (db: myapp_development)

Other:
  ☐ Procfile (port: 5000)
```

Then ask via AskUserQuestion:
> Which files should I copy to the worktree? (I'll auto-remap ports and DB names to avoid conflicts)

Options:
- **All listed files** — copy everything, remap all conflicts
- **Env + Compose only** — just environment and container files
- **Let me pick** — show each file individually for yes/no
- **None** — just create the bare worktree

## Step 5: Port Remapping Strategy

For each port found across selected files, calculate a non-conflicting offset:

**Rules:**
1. Collect ALL ports from the original project (both selected and non-selected files — we need the full picture)
2. Apply a consistent offset: `+100` to all ports (e.g. 3000→3100, 5432→5532, 6379→6479)
3. If an offset port collides with another original port, increment by another 100
4. Verify no remapped port exceeds 65535
5. Verify no remapped port conflicts with well-known system ports (22, 80, 443, etc.)

Build a port mapping table:
```
Port remapping:
  3000 → 3100
  5432 → 5532
  6379 → 6479
```

Show the mapping to the user and ask for confirmation via AskUserQuestion:
> Does this port mapping look good?

Options:
- **Yes, use these** — proceed
- **Use offset +200 instead** — recalculate with bigger offset
- **Let me set manually** — ask for each port individually

## Step 6: Database Isolation

For each database name found:
1. Append `_wt` suffix (e.g. `myapp_dev` → `myapp_dev_wt`)
2. If DATABASE_URL contains a DB name, update it there too
3. Update compose environment variables that reference DB names

For volume names in compose files:
1. Prefix with worktree branch name (e.g. `postgres_data` → `<branch>_postgres_data`)
2. This ensures compose volumes don't overlap

For container/service names in compose files:
1. Add `COMPOSE_PROJECT_NAME=<branch-name>` to the compose environment or `.env`
2. This namespaces all containers automatically without renaming services

Show the DB isolation plan and confirm.

## Step 7: Create Worktree

Execute in order:

```bash
# 1. Create the worktree with new branch
git worktree add -b <branch-name> <target-path>

# 2. Copy selected files to the worktree
# For each selected file, copy it then apply remappings
```

For each selected file:
1. Copy the original to the worktree path
2. Apply port remapping (replace all original→remapped ports)
3. Apply database name remapping
4. Apply volume/project name remapping
5. If it's a compose file, ensure `COMPOSE_PROJECT_NAME` is set

**Important:** Do NOT modify files in the original project. Only write to the worktree.

## Step 8: Verify

After creation:
1. Confirm worktree exists: `git worktree list`
2. Confirm branch exists: `git branch --list <branch-name>`
3. Confirm copied files exist in the worktree
4. Do a quick diff of one remapped file to show the user what changed

## Step 9: Report

```
Worktree created:
  Branch: <branch-name>
  Path:   <target-path>

Copied <N> files with remapping:
  .env            — ports: 3000→3100, 5432→5532 | db: myapp_dev→myapp_dev_wt
  docker-compose  — ports remapped, project name: <branch-name>, volumes namespaced

Quick start:
  cd <target-path>
  docker compose up -d   # runs on remapped ports, isolated DB

To remove later:
  git worktree remove <target-path>
  git branch -d <branch-name>
```

## Safety Rules

- **NEVER modify files in the original project** — all writes go to the worktree only
- **NEVER delete existing worktrees** — only create new ones
- **NEVER force-remove branches** — use `-d` not `-D`
- If any step fails, clean up: remove the worktree and branch, then report the error
- If the user has uncommitted changes, warn them before creating the worktree (worktrees share the git object store, uncommitted changes in the working directory are NOT shared)
