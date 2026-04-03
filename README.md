# Projecter 2.0

Simplified project management tool focused on README and notes synchronization.

## Features

- **Simplified Matching**: Priority matching by YAML front-matter `project` field, then by filename
- **Manual Sync Direction**: No longer auto-resolves conflicts, users choose `collect` or `distribute` based on `diff` results
- **Explicit File Tree**: `tree` command generates file tree to stdout, users copy as needed
- **Git Hook Optional**: Leave to users to handle

## Installation

```bash
pip install -e .
```

## Configuration

Interactive setup on first run:

```bash
projecter create my-project
```

Or manually create config file at `~/.config/projecter/config.json`:

```json
{
    "workspace_dir": "/path/to/workspace",
    "notes_dirs": ["/path/to/notes"]
}
```

## CLI Commands

```bash
# Project management in workspace
projecter create <name>              # Create new project
projecter delete <name>              # Delete project
projecter list                       # List all projects
projecter tree <name>                # Display project file tree

# Notes information retrieval
projecter view <name>               # View and display a note

# Sync (manual direction selection)
projecter diff [name] [-v]           # Show diff ([name] optional, -v for verbose)
projecter distribute [--dry-run]     # Notes -> workspace (one-way)

# Configuration
projecter link <project> <note>      # Manually link (optional)
projecter config                     # Manage configuration
```

**Note**: `collect` command (workspace -> notes) is kept in Python but hidden from CLI. You can still use it via `python -m projecter.collect` if needed.

## Workflow Example

```bash
# 1. Create project in workspace
projecter create my-app

# 2. Edit note in Obsidian

# 3. Check differences
projecter diff

# 4. Choose sync direction based on diff
projecter distribute  # If notes are newer
```

## Matching Mechanism

1. **Priority**: YAML front-matter `project` field
2. **Secondary**: Filename (without .md)
3. **Ambiguity**: Print warning, let user resolve manually

## CLI Purpose

The CLI is used to:
- **Manage workspace**: Create, delete, list projects in the workspace directory
- **Fetch notes info**: Read and display notes from the notes directories
- **Sync content**: Distribute notes content to workspace (one-way)
- **Inspect differences**: Compare workspace and notes to decide sync direction

## Project Structure

```
src/projecter/
├── __init__.py
├── __main__.py
├── cli.py          # CLI commands
├── scanner.py      # Workspace and notes scanning
├── matcher.py      # Matching logic
├── collect.py      # Workspace -> notes (hidden from CLI)
├── distribute.py   # Notes -> workspace
└── diff.py         # Diff detection
```

## Differences from Old Version

| Feature | Old | New |
|---------|-----|-----|
| Matching | `!` prefix filename | YAML `project` field priority |
| Sync | `sync` auto bidirectional | `diff` + manual direction selection |
| Conflict | Auto merge | Print message only |
| File Tree | Auto insert to README | `tree` command, user copies |
| Terminology | "project_dir" / "note_dirs" | "workspace_dir" / "notes_dirs" |
| Collect | Exposed in CLI | Hidden (kept in Python) |
| View | Not available | New command to view notes |

## License

MIT
