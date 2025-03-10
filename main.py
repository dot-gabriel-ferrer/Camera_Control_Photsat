# main.py
import sys
import os
import time
import logging

from PyQt5.QtWidgets import QApplication
import nncam

from main_widget import MainWidget

def main():
    """
    Entry point of the application. Configures logging, creates the main window, and starts the event loop.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log file name with date and time
    log_filename = os.path.join(log_dir, time.strftime("execution_log_%Y%m%d_%H%M%S.log"))
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_filename)  # Log to file
        ]
    )
    
    # Enable Gige support
    nncam.Nncam.GigeEnable(None, None)
    
    app = QApplication(sys.argv)
    mainWin = MainWidget()
    mainWin.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
