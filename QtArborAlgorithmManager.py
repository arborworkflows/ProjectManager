# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Created on October 21 2013

@author: clisle


Requirements:
    - mongoDB instance used to store metadata
    - pymongo, csv packages for python
"""

import sys
sys.path.append("tangelo")
from ArborAlgorithmManagerAPI import ArborAlgorithmManager
from PyQt4.QtCore import pyqtSignal, QObject

class QtArborAlgorithmManager(ArborAlgorithmManager, QObject):
    # had to move signal to class variable because instance variable didn't work, see:
    # http://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect

    # emitted when an algorithm is added or deleted
    algorithmListChangedSignal = pyqtSignal();

    def __init__(self, parent=None):
        self.super = super(QtArborAlgorithmManager, self)
        QObject.__init__(self, parent)
        self.super.__init__()

    # create the infrastructure for a new algorithm. This is a placeholder for when 
    # a plug-in system exists for adding new algorithms
    def newAlgorithm(self,algoName):
        self.super.newAlgorithm(algoName)
        self.algorithmListChangedSignal.emit();
