#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 15 08:37:06 2017

@author: jimmy
"""
'''require PyQt5  '''

__version__ = "20170626"


import platform
import sys
import datetime
from PyQt5.QtCore import (Qt, QObject, pyqtSignal, pyqtSlot, QSettings,
                          QEvent, QTimer)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QMenu, QSystemTrayIcon, QMessageBox)
from PyQt5.QtGui import (QIcon)
from PyQt5.uic import loadUi
import logging
import webbrowser

from bitcomit import bitcomit, btThread

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
        # originally: XStream.stdout().write("{}\n".format(record))


logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class XStream(QObject):
    _stdout = None
    _stderr = None
    messageWritten = pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(msg)
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr
        
class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        #menu = QMenu(parent)
        self.show_action = QAction("Show", self)
        #self.show_action.triggered.connect(qApp.show)
        self.hide_action = QAction("Hide", self)
        #self.hide_action.triggered.connect(self.hide)
        self.quit_action = QAction("Exit", self)
        self.quit_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.hide_action)        
        tray_menu.addSeparator()
        tray_menu.addAction(self.quit_action)

        self.setContextMenu(tray_menu)
        
class MainWindow(QMainWindow):
    '''     MainWindow class     '''
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.settings = QSettings('btReload.ini', QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only, no fallback to registry or or.
        
        if platform.system() == "Windows":
            self.RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            self.regSettings = QSettings(self.RUN_PATH, QSettings.NativeFormat)
        if getattr( sys, 'frozen', False ) :
            # running in a bundle
            bundle_dir = sys._MEIPASS
            ui = '%s/btMainWindow.ui' % bundle_dir
            mainicon = '%s/btReload.png' % bundle_dir
        else:
            ui = 'btMainWindow.ui'
            mainicon = 'btReload.png'
        loadUi(ui,self)
        self.loadSetting()
        self.cbRestart.stateChanged.connect(self.setRestart)
        self.btnStart.clicked.connect(self.startMoni)
        self.btnStop.clicked.connect(self.stopMoni)
        self.cbLaunchOnSystemStart.stateChanged.connect(self.setBootStart)
        self.cbMinimizeToTray.stateChanged.connect(self.setSystemTray)
        self.btnBrowser.clicked.connect(self.openBrowser)
        self.createMenuAction()
        self.setBtnMoni(0)

        self.setFixedSize(600, 400)
        self.setWindowIcon(QIcon(mainicon))
        
        XStream.stdout().messageWritten.connect( self.logTextEdit.insertPlainText )
        XStream.stderr().messageWritten.connect( self.logTextEdit.insertPlainText )
        
        self.worker = None
        self.worker_thread = None
        
        self.timer = QTimer()
        #self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timerTimeout)
        self.timerCount = 0
    
        # Init QSystemTrayIcon
        self.trayIcon = SystemTrayIcon(QIcon(mainicon), self)
        self.trayIcon.show_action.triggered.connect(self.showUI)
        self.trayIcon.hide_action.triggered.connect(self.hide)
        self.trayIcon.activated.connect(self.systemTrayHandle)
        if (self.cbMinimizeToTray.isChecked()):
            self.trayIcon.show()
        #    self.hide()
        
        
        
    def __del__(self):
        ''' destructure     '''    
        
    def createMenuAction(self):
        
        self.actAbout = QAction("About", self)
        self.actAbout.triggered.connect(self.showAbout)
        self.menuAbout.addAction(self.actAbout)
        
    @pyqtSlot()
    def showAbout(self):
        #print("showAbout")
        sVer = "Version: %s\n" % __version__
        #if self.worker:
        sVer = sVer + " bitcomit.py version: %s" % bitcomit.__version__
        
        QMessageBox.information(self, "About - %s" % self.windowTitle(), 
                                sVer , QMessageBox.Ok)
        
        
    def closeEvent(self, event):
        self.saveSetting()
        if self.cbMinimizeToTray.isChecked():
            event.ignore()
            self.hide()
            #self.trayIcon.showMessage(
            #    "btReload",
            #    "Application was minimized to system Tray",
            #    QSystemTrayIcon.Information,
            #    4000
            #)
        else:
            if self.timer.isActive():
                self.timer.stop()
            self.trayIcon.hide()
            event.accept()
    
    def changeEvent(self, e):
        if(e.type() == QEvent.WindowStateChange and self.isMinimized()):
            self.hide()
            e.accept()
            return
        else:
            super(MainWindow, self).changeEvent(e)
            
    @pyqtSlot()    
    def showUI(self):
        self.show()
        if self.isMinimized():
            self.setWindowState(Qt.WindowNoState)

    def systemTrayHandle(self, reason):
        #if reason == QSystemTrayIcon.Trigger:
        #    print('Clicked')
        if reason == QSystemTrayIcon.DoubleClick:
            self.showUI()
            #print('DoubleClick')
        
    def loadSetting(self):
        self.leUrl.setText(self.settings.value('url', "http://127.0.0.1"))
        self.lePort.setText(self.settings.value('port', "12345"))
        self.leUser.setText(self.settings.value('username', "admin"))
        self.lePass.setText(self.settings.value('password', "123456"))
        self.sbWait.setValue(int(self.settings.value('Waittime', "60")))
        self.cbRestart.setCheckState(int(self.settings.value('Restart', 2)))
        self.cbLaunchOnSystemStart.setCheckState(int(self.settings.value('LaunchOnSystemStart', 2)))
        self.cbMinimizeToTray.setCheckState(int(self.settings.value('MinimizeToTray', 2)))
        if (int(self.settings.value('RecheckBitcomit', 1)) == 1):
            RecheckBitcomit = True
        else:
            RecheckBitcomit = False
        self.RecheckBitcomit.setChecked(RecheckBitcomit)
        self.sb_recheckWait.setValue(int(self.settings.value('RecheckWait', 60)))
        

    def setBtnMoni(self, startstop):
        ''' 1: '''
        if startstop:
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(True)
        else:
            self.btnStart.setEnabled(True)
            self.btnStop.setEnabled(False)
        
    def startMoni(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.worker_thread is None:
            self.worker_thread = btThread()
            
        if self.worker is None:
            try:
                #self.log("startMoni","create worker connection")
                self.worker = bitcomit(self.leUrl.text(), self.lePort.text(), 
                                   self.leUser.text(), self.lePass.text(),
                                   int(self.sbWait.text()))  # no parent!
                self.worker.signal_debug.connect(self.log)
                self.worker.signal_countdown.connect(self.updateCountDown)
                self.worker.signal_errored.connect(self.errorHandle)
                self.worker.signal_finished.connect(self.finished)
                
                self.worker.moveToThread(self.worker_thread)
                self.worker_thread.started.connect(self.worker.task)
                self.worker_thread.start()
                self.setBtnMoni(1)
            except:
                exc_type, exc_obj, tb = sys.exc_info()
                # This function returns the current line number set in the traceback object.  
                lineno = tb.tb_lineno  
                self.log(self.__class__.__name__, "%s - %s" % (exc_type, lineno))
                raise
        else:
            self.log("startMoni","worker exist, thread running:%s" % self.worker_thread.isRunning())
            self.worker.do_resume()
            self.worker_thread.start()
            self.setBtnMoni(1)
            
        
    def stopMoni(self):
        if self.timer.isActive():
            self.timer.stop()
        self.setBtnMoni(0)
        if not self.worker is None:
            self.worker.do_stop()
    
    @pyqtSlot(int)
    def setRestart(self, state):
        if self.worker is None:
            return
        if state == Qt.Checked:
            self.worker.setRestart(True)
        else:
            self.worker.setRestart(False)
            
    @pyqtSlot(int)
    def setBootStart(self, state):
        if platform.system() == "Windows":
            if ( state == Qt.Checked):
                self.regSettings.setValue("btReload",sys.argv[0]);
            else:
                self.regSettings.remove("btReload");
                
    @pyqtSlot(int)
    def setSystemTray(self, state):
        if ( state == Qt.Checked):
            self.trayIcon.show()
        else:
            self.trayIcon.hide()
            
    @pyqtSlot()
    def timerTimeout(self):
        #self.log("timerTimeout", "timerTimeout: try startMoni()")
        timeLeave = self.sb_recheckWait.value() - self.timerCount
        self.updateTimerCountDown(timeLeave)
        if ( timeLeave <= 0):
            self.timerCount = 0
            self.startMoni()
        self.timerCount = self.timerCount + 1
        
    def finished(self):
        self.setBtnMoni(0)
        # if you want the thread to stop after the worker is done
        # you can always call thread.start() again later
        if not self.worker_thread is None:
            self.worker_thread.quit()
        
    def errorHandle(self):
        self.log("errorHandle", "bitcomit error")
        self.stopMoni()
        if not self.worker_thread is None:
            self.worker_thread.terminate()
            self.worker_thread.wait(30000)
        self.worker_thread = None
        self.worker = None
        if self.RecheckBitcomit.isChecked():
            self.timer.start(1000)
            
    def log(self, sFrom, sMsg):
        self.logTextEdit.appendPlainText("[%s] %s : %s " 
                                         %(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"), 
                                           sFrom, sMsg))
        
    def updateTimerCountDown(self, count):
        self.statusbar.showMessage("Check bitcomit in %s sec" % str(count))

    def updateCountDown(self, count):
        self.statusbar.showMessage("Next check in %s sec" % str(count))
        
    def saveSetting(self):
        ''' save setting to setting file'''
        self.settings.setValue('url', self.leUrl.text())
        self.settings.setValue('port', self.lePort.text())
        self.settings.setValue('username', self.leUser.text())
        self.settings.setValue('password', self.lePass.text())
        self.settings.setValue('Restart', self.cbRestart.checkState())
        self.settings.setValue('Waittime', self.sbWait.text())
        self.settings.setValue('LaunchOnSystemStart', self.cbLaunchOnSystemStart.checkState())
        self.setBootStart(self.cbLaunchOnSystemStart.checkState())
        self.settings.setValue('MinimizeToTray', self.cbMinimizeToTray.checkState())
        if self.RecheckBitcomit.isChecked():
            RecheckBitcomit = 1
        else:
            RecheckBitcomit = 0
        self.settings.setValue('RecheckBitcomit', RecheckBitcomit)
        self.settings.setValue('RecheckWait', self.sb_recheckWait.value())

    def openBrowser(self):
        ''' open system's browser '''
        user = self.leUser.text()
        pw = self.lePass.text()
        url = self.leUrl.text()
        '''IE6 (KB832894) and above not support Basic authentication with URL
         eg: http(s)://user:passwaord@url:port
        '''
        if (url.find("http://") == -1):
          url = "http://%s" % url
        '''
            url = "http://%s:%s@%s" % (user, pw, url)
        else:
            url = url[:7] + user + ':' + pw + '@' + url[7:]
        '''    
        port =  self.lePort.text()
        print("launch browser with url: %s:%s" % (url, port))
        webbrowser.open("%s:%s" % (url,port) , new=2)
        
# main
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setOrganizationName("coolshou")
    app.setOrganizationDomain("coolshou.idv.tw");
    app.setApplicationName("btReload")
    #AppUserModelID
    if platform.system() == "Windows":
        import ctypes
        myappid = u'btReload.coolshou.idv.tw' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    MAINWIN = MainWindow()
    MAINWIN.setWindowTitle("Bitcomit reload Task")
    MAINWIN.show()


    sys.exit(app.exec_())
    