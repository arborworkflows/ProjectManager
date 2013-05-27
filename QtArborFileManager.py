# -*- coding: utf-8 -*-
"""
Created on Sat Mar 30 20:36:09 2013

@author: clisle

This API manages the creation, naming, and upload of datasets into the Arbor
database system.  This is built as a client application to Kitware's Tangelo web
framework.  This API allows the user to create new projects, create datatypes
for files to be associated with the projects, and upload files to the projects.
Initially, this is developed as: an API layer called by an application program,
but the thinking is that this might grow up to become a Tangelo service,
someday.

Requirements:
    - mongoDB instance used to store metadata
    - pymongo, csv packages for python
"""

import sys
sys.path.append("tangelo")
from ArborFileManagerAPI import ArborFileManager
from PyQt4.QtCore import pyqtSignal, QObject

class QtArborFileManager(ArborFileManager, QObject):
    # had to move signal to class variable because instance variable didn't work, see:
    # http://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect

    # emitted when a project is added or deleted
    projectListChangedSignal = pyqtSignal();
    datasetListChangedSignal = pyqtSignal();
    datatypeListChangedSignal = pyqtSignal();

    def __init__(self, parent=None):
        self.super = super(QtArborFileManager, self)
        QObject.__init__(self, parent)
        self.super.__init__()

    # create the record in Mongo for a new project
    def newProject(self,projectName):
        self.super.newProject(projectName)
        self.projectListChangedSignal.emit();

    # add a tree to the project
    def newTreeInProject(self,treename,treefile,projectTitle, treetype):
        self.super.newTreeInProject(treename, treefile, projectTitle, treetype)

        # emit a signal so the GUI knows to update
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit();

    def newTreeInProjectFromString(self,treename,treestring,projectTitle, description,treetype):
        self.super.newTreeInProjectFromString(treename, treestring, projectTitle, description, treetype)
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit()

    # add a character matrix to the project
    def newCharacterMatrixInProject(self,instancename,filename,projectTitle):
        self.super.newCharacterMatrixInProject(instancename, filename, projectTitle)
        self.datasetListChangedSignal.emit();
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit()

    # add a character matrix to the project
    def newOccurrencesInProject(self,instancename,filename,projectTitle):
        self.super.newOccurrencesInProject(instancename, filename, projectTitle)
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit()

    # add sequences to the project
    def newSequencesInProject(self,instancename,filename,projectTitle):
        self.super.newSequencesInProject(instancename, filename, projectTitle)
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit()

   # add sequences to the project
    def newWorkflowInProject(self,instancename,filename,projectTitle):
        self.super.newWorkflowInProject(instancename, filename, projectTitle)
        self.datatypeListChangedSignal.emit()
        self.datasetListChangedSignal.emit()
