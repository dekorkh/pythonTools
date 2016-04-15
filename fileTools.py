'''
Created on Sep 18, 2011

Mostly short recipies and tools for working with basic fileIO

Methods:
writedict() -- Format a dictionary into a text file in a simple tabbed hierarchy.

@author: dkorkh
'''

import os
import re
from time import sleep
import hashlib
import json
import printtools

def getRelativePathFrom(src_abs_path, trg_abs_path):
    r"""Return the trg_abs_path as a relative path to src_abs_path."""
    ret_path = ''
    src_abs_path = src_abs_path.lower().replace('\\', '/')
    trg_abs_path = trg_abs_path.lower().replace('\\', '/')
    trg_fn = getFileName(trg_abs_path)
    src_abs_path = getDirectory(src_abs_path)
    trg_abs_path = getDirectory(trg_abs_path)
    src_tk_path = src_abs_path.split('/')
    trg_tk_path = trg_abs_path.split('/')
    minlen = min([len(src_tk_path),len(trg_tk_path)])
    for i in range(minlen):
        if src_tk_path[0] == trg_tk_path[0]:
            src_tk_path.pop(0)
            trg_tk_path.pop(0)
    ret_path += '/'.join([".." for x in src_tk_path])
    ret_path = '/'.join([ret_path] + trg_tk_path)
    if trg_fn:
        ret_path = '/'.join([ret_path, trg_fn])
    else:
        ret_path += '/'
    ret_path = ret_path.lstrip('/')
    return ret_path

def checkOutFile(filePath):
    if os.access(filePath, os.F_OK) and not os.access(filePath, os.W_OK):
        os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -nowarn -quiet -ignoreerrors -editor null " + "\"" +filePath + "\"")

def statFile(filePath):
    r"""Print the stats of the file to the console."""
    os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -cstat " + "\"" +filePath + "\"")

def checkOutMany(filepath_list, batch_size = 100):
    #filter out write_enabled files
    filepath_list = filter(lambda x: not os.access(x, os.W_OK), filepath_list)
    #send by batches of 50
    while len(filepath_list) > batch_size:
        joinpaths = ['\"'+x+'\"' for x in filepath_list[:batch_size]]
        joinpaths = ';'.join(joinpaths)
        os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -nowarn -quiet -ignoreerrors -editor null " + joinpaths)
        filepath_list = filepath_list[batch_size:]
    #send any that remain
    if len(filepath_list):
        joinpaths = ['\"'+x+'\"' for x in filepath_list]
        joinpaths = ';'.join(joinpaths)
        os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -nowarn -quiet -ignoreerrors -editor null " + joinpaths)

def unCheckOutMany(filepath_list):
    #filter out write_enabled files
    filepath_list = filter(lambda x: os.access(x, os.W_OK), filepath_list)
    #send by batches of 50
    while len(filepath_list) > 50:
        joinpaths = ['\"'+x+'\"' for x in filepath_list[:50]]
        joinpaths = ';'.join(joinpaths)
        os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -undo " + joinpaths)
        filepath_list = filepath_list[50:]
    #send any that remain
    if len(filepath_list):
        joinpaths = ['\"'+x+'\"' for x in filepath_list]
        joinpaths = ';'.join(joinpaths)
        os.system("C:\\Cryptic\\tools\\bin\\gimme.exe -undo " + joinpaths)

def canWrite(filePath):
    if os.access(filePath, os.F_OK) and not os.access(filePath, os.W_OK):
        return False
    else:
        return True
    
def exists(filePath):
    if os.access(filePath, os.F_OK):
        return True
    else:
        return False

def getDirectory(filePath):
    """Return a directory path to the file."""
    if os.path.isdir(filePath):
        return filePath
    return os.path.dirname(filePath)

def getFileName(filePath):
    """Return the file name given the full path."""
    return os.path.basename(filePath)

def fileKey(filePath):
    """Return the lowercase name of the file without extension."""
    if os.path.isfile(filePath):
        return os.path.basename(filePath).lower().split(".")[0]

def fileExt(filePath):
    """Return the lowercase extension of the file without a dot."""
    if os.path.isfile(filePath):
        return os.path.basename(filePath).lower().split(".")[-1]
    
def delete(filePath):
    os.remove(filePath)
    
def searchFiles(directory, fileType = ".", name_srch_rgx = ".*", exact = False):
        
    #define vars
    fileList = [] #will store all files found by type and filter
    print "searching for "+fileType+" files...",
    if exact:
        print "\twith exact name: "+name_srch_rgx
    if name_srch_rgx != ".*":
        print "\tfor "+name_srch_rgx+" in the name...",
    #search files by type and filter
    for root, dirs, files in os.walk(directory, topdown=True):
        for each in files:
            #re.search takes 2 strings as arguments, if the first string is found in the second, returns true
            #str.lower() converts all values in the string to lowercase to avoid case mismatch
            if exact:
                if re.search((fileType.lower()+"$"), each.lower()):
                    if each.lower() == name_srch_rgx.lower():
                        fileList.append(root+"/"+each)
            elif re.search(name_srch_rgx.lower(), each.lower()) and re.search((fileType.lower()+"$"), each.lower()):
                #add files to the list with their path
                fileList.append(root+"/"+each)
    print "complete"
    for index in xrange(len(fileList)):
        fileList[index] = fileList[index].replace("\\","/")
    return fileList

def searchFilesToDict(directory, fileType = ".", name_srch_rgx = ".*", exact = False):
    r"""Search for files and return a dictionary of paths with lowercase filename without extension as keys."""
    return groupFilesByNameFlat(searchFiles(directory      = directory,
                                            fileType       = fileType,
                                            name_srch_rgx  = name_srch_rgx,
                                            exact          = exact))

def waitForFile(fp,mx=5,incr=.1):
    """
    
    run until the file is writable or max time runs out
    return True if file becomes writeable before time runs out, False otherwise
    
    """
    w = False
    while((not os.access(fp, os.W_OK)) and (mx > 0)):
        sleep(incr)
        mx -= incr
    if os.access(fp, os.W_OK):
        w = True
    return w

def genUID(s,l):
    hashedLogName = hashlib.sha1(s).hexdigest()
    return hashedLogName[:l]

class Config_Data(object):
    def __init__(self,fp):
        self.fp = fp
    
    def load(self):
        f = open(self.fp,"r")
        d = json.load(f)
        self.__dict__ = dict(d.items() + self.__dict__.items())
        f.close()
    
    def save(self):
        f = open(self.fp,"w")
        json.dump(self.__dict__,
                  f,
                  indent = 2,
                  sort_keys = True)
        f.close()
        
    def set(self, setting, value):
        '''create/overwrite a setting.'''
        self.__dict__[setting] = value



class FileList(object):
    """gets a list of files based on extension and stores/loads them from a .txt
    to avoid unnecessary searches."""
    
    def __init__(self, root, ext, manifest, regex = ".*"):
        self.ext        = ext
        self.root       = root
        self.regex      = regex
        self.manifest   = manifest
        self.fp_list    = []
        if not os.access(self.manifest, os.F_OK):
            self.fp_list = searchFiles(self.root, self.ext, self.regex)
            self.saveFileList()
        else:
            self.loadFileList()
    
    def __printFileFromPath(self, fp):
        fname = os.path.basename(fp)
        print "{}{}{}".format("-"*(40-len(fname)/2), fname, "-"*(40-len(fname)/2))
        with open(fp, "r") as f:
            for line in f:
                print line,
        print "-"*80
    
    def __printFileFromIndex(self, index):
        fp = self.fp_list[index]
        self.__printFileFromPath(fp)
        
    def __getFileFromPath(self, fp):
        with open(fp, "r") as f:
            return f.read()
    
    def __getFileFromIndex(self, index):
        fp = self.fp_list[index]
        return self.__getFileFromPath(fp)
        
    
    def saveFileList(self):
        """Save the list of files into a txt to avoid searching over and over."""
        with open(self.manifest, "w") as f:
            for fp in self.fp_list:
                f.write(fp+"\n")

    def loadFileList(self):
        """Return a list of file paths from a file."""
        with open(self.manifest, "r") as f:
            for line in f:
                self.fp_list.append(line.strip())
                
    def updateManifest(self):
        """Do another search for the files and update the manifest"""
        self.fp_list = searchFiles(self.root, self.ext, self.regex)
        self.saveFileList()
        
    def printFile(self, arg):
        """Print the contents of a file at index."""
        if type(arg) == str:
            self.__printFileFromPath(arg)
        elif type(arg) == int:
            self.__printFileFromIndex(arg)
        
    def filter(self, rgx):
        """return a list of files who's basename is a regexmatch"""
        return filter(lambda x: re.match(rgx, os.path.basename(x)), self.fp_list)
    
    def getFile(self, arg):
        """Return the contents of a file at index."""
        if type(arg) == str:
            return self.__getFileFromPath(arg)
        elif type(arg) == int:
            return self.__getFileFromIndex(arg)
    
    def dir(self):
        '''print files with their indeces'''
        for i, fp in enumerate(self.fp_list):
            print "{:50}{:}".format(os.path.basename(fp),i)
    
    def getFiles(self):
        '''Return a list of files.'''
        return self.fp_list

def writedict(dictionary, filepath, sort = True):
    r"""Format a dictionary into a text file in a simple tabbed hierarchy.
    
    Keyword arguments:
    sort  -- Dictionary keys and entries will be sorted using basic sort().
    
    Nested dictionaries will be formatted recursively, lists formatted by
    entry per line and all other objects will user their native __str__ 
    representations."""
    def formatdicttos(d, depth):
        s = ''
        keys = d.keys()
        if sort:
            keys.sort()
        for k in keys:
            v = d[k]
            s = ''.join([s, '\t'*depth, str(k), '\n'])
            if type(v) != list:
                if type(v) == dict:
                    s = ''.join([s,formatdicttos(v, depth + 1)])
                    continue
                s = ''.join([s, '\t'*(depth + 1), str(v), '\n'])
                continue
            if sort:
                v.sort()
            for e in v:
                if type(e) == dict:
                    s = ''.join([s,formatdicttos(e, depth + 1)])
                else:
                    s = ''.join([s, '\t'*(depth + 1), str(e), '\n'])
        return s
    writestring = formatdicttos(dictionary, 0)
    f = open(filepath, 'w')
    try:
        f.write(writestring)
    finally:
        f.close()

#FILE PARSING UTILITIES
def readFile(filepath, strip_nl = False):
    r"""Return a list of lines from a file.
    Arguments:
    filepath -- The path to the file.
    Keyword Arguments:
    strip_nl -- If True will strip the new line chars from each line. (default: False)"""
    f = open(filepath, 'r')
    lines = f.readlines()
    f.close()
    if strip_nl:
        lines = [x.strip('\n') for x in lines]
    return lines

def readCSV(filepath, delimiter = ','):
    r"""Return a rectangular list from a csv.
    delimiter  -- use this token to split the columns. (default = ,)."""
    f = open(filepath, 'r')
    lines = f.readlines()
    f.close()
    rows = []
    for line in lines:
        line = line.replace(' ','').strip()
        columns = [x for x in line.split(delimiter)]
        rows.append(columns)
    return rows

def writeCSV(filepath, nestedlist, delimiter = ','):
    r"""Write a nested list into a csv."""
    f = open(filepath, 'w')
    f.writelines('\n'.join([','.join([str(e) for e in line]) for line in nestedlist]))
    f.close()

def writeFile(filepath, lines, nl = False):
    r"""Write a list of strings to file, joined by new lines if nl is True."""
    nl = '\n' if nl else ''
    f = open(filepath, 'w')
    f.writelines(nl.join(lines))
    f.close()

def groupFilesByName(file_list, preserveCase = False):
    '''return a dictionary of files from file_list using the basename minus extension as keys.
    {filename : {ext : filepath, ...},...}'''
    file_dict = {}
    for f in file_list:
        fname = os.path.basename(f).lower().split('.')[0]
        ext = os.path.basename(f).lower().split('.')[-1]
        if not fname in file_dict:
            file_dict[fname] = {ext : None}
        file_dict[fname][ext] = f if preserveCase else f.lower()
    return file_dict

def groupFilesByNameFlat(file_list, preserveCase = False):
    '''return a dictionary of files from file_list using the basename minus extension as keys.
    {filename : filepath ,..}'''
    file_dict = {}
    for f in file_list:
        fname = os.path.basename(f).lower().split('.')[0]
        file_dict[fname] = f if preserveCase else f.lower()
    return file_dict

#FILE WRITING UTILITIES
def writeListDict(fobject, somedict, label):
    fobject.write(label+'\n')
    for k, v in somedict:
        fobject.write(k+'\n')
        fobject.write('\t'+'\n\t'.join(v))
    return fobject

class SList(list):
    def __init__(self, func, *args, **kwargs):
        from __main__ import __file__ as modname
        self.force_rebuild = kwargs.pop('force_rebuild', 0)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.root = ''.join(['c:/denis_korkh/temp/',
                             os.path.basename(modname).split('.')[0],
                              '_temp/',
                              func.__name__,
                              '/'])
        if not os.access(self.root, os.F_OK):
            os.makedirs(self.root)
        self.path = self.root + self.makename(self.func, self.args, self.kwargs)
        if os.access(self.path, os.F_OK) and not self.force_rebuild:
            super(SList,self).__init__(self.load())
        else:
            self.rebuild()
            self.save()
    def makename(self, fn, args, kwargs):
        return '_'.join([fn.__name__,str(hash(tuple(fn.__name__+str(args)+str(kwargs))))]) + '.json'
    def load(self):
        f = open(self.path, 'r')
        t = json.load(f)
        f.close()
        return t
    def save(self):
        f = open(self.path, 'w')
        json.dump(self, f)
        f.close()
    def rebuild(self):
        result = self.func(*self.args, **self.kwargs)
        if type(result) != list:
            raise TypeError('{} expected type {}, got {}'.format(self.__name__, list, type(result)))
        super(SList,self).__init__(result)

class SDict(dict):
    r"""A disc stored dictionary.
        Takes a dict returning function, arguments, and writes the result
        to disc.  Reads from disc if the program name, function, and arguments are
        the same on consequitive runs."""
    def __init__(self, func, *args, **kwargs):
        super(SDict,self).__init__()
        self.force_rebuild = kwargs.pop('force_rebuild', 0)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        from __main__ import __file__ as modname
        self.root = ''.join(['c:/denis_korkh/temp/',
                             os.path.basename(modname).split('.')[0],
                              '_temp/',
                              func.__name__,
                              '/'])
        if not os.access(self.root, os.F_OK):
            os.makedirs(self.root)
        self.path = self.root + self.makename(self.func, self.args, self.kwargs)
        if os.access(self.path, os.F_OK) and not self.force_rebuild:
            self.update(self.load())
        else:
            self.rebuild()
            self.save()
    def makename(self, fn, args, kwargs):
        return '_'.join([fn.__name__,str(hash(tuple(fn.__name__+str(args)+str(kwargs))))]) + '.json'
    def load(self):
        print ':'.join([self.func.__name__,'loading from disc.'])
        f = open(self.path, 'r')
        t = json.load(f)
        f.close()
        return t
    def save(self):
        f = open(self.path, 'w')
        json.dump(self, f)
        f.close()
    def rebuild(self):
        print ':'.join([self.func.__name__,'recalculating.'])
        result = self.func(*self.args, **self.kwargs)
        if type(result) != dict:
            raise TypeError('{} expected type {}, got {}'.format(self.__name__, dict, type(result)))
        self.update(self.func(*self.args, **self.kwargs))
#===============================================================================
# EXCEPTIONS
#===============================================================================

class FileToolsError(Exception):
    r"""Base class for exceptions in fileTools module."""
    pass

class LockedFileError(FileToolsError):
    r"""Error trying to access a locked file."""
    def __init__(self, path):
        self.path = path
        
    def __str__(self):
        return "Trying to write to a locked file: {}".format(self.path)
#===============================================================================
# 
#===============================================================================

if __name__ == '__main__':
    a = [1,2,3]
    b = []
    def r(a,b):
        b.append(a.pop(2))
    r(a,b)
    print a
    print b
    