'''
Created on Jan 18, 2013

stuff to help print 

Classes:
PBar  -- Print progress ticks to screen for loops that have a known total.

Methods:
printlist() -- Print each element of the list on a new line.
printdict() -- Formats a table-like print to the console given a dict of dict key:value pairs.

@author: dkorkh
'''
import sys
import time
from math import floor

class PBar(object):
    r"""Print progress ticks to screen for loops that have a known total.
    
    Initialize before entering a loop with a max count and then call update
    every iteration from within the loop to get a console print out of progress.
    
    Arguments:
    label      -- The label for the progress bar.
    maxcount   -- The total iterations expected.
    
    Keyword arguments:
    tick       -- The symbol to use as a tick.
    scrnwidht  -- The length of the progress bar.
    
    Methods:
    update()   -- Call from inside the loop on every iteration.
    reset()    -- Call to re-initialize the progress bar.
    """
    def __init__(self, label, maxcount, tick = '.', scrnwidth = 100):
        self.label = label
        self.maxcount = maxcount
        self.tick = tick
        self.scrnwidth = scrnwidth
        self.counter = 0.0
        self.progress_counter = 0
        self.done = 0
        
        self.start = 1
        self.timestart = 0.0
    
    def update(self):
        if self.start:
            print '[{}{}]'.format(self.label,' '*(self.scrnwidth-len(self.label)-2))
            self.start = 0
            self.time = time.clock()
        self.counter += 1
        progress = self.counter/self.maxcount
        ticks = int(floor(progress*self.scrnwidth - self.progress_counter))
        if ticks:
            self.progress_counter += ticks
            sys.stdout.write(self.tick*ticks)
        if self.progress_counter >= self.scrnwidth and not self.done:
            self.done = 1
            print ' {:.4f}sec'.format(time.clock()-self.timestart)
        
    
    def reset(self, label, maxcount):
        self.label = label
        self.maxcount = maxcount
        self.done = 0
        self.progress_counter = 0
        self.counter = 0.0
        self.start = 1

class PBar2(object):
    r"""Print progress ticks to screen for loops that have a known total.
    
    Initialize before entering a loop with a max count and then call update
    every iteration from within the loop to get a console print out of progress.
    
    Arguments:
    label      -- The label for the progress bar.
    maxcount   -- The total iterations expected.
    
    Keyword arguments:
    tick       -- The symbol to use as a tick.
    scrnwidht  -- The length of the progress bar.
    
    Methods:
    update()   -- Call from inside the loop on every iteration.
    reset()    -- Call to re-initialize the progress bar.
    """
    def __init__(self, label, maxcount, tick = '.', scrnwidth = 100):
        self.label = label
        self.maxcount = maxcount
        self.tick = tick
        self.scrnwidth = scrnwidth
        self.counter = 0.0
        self.progress_counter = 0
        self.done = 0
        
        self.start = 1
        self.timestart = 0.0
    
    def update(self):
        if self.start:
            print '[{}{}]'.format(self.label,' '*(self.scrnwidth-len(self.label)-2))
            self.start = 0
            self.timestart = time.clock()
        self.counter += 1
        progress = self.counter/self.maxcount
        ticks = int(floor(progress*self.scrnwidth - self.progress_counter))
        if ticks:
            self.progress_counter += ticks
            sys.stdout.write(self.tick*ticks)
        if self.progress_counter >= self.scrnwidth and not self.done:
            self.done = 1
            print ' {:.4f}sec'.format(time.clock()-self.timestart)
        
    
    def reset(self, maxcount):
        self.maxcount = maxcount
        self.done = 0
        self.progress_counter = 0
        self.counter = 0.0
        self.start = 1
        self.timestart = 0.0
        
    def setlabel(self, label):
        r"""Sets the label for the progress object."""
        self.label = label

#===============================================================================
# METHODS
#===============================================================================

def printlist(somelist, label = None):
    r"""Print each element of the list on a new line."""
    t = '\t' if label else ''
    if label:
        print label
    print (t + '\n{t}'.format(t = t).join([str(x) for x in somelist]))

def printdict(d, keylist = None, sort_keys = True, fn_filter = (lambda v: True)):
    r"""Formats a table-like print to the console given a dict of dict key:value pairs.
    Arguments:
    d            -- The dictionary to format.
    keyorder     -- Optionally, the keylist could specify the order of keys.
    sort_keys    -- Sort the entries in the dictionary. (default: True)
    fn_filter    -- An optional function that takes an entry and prints only if it returns True.
                    (default: always returns true)"""
    dict_fields = keylist if keylist else d.keys()
    field_lengths = [0 for x in dict_fields]
    for v in d.values():
        for ii, kk in enumerate(dict_fields):
            if len(str(v[kk])) > field_lengths[ii]:
                field_lengths[ii] = len(str(v[kk]))
    
    print '|'.join(['{0:{1}}'.format(a, b) for a, b in zip(dict_fields, field_lengths)])
    
    d_keys = d.keys()
    d_keys.sort()
    for k in d_keys:
        v = d[k]
        if fn_filter(v):
            row_s = '|'.join(['{0:{1}}'.format(v[a], b) for a, b in zip(dict_fields, field_lengths)])
            print '-'*len(row_s)
            print row_s
