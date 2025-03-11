import logging
from PyQt5.QtWidgets import QMessageBox

def log_exceptions(func):
    """
    Decorator to capture exceptions, log them, 
    and display an error message box if the object 'self' has a setEnabled method.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception("Exception in %s", func.__name__)
            self_obj = args[0] if args else None
            if hasattr(self_obj, "setEnabled"):
                QMessageBox.warning(self_obj, "Error", f"An error occurred in {func.__name__}:\n{e}")
            # Return None or re-raise the exception, depending on your preference.
            return None
    return wrapper
