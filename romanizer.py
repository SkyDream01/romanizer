# -*- coding: utf-8 -*-
"""
romanizer.py
------------
核心逻辑已重构为面向对象的 Romanizer 类，提供更佳的性能和可复用性。
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Generator, Tuple, Set

# ========== 第三方库检查 ==========
try:
    import pykakasi
    from pypinyin import Style, lazy_pinyin
except ImportError as e:
    print(f"错误：缺少必要的第三方库。请运行 'pip install pypinyin pykakasi'。", file=sys.stderr)
    sys.exit(1)

__all__ = ["Romanizer", "load_dict", "ILLEGAL_CHARS_RE", "RESERVED_NAMES"]

# ========== 预编译正则 (模块级常量) ==========
# 匹配非法字符
ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Windows 保留设备名
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

class Romanizer:
    def __init__(self, lang: str = "jp", style: str = "camel", sep: str = "_", custom_dict: Optional[Dict[str, str]] = None):
        """
        初始化转换器。在此处预加载资源以提高批处理性能。
        """
        self.lang = lang
        self.style = style
        self.sep = sep
        self.custom_dict = custom_dict
        
        # 初始化 pykakasi (耗时操作，仅做一次)
        if self.lang == "jp":
            self.kks = pykakasi.kakasi()
        else:
            self.kks = None

        # 预处理自定义字典的正则匹配模式
        self.dict_pattern = None
        if self.custom_dict:
            # 长词优先匹配
            sorted_keys = sorted(self.custom_dict.keys(), key=len, reverse=True)
            # 预编译正则
            pattern_str = "|".join(re.escape(key) for key in sorted_keys)
            self.dict_pattern = re.compile(f'({pattern_str})')

    def _format_romaji(self, segments: List[str]) -> str:
        """格式化片段列表"""
        parts = [s for s in segments if s]
        if not parts:
            return ""

        if self.style == "camel":
            return "".join(p.capitalize() for p in parts)
        elif self.style == "upper":
            return self.sep.join(p.upper() for p in parts)
        else:  # lower
            return self.sep.join(p.lower() for p in parts)

    def _sanitize_filename(self, stem: str) -> str:
        """净化文件名"""
        stem = unicodedata.normalize("NFKC", stem)
        stem = ILLEGAL_CHARS_RE.sub(self.sep, stem)
        
        if stem.upper() in RESERVED_NAMES:
            stem += "_"
            
        strip_chars = ' .' + self.sep
        stem = stem.strip(strip_chars)
        
        if self.sep:
            stem = re.sub(re.escape(self.sep) + '+', self.sep, stem)
            
        return stem or "untitled"

    def convert(self, filename: str) -> str:
        """将单个文件名转换为目标格式（纯内存操作，不涉及文件系统）"""
        p = Path(filename)
        stem, ext = p.stem, p.suffix
        final_segments = []

        # 1. 分词与转换
        if self.custom_dict and self.dict_pattern:
            # 使用预编译的正则进行分割
            tokens = self.dict_pattern.split(stem)
            tokens = [t for t in tokens if t] # 去除空串
            
            for token in tokens:
                if token in self.custom_dict:
                    final_segments.extend(self.custom_dict[token].split())
                else:
                    final_segments.extend(self._convert_segment(token))
        else:
            final_segments = self._convert_segment(stem)

        # 2. 格式化
        formatted_stem = self._format_romaji(final_segments)
        
        # 3. 净化
        safe_stem = self._sanitize_filename(formatted_stem)
        
        return safe_stem + ext

    def _convert_segment(self, text: str) -> List[str]:
        """辅助函数：根据语言转换文本片段"""
        if not text:
            return []
        if self.lang == "cn":
            return lazy_pinyin(text, style=Style.NORMAL)
        elif self.lang == "jp" and self.kks:
            result = self.kks.convert(text)
            return [item["hepburn"] for item in result]
        return [text]

    def process_items(self, target_path: Path, recursive: bool = False, dry_run: bool = False) -> Generator[Tuple[Path, Path, str], None, None]:
        """
        核心批处理生成器。
        
        Yields:
            (src_path, dst_path, status)
            status: 'success', 'skip', 'conflict' (仅dry-run), 'error'
        """
        # 1. 收集文件
        if target_path.is_file():
            files = [target_path]
        elif target_path.is_dir():
            method = target_path.rglob if recursive else target_path.glob
            files = [f for f in method('*') if f.is_file() and not f.name.startswith('.')]
        else:
            return

        # 2. 处理文件
        # 记录本次批处理中已经占用的目标路径（用于处理批次内的命名冲突）
        seen_destinations: Set[Path] = set()

        for src in files:
            try:
                new_name = self.convert(src.name)
                dst = src.with_name(new_name)

                # 如果名字符合预期且未改变
                if src == dst:
                    seen_destinations.add(src)
                    yield src, dst, "skip"
                    continue

                # --- 冲突解决逻辑 ---
                # 检查磁盘上是否存在，或者在本次批处理中是否已经被预定
                candidate = dst
                n = 1
                while candidate.exists() or candidate in seen_destinations:
                    candidate = dst.with_stem(f"{dst.stem}-{n}")
                    n += 1

                final_dst = candidate
                seen_destinations.add(final_dst)

                if dry_run:
                    # 预览模式不执行 rename
                    status = "success" # 预览时我们认为计算出的路径就是成功的路径
                    yield src, final_dst, status
                else:
                    # 执行重命名
                    src.rename(final_dst)
                    yield src, final_dst, "success"

            except Exception as e:
                # 即使出错也不中断整个流程，而是yield错误信息
                # 利用 dst_path 位置传递错误信息
                yield src, Path(str(e)), "error"

# ========== 可选依赖导入（避免循环引用） ==========
try:
    from meta_romanizer import MetaRomanizer, AUDIO_EXTENSIONS
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    AUDIO_EXTENSIONS = set()

# ========== 辅助函数 (保持向下兼容) ==========

def load_dict(dict_file: str) -> Optional[Dict[str, str]]:
    """加载 JSON 字典"""
    try:
        with open(dict_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else None
    except Exception as e:
        print(f"字典加载失败: {e}", file=sys.stderr)
        return None

# ========== CLI 入口 ==========

def main():
    parser = argparse.ArgumentParser(description="批量文件名罗马音转换工具 (Optimized)")
    parser.add_argument("path", help="目标路径")
    parser.add_argument("-l", "--lang", choices=["jp", "cn"], default="jp", help="语言")
    parser.add_argument("-s", "--style", choices=["camel", "lower", "upper"], default="camel", help="风格")
    parser.add_argument("--sep", default="_", help="分隔符")
    parser.add_argument("-d", "--dict", help="自定义字典路径")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--meta", action="store_true", help="重命名同时罗马化音频元数据标签")
    parser.add_argument("--meta-only", action="store_true", help="仅罗马化音频元数据标签，不重命名文件")
    parser.add_argument("--no-backup", action="store_true", help="修改元数据时不创建备份文件")
    
    args = parser.parse_args()
    
    if (args.meta or args.meta_only) and not HAS_MUTAGEN:
        print("错误: 音频元数据功能需要 mutagen 库。请运行 'pip install mutagen'。", file=sys.stderr)
        sys.exit(1)
    
    if args.meta and args.meta_only:
        print("错误: --meta 和 --meta-only 不能同时使用。", file=sys.stderr)
        sys.exit(1)
    
    if re.search(ILLEGAL_CHARS_RE, args.sep):
        print(f"错误: 分隔符 '{args.sep}' 非法。", file=sys.stderr)
        sys.exit(1)

    target_path = Path(args.path)
    if not target_path.exists():
        print("错误: 路径不存在。", file=sys.stderr)
        sys.exit(1)

    custom_dict = load_dict(args.dict) if args.dict else None
    
    # 实例化转换器
    converter = Romanizer(args.lang, args.style, args.sep, custom_dict)
    
    if args.meta_only:
        # 独立元数据罗马化模式
        mode_str = "预览" if args.dry_run else "执行"
        print(f"正在处理音频元数据: {target_path} (模式: {mode_str})")
        print("-" * 40)
        meta = MetaRomanizer(romanizer=converter, backup=not args.no_backup)
        count = 0
        for filepath, changes, status in meta.process_items(target_path, args.recursive, args.dry_run):
            if status == "unsupported":
                continue
            elif status == "skip":
                print(f"[跳过] {filepath.name}: 无需更改")
            elif status == "error":
                print(f"[错误] {filepath.name}: {changes}")
            else:
                action = "预览" if args.dry_run else "处理"
                print(f"[{action}] {filepath.name}")
                for field, (old_vals, new_vals) in changes.items():
                    for o, n in zip(old_vals, new_vals):
                        print(f"  {field}: {o} -> {n}")
                count += 1
        print("-" * 40)
        print(f"完成。共处理 {count} 个音频文件的元数据。")

    elif args.meta:
        # 组合模式：重命名 + 元数据罗马化
        mode_str = "预览" if args.dry_run else "执行"
        print(f"正在处理: {target_path} (模式: {mode_str}, 含音频元数据)")
        print("-" * 40)
        meta = MetaRomanizer(romanizer=converter, backup=not args.no_backup)
        count = 0
        meta_count = 0
        for src, dst, status in converter.process_items(target_path, args.recursive, args.dry_run):
            if status == "skip":
                print(f"[跳过] {src.name}")
            elif status == "error":
                print(f"[错误] {src.name}: {dst}")
            else:
                action = "预览" if args.dry_run else "重命名"
                print(f"[{action}] {src.name} -> {dst.name}")
                count += 1

            # 对音频文件处理元数据（dry-run 时用 src，实际执行时用 dst）
            if args.dry_run or status == "error":
                target_file = src
            else:
                target_file = dst
            if target_file.suffix.lower() in AUDIO_EXTENSIONS:
                result = meta.romanize_metadata(target_file, dry_run=args.dry_run)
                if result["status"] == "success" and result["changes"]:
                    print(f"  [元数据] 已修改 {len(result['changes'])} 个字段")
                    for field, (old_vals, new_vals) in result["changes"].items():
                        for o, n in zip(old_vals, new_vals):
                            print(f"    {field}: {o} -> {n}")
                    meta_count += 1

        print("-" * 40)
        print(f"完成。重命名 {count} 个文件，元数据处理 {meta_count} 个文件。")

    else:
        # 原有重命名模式（不变）
        print(f"正在处理: {target_path} (模式: {'预览' if args.dry_run else '执行'})")
        print("-" * 40)
        count = 0
        for src, dst, status in converter.process_items(target_path, args.recursive, args.dry_run):
            if status == "skip":
                print(f"[跳过] {src.name}")
            elif status == "error":
                print(f"[错误] {src.name}: {dst}")
            else:
                action = "预览" if args.dry_run else "重命名"
                print(f"[{action}] {src.name} -> {dst.name}")
                count += 1
        print("-" * 40)
        print(f"完成。共处理 {count} 个文件。")

if __name__ == "__main__":
    main()