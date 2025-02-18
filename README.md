# Romanizer (文件名转换工具 / ファイル名変換ツール)

**English | [简体中文](#简体中文) | [日本語](#日本語)**  

---

## English

### Overview

`Romanizer` is a batch renaming tool for files, converting Chinese and Japanese characters in filenames into Latin alphabet (Pinyin or Romaji). It supports **custom dictionary imports**.

### Features

- **Chinese and Japanese character conversion**: Convert filenames containing Chinese characters to **Pinyin** or Japanese characters to **Romaji**.
- **Custom dictionary import**: Users can define a JSON dictionary for custom replacements.
- **Command-line options**: Select conversion mode (`-cn` for Pinyin, `-jp` for Romaji) and load a dictionary file.

### Installation

Ensure Python 3.x is installed, then install dependencies:

```bash
pip install pykakasi pypinyin jaconv
```

### Usage

Basic command format:

```bash
python romanizer.py <target_directory> [options]
```

#### Options:
- `-cn`: Convert Chinese to Pinyin (default).
- `-jp`: Convert Japanese to Romaji.
- `-d <file>`: Load a custom dictionary (`.json`).

#### Example:

```bash
python romanizer.py ./my_files -cn -d custom_dict.json
```

Using the dictionary:

```json
{
    "水樹 奈々": "Nana Mizuki",
    "水樹奈々": "Nana Mizuki"
}
```

Before:
- `水樹奈々.mp3`  
- `花火 祭り.txt`  

After:
- `Nana Mizuki.mp3` (via dictionary)
- `huo huo sai ri.txt` (if using Pinyin mode)

For detailed logs, check the terminal output.

---

## 简体中文

### 概述

`Romanizer` 是一个 **批量重命名** 文件的 Python 工具，可将文件名中的 **中文转换为拼音** 或 **日文转换为罗马字**，并支持 **自定义字典**。

### 功能

- **中日文字符转换**：可将文件名中的 **中文转换为拼音**，或 **日文转换为罗马字**。
- **自定义字典导入**：支持 JSON 格式的自定义字典进行特定替换。
- **命令行选项**：可选择转换模式（`-cn` 拼音，`-jp` 罗马字），并加载字典文件。

### 安装

请确保已安装 Python 3.x，然后运行以下命令安装依赖：

```bash
pip install pykakasi pypinyin jaconv
```

### 使用方法

命令格式：

```bash
python romanizer.py <目标目录> [选项]
```

#### 选项：
- `-cn`：转换中文为拼音（默认）。
- `-jp`：转换日文为罗马字。
- `-d <文件>`：加载自定义字典（JSON 格式）。

#### 示例：

```bash
python romanizer.py ./我的文件夹 -cn -d custom_dict.json
```

**示例字典文件 (`custom_dict.json`)**：

```json
{
    "水樹 奈々": "Nana Mizuki",
    "水樹奈々": "Nana Mizuki"
}
```

转换前：
- `水樹奈々.mp3`
- `花火 祭り.txt`

转换后：
- `Nana Mizuki.mp3`（通过字典替换）
- `hua huo sai ri.txt`（如果选择拼音模式）

详细的转换日志会显示在终端。

---

## 日本語

### 概要

`Romanizer` は、ファイル名に含まれる **中国語をピンイン** に、また **日本語をローマ字** に変換する **バッチリネームツール** です。**カスタム辞書のインポート**。

### 機能

- **中日文字のローマ字変換**：  
  - **中国語** → **ピンイン** に変換  
  - **日本語** → **ローマ字** に変換
- **カスタム辞書の読み込み**：  
  - JSON形式の辞書ファイルを利用し、特定の単語を変更可能。
- **コマンドラインオプション**：  
  - 変換モード（`-cn` ピンイン、`-jp` ローマ字）や、辞書ファイルを指定可能。

### インストール

Python 3.x がインストールされていることを確認し、次のコマンドで依存関係をインストールしてください：

```bash
pip install pykakasi pypinyin jaconv
```

### 使い方

基本的なコマンド：

```bash
python romanizer.py <ターゲットフォルダ> [オプション]
```

#### オプション：
- `-cn`：**中国語をピンインに変換**（デフォルト）。
- `-jp`：**日本語をローマ字に変換**。
- `-d <ファイル>`：**カスタム辞書（JSON形式）を読み込む**。

#### 例：

```bash
python romanizer.py ./フォルダ名 -cn -d custom_dict.json
```

**カスタム辞書 (`custom_dict.json`) の例**：

```json
{
    "水樹 奈々": "Nana Mizuki",
    "水樹奈々": "Nana Mizuki"
}
```

変換前：
- `水樹奈々.mp3`
- `花火 祭り.txt`

変換後：
- `Nana Mizuki.mp3`（辞書による変換）
- `hanabi matsuri.txt`（ローマ字変換）

変換プロセスの詳細はターミナルに出力されます。

---

## License / 许可证 / ライセンス

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.  
本项目采用 **MIT 许可证**，详细信息请查看 [LICENSE](LICENSE) 文件。  
本プロジェクトは **MITライセンス** のもとで提供されています。[LICENSE](LICENSE) をご覧ください。

