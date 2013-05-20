# -*- coding: utf-8 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtDeclarative


# define the dialogs designed for the NSF demo in May 2913
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
            
    
    
def initializeAllDialogs(arborAPI):
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
        self.fileSelectorNewick.setNameFilter("Newick files (*.phy)")

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