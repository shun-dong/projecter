"""Scanner - Scan projects and notes

Only scans README.md and .md files, no other file operations.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple


class ProjectInfo(NamedTuple):
    """Project information"""
    name: str
    path: str  # Project directory path
    readme_path: str  # Full path to README.md
    yaml_front: Dict[str, any]  # Parsed YAML front-matter


class NoteInfo(NamedTuple):
    """Note information"""
    name: str  # Filename (without .md)
    path: str  # Full path
    yaml_front: Dict[str, any]  # Parsed YAML front-matter


def parse_yaml_front_matter(content: str) -> tuple:
    """Parse YAML front-matter

    Args:
        content: File content

    Returns:
        (yaml_dict, remaining_content)
    """
    lines = content.split('\n')

    # Check if starts with ---
    if not lines or lines[0].strip() != '---':
        return {}, content

    yaml_lines = []
    end_index = -1

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_index = i
            break
        yaml_lines.append(line)

    if end_index == -1:
        return {}, content
    
    # Parse YAML
    yaml_data = {}
    for line in yaml_lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Strip quotes from string values
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            yaml_data[key] = value
    
    remaining = '\n'.join(lines[end_index + 1:])
    return yaml_data, remaining
    yaml_data = {}
    for line in yaml_lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # 去除字符串值的引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            yaml_data[key] = value
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            yaml_data[key] = value
    
    remaining = '\n'.join(lines[end_index + 1:])
    return yaml_data, remaining


def read_file_content(filepath: str) -> str:
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ""


def scan_projects(project_dir: str) -> List[ProjectInfo]:
    """Scan project directory for non-empty projects containing README.md

    Args:
        project_dir: Project root directory

    Returns:
        List of ProjectInfo
    """
    projects = []
    
    if not os.path.exists(project_dir):
        return projects
    
    for entry in sorted(os.listdir(project_dir)):
        subdir_path = os.path.join(project_dir, entry)
        
        # Only process directories
        if not os.path.isdir(subdir_path):
            continue

        # Check directory contents
        items = os.listdir(subdir_path)

        # Must have README.md to be considered a project
        if "README.md" not in items:
            continue

        # Ignore hidden files and directories (e.g., .git, .DS_Store)
        visible_items = [i for i in items if not i.startswith('.')]
        items = os.listdir(subdir_path)
        non_readme_items = [i for i in items if i != "README.md"]

        if not visible_items:
            # Directory completely empty (or only hidden files), skip
            continue
            # Empty project, skip
            continue

        # Read README.md
        readme_path = os.path.join(subdir_path, "README.md")
        if not os.path.exists(readme_path):
            continue

        # Read and parse YAML front-matter
        content = read_file_content(readme_path)
        yaml_front, _ = parse_yaml_front_matter(content)
        
        projects.append(ProjectInfo(
            name=entry,
            path=subdir_path,
            readme_path=readme_path,
            yaml_front=yaml_front
        ))
    
    return projects


def scan_notes(note_dirs: List[str]) -> List[NoteInfo]:
    """Scan notes directories for all .md files

    Args:
        note_dirs: List of notes directories

    Returns:
        List of NoteInfo
    """
    notes = []
    
    for note_dir in note_dirs:
        if not os.path.exists(note_dir):
            continue
        
        for filename in os.listdir(note_dir):
            # Only process .md files
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(note_dir, filename)
            if not os.path.isfile(filepath):
                continue

            # Read and parse YAML front-matter
            content = read_file_content(filepath)
            yaml_front, _ = parse_yaml_front_matter(content)

            # Remove .md from filename
            name = filename[:-3]
            
            notes.append(NoteInfo(
                name=name,
                path=filepath,
                yaml_front=yaml_front
            ))
    
    return notes


def get_project_content(project_info: ProjectInfo) -> str:
    """Get project README content (without YAML front-matter)"""
    content = read_file_content(project_info.readme_path)
    _, remaining = parse_yaml_front_matter(content)
    return remaining


def get_note_content(note_info: NoteInfo) -> str:
    """Get note content (without YAML front-matter)"""
    content = read_file_content(note_info.path)
    _, remaining = parse_yaml_front_matter(content)
    return remaining
