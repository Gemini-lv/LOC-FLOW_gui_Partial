"""waveform_download_mseed.py
# coding: utf-8

#obspy is included in phasenet
#type 'conda activate phasenet' first

# Import modules
import math
import numpy as np
import pandas as pd
import os 
import shutil
from time import time
from datetime import datetime, timedelta, timezone
from obspy import UTCDateTime, read, read_inventory, read_events
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import (
    CircularDomain,
    Restrictions,
    MassDownloader,
)

# Date and time 
year0 = 2016 # year
mon0 = 10 # month
day0 = 14 #day
nday = 1 # number of days
tb = 0 # beginning time
te = 3000 # ending time, for quick test
#te = 86400 # ending time, the whole day
samplingrate = 100 # resampling rate in Hz

# Station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
network= "IV,YR" # network
channels = ["HH?","EH?"] # station channel priority, 
# If not specified, default channel_priorities: 
#"HH[ZNE12]", "BH[ZNE12]","MH[ZNE12]", "EH[ZNE12]", "LH[ZNE12]", "HL[ZNE12]"
#"BL[ZNE12]", "ML[ZNE12]", "EL[ZNE12]", "LL[ZNE12]", "SH[ZNE12]"),
#https://ds.iris.edu/ds/nodes/dmc/data/formats/seed-channel-naming/

# Define the data directories
data_dir = os.getcwd()
raw_waveform_dir = os.path.join(data_dir, "waveform_mseed")
processed_waveform_dir = os.path.join(data_dir, "waveform_sac")

fname = 'station_all.dat'
o = open(fname,"w")

# Remove the old directories and create new ones
if os.path.isdir(raw_waveform_dir):
    shutil.rmtree(raw_waveform_dir)
os.mkdir(raw_waveform_dir)

if os.path.isdir(processed_waveform_dir):
    shutil.rmtree(processed_waveform_dir)
os.mkdir(processed_waveform_dir)

# Write station information into sac header
def obspy_to_sac_header(stream, inventory):
    for tr in stream:

        # Add stats for SAC format
        tr.stats.sac = dict()

        # Add station and channel information
        metadata = inventory.get_channel_metadata(tr.id)
        tr.stats.sac.stla = metadata["latitude"]
        tr.stats.sac.stlo = metadata["longitude"]
        tr.stats.sac.stel = metadata["elevation"]
        tr.stats.sac.stdp = metadata["local_depth"]
        tr.stats.sac.cmpaz = metadata["azimuth"]
        tr.stats.sac.cmpinc = metadata["dip"] + 90 # different definitions
        
        # set event origin time as reference time
        tr.stats.sac.o = 0

t0 = time()
ETA = 0
k = -1

for i in range(nday):
    # Calculate ETA based on average processing time
    running_time = time() - t0
    days_per_sec = (i + 1) / running_time
    days_to_do = nday - i
    ETA = days_to_do / days_per_sec
    
    origins = UTCDateTime(year0,mon0,day0) + 86400*i
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')
    
    print("Fetching date %d / %d [ETA: %.d s]" % (i+1, nday, ETA))
    print(year,mon,day)
    k += 1

    # Start and end time of waveforms
    starttime= origins + timedelta(seconds=tb)
    endtime = origins + timedelta(seconds=te)
    
    domain = CircularDomain(
        latitude=latref, longitude=lonref, minradius=0.0, maxradius=maxradius/111.19
    )
    
    # see https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.mass_downloader.html
    restrictions = Restrictions(
        starttime=starttime,
        endtime=endtime,
        reject_channels_with_gaps=False,
        #channel="", # use all available channels if not provided
        channel_priorities=channels,
        network=network, # use all available networks if not provided
        #station="",
        #location="00",
        minimum_length = 0.5,
        sanitize=False,
    )

    eventid_dir = os.path.join(raw_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))
    if os.path.isdir(eventid_dir):
        shutil.rmtree(eventid_dir)
    os.mkdir(eventid_dir)

    # use all available providers
    mdl = MassDownloader() 

    # Get the data (if available) and write to output file
    mdl.download(domain, restrictions, mseed_storage=eventid_dir, stationxml_storage=eventid_dir)
    # Remove the response, write header, rotate components
    st = read(os.path.join(eventid_dir,"*.mseed"))
    inv = read_inventory(os.path.join(eventid_dir,"*.xml"))
    st.merge(method=1, fill_value='interpolate')
    st = st.trim(starttime, endtime, pad=True, fill_value=0)
    for tr in st: 
        if np.isnan(np.max(tr.data)) or np.isinf(np.max(tr.data)):
            st.remove(tr)
    st.detrend("demean")
    st.detrend("linear")
    st.interpolate(sampling_rate=samplingrate,startime=tb)
    #response removal takes significant time
    #If you don't remove response here, the magnitude output in REAL is meaningless
    #If you decide to download raw data, you may remove response under the ../Magnitude directory to compute magnitude
    pre_filt = [0.001, 0.002, 25, 30]
    st.attach_response(inv)
    st.remove_response(pre_filt=pre_filt,water_level=60,taper=True,taper_fraction=0.00001)
    obspy_to_sac_header(st, inv)
    st.rotate(method="->ZNE", inventory=inv) #rotate to ZNE, optional, recommended, FDTCC only recognizes ENZ
    sacid_dir = os.path.join(processed_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))

    if os.path.isdir(sacid_dir):
        shutil.rmtree(sacid_dir)
    os.mkdir(sacid_dir)

    for tr in st:
        traceid=os.path.join(sacid_dir,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel)
        if tr.stats.channel[2] == 'Z':
            o.write('{} {} {} {} {} {}\n'.format(tr.stats.sac.stlo,tr.stats.sac.stla,tr.stats.network,tr.stats.station,tr.stats.channel,tr.stats.sac.stel/1000))
        tr.write(traceid, format="SAC")
    
    print("Data on %04d-%02d-%02d found" % (int(year),int(mon),int(day)))
    shutil.rmtree(eventid_dir)
o.close()

shutil.rmtree(raw_waveform_dir)
os.system ("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format (fname, fname)) # remove duplicated stations
"""

 
""" phasenet_input.py
#!/bin/python -w
# coding: utf-8

# Import modules
import math
import numpy as np
import pandas as pd
import os
import shutil
from time import time
import obspy
from obspy.geodetics import locations2degrees
from datetime import datetime, timedelta, timezone
from obspy import UTCDateTime, read, read_inventory, read_events
from obspy.clients.fdsn import Client

# Date and time 
year0 = 2016 # year
mon0 = 10 # month
day0 = 14 #day
nday = 1 # number of days
tbeg = 0 # beginning time
         # the length will be as long as the data in waveform_sac

# Station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
threecomp = 1 # 1: use three components E/N/Z
              # 0: use E/N/Z, E/Z, N/Z, Z
              # It is fine to use either one before the dt.cc calculation.
              # NOTE: FDTCC use ENZ only by default. 
              #       Want to use Z alone? change E and N to Z in FDTCC.c.

data_dir = os.getcwd()
sac_waveform_dir = os.path.join(data_dir, "waveform_sac")
stationdir = os.path.join(data_dir,"station_all.dat")
stationsel = os.path.join(data_dir,"station.dat")

fname = os.path.join(data_dir,"fname.csv")
p = open(stationsel,"w")
o = open(fname,"w")
o.write('fname\n')

if not os.path.isdir(sac_waveform_dir):
    print("No this directory ",sac_waveform_dir)

for i in range(nday):
    origins = UTCDateTime(year0,mon0,day0) + 86400*i
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')
    print(year,mon,day)
    sacid_dir = os.path.join(sac_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))
        
    with open(stationdir, "r") as f:
        for station in f:
            lon, lat, net, sta, chan, elev = station.split(" ")
        
            chane = chan[:2]+"E" #E,2
            chann = chan[:2]+"N" #N,1 consider use st.rotate in waveform_download_mseed.py
            chanz = chan[:2]+"Z"

            tracee = os.path.join(sacid_dir,net+'.'+sta+'.'+chane)
            tracen = os.path.join(sacid_dir,net+'.'+sta+'.'+chann)
            tracez = os.path.join(sacid_dir,net+'.'+sta+'.'+chanz)
            
            dist = 111.19*locations2degrees(float(latref), float(lonref), float(lat), float(lon))
            if dist > maxradius:
                continue
         
            if os.path.exists(tracee) or os.path.exists(tracen) or os.path.exists(tracez):
                o.write('{}\n'.format(year+mon+day+'/'+net+'.'+sta+'.'+chanz[:-1]+"*"))
                p.write(station)

o.close()
f.close()
p.close()

os.system ("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format (stationsel, stationsel))

"""

# 该页面用于下载数据，用pyqt5实现，只是一个子页面
import math
import numpy as np
import pandas as pd
import os 
import shutil
from time import time
from datetime import datetime, timedelta, timezone
from obspy import UTCDateTime, read, read_inventory, read_events
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import (
    CircularDomain,
    Restrictions,
    MassDownloader,
)
# from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QMessageBox # Original
# from PyQt5.QtWidgets import QFormLayout # Original
# from PyQt5.QtWidgets import QApplication # Original

# Using PyQt Fluent Widgets replacements where applicable
from qfluentwidgets import (BodyLabel as QLabel, LineEdit as QLineEdit,
                            PrimaryPushButton as QPushButton, MessageBox as QMessageBox, FluentWindow)
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QFormLayout, QApplication # Keep layout and base classes
from PyQt5.QtCore import QThread, pyqtSignal # Keep QtCore


def load_config():
    try:
        with open("config.ini", "r") as f:
            lines = f.readlines()
        # 构造一个字典来存储配置项
        config = {}
        for line in lines:
            if "=" in line:
                key, value = line.split("=", 1) # Split only on the first '='
                config[key.strip()] = value.strip()
        # Provide default work_dir if not in config
        if "work_dir" not in config:
            config["work_dir"] = os.getcwd() # Default to current working directory
            print("Warning: 'work_dir' not found in config.ini, using current directory.")
        return config
    except FileNotFoundError:
        print("Error: config.ini not found. Creating a default one.")
        default_config = {"work_dir": os.getcwd()}
        with open("config.ini", "w") as f:
            for key, value in default_config.items():
                f.write(f"{key} = {value}\n")
        return default_config
    except Exception as e:
        print(f"Error loading config.ini: {e}")
        # Return a default config or raise an error, depending on desired behavior
        return {"work_dir": os.getcwd()}


# 多线程下载数据，避免阻塞主线程
class DownloadThread(QThread):
    signal_progress = pyqtSignal(int)  # 信号，用于更新进度条
    signal_finished = pyqtSignal()  # 信号，用于下载完成
    signal_error = pyqtSignal(str)  # 信号，用于下载错误

    def __init__(self, year, month, day, nday, tb, te, 
                 latref, lonref, maxradius, network, channels):
        super().__init__()
        self.year = year
        self.month = month
        self.day = day
        self.nday = nday
        self.tb = tb
        self.te = te
        self.latref = latref
        self.lonref = lonref
        self.maxradius = maxradius
        self.network = network
        self.channels = channels
        self.config = load_config()
        self.raw_waveform_dir = os.path.join(self.config["work_dir"], "Data/waveform_mseed")
        self.processed_waveform_dir = os.path.join(self.config["work_dir"], "Data/waveform_sac")
        self.fname = os.path.join(self.config["work_dir"], "Data/station_all.dat")
        self.o = open(self.fname, "w")

        self.t0 = time()
        self.ETA = 0
        self.k = -1

    def obspy_to_sac_header(self, stream, inventory):
        for tr in stream:
            # Add stats for SAC format
            tr.stats.sac = dict()
            # Add station and channel information
            metadata = inventory.get_channel_metadata(tr.id)
            tr.stats.sac.stla = metadata["latitude"]
            tr.stats.sac.stlo = metadata["longitude"]
            tr.stats.sac.stel = metadata["elevation"]
            tr.stats.sac.stdp = metadata["local_depth"]
            tr.stats.sac.cmpaz = metadata["azimuth"]
            tr.stats.sac.cmpinc = metadata["dip"] + 90

            # set event origin time as reference time
            tr.stats.sac.o = 0

    def run(self):
        try:
            # Remove the old directories and create new ones
            if os.path.isdir(self.raw_waveform_dir):
                shutil.rmtree(self.raw_waveform_dir)
            # 允许多级目录创建
            os.makedirs(self.raw_waveform_dir, exist_ok=True)

            if os.path.isdir(self.processed_waveform_dir):
                shutil.rmtree(self.processed_waveform_dir)
            os.makedirs(self.processed_waveform_dir, exist_ok=True)

            # Write station information into sac header
            for i in range(self.nday):
                # Update progress bar
                
                # Calculate ETA based on average processing time
                running_time = time() - self.t0
                days_per_sec = (i + 1) / running_time
                days_to_do = self.nday - i
                self.ETA = days_to_do / days_per_sec

                origins = UTCDateTime(self.year, self.month, self.day) + 86400 * i
                newdate = origins.strftime("%Y/%m/%d")
                year, mon, day = newdate.split('/')

                print("Fetching date %d / %d [ETA: %.d s]" % (i + 1, self.nday, self.ETA))
                print(year, mon, day)
                self.k += 1

                # Start and end time of waveforms
                starttime = origins + timedelta(seconds=self.tb)
                endtime = origins + timedelta(seconds=self.te)

                domain = CircularDomain(
                    latitude=self.latref, longitude=self.lonref, minradius=0.0,
                    maxradius=self.maxradius / 111.19
                )

                restrictions = Restrictions(
                    starttime=starttime,
                    endtime=endtime,
                    reject_channels_with_gaps=False,
                    channel_priorities=self.channels,
                    network=self.network,
                    minimum_length=0.5,
                    sanitize=False,
                )

                eventid_dir = os.path.join(self.raw_waveform_dir, "%04d%02d%02d" % (int(year), int(mon), int(day)))
                if os.path.isdir(eventid_dir):
                    shutil.rmtree(eventid_dir)
                os.makedirs(eventid_dir, exist_ok=True)

                # use all available providers
                mdl = MassDownloader()

                # Get the data (if available) and write to output file
                mdl.download(domain, restrictions, mseed_storage=eventid_dir, stationxml_storage=eventid_dir)
                
                # Remove the response, write header, rotate components
                print("removing response")
                st = read(os.path.join(eventid_dir, "*.mseed"))
                inv = read_inventory(os.path.join(eventid_dir, "*.xml"))
                
                st.merge(method=1, fill_value='interpolate')
                st = st.trim(starttime, endtime, pad=True, fill_value=0)
                
                for tr in st: 
                    if np.isnan(np.max(tr.data)) or np.isinf(np.max(tr.data)):
                        st.remove(tr)
                print("post removing response")
                st.detrend("demean")
                st.detrend("linear")
                st.interpolate(sampling_rate=100, startime=self.tb)
                pre_filt = [0.001, 0.002, 25, 30]
                st.attach_response(inv)
                st.remove_response(pre_filt=pre_filt,water_level=60,taper=True,taper_fraction=0.00001)
                self.obspy_to_sac_header(st, inv)
                st.rotate(method="->ZNE", inventory=inv) #rotate to ZNE, optional, recommended, FDTCC only recognizes ENZ
                sacid_dir = os.path.join(self.processed_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))    
                if os.path.isdir(sacid_dir):
                    shutil.rmtree(sacid_dir)
                os.makedirs(sacid_dir, exist_ok=True)

                for tr in st:
                    traceid = os.path.join(sacid_dir, tr.stats.network + '.' + tr.stats.station + '.' + tr.stats.channel)
                    if tr.stats.channel[2] == 'Z':
                        self.o.write('{} {} {} {} {} {}\n'.format(tr.stats.sac.stlo, tr.stats.sac.stla, tr.stats.network, tr.stats.station, tr.stats.channel, tr.stats.sac.stel / 1000))
                    tr.write(traceid, format="SAC")
                print("Data on %04d-%02d-%02d found" % (int(year),int(mon),int(day)))
                shutil.rmtree(eventid_dir)
                self.signal_progress.emit(int((i + 1) / self.nday * 100))
            self.o.close()
            shutil.rmtree(self.raw_waveform_dir)
            try:
                os.system("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format(self.fname, self.fname))
            except Exception as e:
                print("Error: ", e) # 这个似乎在后边也用不上
                self.signal_finished.emit()
            self.signal_finished.emit()  # 下载完成信号
        except Exception as e:
            print("Error: ", e)
            self.signal_error.emit(str(e))
            self.o.close()

class phasenet_input(QThread):
    signal_progress = pyqtSignal(int)
    signal_finished = pyqtSignal()
    signal_error = pyqtSignal(str)
    def __init__(self, year, month, day, nday, tb, te, latref, lonref, maxradius, threecomp, work_dir):
        super().__init__()
        self.year = year
        self.month = month
        self.day = day
        self.nday = nday
        self.tb = tb
        self.te = te
        self.latref = latref
        self.lonref = lonref
        self.maxradius = maxradius
        self.threecomp = threecomp
        self.work_dir = work_dir
        self.processed_waveform_dir = os.path.join(self.work_dir, "Data/waveform_sac")
        self.stationdir = os.path.join(self.work_dir, "Data/station_all.dat")
        self.stationsel = os.path.join(self.work_dir, "Data/station.dat")
        self.fname = os.path.join(self.work_dir, "Data/fname.csv")
        print(self.processed_waveform_dir)
    
    def run(self):
        try:
            from obspy.geodetics import locations2degrees
            # Remove the old station_all.dat\station.dat\fname.csv
            if os.path.exists(self.stationsel):
                os.remove(self.stationsel)
            if os.path.exists(self.fname):
                os.remove(self.fname)
            self.p = open(self.stationsel, "w")
            self.o = open(self.fname, "w")
            self.o.write('fname\n')

            if not os.path.isdir(self.processed_waveform_dir):
                print("No this directory ", self.processed_waveform_dir)
                self.signal_error.emit("No this directory " + self.processed_waveform_dir)
                return
            
            for i in range(self.nday):
                print("Fetching date %d / %d" % (i + 1, self.nday))
                origins = UTCDateTime(self.year, self.month, self.day) + 86400 * i
                newdate = origins.strftime("%Y/%m/%d")
                year, mon, day = newdate.split('/')
                sacid_dir = os.path.join(self.processed_waveform_dir, "%04d%02d%02d" % (int(year), int(mon), int(day)))
                with open(self.stationdir, "r") as f:
                    for station in f.readlines():
                        lon, lat, net, sta, chan, elev = station.split(" ")
                        chane = chan[:2] + "E"
                        chann = chan[:2] + "N"  # N,1 consider use st.rotate in waveform_download_mseed.py  
                        chanz = chan[:2] + "Z"
                        tracee = os.path.join(sacid_dir, net + '.' + sta + '.' + chane)
                        tracen = os.path.join(sacid_dir, net + '.' + sta + '.' + chann)
                        tracez = os.path.join(sacid_dir, net + '.' + sta + '.' + chanz)

                        dist = 111.19 * locations2degrees(float(self.latref), float(self.lonref), float(lat), float(lon))
                        if dist > self.maxradius:
                            continue
                        if os.path.exists(tracee) or os.path.exists(tracen) or os.path.exists(tracez):
                            self.o.write('{}\n'.format(year + mon + day + '/' + net + '.' + sta + '.' + chanz[:-1] + "*"))
                            self.p.write(station)
                self.signal_progress.emit(int((i + 1) / self.nday * 100))
            self.signal_progress.emit(100)
            self.o.close()
            self.p.close()
            f.close()
            os.system("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format(self.stationsel, self.stationsel))
            self.signal_finished.emit()  # 下载完成信号
        except Exception as e:
            print("Error: ", e)
            self.signal_error.emit(str(e))
            self.o.close()
            self.p.close()

# 该页面用于下载数据，用pyqt5实现，只是一个子页面
from qfluentwidgets import (LineEdit, PrimaryPushButton, PushButton, BodyLabel, CaptionLabel,
                            InfoBar, InfoBarPosition, ProgressBar, FluentWindow, Dialog)

class waveform_download_mseed_gui(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create input fields for parameters using Fluent Widgets
        self.year_input = LineEdit(self)
        self.month_input = LineEdit(self)
        self.day_input = LineEdit(self)
        self.nday_input = LineEdit(self)
        self.tb_input = LineEdit(self)
        self.te_input = LineEdit(self)
        self.latref_input = LineEdit(self)
        self.lonref_input = LineEdit(self)
        self.maxradius_input = LineEdit(self)
        self.network_input = LineEdit(self)
        self.channels_input = LineEdit(self)

        # Create download button and status labels using Fluent Widgets
        self.download_button = PrimaryPushButton("Download Waveforms", self)
        self.phasenet_input_button = PushButton("Generate Phasenet Input", self) # Use standard PushButton for secondary action
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setVisible(False) # Hide initially

        # Set default values
        self.year_input.setText("2016")
        self.month_input.setText("10")
        self.day_input.setText("14")
        self.nday_input.setText("1")
        self.tb_input.setText("0")
        self.te_input.setText("3000")
        self.latref_input.setText("42.75")
        self.lonref_input.setText("13.25")
        self.maxradius_input.setText("50")
        self.network_input.setText("IV,YR")
        self.channels_input.setText("HH?,EH?")

        # Create form layout
        form_layout = QFormLayout()
        form_layout.addRow("Year:", self.year_input)
        form_layout.addRow("Month:", self.month_input)
        form_layout.addRow("Day:", self.day_input)
        form_layout.addRow("Number of days:", self.nday_input)
        form_layout.addRow("Begin time (seconds):", self.tb_input)
        form_layout.addRow("End time (seconds):", self.te_input)
        form_layout.addRow("Reference latitude:", self.latref_input)
        form_layout.addRow("Reference longitude:", self.lonref_input)
        form_layout.addRow("Maximum radius (km):", self.maxradius_input)
        form_layout.addRow("Network codes:", self.network_input)
        form_layout.addRow("Channel priorities:", self.channels_input)

        # Setup main layout
        main_layout = QVBoxLayout(self) # Set layout directly on self
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.download_button)
        main_layout.addWidget(self.phasenet_input_button)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.progress_bar)
        main_layout.addStretch(1) # Push elements to the top

        # Connect signals
        self.download_button.clicked.connect(self.start_download)
        self.phasenet_input_button.clicked.connect(self.start_phasenet_input)

        self.config = load_config()

    def _show_info_bar(self, title, content, success=True, duration=3000):
        """Helper function to show InfoBar messages."""
        position = InfoBarPosition.TOP_RIGHT
        if success:
            InfoBar.success(title, content, duration=duration, parent=self, position=position)
        else:
            InfoBar.error(title, content, duration=duration, parent=self, position=position)

    def _set_buttons_enabled(self, enabled):
        """Enable/disable action buttons."""
        self.download_button.setEnabled(enabled)
        self.phasenet_input_button.setEnabled(enabled)

    def start_download(self):
        self._set_buttons_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._show_info_bar("Starting", "Waveform download initiated...", success=True, duration=2000)

        try:
            # Get parameters from input fields
            year = int(self.year_input.text())
            month = int(self.month_input.text())
            day = int(self.day_input.text())
            nday = int(self.nday_input.text())
            tb = int(self.tb_input.text())
            te = int(self.te_input.text())
            latref = float(self.latref_input.text())
            lonref = float(self.lonref_input.text())
            maxradius = float(self.maxradius_input.text())
            network = self.network_input.text().strip()
            channels = self.channels_input.text().strip().split(',')

            # Create and start download thread
            self.download_thread = DownloadThread(
                year, month, day, nday, tb, te,
                latref, lonref, maxradius, network, channels
            )

            # Connect thread signals
            self.download_thread.signal_progress.connect(self.update_progress)
            self.download_thread.signal_finished.connect(self.download_completed)
            self.download_thread.signal_error.connect(self.download_error)

            # Start download
            self.download_thread.start()

        except ValueError as e:
            self._show_info_bar("Input Error", f"Invalid input: {str(e)}", success=False, duration=5000)
            self._set_buttons_enabled(True)
            self.progress_bar.setVisible(False)
        except Exception as e: # Catch other potential errors during setup
            self._show_info_bar("Error", f"Failed to start download: {str(e)}", success=False, duration=5000)
            self._set_buttons_enabled(True)
            self.progress_bar.setVisible(False)


    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_completed(self):
        self._show_info_bar("Success", "Waveform download completed successfully.", success=True)
        self.progress_bar.setValue(100)
        # Optionally hide progress bar after a delay or keep it at 100%
        # self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)

    def download_error(self, error_message):
        self._show_info_bar("Download Failed", f"Error: {error_message}", success=False, duration=5000)
        self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)

    def start_phasenet_input(self):
        self._set_buttons_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._show_info_bar("Starting", "Phasenet input generation initiated...", success=True, duration=2000)

        try:
            # Get parameters from input fields
            year = int(self.year_input.text())
            month = int(self.month_input.text())
            day = int(self.day_input.text())
            nday = int(self.nday_input.text())
            tb = int(self.tb_input.text()) # Although not used by phasenet_input, keep for consistency
            te = int(self.te_input.text()) # Although not used by phasenet_input, keep for consistency
            latref = float(self.latref_input.text())
            lonref = float(self.lonref_input.text())
            maxradius = float(self.maxradius_input.text())

            # Create and start phasenet input thread
            self.phasenet_thread = phasenet_input(
                year, month, day, nday, tb, te, # Pass tb, te even if unused
                latref, lonref, maxradius, 1, self.config["work_dir"]
            )

            # Connect thread signals
            self.phasenet_thread.signal_progress.connect(self.update_progress)
            self.phasenet_thread.signal_finished.connect(self.convert_completed)
            self.phasenet_thread.signal_error.connect(self.convert_error)

            # Start process
            self.phasenet_thread.start()

        except ValueError as e:
            self._show_info_bar("Input Error", f"Invalid input: {str(e)}", success=False, duration=5000)
            self._set_buttons_enabled(True)
            self.progress_bar.setVisible(False)
        except Exception as e: # Catch other potential errors during setup
            self._show_info_bar("Error", f"Failed to start process: {str(e)}", success=False, duration=5000)
            self._set_buttons_enabled(True)
            self.progress_bar.setVisible(False)

    def convert_completed(self):
        self._show_info_bar("Success", "Phasenet input generated successfully.", success=True)
        self.progress_bar.setValue(100)
        # self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)

    def convert_error(self, error_message):
        self._show_info_bar("Generation Failed", f"Error: {error_message}", success=False, duration=5000)
        self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)


        

import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QApplication, QFrame
from PyQt5.QtCore import Qt
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = waveform_download_mseed_gui()
    window.show()
    sys.exit(app.exec_())
