"""Matcher - Responsible for matching projects and note files"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from .scanner import ProjectInfo, NoteInfo


@dataclass
class MatchResult:
    """Match result"""
    project_name: str
    note_path: Optional[str]
    matched_by: str  # 'yaml', 'filename', 'none'
    confidence: float


def match_project_to_notes(
    projects: List[ProjectInfo],
    notes: List[NoteInfo]
) -> Dict[str, MatchResult]:
    """Match projects to notes

    Matching priority:
    1. YAML front-matter project field (exact match)
    2. Filename match (without .md)

    Returns: {project_name: MatchResult}
    """
    results = {}

    # Create note lookup indexes
    yaml_index = {}  # project_name -> note
    filename_index = {}  # filename_stem -> [notes]

    for note in notes:
        # Index YAML project field
        yaml_project = note.yaml_front.get('project')
        if yaml_project:
            if yaml_project in yaml_index:
                # Duplicate project field, mark as ambiguous
                yaml_index[yaml_project] = None  # None means ambiguous
            else:
                yaml_index[yaml_project] = note

        # Index filename
        stem = Path(note.path).stem
        if stem not in filename_index:
            filename_index[stem] = []
        filename_index[stem].append(note)

    # Find matches for each project
    for project in projects:
        match = _match_single_project(project, yaml_index, filename_index)
        results[project.name] = match

    return results


def _match_single_project(
    project: ProjectInfo,
    yaml_index: Dict[str, Optional[NoteInfo]],
    filename_index: Dict[str, List[NoteInfo]]
) -> MatchResult:
    """Find matching note for a single project"""

    # 1. Priority: match YAML project field
    if project.name in yaml_index:
        note = yaml_index[project.name]
        if note is None:
            # Ambiguous: multiple notes have same project field
            return MatchResult(
                project_name=project.name,
                note_path=None,
                matched_by='yaml_ambiguous',
                confidence=0.0
            )
        return MatchResult(
            project_name=project.name,
            note_path=note.path,
            matched_by='yaml',
            confidence=1.0
        )

    # 2. Secondary: match filename
    if project.name in filename_index:
        notes = filename_index[project.name]
        if len(notes) == 1:
            return MatchResult(
                project_name=project.name,
                note_path=notes[0].path,
                matched_by='filename',
                confidence=0.8
            )
        else:
            # Multiple notes with same filename (in different directories)
            return MatchResult(
                project_name=project.name,
                note_path=None,
                matched_by='filename_ambiguous',
                confidence=0.0
            )

    # No match
    return MatchResult(
        project_name=project.name,
        note_path=None,
        matched_by='none',
        confidence=0.0
    )


def find_note_by_path(notes: List[NoteInfo], note_path: str) -> Optional[NoteInfo]:
    """Find note by path"""
    for note in notes:
        if note.path == note_path:
            return note
    return None


def find_note_for_project(
    project_name: str,
    note_dirs: List[str]
) -> Optional[NoteInfo]:
    """Find matching note for a single project name

    This is a convenience function for CLI commands

    Args:
        project_name: Project name
        note_dirs: List of notes directories

    Returns:
        Matching NoteInfo, or None
    """
    from .scanner import scan_notes

    notes = scan_notes(note_dirs)

    # First priority: YAML front-matter `project` field
    for note in notes:
        if note.yaml_front.get('project') == project_name:
            return note

    # Second priority: filename match
    for note in notes:
        if note.name == project_name:
            return note

    return None
