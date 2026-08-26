# -*- coding: utf-8 -*-
"""
meta_romanizer.py
-----------------
音频元数据罗马化模块。通过 mutagen 库读写音频文件的嵌入标签，
将 CJK 文本字段罗马化，保留非 CJK 部分不变。
"""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Generator, Tuple

try:
    import mutagen
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TPE2, TCON, TCOM, COMM
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.oggopus import OggOpus
    from mutagen.mp4 import MP4
    from mutagen.id3._frames import TextFrame
except ImportError:
    raise ImportError(
        "缺少 mutagen 库。请运行 'pip install mutagen'。"
    )

from romanizer import Romanizer

__all__ = ["MetaRomanizer"]

# CJK 字符范围正则
_CJK_RE = re.compile(
    r'[\u3040-\u309F'   # 平假名
    r'\u30A0-\u30FF'    # 片假名
    r'\u4E00-\u9FFF'    # CJK 统一汉字
    r'\u3400-\u4DBF'    # CJK 扩展 A
    r'\uF900-\uFAFF'    # CJK 兼容汉字
    r']'
)

# 用于分割 CJK / 非 CJK 片段
_CJK_SPLIT_RE = re.compile(
    r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF]+)'
)

# 可处理的音频扩展名
AUDIO_EXTENSIONS = {
    '.mp3', '.flac', '.ogg', '.opus', '.m4a', '.aac',
    '.wma', '.wav', '.aiff', '.aif', '.mpc', '.ape',
    '.wv', '.tta', '.tak', '.dsf', '.dff'
}

# 标准字段统一映射 (canonical_name -> per-format tag key)
# MP3 ID3 frames, Vorbis comment keys, MP4/iTunes atom keys
FIELD_MAP: Dict[str, Dict[str, str]] = {
    "title":       {"mp3": "TIT2", "vorbis": "TITLE",       "mp4": "\xa9nam"},
    "artist":      {"mp3": "TPE1", "vorbis": "ARTIST",      "mp4": "\xa9ART"},
    "album":       {"mp3": "TALB", "vorbis": "ALBUM",       "mp4": "\xa9alb"},
    "albumartist": {"mp3": "TPE2", "vorbis": "ALBUMARTIST", "mp4": "aART"},
    "genre":       {"mp3": "TCON", "vorbis": "GENRE",       "mp4": "\xa9gen"},
    "composer":    {"mp3": "TCOM", "vorbis": "COMPOSER",    "mp4": "\xa9wrt"},
    "comment":     {"mp3": "COMM", "vorbis": "COMMENT",     "mp4": "\xa9cmt"},
}

# MP3 ID3 frame 类映射（用于创建新帧）
_ID3_FRAME_CLASS = {
    "TIT2": TIT2, "TPE1": TPE1, "TALB": TALB, "TPE2": TPE2,
    "TCON": TCON, "TCOM": TCOM, "COMM": COMM,
}


def _detect_format(audio_file) -> Optional[str]:
    """检测 mutagen 文件对象的格式族，返回 'mp3'/'vorbis'/'mp4'/None"""
    if isinstance(audio_file, (ID3,)) or hasattr(audio_file, 'tags') and isinstance(getattr(audio_file, 'tags', None), ID3):
        return "mp3"
    if isinstance(audio_file, (FLAC, OggVorbis, OggOpus)):
        return "vorbis"
    if isinstance(audio_file, MP4):
        return "mp4"
    # 回退：通过类型名判断
    type_name = type(audio_file).__name__
    if "ID3" in type_name or "MP3" in type_name:
        return "mp3"
    if "FLAC" in type_name or "Ogg" in type_name or "Vorbis" in type_name or "Opus" in type_name:
        return "vorbis"
    if "MP4" in type_name or "AAC" in type_name or "M4A" in type_name:
        return "mp4"
    return None


class MetaRomanizer:
    """音频元数据罗马化器"""

    def __init__(self, romanizer: Romanizer, backup: bool = True):
        self.romanizer = romanizer
        self.backup = backup

    @staticmethod
    def has_cjk(text: str) -> bool:
        """检测文本是否包含 CJK 字符"""
        return bool(_CJK_RE.search(text))

    def romanize_value(self, text: str) -> str:
        """罗马化单个文本值，保留非 CJK 部分"""
        if not text:
            return text
        parts = _CJK_SPLIT_RE.split(text)
        result = []
        for part in parts:
            if not part:
                continue
            if self.has_cjk(part):
                segments = self.romanizer._convert_segment(part)
                # 元数据默认用空格分隔小写（比驼峰更自然）
                result.append(" ".join(s.lower() for s in segments if s))
            else:
                result.append(part)
        return "".join(result)

    def _get_text_tags(self, audio_file, fmt: str) -> Dict[str, List[str]]:
        """格式感知地提取所有文本标签，返回 {canonical_name: [values]}"""
        tags = {}
        field_keys = FIELD_MAP.get("_all_formats", {})

        if fmt == "mp3":
            id3 = audio_file.tags if hasattr(audio_file, 'tags') else None
            if id3 is None:
                return tags
            for canon, fmt_map in FIELD_MAP.items():
                frame_id = fmt_map.get("mp3")
                if frame_id:
                    frames = id3.getall(frame_id)
                    if frames:
                        values = []
                        for frame in frames:
                            if hasattr(frame, 'text'):
                                values.extend([str(t) for t in frame.text])
                        if values:
                            tags[canon] = values
            # 处理 TXXX 等用户自定义文本帧
            for frame in id3.getall("TXXX"):
                if hasattr(frame, 'text') and frame.desc:
                    key = f"TXXX:{frame.desc}"
                    tags[key] = [str(t) for t in frame.text]

        elif fmt == "vorbis":
            if audio_file.tags is None:
                return tags
            for key, values in audio_file.tags:
                key_upper = key.upper()
                canon = None
                for cname, fmt_map in FIELD_MAP.items():
                    if fmt_map.get("vorbis") == key_upper:
                        canon = cname
                        break
                if canon:
                    if canon not in tags:
                        tags[canon] = []
                    tags[canon].extend(values if isinstance(values, list) else [values])
                else:
                    # 非标准字段也处理
                    tags[key] = values if isinstance(values, list) else [values]

        elif fmt == "mp4":
            if audio_file.tags is None:
                return tags
            for key, values in audio_file.tags.items():
                canon = None
                for cname, fmt_map in FIELD_MAP.items():
                    if fmt_map.get("mp4") == key:
                        canon = cname
                        break
                # MP4 文本标签通常是字符串列表
                str_values = [str(v) for v in values if isinstance(v, (str, bytes))]
                if str_values:
                    if canon:
                        tags[canon] = str_values
                    else:
                        tags[key] = str_values

        return tags

    def _set_text_tag(self, audio_file, fmt: str, canon: str, new_values: List[str], original_key: str = None):
        """格式感知地写回单个标签"""
        if fmt == "mp3":
            id3 = audio_file.tags
            frame_id = FIELD_MAP.get(canon, {}).get("mp3")
            if not frame_id and original_key and original_key.startswith("TXXX:"):
                # TXXX 自定义帧
                desc = original_key.split(":", 1)[1]
                for frame in id3.getall("TXXX"):
                    if frame.desc == desc:
                        frame.text = new_values
                        break
                return
            if not frame_id:
                return
            frames = id3.getall(frame_id)
            if frames:
                frames[0].text = new_values
            else:
                cls = _ID3_FRAME_CLASS.get(frame_id)
                if cls:
                    id3.add(cls(encoding=3, text=new_values))

        elif fmt == "vorbis":
            vorbis_key = FIELD_MAP.get(canon, {}).get("vorbis")
            if not vorbis_key and original_key:
                vorbis_key = original_key
            if vorbis_key:
                audio_file.tags[vorbis_key] = new_values

        elif fmt == "mp4":
            mp4_key = FIELD_MAP.get(canon, {}).get("mp4")
            if not mp4_key and original_key:
                mp4_key = original_key
            if mp4_key:
                audio_file.tags[mp4_key] = new_values

    def romanize_metadata(self, filepath: Path, dry_run: bool = False) -> Dict:
        """
        罗马化单个音频文件的元数据。

        Returns:
            {"file": Path, "changes": {field: (old, new)}, "status": str, "message": str}
        """
        result = {
            "file": filepath,
            "changes": {},
            "status": "skip",
            "message": ""
        }

        try:
            audio = mutagen.File(filepath)
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"无法打开文件: {e}"
            return result

        if audio is None:
            result["status"] = "unsupported"
            result["message"] = "不支持的音频格式"
            return result

        if audio.tags is None:
            result["message"] = "无元数据标签"
            return result

        fmt = _detect_format(audio)
        if fmt is None:
            result["status"] = "unsupported"
            result["message"] = "无法识别的标签格式"
            return result

        text_tags = self._get_text_tags(audio, fmt)
        changes = {}

        for canon, values in text_tags.items():
            new_values = []
            changed = False
            for val in values:
                if self.has_cjk(val):
                    rom = self.romanize_value(val)
                    if rom != val:
                        new_values.append(rom)
                        changed = True
                    else:
                        new_values.append(val)
                else:
                    new_values.append(val)
            if changed:
                changes[canon] = (values, new_values)

        if not changes:
            result["message"] = "无需更改（无 CJK 文本）"
            return result

        result["changes"] = changes

        if dry_run:
            result["status"] = "success"
            result["message"] = f"预览: {len(changes)} 个字段"
            return result

        # 备份
        if self.backup:
            try:
                bak_path = filepath.with_suffix(filepath.suffix + ".bak")
                if not bak_path.exists():
                    shutil.copy2(filepath, bak_path)
            except OSError as e:
                result["status"] = "error"
                result["message"] = f"备份失败: {e}"
                return result

        # 写回
        for canon, (old_vals, new_vals) in changes.items():
            try:
                self._set_text_tag(audio, fmt, canon, new_vals)
            except Exception as e:
                result["status"] = "error"
                result["message"] = f"写入 {canon} 失败: {e}"
                return result

        try:
            audio.save()
            result["status"] = "success"
            result["message"] = f"已修改 {len(changes)} 个字段"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"保存失败: {e}"

        return result

    def process_items(
        self,
        target_path: Path,
        recursive: bool = False,
        dry_run: bool = False
    ) -> Generator[Tuple[Path, Dict, str], None, None]:
        """
        批量处理音频文件元数据。

        Yields:
            (filepath, changes_dict, status)
            status: 'success', 'skip', 'error', 'unsupported'
        """
        # 收集文件
        if target_path.is_file():
            files = [target_path]
        elif target_path.is_dir():
            method = target_path.rglob if recursive else target_path.glob
            files = [f for f in method('*') if f.is_file() and not f.name.startswith('.')
                     and f.suffix.lower() in AUDIO_EXTENSIONS]
        else:
            return

        for filepath in files:
            result = self.romanize_metadata(filepath, dry_run)
            yield result["file"], result["changes"], result["status"]
