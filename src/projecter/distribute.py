"""Distribute - Sync notes back to workspace README

Functionality: Notes → Workspace
- Absolute paths → Relative paths
- Remove log blocks
- Do not auto-resolve conflicts
- Only operate on README.md
- **No backup generated**
"""

import os
import re
from typing import Optional

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter


def convert_absolute_to_relative(content: str, project_path: str) -> str:
    """Convert absolute links in content to relative links

    Args:
        content: Note content
        project_path: Project directory path (used to identify absolute paths)

    Returns:
        Converted content
    """
    def replace_link(match):
        label = match.group(1)
        abs_path = match.group(2)

        # Skip external links
        if (abs_path.startswith('http') or
            abs_path.startswith('www.') or
            abs_path.startswith('//')):
            return match.group(0)

        # Normalize paths
        abs_path_norm = abs_path.replace('\\', '/')
        project_norm = project_path.replace('\\', '/')

        # If path is under project directory, convert to relative
        if abs_path_norm.startswith(project_norm):
            rel_path = os.path.relpath(abs_path, project_path).replace('\\', '/')
            return f'[{label}]({rel_path})'

        # Keep other absolute paths unchanged
        return match.group(0)

    # Match [label](path) format
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replace_link, content)


def remove_log_block(content: str) -> str:
    """Remove log blocks

    Log blocks start with # log or ## log
    Continue until next same-level or higher-level heading

    Args:
        content: Content

    Returns:
        Content with log blocks removed
    """
    lines = content.split('\n')
    result = []
    skipping = False
    log_header_level = 0

    for line in lines:
        stripped = line.strip()

        # Detect log heading (# log, ## log, etc.)
        log_match = re.match(r'^(#+)\s*log\b', stripped, re.IGNORECASE)
        if log_match:
            skipping = True
            log_header_level = len(log_match.group(1))
            continue

        if skipping:
            # Detect if reached new same-level or higher-level heading
            header_match = re.match(r'^(#+)\s', stripped)
            if header_match:
                header_level = len(header_match.group(1))
                if header_level <= log_header_level:
                    # New block starts, end skipping
                    skipping = False
                    result.append(line)
            # Otherwise continue skipping
            continue

        result.append(line)

    return '\n'.join(result)


def distribute_note_to_project(
    note_info: NoteInfo,
    project_info: ProjectInfo,
    dry_run: bool = False
) -> bool:
    """Sync note to project README

    Args:
        note_info: Note information
        project_info: Project information
        dry_run: If True, only display operation without executing

    Returns:
        Whether successful
    """
    # Read note content
    note_content = read_file_content(note_info.path)
    yaml_front, body = parse_yaml_front_matter(note_content)

    # Convert paths
    converted_body = convert_absolute_to_relative(body, project_info.path)

    # Remove log blocks
    cleaned_body = remove_log_block(converted_body)

    # Build new content (keep YAML front-matter, ensure project field exists)
    if not yaml_front.get('project'):
        yaml_front['project'] = project_info.name

    new_content = "---\n"
    for key, value in yaml_front.items():
        new_content += f"{key}: {value}\n"
    new_content += "---\n\n"
    new_content += cleaned_body

    # Check existing README
    readme_path = project_info.readme_path
    if os.path.exists(readme_path):
        existing_content = read_file_content(readme_path)

        if existing_content.strip() == new_content.strip():
            print(f"  {project_info.name}: Content identical, no sync needed")
            return True

    if dry_run:
        print(f"  [dry-run] Will sync {note_info.name} → {project_info.name}/README.md")
        return True

    # Write README
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  {note_info.name} → {project_info.name}/README.md")
        return True
    except Exception as e:
        print(f"  {project_info.name}: Write failed - {e}")
        return False


def distribute(notes: list, projects: list, dry_run: bool = False) -> None:
    """Batch distribute notes to projects

    Args:
        notes: List of NoteInfo
        projects: List of ProjectInfo
        dry_run: If True, only display operation without executing
    """
    if not notes:
        print("No notes found to sync")
        return

    if not projects:
        print("No target projects found")
        return

    # Create project name to project mapping
    project_map = {p.name: p for p in projects}

    print(f"\nDistributing notes to projects ({'preview mode' if dry_run else 'execute mode'})...")
    print(f"Notes count: {len(notes)}")
    print(f"Target projects count: {len(projects)}\n")

    success_count = 0
    unmatched_notes = []

    for note in notes:
        # Get project name from YAML or filename
        project_name = note.yaml_front.get('project') or note.name

        if project_name in project_map:
            if distribute_note_to_project(note, project_map[project_name], dry_run):
                success_count += 1
        else:
            unmatched_notes.append(note)

    if unmatched_notes:
        print(f"\nUnmatched notes (no corresponding project found):")
        for note in unmatched_notes:
            print(f"  - {note.name} ({note.path})")

    print(f"\nComplete: {success_count}/{len(notes)} notes synced")
