import os
import re
from merge2 import merge2


def collect(PROJECT_DIR, TARGET_READMES_DIRS):
    # 确保所有目标目录存在
    for dir in TARGET_READMES_DIRS:
        if not os.path.exists(dir):
            os.makedirs(dir)

    def make_absolute_link(proj_path, proj_name, match):
        label, rel_path = match.group(1), match.group(2)
        if (rel_path.endswith(".cn") or rel_path.startswith("http") or rel_path.endswith(".com")  or rel_path.endswith(".me")
            or rel_path.startswith("www") or rel_path.endswith(".org") or rel_path.endswith(".net") or rel_path.endswith(".edu")):
            # 如果是绝对路径或外部链接，直接返回
            return f'[{label}]({rel_path})'
        abs_path = os.path.join(proj_path, rel_path)
        abs_path_norm = os.path.abspath(abs_path).replace("\\", "/")
        return f'[{label}]({abs_path_norm})'

    for project in os.listdir(PROJECT_DIR):
        subdir = os.path.join(PROJECT_DIR, project)
        readme = os.path.join(subdir, "README.md")
        if os.path.isdir(subdir) and os.path.exists(readme):
            with open(readme, "r", encoding='utf-8') as f:
                content = f.read()
            def replacer(match):
                return make_absolute_link(subdir, project, match)
            new_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, content)
            # 优先同步到第一个存在同名文件的目录，否则放到最后一个目录
            target_file = None
            for dir in TARGET_READMES_DIRS:
                candidate = os.path.join(dir, f"!{project}.md")
                if os.path.exists(candidate):
                    target_file = candidate
                    break
            if not target_file:
                target_file = os.path.join(TARGET_READMES_DIRS[-1], f"!{project}.md")
                print(f"创建新项目: {target_file}")

            merged_content = new_content
            conflict = False
            if os.path.exists(target_file):
                with open(target_file, "r", encoding='utf-8') as f:
                    old_content = f.read()
                if old_content != new_content:
                    merged_content, conflict = merge2(old_content, new_content)
            with open(target_file, "w", encoding='utf-8') as f:
                f.write(merged_content)
            if conflict:
                print(f"冲突: {project} -> {target_file} 已自动合并并标记冲突")
            # else:
            #     print(f"同步: {project} -> {target_file}")

    print("正向同步完成。")

if __name__ == "__main__":
    PROJECT_DIR = r"C:\Users\liuSu\Desktop\test\c"
    TARGET_READMES_DIRS = [
        r"C:\Users\liuSu\Desktop\test2",
        r"C:\Users\liuSu\Desktop\test3",
    ]
    collect(PROJECT_DIR, TARGET_READMES_DIRS)
