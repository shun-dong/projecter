#!/usr/bin/env python3
"""Projecter CLI - Manage projects and notes synchronization

Commands:
- create: Create a new project in workspace
- delete: Delete a project from workspace
- list: List all projects in workspace
- tree: Display file tree of a project
- distribute: Sync notes → workspace (one-way)
- diff: Show diff between workspace and notes
- link: Manually link project to note
- view: View and display a note from notes directories
- config: Manage configuration

The CLI is used to manage the workspace and fetch information from the notes side.
"""

import json
import os
import sys
from pathlib import Path

import click

from .scanner import scan_projects, scan_notes, read_file_content
from .matcher import match_project_to_notes
from .collect import collect as collect_module
from .distribute import distribute as distribute_module
from .distribute import distribute
from .diff import diff


# Config file paths
CONFIG_DIR = Path.home() / '.config' / 'projecter'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_config(config):
    """Save configuration to file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config():
    """Get configuration, create interactively if not exists"""
    config = load_config()
    if config is None:
        click.echo("First time setup, configuration required...")
        config = create_config_interactive()
    return config


def create_config_interactive():
    """Interactively create configuration"""
    click.echo("\n=== Projecter Configuration ===")

    workspace_dir = click.prompt("Workspace directory path", type=str)
    while not os.path.isdir(workspace_dir):
        click.echo(f"Directory does not exist: {workspace_dir}")
        workspace_dir = click.prompt("Workspace directory path", type=str)

    notes_dirs = []
    click.echo("\nNotes directories (add multiple, empty line to finish)")
    while True:
        notes_dir = click.prompt("Notes directory path", type=str, default='')
        if not notes_dir:
            break
        if os.path.isdir(notes_dir):
            notes_dirs.append(notes_dir)
            click.echo(f"Added: {notes_dir}")
        else:
            click.echo(f"Directory does not exist: {notes_dir}")

    if not notes_dirs:
        click.echo("Error: At least one notes directory is required")
        sys.exit(1)

    config = {
        'workspace_dir': workspace_dir,
        'notes_dirs': notes_dirs
    }

    save_config(config)
    click.echo(f"\nConfiguration saved to: {CONFIG_FILE}")
    return config


@click.group(
    help="""Projecter - Manage projects and notes synchronization

Projecter manages the relationship between your workspace (project directories)
and your notes. It provides commands to create projects, sync content between
workspace and notes, and inspect differences.

Configuration:
  Config is stored in ~/.config/projecter/config.json
  Run 'projecter config' to set up workspace and notes directories.
"""
)
@click.version_option(version='2.0.0', prog_name='projecter')
def cli():
    """Projecter - Manage projects and notes synchronization"""
    pass


@cli.command(
    short_help="Create a new project in workspace (NAME)",
    help="""Create a new project in workspace

Arguments:
  NAME    Name of the project to create

Creates a new project directory in the configured workspace with a README.md
containing YAML front-matter. The project field in YAML will be set to NAME.
"""
)
@click.argument('name')
def create(name):
    """Create a new project in workspace"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    project_path = os.path.join(workspace_dir, name)

    if os.path.exists(project_path):
        click.echo(f"Error: Project '{name}' already exists")
        sys.exit(1)

    # Create project directory
    os.makedirs(project_path)

    # Create README.md
    readme_path = os.path.join(project_path, 'README.md')
    content = f"""---
project: {name}
tags:
---

# {name}

Project description...
"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    click.echo(f"Created project: {name}")
    click.echo(f"  Path: {project_path}")
    click.echo(f"  README: {readme_path}")


@cli.command(
    short_help="Delete a project from workspace (NAME)",
    help="""Delete a project from workspace

Arguments:
  NAME    Name of the project to delete

Deletes the project directory and all its contents from the workspace.
This operation cannot be undone. A confirmation prompt will be shown.
"""
)
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to delete this project? This cannot be undone!')
def delete(name):
    """Delete a project from workspace"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    project_path = os.path.join(workspace_dir, name)

    if not os.path.exists(project_path):
        click.echo(f"Error: Project '{name}' does not exist")
        sys.exit(1)

    import shutil
    shutil.rmtree(project_path)
    click.echo(f"Deleted project: {name}")


@cli.command(
    short_help="List all projects in workspace",
    help="""List all projects in workspace

Displays all projects found in the workspace directory, along with their
YAML 'project' field values if present.
"""
)
def list():
    """List all projects in workspace"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    projects = scan_projects(workspace_dir)

    if not projects:
        click.echo("No projects found")
        return

    click.echo(f"\nFound {len(projects)} projects:\n")
    click.echo(f"{'Name':<20} {'Project Field'}")
    click.echo("-" * 40)

    for project in projects:
        project_field = project.yaml_front.get('project', '-')
        click.echo(f"{project.name:<20} {project_field}")


@cli.command(
    short_help="Display file tree of a project (NAME)",
    help="""Display file tree of a project

Arguments:
  NAME    Name of the project

Shows a simple file tree of the project directory, with README.md listed first.
"""
)
@click.argument('name')
def tree(name):
    """Display file tree of a project"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    project_path = os.path.join(workspace_dir, name)

    if not os.path.exists(project_path):
        click.echo(f"Error: Project '{name}' does not exist")
        sys.exit(1)

    # Generate file tree
    click.echo(f"\n{name}")
    items = sorted(os.listdir(project_path))

    # Ensure README.md is first
    if 'README.md' in items:
        items.remove('README.md')
        items.insert(0, 'README.md')

    for i, item in enumerate(items):
        item_path = os.path.join(project_path, item)
        is_dir = os.path.isdir(item_path)
        suffix = "/" if is_dir else ""

        prefix = "└── " if i == len(items) - 1 else "├── "
        click.echo(f"{prefix}[{item}{suffix}]({item}{suffix})")

    click.echo("\nFile tree generated")


# collect command is kept in Python but hidden from CLI
# Users can still use: python -m projecter.collect
def _collect(dry_run):
    """Internal collect function (not exposed as CLI command)"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    projects = scan_projects(workspace_dir)
    collect_module(projects, config.get('notes_dirs', config.get('note_dirs', [])), dry_run)


@cli.command(
    short_help="Sync notes -> workspace (--dry-run)",
    help="""Sync notes → workspace (one-way)

Options:
  --dry-run    Preview mode, do not actually execute

Synchronizes content from notes directories to the workspace.
Converts absolute paths to relative paths and removes log blocks.
"""
)
@click.option('--dry-run', is_flag=True, help='Preview mode, do not actually execute')
def distribute(dry_run):
    """Sync notes → workspace (one-way)"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    projects = scan_projects(workspace_dir)
    notes = scan_notes(config.get('notes_dirs', config.get('note_dirs', [])))
    distribute_module(notes, projects, dry_run)


@cli.command(
    name='diff',
    short_help="Show diff between workspace and notes ([NAME] -v)",
    help="""Show diff between workspace and notes

Arguments:
  [PROJECT_NAME]    Optional project name to check (default: check all)

Options:
  -v, --verbose    Show detailed differences

Compares README files in workspace with corresponding notes and shows
the differences. If no project name is specified, checks all projects.
"""
)
@click.argument('project_name', required=False)
@click.option('-v', '--verbose', is_flag=True, help='Show detailed differences')
def diff_cmd(project_name, verbose):
    """Show diff between workspace and notes"""
    config = get_config()
    workspace_dir = config.get('workspace_dir', config.get('project_dir'))
    projects = scan_projects(workspace_dir)
    notes = scan_notes(config.get('notes_dirs', config.get('note_dirs', [])))

    if project_name:
        # Check specific project only
        project = next((p for p in projects if p.name == project_name), None)
        if not project:
            click.echo(f"Error: Project '{project_name}' does not exist")
            sys.exit(1)

        note_map = {n.yaml_front.get('project') or n.name: n for n in notes}
        note = note_map.get(project_name)

        from .diff import diff_project_note, print_diff
        result = diff_project_note(project, note)
        print_diff(result, verbose)
    else:
        # Check all projects
        diff(projects, notes, verbose)


@cli.command(
    short_help="Manually link project to note (PROJECT NOTE)",
    help="""Manually link project to note

Arguments:
  PROJECT    Project name in workspace
  NOTE       Note name in notes directories

Links a project to a note by modifying the YAML front-matter.
Note: This feature is not yet fully implemented. You can manually
edit the note's YAML front-matter to add the 'project' field.
"""
)
@click.argument('project')
@click.argument('note')
def link(project, note):
    """Manually link project to note"""
    click.echo(f"Link feature not yet implemented: {project} <-> {note}")
    click.echo("Tip: You can manually edit the note's YAML front-matter to add the 'project' field")


@cli.command(
    name='view',
    short_help="View and display a note from notes directories (NAME)",
    help="""View and display a note from notes directories

Arguments:
  NAME    Name of the note to view (without .md extension)

Searches for NAME.md in all configured notes directories and displays
its contents. If multiple notes with the same name exist, displays
a warning and shows the first one found.
"""
)
@click.argument('name')
def view_note(name):
    """Read and display a note from notes directories"""
    config = get_config()
    notes_dirs = config.get('notes_dirs', config.get('note_dirs', []))

    # Search for {name}.md in all notes directories
    found = []
    for notes_dir in notes_dirs:
        note_path = os.path.join(notes_dir, f"{name}.md")
        if os.path.exists(note_path):
            found.append(note_path)

    if not found:
        click.echo(f"Error: Note '{name}' not found in any notes directory")
        sys.exit(1)

    if len(found) > 1:
        click.echo(f"Warning: Multiple notes found, displaying first:")
        for path in found:
            click.echo(f"  - {path}")

    # Read and display content
    content = read_file_content(found[0])
    # Handle encoding issues on Windows terminals (GBK codec)
    try:
        click.echo(content)
    except UnicodeEncodeError:
        # Fallback: encode with errors='replace' for incompatible terminals
        sys.stdout.write(content.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))
        sys.stdout.flush()


@cli.command(
    short_help="Manage configuration",
    help="""Manage configuration

Interactive command to view and modify the projecter configuration.
Shows current workspace and notes directories, and allows reconfiguration.
"""
)
def config():
    """Manage configuration"""
    current_config = load_config()

    if current_config:
        click.echo("\nCurrent configuration:")
        workspace = current_config.get('workspace_dir', current_config.get('project_dir', 'Not set'))
        notes = current_config.get('notes_dirs', current_config.get('note_dirs', []))
        click.echo(f"  Workspace directory: {workspace}")
        click.echo(f"  Notes directories: {', '.join(notes) if notes else 'Not set'}")

    if click.confirm("\nReconfigure?"):
        create_config_interactive()


# Entry point
def main():
    cli()


if __name__ == '__main__':
    main()
