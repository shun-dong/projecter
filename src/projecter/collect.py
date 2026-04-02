"""Collect - Sync project README to notes

Functionality: Project → Notes
- Relative paths → Absolute paths
- Do not auto-resolve conflicts
- Only operate on .md files
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter


def convert_relative_to_absolute(content: str, project_path: str) -> str:
    """Convert relative links in content to absolute links

    Args:
        content: README content
        project_path: Project directory path

    Returns:
        Converted content
    """
    def replace_link(match):
        label = match.group(1)
        rel_path = match.group(2)

        # Skip external links and absolute paths
        if (rel_path.startswith('http') or
            rel_path.startswith('/') or
            rel_path.startswith('\\') or
            rel_path.endswith('.com') or
            rel_path.endswith('.cn') or
            rel_path.endswith('.org')):
            return match.group(0)

        # Convert to absolute path
        abs_path = os.path.abspath(os.path.join(project_path, rel_path))
        abs_path = abs_path.replace('\\', '/')

        return f'[{label}]({abs_path})'

    # Match [label](path) format
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replace_link, content)


def collect_project_to_note(
    project_info: ProjectInfo,
    note_dirs: list,
    dry_run: bool = False
) -> bool:
    """Sync project README to note

    Args:
        project_info: Project information
        note_dirs: List of notes directories
        dry_run: If True, only display operation without executing

    Returns:
        Whether successful
    """
    # Read project README
    project_content = read_file_content(project_info.readme_path)
    yaml_front, body = parse_yaml_front_matter(project_content)

    # Convert paths
    converted_body = convert_relative_to_absolute(body, project_info.path)

    # Build new content (keep YAML front-matter, ensure project field exists)
    if not yaml_front.get('project'):
        yaml_front['project'] = project_info.name

    new_content = "---\n"
    for key, value in yaml_front.items():
        new_content += f"{key}: {value}\n"
    new_content += "---\n\n"
    new_content += converted_body

    # Determine target note path
    # Prefer first notes directory
    target_dir = note_dirs[0] if note_dirs else None
    if not target_dir or not os.path.exists(target_dir):
        print(f"Error: Notes directory does not exist: {target_dir}")
        return False

    # Note filename uses project name + .md (no longer using ! prefix)
    note_filename = f"{project_info.name}.md"
    note_path = os.path.join(target_dir, note_filename)

    # Check if note already exists
    if os.path.exists(note_path):
        # Read existing note
        existing_content = read_file_content(note_path)

        if existing_content.strip() == new_content.strip():
            print(f"  {project_info.name}: Content identical, no sync needed")
            return True

    if dry_run:
        print(f"  [dry-run] Will sync {project_info.name} → {note_path}")
        return True
    if os.path.exists(note_path):
        # Read existing note
        existing_content = read_file_content(note_path)

        if existing_content.strip() == new_content.strip():
            print(f"  {project_info.name}: Content identical, no sync needed")
            return True

        if not dry_run:
            # Backup existing note
            backup_path = note_path + '.backup'
            shutil.copy2(note_path, backup_path)
            print(f"  {project_info.name}: Backed up existing note to {backup_path}")

    if dry_run:
        print(f"  [dry-run] Will sync {project_info.name} → {note_path}")
        return True

    # Write note
    try:
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  {project_info.name} → {note_path}")
        return True
    except Exception as e:
        print(f"  {project_info.name}: Write failed - {e}")
        return False


def collect(projects: list, note_dirs: list, dry_run: bool = False) -> None:
    """Batch collect projects to notes

    Args:
        projects: List of ProjectInfo
        note_dirs: List of notes directories
        dry_run: If True, only display operation without executing
    """
    if not projects:
        print("No projects found to sync")
        return

    if not note_dirs:
        print("Error: No notes directories configured")
        return

    print(f"\nCollecting projects to notes ({'preview mode' if dry_run else 'execute mode'})...")
    print(f"Projects: {len(projects)}")
    print(f"Target notes directories: {', '.join(note_dirs)}\n")

    success_count = 0
    for project in projects:
        if collect_project_to_note(project, note_dirs, dry_run):
            success_count += 1

    print(f"\nComplete: {success_count}/{len(projects)} projects synced")
