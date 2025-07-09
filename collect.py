import os
import re
import shutil

def collect(PROJECT_DIR,TARGET_READMES_DIR ):
    if not os.path.exists(TARGET_READMES_DIR):
        os.makedirs(TARGET_READMES_DIR)

    def make_absolute_link(proj_path, proj_name, match):
        # 获取原始markdown链接内容
        label, rel_path = match.group(1), match.group(2)
        abs_path = os.path.join(proj_path, rel_path)
        abs_path_norm = os.path.abspath(abs_path).replace("\\", "/")
        # 替换为绝对路径
        return f'[{label}]({abs_path_norm})'

    for project in os.listdir(PROJECT_DIR):
        subdir = os.path.join(PROJECT_DIR, project)
        readme = os.path.join(subdir, "README.md")
        if os.path.isdir(subdir) and os.path.exists(readme):
            with open(readme, "r", encoding='utf-8') as f:
                content = f.read()
            # 替换tree部分的相对链接为绝对链接
            # 匹配 tree 区块的所有 markdown 链接
            def replacer(match):
                return make_absolute_link(subdir, project, match)
            new_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, content)
            # 保存到目标目录
            target_file = os.path.join(TARGET_READMES_DIR, f"{project}.md")
            with open(target_file, "w", encoding='utf-8') as f:
                f.write(new_content)
            print(f"同步: {project} -> {target_file}")

    print("正向同步完成。")

if __name__ == "__main__":
    # 你自己的项目主目录（包含各项目子文件夹）
    PROJECT_DIR = r"C:\Users\liuSu\Desktop\test"   # 替换为你的实际路径
    # 要同步到的目录
    TARGET_READMES_DIR = r"C:\Users\liuSu\Desktop\test2"  # 替换为你的实际路径
    collect(PROJECT_DIR, TARGET_READMES_DIR)
