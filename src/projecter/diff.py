"""Diff - 检测项目和笔记之间的差异

功能：
- 对比项目 README 和笔记内容
- 显示差异，不自动解决
- 帮助用户决定同步方向
"""

import difflib
import os
from typing import List, Optional, Tuple

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter


class DiffResult:
    """差异检测结果"""
    def __init__(self, project_name: str, note_path: Optional[str] = None):
        self.project_name = project_name
        self.note_path = note_path
        self.project_only = False  # 只有项目，没有笔记
        self.note_only = False     # 只有笔记，没有项目
        self.both_modified = False # 双方都有修改
        self.project_newer = False # 项目较新
        self.note_newer = False    # 笔记较新
        self.identical = False     # 内容相同
        self.diff_lines: List[str] = []  # 差异行
        self.error: Optional[str] = None


def compute_diff(project_content: str, note_content: str) -> List[str]:
    """计算两个内容的差异
    
    Returns:
        差异行列表（统一 diff 格式）
    """
    project_lines = project_content.splitlines(keepends=True)
    note_lines = note_content.splitlines(keepends=True)
    
    # 使用 unified diff
    diff = list(difflib.unified_diff(
        note_lines,           # 旧版本
        project_lines,        # 新版本
        fromfile='note',      # 笔记
        tofile='project',     # 项目
        lineterm=''
    ))
    
    return diff


def diff_project_note(
    project_info: ProjectInfo,
    note_info: Optional[NoteInfo]
) -> DiffResult:
    """对比单个项目和笔记
    
    Args:
        project_info: 项目信息
        note_info: 笔记信息（可能为 None）
        
    Returns:
        DiffResult
    """
    result = DiffResult(project_info.name, note_info.path if note_info else None)
    
    # 读取项目 README 内容（不含 YAML）
    project_content_full = read_file_content(project_info.readme_path)
    _, project_body = parse_yaml_front_matter(project_content_full)
    
    # 如果没有笔记
    if note_info is None:
        result.project_only = True
        return result
    
    # 读取笔记内容（不含 YAML）
    note_content_full = read_file_content(note_info.path)
    _, note_body = parse_yaml_front_matter(note_content_full)
    
    # 对比内容
    if project_body.strip() == note_body.strip():
        result.identical = True
        return result
    
    # 计算差异
    result.diff_lines = compute_diff(project_body, note_body)
    
    # 简单判断：看谁的内容更长或根据文件修改时间
    # 注意：这里只是启发式判断，不完全准确
    try:
        project_mtime = os.path.getmtime(project_info.readme_path)
        note_mtime = os.path.getmtime(note_info.path)
        
        if project_mtime > note_mtime:
            result.project_newer = True
        else:
            result.note_newer = True
    except Exception:
        # 如果无法获取时间，默认双方都有修改
        result.both_modified = True
    
    return result


def diff_all(
    projects: List[ProjectInfo],
    notes: List[NoteInfo]
) -> List[DiffResult]:
    """对比所有项目和笔记
    
    Args:
        projects: 项目列表
        notes: 笔记列表
        
    Returns:
        DiffResult 列表
    """
    # 创建笔记映射
    note_map = {}
    for note in notes:
        # 优先使用 YAML 中的 project 字段，其次使用文件名
        key = note.yaml_front.get('project') or note.name
        if key in note_map:
            # 有重复，跳过
            print(f"警告: 笔记 '{key}' 有多个匹配，跳过")
            continue
        note_map[key] = note
    
    results = []
    
    for project in projects:
        note = note_map.get(project.name)
        result = diff_project_note(project, note)
        results.append(result)
    
    return results


def print_diff(result: DiffResult, verbose: bool = False) -> None:
    """打印差异结果
    
    Args:
        result: DiffResult
        verbose: 是否显示详细差异
    """
    name = result.project_name
    
    if result.error:
        print(f"  {name}: 错误 - {result.error}")
        return
    
    if result.project_only:
        print(f"  {name}: 只有项目，无对应笔记")
        print(f"    建议: projecter collect {name}")
        return
    
    if result.note_only:
        print(f"  {name}: 只有笔记，无对应项目（这种情况不应该发生）")
        return
    
    if result.identical:
        print(f"  {name}: ✓ 内容相同")
        return
    
    if result.project_newer:
        print(f"  {name}: 项目较新")
        print(f"    建议: projecter collect {name}  (项目 → 笔记)")
    elif result.note_newer:
        print(f"  {name}: 笔记较新")
        print(f"    建议: projecter distribute {name}  (笔记 → 项目)")
    else:
        print(f"  {name}: 双方都有修改")
        print(f"    建议: 请手动在 Obsidian 中解决后，再选择方向同步")
    
    if verbose and result.diff_lines:
        print(f"\n  差异详情:")
        for line in result.diff_lines[:50]:  # 最多显示 50 行
            print(f"    {line}")
        if len(result.diff_lines) > 50:
            print(f"    ... (还有 {len(result.diff_lines) - 50} 行)")
        print()


def diff(projects: List[ProjectInfo], notes: List[NoteInfo], verbose: bool = False) -> None:
    """显示所有差异
    
    Args:
        projects: 项目列表
        notes: 笔记列表
        verbose: 是否显示详细差异
    """
    print(f"\n检查项目和笔记的差异...")
    print(f"项目数: {len(projects)}")
    print(f"笔记数: {len(notes)}\n")
    
    results = diff_all(projects, notes)
    
    has_diff = False
    for result in results:
        if not result.identical:
            has_diff = True
            print_diff(result, verbose)
    
    if not has_diff:
        print("所有项目与笔记内容相同，无需同步 ✓")
    else:
        print("\n检测到差异，请根据建议手动选择同步方向")
