from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QWidget

class CircularProgress(QWidget):
    """
    Circular progress bar that displays the current and maximum values inside a circle.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._maximum = 100
        self._arcColor = QColor("#4CAF50")  # arc color
        self.setMinimumSize(50, 50)
    
    def sizeHint(self):
        """
        Suggest a default size for the widget.
        """
        return QSize(100, 100)
    
    def setValue(self, value: int):
        """
        Set the current progress value.
        """
        self._value = value
        self.update()
    
    def value(self) -> int:
        """
        Get the current progress value.
        """
        return self._value
    
    def setMaximum(self, maximum: int):
        """
        Set the maximum value for the progress bar.
        """
        self._maximum = maximum
        self.update()
    
    def maximum(self) -> int:
        """
        Get the maximum value of the progress bar.
        """
        return self._maximum
    
    def setArcColor(self, color):
        """
        Set the color of the arc (can be a string or QColor).
        """
        if isinstance(color, str):
            self._arcColor = QColor(color)
        elif isinstance(color, QColor):
            self._arcColor = color
        self.update()
    
    def paintEvent(self, event):
        """
        Draws the circle and the arc representing the progress.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        size = min(rect.width(), rect.height())
        
        margin = size * 0.1
        circleRect = rect.adjusted(int(margin), int(margin), -int(margin), -int(margin))
        
        penWidth = size * 0.08
        pen = QPen(QColor("#DDDDDD"), penWidth)
        painter.setPen(pen)
        painter.drawEllipse(circleRect)
        
        pen.setColor(self._arcColor)
        painter.setPen(pen)
        startAngle = 90 * 16
        spanAngle = -int((self._value / self._maximum) * 360 * 16)
        painter.drawArc(circleRect, startAngle, spanAngle)
        
        painter.setPen(QColor(self._arcColor).darker())
        font = QFont()
        font.setBold(True)
        font.setPointSize(int(size * 0.2))
        painter.setFont(font)
        
        text = f"{self._value}/{self._maximum}"
        painter.drawText(rect, Qt.AlignCenter, text)
