# RomanizerGUI.py (Optimized)

import sys
import os
import re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
                               QTextEdit, QFileDialog, QGroupBox, QMessageBox, 
                               QListWidget, QListWidgetItem, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QColor

# 导入优化后的模块
try:
    from romanizer import Romanizer, load_dict, ILLEGAL_CHARS_RE
except ImportError:
    QMessageBox.critical(None, "错误", "无法导入 'romanizer.py'。")
    sys.exit(1)

class RenameWorker(QThread):
    """
    后台工作线程
    
    得益于 romanizer.py 的重构，现在 Worker 的职责非常单一：
    只需调用核心库的生成器，并转发信号即可。无需重复实现 dry-run 逻辑。
    """
    progress_signal = Signal(str, str, str) # src_name, dst_name, status
    log_signal = Signal(str)
    finished_signal = Signal(str)
    
    def __init__(self, target_path, config):
        super().__init__()
        self.target_path = target_path
        self.config = config # 包含 lang, style, sep, custom_dict, recursive, dry_run

    def run(self):
        try:
            # 初始化转换器 (耗时操作放在线程中)
            self.log_signal.emit("正在初始化转换引擎...")
            converter = Romanizer(
                lang=self.config['lang'],
                style=self.config['style'],
                sep=self.config['sep'],
                custom_dict=self.config['custom_dict']
            )
            
            mode_str = "预览" if self.config['dry_run'] else "执行"
            self.log_signal.emit(f"开始{mode_str}处理...\n")

            count = 0
            # 调用核心生成器
            iterator = converter.process_items(
                self.target_path, 
                self.config['recursive'], 
                self.config['dry_run']
            )

            for src, dst, status in iterator:
                if status == "error":
                    self.log_signal.emit(f"[错误] {src.name}: {dst}")
                    self.progress_signal.emit(src.name, str(dst), "error")
                elif status == "skip":
                    # 只有在非Dry-Run或者用户需要看skip详情时才发信号，防止列表过长
                    # 这里为了演示，我们发信号并在GUI处理显示颜色
                    self.progress_signal.emit(src.name, dst.name, "skip")
                else:
                    arrow = "->"
                    self.log_signal.emit(f"{src.name} {arrow} {dst.name}")
                    self.progress_signal.emit(src.name, dst.name, "success")
                    count += 1
            
            self.finished_signal.emit(f"{mode_str}完成，涉及 {count} 个文件。")
            
        except Exception as e:
            self.log_signal.emit(f"\n致命错误: {e}")
            self.finished_signal.emit("操作因错误中止。")

class RomanizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Romanizer - 文件名罗马音转换工具 (Optimized)")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_ui()
        self.worker = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        control_panel.setMaximumWidth(380)
        main_layout.addWidget(control_panel)
        
        # 右侧输出面板
        output_panel = self.create_output_panel()
        main_layout.addWidget(output_panel)
        
        self.statusBar().showMessage("就绪")

    def create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 1. 路径选择
        path_group = QGroupBox("1. 目标设置")
        path_layout = QVBoxLayout(path_group)
        h_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("拖入文件夹或点击浏览...")
        h_layout.addWidget(self.path_edit)
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_path)
        h_layout.addWidget(self.browse_btn)
        path_layout.addLayout(h_layout)
        self.recursive_cb = QCheckBox("递归包含子目录")
        path_layout.addWidget(self.recursive_cb)
        layout.addWidget(path_group)
        
        # 2. 转换选项
        opts_group = QGroupBox("2. 转换规则")
        opts_layout = QVBoxLayout(opts_group)
        
        # 语言
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("源语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["日语 (jp)", "中文 (cn)"])
        row1.addWidget(self.lang_combo)
        opts_layout.addLayout(row1)
        
        # 风格
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("输出风格:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["驼峰式 (CamelCase)", "小写 (lowercase)", "大写 (UPPERCASE)"])
        row2.addWidget(self.style_combo)
        opts_layout.addLayout(row2)

        # 分隔符
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("分隔符:"))
        self.sep_edit = QLineEdit("_")
        row3.addWidget(self.sep_edit)
        opts_layout.addLayout(row3)
        layout.addWidget(opts_group)

        # 3. 字典
        dict_group = QGroupBox("3. 高级 (字典)")
        dict_layout = QHBoxLayout(dict_group)
        self.dict_edit = QLineEdit()
        self.dict_edit.setPlaceholderText("可选: .json 字典")
        dict_layout.addWidget(self.dict_edit)
        self.dict_btn = QPushButton("...")
        self.dict_btn.clicked.connect(self.browse_dict)
        dict_layout.addWidget(self.dict_btn)
        layout.addWidget(dict_group)
        
        layout.addStretch()

        # 4. 动作
        act_group = QGroupBox("4. 操作")
        act_layout = QHBoxLayout(act_group)
        self.preview_btn = QPushButton("🔍 生成预览")
        self.preview_btn.clicked.connect(lambda: self.start_worker(dry_run=True))
        act_layout.addWidget(self.preview_btn)
        
        self.run_btn = QPushButton("🚀 执行重命名")
        self.run_btn.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        self.run_btn.clicked.connect(lambda: self.start_worker(dry_run=False))
        act_layout.addWidget(self.run_btn)
        layout.addWidget(act_group)
        
        return panel

    def create_output_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        splitter = QSplitter(Qt.Vertical)
        
        # 列表
        self.preview_list = QListWidget()
        self.preview_list.setFont(QFont("Consolas", 10))
        splitter.addWidget(self.preview_list)
        
        # 日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        splitter.addWidget(self.log_text)
        
        splitter.setSizes([450, 150])
        layout.addWidget(splitter)
        return panel

    def browse_path(self):
        start = self.path_edit.text() if os.path.isdir(self.path_edit.text()) else ""
        path = QFileDialog.getExistingDirectory(self, "选择文件夹", start)
        if path:
            self.path_edit.setText(str(Path(path)))
            self.preview_list.clear()

    def browse_dict(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择字典", "", "JSON (*.json)")
        if path:
            self.dict_edit.setText(path)

    def start_worker(self, dry_run):
        # 验证
        path_str = self.path_edit.text().strip()
        if not path_str or not Path(path_str).exists():
            QMessageBox.warning(self, "提示", "请先选择有效的文件夹。")
            return

        sep = self.sep_edit.text()
        if re.search(ILLEGAL_CHARS_RE, sep):
            QMessageBox.warning(self, "错误", "分隔符包含非法字符。")
            return

        if not dry_run:
            if QMessageBox.Question != QMessageBox.question(self, "确认", "确定要执行重命名吗？此操作不可逆。", QMessageBox.Yes | QMessageBox.No):
                return

        # 准备配置
        custom_dict = None
        dict_path = self.dict_edit.text().strip()
        if dict_path:
            custom_dict = load_dict(dict_path)
            if custom_dict is None:
                QMessageBox.warning(self, "错误", "字典文件读取失败，请检查格式。")
                return

        style_map = {"驼峰式 (CamelCase)": "camel", "小写 (lowercase)": "lower", "大写 (UPPERCASE)": "upper"}
        
        config = {
            'lang': "jp" if self.lang_combo.currentIndex() == 0 else "cn",
            'style': style_map[self.style_combo.currentText()],
            'sep': sep,
            'custom_dict': custom_dict,
            'recursive': self.recursive_cb.isChecked(),
            'dry_run': dry_run
        }

        # UI 状态
        self.set_ui_busy(True)
        self.preview_list.clear()
        self.log_text.clear()

        # 启动线程
        self.worker = RenameWorker(Path(path_str), config)
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.log_signal.connect(self.log_text.append)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, src, dst, status):
        item_text = f"{src} -> {dst}"
        item = QListWidgetItem(item_text)
        
        if status == "success":
            item.setForeground(QColor("#228B22")) # Green
        elif status == "skip":
            item.setText(f"{src} (无变化)")
            item.setForeground(QColor("#808080")) # Gray
        elif status == "error":
            item.setText(f"{src} [错误: {dst}]")
            item.setForeground(QColor("#FF0000")) # Red
            
        self.preview_list.addItem(item)
        self.preview_list.scrollToBottom()

    def on_worker_finished(self, msg):
        self.set_ui_busy(False)
        self.statusBar().showMessage(msg, 5000)
        QMessageBox.information(self, "完成", msg)

    def set_ui_busy(self, busy):
        self.preview_btn.setEnabled(not busy)
        self.run_btn.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)

def main():
    app = QApplication(sys.argv)
    window = RomanizerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()