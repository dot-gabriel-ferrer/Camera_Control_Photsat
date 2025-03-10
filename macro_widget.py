import csv
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QTableWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QFont

class MacroModeWidget(QWidget):
    """
    Widget that manages Macro Mode:
    - A table with columns [Captures, Exposure (us), Gain, Prefix, Directory]
    - Buttons to add/remove rows, load/save CSV, and start Macro capture.
    """
    macroStarted = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["Captures", "Exposure (us)", "Gain", "Prefix", "Directory"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        font = QFont()
        font.setPointSize(5)  # Adjust this value to the desired font size
        self.table.setFont(font)
        header.setFont(font)
        
        layout.addWidget(self.table)
        
        btnLayout = QHBoxLayout()
        self.btnAdd = QPushButton("Add Row")
        self.btnRemove = QPushButton("Remove Row")
        btnLayout.addWidget(self.btnAdd)
        btnLayout.addWidget(self.btnRemove)
        layout.addLayout(btnLayout)
        
        csvBtnLayout = QHBoxLayout()
        self.btnLoadCSV = QPushButton("Load Macro CSV")
        self.btnSaveCSV = QPushButton("Save Macro CSV")
        csvBtnLayout.addWidget(self.btnLoadCSV)
        csvBtnLayout.addWidget(self.btnSaveCSV)
        layout.addLayout(csvBtnLayout)
        
        self.btnStartMacro = QPushButton("Start Macro Capture")
        layout.addWidget(self.btnStartMacro)
        
        # Connections
        self.btnAdd.clicked.connect(self.addRow)
        self.btnRemove.clicked.connect(self.removeRow)
        self.btnStartMacro.clicked.connect(self.startMacro)
        self.btnLoadCSV.clicked.connect(self.loadCSV)
        self.btnSaveCSV.clicked.connect(self.saveCSV)

    def addRow(self):
        """
        Adds a new row to the table with default values.
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("1"))
        self.table.setItem(row, 1, QTableWidgetItem("1000"))
        self.table.setItem(row, 2, QTableWidgetItem("100"))
        self.table.setItem(row, 3, QTableWidgetItem("macro_"))
        
        # Search up the parent hierarchy for a widget with the attribute le_directory
        default_dir = "."
        p = self.parent()
        while p is not None:
            if hasattr(p, "le_directory"):
                default_dir = p.le_directory.text().strip()
                break
            p = p.parent()
        
        self.table.setItem(row, 4, QTableWidgetItem(default_dir))
    
    def removeRow(self):
        """
        Removes the currently selected row from the table.
        """
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
    
    def startMacro(self):
        """
        Reads the parameters from each row of the table and emits the 'macroStarted'
        signal with a list of steps (dictionaries).
        """
        steps = []
        for row in range(self.table.rowCount()):
            try:
                captures = int(self.table.item(row, 0).text())
            except:
                captures = 1
            
            try:
                exposure = int(self.table.item(row, 1).text())
            except:
                exposure = 1000
            
            try:
                gain = int(self.table.item(row, 2).text())
            except:
                gain = 100
            
            prefix = self.table.item(row, 3).text()
            directory = self.table.item(row, 4).text()
            
            steps.append({
                "captures": captures,
                "exposure": exposure,
                "gain": gain,
                "prefix": prefix,
                "directory": directory
            })
        
        if steps:
            self.macroStarted.emit(steps)
        else:
            QMessageBox.warning(self, "Warning", "No macro steps defined.")
    
    def loadCSV(self):
        """
        Opens a file dialog to load Macro steps from a CSV file.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Load Macro CSV", "", "CSV Files (*.csv)")
        if filename:
            self.table.setRowCount(0)
            with open(filename, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.addRow()
                    currentRow = self.table.rowCount() - 1
                    self.table.item(currentRow, 0).setText(row.get("captures", "1"))
                    self.table.item(currentRow, 1).setText(row.get("exposure", "1000"))
                    self.table.item(currentRow, 2).setText(row.get("gain", "100"))
                    self.table.item(currentRow, 3).setText(row.get("prefix", "macro_"))
                    self.table.item(currentRow, 4).setText(row.get("directory", "."))
    
    def saveCSV(self):
        """
        Opens a file dialog to save the Macro steps to a CSV file.
        """
        filename, _ = QFileDialog.getSaveFileName(self, "Save Macro CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ["captures", "exposure", "gain", "prefix", "directory"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in range(self.table.rowCount()):
                    writer.writerow({
                        "captures": self.table.item(row, 0).text(),
                        "exposure": self.table.item(row, 1).text(),
                        "gain": self.table.item(row, 2).text(),
                        "prefix": self.table.item(row, 3).text(),
                        "directory": self.table.item(row, 4).text()
                    })
