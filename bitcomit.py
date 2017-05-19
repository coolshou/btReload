#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 14 10:37:03 2017

@author: coolshou
"""
''' require lxml '''
try:
    # For Python 3.0 and later
    #from urllib.request import urlopen
    from urllib import request
except ImportError as e:
    # Fall back to Python 2's urllib2
    #from urllib2 import urlopen, request
    print(e)
from lxml import etree
from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot, QMutex, QThread)
from PyQt5.QtWidgets import (QApplication)
import os
import time
import shutil
import sys

locker = QMutex()

class btThread(QThread):
    def run(self):
        self.exec_()
        
class bitcomit(QObject):

    signal_debug = pyqtSignal(str, str)
    signal_finished = pyqtSignal()
    signal_errored = pyqtSignal()
    signal_countdown =pyqtSignal(int)
    
    def __init__(self, sUrl, sPort, sUser, sPassword, 
                 waittime = 60 , restart = True) :
        super(bitcomit, self).__init__(None)
        
        self.exiting = False
        self.interval = 1
        self.waittime = waittime # 60 * self.interval
        self.count = 0
        self.stop = False
        self.restart = restart
        
        self.initAuth( sUrl, sPort, sUser, sPassword)
            
    def __del__(self):
        ''' destructure?     '''
        self.exiting = True
        self.stop = False

    @pyqtSlot()
    def task(self):
        '''
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
        #exec by QThread.start()
        '''
        self.stop = False        
        self.exiting = False
        self.signal_debug.emit(self.__class__.__name__, 
                               "start monitor BitComit task")
        while not self.exiting:
            #do task          
            self.signal_countdown.emit(self.count)
            if self.count<=0:
                try:
                    self.doTaskControl()
                except:
                    self.traceback()
                    raise
                self.count=self.waittime 
            self.count = self.count - 1
            QApplication.processEvents() 
            #self.signal_debug.emit(self.__class__.__name__, "stop status: %s" % self.stop)
            
            time.sleep(self.interval)
            if self.stop:
                self.signal_debug.emit(self.__class__.__name__, "user stop!!")
                self.signal_finished.emit()
                break
            
        self.signal_debug.emit(self.__class__.__name__, "task end!!")

    @pyqtSlot()
    def do_stop(self):
        ''' stop the sender thread  '''
        locker.lock()
        #self.signal_debug.emit(self.__class__.__name__, "do_stop!!")
        self.stop = True
        locker.unlock()

    @pyqtSlot()        
    def do_resume(self):
        ''' resume the sender thread  '''
        locker.lock()
        self.stop = False
        locker.unlock()

    @pyqtSlot(bool)        
    def setRestart(self, bRestart):
        locker.lock()
        self.restart = bRestart
        locker.unlock()

    def initAuth(self, sUrl, sPort, sUser, sPassword):
        self.base_url = sUrl
        self.port= sPort
        self.username= sUser
        self.password= sPassword
        self.signal_debug.emit(self.__class__.__name__, 
                               "init:%s, %s, %s, %s" %(self.base_url, self.port, 
                                      self.username, self.password))
        # create a password manager
        password_mgr = request.HTTPPasswordMgrWithDefaultRealm()
        
        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        self.top_level_url = self.base_url + ":" +self.port #"http://192.168.10.108:24374"
        password_mgr.add_password(None, self.top_level_url, self.username, self.password)
        
        handler = request.HTTPBasicAuthHandler(password_mgr)
        
        # create "opener" (OpenerDirector instance)
        self.opener = request.build_opener(handler)
    
        # Install the opener.
        # Now all calls to urllib.request.urlopen use our opener.
        request.install_opener(self.opener)
        
    def doTaskControl(self):
        # use the opener to fetch a URL
        try:
            rows = self.getTaskListRows()
            targetList = list()
            for i in range( 1, len(rows)):
                #progress
                #progress = rows[i].getchildren()[5].text
                progress = self.getProgress(rows[i])
                #print(progress)
                if "100.0%" in progress: 
                    targetList.append(i-1)
            
            if (len(targetList) <= 0):
                self.signal_debug.emit(self.__class__.__name__, "Not found any finished bitcomit task")
            else:    
                for tRow in targetList:
                    #get bt task's file name with full path
                    f = self.getSaveFilename(tRow)
                    #print(f)
                    self.stopTask(tRow)
                    #make sure it is stoped
                    rows =self.getTaskListRows()
                    state = self.getState(rows[tRow+1])
                    if "stopped" in state:
                        #remove file
                        try:
                            self.signal_debug.emit(self.__class__.__name__, "going to remove: %s" % f)
                            self.remove(f)
                        except:
                            e = sys.exc_info()[0]
                            self.signal_debug.emit(self.__class__.__name__, "Error: %s" % e)
                            pass
                        if self.restart:
                            self.startTask(tRow)
                
        except:
            self.traceback()
            self.signal_errored.emit()
        finally:
            targetList = None
            rows = None

    def getTaskListRows(self):
        '''get task_list rows : /panel/task_list'''
        a_url=self.top_level_url+"/panel/task_list"
        self.signal_debug.emit(self.__class__.__name__, a_url)
        try:
            response = self.opener.open(a_url)
            html = response.read()
            #print(html.decode("utf-8"))
            page = etree.HTML(html.decode("utf-8") )
            #print(page.text)
            tables = page.xpath(u"//table[3]")
            rows = tables[0].findall("tr")
            return rows
        except:
            self.traceback()
            return []
        
    def getProgress(self, row):
        progress = row.getchildren()[5].text
        return progress
    
    def getState(self, row):
        state = row.getchildren()[2].text
        return state

    def getSaveFilename(self, idx):
        ''' task detail : /panel/task_detail?id=0 '''
        sUrl = self.top_level_url+"/panel/task_detail?id="+str(idx)
        t_response = self.opener.open(sUrl)
        t_html = t_response.read()
        t_page = etree.HTML(t_html.decode("utf-8") )
        #print(t_page)
        t_names = t_page.xpath(u"//tr[2]/td[2]")
        #get file name
        #print(t_names[0].text)
        return t_names[0].text
        
    def stopTask(self, idx):
        '''stop task : "/panel/task_action?id=0&action=stop"'''
        #print(sUrl)
        sUrl = self.top_level_url+"/panel/task_action?id="+str(idx)+"&action=stop"
        self.opener.open(sUrl)
        
    def startTask(self, idx):
        '''start task : "/panel/task_action?id=0&action=start"'''
        #print(sUrl)
        sUrl = self.top_level_url+"/panel/task_action?id="+str(idx)+"&action=start"
        self.opener.open(sUrl)

    def remove(self, path):
        """ param <path> could either be relative or absolute. """
        if os.path.isfile(path):
            os.remove(path)  # remove the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove dir and all contains
        else:
            raise ValueError("file {} is not a file or dir.".format(path))

    def traceback(self, err=None):
        exc_type, exc_obj, tb = sys.exc_info()
        # This function returns the current line number set in the traceback object.  
        lineno = tb.tb_lineno  
        self.signal_debug.emit(self.__class__.__name__, 
                               "%s - %s - Line: %s" % (exc_type, exc_obj, lineno))
        
if __name__ == "__main__":
    bt = bitcomit("http://192.168.10.108", "24374", "admin", "123456")
    bt.doTaskControl()