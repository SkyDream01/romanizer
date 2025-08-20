# RomanizerGUI.py (已更新)

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
                               QTextEdit, QFileDialog, QGroupBox, QMessageBox, QProgressBar,
                               QListWidget, QListWidgetItem, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon

try:
    from romanizer import batch_rename, load_dict, pykakasi, convert_filename, ensure_unique
except ImportError:
    QMessageBox.critical(None, "错误", "无法导入 'romanizer.py'。请确保它与GUI脚本在同一目录下。")
    sys.exit(1)

# ... (StreamRedirector 和 RenameWorker 类保持不变) ...
class StreamRedirector(QObject):
    """一个将写入操作(如print)重定向到Qt信号的类"""
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(text)

    def flush(self):
        pass

class RenameWorker(QThread):
    """用于在后台执行重命名操作的线程类"""
    preview_item_signal = Signal(str, str, str) 
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, target_path, lang, style, sep, custom_dict, recursive, dry_run):
        super().__init__()
        self.target_path = target_path
        self.lang = lang
        self.style = style
        self.sep = sep
        self.custom_dict = custom_dict
        self.recursive = recursive
        self.dry_run = dry_run
        self.kks = pykakasi.kakasi()

    def run(self):
        redirector = StreamRedirector()
        redirector.text_written.connect(self.log_signal)
        original_stdout = sys.stdout
        sys.stdout = redirector
        
        try:
            if self.dry_run:
                self.log_signal.emit("正在生成预览...\n")
                if self.target_path.is_file():
                    files_to_process = [self.target_path]
                else:
                    glob_method = self.target_path.rglob if self.recursive else self.target_path.glob
                    files_to_process = [f for f in glob_method('*') if f.is_file() and not f.name.startswith('.')]
                
                rename_map = {}
                for src_path in files_to_process:
                    new_filename = convert_filename(
                        src_path.name, self.lang, self.kks, self.style, self.sep, self.custom_dict, self.dry_run
                    )
                    dst_path = src_path.with_name(new_filename)
                    
                    if src_path == dst_path:
                        self.preview_item_signal.emit(src_path.name, new_filename, "skip")
                        continue
                    
                    if dst_path in rename_map.values():
                        temp_parent = Path("./temp")
                        unique_stem = dst_path.stem
                        n = 1
                        while temp_parent / f"{unique_stem}-{n}{dst_path.suffix}" in rename_map.values():
                            n += 1
                        unique_dst_path = temp_parent / f"{unique_stem}-{n}{dst_path.suffix}"
                        status = "conflict"
                    else:
                        unique_dst_path = dst_path
                        status = "rename"
                    
                    rename_map[src_path] = unique_dst_path
                    self.preview_item_signal.emit(src_path.name, unique_dst_path.name, status)
                
                self.log_signal.emit("\n预览生成完毕。")
            else:
                self.log_signal.emit("正在执行重命名...\n")
                batch_rename(
                    self.target_path,
                    lang=self.lang,
                    kks=self.kks,
                    style=self.style,
                    sep=self.sep,
                    custom_dict=self.custom_dict,
                    dry_run=self.dry_run,
                    recursive=self.recursive
                )
            
            self.finished_signal.emit(True, "操作完成！")
            
        except Exception as e:
            self.finished_signal.emit(False, f"发生错误: {str(e)}")
        finally:
            sys.stdout = original_stdout


class RomanizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Romanizer - 文件名罗马音转换工具")
        self.setGeometry(100, 100, 1000, 700)
        
        self.worker = None
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        control_panel = self.create_control_panel()
        control_panel.setMaximumWidth(400)
        main_layout.addWidget(control_panel)
        
        output_panel = self.create_output_panel()
        main_layout.addWidget(output_panel)
        
        self.statusBar().showMessage("就绪")
    
    def create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        path_group = QGroupBox("1. 选择目标")
        path_layout = QVBoxLayout(path_group)
        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择文件夹或输入文件路径...")
        self.path_edit.textChanged.connect(self.clear_preview)
        path_input_layout.addWidget(self.path_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setToolTip("浏览文件夹") # <--- UI 文本优化
        self.browse_btn.clicked.connect(self.browse_path)
        path_input_layout.addWidget(self.browse_btn)
        path_layout.addLayout(path_input_layout)
        self.recursive_cb = QCheckBox("递归处理子目录")
        path_layout.addWidget(self.recursive_cb)
        layout.addWidget(path_group)
        
        options_group = QGroupBox("2. 配置转换规则")
        options_layout = QVBoxLayout(options_group)
        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel("语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["日语 (jp)", "中文 (cn)"])
        grid_layout.addWidget(self.lang_combo, 1)
        options_layout.addLayout(grid_layout)
        
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("风格:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["驼峰式 (CamelCase)", "小写 (lowercase)", "大写 (UPPERCASE)"])
        style_layout.addWidget(self.style_combo, 1)
        options_layout.addLayout(style_layout)

        sep_layout = QHBoxLayout()
        sep_layout.addWidget(QLabel("分隔符:"))
        self.sep_edit = QLineEdit("_")
        self.sep_edit.setMaximumWidth(100)
        sep_layout.addWidget(self.sep_edit)
        sep_layout.addStretch()
        options_layout.addLayout(sep_layout)
        layout.addWidget(options_group)

        dict_group = QGroupBox("3. 自定义字典 (可选)")
        dict_layout = QVBoxLayout(dict_group)
        dict_input_layout = QHBoxLayout()
        self.dict_edit = QLineEdit()
        self.dict_edit.setPlaceholderText("选择 .json 字典文件...")
        dict_input_layout.addWidget(self.dict_edit)
        self.dict_browse_btn = QPushButton("...")
        self.dict_browse_btn.setToolTip("浏览字典文件")
        self.dict_browse_btn.clicked.connect(self.browse_dict)
        dict_input_layout.addWidget(self.dict_browse_btn)
        dict_layout.addLayout(dict_input_layout)
        layout.addWidget(dict_group)
        
        layout.addStretch()

        action_group = QGroupBox("4. 执行操作")
        button_layout = QHBoxLayout(action_group)
        self.preview_btn = QPushButton("生成预览")
        self.preview_btn.setStyleSheet("background-color: #DAA520; color: white;")
        self.preview_btn.clicked.connect(lambda: self.start_operation(dry_run=True))
        button_layout.addWidget(self.preview_btn)
        
        self.execute_btn = QPushButton("执行重命名")
        self.execute_btn.setStyleSheet("background-color: #c82333; color: white;")
        self.execute_btn.clicked.connect(lambda: self.start_operation(dry_run=False))
        button_layout.addWidget(self.execute_btn)
        layout.addWidget(action_group)
        
        return panel
    
    def create_output_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        splitter = QSplitter(Qt.Vertical)
        
        preview_group = QGroupBox("预览结果")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_list = QListWidget()
        font = QFont("Consolas" if sys.platform == "win32" else "Menlo")
        font.setPointSize(10)
        self.preview_list.setFont(font)
        preview_layout.addWidget(self.preview_list)
        splitter.addWidget(preview_group)
        
        log_group = QGroupBox("详细日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        splitter.addWidget(log_group)
        
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return panel

    ##### VV VV VV VV VV 已修改此函数 VV VV VV VV VV #####
    def browse_path(self):
        """浏览并选择一个目标文件夹，使用系统原生对话框。"""
        # 检查当前输入框中是否为有效路径，作为对话框的起始位置
        start_path = self.path_edit.text()
        if not os.path.isdir(start_path):
            start_path = "" # 如果不是有效目录，则使用默认位置

        # 调用 QFileDialog.getExistingDirectory 静态方法
        # 这个方法会打开一个只允许选择文件夹的原生系统对话框
        path = QFileDialog.getExistingDirectory(
            self,
            "选择目标文件夹",
            start_path # 对话框的初始路径
        )
        
        # 如果用户成功选择了一个文件夹 (path 字符串不为空)
        if path:
            # QFileDialog 返回的路径使用正斜杠'/'，我们用 Path 转一下以适应当前系统
            self.path_edit.setText(str(Path(path)))
    ##### ^^ ^^ ^^ ^^ ^^ 已修改此函数 ^^ ^^ ^^ ^^ ^^ #####

    def browse_dict(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择字典文件", "", "JSON 文件 (*.json)")
        if path:
            self.dict_edit.setText(path)
    
    def clear_preview(self):
        self.preview_list.clear()

    def add_preview_item(self, old_name, new_name, status):
        item = QListWidgetItem()
        arrow = "->"
        if status == "skip":
            arrow = "=="
            item.setForeground(QColor("gray"))
            text = f"{old_name:<50} {arrow} (无需改动)"
        elif status == "conflict":
            item.setForeground(QColor("orange"))
            text = f"{old_name:<50} {arrow} {new_name} (冲突！)"
        else:
            item.setForeground(QColor("#2E8B57"))
            text = f"{old_name:<50} {arrow} {new_name}"

        item.setText(text)
        self.preview_list.addItem(item)
    
    def start_operation(self, dry_run):
        path_text = self.path_edit.text().strip()
        if not path_text:
            QMessageBox.warning(self, "警告", "请先选择目标路径！")
            return
        
        target_path = Path(path_text)
        if not target_path.exists():
            QMessageBox.warning(self, "警告", "目标路径不存在！")
            return
        
        if not dry_run:
            reply = QMessageBox.question(self, "确认操作",
                                           "这将永久性地重命名文件。\n你确定要继续吗？",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        lang = "jp" if self.lang_combo.currentIndex() == 0 else "cn"
        style_map = {"驼峰式 (CamelCase)": "camel", "小写 (lowercase)": "lower", "大写 (UPPERCASE)": "upper"}
        style = style_map[self.style_combo.currentText()]
        sep = self.sep_edit.text()
        recursive = self.recursive_cb.isChecked()
        dict_file = self.dict_edit.text().strip()
        
        custom_dict = None
        if dict_file:
            custom_dict = load_dict(dict_file)
            if custom_dict is None:
                QMessageBox.critical(self, "错误", f"无法加载或解析字典文件: {dict_file}")
                return

        if re.search(r'[<>:"/\\|?*\x00-\x1f]', sep):
            QMessageBox.warning(self, "警告", "分隔符包含非法文件名字符！")
            return
        
        self.set_controls_enabled(False)
        self.log_text.clear()
        self.preview_list.clear()
        
        self.worker = RenameWorker(target_path, lang, style, sep, custom_dict, recursive, dry_run)
        self.worker.preview_item_signal.connect(self.add_preview_item)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.operation_finished)
        self.worker.start()

    def append_log(self, message):
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertPlainText(message.rstrip('\n') + '\n')
        self.log_text.moveCursor(QTextCursor.End)

    def operation_finished(self, success, message):
        self.set_controls_enabled(True)
        self.log_text.append(f"\n--- {message} ---")
        self.statusBar().showMessage(message, 5000)

    def set_controls_enabled(self, enabled):
        """统一设置所有输入控件的启用状态"""
        self.browse_btn.setEnabled(enabled)
        self.dict_browse_btn.setEnabled(enabled)
        self.preview_btn.setEnabled(enabled)
        self.execute_btn.setEnabled(enabled)
        self.path_edit.setEnabled(enabled)
        self.dict_edit.setEnabled(enabled)
        self.lang_combo.setEnabled(enabled)
        self.style_combo.setEnabled(enabled)
        self.sep_edit.setEnabled(enabled)
        self.recursive_cb.setEnabled(enabled)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "确认退出", "操作仍在进行中，确定要退出吗？",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = RomanizerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
