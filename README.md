# romanizer.py

A powerful batch file renamer to convert filenames with Chinese/Japanese characters into Roman alphabet.

[**English**](#english) | [**中文**](#中文-chinese) | [**日本語**](#日本語-japanese)

---

## English

### 📜 Overview

`romanizer.py` is a versatile command-line tool for batch renaming files. It specializes in converting filenames containing Chinese or Japanese characters into their romanized equivalents (Hanyu Pinyin for Chinese, Hepburn Romanization for Japanese), ensuring cross-platform compatibility and better organization.

### ✨ Features

-   **Dual-Language Support**: Converts Chinese characters to Hanyu Pinyin and Japanese characters to Hepburn Romanization.
-   **Flexible Naming Styles**: Formats output filenames in `CamelCase`, `lowercase`, or `UPPERCASE`.
-   **Customizable Separators**: Allows specifying a custom separator (e.g., `_` or `-`) for `lowercase` and `UPPERCASE` styles.
-   **Custom Dictionary**: Enables precise-word replacement using a custom dictionary file, with a long-word-first matching strategy.
-   **Cross-Platform Safe Names**: Automatically sanitizes filenames by removing illegal characters (`< > : " / \ | ? *`), handling reserved names on Windows, and normalizing characters.
-   **Conflict Resolution**: Automatically avoids filename collisions by appending a numeric suffix (e.g., `file-1.txt`, `file-2.txt`) if the target filename already exists.
-   **Dry-Run Mode**: Provides a preview of all renaming operations without actually modifying any files, ensuring you can review the changes before committing them.

### 📋 Requirements

-   Python 3.10+
-   Third-party libraries: `pypinyin`, `pykakasi`

### 🛠️ Installation

1. Clone or download this repository.

2. Install the required Python packages using pip:

   ```bash
   pip install pypinyin pykakasi
   ```

### 🚀 Usage

#### Basic Syntax

```bash
python romanizer.py [PATH] [OPTIONS]
```

#### Arguments

-   `path`: (Required) The path to the target file or directory. If a directory is provided, the script will recursively process all files within it.

#### Options

-   `-l`, `--lang`: The source language. `jp` for Japanese, `cn` for Chinese. (Default: `jp`)
-   `-s`, `--style`: The output naming style. `camel` for CamelCase, `lower` for lowercase, `upper` for UPPERCASE. (Default: `camel`)
-   `--sep`: The separator to use for `lower` and `upper` styles. (e.g., `_`, `-`). (Default: none)
-   `-d`, `--dict`: Path to a custom dictionary file for specific word replacements.
-   `--dry-run`: Preview the changes without actually renaming files.

#### Examples

1. **Convert Japanese filenames to CamelCase (default behavior):**
   Assume you have files like `東京タワー.jpg` and `吾輩は猫である.txt`.

   ```bash
   python romanizer.py /path/to/your/files
   ```

   *Result:*

   -   `東京タワー.jpg` -> `ToukyouTawa-.jpg`
   -   `吾輩は猫である.txt` -> `Wagahaihanekodearu.txt`

2. **Convert Chinese filenames to lowercase with underscore separators:**
   Assume you have a file `你好世界.mp4`.

   ```bash
   python romanizer.py /path/to/your/files -l cn -s lower --sep _
   ```

   *Result:*

   -   `你好世界.mp4` -> `ni_hao_shi_jie.mp4`

3. **Use a custom dictionary for precise replacements:**
   Create a dictionary file, for example `mydict.txt`:

   ```
   # Comments are ignored
   東京タワー=TokyoTower
   你好=Hi
   ```

   Then run the script with the `-d` option:

   ```bash
   python romanizer.py /path/to/your/files -d mydict.txt
   ```

   *Result:*

   -   `東京タワー.jpg` will be renamed to `TokyoTower.jpg` (dictionary rule takes precedence).

4. **Preview changes before applying them (Dry Run):**
   This is highly recommended before running the script on important data.

   ```bash
   python romanizer.py /path/to/your/files --dry-run
   ```

   *Output:*

   ```
   [预览] 東京タワー.jpg -> ToukyouTawa-.jpg
   [预览] 吾輩は猫である.txt -> Wagahaihanekodearu.txt
   ...
   (No files will be changed on your filesystem)
   ```

---

## 中文 (Chinese)

### 📜 概述

`romanizer.py` 是一个功能强大的命令行工具，用于批量重命名文件。它专门将包含中文或日文的文件名转换为对应的罗马字母表示形式（中文转为汉语拼音，日文转为平文式罗马字），从而确保文件名的跨平台兼容性并优化文件组织。

### ✨ 功能特性

-   **双语支持**: 可将中文字符转换为汉语拼音，日文字符转换为平文式罗马字 (Hepburn Romanization)。
-   **灵活的命名风格**: 支持将输出文件名格式化为 `驼峰式 (CamelCase)`、`全小写 (lowercase)` 或 `全大写 (UPPERCASE)`。
-   **自定义分隔符**: 在 `全小写` 和 `全大写` 风格下，允许用户指定自定义分隔符（如 `_` 或 `-`）。
-   **自定义字典**: 支持通过字典文件实现特定词汇的精确替换，并采用长词优先的匹配策略。
-   **跨平台安全命名**: 自动净化文件名，移除非法字符 (`< > : " / \ | ? *`)，处理 Windows 保留设备名，并进行字符归一化。
-   **冲突解决**: 当目标文件名已存在时，自动在文件名后追加数字后缀（如 `file-1.txt`, `file-2.txt`）以避免重名冲突。
-   **预览模式 (Dry-Run)**: 在不实际修改任何文件的情况下，预先展示所有将要执行的重命名操作，确保您可以在提交更改前进行核对。

### 📋 环境要求

-   Python 3.10+
-   第三方库: `pypinyin`, `pykakasi`

### 🛠️ 安装

1. 克隆或下载此项目代码。

2. 使用 pip 安装所需的 Python 依赖包：

   ```bash
   pip install pypinyin pykakasi
   ```

### 🚀 使用方法

#### 基本语法

```bash
python romanizer.py [路径] [选项]
```

#### 参数

-   `path`: (必需) 目标文件或文件夹的路径。如果提供的是文件夹路径，脚本将递归处理其中的所有文件。

#### 选项

-   `-l`, `--lang`: 源文件语言。`jp` 代表日语, `cn` 代表中文。(默认: `jp`)
-   `-s`, `--style`: 输出命名风格。`camel` 代表驼峰式, `lower` 代表全小写, `upper` 代表全大写。(默认: `camel`)
-   `--sep`: 用于 `lower` 和 `upper` 风格的分隔符 (例如 `_`, `-`)。(默认: 无)
-   `-d`, `--dict`: 自定义替换字典文件的路径。
-   `--dry-run`: 预览模式，仅显示将要发生的改变，不实际重命名文件。

#### 使用示例

1. **将日语文件名转换为驼峰式（默认行为）:**
   假设您有文件 `東京タワー.jpg` 和 `吾輩は猫である.txt`。

   ```bash
   python romanizer.py /path/to/your/files
   ```

   *结果:*

   -   `東京タワー.jpg` -> `ToukyouTawa-.jpg`
   -   `吾輩は猫である.txt` -> `Wagahaihanekodearu.txt`

2. **将中文文件名转换为带下划线的小写格式:**
   假设您有一个文件 `你好世界.mp4`。

   ```bash
   python romanizer.py /path/to/your/files -l cn -s lower --sep _
   ```

   *结果:*

   -   `你好世界.mp4` -> `ni_hao_shi_jie.mp4`

3. **使用自定义字典进行精确替换:**
   创建一个字典文件，例如 `mydict.txt`：

   ```
   # 以'#'开头的行是注释，将被忽略
   東京タワー=TokyoTower
   你好=Hi
   ```

   然后使用 `-d` 选项运行脚本：

   ```bash
   python romanizer.py /path/to/your/files -d mydict.txt
   ```

   *结果:*

   -   `東京タワー.jpg` 将被重命名为 `TokyoTower.jpg` (字典规则优先)。

4. **在应用更改前进行预览（Dry Run）:**
   强烈建议在处理重要数据前使用此模式。

   ```bash
   python romanizer.py /path/to/your/files --dry-run
   ```

   *输出:*

   ```
   [预览] 東京タワー.jpg -> ToukyouTawa-.jpg
   [预览] 吾輩は猫である.txt -> Wagahaihanekodearu.txt
   ...
   (您的文件系统中的任何文件都不会被实际更改)
   ```

---

## 日本語 (Japanese)

### 📜 概要

`romanizer.py`は、ファイル名を一括でリネームするための強力なコマンドラインツールです。特に、日本語や中国語の文字を含むファイル名を、それぞれのローマ字表記（日本語はヘボン式、中国語は漢語拼音）に変換することに特化しており、クロスプラットフォームでの互換性を確保し、ファイル整理を効率化します。

### ✨ 主な機能

-   **二言語対応**: 日本語の文字をヘボン式ローマ字に、中国語の文字を漢語拼音（Hanyu Pinyin）に変換します。
-   **柔軟な命名スタイル**: 出力ファイル名を`キャメルケース (CamelCase)`、`小文字 (lowercase)`、`大文字 (UPPERCASE)`のいずれかの形式にフォーマットします。
-   **カスタム区切り文字**: `小文字`や`大文字`スタイルで、アンダースコア (`_`) やハイフン (`-`) などのカスタム区切り文字を指定できます。
-   **カスタム辞書**: 独自の辞書ファイルを用いて、特定の単語を正確に置換できます（長い単語が優先的にマッチングされます）。
-   **クロスプラットフォーム対応の安全なファイル名**: 不正な文字 (`< > : " / \ | ? *`) を自動的に除去し、Windowsの予約名を回避し、文字を正規化することで、安全なファイル名を生成します。
-   **競合解決**: リネーム後のファイル名が既に存在する場合、自動的に数字の接尾辞（例: `file-1.txt`, `file-2.txt`）を追加して衝突を回避します。
-   **プレビューモード (Dry-Run)**: 実際にファイルを変更することなく、実行されるリネーム操作の一覧をプレビュー表示します。これにより、変更を適用する前に内容を確認できます。

### 📋 動作環境

-   Python 3.10以降
-   サードパーティライブラリ: `pypinyin`, `pykakasi`

### 🛠️ インストール

1. このリポジトリをクローンまたはダウンロードします。

2. pipを使用して、必要なPythonパッケージをインストールします。

   ```bash
   pip install pypinyin pykakasi
   ```

### 🚀 使用方法

#### 基本構文

```bash
python romanizer.py [パス] [オプション]
```

#### 引数

-   `path`: (必須) 対象となるファイルまたはディレクトリのパス。ディレクトリを指定した場合、その中のすべてのファイルが再帰的に処理されます。

#### オプション

-   `-l`, `--lang`: 元の言語。`jp` で日本語、 `cn` で中国語。(デフォルト: `jp`)
-   `-s`, `--style`: 出力ファイルの命名スタイル。`camel` (キャメルケース)、`lower` (小文字)、`upper` (大文字)。(デフォルト: `camel`)
-   `--sep`: `lower` と `upper` スタイルで使用する区切り文字 (例: `_`, `-`)。(デフォルト: なし)
-   `-d`, `--dict`: 特定の単語置換ルールを定義したカスタム辞書ファイルのバス。
-   `--dry-run`: プレビューモード。ファイルのリネームを実際には行わず、変更内容のみ表示します。

#### 使用例

1. **日本語のファイル名をキャメルケースに変換する（デフォルト動作）:**
   `東京タワー.jpg` や `吾輩は猫である.txt` といったファイルがあるとします。

   ```bash
   python romanizer.py /path/to/your/files
   ```

   *結果:*

   -   `東京タワー.jpg` -> `ToukyouTawa-.jpg`
   -   `吾輩は猫である.txt` -> `Wagahaihanekodearu.txt`

2. **中国語のファイル名をアンダースコア区切りの小文字に変換する:**
   `你好世界.mp4` というファイルがあるとします。

   ```bash
   python romanizer.py /path/to/your/files -l cn -s lower --sep _
   ```

   *結果:*

   -   `你好世界.mp4` -> `ni_hao_shi_jie.mp4`

3. **カスタム辞書を使って正確に置換する:**
   辞書ファイル（例: `mydict.txt`）を作成します。

   ```
   # '#'で始まる行はコメントとして無視されます
   東京タワー=TokyoTower
   你好=Hi
   ```

   `-d` オプションでスクリプトを実行します。

   ```bash
   python romanizer.py /path/to/your/files -d mydict.txt
   ```

   *結果:*

   -   `東京タワー.jpg` は `TokyoTower.jpg` にリネームされます（辞書のルールが優先されます）。

4. **変更を適用する前にプレビューする（Dry Run）:**
   重要なデータを扱う前に、このモードを使用することを強く推奨します。

   ```bash
   python romanizer.py /path/to/your/files --dry-run
   ```

   *出力:*

   ```
   [プレビュー] 東京タワー.jpg -> ToukyouTawa-.jpg
   [プレビュー] 吾輩は猫である.txt -> Wagahaihanekodearu.txt
   ...
   (ファイルシステム上のファイルは一切変更されません)
   ```

---

## 📜 License

This project is licensed under the MIT License.