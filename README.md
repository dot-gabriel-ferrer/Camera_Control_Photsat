# EHD Camera Controller UI PhotSat

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

EHD Camera Controller UI PhotSat is a GUI application built with PyQt5 for controlling and capturing images from a camera using the NNcam SDK. The application provides features such as live preview, exposure and gain settings, macro capture sequences, and file saving in multiple formats (JPEG, RAW, FITS).

## Prerequisites

Before using this software, please ensure you have installed **EHDViewLite** from the [EHD website](https://www.ehd.de/driver/).
Alternatively, you can add a udev rules file to configure device permissions.

### Udev Rules (for Linux)

Create a file named `99-ehdcam.rules` with the following contents and copy it to `/etc/udev/rules.d`:

```bash
# Copy this file to /etc/udev/rules.d

# Once done, unplug and re-plug your device. This is all that is
# necessary to see the new permissions. Udev does not have to be restarted.

# If you think permissions of 0666 are too loose, then see:
# http://reactivated.net/writing_udev_rules.html for more information on finer
# grained permission setting.

SUBSYSTEM=="usb", ATTRS{idVendor}=="0547", MODE="0666"
```

After copying the file, unplug and re-plug your camera device.

## Features

- **Camera Control:** Open/close the camera, capture images (Snap/Trigger), adjust exposure and gain.
- **Live Preview:** Display a live preview with options to flip the image horizontally or vertically.
- **Macro Mode:** Create macro capture sequences by defining a series of steps via a table, with CSV import/export.
- **Histogram Display:** View a live histogram of the image intensity.
- **Logging:** Integrated execution log to display debug and error messages.
- **Customizable Themes:** Apply different themes and customize text color.

## Project Files

- `circular_progress.py` - Custom circular progress bar widget.
- `collapsible_box.py` - A collapsible container widget.
- `control_widget.py` - Main widget for camera control.
- `libnncam.so` - Native shared library (Linux). *(For Windows, use the corresponding DLL.)*
- `logging_utils.py` - Logging widget and handler.
- `macro_widget.py` - Widget to manage macro capture sequences.
- `main_widget.py` - Main window containing tabs for control and execution log.
- `main.py` - Entry point of the application.
- `nncam.py` - Python bindings for the NNcam SDK.
- `preview_label.py` - Custom QLabel for camera preview.
- `preview_window.py` - Independent window for preview with zoom and pan.
- `utils.py` - Utility functions and decorators.

## Installation


## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/EHD-Camera-Controller.git
   cd EHD-Camera-Controller
   ```
2. **Install Dependencies:**
   All required Python packages are listed in the `requirements.txt` file. To install them, run:

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` file should contain the following (or similar) content:

   ```plaintext
   PyQt5>=5.15.0
   qt_material>=2.8.0
   qtawesome>=1.2.0
   numpy>=1.18.0
   matplotlib>=3.1.0
   astropy>=4.0.0
   ```
3. **Configure the NNcam Library:**

   * **For Linux:**

     Ensure `libnncam.so` is either in the project folder or in your system library path.

     Also, if needed, add the `99-ehdcam.rules` file to `/etc/udev/rules.d` as described below:

     ```bash
     # Copy this file to /etc/udev/rules.d

     # Once done, unplug and re-plug your device. This is all that is
     # necessary to see the new permissions. Udev does not have to be restarted.

     # If you think permissions of 0666 are too loose, then see:
     # http://reactivated.net/writing_udev_rules.html for more information on finer
     # grained permission setting.

     SUBSYSTEM=="usb", ATTRS{idVendor}=="0547", MODE="0666"
     ```
   * **For Windows:**

     Replace `libnncam.so` with the corresponding DLL (e.g., `libnncam.dll`) and update the PyInstaller configuration accordingly.
4. **Install EHDViewLite:**
   Download and install **EHDViewLite** from [https://www.ehd.de/driver/](https://www.ehd.de/driver/).

After following these steps, you should have all the necessary dependencies installed to run the application.

## Running the Application

To run the application, execute:

```bash
python main.py
```

## Building an Executable with PyInstaller

### Linux

To build a standalone executable on Linux:

```bash
pyinstaller --onefile --windowed --icon=your_icon.ico --add-data "libnncam.so:." main.py
```

### Windows

For Windows, use the appropriate DLL and adjust the binary separator (use a semicolon):

```bash
pyinstaller --onefile --windowed --icon=your_icon.ico --add-binary "libnncam.dll;." main.py
```

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
