# Romanizer

这是一个用于批量重命名目录中文件名的 Python 工具，支持将文件名中的中日文字符转换为罗马字母（拼音或罗马字），并根据用户的需求处理自定义字典、特殊字符以及重复号。该工具适用于整理文件名并提高可读性的场景。

## 功能特点 / Features / 機能の特徴

- **中日文字符转换 / Chinese and Japanese Character Conversion / 中国語と日本語の文字変換**：支持将文件名中的中文和日文字符转换为拼音或罗马字 / Converts Chinese and Japanese characters in filenames to pinyin or romaji.
- **自定义字典 / Custom Dictionary / カスタム辞書**：可导入 JSON 格式的自定义字典文件，支持对文件名中的特定字符进行整体替换 / Allows importing a custom dictionary in JSON format for specific character replacements in filenames.
- **特殊字符保留 / Preserve Special Characters / 特殊文字の保持**：文件名中的非字母数字字符（如标点符号）会被保留 / Special characters such as punctuation marks are preserved in the filenames.
- **支持命令行参数 / Command Line Arguments / コマンドライン引数のサポート**：支持指定转换模式（中文拼音、日语罗马字），以及加载字典文件进行替换 / Supports specifying conversion modes (Chinese pinyin, Japanese romaji) and loading dictionary files for replacement.

## 安装要求 / Requirements / インストール要件

- Python 3.x
- 以下 Python 库 / Required Python Libraries / 必要なPythonライブラリ：
  - `pykakasi`（用于日文转换 / For Japanese Conversion）
  - `pypinyin`（用于中文拼音转换 / For Chinese Pinyin Conversion）
  - `jaconv`（用于假名转换 / For Kana Conversion）
  

可以通过以下命令安装所需依赖 / Install the required dependencies via the following command:

```bash
pip install pykakasi pypinyin jaconv
```

## 使用方法 / Usage / 使用方法

### 基本用法 / Basic Usage / 基本的な使い方

```bash
python romanizer.py <目标目录> [选项]
```

### 参数说明 / Arguments / 引数の説明

- `<目标目录> / Target Directory / 目標ディレクトリ`：指定要批量重命名的目录路径 / Specify the directory path to batch rename files.
- `-cn` 或 `chinese`：使用中文拼音转换模式（默认 / Default） / Use Chinese Pinyin conversion mode (default).
- `-jp` 或 `japanese`：使用日语罗马字转换模式 / Use Japanese Romaji conversion mode.
- `-d` 或 `--dict` 后接字典文件路径：指定自定义字典（JSON 格式） / Specify a custom dictionary (in JSON format) using `-d` or `--dict` followed by the dictionary file path.

### 示例 / Examples / 例

1. **使用中文拼音模式并加载自定义字典 / Use Chinese Pinyin mode with custom dictionary**

   ```bash
   python romanizer.py ./File_Path -cn -d custom_dict.json
   ```

2. **使用日语罗马字模式并加载自定义字典 / Use Japanese Romaji mode with custom dictionary**

   ```bash
   python romanizer.py ./File_Path -jp --dict custom_dict.json
   ```

3. **仅使用中文拼音模式 / Use Chinese Pinyin mode only**

   ```bash
   python romanizer.py ./File_Path -cn
   ```

4. **仅使用日语罗马字模式 / Use Japanese Romaji mode only**

   ```bash
   python romanizer.py ./File_Path -jp
   ```

## 字典文件格式 / Dictionary File Format / 辞書ファイル形式

字典文件应为 JSON 格式，包含需要替换的键值对。示例 / The dictionary file should be in JSON format, with key-value pairs for replacements. Example:

```json
{
    "水樹奈々": "Nana Mizuki",
    ……
}
```

程序会根据字典中的映射进行整体替换 / The program will replace based on the mappings in the dictionary.

## 文件名转换规则 / Filename Conversion Rules / ファイル名の変換ルール

1. **中文字符转换 / Chinese Character Conversion / 中国語の文字変換**：使用 `pypinyin` 库将中文字符转换为拼音 / Convert Chinese characters to pinyin using `pypinyin`.
2. **日文字符转换 / Japanese Character Conversion / 日本語の文字変換**：使用 `pykakasi` 库将日文字符转换为罗马字（如果使用日语转换模式） / Convert Japanese characters to romaji using `pykakasi` (when using Japanese conversion mode).
4. **特殊字符 / Special Characters / 特殊文字**：保留文件名中的特殊字符，例如 `-`, `_`, `.` 等 / Preserve special characters like `-`, `_`, `.` in filenames.

## 示例 / Example / 例

假设文件夹中有以下文件 / Suppose there are the following files in the folder:

- `水樹 奈々.mp3`
- `花火 祭り.txt`

### 1. **使用中文拼音转换模式 / Use Chinese Pinyin Conversion Mode**

```bash
python romanizer.py ./File_Path -cn
```

转换后 / After conversion:

- `水樹 奈々.mp3` -> `shui zhu nai nai.mp3`
- `花火 祭り.txt` -> `hua huo sai ri.txt`

### 2. **使用日语罗马字转换模式 / Use Japanese Romaji Conversion Mode**

```bash
python romanizer.py ./File_Path -jp
```

转换后 / After conversion:

- `水樹 奈々.mp3` -> `mizuki nana.mp3`
- `花火 祭り.txt` -> `hanabi matsuri.txt`

### 3. **使用自定义字典 / Use Custom Dictionary**

假设 `custom_dict.json` 内容如下 / Example of `custom_dict.json`:

```json
{
    "水樹 奈々": "Nana Mizuki",
    "水樹奈々": "Nana Mizuki"
}
```

执行以下命令 / Run the following command:

```bash
python romanizer.py ./File_Path -cn -d custom_dict.json
```

转换后 / After conversion:

- `水樹 奈々.mp3` -> `Nana Mizuki.mp3`
- `花火 祭り.txt` -> `hua huo sai ri.txt`

## 错误处理与日志 / Error Handling and Logs / エラーハンドリングとログ

在执行过程中，程序会显示详细的处理日志，包括 / During execution, the program will show detailed logs, including:

- 每个文件的转换过程 / The conversion process of each file.
- 是否有任何文件未成功重命名 / Whether any files failed to rename.
- 自定义字典的替换信息 / Information about dictionary replacements.

## 贡献 / Contribution / 貢献

欢迎贡献代码或报告问题 / Contributions are welcome. Please report any issues or suggestions through [GitHub Issues](https://github.com/yourusername/yourrepo/issues).

## 授权 / License / ライセンス

该项目遵循 MIT 许可证 / This project is licensed under the MIT License. 详情请参阅 [LICENSE](LICENSE) 文件 / See the [LICENSE](LICENSE) file for more details.

