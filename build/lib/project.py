import os
import re

def parse_yaml_front(lines):
    if not lines or not lines[0].strip() == '---':
        return [], -1
    yaml_lines = []
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            return yaml_lines, i
        yaml_lines.append(line.rstrip('\n'))
    return [], -1

def has_key_line(yaml_lines, key):
    for l in yaml_lines:
        if re.match(rf'^\s*{key}\s*:', l):
            return True
    return False

def make_front_matter(project_name):
    return f"---\nproject: {project_name}\ntags:\n---\n"

def gen_tree_markdown(subdir_path, project_name):
    """生成项目名+一级子内容（含README本身）的树，带markdown链接"""
    names = sorted(os.listdir(subdir_path))
    if "README.md" not in names:
        names = ["README.md"] + names
    # 排序，同时去重（防"意外"产生双README）
    names = sorted(set(names), key=lambda n: (n != "README.md", n.lower()))

    tree_lines = [f"{project_name}"]
    n = len(names)
    for i, name in enumerate(names):
        fullpath = os.path.join(subdir_path, name)
        is_dir = os.path.isdir(fullpath) if name != "README.md" else False
        suffix = "/" if is_dir else ""
        label = f"{name}{suffix}"
        link = f"[{label}]({label})"
        prefix = "└── " if i == n-1 else "├── "
        tree_lines.append(prefix + link)
    return "\n".join(tree_lines) + "\n"

def remove_tree_block(lines, project_name):
    """
    移除 content (字符串) 里 project 文件树块，返回剩余部分
    - 树块开头特征：'<项目名>\n├── [README.md](README.md)' 或 '└──' 行
    """
    n = len(lines)
    start, end = None, None

    # 识别树开头
    for i in range(n):
        if lines[i].strip() == project_name and i+1 < n and (lines[i+1].lstrip().startswith('├── [') or lines[i+1].lstrip().startswith('└── [')):
            start = i
            # 往后找连续的├──或└──行
            end = start+1
            while end < n and (lines[end].lstrip().startswith('├── [') or lines[end].lstrip().startswith('└── [')):
                end += 1
            # 包括project名那行和树的全部
            return lines[:start] + lines[end:]
    return lines  # 没找到树，原样返回

def project(PROJECT_DIR):
    '''为目录下每个子项目生成或更新 README.md 文件'''
    for entry in sorted(os.listdir(PROJECT_DIR)):
        subdir_path = os.path.join(PROJECT_DIR, entry)
        if os.path.isdir(subdir_path):
            items = os.listdir(subdir_path)
            non_readme_items = [i for i in items if i != "README.md"]
            if not non_readme_items:
                print(f"*** 空项目: {entry}，已跳过 ***")
                continue

            readme_path = os.path.join(subdir_path, "README.md")
            front = make_front_matter(entry)
            tree_block = gen_tree_markdown(subdir_path, entry)

            if not os.path.exists(readme_path):
                # 先生成 README 文件
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(front)
                print(f"新建: {readme_path}")
                continue

            with open(readme_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 移除已有树块
                lines = remove_tree_block(lines, entry)
            yaml_lines, yaml_endline = parse_yaml_front(lines)
            need_fix_front = False
            if not yaml_lines or not has_key_line(yaml_lines, 'project') or not has_key_line(yaml_lines, 'tags'):
                need_fix_front = True
                print(f"修复front-matter: {readme_path}")

            content_after = "".join(lines[yaml_endline+1:]) if yaml_endline >= 0 else "".join(lines)

            result_lines = []
            if need_fix_front:
                result_lines.append(front)
                result_lines.append('\n')
                result_lines.append(content_after.lstrip('\n'))
            else:
                result_lines.extend(lines)
            if tree_block:
                if not need_fix_front and yaml_endline >= 0:
                    out_before = lines[:yaml_endline+1]
                    out_after = lines[yaml_endline+1:]
                    while out_after and out_after[0].strip() == '':
                        out_after = out_after[1:]
                    result_lines = out_before + ["\n" + tree_block + "\n"] + out_after
                elif need_fix_front:
                    result_lines.insert(2, "\n" + tree_block + "\n")
                else:
                    result_lines.insert(0, "\n" + tree_block + "\n")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.writelines(result_lines)
            # print(f"更新: {readme_path}")

    print("处理完成。")

if __name__ == "__main__":
    PROJECT_DIR = r"C:\Users\liuSu\desktop\test"
    project(PROJECT_DIR)
    
