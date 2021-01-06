# -*- coding: utf-8 -*-
"""
OrthoViewLite.py
based on https://github.com/kklmn/OrthoView by Konstantin Klementiev
modified by Axel Schneider (added File Selector)
https://github.com/Axel-Erfurt
"""

__author__ = "Konstantin Klementiev"
__versioninfo__ = (1, 0, 2)
__version__ = '.'.join(map(str, __versioninfo__))
__date__ = "8 Feb 2020"
__license__ = "MIT license"

import os
import sys
import cv2
from matplotlib.figure import Figure
import numpy as np
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget,QAction, QFileDialog, QMenu, 
                             QToolBar, QHBoxLayout, QTreeView, QFileSystemModel, QSizePolicy, 
                             QMessageBox)
from PyQt5.QtCore import Qt, QDir, QStandardPaths, QFileInfo
import matplotlib.backends.backend_qt5agg as mpl_qt

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


selfDir = os.path.dirname(__file__)
iniApp = (os.path.join(selfDir, 'OrthoViewList.ini'))
config = ConfigParser(
    dict(pos='[0, 0]', corners='[None]*4', scalex=0, scaley=0))
config.add_section('window')
config.read(iniApp)


def write_config():
    with open(iniApp, 'w+') as cf:
        config.write(cf)


class MyToolBar(mpl_qt.NavigationToolbar2QT):
    def set_message(self, s):
        try:
            sstr = s.split()

            while len(sstr) > 5:
                del sstr[0]
            x, y = float(sstr[0][2:]), float(sstr[1][2:])
            s = f'x = {x:.2f}\ny = {y:.2f}'
        except Exception:
            pass

        if self.coordinates:
            self.locLabel.setText(s)


class MyMplCanvas(mpl_qt.FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.fig.patch.set_facecolor('None')
        super(MyMplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.updateGeometry()
        self.setupPlot()
        self.mpl_connect('button_press_event', self.onPress)
        self.img = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mouseClickPos = None

        self.menu = QMenu()


    def setupPlot(self):
        rect = [0., 0., 1., 1.]
        self.axes = self.fig.add_axes(rect)
        self.axes.axis("off")

    def imshow(self, img):
        if self.img is None:
            self.img = self.axes.imshow(img)
        else:
            prev = self.img.get_array()
            self.img.set_data(img)
            if prev.shape != img.shape:
                self.img.set_extent(
                    [-0.5, img.shape[1]-0.5, img.shape[0]-0.5, -0.5])
                self.axes.set_xlim((0, img.shape[1]))
                self.axes.set_ylim((img.shape[0], 0))
                self.toolbar.update()
        self.draw()

    def onPress(self, event):
        if (event.xdata is None) or (event.ydata is None):
            self.mouseClickPos = None
            return
        self.mouseClickPos = int(round(event.xdata)), int(round(event.ydata))


class OrthoView(QMainWindow):
    def __init__(self, parent=None):
        super(OrthoView, self).__init__(parent)

        self.setWindowTitle('OrthoViewLite')
        self.setStyleSheet("QMainWindow {background: #e9e9e9;} QHBoxLayout \
                            {background: #e9e9e9;} QTreeView {background: #e9e9e9;}  \
                            FigureCanvasQTAgg {background: #e9e9e9;} QToolBar {border: 0px;}")
        self.setMinimumSize(500, 350)
        self.image_file_path = ""   
        if config.has_option('window', 'win_left') and config.has_option('window', 'win_top') \
            and config.has_option('window', 'win_width') and config.has_option('window', 'win_height'):
            left = int(config.get('window', 'win_left'))
            top = int(config.get('window', 'win_top'))
            width = int(config.get('window', 'win_width'))
            height = int(config.get('window', 'win_height'))
            self.setGeometry (left, top, width, height)
            
        self.home_path = QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)[0]

        self.tb = QToolBar("File")
        
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tb.addWidget(empty)
        
        open_btn = QAction("Open Image File", self, triggered=self.openFile)
        open_btn.setIcon(QIcon.fromTheme("document-open"))
        self.tb.addAction(open_btn)
       
        go_up_btn = QAction("one level up", self, triggered=self.oneUp)
        go_up_btn.setIcon(QIcon.fromTheme("go-up"))
        self.tb.addAction(go_up_btn)
        
        go_home_btn = QAction("go to home", self, triggered=self.goHome)
        go_home_btn.setIcon(QIcon.fromTheme("go-home"))
        self.tb.addAction(go_home_btn)

        stretch = QWidget()
        stretch.setFixedWidth(200)
        self.tb.addWidget(stretch)

        self.plotCanvas = MyMplCanvas(self)
        self.plotCanvas.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = MyToolBar(self.plotCanvas, self)
        for action in self.toolbar.findChildren(QAction):
            if action.text() in ['Customize', 'Subplots']:
                action.setVisible(False)
        self.toolbar.locLabel.setAlignment(Qt.AlignRight)
        self.toolbar.locLabel.setFixedWidth(200)

        self.tb.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tb.setMovable(False)
        self.tb.setAllowedAreas(Qt.TopToolBarArea)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.addToolBar(self.toolbar)
        self.addToolBar(self.tb)

        
        mylayout = QHBoxLayout()
        mylayout.addWidget(self.plotCanvas)
        
        self.mylistwidget = QTreeView()
        self.mylistwidget.setFixedWidth(300)
        mylayout.addWidget(self.mylistwidget)
        
        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files | QDir.AllDirs)
        self.fileModel.setRootPath(QDir.homePath())
        
        self.mylistwidget.setModel(self.fileModel)
        self.mylistwidget.setRootIndex(self.fileModel.index(self.home_path))
        #self.mylistwidget.setRootIndex(self.fileModel.index("/"))
        
        self.mylistwidget.selectionModel().selectionChanged.connect(self.on_clicked)
        self.mylistwidget.clicked.connect(self.tree_clicked)
        col = [1, 2, 3, 4]
        for c in col:
            self.mylistwidget.hideColumn(c)
        
        mywidget = QWidget()
        mywidget.setLayout(mylayout)
        self.setCentralWidget(mywidget)
        
        self.myfilter = ["tif", "tiff", "png", "jpg"]
        self.treefilter = ["*.tif", "*.tiff", "*.png", "*.jpg"]
        
        self.fileModel.setNameFilters(self.treefilter)
        self.fileModel.setNameFilterDisables(False)

        self.mylistwidget.setFocus()        
        self.mylistwidget.resizeColumnToContents(1)

    def goHome(self):
       self.mylistwidget.setRootIndex(self.fileModel.index(self.home_path)) 
       
    def oneUp(self):
       self.mylistwidget.setRootIndex(self.mylistwidget.rootIndex().parent()) 

    def on_clicked(self):
        path = self.fileModel.fileInfo(self.mylistwidget.currentIndex()).absoluteFilePath()
        if QDir.exists(QDir(path)):
            print(path, "is folder")
        else:
            if QFileInfo(path).suffix() in self.myfilter:
                if not os.stat(path).st_size == 0:
                    print(path)
                    self.image_file_path = path
                    self.updateFrame()
                else:
                    print("file not exists or has size 0")
                    self.msgbox("File is empty (size 0)") 
                
    def tree_clicked(self):
        index = self.mylistwidget.currentIndex()
        if not self.mylistwidget.isExpanded(index):
            self.mylistwidget.setExpanded(index, True) 
            self.mylistwidget.resizeColumnToContents(0)
        else:
            self.mylistwidget.setExpanded(index, False) 
            self.mylistwidget.resizeColumnToContents(0)
        
    def openFile(self):
        print("open File Dialog")
        path, _ = QFileDialog.getOpenFileName(self, "Open File", self.image_file_path,"Image Files (*.tif *.tiff *.png *.jpg)")
        if path:
            if os.path.isfile(path) and not os.stat(path).st_size == 0:
                self.image_file_path = path
                print("file exists:",self.image_file_path)
                self.updateFrame()
            else:
                print("file not exists or has size 0")      
                self.msgbox("File is empty (size 0)")    


    def getFrame(self, path):
        if os.path.isfile(path):
            frame = cv2.imread(path, 1)
            if not np.shape(frame) == ():
                self.img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                print("Error!")
                frame = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                self.img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            self.openFile()

    def updateFrame(self):
        self.getFrame(self.image_file_path)
        overlay = self.img.copy()
        alpha = 0.75  # transparency factor
        imageNew = cv2.addWeighted(overlay, alpha, self.img, 1-alpha, 0)
        self.plotCanvas.imshow(imageNew)
        
    def closeEvent(self, e):
        config.set('window', 'win_left', str(self.geometry().x()))
        config.set('window', 'win_top', str(self.geometry().y()))
        config.set('window', 'win_width', str(self.geometry().width()))
        config.set('window', 'win_height', str(self.geometry().height()))
        
        with open(iniApp, 'w+') as cf:
            config.write(cf)

    def msgbox(self, message):
        msg = QMessageBox(2, "Error", message, QMessageBox.Ok)
        msg.exec()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QIcon(os.path.join(selfDir, '_static', 'orthoview.ico'))
    app.setWindowIcon(icon)

    window = OrthoView()
    window.show()
    sys.exit(app.exec_())
