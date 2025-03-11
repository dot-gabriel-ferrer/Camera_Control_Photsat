import logging
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QVBoxLayout

class LogWidget(QWidget):
    """
    Widget that contains a read-only QPlainTextEdit
    for displaying the application's log messages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logText = QPlainTextEdit(self)
        self.logText.setReadOnly(True)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.logText)
    
    def appendLog(self, message: str):
        """
        Appends text to the log widget.
        """
        self.logText.appendPlainText(message)

class LogHandler(logging.Handler):
    """
    Logging handler that forwards messages to a LogWidget instance.
    """
    def __init__(self, logWidget: LogWidget):
        super().__init__()
        self.logWidget = logWidget
    
    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self.logWidget.appendLog(msg)
