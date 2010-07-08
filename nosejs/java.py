
"""A *very* minimal implementation of Java :)

This is for using Rhino compatible scripts in Spidermonkey that create java objects
"""
import os

class _SM_JavaFile(file):
    
    def getParent(self):
        return os.path.dirname(self.name)