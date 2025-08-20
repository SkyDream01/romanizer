# -*- coding: utf-8 -*-
"""
romanizer.py
------------
一个功能强大的批量文件名转换工具。

该脚本旨在通过一套健壮的自动化流程，将包含中文或日文等复杂字符的文件名，
转换为规范、可移植且易于阅读的罗马字母形式。

核心特性:
1.  多语言支持:
    -   中文 -> Hanyu Pinyin (汉语拼音)
    -   日文 -> Hepburn Romanization (平文式罗马字)
2.  灵活的命名风格:
    -   驼峰式 (CamelCase)
    -   全小写 (lowercase)
    -   全大写 (UPPERCASE)
3.  强大的自定义字典:
    -   通过JSON文件定义特定词汇的精确翻译，实现术语统一。
    -   采用"分词-转换-格式化"流水线，确保字典命中词与自动转换词的命名风格完全一致。
4.  跨平台文件名安全:
    -   自动净化在 Windows, macOS, Linux 等主流操作系统中的非法字符。
    -   处理Windows保留设备名，确保最大兼容性。
5.  智能冲突解决:
    -   自动检测并处理重命名后的文件名冲突，通过添加数字后缀保证文件不被覆盖。
6.  安全预览模式:
    -   提供 "--dry-run" 模式，允许在不修改任何文件的情况下，预覽所有重命名操作的结果。
7.  递归处理能力:
    -   可通过 "--recursive" 选项，递归遍历并处理所有子目录中的文件。
"""

# ========== 核心模块导入 ==========
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

# ========== 第三方库导入 ==========
# 请确保已安装: pip install pykakasi pypinyin
try:
    import pykakasi
    from pypinyin import Style, lazy_pinyin
except ImportError as e:
    print(f"错误：缺少必要的第三方库。请运行 'pip install pykakasi pypinyin' 来安装。", file=sys.stderr)
    print(f"原始错误: {e}", file=sys.stderr)
    sys.exit(1)

# ========== 工具函数 ==========

def format_romaji(segments: List[str], style: str = "camel", sep: str = "") -> str:
    """
    将罗马音/拼音片段列表，格式化为指定风格的字符串。

    Args:
        segments (List[str]): 待格式化的字符串片段列表。
        style (str): 目标命名风格 ('camel', 'lower', 'upper')。
        sep (str): 在 'lower' 和 'upper' 风格中使用的分隔符。

    Returns:
        str: 格式化后的字符串。
    """
    # 过滤掉由转换库可能产生的空字符串片段
    parts = [s for s in segments if s]
    if not parts:
        return ""

    if style == "camel":
        # 驼峰风格：每个片段首字母大写，其余小写，然后无缝拼接。
        return "".join(p.capitalize() for p in parts)
    elif style == "upper":
        # 大写风格：所有片段转为大写，用指定分隔符连接。
        return sep.join(p.upper() for p in parts)
    else:  # 默认为 "lower"
        # 小写风格：所有片段转为小写，用指定分隔符连接。
        return sep.join(p.lower() for p in parts)


def safe_filename_stem(stem: str, replacement: str = '_') -> str:
    """
    净化文件名主体 (不含扩展名)，移除或替换在主流操作系统中非法的字符。

    此函数执行以下操作：
    1.  Unicode 归一化 (NFKC)，将全角字符（如：／？＂）转为半角。
    2.  移除或替换操作系统禁止的字符 (如 < > : " / \ | ? *) 和所有控制字符。
    3.  处理 Windows 平台下的保留设备名 (如 CON, PRN)，为其添加后缀。
    4.  移除文件名开头和结尾的无效字符 (如空格、点、替换符)。
    5.  合并连续的替换字符为一个，保持文件名整洁。

    Args:
        stem (str): 原始文件名主体。
        replacement (str): 用于替换非法字符的字符串。

    Returns:
        str: 净化后的安全文件名主体。若结果为空，则返回 'untitled'。
    """
    # 步骤 1: Unicode 归一化 (NFKC)，处理全角符号等兼容性字符。
    stem = unicodedata.normalize("NFKC", stem)

    # 步骤 2: 移除或替换非法字符。预编译正则表达式以提高性能。
    illegal_chars_re = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    stem = illegal_chars_re.sub(replacement, stem)

    # 步骤 3: 规避 Windows 保留设备名 (例如 'CON.txt' 是无效的)。
    # 检查不区分大小写。
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    if stem.upper() in reserved_names:
        stem += "_"

    # 步骤 4: Windows 不允许文件名以点或空格开头/结尾。此处一并处理替换符。
    strip_chars = ' .' + replacement
    stem = stem.strip(strip_chars)

    # 步骤 5: 将多个连续的替换符压缩成一个。
    if replacement:
        replacement_escaped = re.escape(replacement)
        stem = re.sub(f'{replacement_escaped}+', replacement, stem)

    # 最终保障：如果处理后文件名变为空，提供一个默认名称。
    return stem or "untitled"


def ensure_unique(path: Path) -> Path:
    """
    确保文件路径的唯一性。如果路径已存在，则添加数字后缀以创建新路径。

    例如：如果 "file.txt" 存在，它将依次尝试 "file-1.txt", "file-2.txt", ...
    直到找到一个不存在的路径。

    Args:
        path (Path): 原始目标路径。

    Returns:
        Path: 一个保证不存在的唯一路径。
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


def tokenize_by_dict(text: str, custom_dict: Dict[str, str]) -> List[str]:
    """
    使用自定义字典的键作为分隔符，将文本分割成一个片段列表。
    这种方法是实现“字典命中词”与“自动转换词”风格统一的关键。

    例如:
    text = "【新世紀】エヴァンゲリオン-01"
    custom_dict = {"【新世紀】": "Shin Seiki", "-": "_"}
    返回: ['【新世紀】', 'エヴァンゲリオン', '-', '01']

    Args:
        text (str): 待分词的原始文本。
        custom_dict (Dict[str, str]): 用于分词的字典。

    Returns:
        List[str]: 分词后的片段列表，包含字典键和非字典文本。
    """
    if not custom_dict:
        return [text]

    # 按键长度降序排序，确保长词优先匹配 (例如，优先匹配 "AB"，而不是 "A")。
    sorted_keys = sorted(custom_dict.keys(), key=len, reverse=True)

    # 构建一个正则表达式，用于按字典键分割字符串。
    # re.escape 确保键中的特殊正则字符 (如 '[', ']') 被正确处理。
    # `(A|B|C)` 形式的正则会匹配 A 或 B 或 C，并且捕获组会保留分隔符。
    pattern = "|".join(re.escape(key) for key in sorted_keys)
    tokens = re.split(f'({pattern})', text)

    # 过滤掉 re.split 可能产生的空字符串。
    return [token for token in tokens if token]


# ========== 核心转换逻辑 ==========

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
    对单个文件名执行完整的转换、格式化和净化流程。

    处理流水线:
    1.  **分词 (Tokenize)**: 若存在自定义字典，使用其键将文件名主体分割成逻辑片段。
    2.  **转换 (Convert)**: 遍历片段。若片段是字典键，则获取其对应的值；否则，进行罗马化/拼音化。
    3.  **收集 (Collect)**: 将所有转换后的罗马音/拼音词素收集到一个统一列表中。
    4.  **格式化 (Format)**: 对整个列表应用统一的命名风格 (驼峰、小写等)。
    5.  **净化 (Sanitize)**: 对格式化后的文件名主体进行安全检查，确保其跨平台兼容。

    Args:
        filename (str): 原始文件名 (含扩展名)。
        lang (str): 语言 ('cn' 或 'jp')。
        kks (pykakasi.kakasi): pykakasi 实例。
        style (str): 命名风格。
        sep (str): 分隔符。
        custom_dict (Optional[Dict[str, str]]): 自定义替换字典。
        dry_run (bool): 是否为预览模式。

    Returns:
        str: 经过完整处理的新文件名。
    """
    p = Path(filename)
    stem, ext = p.stem, p.suffix
    
    final_segments = []

    if custom_dict:
        tokens = tokenize_by_dict(stem, custom_dict)
        for token in tokens:
            if token in custom_dict:
                # 命中字典：获取预定义的值。
                value = custom_dict[token]
                if dry_run:
                    print(f"[字典] 命中: '{token}' -> '{value}'")
                # 将字典值按空格分割成词素，以参与后续统一格式化。
                # 例如: "Shin Seiki" -> ["Shin", "Seiki"]
                final_segments.extend(value.split())
            else:
                # 未命中字典：执行标准的罗马化/拼音化。
                if lang == "cn":
                    final_segments.extend(lazy_pinyin(token, style=Style.NORMAL))
                elif lang == "jp":
                    result = kks.convert(token)
                    final_segments.extend([item["hepburn"] for item in result])
    else:
        # 无自定义字典：对整个文件名主体进行罗马化/拼音化。
        if lang == "cn":
            final_segments = lazy_pinyin(stem, style=Style.NORMAL)
        elif lang == "jp":
            result = kks.convert(stem)
            final_segments = [item["hepburn"] for item in result]

    # 将收集到的所有片段进行统一的风格格式化。
    formatted_stem = format_romaji(final_segments, style=style, sep=sep)
    
    # 净化格式化后的文件名，确保安全。
    safe_stem = safe_filename_stem(formatted_stem)
    
    return safe_stem + ext


def batch_rename(
    target_path: Path,
    lang: str,
    kks: pykakasi.kakasi,
    style: str = "camel",
    sep: str = "",
    custom_dict: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    recursive: bool = False
):
    """
    对指定路径下的文件或单个文件执行批量重命名操作。

    Args:
        target_path (Path): 目标文件或目录的路径。
        ... (其他参数传递给 convert_filename): ...
        recursive (bool): 如果目标是目录，是否递归处理所有子目录。
    """
    if target_path.is_file():
        files_to_process = [target_path]
    elif target_path.is_dir():
        if recursive:
            print("模式: 递归处理所有子目录...")
            # rglob('*') 递归遍历目录下的所有项目
            glob_method = target_path.rglob
        else:
            print("模式: 仅处理当前目录...")
            # glob('*') 仅遍历当前目录下的项目
            glob_method = target_path.glob
        # 筛选出文件，排除目录和隐藏文件
        files_to_process = [f for f in glob_method('*') if f.is_file() and not f.name.startswith('.')]
    else:
        print(f"错误: 路径无效或不存在: {target_path}", file=sys.stderr)
        return

    print(f"发现 {len(files_to_process)} 个文件待处理...")
    if not files_to_process:
        return

    for src_path in files_to_process:
        new_filename = convert_filename(
            src_path.name, lang, kks, style, sep, custom_dict, dry_run
        )
        
        # 构造新文件的完整路径
        dst_path = src_path.with_name(new_filename)

        if src_path == dst_path:
            # 如果新旧文件名相同，则跳过
            print(f"[跳过] {src_path.name} (无需改动)")
            continue

        # 确保目标路径唯一，避免覆盖现有文件
        unique_dst_path = ensure_unique(dst_path)
        final_dst_name = unique_dst_path.name

        if dry_run:
            # 在预览模式下，显示将要发生的重命名
            print(f"[预览] {src_path.name} -> {final_dst_name}")
        else:
            # 实际执行重命名操作
            try:
                src_path.rename(unique_dst_path)
                print(f"[成功] {src_path.name} -> {final_dst_name}")
            except OSError as e:
                print(f"错误: 重命名 {src_path.name} 失败: {e}", file=sys.stderr)

# ========== 命令行接口 (CLI) 与主程序 ==========

def load_dict(dict_file: str) -> Optional[Dict[str, str]]:
    """
    从 JSON 文件加载自定义替换字典，并进行基本验证。
    """
    try:
        with open(dict_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            if not isinstance(data, dict):
                print(f"错误: 字典文件 {dict_file} 格式不正确，根元素应为 JSON 对象。", file=sys.stderr)
                return None
            
            # 确保字典的键和值都是字符串类型
            return {str(k): str(v) for k, v in data.items()}
                
    except FileNotFoundError:
        print(f"错误: 字典文件不存在: {dict_file}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"错误: 字典文件 {dict_file} 不是有效的 JSON: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"错误: 读取字典文件 {dict_file} 时发生未知错误: {e}", file=sys.stderr)
        return None


def main():
    """脚本主入口函数，负责解析命令行参数并启动重命名流程。"""
    parser = argparse.ArgumentParser(
        description="一个强大、灵活的文件名罗马音/拼音转换工具。",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
示例:
  # 将 '日文歌曲' 文件夹内的所有文件名转为驼峰式
  python romanizer.py ./日文歌曲 -l jp -s camel

  # 将 '中文文档.docx' 转为小写下划线风格，并预览结果
  python romanizer.py 中文文档.docx -l cn -s lower --sep _ --dry-run
  
  # 使用自定义字典 'mydict.json' 递归处理 'project' 文件夹
  python romanizer.py ./project -d mydict.json -r
"""
    )
    parser.add_argument("path", help="目标文件或文件夹的路径。")
    parser.add_argument("-l", "--lang", choices=["jp", "cn"], default="jp", help="语言 (jp: 日语, cn: 中文)。默认为 'jp'。")
    parser.add_argument("-s", "--style", choices=["camel", "lower", "upper"], default="camel", help="输出命名风格 (camel: 驼峰, lower: 小写, upper: 大写)。默认为 'camel'。")
    parser.add_argument("--sep", default="_", help="分隔符，在 'lower' 和 'upper' 风格下生效。默认为 '_'。")
    parser.add_argument("-d", "--dict", help="自定义替换字典的路径 (JSON 格式)。")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录中的所有文件。")
    parser.add_argument("--dry-run", action="store_true", help="预览模式：仅显示重命名计划，不执行任何文件操作。")
    
    args = parser.parse_args()

    # 校验分隔符是否包含非法文件名字符
    illegal_sep_chars = r'[<>:"/\\|?*\x00-\x1f]'
    if re.search(illegal_sep_chars, args.sep):
        print(f"错误: 分隔符 '{args.sep}' 包含非法文件名字符。", file=sys.stderr)
        sys.exit(1)

    target_path = Path(args.path)
    if not target_path.exists():
        print(f"错误: 输入的路径不存在: {args.path}", file=sys.stderr)
        sys.exit(1)

    custom_dict = load_dict(args.dict) if args.dict else None
    if args.dict and custom_dict is None:
        # 如果指定了字典但加载失败，则退出程序
        sys.exit(1)

    print("正在初始化转换器...")
    kks = pykakasi.kakasi()
    
    print("="*20)
    print("开始处理文件...")
    batch_rename(
        target_path,
        lang=args.lang,
        kks=kks,
        style=args.style,
        sep=args.sep,
        custom_dict=custom_dict,
        dry_run=args.dry_run,
        recursive=args.recursive
    )
    print("处理完成。")
    print("="*20)

if __name__ == "__main__":
    main()
