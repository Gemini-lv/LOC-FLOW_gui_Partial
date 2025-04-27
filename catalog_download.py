# 该页面用于下载地震目录，用pyqt5实现，只是一个子页面



"""catalog_download.py

from obspy import UTCDateTime
from obspy import read_inventory
from obspy.clients.fdsn import Client

#obspy is included in phasenet
#type 'conda activate phasenet' first
# station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
eventprovider = "INGV" # use specfic provider, e.g., IRIS, SCEDC, INGV, etc
tbeg=UTCDateTime("2016-10-14T0:00:00.00") # beginning time
tend=UTCDateTime("2016-10-15T0:00:00.00") # ending time

# file name
eventfile = 'catalog.dat'

client = Client(eventprovider)
events = client.get_events(starttime=tbeg, endtime=tend, latitude=latref, longitude=lonref, maxradius=maxradius/111.19,orderby="time-asc")
#events.plot()

with open(eventfile, "w") as f:
    for event in events:
        origin = event.origins[0]
        f.write("{} {} {} {} {}\n".format(origin.time, origin.latitude, origin.longitude, origin.depth/1000, event.magnitudes[0].mag))
f.close()

"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from PyQt5.QtCore import QThread, pyqtSignal
import os

# 使用多线程实现以上功能，避免阻塞主线程
class catalog_download_thread(QThread):
    # Signal to update the UI with progress or results
    download_finished = pyqtSignal(str)
    download_progress = pyqtSignal(str)
    download_error = pyqtSignal(str)

    def __init__(self, 
                 latref, lonref, maxradius, 
                 eventprovider, tbeg, tend, eventfile,
                 minmagnitude, parent=None):
        super().__init__(parent)
        self.latref = latref
        self.lonref = lonref
        self.maxradius = maxradius
        self.eventprovider = eventprovider
        self.tbeg = UTCDateTime(tbeg)
        self.tend = UTCDateTime(tend)
        self.eventfile = eventfile
        self.minmagnitude = minmagnitude
        self.load_config()
        self.eventfile = os.path.join(self.work_dir, 'Data', self.eventfile)  # Save to work_dir/Data directory
        
    def load_config(self):
        # config.ini
        config_file = os.path.join('./', "config.ini")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("loc_flow_path"):
                        self.loc_flow_path = line.split("=")[1].strip()
                    elif line.startswith("work_dir"):
                        self.work_dir = line.split("=")[1].strip()
        else:
            # 弹出警告框，提示用户配置文件不存在
            self.download_error.emit("Configuration file not found. Please check the path.")
            return
        # 数据将保存在self.work_dir/Data目录下
        if not os.path.exists(self.work_dir + '/Data'):
            os.makedirs(self.work_dir + '/Data', exist_ok=True)
        # 把self.eventfile保存在config.ini中

        with open(config_file, "w") as f:
            #f.write(lines)
            # 删除原有的eventfile行
            lines = [line for line in lines if not line.startswith("eventfile")]
            f.writelines(lines)
            f.write(f"\n")
            f.write(f"eventfile = {os.path.join(self.work_dir, 'Data', self.eventfile)}\n")

    def run(self):
        try:
            self.download_progress.emit("Connecting to client...")
            client = Client(self.eventprovider)
            
            self.download_progress.emit("Fetching events...")
            events = client.get_events(
                starttime=self.tbeg,
                endtime=self.tend,
                latitude=self.latref,
                longitude=self.lonref,
                maxradius=self.maxradius/111.19,
                minmagnitude=self.minmagnitude,
                orderby="time-asc"
            )
            print(self.maxradius/111.19)
            self.cat = events
            self.download_progress.emit(f"Writing {len(events)} events to file...")
            count = 0
            # 如果文件存在，先删除
            if os.path.exists(self.eventfile):
                os.remove(self.eventfile)
            with open(self.eventfile, "w") as f:
                for event in events:
                    origin = event.origins[0]
                    f.write("{} {} {} {} {}\n".format(
                        origin.time, 
                        origin.latitude, 
                        origin.longitude, 
                        origin.depth/1000, 
                        event.magnitudes[0].mag
                    ))
                    count += 1
                    if count % 10 == 0:  # Update progress every 10 events
                        self.download_progress.emit(f"Writing event {count}/{len(events)}...")
                        
            self.download_finished.emit(f"Successfully downloaded {len(events)} events to {self.eventfile}")
        except Exception as e:
            self.download_error.emit(f"Error downloading catalog: {str(e)}")

class plot_events_thread(QThread):
    
    download_error = pyqtSignal(str)
    download_finished = pyqtSignal(str)
    download_progress = pyqtSignal(str)
    def __init__(self, latref, lonref, maxradius, eventprovider, tbeg, tend, eventfile, parent=None):
        super().__init__(parent)
        self.latref = latref
        self.lonref = lonref
        self.maxradius = maxradius
        self.eventfile = eventfile
        self.tbeg = UTCDateTime(tbeg)
        self.tend = UTCDateTime(tend)
        self.eventprovider = eventprovider

    def run(self):
        try:
            self.download_progress.emit("Plotting events...")
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
            import numpy as np

            # Create a figure with a GeoAxes
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            
            # Add map features with improved styling
            ax.add_feature(cfeature.LAND, facecolor='#f2f2f2')
            ax.add_feature(cfeature.OCEAN, facecolor='#d1e5ff')
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
            ax.add_feature(cfeature.LAKES, alpha=0.7)
            ax.add_feature(cfeature.RIVERS, linewidth=0.5, alpha=0.5)
            
            # Add gridlines
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            
            # Calculate map extent based on event locations and reference point
            #lats = [event.origins[0].latitude for event in self.cat]
            #lons = [event.origins[0].longitude for event in self.cat]
            #depths = [event.origins[0].depth/1000 for event in self.cat]  # Convert to km
            #mags = [event.magnitudes[0].mag for event in self.cat]
            # 从config.ini中加载eventfile的路径
            import pandas as pd
            data = pd.read_csv(self.eventfile, sep=" ",names=["time", "latitude", "longitude", "depth", "magnitude"], header=None)
            lats = data['latitude'].tolist()
            lons = data['longitude'].tolist()
            depths = data['depth'].tolist()
            mags = data['magnitude'].tolist()


            
            # Set map extent with some padding
            buffer = max(0.5, self.maxradius/111.19 * 1.1)  # At least 2 degrees or 110% of search radius
            extent = [
                min(min(lons), self.lonref) - buffer,
                max(max(lons), self.lonref) + buffer,
                min(min(lats), self.latref) - buffer,
                max(max(lats), self.latref) + buffer
            ]
            ax.set_extent(extent, crs=ccrs.PlateCarree())
            
            # Create custom colormap for depths
            colors = ['#FF0000', '#FFA500', '#FFFF00', '#008000', '#0000FF', '#4B0082']  # Red to violet
            cmap = LinearSegmentedColormap.from_list('depth_cmap', colors)
            
            # Plot earthquakes with size proportional to magnitude and color by depth
            scatter = ax.scatter(lons, lats, 
                s=[max(5, m**3) for m in mags],  # Better scaling for visibility
                c=depths,
                cmap=cmap,
                alpha=0.7,
                edgecolor='black',
                linewidth=0.5,
                transform=ccrs.PlateCarree())
            
            # Add reference point
            ax.plot(self.lonref, self.latref, 'k*', markersize=15, transform=ccrs.PlateCarree())
            ax.text(self.lonref, self.latref, ' Reference', fontsize=10, transform=ccrs.PlateCarree())
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax, pad=0.01, shrink=0.8)
            cbar.set_label('Depth (km)', rotation=270, labelpad=20)
            
            # Add a circle showing the search radius
            theta = np.linspace(0, 2*np.pi, 100)
            radius = self.maxradius/111.19  # Convert km to degrees
            circle_lons = self.lonref + radius * np.cos(theta)
            circle_lats = self.latref + radius * np.sin(theta)
            ax.plot(circle_lons, circle_lats, 'k--', linewidth=1.5, alpha=0.7, transform=ccrs.PlateCarree())
            
            # Title and labels
            title_str = f"Earthquake Catalog: {self.tbeg.strftime('%Y-%m-%d')} to {self.tend.strftime('%Y-%m-%d')}"
            ax.set_title(title_str, fontsize=16, fontweight='bold')
            
            # Add legend for magnitude scale
            for m in [3, 4, 5]:
                plt.scatter([], [], s=m**3, c='gray', alpha=0.7, edgecolor='black',
                    linewidth=0.5, label=f'M{m}')
            plt.legend(scatterpoints=1, frameon=True, labelspacing=1, title='Magnitude')
            
            # Add source information
            #plt.figtext(0.02, 0.02, f"Data Source: {self.eventprovider}", fontsize=8)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.eventfile.replace('.dat', '.png')), dpi=300)
            plt.close()
            self.download_finished.emit("Plotting completed. Map saved as map.png")
        
        except Exception as e:
            print(f"Error plotting events: {str(e)}")
            self.download_error.emit(f"Error plotting events: {str(e)}")

from PyQt5.QtWidgets import QWidget, QVBoxLayout,QFormLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QHBoxLayout,    QCheckBox
class catalog_download_gui(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create input fields for parameters
        self.latref_input = QLineEdit()
        self.lonref_input = QLineEdit()
        self.maxradius_input = QLineEdit()
        self.eventprovider_input = QLineEdit()
        self.tbeg_input = QLineEdit()
        self.tend_input = QLineEdit()
        self.eventfile_input = QLineEdit()
        self.minmagnitude_input = QLineEdit()

        # Create a button to start the download
        self.download_button = QPushButton("Download Catalog")
        # Create progress display
        self.progress_label = QLabel("Ready to download")
        self.status_label = QLabel("")

        # Set default values
        self.latref_input.setText("42.75")
        self.lonref_input.setText("13.25")
        self.maxradius_input.setText("50")
        self.eventprovider_input.setText("USGS")
        self.tbeg_input.setText("2016-10-14T0:00:00.00")
        self.tend_input.setText("2016-11-15T0:00:00.00")
        self.eventfile_input.setText("catalog.dat")
        self.minmagnitude_input.setText("0")
        
        
        # Create form layout
        form_layout = QFormLayout()
        form_layout.addRow("Latitude (reference):", self.latref_input)
        form_layout.addRow("Longitude (reference):", self.lonref_input)
        form_layout.addRow("Max Radius (km):", self.maxradius_input)
        form_layout.addRow("Event Provider:", self.eventprovider_input)
        form_layout.addRow("Start Time:", self.tbeg_input)
        form_layout.addRow("End Time:", self.tend_input)
        form_layout.addRow("Min Magnitude:", self.minmagnitude_input)
        
        # Add file selection with browse button
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.eventfile_input)
        #file_layout.addWidget(self.browse_button)
        form_layout.addRow("Output Filename:", file_layout)

        # 增加一个画图勾选框，默认不勾选
        self.plot_checkbox = QCheckBox("Plot Events")
        form_layout.addRow(self.plot_checkbox)
        
        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.download_button)
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.download_button.clicked.connect(self.start_download)
        #self.browse_button.clicked.connect(self.browse_file)
        
    def start_download(self):
        # Disable button during download
        self.download_button.setEnabled(False)
        self.status_label.setText("")
        
        try:
            # Get parameters from input fields
            latref = float(self.latref_input.text())
            lonref = float(self.lonref_input.text())
            maxradius = float(self.maxradius_input.text())
            eventprovider = self.eventprovider_input.text().strip()
            tbeg = self.tbeg_input.text().strip()
            tend = self.tend_input.text().strip()
            eventfile = self.eventfile_input.text().strip()
            minmagnitude = float(self.minmagnitude_input.text())
            
            # Create and start download thread
            self.download_thread = catalog_download_thread(
            latref, lonref, maxradius, eventprovider,
            tbeg, tend, eventfile,minmagnitude
            )
            
            # Connect thread signals
            self.download_thread.download_progress.connect(self.progress_label.setText)
            self.download_thread.download_finished.connect(self.download_completed)
            self.download_thread.download_error.connect(self.download_error)
            
            # Start download
            self.download_thread.start()
            
        except ValueError as e:
            self.status_label.setText(f"Invalid input: {str(e)}")
            self.download_button.setEnabled(True)
            
    def download_completed(self, message):
        self.status_label.setText(message)
        self.progress_label.setText("Download complete")
        if self.plot_checkbox.isChecked():
            self.plot_events_thread = plot_events_thread(
                float(self.latref_input.text()),
                float(self.lonref_input.text()),
                float(self.maxradius_input.text()),
                self.eventprovider_input.text().strip(),
                self.tbeg_input.text().strip(),
                self.tend_input.text().strip(),
                self.download_thread.eventfile,
            )

            self.plot_events_thread.start()
            self.progress_label.setText("Plotting events...")
            self.plot_events_thread.download_error.connect(self.download_error)
            self.plot_events_thread.download_finished.connect(self.plot_completed)
            self.plot_events_thread.download_progress.connect(self.progress_label.setText)
        else:
            self.download_button.setEnabled(True)
        
    def download_error(self, error_message):
        self.status_label.setText(error_message)
        self.progress_label.setText("Download failed")
        self.download_button.setEnabled(True)

    def plot_completed(self, message):
        self.status_label.setText(message)
        self.progress_label.setText("Plotting complete")
        self.download_button.setEnabled(True)
        # 弹出图像窗口
        from matplotlib import pyplot as plt
        img = plt.imread(self.download_thread.eventfile.replace('.dat', '.png'))
        plt.imshow(img)
        plt.axis('off')
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = catalog_download_gui()
    window.setWindowTitle("Catalog Download")
    window.show()
    sys.exit(app.exec_())