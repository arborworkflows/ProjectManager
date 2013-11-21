# -*- coding: utf-8 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtDeclarative

import sys
sys.path.append("tangelo")

from ArborAlgorithmManagerAPI import ArborAlgorithmManager



# test to see if a variable can be expressed as a continous numeric value. This
# test is used when displaying the character names, so the user knows if they are 
# continuous or discrete characters

def isContinuous(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
            
            
# define the dialogs designed to exercise the API 
class NewProjectDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewProjectDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Enter the name of a new Arbor Project")
        self.projectNameDialog = QLineEdit()
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.projectNameDialog)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeProjectDialog)
        self.acceptButton.clicked.connect(self.createNewProject)
        
    def closeProjectDialog(self):
        self.hide()

    def createNewProject(self):
        projectTitleAsQstring = self.projectNameDialog.text()
        # need to convert from PyQt4.QtCore.QString to Python string
        projectTitle = str(projectTitleAsQstring)
        # if a valid name was entered, create the project record 
        
        if len(projectTitle)>0:
            print "creating project entitled:",projectTitle
            self.hide()
            # create project record in the database
            self.api.newProject(projectTitle)
            
    
    
def initializeAllDialogs(arborAPI,algorithms):
    global savedArborAPI
    savedArborAPI = arborAPI
    global newProjectDialogInstance 
    newProjectDialogInstance = NewProjectDialog(arborAPI)
    global newTreeDialogInstance
    newTreeDialogInstance = NewTreeDialog(arborAPI)
    global newCharacterDialogInstance
    newCharacterDialogInstance = NewCharacterDialog(arborAPI)
    global newOccurrenceDialogInstance
    newOccurrenceDialogInstance = NewOccurrenceDialog(arborAPI)
    global newSequenceDialogInstance
    newSequenceDialogInstance = NewSequenceDialog(arborAPI)
    global newWorkflowDialogInstance
    newWorkflowDialogInstance = NewWorkflowDialog(arborAPI)
    global newOpenTreeOfLifeDialogInstance
    newOpenTreeOfLifeDialogInstance = NewOpenTreeOfLifeDialog(arborAPI)
    global newAlgorithmControlsDialogInstance
    newAlgorithmControlsDialogInstance = NewAlgorithmControlsDialog(arborAPI,algorithms)
    if (arborAPI.getCurrentProject()):
        newAlgorithmControlsDialogInstance.setCurrentProject(arborAPI.getCurrentProject())
    

    
def openNewProjectDialog():
    global app
    print "open new project"
    global newProjectDialogInstance
    newProjectDialogInstance.show()
    #text, ok = QInputDialog.getText('Create New Project',   'Enter the new project name:')
    #if ok:
    #    print "accept was clicked"



# pop up to load a new tree into the selected project
class NewTreeDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewTreeDialog, self).__init__(parent)
        self.api = ArborAPI
        self.treeType = "newick"
        self.titleText = QLabel("Add a new Tree to the current project")
        self.titleText2 = QLabel("Enter the name to give the dataset here:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.selectFileName = QPushButton("Select PhyloXML file to import")
        self.fileSelector = QFileDialog()
        self.fileSelector.setNameFilter("PhyloXML files (*.xml)")
        self.selectFileNameNewick = QPushButton("Select Newick file to import")
        self.fileSelectorNewick = QFileDialog()
        self.fileSelectorNewick.setNameFilter("Newick files (*.*)")

        #self.fileSelector.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.selectFileNameNewick)
        self.layout.addWidget(self.selectFileName)
        self.layout.addWidget(self.confirmationText)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeTreeDialog)
        self.selectFileName.clicked.connect(self.openFileDialog)
        self.selectFileNameNewick.clicked.connect(self.openFileDialogNewick)
        self.acceptButton.clicked.connect(self.createNewTree)
        self.fileSelector.fileSelected.connect(self.displayNewTreeStatus)
        self.fileSelectorNewick.fileSelected.connect(self.displayNewTreeStatus) 
        
    def closeTreeDialog(self):
        self.hide()
        
    def openFileDialog(self):
        self.fileSelector.show()
        self.treeType = "phyloxml"
        
    def openFileDialogNewick(self):
        self.fileSelectorNewick.show()        
        self.treeType = "newick"
        
    def displayNewTreeStatus(self,treefile):
        self.savedTreeFilename = str(treefile)
        confirmString = str("OK to import file '"+treefile+ "' as '"+str(self.nameDialog.text())+"' ?")
        self.confirmationText.setText(confirmString)
        
    # the user selected a treefile and confirmed the selection was OK, so perform
    # the import operation
    def createNewTree(self):
        nameForTree = str(self.nameDialog.text())
        print "create new tree from file: ",self.savedTreeFilename
        print "name for the tree is: ",nameForTree
        print "default project for tree is: ", self.api.getCurrentProject()
        # need to convert from PyQt4.QtCore.QString to Python string
        #projectTitle = str(projectTitleAsQstring)
        # if valid names are entered, then create the tree record 
        if len(self.savedTreeFilename)>0 and len(self.api.getCurrentProject())>0:
            print "adding a tree entitled: ",self.savedTreeFilename
            self.hide()
#            # create project record in the database
            self.api.newTreeInProject(nameForTree, self.savedTreeFilename, self.api.getCurrentProject(),self.treeType)
#            
def openNewTreeDialog():
    global app
    print "open new tree dialog"
    global newTreeDialogInstance
    newTreeDialogInstance.show()
 
 #------------------------ definition for character matrix -----------------
 
class NewCharacterDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewCharacterDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Add a new Character Matrix to the current project")
        self.titleText2 = QLabel("Enter the name to give the dataset here:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.selectFileName = QPushButton("Select CSV file to import")
        self.fileSelector = QFileDialog()
        self.fileSelector.setNameFilter("CSV files (*.csv)")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.selectFileName)
        self.layout.addWidget(self.confirmationText)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeCharacterDialog)
        self.selectFileName.clicked.connect(self.openFileDialog)
        self.acceptButton.clicked.connect(self.createNewCharacterMatrix)
        self.fileSelector.fileSelected.connect(self.displayNewCharacterStatus)
        
    def closeCharacterDialog(self):
        self.hide()
    def openFileDialog(self):
        self.fileSelector.show()
    def displayNewCharacterStatus(self,inputfile):
        self.savedFilename = str(inputfile)
        confirmString = str("OK to import file '"+inputfile+ "' as '"+str(self.nameDialog.text())+"' ?")
        self.confirmationText.setText(confirmString)
        
    # the user selected a CSV file and confirmed the selection was OK, so perform
    # the import operation
    def createNewCharacterMatrix(self):
        nameForInstance = str(self.nameDialog.text())
        print "create new character matrix from file: ",self.savedFilename
        print "name for the tree is: ",nameForInstance
        print "default project for matrix is: ", self.api.getCurrentProject()
        # if valid names are entered, then create the character record 
        if len(self.savedFilename)>0 and len(self.api.getCurrentProject())>0:
            print "adding a tree entitled: ",self.savedFilename
            self.hide()
#            # create project record in the database
            self.api.newCharacterMatrixInProject(nameForInstance, self.savedFilename, self.api.getCurrentProject())
#            
def openNewCharacterDialog():
    global app
    print "open new character matrix dialog"
    global newCharacterDialogInstance
    newCharacterDialogInstance.show()
 
 #------------------------ definition for occurrences -----------------
 
class NewOccurrenceDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewOccurrenceDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Add a new set of species occurrences to the current project")
        self.titleText2 = QLabel("Enter the name to give the dataset here:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.selectFileName = QPushButton("Select CSV file to import")
        self.fileSelector = QFileDialog()
        self.fileSelector.setNameFilter("CSV files (*.csv)")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.selectFileName)
        self.layout.addWidget(self.confirmationText)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeOccurrencesDialog)
        self.selectFileName.clicked.connect(self.openFileDialog)
        self.acceptButton.clicked.connect(self.createNewOccurrences)
        self.fileSelector.fileSelected.connect(self.displayNewOccurrencesStatus)
        
    def closeOccurrencesDialog(self):
        self.hide()
        
    def openFileDialog(self):
        self.fileSelector.show()
        
    def displayNewOccurrencesStatus(self,inputfile):
        self.savedFilename = str(inputfile)
        confirmString = str("OK to import file '"+inputfile+ "' as '"+str(self.nameDialog.text())+"' ?")
        self.confirmationText.setText(confirmString)
        
    # the user selected a CSV file and confirmed the selection was OK, so perform
    # the import operation
    def createNewOccurrences(self):
        nameForInstance = str(self.nameDialog.text())
        print "create new occurrence records from file: ",self.savedFilename
        print "name for the occurrence set is: ",nameForInstance
        print "default project for occurrence is: ", self.api.getCurrentProject()
        # if valid names are entered, then create the character record 
        if len(self.savedFilename)>0 and len(self.api.getCurrentProject())>0:
            print "adding occurrences entitled: ",self.savedFilename
            self.hide()
#            # create project record in the database
            self.api.newOccurrencesInProject(nameForInstance, self.savedFilename, self.api.getCurrentProject())
#            
def openNewOccurrencesDialog():
    global app
    print "open new occurrence dialog"
    global newOccurrenceDialogInstance
    newOccurrenceDialogInstance.show()
 
 
 
 
 #------------------------ definition for sequences  -----------------
 
class NewSequenceDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewSequenceDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Add ew sequences to the current project")
        self.titleText2 = QLabel("Enter the name to give the sequence set:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.selectFileName = QPushButton("Select sequences file to import")
        self.fileSelector = QFileDialog()
        self.fileSelector.setNameFilter("FASTA files (*.fasta)")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.selectFileName)
        self.layout.addWidget(self.confirmationText)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeSequenceDialog)
        self.selectFileName.clicked.connect(self.openFileDialog)
        self.acceptButton.clicked.connect(self.createNewSequence)
        self.fileSelector.fileSelected.connect(self.displayNewSequenceStatus)
        
    def closeSequenceDialog(self):
        self.hide()
        
    def openFileDialog(self):
        self.fileSelector.show()
        
    def displayNewSequenceStatus(self,inputfile):
        self.savedFilename = str(inputfile)
        confirmString = str("OK to import file '"+inputfile+ "' as '"+str(self.nameDialog.text())+"' ?")
        self.confirmationText.setText(confirmString)
        
    # the user selected a CSV file and confirmed the selection was OK, so perform
    # the import operation
    def createNewSequence(self):
        nameForInstance = str(self.nameDialog.text())
        print "create new sequence records from file: ",self.savedFilename
        print "name for the sequence set is: ",nameForInstance
        print "default project for sequence is: ", self.api.getCurrentProject()
        # if valid names are entered, then create the character record 
        if len(self.savedFilename)>0 and len(self.api.getCurrentProject())>0:
            print "adding sequence entitled: ",self.savedFilename
            self.hide()
#            # create project record in the database
            self.api.newSequencesInProject(nameForInstance, self.savedFilename, self.api.getCurrentProject())
#            
def openNewSequenceDialog():
    global app
    print "open new sequence dialog"
    global newSequenceDialogInstance
    newSequenceDialogInstance.show()
 
 
 
 #------------------------ definition for workflows  -----------------
 
class NewWorkflowDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewWorkflowDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Add a new workflow to the current project")
        self.titleText2 = QLabel("Enter the name to give the workflow:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.selectFileName = QPushButton("Select workflow file to import")
        self.fileSelector = QFileDialog()
        self.fileSelector.setNameFilter("wflow files (*.wflow)")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.selectFileName)
        self.layout.addWidget(self.confirmationText)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeWorkflowDialog)
        self.selectFileName.clicked.connect(self.openFileDialog)
        self.acceptButton.clicked.connect(self.createNewWorkflow)
        self.fileSelector.fileSelected.connect(self.displayNewWorkflowStatus)
        
    def closeWorkflowDialog(self):
        self.hide()
        
    def openFileDialog(self):
        self.fileSelector.show()
        
    def displayNewWorkflowStatus(self,inputfile):
        self.savedFilename = str(inputfile)
        confirmString = str("OK to import file '"+inputfile+ "' as '"+str(self.nameDialog.text())+"' ?")
        self.confirmationText.setText(confirmString)
        
    # the user selected a CSV file and confirmed the selection was OK, so perform
    # the import operation
    def createNewWorkflow(self):
        nameForInstance = str(self.nameDialog.text())
        print "create new sequence records from file: ",self.savedFilename
        print "name for the sequence set is: ",nameForInstance
        print "default project for sequence is: ", self.api.getCurrentProject()
        # if valid names are entered, then create the character record 
        if len(self.savedFilename)>0 and len(self.api.getCurrentProject())>0:
            print "adding sequence entitled: ",self.savedFilename
            self.hide()
#            # create project record in the database
            self.api.newWorkflowInProject(nameForInstance, self.savedFilename, self.api.getCurrentProject())
#            
def openNewWorkflowDialog():
    global app
    print "open new workflow dialog"
    global newWorkflowDialogInstance
    newWorkflowDialogInstance.show()
 
 #----------------
 
 
# pop up to load a tree from the Open Tree of Life Project
class NewOpenTreeOfLifeDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,parent=None):
        super(NewOpenTreeOfLifeDialog, self).__init__(parent)
        self.api = ArborAPI
        self.titleText = QLabel("Import a tree from the Open Tree of Life")
        self.titleText2 = QLabel("Enter the name to give the dataset here:")
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.titleText3 = QLabel("Enter the OTTol ID to query:")
        self.ottolidDialog = QLineEdit()
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton = QPushButton("Accept")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.titleText)
        self.layout.addWidget(self.titleText2)
        self.layout.addWidget(self.nameDialog)
        self.layout.addWidget(self.titleText3)
        self.layout.addWidget(self.ottolidDialog)
        self.layout.addWidget(self.acceptButton)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.cancelButton.clicked.connect(self.closeTreeDialog)
        self.acceptButton.clicked.connect(self.createNewTreeFromOpenTreeOfLife)
        
    def closeTreeDialog(self):
        self.hide()
        
    # the user has entered an OTToLID from the OTL, so lets retrieve it
    def createNewTreeFromOpenTreeOfLife(self):
        nameForTree = str(self.nameDialog.text())
        print "query OpenTreeOfLife from ottolID: ",self.ottolidDialog.text()
        print "name for the tree is: ",nameForTree
        print "default project for tree is: ", self.api.getCurrentProject()
        # need to convert from PyQt4.QtCore.QString to Python string
        #projectTitle = str(projectTitleAsQstring)
        # if valid names are entered, then create the tree record 
        if len(self.api.getCurrentProject())>0:
            self.hide()
#           # create project record in the database
            self.api.newTreeFromOpenTreeOfLife(nameForTree, self.ottolidDialog.text(), self.api.getCurrentProject())
#            
def openNewTreeOfLifeDialog():
    global app
    print "open new tree dialog"
    global newOpenTreeOfLifeDialogInstance
    newOpenTreeOfLifeDialogInstance.show()
    
    
     #----------------
 
 
# pop up to load a tree from the Open Tree of Life Project
class NewAlgorithmControlsDialog(QDialog):   
    # Define the  user interface for a new dialog to be created
    def __init__(self, ArborAPI,ArborAlgorithmsAPI,parent=None):
        super(NewAlgorithmControlsDialog, self).__init__(parent)
        self.api = ArborAPI
        self.algorithms = ArborAlgorithmsAPI
        self.currentProjectName = ''
        self.titleText = QLabel("Run Analyses")
        
        self.vert_splitter = QSplitter(Qt.Vertical, self)
        self.button_splitter = QSplitter(Qt.Vertical,self)
        self.vert_splitter2 = QSplitter(Qt.Vertical,self)
        
        # list the tree instances of data in the project
        self.treeLabel = QLabel("Select a Tree:")      
        self.treeLabel.setMaximumHeight(40)
        self.treeListWidget = QListWidget(self)
        self.treeListWidget.setObjectName("treeListWidget")
        
        # list the character matrix instances of data in the project
        self.matrixLabel = QLabel("Select a Character Matrix:")
        self.matrixLabel.setMaximumHeight(40)
        self.matrixListWidget = QListWidget(self)
        self.matrixListWidget.setObjectName("matrixListWidget")
        
        # list the attribute columns in the current character matrix
        self.charcterLabel = QLabel("Select a Character:")
        self.charcterLabel.setMaximumHeight(40)        
        self.characterListWidget = QListWidget(self)
        self.characterListWidget.setObjectName("characterListWidget")

      # list the algorithms available
        self.algorithmLabel = QLabel("Algorithm To Run:")
        self.algorithmLabel.setMaximumHeight(40)
        self.algorithmListWidget = QListWidget(self)
        self.algorithmListWidget.setObjectName("algorithmListWidget")
    
        self.confirmationText = QLabel("")
        self.nameDialog = QLineEdit()
        self.titleText3 = QLabel("Enter the output name to use:")
        self.titleText3.setMaximumHeight(40)
        self.outputObjectName = QLineEdit()
        self.outputObjectName.setMaximumHeight(50)
        self.cancelButton = QPushButton("Close Window")
        self.runButton = QPushButton("Run Tree/Matrix \n  Algorithm")
        
        #put up a logo
        pm = QPixmap("Arbor_128px.png")
        self.arborLogo = QLabel()
        self.arborLogo.setPixmap(pm);
        self.arborLogo.setAlignment(Qt.AlignCenter)
        
        # lay out the elements in the dialog panel 
        self.vert_splitter.addWidget(self.treeLabel)
        self.vert_splitter.addWidget(self.treeListWidget)
        self.vert_splitter.addWidget(self.matrixLabel)
        self.vert_splitter.addWidget(self.matrixListWidget)
        self.vert_splitter2.addWidget(self.charcterLabel)
        self.vert_splitter2.addWidget(self.characterListWidget)
        self.vert_splitter2.addWidget(self.algorithmLabel)
        self.vert_splitter2.addWidget(self.algorithmListWidget)       
        self.button_splitter.addWidget(self.arborLogo)
        self.button_splitter.addWidget(self.titleText3)
        self.button_splitter.addWidget(self.outputObjectName)
        self.button_splitter.addWidget(self.runButton)
        self.button_splitter.addWidget(self.cancelButton)   
         
        self.layout = QHBoxLayout()
        #self.layout.addWidget(self.arborLogo)
        self.layout.addWidget(self.vert_splitter)
        self.layout.addWidget(self.vert_splitter2)
        self.layout.addWidget(self.button_splitter)
        self.setLayout(self.layout)
        
        # connect statements to connect behaviors to events
        self.cancelButton.clicked.connect(self.closeAlgrorithmControlsDialog)
        self.runButton.clicked.connect(self.doStuff)
        self.matrixListWidget.currentItemChanged.connect(self.fillCharacterListWidget)
        
    def closeAlgrorithmControlsDialog(self):
        self.hide()
        
    def clearAll(self):
        self.treeListWidget.clear()
        self.matrixListWidget.clear()
        self.characterListWidget.clear()        
        
    def loadAlgorithms(self):
         # get a record from the Arbor datastore and iterate through its headers
        self.algorithmListWidget.clear()
        charList = self.algorithms.returnListOfLoadedAlgorithms()
        for j in range(0,len(charList)):
            self.algorithmListWidget.addItem(charList[j])
        
    def setCurrentProject(self,prname):
        self.characterListWidget.clear()
        # fill tree and character matrix lists
        treeInstances = self.api.getListOfDatasetsByProjectAndType(prname,'PhyloTree')
        self.currentProjectName = prname;
        #print "api returned trees: ",treeInstances
        self.treeListWidget.clear()
        for j in range(0,len(treeInstances)):
            self.treeListWidget.addItem(treeInstances[j])
        matrixInstances = self.api.getListOfDatasetsByProjectAndType(prname,'CharacterMatrix')
        #print "api returned matrices: ",matrixInstances
        self.matrixListWidget.clear()
        for j in range(0,len(matrixInstances)):
            self.matrixListWidget.addItem(matrixInstances[j])

    # this method finds whih matrix has been selected and list all the columns
    # to be processed in the cha    
    def fillCharacterListWidget(self):
        if (self.matrixListWidget.currentItem()):
         matrixname = str(self.matrixListWidget.currentItem().text())
         self.characterListWidget.clear()
         # get a record from the Arbor datastore and iterate through its headers
         charList = self.api.returnCharacterListFromCharacterMatrix(
                             self.matrixListWidget.currentItem().text(),
                             self.currentProjectName)
         # now fill the display widget with the characters, indicating their continuous or discrete nature
         # by listing them one per line with the proper type indicated
         for j in range(0,len(charList)):
            #if isContinuous(charList[j]):
            #    charentry = "Continuous: "+charList[j]
            #else:
            #    charentry = "Discrete:   "+charList[j]
            charentry = charList[j]
            self.characterListWidget.addItem(charentry)

    # the user has invoked run on a selected algorithm, collected the selected datasets and invoke
    # the algorithm

    def doStuff(self):
        currenttree = currentmatrix = currentcharacter =  outputname = ''
        if (self.algorithmListWidget.currentItem()):
            algorithmToRun = self.algorithmListWidget.currentItem().text()
            if (self.treeListWidget.currentItem()):
                currenttree=self.treeListWidget.currentItem().text()
            if (self.matrixListWidget.currentItem()):
                currentmatrix = self.matrixListWidget.currentItem().text()
            if (self.characterListWidget.currentItem()):                
                currentcharacter = self.characterListWidget.currentItem().text()
            if (self.outputObjectName.text()):
                outputname = self.outputObjectName.text()
            # TODO: add checking logic here to make sure appropriate data types are defined for algorithms
            # before running them.  All algorithms could have a list of data they depend on and it would get checked 
            self.algorithms.runAlgorithmByName(algorithmToRun,self.currentProjectName,currenttree,currentmatrix,currentcharacter,outputname)
        pass
#            
def openAlgorithmControlsDialog():
    global app
    print "open algorithm controls "
    global newAlgorithmControlsDialogInstance
    #newAlgorithmControlsDialogInstance.clearAll()
    newAlgorithmControlsDialogInstance.loadAlgorithms()
    newAlgorithmControlsDialogInstance.show()
    
# this is defined at the dialogs package level, it invokes changed toany 
# dialogs that needs to know the project has changed    
def changeCurrentProject(prname):
    newAlgorithmControlsDialogInstance.setCurrentProject(prname)
