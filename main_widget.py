import logging
import datetime
import numpy as np

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QSignalBlocker
from PyQt5.QtWidgets import QApplication  # Necessary import
from PyQt5.QtGui import QImage, QPixmap, QColor, QIcon

from logging_utils import LogWidget, LogHandler
from control_widget import ControlWidget
from utils import log_exceptions

class MainWidget(QtWidgets.QWidget):
    """
    Main window that contains two tabs:
    1) Control (ControlWidget)
    2) Execution Log (LogWidget)
    Additionally, it integrates the logic for Macro capture (when the macroStarted signal is received).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Photsat EHD Camera Controller')
        self.setMinimumSize(1024, 720)
        
        self.setWindowIcon(QIcon("icon.ico"))
        # If you have an icon, for example:
        # self.setWindowIcon(QIcon('PhotSat Estrella 1.png'))
        
        self.tabs = QtWidgets.QTabWidget(self)
        self.controlTab = ControlWidget(self)
        self.logTab = LogWidget(self)
        
        self.tabs.addTab(self.controlTab, "Control")
        self.tabs.addTab(self.logTab, "Execution Log")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Configure logging to redirect messages to the logTab
        log_handler = LogHandler(self.logTab)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        
        # Macro capture variables
        self.macroSteps = []
        self.currentStepIndex = 0
        self.currentCaptureIndex = 0
        self.totalMacroCaptures = 0
        self.completedMacroCaptures = 0
        self.macroCount = 0
        self.macroRetryCount = 0
        self.macroTimer = QTimer(self)
        
        # Connect the macroStarted signal from MacroModeWidget (inside controlTab) to startMacroCapture
        self.controlTab.macroWidget.macroStarted.connect(self.startMacroCapture)
    
    @log_exceptions
    def startMacroCapture(self, steps: list):
        """
        Starts the Macro sequence using the list of 'steps' (each containing
        captures, exposure, gain, prefix, and directory).
        """
        for step in steps:
            if not step.get("directory"):
                step["directory"] = self.controlTab.le_directory.text().strip()
        
        self.macroSteps = steps
        self.totalMacroCaptures = sum(s.get("captures", 1) for s in steps)
        self.completedMacroCaptures = 0
        self.currentStepIndex = 0
        self.currentCaptureIndex = 0
        self.macroCount = 0
        self.macroRetryCount = 0
        
        self.controlTab.circularProgress.setMaximum(self.totalMacroCaptures)
        self.controlTab.circularProgress.setValue(0)
        
        logging.info("Starting Macro: %d steps, %d total captures",
                     len(steps), self.totalMacroCaptures)
        
        self.executeCurrentMacroCapture()

    @log_exceptions
    def executeCurrentMacroCapture(self):
        """
        Configures the camera and calls onBtnSnap() or TriggerSoftware to perform the capture,
        then schedules processing of the image with a short delay.
        """
        if self.currentStepIndex >= len(self.macroSteps):
            logging.info("Macro sequence completed (%d captures processed).",
                         self.completedMacroCaptures)
            return
        
        currentStep = self.macroSteps[self.currentStepIndex]
        captures = currentStep.get("captures", 1)
        exposure = currentStep.get("exposure", 1000)
        gain = currentStep.get("gain", 100)
        prefix = currentStep.get("prefix", "macro_")
        directory = currentStep.get("directory", self.controlTab.le_directory.text().strip())
        
        # Update interface controls
        self.controlTab.spin_expoTime.setValue(exposure)
        self.controlTab.spin_expoGain.setValue(gain)
        self.controlTab.le_file_prefix.setText(prefix)
        
        # Configure the camera
        try:
            self.controlTab.hcam.put_ExpoTime(exposure)
            self.controlTab.hcam.put_ExpoAGain(gain)
            self.controlTab.manual_exposure = exposure
            self.controlTab.manual_gain = gain
        except Exception as e:
            logging.exception("Error configuring camera in Macro: %s", e)
            return
        
        logging.info("Macro step %d/%d, capture %d/%d: Expo=%d us, Gain=%d, Prefix=%s, Dir=%s",
                     self.currentStepIndex + 1, len(self.macroSteps),
                     self.currentCaptureIndex + 1, captures,
                     exposure, gain, prefix, directory)
        
        if self.controlTab.cur and (self.controlTab.cur.model.still == 0):
            # Camera in non-still mode
            self.controlTab.onBtnSnap()
        else:
            # Still mode: use Snap or TriggerSoftware (if available)
            if hasattr(self.controlTab.hcam, "TriggerSoftware"):
                try:
                    self.controlTab.hcam.TriggerSoftware()
                except Exception as e:
                    logging.exception("Error in TriggerSoftware: %s", e)
                    self.controlTab.hcam.Snap(self.controlTab.res)
            else:
                self.controlTab.hcam.Snap(self.controlTab.res)
        
        delay = exposure // 1000 + 500  # delay to allow capture
        QTimer.singleShot(delay, self._attemptProcessMacroCapture)

    @log_exceptions
    def _attemptProcessMacroCapture(self):
        """
        Attempts to extract the image from the buffer after a Snap/Trigger.
        If it fails, retries several times; if ultimately unsuccessful, skips this capture.
        """
        MAX_RETRIES = 5
        try:
            self.controlTab.hcam.PullImageV4(self.controlTab.pData, 0, self.controlTab.bitdepth, 0, None)
        except nncam.HRESULTException as e:
            logging.warning("Error extracting image (retry %d): %s", self.macroRetryCount, e)
            self.macroRetryCount += 1
            if self.macroRetryCount < MAX_RETRIES:
                QTimer.singleShot(500, self._attemptProcessMacroCapture)
                return
            else:
                logging.error("Maximum retries reached, skipping this capture.")
                self.macroRetryCount = 0
                self._finishCurrentCapture(skip=True)
                return
        else:
            self.macroRetryCount = 0
            self._processExtractedMacroImage()

    @log_exceptions
    def _processExtractedMacroImage(self):
        """
        Processes the image currently in the buffer and saves it as a FITS file in the specified directory.
        Then proceeds to the next capture/step.
        """
        import numpy as np
        stride = nncam.TDIBWIDTHBYTES(self.controlTab.imgWidth * self.controlTab.bitdepth)
        dtype = np.uint16 if self.controlTab.bitdepth > 8 else np.uint8
        
        raw_arr = np.frombuffer(self.controlTab.pData, dtype=dtype)
        elems_per_row = stride // (self.controlTab.bitdepth // 8)
        raw_arr = raw_arr.reshape((self.controlTab.imgHeight, elems_per_row))
        raw_image = raw_arr[:, :self.controlTab.imgWidth]
        
        # Save as FITS
        self.controlTab.lastRawImage = raw_image.copy()
        self.macroCount += 1
        
        import datetime
        from astropy.io import fits
        
        hdr = fits.Header()
        exp = self.controlTab.manual_exposure / 1e6 if self.controlTab.manual_exposure else 'N/A'
        hdr['EXPTIME'] = (exp, "Exposure time in seconds")
        hdr['GAIN'] = (self.controlTab.manual_gain, "Gain in percentage")
        
        try:
            hdr['TEMP'] = self.controlTab.hcam.get_Temperature() / 10
        except:
            hdr['TEMP'] = 'N/A'
        
        hdr['WIDTH'] = self.controlTab.imgWidth
        hdr['HEIGHT'] = self.controlTab.imgHeight
        hdr['BITDEPTH'] = self.controlTab.bitdepth
        if hasattr(self.controlTab, 'cur') and hasattr(self.controlTab.cur, 'displayname'):
            hdr['CAMERA'] = self.controlTab.cur.displayname
        else:
            hdr['CAMERA'] = 'Unknown'
        
        hdr['DATAMEAN'] = f"{np.mean(raw_image):.3f}"
        hdr['DATAMED']  = f"{np.median(raw_image):.3f}"
        hdr['DATASTD']  = f"{np.std(raw_image):.3f}"
        hdr['DATAMAX']  = f"{np.max(raw_image):.3f}"
        hdr['DATAMIN']  = f"{np.min(raw_image):.3f}"
        hdr['CAPTIME']  = datetime.datetime.now().isoformat()
        
        prefix = self.macroSteps[self.currentStepIndex].get("prefix", "macro_")
        directory = self.macroSteps[self.currentStepIndex].get("directory", self.controlTab.le_directory.text().strip())
        
        fits_filename = f"{directory}/{prefix}{self.macroCount}.fits"
        
        hdu = fits.PrimaryHDU(data=raw_image, header=hdr)
        hdul = fits.HDUList([hdu])
        hdul.writeto(fits_filename, overwrite=True)
        
        logging.info("Macro FITS saved: %s", fits_filename)
        
        # Update preview
        if self.controlTab.bitdepth > 8:
            preview_arr = (raw_image.astype(np.float32) / (2**self.controlTab.bitdepth - 1) * 255).astype(np.uint8)
        else:
            preview_arr = raw_image
        
        from PyQt5.QtGui import QImage, QPixmap
        image_preview = QImage(preview_arr.data, self.controlTab.imgWidth, self.controlTab.imgHeight,
                               self.controlTab.imgWidth, QImage.Format_Grayscale8)
        newimage = image_preview.scaled(self.controlTab.lbl_video.width(),
                                        self.controlTab.lbl_video.height(),
                                        self.controlTab.Qt.KeepAspectRatio,
                                        self.controlTab.Qt.FastTransformation)
        
        self.controlTab.currentPreviewImage = newimage
        self.controlTab.lbl_video.setPixmap(QPixmap.fromImage(newimage))
        
        self._finishCurrentCapture(skip=False)

    @log_exceptions
    def _finishCurrentCapture(self, skip=False):
        """
        Called after extracting and/or saving the image.
        Updates counters and advances to the next capture/step.
        """
        self.completedMacroCaptures += 1
        self.controlTab.circularProgress.setValue(self.completedMacroCaptures)
        
        currentStep = self.macroSteps[self.currentStepIndex]
        captures = currentStep.get("captures", 1)
        
        if self.currentCaptureIndex < captures - 1:
            self.currentCaptureIndex += 1
        else:
            self.currentCaptureIndex = 0
            self.currentStepIndex += 1
        
        if self.completedMacroCaptures < self.totalMacroCaptures:
            QTimer.singleShot(500, self.executeCurrentMacroCapture)
        else:
            logging.info("Macro sequence completed (%d captures processed).",
                         self.completedMacroCaptures)
