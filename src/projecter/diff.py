"""Diff - Detect differences between workspace and notes

Functionality:
- Compare workspace README and note content
- Compare under same "view" (compare after conversion)
- Display differences without auto-resolution
"""

import difflib
import os
from typing import List, Optional, Tuple

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter
from .collect import convert_relative_to_absolute
from .distribute import convert_absolute_to_relative, remove_log_block


class DiffResult:
    """Difference detection result"""
    def __init__(self, project_name: str, note_path: Optional[str] = None):
        self.project_name = project_name
        self.note_path = note_path
        self.project_only = False      # Only project, no note
        self.note_only = False         # Only note, no project
        self.identical = False         # Content identical

        # Differences from different perspectives
        self.collect_would_change = False   # collect would change note
        self.distribute_would_change = False # distribute would change project

        self.diff_collect = []         # collect perspective diff
        self.diff_distribute = []      # distribute perspective diff

        self.error: Optional[str] = None


def compute_diff(old_content: str, new_content: str, from_name: str = 'old', to_name: str = 'new') -> List[str]:
    """Compute differences between two contents

    Returns:
        List of diff lines (unified diff format)
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    # Use unified diff
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_name,
        tofile=to_name,
        lineterm=''
    ))

    return diff


def diff_project_note(
    project_info: ProjectInfo,
    note_info: Optional[NoteInfo]
) -> DiffResult:
    """Compare a single project and note

    Args:
        project_info: Project information
        note_info: Note information (may be None)

    Returns:
        DiffResult
    """
    result = DiffResult(project_info.name, note_info.path if note_info else None)

    # Read project README content (without YAML)
    project_content_full = read_file_content(project_info.readme_path)
    _, project_body = parse_yaml_front_matter(project_content_full)

    # If no note
    if note_info is None:
        result.project_only = True
        return result

    # Read note content (without YAML)
    note_content_full = read_file_content(note_info.path)
    _, note_body = parse_yaml_front_matter(note_content_full)

    # === Perspective 1: collect (project→notes) ===
    # Convert project content to note format: relative→absolute paths
    project_as_note = convert_relative_to_absolute(project_body, project_info.path)

    if project_as_note.strip() != note_body.strip():
        result.collect_would_change = True
        result.diff_collect = compute_diff(
            note_body,
            project_as_note,
            from_name='note',
            to_name='project->note'
        )

    # === Perspective 2: distribute (notes→project) ===
    # Convert note content to project format: absolute→relative paths, remove log
    note_as_project = convert_absolute_to_relative(note_body, project_info.path)
    note_as_project = remove_log_block(note_as_project)

    if note_as_project.strip() != project_body.strip():
        result.distribute_would_change = True
        result.diff_distribute = compute_diff(
            project_body,
            note_as_project,
            from_name='project',
            to_name='note->project'
        )

    # If both perspectives are same, content is identical
    if not result.collect_would_change and not result.distribute_would_change:
        result.identical = True

    return result


def diff_all(
    projects: List[ProjectInfo],
    notes: List[NoteInfo]
) -> List[DiffResult]:
    """Compare all projects and notes

    Args:
        projects: List of projects
        notes: List of notes

    Returns:
        List of DiffResult
    """
    # Create note mapping
    note_map = {}
    for note in notes:
        # Prefer YAML project field, then filename
        key = note.yaml_front.get('project') or note.name
        if key in note_map:
            # Duplicate, skip
            print(f"Warning: Note '{key}' has multiple matches, skipping")
            continue
        note_map[key] = note

    results = []

    for project in projects:
        note = note_map.get(project.name)
        result = diff_project_note(project, note)
        results.append(result)

    return results


def print_diff(result: DiffResult, verbose: bool = False) -> None:
    """Print diff result

    Args:
        result: DiffResult
        verbose: Whether to show detailed differences
    """
    name = result.project_name

    if result.error:
        print(f"  {name}: Error - {result.error}")
        return

    if result.project_only:
        print(f"  {name}: Project only, no corresponding note")
        print(f"    Suggestion: projecter collect {name}")
        return

    if result.note_only:
        print(f"  {name}: Note only, no corresponding project")
        return

    if result.identical:
        print(f"  {name}: Content identical")
        return

    # Show differences from different perspectives
    if result.collect_would_change and result.distribute_would_change:
        print(f"  {name}: Differences in both directions")
        print(f"    collect would modify note (project→notes)")
        print(f"    distribute would modify project (notes→project)")
        print(f"    Suggestion: Please check differences and choose direction")
    elif result.collect_would_change:
        print(f"  {name}: collect would modify note")
        print(f"    Suggestion: projecter collect {name}  (project→notes)")
    elif result.distribute_would_change:
        print(f"  {name}: distribute would modify project")
        print(f"    Suggestion: projecter distribute {name}  (notes→project)")

    if verbose:
        if result.collect_would_change and result.diff_collect:
            print(f"\n  collect diff (project→notes):")
            for line in result.diff_collect[:30]:
                print(f"    {line}")
            if len(result.diff_collect) > 30:
                print(f"    ... ({len(result.diff_collect) - 30} more lines)")

        if result.distribute_would_change and result.diff_distribute:
            print(f"\n  distribute diff (notes→project):")
            for line in result.diff_distribute[:30]:
                print(f"    {line}")
            if len(result.diff_distribute) > 30:
                print(f"    ... ({len(result.diff_distribute) - 30} more lines)")
        print()


def diff(projects: List[ProjectInfo], notes: List[NoteInfo], verbose: bool = False) -> None:
    """Display all differences

    Args:
        projects: List of projects
        notes: List of notes
        verbose: Whether to show detailed differences
    """
    print(f"\nChecking differences between workspace and notes...")
    print(f"Projects: {len(projects)}")
    print(f"Notes: {len(notes)}\n")

    results = diff_all(projects, notes)

    has_diff = False
    for result in results:
        if not result.identical:
            has_diff = True
            print_diff(result, verbose)

    if not has_diff:
        print("All projects and notes have identical content, no sync needed")
    else:
        print("\nDifferences detected, please manually choose sync direction based on suggestions")
