import sys
from PySide6.QtWidgets import QApplication, QWidget
from modules.mainwindow import Widget
# import default

# Calibration doesn't work
# Get the well, row thing to work with dipping
# reduce z speed
# fuck off

app = QApplication(sys.argv)
widget = Widget()
widget.show()
sys.exit(app.exec())


#File which runs the program
#To do:
#Fix the save feature in the main window?? - default settings, saved settings
#Add errors - for ex, if no port or file is selected before running
#Styling
#Adding the connected button up top (as well as an indication of the port)
#When you open a file with "edit," it doesn't make it the actual file
# to determine the OS
#import platform
#C:\Users\Iris Kinetics\AppData\Local\Programs\Python