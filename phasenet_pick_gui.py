"""import warnings
import numpy as np
import pandas as pd
import shutil
import os
from datetime import datetime

#os.system('conda activate phasenet') 
#If you didn't install phasenet in your base environment,
#please manually do this in your command line

#see cookbook step 1b
#####################step 1 ####################
# run phasenet to generate pick file picks.csv
print("################\nrun PhaseNet\n###############")
# Remove the previous directory
#if os.path.isdir("results"):
#    shutil.rmtree("results")
command = "python ../../src/PhaseNet/phasenet/predict.py --mode=pred --model_dir=../../src/PhaseNet/model/190703-214543 --data_dir=../../Data/waveform_sac --data_list=../../Data/fname.csv --batch_size=1 --format=sac --highpass_filter=1 --amplitude"
print(command)
os.system(command)


#####################step 2####################
print("################\nseparate P and S picks\n###############")
# seperate the picks in picks.csv into p and s picks
pickfile = './results/picks.csv'
output1 = 'temp.p'
output2 = 'temp.s'
prob_threshold = 0.5
samplingrate = 0.01 #samplingrate of your data, default 100 hz

f = open(output1,'w')
g = open(output2,'w')
data = pd.read_csv(pickfile, parse_dates=["begin_time", "phase_time"])
data = data[data["phase_score"] >= prob_threshold].reset_index(drop=True)

data[["year", "mon", "day"]] = data["begin_time"].apply(lambda x: pd.Series([f"{x.year:04d}", f"{x.month:02d}", f"{x.day:02d}"]))
data["ss"] = data["begin_time"].apply(lambda x: (x - datetime.fromisoformat(f"{x.year:04d}-{x.month:02d}-{x.day:02d}")).total_seconds())
data[["net", "name", "loc", "channel"]] = data["station_id"].apply(lambda x: pd.Series(x.split(".")))
data["dum"] = pd.Series(np.ones(len(data)))
data["phase_amp"] = data["phase_amp"] * 2080 * 20 
# why 2080? see https://docs.obspy.org/_modules/obspy/signal/invsim.html
# 2080*20 is because PhaseNet didn’t convolve the response into the Wood-Anderson type and a factor of 20 is experimentally adopted to correct the amplitude.
# Please consider re-calculating the magnitude using the other script 'calc_mag.py'
data["phase_time"] = data["ss"] + data["phase_index"] * samplingrate
data[data["phase_type"] == "P"].to_csv(output1, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)
data[data["phase_type"] == "S"].to_csv(output2, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)

for i in range(len(data["file_name"])):
    (pickfile,junk) = data["file_name"][i].split('/')
    if os.path.isdir(pickfile):
        shutil.rmtree(pickfile)
#####################step 3####################
print("################\ncreat pick files by date and station name\n###############")
# separate picks based on date and station names
# the picks maybe not in order, it is fine and REAL
# will sort it by their arrival
command = "pick2real -Ptemp.p -Stemp.s &"
print(command)
os.system(command)
#os.remove(output1) 
#os.remove(output2) 
"""

# phasenet检测页面，这个页面还是简单的
def load_config():
    with open("config.ini", "r") as f:
        lines = f.readlines()
    # 构造一个字典来存储配置项
    config = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=")
            config[key.strip()] = value.strip()
    return config

import os
import sys
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFormLayout,QApplication
# qthread 避免界面卡死
class PhasenetThread(QThread):
    signal_progress = pyqtSignal(int)
    signal_finished = pyqtSignal()
    signal_error = pyqtSignal(str)
    def __init__(self,parent=None,data_list='',data_dir='', batch_size=1, highpass_filter=1, amplitude=True,format='sac'):
        super().__init__(parent)
        self.config = load_config()
        self.loc_flow_path = self.config['loc_flow_path']
        self.base_command = 'python {}/src/PhaseNet/phasenet/predict.py --mode=pred --model_dir={}/src/PhaseNet/model/190703-214543'.format(self.loc_flow_path, self.loc_flow_path)
        self.data_list = data_list
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.work_dir = self.config['work_dir']
        self.highpass_filter = highpass_filter
        self.amplitude = amplitude
        self.format = format
    def run(self):
        try:
            command = self.base_command + ' --data_list={} --data_dir={} --batch_size={} --highpass_filter={} --amplitude --format={}'.format(self.data_list, self.data_dir, self.batch_size, self.highpass_filter, self.format)
            # --result_dir = self.data_dir + 'Pick/results'
            if not os.path.exists(self.work_dir + '/Pick'):
                os.makedirs(self.work_dir + '/Pick', exist_ok=True)
            if not os.path.exists(self.work_dir + '/Pick/results'):
                os.makedirs(self.work_dir + '/Pick/results', exist_ok=True)
            command += ' --result_dir={}/Pick/results'.format(self.work_dir)
            print(command)
            os.system(command)
            self.signal_finished.emit()
        except Exception as e:
            self.signal_error.emit(str(e))


class PhasenetPickGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Load configuration
        self.config = load_config()
        
        # Create input fields for parameters
        self.data_dir_input = QLineEdit()
        self.data_list_input = QLineEdit()
        self.batch_size_input = QLineEdit()
        self.highpass_filter_input = QLineEdit()
        
        # Set default values from config
        self.data_dir_input.setText(self.config['work_dir'] + '/Data/waveform_sac')
        self.data_list_input.setText(self.config['work_dir'] + '/Data/fname.csv')
        self.batch_size_input.setText('1')
        self.highpass_filter_input.setText('1')
        
        # Create buttons for file selection
        self.data_dir_button = QPushButton("Browse...")
        self.data_list_button = QPushButton("Browse...")
        
        # Create run button and status labels
        self.run_button = QPushButton("Run PhaseNet")
        self.progress_label = QLabel("Ready to run PhaseNet")
        self.status_label = QLabel("")
        
        # Setup form layout
        form_layout = QFormLayout()
        
        # Improve layout with horizontal arrangement
        data_dir_layout = QVBoxLayout()
        data_dir_widget = QWidget()
        data_dir_hbox = QHBoxLayout(data_dir_widget)
        data_dir_hbox.addWidget(self.data_dir_input)
        data_dir_hbox.addWidget(self.data_dir_button)
        data_dir_hbox.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow("Data Directory:", data_dir_widget)
        
        data_list_widget = QWidget()
        
        data_list_hbox = QHBoxLayout(data_list_widget)
        data_list_hbox.addWidget(self.data_list_input)
        data_list_hbox.addWidget(self.data_list_button)
        data_list_hbox.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow("Data List CSV:", data_list_widget)
        
        # Empty comment for batch size field
        form_layout.addRow("Batch Size:", self.batch_size_input)
        # 
        form_layout.addRow("Highpass Filter:", self.highpass_filter_input)
        
        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.run_button)
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.data_dir_button.clicked.connect(self.browse_data_dir)
        self.data_list_button.clicked.connect(self.browse_data_list)
        self.run_button.clicked.connect(self.start_phasenet)
    
    def browse_data_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Data Directory")
        if directory:
            self.data_dir_input.setText(directory)
    
    def browse_data_list(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Data List CSV", "", "CSV Files (*.csv)")
        if file:
            self.data_list_input.setText(file)
    
    def start_phasenet(self):
        # Disable button during processing
        self.run_button.setEnabled(False)
        self.status_label.setText("")
        self.progress_label.setText("Starting PhaseNet...")
        
        try:
            # Get parameters from input fields
            data_dir = self.data_dir_input.text()
            data_list = self.data_list_input.text()
            batch_size = int(self.batch_size_input.text())
            highpass_filter = float(self.highpass_filter_input.text())
            
            # Create and start PhaseNet thread
            self.phasenet_thread = PhasenetThread(
                self, data_list, data_dir, 
                batch_size=batch_size, 
                highpass_filter=highpass_filter
            )
            
            # Connect thread signals
            self.phasenet_thread.signal_progress.connect(self.update_progress)
            self.phasenet_thread.signal_finished.connect(self.phasenet_completed)
            self.phasenet_thread.signal_error.connect(self.phasenet_error)
            
            # Start processing
            self.phasenet_thread.start()
            
        except ValueError as e:
            self.status_label.setText(f"Invalid input: {str(e)}")
            self.run_button.setEnabled(True)
    
    def update_progress(self, value):
        self.progress_label.setText(f"Progress: {value}%")
    
    def phasenet_completed(self):
        self.status_label.setText("PhaseNet completed successfully")
        self.progress_label.setText("Processing complete")
        self.run_button.setEnabled(True)
        
    def phasenet_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.progress_label.setText("PhaseNet failed")
        self.run_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    phasenet_gui = PhasenetPickGUI()
    phasenet_gui.setWindowTitle("PhaseNet Pick GUI")
    phasenet_gui.resize(600, 400)
    phasenet_gui.show()
    sys.exit(app.exec_())