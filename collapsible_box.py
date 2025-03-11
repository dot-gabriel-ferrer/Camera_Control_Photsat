from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QVBoxLayout, QSizePolicy
)

class CollapsibleBox(QWidget):
    """
    A collapsible container with a button to show/hide its content.
    Useful for grouping sections of the user interface.
    """
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_button = QToolButton(text=title, checkable=True, checked=True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.clicked.connect(self.on_pressed)
        
        self.content_area = QWidget()
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 0, 0, 0)
        self.content_area.setLayout(self.content_layout)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def on_pressed(self):
        """
        Handles the click event on the button to expand/collapse the content.
        """
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.content_area.setVisible(checked)

    def addWidget(self, widget):
        """
        Adds a widget to the internal content.
        """
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        """
        Adds a layout to the internal content.
        """
        self.content_layout.addLayout(layout)
