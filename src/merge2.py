import difflib

def merge2(old_content, new_content):
    '''保留所有的原有内容的增量合并'''
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    sm = difflib.SequenceMatcher(None, old_lines, new_lines)
    merged_lines = []
    conflict = False

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            merged_lines.extend(old_lines[i1:i2])
        elif tag == 'replace':
            conflict = True
            # merged_lines.append("<<<<<<< 新内容")
            # merged_lines.extend(new_lines[j1:j2])
            # merged_lines.append("=======")
            # merged_lines.extend(old_lines[i1:i2])
            # merged_lines.append(">>>>>>> 旧内容")
            merged_lines.extend(old_lines[i1:i2])
            print(f"冲突: 新内容: {new_lines[j1:j2]}","\n",f"旧内容: {old_lines[i1:i2]}")
        elif tag == 'delete':
            conflict = True
            merged_lines.extend(old_lines[i1:i2])
        elif tag == 'insert':
            conflict = True
            merged_lines.extend(new_lines[j1:j2])
    return "\n".join(merged_lines), conflict

if __name__ == "__main__":
    contentA = '''
        我们大概需要以下的分工, 如果有想到其他工作也可以提出来
        - 代码开发组：
            1. 防干扰的实现（Python）'''
    contentB = '''
        我们大概需要以下的分工, 如果有想到其他工作也可以提出来
        - 代码开发组：
            2. 防干扰的实现（Python）'''
    print(merge2(contentA, contentB))
