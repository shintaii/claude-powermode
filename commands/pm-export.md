---
name: pm-export
description: Export project documentation to a user-specified folder. Copies all markdown files from a project, preserving folder structure.
allowed-tools: "*"
---

# Export Project Documentation

Exporting project: `$ARGUMENTS`

## Step 1: Parse Arguments

Parse `$ARGUMENTS` for:
- **project-slug** (required): The project to export
- **target-folder** (optional): Where to export (default: `docs/powermode/<project-slug>/`)

If no project-slug provided, list available projects from `.powermode/projects/index.json` and ask the user to choose.

## Step 2: Validate Project

1. Read `.powermode/projects/index.json`
2. Find the project by slug
3. If not found, show available projects and ask user to pick

## Step 3: Export

Copy all markdown files from `.powermode/projects/<project-slug>/` to the target folder:

**Include:**
- `project.md`
- `decisions.md` (if exists)
- `issues.md` (if exists)
- `features/<feature-slug>/README.md`
- `features/<feature-slug>/*.md` (all task PRDs)
- `features/<feature-slug>/NOTES.md` (if exists)

**Exclude:**
- `status.json` (internal state, not documentation)
- Any `.json` files

**Preserve structure:**
```
<target-folder>/
├── project.md
├── decisions.md
├── issues.md
└── features/
    ├── <feature-slug>/
    │   ├── README.md
    │   ├── 01-<task>.md
    │   └── NOTES.md
    └── <feature-slug>/
        └── ...
```

## Step 4: Report

Show what was exported:
```
Exported <project-slug> to <target-folder>/
- X feature(s)
- Y task PRD(s)
- Decisions log: [yes/no]
- Issues tracker: [yes/no]
```
