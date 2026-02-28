import os
import re

encodings = ['utf-8', 'gbk', 'gb18030', 'big5', 'ansi', 'gb2312']  # 常见编码列表

# 路径设置
monitems_path = r"C:\Users\fengl\Desktop\爆率文档\MonItems"
call_folder_path = r"C:\Users\fengl\Desktop\爆率文档\call"

# 第一步的正则：匹配复杂格式
pattern_step1 = re.compile(r"#Call\t\[\\爆率文本\\(.*?\.txt)\]\t@.*?(?=\s|$)")
# 第二步的正则：匹配纯文件名
pattern_step2 = re.compile(r"^(.+?\.txt)$", re.MULTILINE)

# 第一步：执行现有代码的逻辑
print("=== 第一步：替换复杂格式为纯文件名 ===")
for filename in os.listdir(monitems_path):
    if filename.endswith(".txt"):
        filepath = os.path.join(monitems_path, filename)
        
        # 尝试不同编码读取
        content = None
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content:
            # 第一步替换
            new_content = pattern_step1.sub(r"\1", content)
            
            # 写入文件（第一步结果）
            with open(filepath, 'w', encoding='ANSI') as f:
                f.write(new_content)
        else:
            print(f"无法解码文件: {filename}")

print("第一步完成！")

# 第二步：执行文件内容合并
print("\n=== 第二步：将纯文件名替换为call文件夹内容 ===")
for filename in os.listdir(monitems_path):
    if filename.endswith(".txt"):
        filepath = os.path.join(monitems_path, filename)
        
        # 读取第一步处理后的文件
        content = None
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content:
            # 分割内容为行
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                # 检查是否是纯文件名引用
                match = pattern_step2.match(line.strip())
                if match:
                    call_filename = match.group(1)
                    call_filepath = os.path.join(call_folder_path, call_filename)
                    
                    # 检查call文件夹中是否存在该文件
                    if os.path.exists(call_filepath):
                        # 读取call文件夹中的文件内容
                        call_content = None
                        for enc in encodings:
                            try:
                                with open(call_filepath, 'r', encoding=enc) as f:
                                    call_content = f.read()
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if call_content:
                            # 将call文件内容添加到新内容中
                            new_lines.append(call_content)
                        else:
                            print(f"无法读取call文件: {call_filename}")
                            new_lines.append(line)  # 保留原行
                    else:
                        print(f"call文件不存在: {call_filename}")
                        new_lines.append(line)  # 保留原行
                else:
                    new_lines.append(line)  # 非引用行，直接保留
            
            # 重新组合内容
            new_content = '\n'.join(new_lines)
            
            # 写入最终文件
            with open(filepath, 'w', encoding='ANSI') as f:
                f.write(new_content)
        else:
            print(f"无法解码文件: {filename}")

print("第二步完成！")
print("\n批量处理完成！")