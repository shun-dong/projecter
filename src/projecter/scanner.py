"""Scanner - 扫描项目和笔记

只扫描 README.md 和 .md 文件，不做其他文件操作
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple


class ProjectInfo(NamedTuple):
    """项目信息"""
    name: str
    path: str  # 项目目录路径
    readme_path: str  # README.md 完整路径
    yaml_front: Dict[str, any]  # YAML front-matter 解析结果


class NoteInfo(NamedTuple):
    """笔记信息"""
    name: str  # 文件名（不含 .md）
    path: str  # 完整路径
    yaml_front: Dict[str, any]  # YAML front-matter 解析结果


def parse_yaml_front_matter(content: str) -> tuple:
    """解析 YAML front-matter
    
    Args:
        content: 文件内容
        
    Returns:
        (yaml_dict, remaining_content)
    """
    lines = content.split('\n')
    
    # 检查是否以 --- 开头
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
    
    # 解析 YAML
    yaml_data = {}
    for line in yaml_lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            yaml_data[key] = value
    
    remaining = '\n'.join(lines[end_index + 1:])
    return yaml_data, remaining


def read_file_content(filepath: str) -> str:
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ""


def scan_projects(project_dir: str) -> List[ProjectInfo]:
    """扫描项目目录，找出所有包含 README.md 的非空项目
    
    Args:
        project_dir: 项目根目录
        
    Returns:
        ProjectInfo 列表
    """
    projects = []
    
    if not os.path.exists(project_dir):
        return projects
    
    for entry in sorted(os.listdir(project_dir)):
        subdir_path = os.path.join(project_dir, entry)
        
        # 只处理目录
        if not os.path.isdir(subdir_path):
            continue
        
        # 检查目录内容
        items = os.listdir(subdir_path)
        
        # 必须有 README.md 才认为是项目
        if "README.md" not in items:
            continue
        
        # 忽略隐藏文件和目录（如 .git, .DS_Store）
        visible_items = [i for i in items if not i.startswith('.')]
        items = os.listdir(subdir_path)
        non_readme_items = [i for i in items if i != "README.md"]
        
        if not visible_items:
            # 目录完全为空（或只有隐藏文件），跳过
            continue
            # 空项目，跳过
            continue
        
        # 读取 README.md
        readme_path = os.path.join(subdir_path, "README.md")
        if not os.path.exists(readme_path):
            continue
        
        # 读取并解析 YAML front-matter
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
    """扫描笔记目录，找出所有 .md 文件
    
    Args:
        note_dirs: 笔记目录列表
        
    Returns:
        NoteInfo 列表
    """
    notes = []
    
    for note_dir in note_dirs:
        if not os.path.exists(note_dir):
            continue
        
        for filename in os.listdir(note_dir):
            # 只处理 .md 文件
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(note_dir, filename)
            if not os.path.isfile(filepath):
                continue
            
            # 读取并解析 YAML front-matter
            content = read_file_content(filepath)
            yaml_front, _ = parse_yaml_front_matter(content)
            
            # 文件名去掉 .md
            name = filename[:-3]
            
            notes.append(NoteInfo(
                name=name,
                path=filepath,
                yaml_front=yaml_front
            ))
    
    return notes


def get_project_content(project_info: ProjectInfo) -> str:
    """获取项目 README 的内容（不含 YAML front-matter）"""
    content = read_file_content(project_info.readme_path)
    _, remaining = parse_yaml_front_matter(content)
    return remaining


def get_note_content(note_info: NoteInfo) -> str:
    """获取笔记的内容（不含 YAML front-matter）"""
    content = read_file_content(note_info.path)
    _, remaining = parse_yaml_front_matter(content)
    return remaining
