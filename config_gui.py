import os
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox
# 该页面为配置页,为pyqt5设计，只是一个子页面
# 需要指定的内容有loc-flow的路径
# 工作路径
# todo:
## 检查loc-flow的完整性
## 检查工作路径进行到哪一步了

class ConfigPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ConfigPage, self).__init__(parent)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # LOC-Flow路径配置
        loc_flow_group = QtWidgets.QGroupBox("LOC-Flow路径配置")
        loc_flow_layout = QtWidgets.QHBoxLayout()
        self.loc_flow_path_edit = QtWidgets.QLineEdit()
        loc_flow_browse_btn = QtWidgets.QPushButton("浏览...")
        loc_flow_browse_btn.clicked.connect(self.browse_loc_flow_path)
        loc_flow_check_btn = QtWidgets.QPushButton("检查完整性(to do)")
        loc_flow_check_btn.clicked.connect(self.check_loc_flow_integrity)
        loc_flow_layout.addWidget(self.loc_flow_path_edit)
        loc_flow_layout.addWidget(loc_flow_browse_btn)
        loc_flow_layout.addWidget(loc_flow_check_btn)
        loc_flow_group.setLayout(loc_flow_layout)
        
        # 工作路径配置
        work_dir_group = QtWidgets.QGroupBox("工作路径配置")
        work_dir_layout = QtWidgets.QHBoxLayout()
        self.work_dir_edit = QtWidgets.QLineEdit()
        work_dir_browse_btn = QtWidgets.QPushButton("浏览...")
        work_dir_browse_btn.clicked.connect(self.browse_work_dir)
        work_dir_check_btn = QtWidgets.QPushButton("检查进度(to do)")
        work_dir_check_btn.clicked.connect(self.check_work_progress)
        work_dir_layout.addWidget(self.work_dir_edit)
        work_dir_layout.addWidget(work_dir_browse_btn)
        work_dir_layout.addWidget(work_dir_check_btn)
        work_dir_group.setLayout(work_dir_layout)
        
        # 保存按钮
        save_btn = QtWidgets.QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        
        # 添加到主布局
        layout.addWidget(loc_flow_group)
        layout.addWidget(work_dir_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def browse_loc_flow_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择LOC-Flow路径")
        if path:
            self.loc_flow_path_edit.setText(path)
    
    def browse_work_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择工作路径")
        if path:
            self.work_dir_edit.setText(path)
    
    def check_loc_flow_integrity(self):
        path = self.loc_flow_path_edit.text()
        if not path:
            QMessageBox.warning(self, "警告", "请先选择LOC-Flow路径")
            return
        
        # 检查必要的文件和目录是否存在
        required_files = ["run.py", "requirements.txt"]
        required_dirs = ["models", "utils"]
        
        missing = []
        for file in required_files:
            if not os.path.isfile(os.path.join(path, file)):
                missing.append(f"文件: {file}")
        
        for directory in required_dirs:
            if not os.path.isdir(os.path.join(path, directory)):
                missing.append(f"目录: {directory}")
        
        if missing:
            QMessageBox.warning(self, "LOC-Flow完整性检查", f"缺少以下文件或目录:\n" + "\n".join(missing))
        else:
            QMessageBox.information(self, "LOC-Flow完整性检查", "LOC-Flow路径完整性检查通过!")
    
    def check_work_progress(self):
        path = self.work_dir_edit.text()
        if not path:
            QMessageBox.warning(self, "警告", "请先选择工作路径")
            return
        
        # 检查工作路径的进度
        progress_steps = {
            "raw_images": "原始图像",
            "processed_images": "已处理图像",
            "detected_features": "已检测特征",
            "sparse_reconstruction": "稀疏重建",
            "dense_reconstruction": "稠密重建"
        }
        
        current_progress = "未开始"
        for step, description in progress_steps.items():
            if os.path.exists(os.path.join(path, step)):
                current_progress = description
        
        QMessageBox.information(self, "工作进度", f"当前工作路径进度: {current_progress}")
    
    def save_config(self):
        loc_flow_path = self.loc_flow_path_edit.text()
        work_dir = self.work_dir_edit.text()
        
        if not loc_flow_path or not work_dir:
            QMessageBox.warning(self, "警告", "请填写完整的配置信息")
            return
        
        # 保存配置到文件
        config_dir = './'
        config_file = os.path.join(config_dir, "config.ini")
        with open(config_file, "w") as f:
            f.write(f"[Paths]\n")
            f.write(f"loc_flow_path = {loc_flow_path}\n")
            f.write(f"work_dir = {work_dir}\n")
        
        QMessageBox.information(self, "保存成功", "配置已保存")

        # 退出该页面
        self.close()
    
    def load_config(self):
        config_file = os.path.join('./', "config.ini")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("loc_flow_path"):
                        self.loc_flow_path_edit.setText(line.split("=")[1].strip())
                    elif line.startswith("work_dir"):
                        self.work_dir_edit.setText(line.split("=")[1].strip())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ConfigPage()
    window.show()
    sys.exit(app.exec_())