# control_widget.py
import ctypes
import numpy as np
import datetime
import logging

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QSignalBlocker
from PyQt5.QtGui import QImage, QColor

from PyQt5.QtWidgets import (
    QLabel, QApplication, QCheckBox, QMessageBox, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QGridLayout, QHBoxLayout, QVBoxLayout, QMenu, QAction,
    QFileDialog, QSpinBox
)

from qt_material import apply_stylesheet
import qtawesome as qta
from astropy.io import fits

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import nncam.nncam as nncam

# Import auxiliary classes
from utils.utils import log_exceptions
from widgets.collapsible_box import CollapsibleBox
from widgets.preview_label import PreviewLabel
from widgets.preview_window import PreviewWindow

from widgets.circular_progress import CircularProgress

plt.style.use('dark_background')


class ControlWidget(QtWidgets.QWidget):
    """
    Main control widget for the camera: opens/closes the camera,
    manages image capture (Snap/Trigger), exposure, gain,
    file saving, histograms, etc.
    """
    evtCallback = pyqtSignal(int)
    
    @log_exceptions
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumSize(1024, 720)
        
        # Camera attributes
        self.hcam = None
        self.timer = QTimer(self)
        self.imgWidth = 0
        self.imgHeight = 0
        self.pData = None
        self.res = 0
        self.count = 0
        self.currentPreviewImage = None
        self.bitdepth = 12
        self.save_capture = False
        self.trigger_remaining = 0
        self.manual_exposure = None
        self.manual_gain = None
        self.previewWindow = None
        # Initial text color
        self.text_color = "#FD3A4A"
        
        # Apply qt_material style
        apply_stylesheet(QApplication.instance(), theme='dark_purple.xml')
        self.updateCustomStyleSheet()
        
        # --- Collapsible Boxes ---
        cameraBox = CollapsibleBox("Camera Settings")
        
        # Resolution
        gboxres = QGroupBox("Resolution")
        self.cmb_res = QComboBox()
        self.cmb_res.setEnabled(False)
        self.cmb_res.currentIndexChanged.connect(self.onResolutionChanged)
        
        vlytres = QVBoxLayout()
        vlytres.addWidget(self.cmb_res)
        gboxres.setLayout(vlytres)
        
        # Exposure
        gboxexp = QGroupBox("Image Control")
        self.cbox_auto = QCheckBox("Auto exposure")
        self.cbox_auto.setEnabled(False)
        
        self.spin_expoTime = QSpinBox()
        self.spin_expoTime.setEnabled(False)
        self.spin_expoTime.setKeyboardTracking(False)
        
        self.spin_expoGain = QSpinBox()
        self.spin_expoGain.setEnabled(False)
        self.spin_expoGain.setKeyboardTracking(False)
        
        self.cbox_auto.stateChanged.connect(self.onAutoExpo)
        self.spin_expoTime.valueChanged.connect(self.onExpoTimeValueChanged)
        self.spin_expoGain.valueChanged.connect(self.onExpoGainValueChanged)
        
        self.lblCameraSpecs = QLabel("Camera Specs: Not available")
        self.btn_openPreview = QtWidgets.QPushButton("Open Preview Window")
        # Initialize flip flags
        self.flip_x = False
        self.flip_y = False

        # Create buttons for horizontal and vertical flip
        self.btn_flipX = QtWidgets.QPushButton("Flip X")
        self.btn_flipY = QtWidgets.QPushButton("Flip Y")

        # Connect the flip buttons to their functions
        self.btn_flipX.clicked.connect(self.toggleFlipX)
        self.btn_flipY.clicked.connect(self.toggleFlipY)
        
        expLayout = QHBoxLayout()
        expLayout.addWidget(QLabel("Time(us):"))
        expLayout.addWidget(self.spin_expoTime)
        expLayout.addSpacing(20)
        expLayout.addWidget(QLabel("Gain(%):"))
        expLayout.addWidget(self.spin_expoGain)
        
        vlytexp = QVBoxLayout()
        vlytexp.addWidget(self.cbox_auto)
        vlytexp.addLayout(expLayout)
        vlytexp.addWidget(self.lblCameraSpecs)
        vlytexp.addWidget(self.btn_flipX)
        vlytexp.addWidget(self.btn_flipY)
        
        gboxexp.setLayout(vlytexp)
        
        # Camera buttons (Turn On, Snap, Trigger)
        self.btn_open = QPushButton("Turn On Camera")
        self.btn_open.clicked.connect(self.onBtnOpen)
        
        self.btn_snap = QPushButton("Snap")
        self.btn_snap.setEnabled(False)
        self.btn_snap.clicked.connect(self.onBtnSnap)
        
        self.btn_trigger = QPushButton("Trigger")
        self.btn_trigger.setEnabled(False)
        self.btn_trigger.clicked.connect(self.onBtnTrigger)
        
        # Checkboxes for save formats
        self.cbox_save_jpeg = QCheckBox("Save JPEG")
        self.cbox_save_jpeg.setChecked(True)
        
        self.cbox_save_raw = QCheckBox("Save RAW")
        self.cbox_save_raw.setChecked(True)
        
        self.cbox_save_fits = QCheckBox("Save FITS")
        self.cbox_save_fits.setChecked(True)
        
        # SpinBox for trigger count
        self.spin_trigger_count = QSpinBox()
        self.spin_trigger_count.setMinimum(1)
        self.spin_trigger_count.setMaximum(100)
        self.spin_trigger_count.setValue(1)
        
        # Circular progress bar
        self.circularProgress = CircularProgress()
        self.circularProgress.setMaximum(self.spin_trigger_count.value())
        self.circularProgress.setValue(0)
        
        # Layout for camera buttons
        layout0 = QVBoxLayout()
        layout0.addWidget(self.btn_open)
        
        layout1 = QHBoxLayout()
        layout1.addWidget(self.btn_snap)
        layout1.addWidget(self.btn_trigger)
        layout1.addWidget(QLabel("Trigger Count:"))
        layout1.addWidget(self.spin_trigger_count)
        layout1.addWidget(self.circularProgress)
        
        layout_control = QVBoxLayout()
        layout_control.addLayout(layout0)
        layout_control.addLayout(layout1)

        saveOptionsLayout = QHBoxLayout()
        saveOptionsLayout.addWidget(self.cbox_save_jpeg)
        saveOptionsLayout.addWidget(self.cbox_save_raw)
        saveOptionsLayout.addWidget(self.cbox_save_fits)
        
        layout3 = QVBoxLayout()
        layout3.addLayout(layout1)
        layout3.addLayout(saveOptionsLayout)
        
        camLayout = QVBoxLayout()
        camLayout.addWidget(gboxres)
        camLayout.addWidget(gboxexp)
        camLayout.addLayout(layout_control)
        camLayout.addLayout(layout3)
        cameraBox.addLayout(camLayout)
        
        # -- File Settings --
        from qtawesome import icon as qta_icon
        
        fileBox = CollapsibleBox("File Settings")
        
        self.le_file_prefix = QLineEdit("photsat_ehd_")
        lbl_prefix = QLabel("Label:")
        
        self.le_directory = QLineEdit(".")
        lbl_dir = QLabel("Directory:")
        
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.onBrowseDirectory)
        btn_browse.setIcon(qta_icon('mdi.folder', color='white'))
        
        self.btn_openDirectory = QPushButton("Open Directory")
        self.btn_openDirectory.setIcon(qta_icon('mdi.folder-open', color='white'))
        self.btn_openDirectory.clicked.connect(self.openLastImagesDirectory)
        
        fileLayout = QVBoxLayout()
        fileLayout.addWidget(lbl_prefix)
        fileLayout.addWidget(self.le_file_prefix)
        fileLayout.addSpacing(10)
        fileLayout.addWidget(lbl_dir)
        fileLayout.addWidget(self.le_directory)
        fileLayout.addWidget(btn_browse)
        fileLayout.addWidget(self.btn_openDirectory)
        
        fileBox.addLayout(fileLayout)
        
        # -- Theme Settings --
        themeBox = CollapsibleBox("Theme Settings")
        self.themeCombo = QComboBox()
        self.themeCombo.addItems(["dark_purple.xml", "dark_blue.xml", "light_blue.xml", "light_red.xml", "dark_red.xml"])
        
        self.btn_applyTheme = QPushButton("Apply Theme")
        self.btn_applyTheme.clicked.connect(self.onApplyTheme)
        
        self.textColorButton = QPushButton("Select Text Color")
        self.textColorButton.clicked.connect(self.onSelectTextColor)
        
        themeLayout = QHBoxLayout()
        themeLayout.addWidget(QLabel("Theme:"))
        themeLayout.addWidget(self.themeCombo)
        themeLayout.addWidget(self.btn_applyTheme)
        themeLayout.addWidget(self.textColorButton)
        
        themeBox.addLayout(themeLayout)
        
        # Left panel
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(fileBox)
        leftLayout.addWidget(cameraBox)
        leftLayout.addWidget(themeBox)
        leftLayout.addStretch()
        
        wgctrl = QtWidgets.QWidget()
        wgctrl.setLayout(leftLayout)
        
        # Right panel (Preview and Histograms/Macro)
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        
        self.lbl_video = PreviewLabel(self)
        self.lbl_video.setMinimumSize(640, 480)
        self.lbl_video.mouseMoved.connect(self.updatePixelCount)
        
        self.lbl_pixel_info = QLabel("Pixel info:")
        self.btn_openPreview.clicked.connect(self.openPreviewWindow)
        
        # Histogram
        self.figure = Figure(figsize=(4, 3))
        self.ax_hist = self.figure.add_subplot(111)
        self.canvas_hist = FigureCanvas(self.figure)
        
        # Histogram tab
        from PyQt5.QtWidgets import QWidget, QTabWidget, QScrollArea
        histTab = QWidget()
        histLayout = QVBoxLayout()
        histLayout.addWidget(self.canvas_hist)
        histTab.setLayout(histLayout)
        
        # Macro tab (loaded from macro_widget.py)
        from widgets.macro_widget import MacroModeWidget
        self.macroWidget = MacroModeWidget(self)
        
        macroScrollArea = QScrollArea()
        macroScrollArea.setWidgetResizable(True)
        macroScrollArea.setWidget(self.macroWidget)
        macroScrollArea.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        macroTab = QWidget()
        macroLayout = QVBoxLayout()
        macroLayout.addWidget(macroScrollArea)
        macroTab.setLayout(macroLayout)
        
        # QTabWidget containing both tabs
        self.rightTab = QTabWidget()
        self.rightTab.addTab(histTab, "Histogram")
        self.rightTab.addTab(macroTab, "Macro")
        
        vlytshow = QVBoxLayout()
        vlytshow.addWidget(self.btn_openPreview)
        vlytshow.addWidget(self.lbl_pixel_info)
        vlytshow.addWidget(self.lbl_video, 3)
        vlytshow.addWidget(self.rightTab, 2)
        
        self.lbl_frame = QLabel()
        vlytshow.addWidget(self.lbl_frame)
        
        wgshow = QWidget()
        wgshow.setLayout(vlytshow)
        
        # Main layout
        gmain = QGridLayout()
        gmain.setColumnStretch(0, 1)
        gmain.setColumnStretch(1, 4)
        gmain.addWidget(wgctrl, 0, 0)
        gmain.addWidget(wgshow, 0, 1)
        
        self.setLayout(gmain)
        
        # Icons (qtawesome)
        self.btn_open.setIcon(qta.icon('mdi.play', color='white'))
        self.btn_snap.setIcon(qta.icon('mdi.image-area', color='white'))
        self.btn_trigger.setIcon(qta.icon('mdi.image-multiple', color='white'))
        
        self.timer.timeout.connect(self.onTimer)
        self.evtCallback.connect(self.onevtCallback)
        
        self.trigger_remaining = 0
        self.save_capture = False

    def toggleFlipX(self):
        """Toggle horizontal flip (X)."""
        self.flip_x = not self.flip_x
        # Optionally update the button text or visual state
        logging.info("Flip X toggled: %s", self.flip_x)

    def toggleFlipY(self):
        """Toggle vertical flip (Y)."""
        self.flip_y = not self.flip_y
        logging.info("Flip Y toggled: %s", self.flip_y)

    def openPreviewWindow(self):
        """
        Opens the independent preview window.
        If it already exists, bring it to focus.
        """
        if not hasattr(self, "previewWindow") or self.previewWindow is None:
            self.previewWindow = PreviewWindow(self)
        self.previewWindow.show()
        self.previewWindow.raise_()  # Optional: bring to front

    def updateCustomStyleSheet(self):
        """
        Applies a custom stylesheet based on self.text_color.
        """
        style = f"""
            QWidget {{
                font-family: 'Roboto', sans-serif;
                color: {self.text_color};
                font-weight: bold;
            }}
        """
        self.setStyleSheet(style)

    @log_exceptions
    def onSelectTextColor(self, checked=False):
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(self.text_color), self, "Select Text Color")
        if color.isValid():
            self.text_color = color.name()
            self.updateCustomStyleSheet()

    @log_exceptions
    def onApplyTheme(self, checked=False):
        theme = self.themeCombo.currentText()
        app = QApplication.instance()
        apply_stylesheet(app, theme=theme)
        self.updateCustomStyleSheet()
    
    @log_exceptions
    def openLastImagesDirectory(self, checked=False):
        from PyQt5.QtCore import QUrl
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtGui import QDesktopServices
        
        directory = self.le_directory.text().strip()
        if directory:
            QDesktopServices.openUrl(QUrl.fromLocalFile(directory))
        else:
            QMessageBox.warning(self, "Warning", "Directory Undefined.")
    
    @log_exceptions
    def onExpoTimeValueChanged(self, value):
        """
        Handles the change in exposure (SpinBox).
        """
        if self.hcam and not self.cbox_auto.isChecked():
            try:
                self.hcam.put_ExpoTime(value)
                self.manual_exposure = value
            except nncam.HRESULTException as e:
                QMessageBox.warning(self, "Error", f"Failed to set exposure time: {e}")
    
    @log_exceptions
    def onExpoGainValueChanged(self, value):
        """
        Handles the change in gain (SpinBox).
        """
        if self.hcam and not self.cbox_auto.isChecked():
            try:
                self.hcam.put_ExpoAGain(value)
                self.manual_gain = value
            except nncam.HRESULTException as e:
                QMessageBox.warning(self, "Error", f"Failed to set gain: {e}")
    
    @log_exceptions
    def onBrowseDirectory(self, checked=False):
        """
        Opens a QFileDialog to choose the directory for saving captures.
        """
        directory = QFileDialog.getExistingDirectory(self, "Choose the Directory", self.le_directory.text())
        if directory:
            self.le_directory.setText(directory)
    
    @log_exceptions
    def onTimer(self):
        """
        Called periodically to update information such as FPS, temperature, etc.
        """
        if self.hcam:
            nFrame, nTime, nTotalFrame = self.hcam.get_FrameRate()
            expotime = self.hcam.get_ExpoTime() / 1e6
            temperature = self.hcam.get_Temperature() / 10
            fps = 1 / expotime if expotime != 0 else 0
            self.lbl_frame.setText(
                f"Frame:       {nTotalFrame}\n"
                f"FPS:         {fps:.6f}\n"
                f"Temperature: {temperature:.2f} ºC\n"
                f"Expo Time:   {expotime:.6f} s\n"
                f"Clock:       {nTime:.0f} us"
            )
    
    @log_exceptions
    def closeCamera(self):
        """
        Closes the camera (if open) and disables controls.
        """
        if self.hcam:
            self.hcam.Close()
        self.hcam = None
        self.pData = None
        self.btn_open.setText("Turn On Camera")
        self.timer.stop()
        self.lbl_frame.clear()
        self.cbox_auto.setEnabled(False)
        self.spin_expoTime.setEnabled(False)
        self.spin_expoGain.setEnabled(False)
        self.btn_snap.setEnabled(False)
        self.btn_trigger.setEnabled(False)
        self.cmb_res.setEnabled(False)
        self.cmb_res.clear()
    
    def closeEvent(self, event):
        """
        Window close event: closes the camera before exiting.
        """
        self.closeCamera()
    
    @log_exceptions
    def onResolutionChanged(self, index):
        """
        Changes the camera resolution when another mode is selected in the combo box.
        """
        if self.hcam:
            self.hcam.Stop()
        self.res = index
        self.imgWidth = self.cur.model.res[index].width
        self.imgHeight = self.cur.model.res[index].height
        
        if self.hcam:
            self.hcam.put_eSize(self.res)
            buffer_size = nncam.TDIBWIDTHBYTES(self.imgWidth * self.bitdepth) * self.imgHeight
            self.pData = ctypes.create_string_buffer(buffer_size)
            self.startCamera()
            self.updateCameraSpecs()
    
    @log_exceptions
    def onAutoExpo(self, state):
        """
        Enables/disables automatic exposure in the camera.
        """
        if self.hcam:
            self.hcam.put_AutoExpoEnable(1 if state else 0)
    
    @log_exceptions
    def startCamera(self):
        """
        Starts the camera in pull mode with a callback (PullMode).
        """
        self.hcam.put_Option(nncam.NNCAM_OPTION_RAW, 1)
        try:
            self.bitdepth = self.hcam.MaxBitDepth()
        except Exception:
            self.bitdepth = 16
        
        self.hcam.put_Option(nncam.NNCAM_OPTION_BITDEPTH, self.bitdepth)
        self.hcam.put_Option(nncam.NNCAM_OPTION_TRIGGER, 0)  # Disables hardware trigger mode, if available
        
        buffer_size = nncam.TDIBWIDTHBYTES(self.imgWidth * self.bitdepth) * self.imgHeight
        self.pData = ctypes.create_string_buffer(buffer_size)
        
        uimin, uimax, uidef = self.hcam.get_ExpTimeRange()
        self.spin_expoTime.setRange(uimin, uimax)
        self.spin_expoTime.setValue(uidef)
        self.manual_exposure = uidef
        
        gmin, gmax, gdef = self.hcam.get_ExpoAGainRange()
        self.spin_expoGain.setRange(gmin, gmax)
        self.spin_expoGain.setValue(gdef)
        self.manual_gain = gdef
        
        self.handleExpoEvent()
        
        try:
            self.hcam.StartPullModeWithCallback(self.eventCallBack, self)
        except nncam.HRESULTException:
            self.closeCamera()
            QMessageBox.warning(self, "Warning", "Failed to start camera.")
        else:
            self.cmb_res.setEnabled(True)
            self.cbox_auto.setEnabled(True)
            self.btn_open.setText(f"Turn Off Camera: {self.cur.displayname}")
            self.btn_snap.setEnabled(True)
            self.btn_trigger.setEnabled(True)
            
            bAuto = self.hcam.get_AutoExpoEnable()
            self.cbox_auto.setChecked(1 == bAuto)
        
        self.timer.start(1000)
    
    @log_exceptions
    def openCamera(self):
        """
        Opens the camera enumerated in self.cur, configures it, and starts capturing.
        """
        self.hcam = nncam.Nncam.Open(self.cur.id)
        if self.hcam:
            self.res = self.hcam.get_eSize()
            self.imgWidth = self.cur.model.res[self.res].width
            self.imgHeight = self.cur.model.res[self.res].height
            
            with QSignalBlocker(self.cmb_res):
                self.cmb_res.clear()
                for i in range(0, self.cur.model.preview):
                    self.cmb_res.addItem("{}*{}".format(self.cur.model.res[i].width, self.cur.model.res[i].height))
                self.cmb_res.setCurrentIndex(self.res)
                self.cmb_res.setEnabled(True)
            
            self.spin_expoTime.setEnabled(True)
            self.spin_expoGain.setEnabled(True)
            self.hcam.put_AutoExpoEnable(0)
            
            self.startCamera()
            self.updateCameraSpecs()
    
    @log_exceptions
    def updateCameraSpecs(self):
        """
        Displays the exposure and gain range in the lblCameraSpecs label.
        """
        try:
            exp_min, exp_max, exp_def = self.hcam.get_ExpTimeRange()
            gain_min, gain_max, gain_def = self.hcam.get_ExpoAGainRange()
            text = (f"Exposure range: {exp_min} - {exp_max} µs (default: {exp_def})\n"
                    f"Gain range: {gain_min} - {gain_max} (default: {gain_def})")
            self.lblCameraSpecs.setText(text)
        except Exception as e:
            logging.exception("Error updating camera specs")
            self.lblCameraSpecs.setText("Camera specs not available")
    
    @log_exceptions
    def onBtnOpen(self, checked=False):
        """
        Button to open/close the camera. If it is already open, it closes it; otherwise, it searches the enumeration.
        """
        if self.hcam:
            self.closeCamera()
        else:
            arr = nncam.Nncam.EnumV2()
            if len(arr) == 0:
                print("check")
                #QMessageBox.warning(self, "Warning", "No camera found.")
            elif len(arr) == 1:
                self.cur = arr[0]
                self.openCamera()
            else:
                menu = QMenu()
                for i in range(len(arr)):
                    action = QAction(arr[i].displayname, self)
                    action.setData(i)
                    menu.addAction(action)
                
                action = menu.exec(self.mapToGlobal(self.btn_open.pos()))
                if action:
                    self.cur = arr[action.data()]
                    self.openCamera()
    
    @log_exceptions
    def onBtnSnap(self, checked=False):
        """
        Performs a single capture (Snap). 
        If the camera does not support still mode, the image from the current buffer is saved.
        Otherwise, a Snap command is issued to the camera.
        """
        if self.hcam:
            if self.cur.model.still == 0:
                # Non-still mode: save what is in pData
                if self.pData is not None:
                    img_format = QImage.Format_Grayscale16 if self.bitdepth > 8 else QImage.Format_Grayscale8
                    bytesPerLine = nncam.TDIBWIDTHBYTES(self.imgWidth * self.bitdepth)
                    image = QImage(self.pData, self.imgWidth, self.imgHeight, bytesPerLine, img_format)
                    self.count += 1
                    
                    if self.cbox_save_jpeg.isChecked():
                        image.save(f"pyqt{self.count}.jpg")
                    
                    if self.cbox_save_raw.isChecked():
                        with open(f"pyqt{self.count}_raw.raw", "wb") as f:
                            f.write(self.pData)
                    
                    if self.cbox_save_fits.isChecked():
                        dtype = np.uint16 if self.bitdepth > 8 else np.uint8
                        raw_arr = np.frombuffer(self.pData, dtype=dtype)
                        stride = nncam.TDIBWIDTHBYTES(self.imgWidth * self.bitdepth)
                        elems_per_row = stride // (self.bitdepth // 8)
                        raw_arr = raw_arr.reshape((self.imgHeight, elems_per_row))
                        raw_image = raw_arr[:, :self.imgWidth]
                        self.saveFitsImage(raw_image)
            else:
                # Still mode: request the camera to Snap
                self.save_capture = True
                if self.cbox_save_jpeg.isChecked():
                    self.hcam.Snap(self.res)
    
    @log_exceptions
    def onBtnTrigger(self, checked=False):
        """
        Button to perform multiple captures (trigger_count).
        """
        if self.hcam:
            self.configureTrigger()
    
    @log_exceptions
    def configureTrigger(self):
        """
        Starts a series of sequential captures based on the value of spin_trigger_count.
        """
        self.trigger_remaining = self.spin_trigger_count.value()
        self.circularProgress.setMaximum(self.trigger_remaining)
        self.circularProgress.setValue(0)
        self.save_capture = True
        self.startSoftwareTriggerCapture()
    
    @log_exceptions
    def startSoftwareTriggerCapture(self):
        """
        Starts (or continues) the 'triggered' captures until trigger_remaining is exhausted.
        """
        if self.trigger_remaining > 0:
            try:
                self.onBtnSnap()
            except Exception as e:
                logging.exception("Error during trigger capture")
                QMessageBox.warning(self, "Error", f"Error capturing image: {e}")
            
            self.trigger_remaining -= 1
            completed = self.spin_trigger_count.value() - self.trigger_remaining
            self.circularProgress.setValue(completed)
            
            QTimer.singleShot(self.manual_exposure // 1000 + 100, self.startSoftwareTriggerCapture)
        else:
            self.save_capture = False
    
    @staticmethod
    @log_exceptions
    def eventCallBack(nEvent, self):
        """
        Static callback that re-emits the event via self.evtCallback.
        """
        self.evtCallback.emit(nEvent)
    
    @log_exceptions
    def onevtCallback(self, nEvent):
        """
        Handles the camera events received via the callback.
        """
        if self.hcam:
            if nncam.NNCAM_EVENT_IMAGE == nEvent:
                self.handleImageEvent()
            elif nncam.NNCAM_EVENT_EXPOSURE == nEvent:
                self.handleExpoEvent()
            elif nncam.NNCAM_EVENT_STILLIMAGE == nEvent:
                self.handleStillImageEvent()
            elif nncam.NNCAM_EVENT_ERROR == nEvent:
                self.closeCamera()
                QMessageBox.warning(self, "Warning", "Generic Error.")
            elif nncam.NNCAM_EVENT_DISCONNECTED == nEvent:
                self.closeCamera()
                QMessageBox.warning(self, "Warning", "Camera disconnect.")
    
    @log_exceptions
    def handleImageEvent(self):
        """
        Extracts the image from the buffer in Pull mode and displays it in lbl_video;
        additionally, if save_capture is active, saves it (FITS).
        """
        try:
            self.hcam.PullImageV4(self.pData, 0, self.bitdepth, 0, None)
        except nncam.HRESULTException:
            pass
        else:
            dtype = np.uint16 if self.bitdepth > 8 else np.uint8
            raw_arr = np.frombuffer(self.pData, dtype=dtype)
            
            stride = nncam.TDIBWIDTHBYTES(self.imgWidth * self.bitdepth)
            elems_per_row = stride // (self.bitdepth // 8)
            raw_arr = raw_arr.reshape((self.imgHeight, elems_per_row))
            
            raw_image = raw_arr[:, :self.imgWidth]
            self.lastRawImage = raw_image.copy()
            
            # Convert to 8-bit for preview
            if self.bitdepth > 8:
                preview_arr = (raw_image.astype(np.float32) / (2**self.bitdepth - 1) * 255).astype(np.uint8)
            else:
                preview_arr = raw_image
            
            image_preview = QImage(preview_arr.data, self.imgWidth, self.imgHeight,
                        self.imgWidth, QImage.Format_Grayscale8)
            newimage = image_preview.scaled(self.lbl_video.width(), self.lbl_video.height(), Qt.KeepAspectRatio, Qt.FastTransformation)

            # Apply flip based on the flags
            if self.flip_x or self.flip_y:
                # The mirrored() function takes two booleans: (horizontal, vertical)
                newimage = newimage.mirrored(self.flip_x, self.flip_y)

            self.currentPreviewImage = newimage
            self.lbl_video.setPixmap(QtGui.QPixmap.fromImage(newimage))

            # If the independent preview window is open, update it as well
            if self.previewWindow is not None:
                self.previewWindow.setImage(newimage)
            
            self.updateHistogramRaw(raw_image)
            self.updatePixelCount()
            
            if self.save_capture and self.cbox_save_fits.isChecked():
                self.count += 1
                self.saveFitsImage(raw_image)
                self.trigger_remaining -= 1
                if self.trigger_remaining > 0:
                    try:
                        self.hcam.TriggerSoftware()
                    except Exception as e:
                        logging.exception("Error executing TriggerSoftware")
                        #QMessageBox.warning(self, "Error", f"Error triggering: {e}")
                else:
                    self.save_capture = False
    
    @log_exceptions
    def handleExpoEvent(self):
        """
        When the camera notifies a change in exposure (e.g., when auto exposure is active),
        synchronizes the controls (spin_expoTime, spin_expoGain).
        """
        if self.hcam:
            if self.cbox_auto.isChecked():
                time_val = self.hcam.get_ExpoTime()
                if not self.spin_expoTime.hasFocus():
                    self.spin_expoTime.blockSignals(True)
                    self.spin_expoTime.setValue(time_val)
                    self.spin_expoTime.blockSignals(False)
                
                gain_val = self.hcam.get_ExpoAGain()
                if not self.spin_expoGain.hasFocus():
                    self.spin_expoGain.blockSignals(True)
                    self.spin_expoGain.setValue(gain_val)
                    self.spin_expoGain.blockSignals(False)
                
                self.manual_exposure = time_val
                self.manual_gain = gain_val
            else:
                # If auto is not active, restore the manual values
                if self.manual_exposure is not None and not self.spin_expoTime.hasFocus():
                    self.spin_expoTime.blockSignals(True)
                    self.spin_expoTime.setValue(self.manual_exposure)
                    self.spin_expoTime.blockSignals(False)
                
                if self.manual_gain is not None and not self.spin_expoGain.hasFocus():
                    self.spin_expoGain.blockSignals(True)
                    self.spin_expoGain.setValue(self.manual_gain)
                    self.spin_expoGain.blockSignals(False)
    
    @log_exceptions
    def handleStillImageEvent(self):
        """
        When a still image is received, extracts it and saves it to disk.
        """
        info = nncam.NncamFrameInfoV3()
        try:
            self.hcam.PullImageV3(None, 1, self.bitdepth, 0, info)
        except nncam.HRESULTException:
            pass
        else:
            if info.width > 0 and info.height > 0:
                bytesPerLine = nncam.TDIBWIDTHBYTES(info.width * self.bitdepth)
                buffer_size = bytesPerLine * info.height
                buf = ctypes.create_string_buffer(buffer_size)
                
                try:
                    self.hcam.PullImageV3(buf, 1, self.bitdepth, 0, info)
                except nncam.HRESULTException:
                    pass
                else:
                    img_format = QImage.Format_Grayscale16 if self.bitdepth > 8 else QImage.Format_Grayscale8
                    image = QImage(buf, info.width, info.height, bytesPerLine, img_format)
                    
                    self.count += 1
                    # Save to disk
                    if self.cbox_save_jpeg.isChecked():
                        self.saveJPEGImage(image)
                    if self.cbox_save_raw.isChecked():
                        self.saveRAWImage(buf)
                    if self.cbox_save_fits.isChecked():
                        dtype = np.uint16 if self.bitdepth > 8 else np.uint8
                        raw_arr = np.frombuffer(buf, dtype=dtype)
                        stride = nncam.TDIBWIDTHBYTES(info.width * self.bitdepth)
                        elems_per_row = stride // (self.bitdepth // 8)
                        raw_arr = raw_arr.reshape((info.height, elems_per_row))
                        raw_image = raw_arr[:, :info.width]
                        self.saveFitsImage(raw_image)
                    
                    self.save_capture = False
    
    @log_exceptions
    def saveJPEGImage(self, image: QImage):
        """
        Saves the image in JPEG format in the directory with the configured prefix.
        """
        jpeg_filename = f"{self.le_directory.text().strip()}/{self.le_file_prefix.text().strip()}{self.count}.jpg"
        image.save(jpeg_filename)
    
    @log_exceptions
    def saveRAWImage(self, raw_image):
        """
        Saves the RAW buffer to a .raw file.
        """
        raw_filename = f"{self.le_directory.text().strip()}/{self.le_file_prefix.text().strip()}{self.count}.raw"
        with open(raw_filename, "wb") as f:
            f.write(raw_image)
    
    @log_exceptions
    def saveFitsImage(self, raw_image: np.ndarray):
        """
        Saves the image in FITS format, including metadata such as exposure, gain, temperature, etc.
        """
        hdr = fits.Header()
        if self.manual_exposure is not None:
            hdr['EXPTIME'] = (self.manual_exposure / 1e6, "Exposure time in seconds")
        else:
            try:
                hdr['EXPTIME'] = (self.hcam.get_ExpoTime() / 1e6, "Exposure time in seconds")
            except:
                hdr['EXPTIME'] = ('N/A', "Exposure time in seconds")
        
        if self.manual_gain is not None:
            hdr['GAIN'] = (self.manual_gain, "Gain in percentage")
        else:
            try:
                hdr['GAIN'] = self.hcam.get_ExpoAGain()
            except:
                hdr['GAIN'] = 'N/A'
        
        try:
            hdr['TEMP'] = self.hcam.get_Temperature() / 10
        except:
            hdr['TEMP'] = 'N/A'
        
        hdr['WIDTH'] = self.imgWidth
        hdr['HEIGHT'] = self.imgHeight
        hdr['BITDEPTH'] = self.bitdepth
        
        if hasattr(self, 'cur') and hasattr(self.cur, 'displayname'):
            hdr['CAMERA'] = self.cur.displayname
        else:
            hdr['CAMERA'] = 'Unknown'
        
        hdr['DATAMEAN'] = f"{np.mean(raw_image):.3f}"
        hdr['DATAMED']  = f"{np.median(raw_image):.3f}"
        hdr['DATASTD']  = f"{np.std(raw_image):.3f}"
        hdr['DATAMAX']  = f"{np.max(raw_image):.3f}"
        hdr['DATAMIN']  = f"{np.min(raw_image):.3f}"
        
        hdr['CAPTIME']  = datetime.datetime.now().isoformat()
        
        hdu = fits.PrimaryHDU(data=raw_image, header=hdr)
        hdul = fits.HDUList([hdu])
        
        fits_filename = f"{self.le_directory.text().strip()}/{self.le_file_prefix.text().strip()}{self.count}.fits"
        hdul.writeto(fits_filename, overwrite=True)
        logging.info("FITS file saved: %s", fits_filename)
    
    def updatePixelCount(self, event=None):
        """
        Updates the lbl_pixel_info label with the mouse position and the pixel value in the 16/8-bit image.
        """
        if event is None:
            if hasattr(self.lbl_video, 'lastMousePos') and self.lbl_video.lastMousePos is not None:
                pos = self.lbl_video.lastMousePos
            else:
                self.lbl_pixel_info.setText("Pixel info:")
                return
        else:
            pos = event.pos() if hasattr(event, 'pos') else event
        
        pm = self.lbl_video.pixmap()
        if pm is None:
            self.lbl_pixel_info.setText("No image loaded")
            return
        
        pm_width = pm.width()
        pm_height = pm.height()
        label_width = self.lbl_video.width()
        label_height = self.lbl_video.height()
        
        x_offset = (label_width - pm_width) // 2
        y_offset = (label_height - pm_height) // 2
        
        x = pos.x() - x_offset
        y = pos.y() - y_offset
        
        if 0 <= x < pm_width and 0 <= y < pm_height:
            qimg = pm.toImage()
            color = QColor(qimg.pixel(x, y))
            
            # Map to the original RAW image
            raw_x = int(x * (self.imgWidth / pm_width))
            raw_y = int(y * (self.imgHeight / pm_height))
            
            if hasattr(self, 'lastRawImage'):
                value = self.lastRawImage[raw_y, raw_x]
                self.lbl_pixel_info.setText(f"Pos: ({raw_x}, {raw_y}) - Counts: {value}")
            else:
                self.lbl_pixel_info.setText(f"Pos: ({x}, {y}) - Gray: {color.red()}")
        else:
            self.lbl_pixel_info.setText("Pixel info:")
    
    def updateHistogramRaw(self, raw_image: np.ndarray):
        """
        Updates the histogram graph based on the received RAW image.
        """
        max_val = 2**self.bitdepth - 1
        n_bins = 256
        hist, bins = np.histogram(raw_image.flatten(), bins=n_bins, range=(0, max_val))
        
        self.ax_hist.clear()
        self.ax_hist.plot(bins[:-1], hist)
        self.ax_hist.set_title(f"Histogram ({self.bitdepth}-bit)")
        self.ax_hist.set_xlabel("Intensity")
        self.ax_hist.set_ylabel("Counts")
        
        self.canvas_hist.draw()

