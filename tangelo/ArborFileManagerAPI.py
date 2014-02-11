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


import pymongo
from bson import ObjectId
from pymongo import Connection
import json
import bson.json_util
import csv

# used for OpenTreeOfLife access
import urllib
import urllib2

# used to parse analysis names from our list of collections
import re

import sys
sys.path.append("tangelo")

# import the recursive algorithm to process phyloXML records and create a mongo collection
#import phyloimport_algorithm

# import the algorithm to add a root to unrooted trees
#import root_phylotree_algorithm

import ArborAlgorithmManagerAPI


import phyloimport_algorithm
import phyloexport_algorithm

import root_phylotree_algorithm

# parser routine for PhyloXML
from Bio import Phylo

# parser routine for fasta files & sequences
from Bio import SeqIO

# load API for managing workflows
import ArborWorkflowManager


# look at a sting and if it is a floating point number, convert its type to avoid saving "0.345" when
# we really want to save 0.345.  We have two tests in sequence so integer values can be returned as ints instead of floats

#def convertIfNumber(s):
#    try:
#        float(s)
#        return float(s)
#    except ValueError:
#        return s

def convertIfNumber(s):
    try:
        int(s)
        return int(s)
    except ValueError:
        try:
            float(s)
            return float(s)
        except ValueError:
            return s

# utility class to add switch statements
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


class ArborFileManager:

    def __init__(self):
        self.projectList = []
        self.datatypeList = []
        self.datasetList = []
        self.currentProjectName = ''
        self.defaultMongoHost = 'localhost'
        self.defaultMongoPort = 27017
        #self.defaultMongoDatabase = 'xdata'
        self.defaultMongoDatabase = 'arbor'
        self.workflows = dict()
        # all collections created have a prefix to destinguish arbor collections
        # from other collections in the database.  The default can be changed
        # through exercsting the API call to set an alternative string. Same for the separation
        # characters
        #self.prefixString = 'ar_'
        self.prefixString = ''
        self.separatorString = "."
        self.projectCollectionName = self.prefixString+'projects'

        # the default mode is no GUI, so no Qt signals are emitted. if a Qt GUI
        # is connected and this state variable is set, then signals will be emitted for
        # some events to update
        self.QtGuiEnabled = False

    # this is called to enable the creation of signals
    def setGuiEnabled(self,enabled):
        self.QtGuiEnabled = enabled

    # change the default prefix string
    def setPrefixString(self,newstr):
       self.prefixString = newstr;
       self.projectCollectionName = self.prefixString+'projects'

    # change the default prefix string
    def setSeparatorString(self,newstr):
       self.separatorString = newstr;

    # allow for the default parameters for the mongo instance to be changed and queried
    def setMongoHost(self,hostname):
        self.defaultMongoHost = hostname;
    def getMongoHost(self):
        return self.defaultMongoHost
    def setMongoDatabase(self,database):
        self.defaultMongoDatabase = database
    def getMongoDatabase(self):
        return self.defaultMongoDatabase
    def setMongoPort(self,portnumber):
        self.defaultMongoPort = portnumber
    def getMongoPort(self):
        return self.defaultMongoPort



    def initDatabaseConnection(self):
        # tf a previous database connection is open, close it.  Anticipate the time when
        # an instance of this API could persist for a long time in a public place where
        # multiple backing databases might be in use.  Don't leave stranded connections.
        if (getattr(self,'connection',False)):
            self.connection.close()
        self.connection = Connection(self.defaultMongoHost, self.defaultMongoPort)
        self.db = self.connection[self.defaultMongoDatabase]
        # if there is a GUI, its project list needs to be updated because of the change in
        # the backing store for the API.
        print "changed database"
        if (self.QtGuiEnabled):
            self.projectListChangedSignal.emit()

    def insertIntoMongo(self,item, collection):
        return collection.insert(item)

    # create the record in Mongo for a new project
    def newProject(self,projectName):
        collectionName = self.prefixString+'projects'
        print "project collection to use is:",collectionName
        projectCollection = self.db[collectionName]

        # we could increase flexability later by creating a UI to add/remove
        # types, but initially just create standard datatypes for this project
        # already included in the record
        projectRecord = {"type" : "ArborProject",
                         "name" : projectName ,
                         #"datatypes" : ["PhyloTree","CharacterMatrix","Observations"],
                         "datatypes" : []
                         #"PhyloTree" : [],
                         #"CharacterMatrix" : [],
                         #"Observations" : []
                         }
        self.insertIntoMongo(projectRecord,projectCollection)

    # look in the database and return a list of the projects currently in the
    # database
    def getListOfProjectNames(self):
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        newlist = []
        #projectlist = self.db.ar_projects.aggregate({ '$project' : {'_id' : 0 , 'name' : 1}})['result']
        projectlist = self.db[self.projectCollectionName].aggregate({ '$project' : {'_id' : 0 , 'name' : 1}})['result']

        print "found ",len(projectlist), " projects"
        for i in range(0,len(projectlist)):
            #print projectlist[i]
            # overlook any totally empty project records
            if len(projectlist[i]) > 0:
                newlist.append( projectlist[i][u'name'])
        return newlist

    def setCurrentProjectName(self,prname):
        print "api: setting curren project to: ",prname
        self.currentProjectName = prname
    def getCurrentProjectName(self):
        return self.currentProjectName

    # look in the database and return a list of the datatypes allowed by a
    # particular project
    def getListOfTypesForProject(self, projname):
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        newlist = []
        project = self.db[self.projectCollectionName].find_one({"name" : projname})
        #print "found project record: ", project
        # some projects may not have dataypes yet, true during initial development at least
        if u'datatypes' in project:
            projecttypes = project[u'datatypes']
            for i in range(0,len(projecttypes)):
                newlist.append( projecttypes[i])
                #print "found type: ",projecttypes[i]
        return newlist

    # find and remove a project indexed through its project name
    def deleteProjectNamed(self,projectName):
        print "removing project named: ",projectName
        project = self.db[self.projectCollectionName].find_one({"name" : projectName})

        # first drop the dataset collections.  Do this by looking through all
        # the datatypes this project has and deleting all instances of any type
        typelist = self.getListOfTypesForProject(projectName)
        for datatype in typelist:
            if datatype in project:
                datasetlist = project[datatype]
                #print "found datasets: ",datasetlist
                for i in range(0,len(datasetlist)):
                    # each dataset name is the key in a dictionary.  We can
                    # assume there is only one key in the dictionary since each
                    # dataset has its own dict
                    collectionName = self.prefixString+projectName+self.separatorString+datatype+self.separatorString+datasetlist[i].keys()[0]
                    print "deleting dataset: ",collectionName
                    self.db.drop_collection(collectionName)
        # now remove the project record from the projects collection
        result = self.db[self.projectCollectionName].remove({ 'name' : projectName})
        return result

    # we might change the naming algorithm later, so lets use this method to lookup the names
    def returnCollectionForObjectByName(self,projectName,datatypeName, datasetName):
        collectionName = self.prefixString+projectName+self.separatorString+datatypeName+self.separatorString+datasetName
        return collectionName

    # similar to above, but for analyses
    def returnCollectionForAnalysisByName(self, analysis_name):
        collection_name = "%sanalyses_%s" % (self.prefixString, analysis_name)
        return collection_name

    # Convert dataset to a text string
    def getDatasetAsTextString(self,projectName,datatypeName, datasetName,stringFormat):
        outputString = None
        collectionName = self.returnCollectionForObjectByName(projectName,datatypeName, datasetName)
        datasetCollection = self.db[collectionName]
        if (datatypeName == "PhyloTree"):
          treeCollection = datasetCollection
          if (stringFormat == "Newick" or stringFormat == "newick"):
             outputString = phyloexport_algorithm.convertTreeToNewickString(treeCollection)
          elif (stringFormat == "PhyloXML" or stringFormat =="phyloxml"):
             print "to be implemented"
          else:
             print "unrecognized format ", stringFormat
        elif (datatypeName == "CharacterMatrix"):
          if (stringFormat == "CSV" or stringFormat == "csv"):
             outputString = phyloexport_algorithm.convertTableToCSVString(datasetCollection)
          elif (stringFormat == "header" or stringFormat == "headers"):
              outputString = phyloexport_algorithm.getHeadersForTable(datasetCollection)
          else:
             print "unrecognized format ", stringFormat

        return outputString

     # find and remove a dataset instance
    def deleteDataset(self,projectName,datatypeName, datasetName):
        print "removing dataset from project named: ",projectName
        project = self.db[self.projectCollectionName].find_one({"name" : projectName})

        # first drop the dataset collections.  Do this by looking through all
        # the datatypes this project has and deleting all instances of any type
        typelist = self.getListOfTypesForProject(projectName)
        if datatypeName in typelist:
            datasetlist = project[datatypeName]
            #print "found datasets: ",datasetlist
            for i in range(0,len(datasetlist)):
                if datasetlist[i].keys()[0] == datasetName:
                    # each dataset name is the key in a dictionary.  We can
                    # assume there is only one key in the dictionary since each
                    # dataset has its own dict
                    collectionName = self.prefixString+projectName+self.separatorString+datatypeName+self.separatorString+datasetlist[i].keys()[0]
                    print "deleting dataset named: ",datasetName, " in collection:",collectionName
                    # remove the corresponding entry from the list to delete the reference to the dataset
                    datasetlist.pop(i)
                    # now push the changed dictionary back out to update the project record
                    self.db[self.projectCollectionName].save(project)
                    # delete the dataset itself by dropping the whole collection
                    result = self.db.drop_collection(collectionName)
            if len(datasetlist) == 0:
                # we deleted the last entry of this type, so delete the type from the datatypes list
                typelist = project[u'datatypes']
                for i in range(0,len(typelist)):
                    if typelist[i] == datatypeName:
                        typelist.pop(i)
                        self.db[self.projectCollectionName].save(project)

    def getListOfDatasetsByProjectAndType(self,projectName,typeName) :
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        newlist = []
        project = self.db[self.projectCollectionName].find_one({"name" : projectName})
        #print "found project record: ", project
        # some projects may not have dataypes yet, true during initial development at least
        if u'datatypes' in project:
            projecttypes = project[u'datatypes']
            if typeName in projecttypes:
                listOfInstances = project[typeName]
                #print "found instances: ",listOfInstances
                for j in range(0,len(listOfInstances)):
                        newlist.append(listOfInstances[j].keys()[0])
        return newlist



    # ------------------- tree traversal and update using phyloimport algorithm

    # add a tree to the project
    def newTreeInProject(self,treename,treefile,projectTitle, treetype):
        collectionName = self.prefixString+projectTitle+self.separatorString+"PhyloTree"+self.separatorString+treename
        treeCollection = self.db[collectionName]
        print "uploading tree to collection: ",collectionName
        print "treetype is: ",treetype
        # create the new collection in mongo for this tree
        trees = Phylo.parse(treefile, treetype)
        #print "length of trees list: ",len(trees)
        for tree in trees:
            #process tree
            phyloimport_algorithm.recursive_clade(tree, treeCollection)
            root_phylotree_algorithm.addRootToTree(treeCollection)
            # add a tree record entry to the 'PyloTree' array in the project record
            self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'PhyloTree': {treename:treefile}}})
            self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'PhyloTree'}})

    # add a tree to the project
    def newTreeInProjectFromString(self,treename,treestring,projectTitle, description,treetype):
        collectionName = self.prefixString+projectTitle+self.separatorString+"PhyloTree"+self.separatorString+treename
        treeCollection = self.db[collectionName]
        treeCollection.drop()
        print "uploading tree to collection: ",collectionName
        print "treetype is: ",treetype

        # if the project does not exist, create it
        projectCollectionName = self.prefixString + 'projects'
        if self.db[projectCollectionName].find_one({"name": projectTitle}) == None:
            self.newProject(projectTitle)

        # create the new collection in mongo for this tree.  The tree is encoded
        # in a string, so it needs to be processed slightly different than from a file
        from StringIO import StringIO
        handle = StringIO(treestring)
        trees = Phylo.parse(handle, treetype)
        #print "length of trees list: ",len(trees)
        for tree in trees:
            phyloimport_algorithm.recursive_clade(tree, treeCollection)
            # add a tree record entry to the 'PyloTree' array in the project record
            self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'PhyloTree': {treename:str(description)}}})
            self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'PhyloTree'}})
            # make sure the tree is rooted, so viewers work
            root_phylotree_algorithm.addRootToTree(treeCollection)

            # emit a signal so the GUI knows to update
            if (self.QtGuiEnabled):
                self.datatypeListChangedSignal.emit();
                self.datasetListChangedSignal.emit();


  # add a tree record for exising collection
    def newTreeInProjectFromExistingCollection(self,treename,projectTitle,description):
        collectionName = self.prefixString+projectTitle+self.separatorString+"PhyloTree"+self.separatorString+treename
        print "adding record of tree in collection: ",collectionName
        # add a tree record entry to the 'PyloTree' array in the project record

        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'PhyloTree': {treename:str(description)}}})
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'PhyloTree'}})
        # emit a signal so the GUI knows to update
        if (self.QtGuiEnabled):
            self.datatypeListChangedSignal.emit();
            self.datasetListChangedSignal.emit();



    # query from the OpenTreeOfLife.  This routine performs the fetch from OTL,
    # retrieves a newick tree and processes it to load into the Arbor database
    def newTreeFromOpenTreeOfLife(self,treename,ottolid,projectTitle):
        url = 'http://opentree-dev.bio.ku.edu:7474/db/data/ext/GoLS/graphdb/getDraftTreeForOttolID'
        values = {"ottolID" : ottolid}
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        print "received OTL response.  Ingesting tree..."
        #system.fflush()
        tree_page = response.read()
        otltreeAsJson = json.loads(tree_page)
        self.newTreeInProjectFromString(treename,otltreeAsJson["tree"],projectTitle,ottolid,"newick")



    # add a character matrix to the project
    def newCharacterMatrixInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+self.separatorString+"CharacterMatrix"+self.separatorString+instancename
        newCollection = self.db[collectionName]
        print "uploading characters to collection: ",collectionName
        # create the new collection in mongo for this tree

        # not all CSV files are the same, so interpret with U=universal
        # newlines
        with open(filename, 'rbU') as csvfile:
            #dialect = csv.Sniffer().sniff(csvfile.read(1024))
            #csvfile.seek(0)
            #reader = csv.reader(csvfile, dialect)
            reader = csv.reader(csvfile)
            rownum = 0
            for row in reader:
                if rownum == 0:
                    header = row
                    print "header row: ",header
                    rownum = rownum+1
                else:
                    characterEntry = dict()
                    for colnum,columntitle in enumerate(row):
                        #print "column: ",colnum, " title: ",columntitle
                        # add each attribute name and value as an entry in the dict.
                        # this fixes the error where all attribute values were strings.
                        characterEntry[header[colnum]] = convertIfNumber(columntitle)
                        # now insert the dictonary as a single entry in the collection
                    newCollection.insert(characterEntry)
                    rownum = rownum+1
                    print rownum

        # add a  matrix record entry to the 'CharacterMatrix' array in the project record
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'CharacterMatrix': {instancename:filename}}})
        # make sure the character type exists in this project
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'CharacterMatrix'}})

    # add a character matrix to the project
    def newCharacterMatrixInProjectFromString(self, datasetname, data, projectTitle, filename):
        collectionName = self.prefixString+projectTitle+self.separatorString+"CharacterMatrix"+self.separatorString+datasetname
        newCollection = self.db[collectionName]
        print "uploading characters to collection: ",collectionName

        # create the new collection in mongo for this table
        lines = data.splitlines(True)
        rownum = 0
        for row in csv.reader(lines):
            if rownum == 0:
                header = row
                print "header row: ",header
                rownum = rownum+1
            else:
                characterEntry = dict()
                for colnum,columntitle in enumerate(row):
                    print "column: ",colnum, " title: ",columntitle
                    # add each attribute name and value as an entry in the dict
                    characterEntry[header[colnum]] = columntitle
                    # now insert the dictonary as a single entry in the collection
                newCollection.insert(characterEntry)
                rownum = rownum+1

        # add a matrix record entry to the 'CharacterMatrix' array in the project record
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'CharacterMatrix': {datasetname:filename}}})
        # make sure the character type exists in this project
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'CharacterMatrix'}})

    # add a character matrix to the project
    def newOccurrencesInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+self.separatorString+"Occurrences"+self.separatorString+instancename
        newCollection = self.db[collectionName]
        print "uploading occurreces to collection: ",collectionName
        # create the new collection in mongo for this tree

        # not all CSV files are the same, so interpret with U=universal
        # newlines
        with open(filename, 'rbU') as csvfile:
            reader = csv.reader(csvfile)
            rownum = 0
            for row in reader:
                if rownum == 0:
                    header = row
                    print "header row: ",header
                    rownum = rownum+1
                else:
                    nextEntry = dict()
                    for colnum,columntitle in enumerate(row):
                        #print "column: ",colnum, " title: ",columntitle
                        # add each attribute name and value as an entry in the dict
                        nextEntry[header[colnum]] = columntitle
                        # now insert the dictonary as a single entry in the collection
                    newCollection.insert(nextEntry)

        # add a  matrix record entry to the 'CharacterMatrix' array in the project record
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'Occurrences': {instancename:filename}}})
        # Add the occurrence data type in the project if the record isn't already there
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'Occurrences'}})

    # add sequences to the project
    def newSequencesInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+self.separatorString+"Sequences"+self.separatorString+instancename
        # create the new collection in mongo for sequence data
        newCollection = self.db[collectionName]
        print "uploading sequences to collection: ",collectionName

        for seq_record in SeqIO.parse(filename,"fasta"):
            print seq_record
            seqDict = dict()
            seqDict['id'] = seq_record.id
            seqDict['seq'] = repr(seq_record.seq)
            newCollection.insert(seqDict)

        # add a record entry to the 'Sequences' array in the project record
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$push': {u'Sequences': {instancename:filename}}})
        # make sure the sequence type exists in this project
        self.db[self.projectCollectionName].update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'Sequences'}})

#-----------------------------------
#------ workflows ------------------
#-----------------------------------


    def getWorkflowCollectionName(self,projectTitle):
       return self.prefixString+projectTitle+self.separatorString+'workflows'

    # add workflow to the project
    def newWorkflowInProject(self,instancename,projectName):
        print "new workflow in project: ",projectName
        # add a record entry to the 'Workflows' array in the project record
        self.db[self.projectCollectionName].update({"name": projectName}, { '$push': {u'Workflow': {instancename:instancename}}})
        # make sure the workflow type exists in this project
        self.db[self.projectCollectionName].update({"name": projectName}, { '$addToSet': {u'datatypes': u'Workflow'}})
        # add a record in the workflow document for this new workflow.  A list of the steps and the connections is
        # maintained in the backing database collection
        workflowCollectionName = self.getWorkflowCollectionName(projectName)
        workflowRecord = dict()
        workflowRecord[u'name'] = instancename
        workflowRecord[u'analyses'] = []
        workflowRecord[u'connections'] = []
        self.db[workflowCollectionName].insert(workflowRecord)

    def deleteWorkflow(self,instancename,projectName):
        print "removing dataset from project named: ",projectName
        project = self.db[self.projectCollectionName].find_one({"name" : projectName})

        # first drop the dataset collections.  Do this by looking through all
        # the datatypes this project has and deleting all instances of any type
        typelist = self.getListOfTypesForProject(projectName)
        if 'Workflow' in typelist:
            datasetlist = project['Workflow']
            print "found workflows: ",datasetlist
            for i in range(0,len(datasetlist)):
                if datasetlist[i].keys()[0] == instancename:
                    # remove the corresponding entry from the list to delete the reference to the dataset
                    datasetlist.pop(i)
                    # now push the changed dictionary back out to update the project record
                    self.db[self.projectCollectionName].save(project)
                    # delete the record for this workflow from the project's workflow document
                    workflowCollectionName = self.getWorkflowCollectionName(projectName)
                    self.db[workflowCollectionName].remove({'name': instancename})
            if len(datasetlist) == 0:
                # we deleted the last entry of this type, so delete the type from the datatypes list
                typelist = project[u'datatypes']
                for i in range(0,len(typelist)):
                    if typelist[i] == 'Workflow':
                        typelist.pop(i)
                        self.db[self.projectCollectionName].save(project)


    def returnWorkflowRecord(self,workflowName,projectTitle):
        collectionName = self.getWorkflowCollectionName(projectTitle)
        print "collection to check:",collectionName
        return (self.db[collectionName].find({'name':workflowName}))[0]

    # deprecated - remove soon?
    def returnWorkflowRecordDeprecated(self,workflowName,projectTitle):
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        project = self.db[self.projectCollectionName].find_one({"name" : projectTitle})
        print "found project record: ", project
        # some projects may not have dataypes yet, true during initial development at least
        if u'datatypes' in project:
            projecttypes = project[u'datatypes']
            print "projecttypes=",projecttypes
            if u'Workflow' in projecttypes:
                print "workflows in this project:",project[u'Workflow']
                if workflowName in project[u'Workflow']:
                    print "found record of this workflow:",workflowName,"in project ",projectTitle
                    workflowlist = self.db[self.getWorkflowCollectionName(projectTitle)].find({'name':workflowName})

        # nothing was found, so return empty
        return None

    def getStatusOfWorkflow(self,workflowName,projectTitle):
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        wfRecord = self.returnWorkflowRecord(workflowName,projectTitle)
        if wfRecord != None:
            return wfRecord
        return "error: couldn't find workflow"

    # add a new workstep to the workflow.  We accomplish this by instantiating a workflow manager and having it
    # add the step, then update the datbase again.  The format of workflows is encapsulated in the WorkflowManager.
    # to keep the state saved in the database, workflow manager instances don't persist between API calls.

    def newWorkstepInWorkflow(self,wflowName,workStepType,stepName,projectTitle):
        wfrecord = self.returnWorkflowRecord(wflowName,projectTitle)
        if (wfrecord != None) :
            workflowMgr = ArborWorkflowManager.WorkflowManager()
            workflowMgr.setDatabaseName(self.defaultMongoDatabase)
            workflowMgr.setProjectName(projectTitle)
            workflowMgr.loadFrom(wfrecord)
            workflowMgr.addWorkstepToWorkflow(workStepType, stepName)
            wfrecord = workflowMgr.serialize()
            self.db[self.getWorkflowCollectionName(projectTitle)].update({'name':wflowName},wfrecord)
        else:
            print "attempt to add step to non-existant workflow"


    # add a new workstep to the workflow.  We accomplish this by instantiating a workflow manager and having it
    # add the step, then update the datbase again.  The format of workflows is encapsulated in the WorkflowManager.
    # to keep the state saved in the database, workflow manager instances don't persist between API calls.

    def updateWorkstepParameter(self,wflowName,stepName,parameterName,parameterValue,projectTitle):
        wfrecord = self.returnWorkflowRecord(wflowName,projectTitle)
        if (wfrecord != None) :
            workflowMgr = ArborWorkflowManager.WorkflowManager()
            workflowMgr.setDatabaseName(self.defaultMongoDatabase)
            workflowMgr.setProjectName(projectTitle)
            workflowMgr.loadFrom(wfrecord)
            workflowMgr.updateParameterOfWorkstep(stepName,parameterName,parameterValue)
            wfrecord = workflowMgr.serialize()
            self.db[self.getWorkflowCollectionName(projectTitle)].update({'name':wflowName},wfrecord)
        else:
            print "attempt to add step to non-existant workflow"

    # connect the output of one analysis to the input of another analysis.  The initial ones didn't have
    # multiple outputs, so this interface needs to be extended.
    def connectStepsInWorkflow(self,wflowName,outStepName,inStepName,projectTitle):
        wfrecord = self.returnWorkflowRecord(wflowName,projectTitle)
        if (wfrecord != None) :
            workflowMgr = ArborWorkflowManager.WorkflowManager()
            workflowMgr.setDatabaseName(self.defaultMongoDatabase)
            workflowMgr.setProjectName(projectTitle)
            workflowMgr.loadFrom(wfrecord)
            workflowMgr.connectStepsInWorkflow(outStepName, inStepName, 'junkHereNotNeeded')
            wfrecord = workflowMgr.serialize()
            self.db[self.getWorkflowCollectionName(projectTitle)].update({'name':wflowName},wfrecord)
        else:
            print "attempt to add step to non-existant workflow"


    # read a workflow out of the database and execute it
    def executeWorkflowInProject(self,instancename,projectTitle):
        # if the workflow is defined, create new workflow manager instance, and load from the datastore record
        project = self.db[self.projectCollectionName].find_one({"name" : projectTitle})
        if u'datatypes' in project:
            projecttypes = project[u'datatypes']
            if u'Workflow' in projecttypes:
                testProfile = {instancename : instancename }
                if testProfile in project[u'Workflow']:
                    print "creating new workflow instance and loading it to run"
                    workflowMgr = ArborWorkflowManager.WorkflowManager()
                    # mongo always returns a list of dictionaries, since this is a singleton, pass the first one to the load
                    workflowDescription = self.db[self.getWorkflowCollectionName(projectTitle)].find({'name':instancename})[0]
                    workflowMgr.setDatabaseName(self.defaultMongoDatabase)
                    workflowMgr.setProjectName(projectTitle)
                    workflowMgr.loadFrom(workflowDescription)
                    workflowMgr.executeWorkflow()

    def returnListOfLoadedWorksteps(self):
        wfm =  ArborWorkflowManager.WorkflowManager()
        return wfm.returnListOfLoadedWorksteps()


#----------- workflows end ------------------------


    # return a python list filled with character strings
    def returnCharacterListFromCharacterMatrix(self,instancename,projectTitle):
        # for some reaseon, the str() was required to resolve the collection name in mongo
        collectionName = str(self.prefixString+projectTitle+self.separatorString+"CharacterMatrix"+self.separatorString+instancename)
        #print 'collection for attribute list is: ',collectionName
        matrix_collection = self.db[collectionName]
        record = matrix_collection.find_one()
        characterNames = []
        for key in record.keys():
            characterNames.append(key)
        return characterNames


#------------------ analyses ----------------

   # add analysis to TreeStore.
   # This function drops the analysis' collection first if it already exists.
   # This way we don't end up with duplicate documents.
    def newAnalysis(self, analysis_name, analysis_item):
        collection_name = self.returnCollectionForAnalysisByName(analysis_name)
        self.db.drop_collection(collection_name)
        analysis_collection = self.db[collection_name]
        self.insertIntoMongo(analysis_item, analysis_collection)

    # returns a list of analysis names
    def getListOfAnalysisNames(self):
        analysis_names = []
        regexp = re.compile(r"%sanalyses_(.*?)$" % self.prefixString)
        for collection_name in self.db.collection_names():
            match = regexp.search(collection_name)
            if match:
                analysis_names.append(match.group(1))
        return analysis_names


