import sys
import os
import paramiko
import threading
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QProcess

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QPushButton, QTextEdit,
                            QLabel, QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
                            QMessageBox)


class SSHDialog(QDialog):
    """Dialog for SSH connection details"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Connection")
        self.resize(400, 200)
        
        layout = QFormLayout()
        
        self.hostname = QLineEdit()
        self.port = QLineEdit("22")
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Host:", self.hostname)
        layout.addRow("Port:", self.port)
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addRow(self.buttons)
        self.setLayout(layout)
        
    def get_credentials(self):
        return {
            'hostname': self.hostname.text(),
            'port': int(self.port.text()),
            'username': self.username.text(),
            'password': self.password.text(),
        }


class CodeExecutor(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.ssh_client = None
        self.ssh_connected = False
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Code Executor")
        self.setGeometry(100, 100, 1000, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create a splitter for code editor and output
        splitter = QSplitter(Qt.Vertical)
        
        # Code editor setup
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_label = QLabel("Code Editor:")
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Courier", 10))
        self.code_editor.setPlaceholderText("Enter your Python code here...")
        
        editor_layout.addWidget(editor_label)
        editor_layout.addWidget(self.code_editor)
        editor_widget.setLayout(editor_layout)
        
        # Output view setup
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_label = QLabel("Output:")
        self.output_view = QTextEdit()
        self.output_view.setFont(QFont("Courier", 10))
        self.output_view.setReadOnly(True)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_view)
        output_widget.setLayout(output_layout)
        
        # Add widgets to splitter
        splitter.addWidget(editor_widget)
        splitter.addWidget(output_widget)
        splitter.setSizes([400, 400])
        
        # Button layout
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Code (Local)")
        self.run_button.clicked.connect(self.run_code_locally)
        
        self.ssh_connect_button = QPushButton("SSH Connect")
        self.ssh_connect_button.clicked.connect(self.setup_ssh_connection)
        
        self.run_remote_button = QPushButton("Run Code (Remote)")
        self.run_remote_button.clicked.connect(self.run_code_remotely)
        self.run_remote_button.setEnabled(False)
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.ssh_connect_button)
        button_layout.addWidget(self.run_remote_button)
        
        # Add layouts to main layout
        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def run_code_locally(self):
        """Run the code locally using QProcess"""
        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Warning", "No code to execute!")
            return
            
        # Save code to temporary file
        temp_file = "temp_code.py"
        with open(temp_file, "w") as f:
            f.write(code)
            
        self.output_view.clear()
        self.output_view.append("Running code locally...\n")
        
        # Run the code in a separate process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.process.start("python", [temp_file])
        
    def handle_stdout(self):
        """Handle standard output from the process"""
        data = self.process.readAllStandardOutput().data().decode()
        self.output_view.append(data)
        
    def handle_stderr(self):
        """Handle standard error from the process"""
        data = self.process.readAllStandardError().data().decode()
        self.output_view.append(f"<span style='color:red;'>{data}</span>")
        
    def process_finished(self):
        """Called when the process finishes"""
        self.output_view.append("\nExecution completed.")
        
    def setup_ssh_connection(self):
        """Setup SSH connection dialog"""
        dialog = SSHDialog(self)
        if dialog.exec_():
            credentials = dialog.get_credentials()
            self.connect_ssh(credentials)
    
    def connect_ssh(self, credentials):
        """Connect to SSH server"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=credentials['hostname'],
                port=credentials['port'],
                username=credentials['username'],
                password=credentials['password']
            )
            self.ssh_connected = True
            self.run_remote_button.setEnabled(True)
            self.output_view.append(f"Connected to {credentials['hostname']} as {credentials['username']}\n")
            QMessageBox.information(self, "Connection", "SSH connection established successfully!")
            
        except Exception as e:
            self.output_view.append(f"SSH connection error: {str(e)}\n")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            self.ssh_connected = False
    
    def run_code_remotely(self):
        """Run code on remote server via SSH"""
        if not self.ssh_connected or not self.ssh_client:
            QMessageBox.warning(self, "Warning", "Not connected to SSH server!")
            return
            
        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Warning", "No code to execute!")
            return
            
        self.output_view.clear()
        self.output_view.append("Running code remotely...\n")
        
        # Create a temporary file on remote server and execute it
        remote_filename = f"/tmp/remote_code_{hash(code)}.py"
        
        # Start execution in a separate thread to avoid freezing UI
        threading.Thread(target=self._execute_remote_code, 
                        args=(code, remote_filename), 
                        daemon=True).start()
    
    def _execute_remote_code(self, code, remote_filename):
        """Execute code remotely (runs in a separate thread)"""
        try:
            # Upload the code
            sftp = self.ssh_client.open_sftp()
            with sftp.file(remote_filename, 'w') as f:
                f.write(code)
            sftp.close()
            
            # Execute the code
            stdin, stdout, stderr = self.ssh_client.exec_command(f"python3 {remote_filename}")
            
            # Read output and display
            while True:
                line = stdout.readline()
                if not line:
                    break
                # Update UI in the main thread
                QApplication.instance().processEvents()
                self.output_view.append(line.rstrip())
                
            # Read errors
            for line in stderr.readlines():
                QApplication.instance().processEvents()
                self.output_view.append(f"<span style='color:red;'>{line.rstrip()}</span>")
                
            # Cleanup
            self.ssh_client.exec_command(f"rm {remote_filename}")
            self.output_view.append("\nRemote execution completed.")
            
        except Exception as e:
            self.output_view.append(f"Remote execution error: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up SSH connection if exists
        if self.ssh_client:
            self.ssh_client.close()
        
        # Clean up temp file
        if os.path.exists("temp_code.py"):
            try:
                os.remove("temp_code.py")
            except:
                pass
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CodeExecutor()
    ex.show()
    sys.exit(app.exec_())