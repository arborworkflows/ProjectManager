# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 22:15:51 2013

@author: clisle
"""

import os
import sys


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtDeclarative


global api

import dialogs

# add calls to manage files for Arbor
import ArborFileManagerAPI

# global data structures to remember the projects, types, and instances
projectList = []
datatypelist = []
datasetList = []

 
class Form(QDialog):
   
    # Define the main user interface
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
         
        self.quitbutton = QPushButton("Quit")
        self.title = QLabel("Arbor Project and File Manager")
        #wf_manager = workflowManager.workflowManager()
        
        self.horiz_splitter = QSplitter()
        
        #put up a logo
        pm = QPixmap("Arbor_128px.png")
        self.arborLogo = QLabel()
        self.arborLogo.setPixmap(pm);
        
        # list window to show the projects currently stored
        self.projectListWidget = QListWidget(self)
        self.projectListWidget.setObjectName("projectListWidget")
 
        # list window to show the type of data allowed in this project 
        self.datatypeListWidget = QListWidget(self)
        self.datatypeListWidget.setObjectName("datatypeListWidget")

        # list the instances of data in the database
        self.datasetListWidget = QListWidget(self)
        self.datasetListWidget.setObjectName("datasetListWidget")
        
        # put the widgets together in the window but allow them to adjust 
        self.horiz_splitter.addWidget(self.arborLogo)
        self.horiz_splitter.addWidget(self.projectListWidget)
        self.horiz_splitter.addWidget(self.datatypeListWidget)
        self.horiz_splitter.addWidget(self.datasetListWidget)
   
        # add buttons
        button_panel = QSplitter();
        self.newProjectButton = QPushButton("New Project")
        self.deleteProjectButton = QPushButton("Delete Selected\nProject")
        self.deleteDatasetButton = QPushButton("Delete Selected\nDataset")

   # add button tow 2
        button_panel2 = QSplitter();
        self.newTreeButton = QPushButton("Load Tree")
        self.newTreeFromOpenTreeButton = QPushButton("Load from OTL")
        self.newCharacterButton = QPushButton("Load Character\nMatrix")
        self.newObservationsButton = QPushButton("Load Occurrences")
        self.newSequencesButton = QPushButton("Load Sequences")
        self.newWorkflowButton = QPushButton("Load Workflow")

        
        button_panel.addWidget(self.newProjectButton)  
        button_panel.addWidget(self.deleteProjectButton)
        button_panel.addWidget(self.deleteDatasetButton)          
        button_panel2.addWidget(self.newTreeButton)     
        button_panel2.addWidget(self.newTreeFromOpenTreeButton)
        button_panel2.addWidget(self.newCharacterButton)
        button_panel2.addWidget(self.newObservationsButton)
        button_panel2.addWidget(self.newSequencesButton)
        button_panel2.addWidget(self.newWorkflowButton)
        
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.horiz_splitter)
        layout.addWidget(button_panel)
        layout.addWidget(button_panel2)
        layout.addWidget(self.quitbutton)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        #self.button.clicked.connect(self.greetings)
        self.quitbutton.clicked.connect(self.quitprogram)
        self.newProjectButton.clicked.connect(self.processNewProjectButton)
        self.deleteProjectButton.clicked.connect(self.deleteSelectedProject)
        self.deleteDatasetButton.clicked.connect(self.deleteSelectedDataset)
        self.newTreeButton.clicked.connect(self.processNewTreeButton)
        self.newTreeFromOpenTreeButton.clicked.connect(self.processNewTreeFromOpenTreeButton)
        self.newCharacterButton.clicked.connect(self.processNewCharacterButton)
        self.newObservationsButton.clicked.connect(self.processNewObservationsButton)
        self.newSequencesButton.clicked.connect(self.processNewSequencesButton)

        # set callback so user clicking on a project displays project info
        #self.projectListWidget.itemActivated.connect(self.clearTypesandDatasetLists)
        self.projectListWidget.itemClicked.connect(self.selectProjectItem)
        # show instances that match the selected datatype
        self.datatypeListWidget.itemClicked.connect(self.selectDataTypeItem)
        
       
    # Initialize the Geiger module under R 
    def greetings(self):
        print ("Running Geiger Init...") 
        #geigerWrap.gw_InitGeiger()
        print ("Finished Geiger Init...") 
               
    # Closeout any leftover processes and interfaces, then quit
    def quitprogram(self):
        print ("Safe Closeout...") 
        #geigerWrap.gw_ShutdownGeiger()
        app.quit()
        
    def processNewProjectButton(self):
        dialogs.openNewProjectDialog()
        self.updateProjectList()
        
    def clearTypesandDatasetLists(self):
        self.datasetListWidget.clear()
        self.datatypeListWidget.clear()
        
    # user selected a particular project, so display the types for this project    
    def selectProjectItem(self):
        # test that there is actually something selected
        if (self.projectListWidget.currentItem()):
            # now display the types in this project
            prname = str(self.projectListWidget.currentItem().text())
            # TODO: do we need a test for a valid project here?  (see selectDataTypeItem)
            api.setCurrentProject(prname)
            typeListForProject = api.getListOfTypesForProject(prname)
            print "api returned types: ",typeListForProject
            self.datatypeListWidget.clear()
            self.datasetListWidget.clear()
            for j in range(0,len(typeListForProject)):
                self.datatypeListWidget.addItem(typeListForProject[j])
            
    # user clicked a datatype inside a project.  we want to display all the 
    # instances of this datatype.  If there is nothing selected, then don't fill the instance list
    def selectDataTypeItem(self):
        # test that there is actually something selected
        if (self.datatypeListWidget.currentItem()):
            typename = str(self.datatypeListWidget.currentItem().text())
            # do nothing if no type is currently selected.  The dataset list 
            # only needs to be updated if the user is currently observing some
            # datasets
            if len(typename)>0:
                prname = api.getCurrentProject()
                instancesForThisType = api.getListOfDatasetsByProjectAndType(prname,typename)
                print "api returned types: ",instancesForThisType
                self.datasetListWidget.clear()
                for j in range(0,len(instancesForThisType)):
                    self.datasetListWidget.addItem(instancesForThisType[j])
  
    # refresh the entire project list dialog with all the projects in the database
    def updateProjectList(self):
        global api
        print "updateProjectList"
        projectListFromMongo = api.getListOfProjectNames()
        self.projectListWidget.clear()
        self.datatypeListWidget.clear()
        self.datasetListWidget.clear()
        for i in range(0,len(projectListFromMongo)):
            self.projectListWidget.addItem(projectListFromMongo[i])
 
            
    # lookup the name from the list of projects and delete it.  Use the 
    # index into the list widget to select the project to delete
    def deleteSelectedProject(self):
        global api
        print "deleteProject"
        currentName = str(self.projectListWidget.currentItem().text())
        print "selected ",currentName," to delete"
        projectListFromMongo = api.getListOfProjectNames()
        if currentName in projectListFromMongo:
            print "found name in project list"
            api.deleteProjectNamed(currentName)
        # this might be redundant because of the projectlistChanged signal    
        self.updateProjectList()
        
    # delete a single dataset from a project
    def deleteSelectedDataset(self):
        global api
        print "deleteDataset"
        currentProjectName = str(self.projectListWidget.currentItem().text())
        currentDatatypeName = str(self.datatypeListWidget.currentItem().text())
        currentDatasetName = str(self.datasetListWidget.currentItem().text())
        api.deleteDataset(currentProjectName,currentDatatypeName,currentDatasetName)   
        self.updateProjectList()

    def processNewTreeButton(self):
        dialogs.openNewTreeDialog()

    def processNewTreeFromOpenTreeButton(self):
        dialogs.openNewTreeOfLifeDialog()
 
    def processNewCharacterButton(self):
        dialogs.openNewCharacterDialog()

    def processNewObservationsButton(self):
        dialogs.openNewOccurrencesDialog()

    def processNewSequencesButton(self):
        dialogs.openNewSequenceDialog()


if __name__ == '__main__':
    # Create the Qt Application
    global app
    app = QApplication(sys.argv)
    
    # connect to database and initiaize the API
    global api
    api = ArborFileManagerAPI.ArborFileManager()
    api.initDatabaseConnection()
    
    # Create and show the form
    form = Form()
    # the window opens up really tiny without this, because QML size wasn't set
    #form.setMinimumSize(800,600)
    dialogs.initializeAllDialogs(api)
    api.projectListChangedSignal.connect(form.updateProjectList)
    api.datasetListChangedSignal.connect(form.selectDataTypeItem)

    form.updateProjectList()
    form.show()
 
    
    # Run the main Qt loop
    app.exec_()



