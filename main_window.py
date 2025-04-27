import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QAction, 
                            QTabWidget, QWidget, QVBoxLayout, QStyleFactory)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from config_gui import ConfigPage
from catalog_download import catalog_download_gui
from waveform_download_mseed_gui import waveform_download_mseed_gui
from phasenet_pick_gui import PhasenetPickGUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOC FLOW")
        self.setGeometry(100, 100, 1000, 700)  # Larger window
        
        # Set modern style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                color: #505050;
                border: 1px solid #c4c4c4;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2980b9;
                border-bottom: none;
            }
            QMenuBar {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 4px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
            QMenu {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2980b9;
                color: white;
            }
        """)
        
        # Create menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Create "Configuration" menu
        self.config_menu = QMenu("Configuration", self)
        self.menu_bar.addMenu(self.config_menu)
        
        # Add "Open Config" action to the menu
        self.open_config_action = QAction("Open Config", self)
        self.open_config_action.triggered.connect(self.open_config_page)
        self.config_menu.addAction(self.open_config_action)
        
        # Create the config page instance
        self.config_page = ConfigPage()

        # Create main tab widget
        self.main_tabs = QTabWidget(self)
        self.main_tabs.setDocumentMode(True)  # More modern look
        self.main_tabs.setIconSize(QSize(20, 20))  # Larger icons
        self.setCentralWidget(self.main_tabs)

        # Create tabs for main sections with icons (you'll need to add actual icon files)
        self.download_tab = QWidget()
        self.pick_tab = QWidget()
        self.real_tab = QWidget()
        self.locate_tab = QWidget()

        # Create layouts for each tab
        download_layout = QVBoxLayout(self.download_tab)
        download_layout.setContentsMargins(10, 15, 10, 10)
        pick_layout = QVBoxLayout(self.pick_tab)
        pick_layout.setContentsMargins(10, 15, 10, 10)
        real_layout = QVBoxLayout(self.real_tab)
        real_layout.setContentsMargins(10, 15, 10, 10)
        locate_layout = QVBoxLayout(self.locate_tab)
        locate_layout.setContentsMargins(10, 15, 10, 10)

        # Add tabs to main tab widget (with dummy icons - replace with your icon paths)
        self.main_tabs.addTab(self.download_tab, "Download")
        self.main_tabs.addTab(self.pick_tab, "Pick")
        self.main_tabs.addTab(self.real_tab, "REAL")
        self.main_tabs.addTab(self.locate_tab, "Locate")

        # Create nested tab widgets for Download
        self.download_tabs = QTabWidget()
        self.download_tabs.setDocumentMode(True)
        download_layout.addWidget(self.download_tabs)

        # Create tabs for Download section
        self.catalog_tab = QWidget()
        self.waveform_tab = QWidget()

        # Create layouts for Download subtabs
        catalog_layout = QVBoxLayout(self.catalog_tab)
        catalog_layout.setContentsMargins(8, 12, 8, 8)
        waveform_layout = QVBoxLayout(self.waveform_tab)
        waveform_layout.setContentsMargins(8, 12, 8, 8)

        # Initialize Download subtab contents
        self.catalog_download = catalog_download_gui()
        catalog_layout.addWidget(self.catalog_download)

        self.waveform_download = waveform_download_mseed_gui()
        waveform_layout.addWidget(self.waveform_download)

        # Add tabs to Download tab widget
        self.download_tabs.addTab(self.catalog_tab, "Catalog")
        self.download_tabs.addTab(self.waveform_tab, "Waveform")

        # Create nested tab widgets for Pick
        self.pick_tabs = QTabWidget()
        self.pick_tabs.setDocumentMode(True)
        pick_layout.addWidget(self.pick_tabs)

        # Create tabs for Pick section
        self.phasenet_tab = QWidget()
        self.eqtransformer_tab = QWidget()

        # Create layouts for Pick subtabs
        phasenet_layout = QVBoxLayout(self.phasenet_tab)
        phasenet_layout.setContentsMargins(8, 12, 8, 8)
        eqtransformer_layout = QVBoxLayout(self.eqtransformer_tab)
        eqtransformer_layout.setContentsMargins(8, 12, 8, 8)

        # Initialize Pick subtab contents
        self.phasenet_gui = PhasenetPickGUI()
        phasenet_layout.addWidget(self.phasenet_gui)

        # EQTransformer GUI placeholder (to be implemented)
        self.eqtransformer_widget = QWidget()
        eqtransformer_layout.addWidget(self.eqtransformer_widget)

        # Add tabs to Pick tab widget
        self.pick_tabs.addTab(self.phasenet_tab, "PhaseNet")
        self.pick_tabs.addTab(self.eqtransformer_tab, "EQTransformer")

    def open_config_page(self):
        if not self.config_page.isVisible():
            self.config_page.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))  # Modern font
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())