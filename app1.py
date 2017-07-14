from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget,  QWidget, QLCDNumber, QSlider,
    QVBoxLayout, QApplication, QLabel, QHBoxLayout, QComboBox, QSplitter,  QAction, QFormLayout,  QInputDialog, QScrollArea,  QMessageBox, QPushButton,  QGroupBox,  QCheckBox,  QLineEdit,  QFrame,  QDial)
from PyQt5.QtGui import QIcon, QColor,  QPalette,  QImage,  QPixmap, QPainter, QPolygonF,  QBrush
import os
from PyQt5.QtCore import Qt,  QRect,  pyqtSignal,  QSignalMapper, QSize, QPointF,  QBasicTimer
from PyQt5.QtMultimedia import QSound
import sys
import time
import random
from serial import Serial
from joystick import Joy
import math
portList= ['Not state'] + ['COM'+str(i) for i in range(1, 20)]
serialSpeedCases=['9600', '14400', '38400', '57600', '115200']
rotate = 0
gaz = 0
class Net(QWidget):
    isConnectedFlag = False
    send =  pyqtSignal(str)
    serial =  Serial()
    def __init__(self):
        super().__init__()
    def sendData(self,  data):
        global portList
        print(data)
        if 'connect' in data:
            port,  speed =  data.replace('connect',  '').split('/')
            if port ==  portList[0]:
                try:
                    self.serial.close()
                    self.isConnectedFlag =  False
                    return 'Disconnected'
                except:
                    return 'Cannot disconnect'                
            for i in range(3):
                try:
                    self.serial = Serial(port,  speed,  dsrdtr = 0, timeout = 10)
                    #self.serial.open()
                    if self.serial.isOpen() ==  True:
                        self.isConnectedFlag =  True
                        #self.serial.open()
                    return 'Connected'
                except:
                    pass
            else: return 'Cannot connect'
        elif 'move' in data:
            rot, gaz =  data.replace('move',  '').split('/')
            message =  bytes( (rot +  '/' + gaz + '$').encode('utf-8'))
            try:
                self.serial.write(message)
                return '<font color ="green">Data sent</font'
            except:
                return '<font color = "red">Cannot send</font>'
        elif "rescan" in data:
            try:
                self.serial.write(bytes('@'.encode('utf-8')))
                return "Starting rescan"
            except:
                return "Cannot rescan"
    def receiveData(self):
        try:
            if self.isConnectedFlag ==  True:
                ans =  ''
                if self.serial.inWaiting() > 0:
                    print("Adding data" + str(self.serial.inWaiting()))
                    ans += str(self.serial.readline())
                if ans !=  '':
                    if '%' in ans:
                        return "Stop"
                    else:
                        print("Sending data")
                        return ans[2:]
            else:
                return "error"
        except:
            print("Error in receiveData (Net)")
            
        
                
class Window (QMainWindow):
    send =  pyqtSignal(int,  int)
    def __init__(self):
        print('window')
        super().__init__()
        self.statusbar =  self.statusBar()
        self.scrollArea =  QScrollArea()
        self.cont =  Content(self, QDesktopWidget().screenGeometry())
        self.scrollArea.setWidget(self.cont)
        self.cont.send[str,  int].connect(self.sendData)
        self.cont.receive[int].connect(self.receiveData)
        self.cont.showMessage[str].connect(self.showMessage)
        self.setCentralWidget(self.scrollArea)
        self.setBackground()
        self.center()
        
        self.setWindowTitle('Navigare')
        self.setWindowIcon(QIcon('icon.jpg'))
        
        self.net =  Net()
        self.net.send[str].connect(self.sendData)
        self.show()
        self.cont.widgets[4].start()
    def closeEvent(self,  event):
        self.net.sendData("connect/0")
    def sendData(self,  data,  numb):
        self.statusBar().showMessage(str(data))
        ans =  self.net.sendData(data)
        self.statusbar.showMessage(ans)
        if 'connect' in data:
            if ans == 'Connected':
                for i in range(self.cont.numberOfWidgets):
                    self.cont.widgets[i].isConnectedFlag = True
                    #self.cont.widget[numb].connectStateChanged(True)
            elif ans == 'Disconnected':
                for i in range(self.cont.numberOfWidgets):
                    self.cont.widgets[i].isConnectedFlag = False
                    #self.cont.widget[numb].connectStateChanged(False)
    def receiveData(self,  numb):
        ans =  self.net.receiveData()
        self.cont.widgets[numb].data =  ans
    def showMessage(self,  message):
        self.statusbar.showMessage(message)
    def setBackground(self):
        pal =  QPalette()
        pal.setColor(QPalette.Background,  Qt.white)
        self.setAutoFillBackground(True)
        self.setPalette(pal)        
    def center(self):
        
        screen =  QDesktopWidget().screenGeometry()
        self.resize(screen.width()/ 1.3,  screen.height() / 1.2)
        size =  self.geometry()
        #x =  (screen.width() - size.width()) / 2
        #y = (screen.height() - size.height()) / 2
        x = 10
        y = 10
        self.move(x,  y)        
class Content(QWidget):
    numberOfWidgets = 6
    receive =  pyqtSignal(int)
    res =  pyqtSignal(int, int)
    send =  pyqtSignal(str,  int)
    showMessage =  pyqtSignal(str)
    windows =  [1, 0, 0, 0, 1, 0]
    #windows[0]=True
    def __init__(self,  parent, screen):
        super().__init__(parent)
        self.screen = screen
        self.create()
    def create(self):
        self.mainBox =  QVBoxLayout(self)
        
        self.widgets = [0]*self.numberOfWidgets
        
        self.controlSplitter = [0]*2
        for i in range(2):
            self.controlSplitter[i] =  QSplitter(Qt.Horizontal)
            self.mainBox.addWidget(self.controlSplitter[i])
        
        #creating widgets
        self.widgets = [Control(pasp =  0), Camera(pasp =  1),  Map(pasp =  2),  Locator_aside(pasp =  3), Locator_atop(pasp =  4), Collisions(pasp =  5) ]
        
        #self.widgets[0].send[int].connect(self.sendData)
        
        #adding widgets to the layout
        for i in range(self.numberOfWidgets):
            self.widgets[i].send[str,  int].connect(self.sendData)
            self.widgets[i].receive[int].connect(self.receiveData)
            self.widgets[i].showMessage[str].connect(self.sendMessage)
            self.controlSplitter[i//3].addWidget(self.widgets[i])
            if self.windows[i] == True:            
                self.widgets[i].show()
                self.widgets[i].isActive =  True
            else:
                self.widgets[i].hide()   
        
        self.setLayout(self.mainBox)
    def sendData(self,  data,  numb):
        self.send.emit(data,  numb)
    def receiveData(self,  numb):
        self.receive.emit(numb)
    def sendMessage(self,  m):
        self.showMessage.emit(m)
    
class Widgets(QFrame):
    send =  pyqtSignal(str,  int)
    receive =  pyqtSignal(int)
    showMessage =  pyqtSignal(str)
    isActive = False
    pasp =  -1
    data =  0
    isConnectedFlag =  False
    def __init__(self,  pasp):
        super().__init__()
        self.pasp =  pasp
        self.setFrameShape(QFrame.StyledPanel)     
        self.create()  
        self.setMinimumHeight(400)
        self.setMinimumWidth(400)
        
    def create(self):
        self.mainWidgetLayout =  QVBoxLayout(self)
        self.setLayout(self.mainWidgetLayout)
    def sendData(self,  data):
        self.send.emit(data,  self.pasp)
    def receiveData(self):
        self.receive.emit(self.pasp)
        
class Control(Widgets):
    global portList
    global serialSpeedCases
    global rotate
    global gaz
    maxRange = {'x':(-90, 90), 'y': (-30, 30) }
    isConnected =  False
    def __init__(self,  pasp):
        super().__init__(pasp)
        self.createMenu()
        self.createControl()
        self.createConnecter()
    def createMenu(self):
        self.gb =  QGroupBox()
        self.gbLayout =  QHBoxLayout()
        self.gbLayout.addWidget(self.gb)
        self.gb.setTitle('Windows')
        self.menuLayout =  QHBoxLayout()
        self.gb.setLayout(self.menuLayout)
        self.mainWidgetLayout.addLayout(self.gbLayout)
        self.setMaximumWidth(400)
        self.setMaximumHeight(400)
        
        self.lis =  ('Camera',  'Map',  'Locator (atop)',  'locator (side)',  'Collisions')
        self.menu =  [0] * 5
        self.menuBoxMapper =  QSignalMapper(self)
        for i in range(5):
            self.menu[i] =  QCheckBox(self.lis[i])
            self.menuBoxMapper.setMapping(self.menu[i],  i)
            self.menu[i].stateChanged[int].connect(self.menuBoxMapper.map)
            self.menuLayout.addWidget(self.menu[i])
        
        self.menuBoxMapper.mapped[int].connect(self.changeWindows)
        self.bLog =  QPushButton('Log')
        self.bSettings =  QPushButton('set')
    def changeWindows(self,  i):
        state = self.menu[i].checkState()
        #self.changeWindSignal.emit(i, state)
    def createControl(self):
        #self.msg.emit("Hello")
        self.rotSliderLayout =  QHBoxLayout()
        
        self.rotSlider =  QSlider(Qt.Horizontal)
        self.rotSlider.setRange(*self.maxRange['x'])
        self.rotSlider.setMinimumWidth(300)
        self.rotSlider.setTickInterval(5)
        self.rotSlider.setTickPosition(QSlider().TicksBothSides)
        self.rotSlider.valueChanged[int].connect(self.rotSliderChanged)
        self.rotLabel =  QLabel('Rotate')
        self.rotLine =  QLineEdit('0')
        self.rotLine.setMaximumWidth(30)
        
        self.rotSliderLayout.addWidget(self.rotSlider)
        self.rotSliderLayout.addStretch(1)
        self.rotSliderLayout.addWidget(self.rotLabel)
        self.rotSliderLayout.addWidget(self.rotLine)

        self.controlLayout =  QHBoxLayout()
        
        self.joystick =  Joy(self.maxRange)
        self.joystick.setFocusPolicy(Qt.StrongFocus)
        self.joystick.setMinimumSize(300, 200)
        self.joystick.sender[int, int].connect(self.joystickMoved)
        
        
        self.gazSlider =  QSlider(Qt.Vertical)
        self.gazSlider.setRange(*self.maxRange['y'])
        self.gazSlider.setMinimumWidth(80)
        self.gazSlider.setTickInterval(2)
        self.gazSlider.setTickPosition(QSlider().TicksBothSides)
        self.gazSlider.valueChanged[int].connect(self.gazSliderChanged)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.joystick)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.gazSlider)
        self.controlLayout.addStretch(1)
        
        self.bottomLayout =  QHBoxLayout()
        self.bKey =  QPushButton('key')
        self.bFix =  QPushButton('Fix')
        self.bLog =  QPushButton('Log')
        self.bLog.clicked.connect(self.p)
        self.bSettings =  QPushButton('set')
        self.bKey.setMaximumWidth(40)
        self.bFix.setMaximumWidth(40)
        self.bLog.setMaximumWidth(40)
        self.bSettings.setMaximumWidth(40)
        
        self.labelSpeed =  QLabel('Speed')
        self.lineSpeed =  QLineEdit('0')
        self.gazLabel =  QLabel('Gas')
        self.gazLine =  QLineEdit('0')        
        self.lineSpeed.setMaximumWidth(50)
        self.bottomLayout.addWidget(self.bKey)
        self.bottomLayout.addWidget(self.bFix)
        self.bottomLayout.addWidget(self.bLog)
        self.bottomLayout.addWidget(self.bSettings)
        
        self.bottomLayout.addStretch(1)
        self.bottomLayout.addWidget(self.labelSpeed)
        self.bottomLayout.addWidget(self.lineSpeed)
        self.bottomLayout.addWidget(self.gazLabel)
        self.bottomLayout.addWidget(self.gazLine)
        self.bottomLayout.addStretch(1)
        
        self.mainWidgetLayout.addLayout(self.rotSliderLayout)
        self.mainWidgetLayout.addLayout(self.controlLayout)
        self.mainWidgetLayout.addLayout(self.bottomLayout)
    def p(self):
        print('Ffffffff')
    def createConnecter(self):
        self.connectGB =  QGroupBox(self)
        
        self.connectGBLayout =  QHBoxLayout()
        
        self.choosePortBox=QFormLayout()
        self.cbPort =  QComboBox()
        self.cbPort.setMaximumWidth(80)
        self.cbPort.addItems(portList)
        self.cbPort.activated[int].connect(self.connect)
        self.cbPort.setCurrentIndex(15)
        self.cbLabel =  QLabel('<font color = "red">Disconnected</font>')
        
        self.choosePortBox.addRow("Port",  self.cbPort)
        self.choosePortBox.addRow("State",  self.cbLabel)
        
        self.connectGBLayout.addLayout(self.choosePortBox)
        
        self.chooseSpeedBox=QFormLayout()
        self.cbSpeed =  QComboBox()
        self.cbSpeed.setMaximumWidth(80)
        self.cbSpeed.addItems(serialSpeedCases)
        self.cbSpeed.setCurrentIndex(0)
    
        self.chooseSpeedBox.addRow("Speed",  self.cbSpeed)
    
        self.connectGBLayout.addLayout(self.chooseSpeedBox)
        
        self.connectGB.setLayout(self.connectGBLayout)
        self.mainWidgetLayout.addWidget(self.connectGB)
        
        self.pSending =  QPixmap('pause.png')
        self.lSending =  QLabel()
        self.lSending.setPixmap(self.pSending)
        self.pCheck =  QPushButton('Check')
        self.connectGBLayout.addWidget(self.lSending)
        self.connectGBLayout.addWidget(self.pCheck)

    def rotSliderChanged(self, rot):
        global rotate
        rotate = rot
        self.updateControls()
    def gazSliderChanged(self, gaze):
        global gaz
        gaz = gaze
        self.updateControls()
    def updateControls(self):
        self.rotLine.setText(str(rotate))
        self.gazLine.setText(str(gaz))
        self.joystick.setPosition(rotate, gaz)
        self.rotSlider.setValue(rotate)
        self.gazSlider.setValue(gaz)
        self.send.emit('move' + str(rotate) + '/' + str(gaz),  self.pasp)
    def joystickMoved(self, x, y):
        global gaz
        global rotate
        gaz = y
        rotate = x
        self.updateControls()
    def connect(self,  port):
        global portList
        speed =  self.cbSpeed.currentText()
        self.sendData('connect' + portList[port] + '/' + speed)
    def connectStateChanged(self, data):
        if data ==  True:
            self.cbLabel.setText('font color = "green">Connected</font>')
        else:
            self.cbLabel.setText('<font color = "red">Disconnected</font>')
            

        
class Camera(Widgets):
    maxRange = { 'x': [-90, 90], 'y': [-90, 90] }
    def __init__(self,  pasp):
        super().__init__(pasp)
        self.createControl()
    def createControl(self):
    
        self.joyLayout = QHBoxLayout()
        self.joystick = Joy(self.maxRange)
        self.joystick.setMinimumSize(200, 200)
        self.joyLayout.addWidget(self.joystick)
        self.mainWidgetLayout.addLayout(self.joyLayout) 
class Map(Widgets):
    def __init__(self,  pasp):
        super().__init__(pasp) 
        self.createControl()
    def createControl(self):
    
        self.cameraHBox = QHBoxLayout()
        self.joy1Layout =  QVBoxLayout()
        self.joy1Label =  QFormLayout()
        self.joy1Line =  QLineEdit('0')
        self.joy1Line.setMaximumWidth(50)
        self.joy1Label.addRow("Horizontal angle",  self.joy1Line)
        self.joystick1 =  QDial()
        self.joystick1.setMinimumHeight(200)
        self.joystick1.setMinimumWidth(200)
        self.joy1Layout.addStretch(1)
        self.joy1Layout.addLayout(self.joy1Label)
        self.joy1Layout.addWidget(self.joystick1)
        self.joy1Layout.addStretch(1)
    
        self.joy2Layout =  QVBoxLayout()
        self.joy2Label =  QFormLayout()
        self.joy2Line =  QLineEdit('0')
        self.joy2Line.setMaximumWidth(50)
        self.joy2Label.addRow("Vertical angle",  self.joy2Line)
        self.joystick2 =  QDial()
        self.joystick2.setMinimumHeight(200)
        self.joystick2.setMinimumWidth(200)
        self.joy2Layout.addStretch(1)
        self.joy2Layout.addLayout(self.joy2Label)
        self.joy2Layout.addWidget(self.joystick2)
        self.joy2Layout.addStretch(1)
    
        self.cameraHBox.addLayout(self.joy1Layout)
        self.cameraHBox.addLayout(self.joy2Layout)
        self.mainWidgetLayout.addLayout(self.cameraHBox)         

class Locator_aside(Widgets):  
    points = ( (-100, -100), (-180, -80), (-120, -70), (-220, -60) )
    def __init__(self,  pasp):
        super().__init__(pasp)
        self.style = open('locator.css', 'r')
        self.styleSheet = self.style.read()
        self.style.close()
        self.setStyleSheet(self.styleSheet)
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.iconLocator = QPixmap('locator-aside.png')
        
        self.contr = QHBoxLayout()
        self.f = QLabel()
        self.mainWidgetLayout.addStretch(2)
        self.mainWidgetLayout.addLayout(self.contr)
        self.rescanBut = QPushButton('Rescan')
        self.rescanBut.setMinimumSize(60, 20)
        self.rescanBut.toggled.connect(self.rescan)
        self.scanSlider = QSlider(Qt.Horizontal)
        self.contr.addWidget(self.rescanBut)
        self.contr.addWidget(self.scanSlider)
    def rescan(self): 
        print('sss')
    def paintEvent(self, event):
        geom  = self.geometry()
        self.zero = (geom.width()-10, int(geom.height()*0.9))
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)   #smoothing for lines
        p.setRenderHint(QPainter.SmoothPixmapTransform)  #smoothing for Pixmap
        p.setPen(Qt.blue)        
        
        #drawing grid & scale numbers
        p.translate(*self.zero)
        step = 20
        p.setOpacity(0.2)
        for i in range(-self.zero[0]//step, 2):
            p.drawLine(i*step, 0, i*step, -geom.height())
        for i in range(-self.zero[1]//step, 0):
            p.drawLine(0, i*step,  -geom.width(), i*step)
            
        p.setOpacity(0.7)
        
        
        for i in range(-self.zero[0]//(step), 2, 2):
            p.drawText(i*step-10, 10, str(i*step))
            
        for i in range(0, -self.zero[1]//step, -2):
            p.drawText(-self.zero[0]+10, i*step+5, str(i*step))
        #-----------------------------------------------------------
        
        #drawing locator
        p.setOpacity(1)
        p.drawLine(-self.zero[0], 0, 0, 0)   #hor Line
        
        p.translate(0, -30)
        p.rotate(50)
        p.drawLine(0, 0, -geom.width()*2, 0) #rotatable line
        p.drawPixmap(-30, -10, self.iconLocator) #locator icon
        #-----------------------------------------------------------
        
        #drawing barrier map
        p.rotate(-50)
        p.translate(0, 30)
        p.setBrush(Qt.blue)
        p.setOpacity(0.2)
        
        
        self.polygon = QPolygonF()
        self.polygon.append(QPointF(self.points[0][1], 0))
        self.polygon.append(QPointF(-self.zero[0], 0))
        self.polygon.append(QPointF(-self.zero[0], -geom.height()*0.9))
        self.polygon.append(QPointF(self.points[-1][1], -self.zero[1]))
        
        for u in self.points:
            p.drawEllipse(u[0]-1, u[1]-1, 2, 2)
            self.polygon.append(QPointF(*u))
            
        p.drawPolygon(self.polygon)        
class Locator_atop(Widgets):
    points = ( (-100, -100), (-80, -180), (-70, -120), (-60, -220) )
    def __init__(self,  pasp):
        super().__init__(pasp)
        self.style = open('locator.css', 'r')
        self.styleSheet = self.style.read()
        self.style.close()
        self.setStyleSheet(self.styleSheet)        
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.iconLocator = QPixmap('locator-atop.png')
        self.points = self.points[::-1]
        self.contr = QHBoxLayout()
        self.f = QLabel()
        self.mainWidgetLayout.addStretch(2)
        self.mainWidgetLayout.addLayout(self.contr)
        self.rescanBut = QPushButton('Rescan')
        self.rescanBut.setMinimumSize(60, 20)
        self.rescanBut.clicked.connect(self.rescan)
        self.scanSlider = QSlider(Qt.Horizontal)
        self.contr.addWidget(self.rescanBut)
        self.contr.addWidget(self.scanSlider)
        self.timer =  QBasicTimer()
        self.polygon =  QPolygonF()
        self.angle =  90
    def start(self):
        #self.timer.start(100,  self)
        #self.sendData("connect19/9600")
        print("Started")
        print()
    def timerEvent(self,  event):
        if self.isConnectedFlag ==  True:
            self.receiveData()
            self.showMessage.emit(self.data)
            if self.data !=  None:
                if self.data ==  "Stop":
                    print("Stop")
                    self.timer.stop()
                else:
                    self.data =  self.data[:-5]
                    print(self.data)
                    i,  l =  map(int, self.data.replace('\n',  '').split('/'))
                    self.angle =  90 - i
                    x =  l *  math.cos(math.radians(i))
                    y =  l *  math.sin(math.radians(-i))
                    #self.polygon.append(QPointF(x,  y))
                    self.points.append((int(x * 8),  int(y * 8)))
                    print(self.points[-1])
        self.update()
    def rescan(self):
        geom =  self.geometry()
        print(geom)
        self.polygon = QPolygonF()
        self.polygon.append(QPointF(-geom.width()//2, -geom.height() // 2))
        self.polygon.append(QPointF(-geom.width()//2, -geom.height()*0.9))
        self.polygon.append(QPointF(geom.width()//2, -geom.height()*0.9))
        self.polygon.append(QPointF(geom.width()//2, -geom.height() // 2))
        
        self.points =  []
        self.sendData("rescan")
        self.update()
        self.timer.start(10,  self)
    def paintEvent(self, event):
        try:
            geom  = self.geometry()
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)   #smoothing for lines
            p.setRenderHint(QPainter.SmoothPixmapTransform)  #smoothing for Pixmap
            p.setPen(Qt.blue)     
            
            #drawing grid & scale numbers
            step = 20
            p.setOpacity(0.2)
            
            for i in range(geom.width()//step):
                p.drawLine(i*step, 0, i*step, geom.height()*0.9)
            for i in range(geom.height()//step):
                p.drawLine(0, i*step,  geom.width(), i*step) 
                
            p.setOpacity(0.7)
            p.translate(geom.width()//2, geom.height()*0.9)
            p.drawLine(0, 0, 200, 200)
            for i in range(-geom.width()//(step*2), geom.width()//(step*2), 2):
                p.drawText(i*step-10, 10, str(i*step))
            for i in range(0, -geom.height()//step, -2):
                p.drawText(-geom.width()//2, i*step+5, str(i*step))    
            #-----------------------------------------------------------
            
            #drawing locator
            p.setOpacity(1)
            p.drawLine(-geom.width()//2, 0, geom.width(), 0)   #hor Line
            
            p.rotate(self.angle)
            p.drawLine(0, 0, 0, -geom.height()) #rotatable line
            p.drawPixmap(-20, -27, self.iconLocator) #locator icon
            #-----------------------------------------------------------
            
            #drawing barrier map
            p.rotate(-self.angle)
            p.setBrush(Qt.blue)
            p.setOpacity(0.2)
            
            
            for u in self.points:
                p.setOpacity(1)
                p.setBrush(QBrush(Qt.red,  Qt.SolidPattern))
                p.drawEllipse(u[0]-2, u[1]-2, 5, 5)
                p.setOpacity(0.2)
                p.setBrush(Qt.blue)
                self.polygon.append(QPointF(*u))
                
            p.drawPolygon(self.polygon)
        except:
            print("Error")

class Collisions(Widgets):
    coll = [False, False, False, False]
    def __init__(self, pasp):
        super().__init__(pasp)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        self.img = QPixmap('car.png')
        self.img = self.img.scaled(200, 94)
        self.imgSize = (200, 94)
        self.bordImg = QPixmap('border.png')
        self.bordImg = self.bordImg.scaled(120, 50)
        self.bordSize = (120, 50)
        self.bordPos = ( (-self.bordSize[0]//2, -self.imgSize[1]//2-55),
                         (-self.bordSize[0]//2, -self.imgSize[1]//2+100),
                         (-self.bordSize[0]//2, -self.imgSize[1]//2-100),
                         (-self.bordSize[0]//2, self.imgSize[1]//2+50) )
        self.coll = [True]*4
        self.alarm = QSound('frog.wav')
        self.contr = QHBoxLayout()
        self.f = QLabel()
        self.mainWidgetLayout.addStretch(2)
        self.mainWidgetLayout.addLayout(self.contr)
        self.rescanBut = QPushButton('Rescan')
        self.scanSlider = QSlider(Qt.Horizontal)
        self.contr.addWidget(self.rescanBut)
        self.contr.addWidget(self.scanSlider)        
    def paintEvent(self, event):
        geom = self.geometry()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)   #smoothing for lines
        p.setRenderHint(QPainter.SmoothPixmapTransform)  #smoothing for Pixmap        
        p.setPen(Qt.blue)
        p.setBrush(Qt.blue)
        p.translate(geom.width()//2, geom.height()//2)
        
        p.drawPixmap(-self.imgSize[0]//2, -self.imgSize[1]//2, self.img)
        p.setOpacity(0.7)
        
        for i in range(4):
            if i == 2: p.rotate(90)
            if self.coll[i]==True:
                p.drawPixmap(*self.bordPos[i], self.bordImg)
    def collisionFound(self, data):
        for i in range(4):
            if data[i] == True and self.coll[i]==False:
                self.alarm = QSound('frog.wav')
            self.coll[i] = data[i]
        self.update()
if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    sys.exit(app.exec_())