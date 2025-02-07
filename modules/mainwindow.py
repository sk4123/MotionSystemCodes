import os.path
import webbrowser
import serial.tools.list_ports as list_ports
import serial
import time
from modules.LED import LED

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QProgressBar, QPushButton, QSlider, 
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout,
    QWidget, QTextEdit, QButtonGroup, QDialog, QGridLayout, QListWidget)

class Widget(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MicroWell Motion Controller")

        ##
        ## Variables
        ##

        # Gcode commands
        self.storedcommand = None

        # Calibration values
        self.calibrationvalues = [0,0,0]

        # Current coordinates
        self.coords = [0, 0, 0]
        self.last_coords = [0, 0, 0]

        # Max and min limits
        self.limits_max = [80, 100, 30]
        self.limits_min = [0, 0, 0]

        # Ports
        self.motionPort = "COM3" #"/dev/ttyACM0" #None
        self.piezoPort = "COM4"
        self.ledPort = "COM5"

        # Baudrates
        self.motionBaud = 250000

        # Serial communication
        self.motionSerial = serial.Serial()
        self.LED = LED(self.ledPort)
        self.LED.connect()
        
        # Helper variables
        self.marlinrow = -1

        # Modes
        self.calibration_mode = False
        self.well_mode = False
        self.row_mode = False
        self.col_mode = False
        self.all_mode = False

        # Well diameter, in mm
        self.dwell = 9

        # Speed
        self.feed_rate = 300

        # LED values
        self.redOn = False
        self.greenOn = False
        self.blueOn = False
        self.yellowOn = False

        ## 
        ## Creating the GUI Layout
        ##

        fullLayout = QGridLayout()

        # Menubar
        #menu = self.menuBar()
        #file_menu = menu.addMenu("File")
        #file_menu.addAction("Load Experiment")
        #file_menu.addAction("Current Experiment")

        # Manual gcode
        gcodeLayout = QHBoxLayout()
        gcodeLabel = QLabel("G-Code:")
        self.gcodeInput = QLineEdit()
        gcodeLayout.addWidget(gcodeLabel)
        gcodeLayout.addWidget(self.gcodeInput)

        # Stop and Send
        commandLayout = QVBoxLayout()
        sendButton = QPushButton("Send")
        #stopButton = QPushButton("Stop")
        homeButton = QPushButton("Home")
        commandLayout.addWidget(sendButton)
        commandLayout.addWidget(homeButton)
        #commandLayout.addWidget(stopButton)

        gcLayout = QHBoxLayout()
        gcLayout.addLayout(gcodeLayout)
        gcLayout.addLayout(commandLayout)

        gcLayout.setContentsMargins(40, 40, 40, 40)

        # Experiment Import
        #experimentLayout = QVBoxLayout()
        #currentExperiment = QLineEdit("None")
        #currentExperiment.setReadOnly(True)
        #loadExperiment = QPushButton("Load Experiment")
        #experimentLayout.addWidget(currentExperiment)
        #experimentLayout.addWidget(loadExperiment)

        # Combining the Stop/Send and Experiment layouts in one
        #commandExpLayout = QHBoxLayout()
        #commandExpLayout.addLayout(commandLayout)
        #commandExpLayout.addLayout(experimentLayout)

        # Marlin Log Data
        #self.log_display = QListWidget()

        # Current locations
        #locationLayout = QGridLayout()
        #xLocationLabel = QLabel("X:")
        #self.x_display = QLineEdit()
        #self.x_display.setReadOnly(True)
        #yLocationLabel = QLabel("Y:")
        #self.y_display = QLineEdit()
        #self.y_display.setReadOnly(True)
        #zLocationLabel = QLabel("Z:")
        #self.z_display = QLineEdit()
        #self.z_display.setReadOnly(True)
        #speed_label = QLabel("Speed Set:")
        #self.speed_set = QLineEdit()
        #locationLayout.addWidget(xLocationLabel, 0, 0)
        #locationLayout.addWidget(yLocationLabel, 1, 0)
        #locationLayout.addWidget(zLocationLabel, 2, 0)
        #locationLayout.addWidget(speed_label, 3, 0)
        #locationLayout.addWidget(self.x_display, 0, 1)
        #locationLayout.addWidget(self.y_display, 1, 1)
        #locationLayout.addWidget(self.z_display, 2, 1)
        #locationLayout.addWidget(self.speed_set, 3, 1)

        # Mode Selection
        modeLayout = QGridLayout()
        options = QButtonGroup(self)
        self.well = QCheckBox("Well:")
        self.wellInput = QLineEdit()
        self.row = QCheckBox("Row:")
        self.rowInput = QLineEdit()
        self.column = QCheckBox("Column:")
        self.colInput = QLineEdit()
        self.all = QCheckBox("All")
        options.addButton(self.well)
        options.addButton(self.row)
        options.addButton(self.column)
        options.addButton(self.all)
        options.setExclusive(True)
        modeLayout.addWidget(self.well, 0, 0)
        modeLayout.addWidget(self.row, 1, 0)
        modeLayout.addWidget(self.column, 2, 0)
        modeLayout.addWidget(self.all, 3, 0)
        modeLayout.addWidget(self.wellInput, 0, 1)
        modeLayout.addWidget(self.rowInput, 1, 1)
        modeLayout.addWidget(self.colInput, 2, 1)

        modeLayout.setContentsMargins(40, 40, 40, 40)

        # Port Selection
        #portLayout = QGridLayout()
        #self.ports = QListWidget()
        #pickPort = QPushButton("Select Port")
        #refreshPort = QPushButton("Refresh Ports")
        #portLayout.addWidget(self.ports, 0, 0, 1, 2)
        #portLayout.addWidget(pickPort, 1, 0)
        #portLayout.addWidget(refreshPort, 1, 1)

        # Calibration
        calLayout = QGridLayout()
        self.activateCal = QCheckBox("Cal. Mode")

        x_01 = QPushButton("X+0.1")
        x_1 = QPushButton("X+1")
        x_5 = QPushButton("X+5")
        xn_01 = QPushButton("X-0.1")
        xn_1 = QPushButton("X-1")
        xn_5 = QPushButton("X-5")

        y_01 = QPushButton("Y+0.1")
        y_1 = QPushButton("Y+1")
        y_5 = QPushButton("Y+5")
        yn_01 = QPushButton("Y-0.1")
        yn_1 = QPushButton("Y-1")
        yn_5 = QPushButton("Y-5")

        z_01 = QPushButton("Z+0.1")
        z_1 = QPushButton("Z+1")
        z_5 = QPushButton("Z+5")
        zn_01 = QPushButton("Z-0.1")
        zn_1 = QPushButton("Z-1")
        zn_5 = QPushButton("Z-5")
    
        calLayout.addWidget(x_1, 3, 5)
        calLayout.addWidget(x_5, 3, 6)
        calLayout.addWidget(x_01, 3, 4)
        calLayout.addWidget(xn_01, 3, 2)
        calLayout.addWidget(xn_1, 3, 1)
        calLayout.addWidget(xn_5, 3, 0)

        calLayout.addWidget(yn_5, 6, 3)
        calLayout.addWidget(yn_1, 5, 3)
        calLayout.addWidget(yn_01, 4, 3)
        calLayout.addWidget(y_01, 2, 3)
        calLayout.addWidget(y_1, 1, 3)
        calLayout.addWidget(y_5, 0, 3)

        calLayout.addWidget(z_5, 0, 7)
        calLayout.addWidget(z_1, 1, 7)
        calLayout.addWidget(z_01, 2, 7)
        calLayout.addWidget(zn_01, 3, 7)
        calLayout.addWidget(zn_1, 4, 7)
        calLayout.addWidget(zn_5, 5, 7)

        calLayout.addWidget(self.activateCal, 0, 0)

        calLayout.setContentsMargins(40, 40, 40, 40)


        #LED Controls
        LEDScaleLayout = QGridLayout()
        redButton = QPushButton('Red')
        redButton.setCheckable(True)
        greenButton = QPushButton('Green')
        greenButton.setCheckable(True)
        blueButton = QPushButton('Blue')
        blueButton.setCheckable(True)
        yellowButton = QPushButton('Yellow')
        yellowButton.setCheckable(True)

        redButton.setStyleSheet("QPushButton:checked {background-color: red}")
        greenButton.setStyleSheet("QPushButton:checked {background-color: green}")
        blueButton.setStyleSheet("QPushButton:checked {background-color: blue}")
        yellowButton.setStyleSheet("QPushButton:checked {background-color: yellow}")
        
        self.redSlider = QSlider(Qt.Horizontal, self)
        self.redSlider.setRange(0, 100)
        self.greenSlider = QSlider(Qt.Horizontal, self)
        self.greenSlider.setRange(0, 100)
        self.blueSlider = QSlider(Qt.Horizontal, self)
        self.blueSlider.setRange(0, 100)
        self.yellowSlider = QSlider(Qt.Horizontal, self)
        self.yellowSlider.setRange(0, 100)

        self.redIntensity = QLineEdit(readOnly=True)
        self.greenIntensity = QLineEdit(readOnly=True)
        self.blueIntensity = QLineEdit(readOnly=True)
        self.yellowIntensity = QLineEdit(readOnly=True)


        LEDScaleLayout.addWidget(self.redSlider, 0, 0)
        LEDScaleLayout.addWidget(self.redIntensity, 0, 1)
        LEDScaleLayout.addWidget(redButton, 0, 2)
        LEDScaleLayout.addWidget(self.greenSlider, 1, 0)
        LEDScaleLayout.addWidget(self.greenIntensity, 1, 1)
        LEDScaleLayout.addWidget(greenButton, 1, 2)
        LEDScaleLayout.addWidget(self.blueSlider, 2, 0)
        LEDScaleLayout.addWidget(self.blueIntensity, 2, 1)
        LEDScaleLayout.addWidget(blueButton, 2, 2)
        LEDScaleLayout.addWidget(self.yellowSlider, 3, 0)
        LEDScaleLayout.addWidget(self.yellowIntensity, 3, 1)
        LEDScaleLayout.addWidget(yellowButton, 3, 2)

        LEDScaleLayout.setContentsMargins(40, 40, 40, 40)

        #Camera Controls
        cameraLayout = QGridLayout()
        fpsLabel = QLabel('FPS')
        exposeLabel = QLabel('Exposure')
        acqLabel = QLabel('Acquisition Interval')
        fpsVal = QLineEdit()
        exposeVal = QLineEdit()
        acqVal = QLineEdit()
        cameraLayout.addWidget(fpsLabel, 0, 0)
        cameraLayout.addWidget(fpsVal, 0, 1)
        cameraLayout.addWidget(exposeLabel, 1, 0)
        cameraLayout.addWidget(exposeVal, 1, 1)
        cameraLayout.addWidget(acqLabel, 2, 0)
        cameraLayout.addWidget(acqVal, 2, 1)

        cameraLayout.setContentsMargins(40, 40, 40, 40)

        #Piezo Controls
        piezoLayout = QHBoxLayout()
        piezoButtonLayout = QVBoxLayout()
        pincButton = QPushButton('+')
        pdecButton = QPushButton('-')
        piezoButtonLayout.addWidget(pincButton)
        piezoButtonLayout.addWidget(pdecButton)
        piezoInputLayout = QHBoxLayout()
        pLabel = QLabel('Set Piezo Step (um)')
        pInput = QLineEdit()
        piezoInputLayout.addWidget(pLabel)
        piezoInputLayout.addWidget(pInput)
        piezoLayout.addLayout(piezoInputLayout)
        piezoLayout.addLayout(piezoButtonLayout)

        piezoLayout.setContentsMargins(40, 40, 40, 40)


        # Putting it all together
        fullLayout.addLayout(gcLayout, 0, 0)
        #fullLayout.addLayout(commandExpLayout, 1, 0)
        #fullLayout.addWidget(self.log_display, 2, 0)
        #fullLayout.addLayout(locationLayout, 0, 1) #
        fullLayout.addLayout(modeLayout, 0, 1) #
        #fullLayout.addLayout(portLayout, 0, 2)
        fullLayout.addLayout(calLayout, 0, 2) #
        fullLayout.addLayout(LEDScaleLayout, 1, 0)
        fullLayout.addLayout(cameraLayout, 1, 1)
        fullLayout.addLayout(piezoLayout, 1, 2)


        # Setting fullLayout and the layout of the GUI
        self.setLayout(fullLayout)
        

        ##
        ## Adding functionality to the GUI
        ##

        self.gcodeInput.editingFinished.connect(self.storeCommand)

        sendButton.released.connect(self.sendCommand)
        homeButton.released.connect(self.home)
        #stopButton.released.connect(self.getCoords) #####

        #self.speed_set.editingFinished.connect(self.speedSet)

        #loadExperiment.released.connect(self.pickExperiment)

        self.well.toggled.connect(self.imageWell)
        self.wellInput.editingFinished.connect(self.wellToImage)

        self.row.toggled.connect(self.imageRow)
        self.rowInput.editingFinished.connect(self.rowToImage)

        self.column.toggled.connect(self.imageCol)
        self.colInput.editingFinished.connect(self.colToImage)

        self.all.toggled.connect(self.imageAll)

        #pickPort.released.connect(self.selectPort)
        #refreshPort.released.connect(self.refreshPorts)

        self.activateCal.toggled.connect(self.calibrationSequence)

        x_01.released.connect(self.press_x01)
        x_1.released.connect(self.press_x1)
        x_5.released.connect(self.press_x5)
        xn_01.released.connect(self.press_xn01)
        xn_1.released.connect(self.press_xn1)
        xn_5.released.connect(self.press_xn5)

        y_01.released.connect(self.press_y01)
        y_1.released.connect(self.press_y1)
        y_5.released.connect(self.press_y5)
        yn_01.released.connect(self.press_yn01)
        yn_1.released.connect(self.press_yn1)
        yn_5.released.connect(self.press_yn5)

        z_5.released.connect(self.press_z5)
        z_1.released.connect(self.press_z1)
        z_01.released.connect(self.press_z01)
        zn_1.released.connect(self.press_zn1)
        zn_01.released.connect(self.press_zn01)
        zn_5.released.connect(self.press_zn5)


        self.redSlider.sliderMoved.connect(self.redPosition)
        self.greenSlider.sliderMoved.connect(self.greenPosition)
        self.blueSlider.sliderMoved.connect(self.bluePosition)
        self.yellowSlider.sliderMoved.connect(self.yellowPosition)

        redButton.toggled.connect(self.redChange)
        greenButton.toggled.connect(self.greenChange)
        blueButton.toggled.connect(self.blueChange)
        yellowButton.toggled.connect(self.yellowChange)



        # Presets
        #self.speed_set.setText(f"{self.feed_rate}")



    ##
    ## GUI Functions
    ##

    # Homes all axes
    def home(self):
        self.sendCommand(["G28 X Y Z"])

    # Takes the input and assigns it to the storedcommand variable
    def storeCommand(self):
        self.storedcommand = self.gcodeInput.text().upper() + ";"
        print(self.storedcommand)
        self.getCoords(self.storedcommand)

    # Modified from pyGcodeSender by ______ - modify!!!!!!!
    def sendCommand(self, c = None):
        if(self.motionPort):
            if self.storedcommand:
                command = [self.storedcommand]
                self.storedcommand = None
                print(f"Command is {command}")
            else:
                command = c
                print(f"Command is {command}")
            
            moveon = False
            #self.getCoords(command)

            try:
                self.motionSerial(self.motionPort, self.motionBaud)
                moveon = True
                print("Starting the sending process")
            except:
                print("No Connection")
            
            if(moveon):
                self.motionSerial.write(b"\r\n\r\n") # Wake up microcontroller
                time.sleep(1)
                self.motionPort.reset_input_buffer()
                print("Sending")

                for code in command:
                    if code.strip().startswith(';') or code.isspace() or len(code) <=0:
                        continue
                    else:
                        self.motionSerial.write((code+'\n').encode())
                        while(1): # Wait untile the former gcode has been completed.
                            a = self.motionSerial.readline()
                            if a.startswith(b'ok'):
                                break
                            else:
                                self.log_display.addItem(a.decode('utf-8'))
        else:
            print("No port")
    
    
    def speedSet(self):
        s = self.speed_set.text()
        if isinstance(s, int):
            s = int(s)
            self.feed_rate = s
        else:
            print("Not an integer")

    #
    def stopMotion(self):
        print("A")

    #
    def pickExperiment(self):
        print("A")

    # Need to get this stuff from Marlin. Add scroll bars too
    def displayMarlin(self, text):
        row = self.marlinrow + 1
        self.log_display.insertItems(row, text)

    #
    def getCoords(self, command):
        c = command[0:2]
        c2 = command[0:3]
        if c == "G1" or c == "G0" or c2 == "G92":
            ind = [command.find("X"), command.find("Y"), command.find("Z"), command.find(";")]
            for f in range(len(ind)):
                if ind[f] == ind[-1] or ind[f] < 0:
                    break
                else:
                    self.coords[f] = ind[f+1:][-1]
        elif c2 == "G28":
            self.coords = [0,0,0]
        print(self.coords)
        self.displayCoords(self.coords)

    # Need to get the coords from Marlin
    def displayCoords(self, coords):
        self.x_display.setText(f"{coords[0]}")
        self.y_display.setText(f"{coords[1]}")
        self.z_display.setText(f"{coords[2]}")

    #
    def imageWell(self):
        if self.well.isChecked():
            self.well_mode = True
        else:
            self.well_mode = False
    
    #
    def wellToImage(self):
        if self.well_mode:
            self.getWell(self.wellInput.text())
        else:
            print("The proper box is not checked")

    #
    def getWell(self, well):
        arr = well
        x = self.letToNum(arr[0])
        y = int(arr[1])
        x , y = x*self.dwell, (y-1)*self.dwell
        self.generateXYCoords([[x,y]])

    #
    def letToNum(self, a):
        if str(a):
            a = a.upper()
            switch = {
                "A": 0,
                "B": 1,
                "C": 2,
                "D": 3,
                "E": 4,
                "F": 5,
                "G": 6,
                "H": 7
            }
            num = switch.get(a, "Input not defined")
            return(num)
        else:
            print("A letter was not used")

    # A row is the letters
    def imageRow(self):
        if self.row.isChecked():
            self.row_mode = True
        else:
            self.row_mode = False

    #
    def rowToImage(self):
        if self.row_mode:
            self.getRow(self.rowInput.text())
        else:
            print("The proper box is not checked")

    #
    def getRow(self, row):
        coords=[]
        row = self.letToNum(row)
        x = row*self.dwell
        for i in range(12):
            y = i*self.dwell
            coords.append([x,y])
        self.generateXYCoords(coords, z = True)

    # A column is the numbers
    def imageCol(self):
        if self.column.isChecked():
            self.col_mode = True
        else:
            self.col_mode = False

    #
    def colToImage(self):
        if self.col_mode:
            self.getCol(self.colInput.text())
        else:
            print("The proper box is not checked")

    #
    def getCol(self, col):
        coords=[]
        col = int(col)
        y = (col-1)*self.dwell
        for i in range(8):
            x = i*self.dwell
            coords.append([x,y])
        self.generateXYCoords(coords, z = False)

    #
    def generateXYCoords(self, coord_pair, z = False):
        gcode_to_send = []
        for pair in coord_pair:
            if self.checkLimits(pair):
                if z:
                    gcode_to_send.append([f"G1 F{self.feed_rate/4} Z{self.limits_max[2]-20}", f"G1 F{self.feed_rate} X{pair[0]} Y{pair[1]};", f"G1 F{self.feed_rate/4} Z{self.limits_max[2]}", "G4 S1"])
                
                gcode_to_send.append([f"G1 F{self.feed_rate} X{pair[0]} Y{pair[1]};"])
            else:
                print("Position not valid")
                break
        print(gcode_to_send)
        self.sendCommand(gcode_to_send)

    
    # 
    def imageAll(self):
        if self.well.isChecked():
            self.well_mode = True
        else:
            self.well_mode = False

    #
    #def getPorts(self):
        #self.ports.clear()
        #self.ports.addItems([a.device for a in list_ports.comports()])
        # 3 is Marlin??
        # 4 is LED driver

    #
    #def selectPort(self):
        #print("Getting new port")
        #self.port = self.ports.currentItem().text()
        #print(f"New port: {self.port}")

    #
    def refreshPorts(self):
        self.getPorts()
    
    #
    def calibrationSequence(self):
        if self.activateCal.isChecked():
            self.sendCommand(["G91;"])
            self.calibration_mode = True
        elif self.calibrationvalues:
            print(f"Cal vals: {self.calibrationvalues}")
            self.calibration_mode = False
            self.sendCommand(["G90;", "M428;"])
            self.limits_max = [x - y for x, y in zip(self.limits_max, self.calibrationvalues)]
            self.limits_min = [x - y for x, y in zip(self.limits_min, self.calibrationvalues)]
        else:
            self.calibration_mode = False
    
    #
    def press_x1(self):
        self.press_cal(1)

    #
    def press_x01(self):
        self.press_cal(2)

    #
    def press_y1(self):
        self.press_cal(3)

    #
    def press_y01(self):
        self.press_cal(4)

    #
    def press_xn1(self):
        self.press_cal(5)

    #
    def press_xn01(self):
        self.press_cal(6)

    #
    def press_yn1(self):
        self.press_cal(7)

    #
    def press_yn01(self):
        self.press_cal(8)

    #
    def press_z1(self):
        self.press_cal(9)

    #
    def press_z01(self):
        self.press_cal(10)

    #
    def press_zn1(self):
        self.press_cal(11)

    #
    def press_zn01(self):
        self.press_cal(12)

    #
    def press_x5(self):
        self.press_cal(13)

    #
    def press_xn5(self):
        self.press_cal(14)

    #
    def press_y5(self):
        self.press_cal(15)

    #
    def press_yn5(self):
        self.press_cal(16)

    #
    def press_z5(self):
        self.press_cal(17)

    #
    def press_zn5(self):
        self.press_cal(18)

    #
    def press_cal(self, which):
        if self.calibration_mode:
            switch={
                1: [1,0,0],
                2: [0.1,0,0],
                3: [0,1,0],
                4: [0,0.1,0],
                5: [-1,0,0],
                6: [-0.1,0,0],
                7: [0,-1,0],
                8: [0,-0.1,0],
                9: [0,0,1],
                10:[0,0,0.1],
                11: [0,0,-1],
                12: [0,0,-0.1],
                13: [5,0,0],
                14: [-5,0,0],
                15: [0,5,0],
                16: [0,-5,0],
                17: [0,0,5],
                18: [0,0,-5]
            }
            arr = switch.get(which, "Invalid Input")
            self.checkLimits(arr, cal=True)
        else:
            print("Calibration mode not activated")

    #
    def checkLimits(self, arr, cal=False):
        non_zero_pos = [next((i for i, x in enumerate(arr) if x), None)]
        coords = [0, 0, 0]
        did_it_run = [0, 0, 0]

        for pos in non_zero_pos:
            if self.calibrationvalues[pos]+arr[pos] > self.limits_max[pos] or self.calibrationvalues[pos]+arr[pos] < self.limits_min[pos]:
                print("Out of calibration bounds")
                break
            elif cal:
                self.calibrationvalues = [self.calibrationvalues[0] + arr[0], self.calibrationvalues[1] + arr[1], self.calibrationvalues[2] + arr[2]]
                self.sendCommand([f"G1 F200 X{arr[0]} Y{arr[1]} Z{arr[2]};"])
            else:
                coords[pos] = arr[pos]
                did_it_run[pos] = 1

        if sum(did_it_run) == len(non_zero_pos):
            for pos in non_zero_pos:
                self.coords[pos] = coords[pos]
            return True
        else:
            return False
        
    ##
    ## LED
    ##
        
    # Red Slider Position display
    def redPosition(self):
        redValue = self.redSlider.value()
        self.redIntensity.setText(f"{redValue}")
        redBrightness = int(redValue)/100
        if self.redOn:
            LED.turnOnLED(self.LED, 2, redBrightness)
            

    # Is the light on or off
    def redChange(self):
        self.redOn = not self.redOn
        if self.redOn:
            #LED.turnOnLED(self.LED, 2, redBrightness)
            return
        else:
            LED.turnOffLED(self.LED, 2)

    # Green Slider Position display
    def greenPosition(self):
        greenValue = self.greenSlider.value()
        self.greenIntensity.setText(f"{greenValue}")
        if self.greenOn:
            LED.ExecuteCommandBuffer(1, int(greenValue)/100)
    
    # Is the light on or off
    def greenChange(self):
        self.greenOn = not self.greenOn

    # Blue Slider Position display
    def bluePosition(self):
        blueValue = self.blueSlider.value()
        self.blueIntensity.setText(f"{blueValue}")
        if self.blueOn:
            LED.ExecuteCommandBuffer(4, int(blueValue)/100)

    # Is the light on or off
    def blueChange(self):
        self.blueOn = not self.blueOn

    # Yellow Slider Position display
    def yellowPosition(self):
        yellowValue = self.yellowSlider.value()
        self.yellowIntensity.setText(f"{yellowValue}")
        if self.yellowOn:
            LED.ExecuteCommandBuffer(3, int(yellowValue)/100)

    # Is the light on or off
    def yellowChange(self):
        self.yellowOn = not self.yellowOn

