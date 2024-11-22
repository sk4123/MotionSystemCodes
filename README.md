Running main.py will run the program.

Current design features:
    Capable of moving to individual wells (to check)
    Capable of moving along specified rows (to check)
    Calibration


Necessary changes:
    Moving to all wells (iterated row movement)
    Integration with optics (possible timer, or a command from the computer)
        Includes the dipping, part of making the system function
    Adding the option to input your own gcode commands directly
    Remove the "Edit gcode" feature
    Make the progress bar work
    Add a signal indicating the arduino is connected
    New stepper drivers
    Add errors
    Styling


This currently runs on Python 12.4 through a virtual environment included in the repo.
Libraries include:
    PySide6 version 6.7.2
    Pyserial version 3.5

The folder named "ui" contains the files used to create the UI using the open-source version of QT Creator: https://www.qt.io/download-open-source.

The folder named "Marlin-2.1.2.4" contains the Marlin 2.1.2.4 code used on the Arduino Mega: https://github.com/MarlinFirmware. The main change files are Marlin/Configuration.h, Marlin/Configuration_adv.h, and Marlin/src/pins/mega/pins_MEGACONTROLLER.h. Full changes are below:
    Configuration.h
        91: BOARD_MEGACONTROLLER
        162-164: TB6560
        176: Commented
        231: 0
        552: 0
        560: 0
        652-654: Commented
        876-879: Commented
        1199: { 400, 400, 63*4 }
        1206: { 1000, 1000, 100 }
        1305: Commented
        1637-1639: 1
        1640: Commented
        1671: true
        1725: 80
        1726: 100
        1734: 40
    Configuration_adv.h
        1103: { false, false, false }
    pins_MEGACONTROLLER
        50-55: 37, 38, 40, 41, 42, 43
        67-77: 2, 3, 22, 4, 5, 23, 6, 7, 24
        79-81: 58, 59, 60
        91 & 93: 61
        97 & 99: 62
        102: 63
        105 & 107: 64
        

