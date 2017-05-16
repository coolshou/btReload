#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 15 08:37:06 2017

@author: jimmy
"""
'''require PyQt5  '''

import sys
import datetime
from PyQt5.QtCore import (Qt, QObject, pyqtSignal, pyqtSlot, QSettings)
from PyQt5.QtWidgets import (QApplication, QMainWindow,
                             QPlainTextEdit, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel,
                             QLineEdit, QCheckBox)
import logging

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
        
        
class MainWindow(QMainWindow):
    '''
    MainWindow class
    '''
    def __init__(self):
        super(MainWindow, self).__init__()
        self.settings = QSettings()
        self.settings.setFallbacksEnabled(False)    # File only, no fallback to registry or or.
 
        self.initUI()
        
        self.setFixedSize(600, 400)
        
        
        XStream.stdout().messageWritten.connect( self.logTextEdit.insertPlainText )
        XStream.stderr().messageWritten.connect( self.logTextEdit.insertPlainText )
        
        self.worker = None
        self.worker_thread = None
                       
    def __del__(self):
        ''' destructure     '''    
        

    def closeEvent(self, event):
        print('Calling')
        print('event: {0}'.format(event))
        self.saveSetting()
        event.accept()

        
    def initUI(self):
        #UI
        self.tabLog = QWidget(self)
        self.topBar = QWidget(self.tabLog)
        self.logTextEdit = QPlainTextEdit(self.tabLog)
        self.buttonBar = QWidget(self.tabLog)
        layout = QVBoxLayout()
        layout.addWidget(self.topBar)
        layout.addWidget(self.logTextEdit)
        layout.addWidget(self.buttonBar)
        #topBar
        #   url
        self.urlBar = QWidget(self.topBar)
        self.lbUrlText = QLabel(self.urlBar)
        self.lbUrlText.setText("Bitcomit URL:")
        self.leUrl = QLineEdit(self.urlBar)
        self.leUrl.setText(self.settings.value('url', "http://127.0.0.1"))
        self.lbPortText = QLabel(self.urlBar)
        self.lbPortText.setText("Port:")
        self.lePort = QLineEdit(self.urlBar)
        self.lePort.setText(self.settings.value('port', "12345"))
        hlayout  = QHBoxLayout()
        hlayout.addWidget(self.lbUrlText)
        hlayout.addWidget(self.leUrl)
        hlayout.addWidget(self.lbPortText)
        hlayout.addWidget(self.lePort)
        self.urlBar.setLayout(hlayout)
        #   admin
        self.adminBar = QWidget(self.topBar)
        self.lbUserText = QLabel(self.adminBar)
        self.lbUserText.setText("Username:")
        self.leUser = QLineEdit(self.adminBar)
        self.leUser.setText(self.settings.value('username', "admin"))
        self.lbPassText = QLabel(self.adminBar)
        self.lbPassText.setText("password:")
        self.lePass = QLineEdit(self.adminBar)
        self.lePass.setText(self.settings.value('password', "123456"))
        self.cbRestart = QCheckBox(self.adminBar)
        self.cbRestart.setText("Start Task after delete file")
        self.cbRestart.setCheckState(int(self.settings.value('Restart', 2)))
        self.cbRestart.stateChanged.connect(self.setRestart)
        hlayout  = QHBoxLayout()
        hlayout.addWidget(self.lbUserText)
        hlayout.addWidget(self.leUser)
        hlayout.addWidget(self.lbPassText)
        hlayout.addWidget(self.lePass)
        hlayout.addWidget(self.cbRestart)
        self.adminBar.setLayout(hlayout)

        vlayout  = QVBoxLayout()
        vlayout.addWidget(self.urlBar)
        vlayout.addWidget(self.adminBar)
        self.topBar.setLayout(vlayout)
        
        #buttonBar
        self.lbWaitText = QLabel(self.buttonBar)
        self.lbWaitText.setText("Wait (s) to check")
        self.leWait = QLineEdit(self.buttonBar)
        self.leWait.setText(self.settings.value('Waittime', "60"))
        
        self.lbCountDownText = QLabel(self.buttonBar)
        self.lbCountDownText.setText("Next checking in:")
        self.lbCountDown = QLabel(self.buttonBar)
        self.btnStart = QPushButton(self.buttonBar)
        self.btnStart.setText("start")
        self.btnStart.clicked.connect(self.startMoni)
        self.btnStop = QPushButton(self.buttonBar)
        self.btnStop.setText("stop")
        self.btnStop.clicked.connect(self.stopMoni)
        self.setBtnMoni(0)
        hlayout  = QHBoxLayout()
        hlayout.addWidget(self.lbWaitText)
        hlayout.addWidget(self.leWait)
        hlayout.addWidget(self.lbCountDownText)
        hlayout.addWidget(self.lbCountDown)
        hlayout.addWidget(self.btnStart)
        hlayout.addWidget(self.btnStop)
        self.buttonBar.setLayout(hlayout)
        self.tabLog.setLayout(layout)
        
        self.setCentralWidget(self.tabLog)
        
    def setBtnMoni(self, startstop):
        ''' 1: '''
        if startstop:
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(True)
        else:
            self.btnStart.setEnabled(True)
            self.btnStop.setEnabled(False)
        
    def startMoni(self):
        if self.worker_thread is None:
            self.worker_thread = btThread()
            
        if self.worker is None:
            try:
                #self.log("startMoni","create worker connection")
                self.worker = bitcomit(self.leUrl.text(), self.lePort.text(), 
                                   self.leUser.text(), self.lePass.text(),
                                   int(self.leWait.text()))  # no parent!
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
        self.setBtnMoni(0)
        self.worker.do_stop()
    
    @pyqtSlot(int)
    def setRestart(self, state):
        if self.worker is None:
            return
        if state == Qt.Checked:
            self.worker.setRestart(True)
        else:
            self.worker.setRestart(False)
        
    def finished(self):
        self.setBtnMoni(0)
        # if you want the thread to stop after the worker is done
        # you can always call thread.start() again later
        if not self.worker_thread is None:
            self.worker_thread.quit()
        
    def errorHandle(self):
        self.log("errorHandle", "bitcomit error")
        self.stopMoni()
        self.worker_thread.terminate()
        self.worker_thread.wait(30000)
        self.worker_thread = None
        self.worker = None
            
    def log(self, sFrom, sMsg):
        self.logTextEdit.appendPlainText("[%s] %s : %s " 
                                         %(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"), 
                                           sFrom, sMsg))
        
    def updateCountDown(self, count):
        #TODO: CountDown label
        #self.log("main", str(count))
        self.lbCountDown.setText(str(count))

    def saveSetting(self):
        ''' save setting to setting file'''
        self.settings.setValue('url', self.leUrl.text())
        self.settings.setValue('port', self.lePort.text())
        self.settings.setValue('username', self.leUser.text())
        self.settings.setValue('password', self.lePass.text())
        self.settings.setValue('Restart', self.cbRestart.checkState())
        self.settings.setValue('Waittime', self.leWait.text())
        

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setOrganizationName("coolshou")
    app.setOrganizationDomain("coolshou.idv.tw");
    app.setApplicationName("btReload")
    MAINWIN = MainWindow()
    MAINWIN.setWindowTitle("Bitcomit reload Tesk")
    MAINWIN.show()


    sys.exit(app.exec_())