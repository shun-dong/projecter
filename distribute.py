import os
import re
def distribute(PROJECT_DIR, TARGET_READMES_DIR):
    def make_relative_link(project_abspath, match):
        label, abs_path = match.group(1), match.group(2)
        # 将绝对路径转为相对路径
        # 只针对属于本项目目录下的文件
        abs_path_norm = abs_path.replace("\\", "/")
        proj_path_norm = project_abspath.replace("\\", "/")
        if abs_path_norm.startswith(proj_path_norm):
            rel_path = os.path.relpath(abs_path_norm, proj_path_norm).replace("\\", "/")
        else:
            # 不属于本项目内的，不处理
            rel_path = abs_path
        return f'[{label}]({rel_path})'

    for fname in os.listdir(TARGET_READMES_DIR):
        if fname.endswith(".md") and fname.startswith("!"):
            project = os.path.splitext(fname)[0][1:]  # 去掉前缀 '!'
            src_file = os.path.join(TARGET_READMES_DIR, fname)
            dst_readme = os.path.join(PROJECT_DIR, project, 'README.md')
            # 仅同步到已存在的本地项目目录
            if os.path.isdir(os.path.join(PROJECT_DIR, project)):
                with open(src_file, "r", encoding='utf-8') as f:
                    content = f.read()
                # 替换tree区块中的绝对路径为相对路径
                abs_project_path = os.path.abspath(os.path.join(PROJECT_DIR, project))
                def replacer(match):
                    return make_relative_link(abs_project_path, match)
                new_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, content)
                with open(dst_readme, "w", encoding='utf-8') as f:
                    f.write(new_content)
                # print(f"同步: {src_file} -> {dst_readme}")
            else:
                print(f"跳过: {project} 未实例化")

    print("反向同步完成。")

if __name__ == "__main__":
    # 你自己的项目主目录（包含各项目子文件夹）
    PROJECT_DIR = r"C:\Users\liuSu\Projects"   # 替换为你的实际路径
    # 要同步到的目录
    TARGET_READMES_DIR = r"C:\Users\liuSu\iCloudDrive\iCloud~md~obsidian\Note\Public"  # 替换为你的实际路径
    distribute(PROJECT_DIR, TARGET_READMES_DIR)