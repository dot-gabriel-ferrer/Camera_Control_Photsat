# Camera_Control_Photsat/

├── main.py                # Application entry point
├── requirements.txt       # List of Python dependencies
├── README.md              # Project documentation
├── assets/                # Contains resources such as icons
│   └── icon.ico           # Application icon
├── widgets/               # UI components and widgets
│   ├── circular_progress.py
│   ├── collapsible_box.py
│   ├── control_widget.py
│   ├── macro_widget.py
│   ├── main_widget.py
│   ├── preview_label.py
│   └── preview_window.py
├── utils/                 # Utility functions and logging utilities
│   ├── logging_utils.py
│   └── utils.py
└── nncam/                 # NNcam SDK bindings and library
     ├── nncam.py
     └── libnncam.so        # For Windows, use the corresponding DLL (e.g., libnncam.dll) or for Linux, use the SO file instead

## Prerequisites

Before using this software, please ensure you have installed **EHDViewLite** from the [EHD website](https://www.ehd.de/driver/). Alternatively, you can configure device permissions using a udev rules file on Linux.

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

* **Camera Control:** Open/close the camera, capture images (Snap/Trigger), and adjust exposure and gain.
* **Live Preview:** Display a live preview with options to flip the image horizontally or vertically.
* **Macro Mode:** Create macro capture sequences by defining a series of steps (with CSV import/export).
* **Histogram Display:** View a live histogram of image intensity.
* **Logging:** Integrated logging to display debug and error messages.
* **Customizable Themes:** Apply different themes and customize text colors.

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

   The `requirements.txt` should include packages such as:

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

     Ensure that `libnncam.so` is located in the `nncam/` folder or in your system's library path. Also, add the `99-ehdcam.rules` file to `/etc/udev/rules.d` as described above.
   * **For Windows:**

     Replace `libnncam.so` with the corresponding DLL (e.g., `libnncam.dll`) in the `nncam/` folder, and adjust any PyInstaller commands accordingly.
4. **Install EHDViewLite:**
   Download and install **EHDViewLite** from [https://www.ehd.de/driver/](https://www.ehd.de/driver/).

## Running the Application

To run the application in development mode, execute:

```bash
python main.py
```

This will start the application and display the main interface.

## Building an Executable with PyInstaller

### Linux

To build a standalone executable on Linux, run:

### Windows

For Windows, use the appropriate DLL and adjust the data separator:

```bash
pyinstaller --onefile --windowed --icon=assets/icon.ico --add-binary "nncam/libnncam.dll;nncam" --name CameraControlPhotsat main.py
```

The generated executable will be located in the `dist/` folder.

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests with your improvements.

## License

This project is licensed under the MIT License. See the [LICENSE]() file for details.

```

Feel free to modify any sections to better fit your project’s needs.
```
