from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel

from utils.utils import log_exceptions

class PreviewLabel(QLabel):
    """
    Specialized QLabel for displaying the camera preview.
    Emits the mouseMoved signal when the mouse moves over the image.
    """
    mouseMoved = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.lastMousePos = None  # Stores the last mouse position.

    @log_exceptions
    def mouseMoveEvent(self, event):
        """
        Overrides the mouse move event to emit a signal and store the mouse position.
        """
        self.lastMousePos = event.pos()
        self.mouseMoved.emit(event)
        super().mouseMoveEvent(event)
