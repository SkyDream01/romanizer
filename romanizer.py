#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
romanizer.py
------------
一个功能强大的批量文件名转换工具。

主要功能:
1.  将包含中文或日文的文件名转换为罗马音/拼音。
    -   中文 -> Hanyu Pinyin (汉语拼音)
    -   日文 -> Hepburn Romanization (平文式罗马字)
2.  支持多种命名风格：驼峰式 (CamelCase)、全小写 (lowercase)、全大写 (UPPERCASE)。
3.  可通过自定义字典实现特定词汇的精确替换。
4.  自动处理文件名中的非法字符，确保跨平台兼容性 (Windows, macOS, Linux)。
5.  自动解决重命名冲突。
6.  提供“预览模式” (dry-run)，在不修改文件系统的情况下预覽重命名结果。
"""

# ========== 核心模块导入 ==========
import argparse
import re
import sys
import unicodedata
from pathlib import Path  # 使用面向对象的 pathlib 模块处理文件路径，代码更现代、更健壮。
from typing import Dict, List, Optional

# ========== 第三方库导入 ==========
import pykakasi
from pypinyin import Style, lazy_pinyin

# ========== 工具函数 ==========

def format_romaji(segments: List[str], style: str = "camel", sep: str = "") -> str:
    """
    将罗马音/拼音片段列表格式化为指定风格的字符串。

    Args:
        segments (List[str]): 罗马音或拼音的字符串片段列表，例如 ['tou', 'kyou']。
        style (str): 目标命名风格。可选值为 "camel", "lower", "upper"。
        sep (str): 在 "lower" 或 "upper" 风格中使用的分隔符，例如 "_" 或 "-"。

    Returns:
        str: 格式化后的最终字符串。
    """
    # 过滤掉由转换库可能产生的空字符串片段
    parts = [s for s in segments if s]
    if not parts:
        return ""

    if style == "camel":
        # 驼峰风格：每个片段首字母大写，其余小写，然后拼接。
        return "".join(p[0].upper() + p[1:].lower() for p in parts)
    elif style == "upper":
        # 大写风格：所有片段转为大写，用分隔符连接。
        return sep.join(p.upper() for p in parts)
    else:  # 默认为 "lower"
        # 小写风格：所有片段转为小写，用分隔符连接。
        return sep.join(p.lower() for p in parts)


def safe_filename(name: str, replacement: str = '-') -> str:
    """
    净化文件名字符串，移除或替换在主流操作系统中非法的字符。

    此函数执行以下操作来确保文件名安全：
    1.  Unicode 归一化 (NFKC)，将全角字符转为半角。
    2.  移除或替换操作系统禁止的字符 (如 < > : " / \ | ? *) 和所有控制字符。
    3.  处理 Windows 平台下的保留设备名 (如 CON, PRN)。
    4.  移除文件名开头和结尾的无效字符 (如空格、点)。
    5.  合并连续的替换字符为一个。

    Args:
        name (str): 原始文件名（不含扩展名部分）。
        replacement (str): 用于替换非法字符的字符串。

    Returns:
        str: 净化后的安全文件名。如果净化后为空，则返回 "untitled"。
    """
    # 步骤 1: Unicode 归一化，以处理兼容性字符（如全角符号）。
    name = unicodedata.normalize("NFKC", name)

    # 步骤 2: 移除或替换非法字符。预编译正则表达式以提高重复使用时的性能。
    # 该正则匹配 < > : " / \ | ? * 以及 ASCII 控制字符 (0x00-0x1F)。
    illegal_chars_re = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    name = illegal_chars_re.sub(replacement, name)

    # 步骤 3: 规避 Windows 保留设备名 (例如 'CON.txt' 是无效的)。
    # 注意：仅当文件名（不含扩展名）完全匹配时才处理，避免误伤（如 'conan.txt'）。
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    name_part, ext_part = Path(name).stem, Path(name).suffix
    if name_part.upper() in reserved_names:  # Windows 保留名不区分大小写
        name_part += "_"
        name = name_part + ext_part

    # 步骤 4: Windows 不允许文件名以点或空格开头/结尾。
    strip_chars = ' .' + replacement
    name = name.strip(strip_chars)

    # 步骤 5: 将多个连续的替换符压缩成一个，使文件名更美观。
    if replacement:
        name = re.sub(f'{re.escape(replacement)}+', replacement, name)

    # 最终保障：如果文件名在处理后变为空，则提供一个默认名称。
    return name or "untitled"


def ensure_unique(path: Path) -> Path:
    """
    检查给定路径是否存在，如果存在，则返回一个带数字后缀的唯一路径。

    例如，如果 `image.jpg` 已存在，此函数将依次尝试 `image-1.jpg`,
    `image-2.jpg`, 直到找到一个不存在的路径。

    Args:
        path (Path): 原始目标路径。

    Returns:
        Path: 一个保证在文件系统中唯一的路径对象。
    """
    if not path.exists():
        return path
    
    parent, stem, suffix = path.parent, path.stem, path.suffix
    n = 1
    while True:
        new_path = parent / f"{stem}-{n}{suffix}"
        if not new_path.exists():
            return new_path
        n += 1


def apply_custom_dict(text: str, custom_dict: Dict[str, str], verbose: bool = False) -> str:
    """
    根据自定义字典替换文本中的内容。

    为确保正确替换（例如 "Tokyo Tower" 优先于 "Tokyo"），
    此函数会优先匹配字典中最长的键。

    Args:
        text (str): 待处理的原始文本。
        custom_dict (Dict[str, str]): 包含替换规则的字典。
        verbose (bool): 是否打印替换日志。

    Returns:
        str: 替换后的文本。
    """
    # 按字典键的长度降序排序。这是实现“长词优先”匹配策略的关键。
    sorted_items = sorted(custom_dict.items(), key=lambda kv: len(kv[0]), reverse=True)
    
    for key, value in sorted_items:
        if key in text:
            if verbose:
                print(f"[字典] 命中规则: '{key}' -> '{value}'")
            text = text.replace(key, value)
    return text


# ========== 核心转换逻辑 ==========

def romanize_text(
    text: str,
    lang: str,
    kks: pykakasi.kakasi,
    style: str = "camel",
    sep: str = ""
) -> str:
    """
    将给定文本统一转换为罗马音或拼音。
    这是一个中心化的转换函数，整合了对不同语言的处理逻辑。

    Args:
        text (str): 待转换的文本。
        lang (str): 语言代码，"cn" 代表中文，"jp" 代表日语。
        kks (pykakasi.kakasi): 一个预先实例化的 pykakasi 对象。
                              （传入实例是为了避免在循环中重复创建，提升性能）
        style (str): 输出的命名风格。
        sep (str): 在非驼峰风格中使用的分隔符。

    Returns:
        str: 转换并格式化后的字符串。
    """
    segments: List[str] = []
    if lang == "cn":
        segments = lazy_pinyin(text, style=Style.NORMAL)
    elif lang == "jp":
        result = kks.convert(text)
        segments = [item["hepburn"] for item in result]
    
    # 调用格式化函数，生成最终字符串
    return format_romaji(segments, style=style, sep=sep)


def convert_filename(
    filename: str,
    lang: str,
    kks: pykakasi.kakasi,
    style: str = "camel",
    sep: str = "",
    custom_dict: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> str:
    """
    对单个文件名执行完整的转换流程。

    流程: 自定义字典替换 -> 罗马音/拼音转换 -> 文件名安全净化。

    Args:
        filename (str): 包含扩展名的完整原始文件名。
        lang (str): 语言代码 ("cn" 或 "jp")。
        kks (pykakasi.kakasi): 预初始化的 pykakasi 实例。
        style (str): 命名风格。
        sep (str): 分隔符。
        custom_dict (Optional[Dict[str, str]]): 自定义替换字典。
        dry_run (bool): 是否为预览模式。

    Returns:
        str: 转换后的新文件名。
    """
    # 步骤 1: 使用 pathlib 分离文件名主体和扩展名
    p = Path(filename)
    name, ext = p.stem, p.suffix

    # 步骤 2: (如果提供了字典) 首先应用自定义替换规则
    if custom_dict:
        name = apply_custom_dict(name, custom_dict, verbose=dry_run)

    # 步骤 3: 对文件名主体进行核心的罗马化/拼音化转换
    new_name = romanize_text(name, lang, kks, style=style, sep=sep)
    
    # 步骤 4: 对转换后的结果进行安全净化，确保其作为文件名是合法的
    new_name = safe_filename(new_name)
    
    # 步骤 5: 拼接回扩展名，得到最终的新文件名
    return new_name + ext


def batch_rename(
    target_path: Path,
    lang: str,
    kks: pykakasi.kakasi,
    style: str = "camel",
    sep: str = "",
    custom_dict: Optional[Dict[str, str]] = None,
    dry_run: bool = False
):
    """
    执行批量重命名操作。

    该函数会遍历指定路径下的所有文件（如果是目录）或处理单个文件，
    并应用 `convert_filename` 函数进行重命名。

    Args:
        target_path (Path): 要处理的文件或目录的路径。
        lang (str): 语言代码。
        kks (pykakasi.kakasi): 预初始化的 pykakasi 实例。
        style (str): 命名风格。
        sep (str): 分隔符。
        custom_dict (Optional[Dict[str, str]]): 自定义替换字典。
        dry_run (bool): 如果为 True，则只打印将要执行的操作，不实际重命名。
    """
    # 根据输入路径是文件还是目录，确定要处理的文件列表
    if target_path.is_file():
        files_to_process = [target_path]
    elif target_path.is_dir():
        # 使用 rglob('*') 进行递归遍历，找出所有文件
        files_to_process = [f for f in target_path.rglob('*') if f.is_file()]
    else:
        print(f"[错误] 路径既不是文件也不是目录: {target_path}", file=sys.stderr)
        return

    print(f"发现 {len(files_to_process)} 个文件待处理...")

    for src_path in files_to_process:
        # 忽略隐藏文件 (以 '.' 开头的文件)
        if src_path.name.startswith('.'):
            continue

        # 为当前文件生成新文件名
        new_filename = convert_filename(
            src_path.name, lang, kks, style, sep, custom_dict, dry_run
        )
        
        # 构建完整的目标路径
        dst_path = src_path.with_name(new_filename)

        # 如果新旧文件名相同，则跳过，避免不必要的操作
        if src_path == dst_path:
            print(f"[跳过] {src_path.name} (文件名无需改动)")
            continue

        # 确保目标路径不与现有文件冲突
        dst_path = ensure_unique(dst_path)

        # 根据是否为预览模式，执行操作或打印预览信息
        if dry_run:
            print(f"[预览] {src_path.name} -> {dst_path.name}")
        else:
            try:
                # 执行重命名
                src_path.rename(dst_path)
                print(f"[成功] {src_path.name} -> {dst_path.name}")
            except OSError as e:
                # 捕获并报告潜在的文件系统错误
                print(f"[错误] 重命名 {src_path.name} 失败: {e}", file=sys.stderr)


# ========== 命令行接口 (CLI) 主程序 ==========

def load_dict(dict_file: str) -> Optional[Dict[str, str]]:
    """
    从文本文件加载自定义替换字典。

    文件格式要求:
    -   每行一条规则，格式为 `原始词=替换词`。
    -   以 `#` 开头的行将被视为注释。
    -   空行将被忽略。

    Args:
        dict_file (str): 字典文件的路径。

    Returns:
        Optional[Dict[str, str]]: 成功则返回字典，失败则返回 None。
    """
    d: Dict[str, str] = {}
    try:
        with open(dict_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # 增强健壮性：如果某行格式不正确（不含 '='），则打印警告并跳过
                if "=" not in line:
                    print(
                        f"[警告] 字典文件 {dict_file} 第 {i} 行格式错误，已跳过: '{line}'",
                        file=sys.stderr
                    )
                    continue
                
                key, value = line.split("=", 1)
                d[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"[错误] 字典文件不存在: {dict_file}", file=sys.stderr)
        return None
    except IOError as e:
        print(f"[错误] 无法读取字典文件 {dict_file}: {e}", file=sys.stderr)
        return None
    return d


def main():
    """
    脚本主入口函数。
    负责解析命令行参数，并启动批量重命名流程。
    """
    # 步骤 1: 设置和解析命令行参数
    parser = argparse.ArgumentParser(
        description="批量文件名罗马音转换器 (romanizer.py)",
        # [已修正] 将 'arg.RawTextHelpFormatter' 更改为 'argparse.RawTextHelpFormatter'
        formatter_class=argparse.RawTextHelpFormatter  # 保持帮助信息中的换行格式
    )
    parser.add_argument("path", help="目标文件或文件夹路径")
    parser.add_argument("-l", "--lang", choices=["jp", "cn"], default="jp", help="语言 (jp: 日语, cn: 中文)。默认为 'jp'")
    parser.add_argument("-s", "--style", choices=["camel", "lower", "upper"], default="camel", help="输出风格 (camel: 驼峰, lower: 小写, upper: 大写)。默认为 'camel'")
    parser.add_argument("--sep", default="", help="分隔符 (仅在 'lower' 和 'upper' 风格下有效)")
    parser.add_argument("-d", "--dict", help="自定义替换字典文件路径 (格式: key=value)")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，只显示将要进行的重命名操作，不实际执行")
    
    args = parser.parse_args()

    # 步骤 2: 验证输入路径的有效性
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"[错误] 输入的路径不存在: {args.path}", file=sys.stderr)
        sys.exit(1)

    # 步骤 3: 加载自定义字典 (如果用户提供了)
    custom_dict = load_dict(args.dict) if args.dict else None
    if args.dict and custom_dict is None:
        sys.exit(1) # 如果加载字典失败，则退出程序

    # 步骤 4: [核心性能优化]
    # 在所有操作开始前，仅实例化一次 kakasi 对象。
    # 这避免了在处理每个文件时都重复加载其内部词典，极大地提升了处理大量文件时的性能。
    print("正在初始化转换器...")
    kks = pykakasi.kakasi()
    
    # 步骤 5: 开始执行批量重命名任务
    print("开始处理文件...")
    batch_rename(
        target_path,
        lang=args.lang,
        kks=kks,
        style=args.style,
        sep=args.sep,
        custom_dict=custom_dict,
        dry_run=args.dry_run
    )
    print("处理完成。")


# 当该脚本作为主程序直接运行时，执行 main() 函数
if __name__ == "__main__":
    main()
