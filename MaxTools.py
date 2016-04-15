'''
Created on Oct 25, 2011

Functions for interfacing with 3ds Max.

@author: dkorkh
'''

import win32com.client
import psutil
import _winreg
import threading
import socket
import os
import subprocess
import re
import NamingConvention
import time

class ExtensionError(Exception):
    def __init__(self, fp):
        self.fp = fp
    def __str__(self):
        return str(self.fp) + " extension mismatch."

class LoadingProgressThread(threading.Thread):
    def __init__(self, t, prgrs_obj):
        threading.Thread.__init__(self)
        self.t = t
        self.go = True
        self.prgrs_obj = prgrs_obj
    
    def run(self):
        '''Run in a separate thread while max is loading updating self.progress.'''
        p = 1.0
        incr = .1
        while self.t > 0 and self.go:
            time.sleep(incr)
            self.t -= incr
            p = p * .9
            if self.prgrs_obj:
                self.prgrs_obj.progress = 1.0 - p
        if self.prgrs_obj:
            self.prgrs_obj.progress = 1.0
        

class Max_Session(object):
    def __init__(self,launchscript,port, prgrs_obj = None):
        self.prgrs_obj = prgrs_obj
        self.timeout = 15
        self.launchscript = launchscript
        self.port = port
        self.ms = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ok = True
        self.progress = 0.0 #fake exponential approaching 1
        try:
            if self.prgrs_obj:
                progressthread = LoadingProgressThread(7.0, self.prgrs_obj)
                progressthread.start()
            self.ms.bind(("127.0.0.1",self.port))
            self.ms.listen(1)
            subprocess.Popen(getMaxInstallDir()+"3dsmax.exe -q - silent -mi -U MAXScript "+self.launchscript)
            print "cm: "+getMaxInstallDir()+"3dsmax.exe -q - silent -mi -U MAXScript "+self.launchscript
            self.con = self.ms.accept()[0]
            self.maxMessenger = Max_Socket(self.con)
            self.maxMessenger.start()
            self.command("OK")
        except:
            if self.prgrs_obj:
                progressthread.go = False
            self.ok = False
        if self.prgrs_obj:
            progressthread.go = False

    
    def command(self,s):
        self.maxMessenger.response = False
        self.maxMessenger.outbox = s
        if s == "EXIT":
            return None
        while not self.maxMessenger.response:
            pass
        ret = self.maxMessenger.inbox
        self.maxMessenger.inbox = None
        return ret
    
    def openFile(self,fp):
        self.command("loadMaxFile \""+fp+"\" quiet:True")
        
    def getSelected(self):
        selected = self.command("$ as array")
        if type(selected) == type([]):
            selected = self.obArrayToNames(selected)
            return selected
        elif self.command("$.name").lower() != "false":
            return [self.command("$.name")]
        else:
            return []
    
    def charExport(self):
        self.command("macros.run \"cryptic\" \"char_Export\";")
    
    def close(self):
        self.command("EXIT")
    
    def getClosestGeoName(self,s):
        s = NamingConvention.Name(s)
        geos = self.getGeometry()
        return s.closestName(geos)
    
    def obArrayToNames(self,ob_ar):
        '''Given an list of objects from max, returns the list with names stripped of pos and type'''
        ret_l = []
        for o in ob_ar:
            o = re.match(".*:([a-zA-Z0-9_]+)", o)
            if o:
                ret_l.append(o.group(1))
        return ret_l
    
    def getGeometry(self):
        '''return a list of editable_poly objects in the scene'''
        geo = self.command("$geometry as array")
        geo = self.obArrayToNames(geo)
        return geo
    
    def fileIn(self, fp):
        return self.command("fileIn \""+fp+"\";")
    
    def getVertPrint(self, o_name):
        '''Return a list of vert positions where the list index is the (vert number - 1)'''
        vert_p = self.command("for vert in $"+o_name+".verts collect vert.pos;")
        for i in range(len(vert_p)):
            vert_p[i] = map(lambda x : float(x), vert_p[i].strip("[]").split(","))
        return vert_p
    
    def rename(self,o_name, new_name):
        self.command("$"+o_name+".name = \"" + new_name + "\"")
    
    def resetXForm(self, o_name):
        children = self.command("$"+o_name+".children")
        if type(children) == type([]):
            for child in children:
                self.command("$"+child+".parent = undefined")
        self.command("resetXForm $"+o_name)
        self.command("collapseStack $"+o_name)
        if type(children) == type([]):
            for child in children:
                self.command("$"+child+".parent = $"+o_name)
                
    def select(self,o_name, children = False):
        '''Select object named o_name, if children is True also select its children.'''
        self.command("select $"+o_name)
        if children:
            self.command("selectMore $.children;")
        
    
    def save(self):
        '''save file'''
        self.command("saveMaxFile (maxFilePath+maxFileName) quiet:True")
    
    def saveAs(self, path):
        '''save file to a path.'''
        self.command("saveMaxFile \""+path+"\" quiet:True")
        
    def exportSelectedWRL(self, path):
        '''export selected to a WRL file at path.'''
        if not path.lower().endswith("wrl"):
            raise ExtensionError(path)
        self.command("exportFile \""+path+"\" #noPrompt selectedOnly:True;")
        
    def getPath(self):
        '''Return the current files path.'''
        p = self.command("maxFilePath + maxFileName").replace("\\","/")
        return p

class Max_Session_2013x64(Max_Session):
    def __init__(self, launchscript, port, prgrs_obj = None):
        self.prgrs_obj = prgrs_obj
        self.timeout = 15
        self.launchscript = launchscript
        self.port = port
        self.ms = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ok = True
        self.progress = 0.0 #fake exponential approaching 1
        try:
            if self.prgrs_obj:
                progressthread = LoadingProgressThread(7.0, self.prgrs_obj)
                progressthread.start()
            self.ms.bind(("127.0.0.1",self.port))
            self.ms.listen(1)
            subprocess.Popen(getMaxInstallDir_2013x64()+"3dsmax.exe -q -silent -mip -U MAXScript "+self.launchscript)
            print "cm: "+getMaxInstallDir_2013x64()+"3dsmax.exe -q -silent -mip -U MAXScript "+self.launchscript
            self.con = self.ms.accept()[0]
            self.maxMessenger = Max_Socket(self.con)
            self.maxMessenger.start()
            self.command("OK")
        except:
            if self.prgrs_obj:
                progressthread.go = False
            self.ok = False
        if self.prgrs_obj:
            progressthread.go = False

class Max_Socket(threading.Thread):
    def __init__(self,sock):
        threading.Thread.__init__(self)
        self.response = False
        self.outbox = None
        self.inbox = None
        self.running = False
        self.con = sock 
    
    def run(self):
        self.running = True
        print "------connection established."
        while self.running:
            if self.outbox:
                print "------sending..."
                self.sendMessage(self.outbox)
                if self.outbox == "EXIT":
                    self.running = False
                    break
                self.outbox = None
                print "------receiving..."
                self.receiveMessage()
                self.response = True
        
    def sendMessage(self,message):
        message = str(message)
        self.con.send(message)
        print "\tsent: "+message
    
    def receiveMessage(self):
        self.inbox = None
        while (not self.inbox) and (type(self.inbox) != type([])):
            self.inbox = self.con.recv(8192)
            if self.inbox == "ID_ARRAY_START":
                print "\t\tdetected an array - switching to array mode..."
                self.receiveArray()
        print "\treceived: "+str(self.inbox)
    
    def receiveArray(self):
        '''receiveMessage switches to this loop if the receive value is an array.'''
        ar = []
        resp = None
        self.con.send("OK")
        while True:
            resp = self.con.recv(8192)
            if resp == "ID_ARRAY_END":
                break
            ar.append(resp)
            self.con.send("OK")
        self.inbox = ar

def getMaxInstallDir():
    """return the install directory of 32 bit max."""
    handle = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"SOFTWARE\\Autodesk\\3dsMax\\11.0\\MAX-1:409\\AdLM")
    installDir = _winreg.QueryValueEx(handle,"InfoPath")[0]
    _winreg.CloseKey(handle)
    return installDir

def getMaxInstallDir_2013x64():
    """return the install directory of 3ds Max 2013 64bit."""
    handle = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"SOFTWARE\\Autodesk\\3dsMax\\15.0", 0, (_winreg.KEY_WOW64_64KEY + _winreg.KEY_READ))
    _winreg.DisableReflectionKey(handle)
    installDir = _winreg.QueryValueEx(handle,"Installdir")[0]
    _winreg.CloseKey(handle)
    return installDir

def messageMax(message):
    maxCOM = win32com.client.Dispatch("Max.Application.11")
    maxCOM._FlagAsMethod("maxCommand")
    return maxCOM.maxCommand(message)
    
def messageMax_2013x64(message):
    maxCOM = win32com.client.Dispatch("Max.Application.13")
    maxCOM._FlagAsMethod("maxCommand")
    return maxCOM.maxCommand(message)

def openFile(filePath):
    pass

def isMaxOpen():
    pids = psutil.get_pid_list()
    for pid in pids:
        process = psutil.Process(pid)
        if process.name == "3dsmax.exe":
            return True
    return False

def compVertPrints(vp1, vp2, tolerance = .0001):
    '''return True if vertex print 1 equals vertex print 2'''
    if len(vp1)!=len(vp2):
        return False
    for v1, v2 in zip(vp1,vp2):
        for vc1, vc2 in zip(v1,v2):
            d = vc1 - vc2
            d = d if d > 0 else d*-1
            if d > tolerance:
                return False
    return True


if __name__ == "__main__":
    pass