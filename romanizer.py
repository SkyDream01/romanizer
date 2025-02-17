import os
import re
import sys
import json
from pypinyin import lazy_pinyin
import jaconv
import pykakasi

# 初始化 pykakasi（用于日文转换）
kks = pykakasi.kakasi()

def apply_custom_dict(text, custom_dict):
    """
    对文本进行自定义字典整体替换：
    若文本中包含字典中的键，则将其替换为对应的值。
    """
    for key, value in custom_dict.items():
        if key in text:
            print(f"[自定义字典] 替换: '{key}' -> '{value}'")
            text = text.replace(key, value)
    return text

def hira_to_romaji(text):
    """使用 pykakasi 将平假名转换为罗马字"""
    result = []
    for item in kks.convert(text):
        result.append(item['hepburn'])
    return "".join(result)

def cjk_to_latin(text, chinese_mode="chinese"):
    """
    转换中日字符为罗马字母，并支持汉字转换模式的选择：
      - chinese_mode="chinese"：使用 pypinyin 转换为中文拼音（默认）
      - chinese_mode="japanese"：使用 pykakasi 按日语规则转换汉字
      
    对于日语重复号「々」，将重复前一个转换结果。
    
    此函数假设自定义字典替换已在调用前进行（因此不会再次传入 custom_dict）。
    """
    result = []
    for char in text:
        # 处理日语重复号「々」
        if char == "々":
            if result:
                repeated = result[-1]
                print(f"[字符转换] 日语重复号 '々' -> 重复前一字符 '{repeated}'")
                result.append(repeated)
            else:
                print("[字符转换] 日语重复号 '々' 无前导字符，原样保留")
                result.append(char)
            continue

        # 处理日文字符（平假名和片假名）
        if '\u3040' <= char <= '\u30ff':
            # 先将片假名转换为平假名
            kana = jaconv.kata2hira(char)
            romaji = hira_to_romaji(kana)
            print(f"[字符转换] 日文 '{char}' -> {romaji}")
            result.append(romaji)
        # 处理汉字（中文或日文汉字）
        elif '\u4e00' <= char <= '\u9fff':
            if chinese_mode == "chinese":
                pinyin = "".join(lazy_pinyin(char))
                print(f"[字符转换] 中文 '{char}' -> {pinyin}")
                result.append(pinyin)
            elif chinese_mode == "japanese":
                converted_list = kks.convert(char)
                romaji = "".join([item['hepburn'] for item in converted_list])
                print(f"[字符转换] 汉字（按日语转换）'{char}' -> {romaji}")
                result.append(romaji)
            else:
                pinyin = "".join(lazy_pinyin(char))
                print(f"[字符转换] 中文 '{char}' -> {pinyin}")
                result.append(pinyin)
        else:
            # 其他字符原样保留（包括特殊字符）
            result.append(char)
    return "".join(result)

def rename_files_in_directory(directory, chinese_mode="chinese", custom_dict=None):
    """批量重命名目录中的文件，并显示详细过程"""
    total = 0
    success = 0
    failures = []
    
    print(f"\n{'='*30}\n开始处理目录: {directory}\n{'='*30}")
    
    for filename in os.listdir(directory):
        total += 1
        old_path = os.path.join(directory, filename)
        
        if not os.path.isfile(old_path):
            print(f"[跳过] 非文件对象: {filename}")
            continue

        print(f"\n▶ 正在处理文件 ({total}): {filename}")
        name, ext = os.path.splitext(filename)
        print(f"  解析结果: 主名称 = {name} | 扩展名 = {ext}")
        
        # 如果提供了自定义字典，则先对整个文件名进行替换
        if custom_dict:
            original_name = name
            name = apply_custom_dict(name, custom_dict)
            if original_name != name:
                print(f"  [自定义字典] 文件名替换后: {original_name} -> {name}")
        
        # 执行中日文字符转换
        print("  开始转换中日文字符:")
        converted = cjk_to_latin(name, chinese_mode)
        print(f"  转换结果: {converted}")
        
        # 特殊字符保留，直接使用转换结果作为新文件名
        new_name = converted
        print(f"  新文件名（保留特殊字符）: {new_name}")
        
        new_path = os.path.join(directory, new_name + ext)
        
        if new_path == old_path:
            print("  无需重命名：新旧名称相同")
            success += 1
            continue
            
        try:
            os.rename(old_path, new_path)
            print(f"✅ 重命名成功: {filename} -> {new_name+ext}")
            success += 1
        except Exception as e:
            print(f"❌ 重命名失败: {str(e)}")
            failures.append(filename)
    
    # 生成统计报告
    print(f"\n{'='*30}\n处理完成")
    print(f"总计文件: {total}")
    print(f"成功处理: {success}")
    print(f"失败处理: {len(failures)}")
    if failures:
        print("失败列表:")
        for f in failures:
            print(f"  - {f}")

if __name__ == "__main__":
    # 用法说明：
    #   python romanizer.py <目标目录> [选项]
    #
    # 可选参数：
    #   -cn 或 chinese：使用中文拼音转换（默认）
    #   -jp 或 japanese：使用日语规则转换汉字
    #   -d 或 --dict 后接字典文件路径：指定自定义字典（JSON 格式）
    #
    # 示例：
    #   python romanizer.py ./我的文件夹 -cn -d custom_dict.json
    #   python romanizer.py ./我的文件夹 -jp --dict custom_dict.json

    if len(sys.argv) < 2:
        print("使用方法: python romanizer.py <目标目录> [选项]")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    mode = "chinese"  # 默认模式
    custom_dict = None

    # 解析后续命令行参数
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("-cn", "chinese"):
            mode = "chinese"
        elif arg in ("-jp", "japanese"):
            mode = "japanese"
        elif arg in ("-d", "--dict"):
            if i + 1 < len(sys.argv):
                dict_file = sys.argv[i+1]
                try:
                    with open(dict_file, 'r', encoding='utf-8') as f:
                        custom_dict = json.load(f)
                    print(f"已加载自定义字典: {dict_file}")
                except Exception as e:
                    print(f"加载字典文件失败: {e}")
                    sys.exit(1)
                i += 1  # 跳过字典文件路径参数
            else:
                print("缺少字典文件路径参数")
                sys.exit(1)
        else:
            print(f"未知参数: {arg}")
            sys.exit(1)
        i += 1

    if not os.path.isdir(target_dir):
        print(f"错误：指定的路径不是目录 {target_dir}")
        sys.exit(1)
    
    print(f"【转换模式】汉字将按 [{mode}] 模式转换")
    rename_files_in_directory(target_dir, chinese_mode=mode, custom_dict=custom_dict)
