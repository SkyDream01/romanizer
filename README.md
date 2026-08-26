# romanizer.py

A powerful batch file renamer to convert filenames with Chinese/Japanese characters into Roman alphabet.

[**English**](#english) | [**中文**](#中文-chinese) | [**日本語**](#日本語-japanese)

---

## English

### 📜 Overview

`romanizer.py` is a versatile command-line tool for batch renaming files. It specializes in converting filenames containing Chinese or Japanese characters into their romanized equivalents (Hanyu Pinyin for Chinese, Hepburn Romanization for Japanese), ensuring cross-platform compatibility and better organization. It can also romanize embedded audio metadata tags (title, artist, album, etc.) for MP3, FLAC, OGG, M4A and other formats.

### ✨ Features

-   **Dual-Language Support**: Converts Chinese characters to Hanyu Pinyin and Japanese characters to Hepburn Romanization.
-   **Flexible Naming Styles**: Formats output filenames in `CamelCase`, `lowercase`, or `UPPERCASE`.
-   **Customizable Separators**: Allows specifying a custom separator (e.g., `_` or `-`) for `lowercase` and `UPPERCASE` styles. (Default: `_`)
-   **Custom JSON Dictionary**: Enables precise word replacement using a JSON dictionary file, with a long-word-first matching strategy.
-   **Cross-Platform Safe Names**: Automatic removal of illegal characters (`< > : " / \ | ? *`), handling of Windows reserved names (e.g., `CON.txt` → `CON_.txt`), and character normalization.
-   **Conflict Resolution**: Automatically adds numerical suffixes (`file-1.txt`, `file-2.txt`) to prevent overwriting.
-   **Dry-Run Mode**: Preview changes before applying, with detailed output.
-   **Directory Control**: Recursive subdirectory processing via `-r` option.
-   **Audio Metadata Romanization**: Romanizes embedded metadata tags (title, artist, album, genre, etc.) in audio files. Supports MP3, FLAC, OGG, Opus, M4A, AAC, WAV, WMA, AIFF, and more. Can work standalone (`--meta-only`) or combined with file renaming (`--meta`). Automatic `.bak` backup before modification.

### 📋 Requirements

-   Python 3.10+
-   Third-party libraries: `pypinyin`, `pykakasi`
-   Optional: `mutagen` (for audio metadata romanization)

### 🛠️ Installation

1. Clone or download this repository.

2. Install the required Python packages:
   ```bash
   pip install pypinyin pykakasi
   ```

   For audio metadata romanization, also install:
   ```bash
   pip install mutagen
   ```

### 🚀 Usage

#### Basic Syntax

```bash
python romanizer.py [PATH] [OPTIONS]
```

#### Arguments

- `path`: (Required) Path to target file or directory.

#### Options

- `-l`, `--lang`: Source language: `jp` for Japanese, `cn` for Chinese. (Default: `jp`)
- `-s`, `--style`: Output style: `camel` for CamelCase, `lower` for lowercase, `upper` for UPPERCASE. (Default: `camel`)
- `--sep`: Separator for `lower`/`upper` styles. (Default: `_`)
- `-d`, `--dict`: Path to JSON dictionary file for custom replacements.
- `-r`, `--recursive`: Recursively process subdirectories.
- `--dry-run`: Preview changes without renaming.
- `--meta`: Also romanize audio metadata tags when renaming files.
- `--meta-only`: Only romanize audio metadata tags, without renaming files.
- `--no-backup`: Skip creating `.bak` backup files when modifying metadata.

#### Examples

1. **Japanese to CamelCase (default):**

   ```bash
   python romanizer.py /path/to/files
   ```

   ```diff
   - 東京タワー.jpg → ToukyouTawa.jpg
   - 吾輩は猫である.txt → Wagahaihanekodearu.txt
   ```

2. **Chinese to lowercase with underscores:**

   ```bash
   python romanizer.py photos -l cn -s lower --sep _
   ```

   ```diff
   - 你好世界.jpg → ni_hao_shi_jie.jpg
   ```

3. **JSON Dictionary Replacement:**
   Create `mydict.json`:

   ```json
   {
     "東京タワー": "TokyoTower",
     "你好": "Hello"
   }
   ```

   Run:

   ```bash
   python romanizer.py /path -d mydict.json
   ```

   ```diff
   - 東京タワー.jpg → TokyoTower.jpg
   - 你好世界.jpg → HelloWorld.jpg
   ```

4. **Recursive Processing:**

   ```bash
   python romanizer.py archive -r --dry-run
   ```

   Output:

   ```
   [Preview] archive/東京タワー.jpg → ToukyouTawa.jpg
   [Preview] archive/photos/写真.jpg → Shashin.jpg
   ```

5. **Windows Reserved Name Handling:**

   ```diff
   - CON.txt → CON_.txt  (Windows compatible)
   ```

6. **Audio Metadata Romanization (standalone):**

   ```bash
   python romanizer.py /path/to/music --meta-only --dry-run
   ```

   Output:
   ```
   [预览] 東京タワー.mp3
     title: 東京タワー -> toukyou tawaa
     artist: 初音ミク -> hatsune miku
   ```

7. **Rename + Audio Metadata (combined):**

   ```bash
   python romanizer.py /path/to/music --meta --dry-run
   ```

   Output:
   ```
   [预览] 東京タワー.mp3 -> ToukyouTawa.mp3
     [元数据] title: 東京タワー -> toukyou tawaa
   ```

---

## 中文 (Chinese)

### 📜 概述

`romanizer.py` 是一个功能强大的命令行工具，用于批量重命名文件。它专门将包含中文或日文的文件名转换为对应的罗马字母表示形式（中文转为汉语拼音，日文转为平文式罗马字），从而确保文件名的跨平台兼容性并优化文件组织。同时支持罗马化音频文件的嵌入元数据标签（标题、艺术家、专辑等），兼容 MP3、FLAC、OGG、M4A 等主流格式。

### ✨ 功能特性

-   **双语支持**: 可将中文字符转换为汉语拼音，日文字符转换为平文式罗马字 (Hepburn Romanization)。
-   **灵活的命名风格**: 支持将输出文件名格式化为 `驼峰式 (CamelCase)`、`全小写 (lowercase)` 或 `全大写 (UPPERCASE)`。
-   **自定义分隔符**: 在 `全小写` 和 `全大写` 风格下，允许用户指定自定义分隔符（如 `_` 或 `-`）。(默认: `_`)
-   **JSON 字典支持**: 通过 JSON 字典文件实现特定词汇的精确替换，采用长词优先的匹配策略。
-   **跨平台安全命名**: 自动移除非法字符 (`< > : " / \ | ? *`)，处理 Windows 保留设备名 (如 `CON.txt` → `CON_.txt`)，并进行字符归一化。
-   **冲突解决**: 目标文件名冲突时自动添加数字后缀 (`file-1.txt`, `file-2.txt`)。
-   **预览模式 (Dry-Run)**: 带详细输出的预执行预览。
-   **目录控制**: 通过 `-r` 选项递归处理子目录。
-   **音频元数据罗马化**: 罗马化音频文件的嵌入元数据标签（标题、艺术家、专辑、流派等）。支持 MP3、FLAC、OGG、Opus、M4A、AAC、WAV、WMA、AIFF 等格式。可独立使用（`--meta-only`）或配合重命名（`--meta`），修改前自动创建 `.bak` 备份。

### 📋 环境要求

-   Python 3.10+
-   第三方库: `pypinyin`, `pykakasi`
-   可选: `mutagen`（音频元数据罗马化功能）

### 🛠️ 安装

1. 克隆或下载项目：

   ```bash
   git clone https://github.com/yourusername/romanizer.git
   ```

2. 安装依赖：

   ```bash
   pip install pypinyin pykakasi
   ```

   如需音频元数据罗马化功能，还需安装：
   ```bash
   pip install mutagen
   ```

### 🚀 使用方法

#### 基本语法

```bash
python romanizer.py [路径] [选项]
```

#### 参数

- `path`: (必需) 目标路径（文件/目录）。

#### 选项

- `-l`, `--lang`: 源语言：`jp` (日语), `cn` (中文)。(默认: `jp`)
- `-s`, `--style`: 输出风格：`camel` (驼峰), `lower` (小写), `upper` (大写)。(默认: `camel`)
- `--sep`: `lower`/`upper` 风格的分隔符。(默认: `_`)
- `-d`, `--dict`: 自定义替换字典的 JSON 文件路径。
- `-r`, `--recursive`: 递归处理子目录。
- `--dry-run`: 仅预览，不执行操作。
- `--meta`: 重命名同时罗马化音频元数据标签。
- `--meta-only`: 仅罗马化音频元数据标签，不重命名文件。
- `--no-backup`: 修改元数据时不创建 `.bak` 备份文件。

#### 示例

1. **日语转驼峰式：**

   ```bash
   python romanizer.py ~/文档
   ```

   ```diff
   - 東京タワー.jpg → ToukyouTawa.jpg
   ```

2. **中文转下划线分隔：**

   ```bash
   python romanizer.py 相册 -l cn -s lower --sep _
   ```

   ```diff
   - 北京故宫.png → bei_jing_gu_gong.png
   ```

3. **JSON 字典替换：**
   `mydict.json`:

   ```json
   {
     "東京タワー": "TokyoTower",
     "北京": "Beijing"
   }
   ```

   执行：

   ```bash
   python romanizer.py . -d mydict.json
   ```

   ```diff
   - 東京タワー.jpg → TokyoTower.jpg
   - 北京故宫.jpg → BeijingGuGong.jpg
   ```

4. **递归处理子目录：**

   ```bash
   python romanizer.py 项目目录 -r --dry-run
   ```

   输出：

   ```
   [预览] 项目目录/琴譜.pdf → QinPu.pdf
   [预览] 项目目录/子目录/楽譜.jpg → Yokufu.jpg
   ```

5. **Windows保留名处理：**

   ```diff
   - CON.txt → CON_.txt  (Windows兼容)
   ```

6. **独立音频元数据罗马化（预览）：**

   ```bash
   python romanizer.py /path/to/music --meta-only --dry-run
   ```

   输出：
   ```
   [处理] 東京タワー.mp3
     title: 東京タワー -> toukyou tawaa
     artist: 初音ミク -> hatsune miku
   ```

7. **重命名 + 音频元数据罗马化（组合模式）：**

   ```bash
   python romanizer.py /path/to/music --meta --dry-run
   ```

   输出：
   ```
   [预览] 東京タワー.mp3 -> ToukyouTawa.mp3
     [元数据] title: 東京タワー -> toukyou tawaa
   ```

---

## 日本語 (Japanese)

### 📜 概要

`romanizer.py`は、ファイル名を一括でリネームするための強力なコマンドラインツールです。特に、日本語や中国語の文字を含むファイル名を、それぞれのローマ字表記（日本語はヘボン式、中国語は漢語拼音）に変換することに特化しており、クロスプラットフォームでの互換性を確保し、ファイル整理を効率化します。また、MP3、FLAC、OGG、M4Aなどの主要フォーマットのオーディオファイルのメタデータタグ（タイトル、アーティスト、アルバムなど）のローマ字化にも対応しています。

### ✨ 主な機能

-   **二言語対応**: 日本語の文字をヘボン式ローマ字に、中国語の文字を漢語拼音に変換します。
-   **柔軟な命名スタイル**: 出力ファイル名を`キャメルケース (CamelCase)`、`小文字 (lowercase)`、`大文字 (UPPERCASE)`のいずれかにフォーマットします。
-   **カスタム区切り文字**: `小文字`や`大文字`スタイルでの区切り文字をカスタマイズ可能です（デフォルト: `_`）。
-   **JSON辞書サポート**: JSON形式のカスタム辞書ファイルで単語を正確に置換（長い単語が優先的にマッチ）。
-   **クロスプラットフォーム対応**: 不正な文字 (`< > : " / \ | ? *`) を除去し、Windows予約名 (`CON.txt` → `CON_.txt`) を回避。
-   **競合解決**: ファイル名重複時に数字を追加します (`file-1.txt`)。
-   **プレビューモード (Dry-Run)**: 変更内容を適用前に確認可能。
-   **ディレクトリ制御**: `-r`オプションでサブディレクトリを再帰処理。
-   **オーディオメタデータのローマ字化**: オーディオファイルの埋め込みメタデータタグ（タイトル、アーティスト、アルバム、ジャンルなど）をローマ字化します。MP3、FLAC、OGG、Opus、M4A、AAC、WAV、WMA、AIFF等に対応。単独使用（`--meta-only`）またはリネームとの併用（`--meta`）が可能。変更前に`.bak`バックアップを自動作成。

### 📋 動作環境

-   Python 3.10以降
-   サードパーティライブラリ: `pypinyin`, `pykakasi`
-   オプション: `mutagen`（オーディオメタデータのローマ字化機能用）

### 🛠️ インストール

1. リポジトリをクローン:

   ```bash
   git clone https://github.com/yourusername/romanizer.git
   ```

2. 依存パッケージをインストール:

   ```bash
   pip install pypinyin pykakasi
   ```

   オーディオメタデータのローマ字化機能が必要な場合:
   ```bash
   pip install mutagen
   ```

### 🚀 使用方法

#### 基本構文

```bash
python romanizer.py [パス] [オプション]
```

#### 引数

- `path`: (必須) 対象のファイル/ディレクトリパス。

#### オプション

- `-l`, `--lang`: 対象言語：`jp` (日本語), `cn` (中国語) (デフォルト: `jp`)
- `-s`, `--style`: 命名スタイル：`camel`, `lower`, `upper` (デフォルト: `camel`)
- `--sep`: `lower`/`upper`スタイルの区切り文字 (デフォルト: `_`)
- `-d`, `--dict`: カスタム辞書(JSON)のパス。
- `-r`, `--recursive`: サブディレクトリを再帰処理。
- `--dry-run`: プレビューモード（実際に変更を加えません）。
- `--meta`: リネームと同時にオーディオメタデータタグをローマ字化。
- `--meta-only`: オーディオメタデータタグのみローマ字化（ファイル名は変更しない）。
- `--no-backup`: メタデータ変更時に`.bak`バックアップを作成しない。

#### 使用例

1. **日本語をキャメルケースに:**

   ```bash
   python romanizer.py ~/ドキュメント
   ```

   ```diff
   - 日本料理.jpg → NihonRyouri.jpg
   ```

2. **カスタム区切り文字指定:**

   ```bash
   python romanizer.py 音楽 -s lower --sep -
   ```

   ```diff
   - 桜.flac → sakura.flac
   ```

3. **JSON辞書を使用:**
   `mydict.json`:

   ```json
   {
     "東京タワー": "TokyoTower",
     "画像": "Image"
   }
   ```

   実行:

   ```bash
   python romanizer.py . -d mydict.json
   ```

   ```diff
   - 東京タワー.jpg → TokyoTower.jpg
   - 画像処理.png → ImageProcessing.png
   ```

4. **再帰処理のプレビュー:**

   ```bash
   python romanizer.py プロジェクト -r --dry-run
   ```

   出力:

   ```
   [プレビュー] プロジェクト/報告書.docx -> HoukokuSho.docx
   [プレビュー] プロジェクト/サブ/図表.jpg -> ZuHyou.jpg
   ```

5. **Windows予約名の自動修正:**

   ```diff
   - CON.png -> CON_.png  (Windows互換)
   ```

6. **オーディオメタデータのローマ字化（プレビュー）:**

   ```bash
   python romanizer.py /path/to/music --meta-only --dry-run
   ```

   出力:
   ```
   [処理] 東京タワー.mp3
     title: 東京タワー -> toukyou tawaa
     artist: 初音ミク -> hatsune miku
   ```

7. **リネーム + メタデータローマ字化（併用）:**

   ```bash
   python romanizer.py /path/to/music --meta --dry-run
   ```

   出力:
   ```
   [プレビュー] 東京タワー.mp3 -> ToukyouTawa.mp3
     [メタデータ] title: 東京タワー -> toukyou tawaa
   ```

---

## 📜 License

This project is licensed under the MIT License.