Requires Pyside6 and Pyserial

This code details the use of the well plate scanner developed by Professor Selim Unlu's lab at Boston University. It uses a modified version of Marlin 2.12.4 with the attached configuration files.

The program is started through main.py

Step 1: Connect to the device. If you have multiple COM devices connected, then you will need to figure out which is the device. This is easiest through Device Manger. Turn on your device while in Device Manger and see which COM port shows up; this is the one you will select. Click "Refresh Ports", select the port, and click "Select Port".

Step 2: Home the axes by using "G28 X Y Z". If the z axis is inside the well, run "G28 Z" first, then "G28 X Y". Capitalization does not matter.

Step 3: Calibrate the device over well A1, where this well is furthest from both motors. It is very important that the well plate is placed in this orientation. It is very important that you wait until the vs code terminal says "Sending" before you begin. Positive values are away from the endstop, negative values are towards. For the z, you want the height to be above everything on the well plate to avoid hitting something during motion. When you are done, uncheck the calibration box and the axes will be updated with the current position as zero. If you want to change the calibration at any time it is possible, just be aware that the position the stages are in when you uncheck the calibration box are going to be the new zeros.

Step 4: Start the experiment. For Well, Column, and Row inputs, you need to press "Enter" on your keyboard after you manually input which well, column, or row you would like to image. The "Run" button does not run these inputs (yet).

