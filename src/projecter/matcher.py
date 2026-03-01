"""匹配器 - 负责匹配项目和笔记文件"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from .scanner import ProjectInfo, NoteInfo


@dataclass
class MatchResult:
    """匹配结果"""
    project_name: str
    note_path: Optional[str]
    matched_by: str  # 'yaml', 'filename', 'none'
    confidence: float


def match_project_to_notes(
    projects: List[ProjectInfo], 
    notes: List[NoteInfo]
) -> Dict[str, MatchResult]:
    """将项目与笔记进行匹配
    
    匹配优先级：
    1. YAML front-matter 的 project 字段（精确匹配）
    2. 文件名匹配（去掉 .md）
    
    返回: {project_name: MatchResult}
    """
    results = {}
    
    # 创建笔记查找索引
    yaml_index = {}  # project_name -> note
    filename_index = {}  # filename_stem -> [notes]
    
    for note in notes:
        # 索引 YAML project 字段
        yaml_project = note.yaml_front.get('project')
        if yaml_project:
            if yaml_project in yaml_index:
                # 重复的 project 字段，标记为歧义
                yaml_index[yaml_project] = None  # None 表示歧义
            else:
                yaml_index[yaml_project] = note
        
        # 索引文件名
        stem = Path(note.path).stem
        if stem not in filename_index:
            filename_index[stem] = []
        filename_index[stem].append(note)
    
    # 为每个项目查找匹配
    for project in projects:
        match = _match_single_project(project, yaml_index, filename_index)
        results[project.name] = match
    
    return results


def _match_single_project(
    project: ProjectInfo, 
    yaml_index: Dict[str, Optional[NoteInfo]], 
    filename_index: Dict[str, List[NoteInfo]]
) -> MatchResult:
    """为单个项目查找匹配的笔记"""
    
    # 1. 优先匹配 YAML project 字段
    if project.name in yaml_index:
        note = yaml_index[project.name]
        if note is None:
            # 歧义：多个笔记有相同的 project 字段
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
    
    # 2. 其次匹配文件名
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
            # 多个笔记文件名相同（在不同目录）
            return MatchResult(
                project_name=project.name,
                note_path=None,
                matched_by='filename_ambiguous',
                confidence=0.0
            )
    
    # 无匹配
    return MatchResult(
        project_name=project.name,
        note_path=None,
        matched_by='none',
        confidence=0.0
    )


def find_note_by_path(notes: List[NoteInfo], note_path: str) -> Optional[NoteInfo]:
    """根据路径查找笔记"""
    for note in notes:
        if note.path == note_path:
            return note
    return None


def find_note_for_project(
    project_name: str, 
    note_dirs: List[str]
) -> Optional[NoteInfo]:
    """为单个项目名称查找匹配的笔记
    
    这是一个便利函数，用于 CLI 命令
    
    Args:
        project_name: 项目名称
        note_dirs: 笔记目录列表
        
    Returns:
        匹配的 NoteInfo，或 None
    """
    from .scanner import scan_notes
    
    notes = scan_notes(note_dirs)
    
    # 第一优先级：YAML front-matter 的 `project` 字段
    for note in notes:
        if note.yaml_front.get('project') == project_name:
            return note
    
    # 第二优先级：文件名匹配
    for note in notes:
        if note.name == project_name:
            return note
    
    return None
