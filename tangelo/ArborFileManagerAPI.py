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
import csv


# import the recursive algorithm to process phyloXML records and create a mongo collection
import phyloimport_algorithm

# parser routine for PhyloXML
from Bio import Phylo

# parser routine for fasta files & sequences
from Bio import SeqIO

class ArborFileManager:
    def __init__(self):
        self.projectList = []
        self.datatypeList = []
        self.datasetList = []
        self.currentProjectName = ''
        self.defaultMongoHost = 'localhost'
        self.defaultMongoPort = 27017
        self.defaultMongoDatabase = 'xdata'
        # all collections created have a prefix to destinguish arbor collections
        # from other collections in the database.  The default can be changed
        # through exercsting the API call to set an alternative string.
        self.prefixString = 'ar_'

    # change the default prefix string
    def setPrefixString(self,newstr):
       self.prefixString = newstr;

    # allow for the default parameters for the mongo instance to be changed
    def setMongoHost(self,hostname):
        self.defaultMongoHost = hostname;
    def setMongoDatabase(self,database):
        self.defaultMongoDatabase = database
    def setMongoPort(self,portnumber):
        self.defaultMongoPort = portnumber

    def initDatabaseConnection(self):
        self.connection = Connection(self.defaultMongoHost, self.defaultMongoPort)
        self.db = self.connection[self.defaultMongoDatabase]

    def insertIntoMongo(self,item, collection):
        return collection.insert(item)

    # create the record in Mongo for a new project
    def newProject(self,projectName):
        collectionName = self.prefixString+'projects'
        print "collection to use is:",collectionName
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
        projectlist = self.db.ar_projects.aggregate({ '$project' : {'_id' : 0 , 'name' : 1}})['result']
        print "found ",len(projectlist), " projects"
        for i in range(0,len(projectlist)):
            #print projectlist[i]
            # overlook any totally empty project records
            if len(projectlist[i]) > 0:
                newlist.append( projectlist[i][u'name'])
        return newlist

    def setCurrentProject(self,prname):
        print "api: setting curren project to: ",prname
        self.currentProjectName = prname
    def getCurrentProject(self):
        return self.currentProjectName

   # look in the database and return a list of the datatypes allowed by a
   # particular project
    def getListOfTypesForProject(self, projname):
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        newlist = []
        project = self.db.ar_projects.find_one({"name" : projname})
        print "found project record: ", project
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
        project = self.db.ar_projects.find_one({"name" : projectName})

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
                    collectionName = self.prefixString+projectName+"_"+datatype+"_"+datasetlist[i].keys()[0]
                    print "deleting dataset: ",collectionName
                    self.db.drop_collection(collectionName)
        # now remove the project record from the projects collection
        result = self.db.ar_projects.remove({ 'name' : projectName})
        return result

     # find and remove a dataset instance
    def deleteDataset(self,projectName,datatypeName, datasetName):
        print "removing dataset from project named: ",projectName
        project = self.db.ar_projects.find_one({"name" : projectName})

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
                    collectionName = self.prefixString+projectName+"_"+datatypeName+"_"+datasetlist[i].keys()[0]
                    print "deleting dataset named: ",datasetName, " in collection:",collectionName
                    # remove the corrresponding entry from the list to delete the reference to the dataset
                    datasetlist.pop(i)
                    # now push the changed dictionary back out to update the project record
                    self.db.ar_projects.save(project)
                    # delete the dataset itself by dropping the whole collection
                    result = self.db.drop_collection(collectionName)
            if len(datasetlist) == 0:
                # we deleted the last entry of this type, so delete the type from the datatypes list
                typelist = project[u'datatypes']
                for i in range(0,len(typelist)):
                    if typelist[i] == datatypeName:
                        typelist.pop(i)
                        self.db.ar_projects.save(project)

    def getListOfDatasetsByProjectAndType(self,projectName,typeName) :
        # return a list of only the project names by using the $project operator in mongo.
        # pick the 'result' field from the query
        newlist = []
        project = self.db.ar_projects.find_one({"name" : projectName})
        print "found project record: ", project
        # some projects may not have dataypes yet, true during initial development at least
        if u'datatypes' in project:
            projecttypes = project[u'datatypes']
            if typeName in projecttypes:
                listOfInstances = project[typeName]
                print "found instances: ",listOfInstances
                for j in range(0,len(listOfInstances)):
                    newlist.append(listOfInstances[j].keys()[0])
        return newlist

    # ------------------- tree traversal and update using phyloimport algorithm

    # add a tree to the project
    def newTreeInProject(self,treename,treefile,projectTitle):
        collectionName = self.prefixString+projectTitle+"_"+"PhyloTree"+"_"+treename
        treeCollection = self.db[collectionName]
        print "uploading tree to collection: ",collectionName
        # create the new collection in mongo for this tree
        trees = Phylo.parse(treefile, "phyloxml")
        #print "length of trees list: ",len(trees)
        for tree in trees:
            #process tree
            phyloimport_algorithm.recursive_clade(tree, treeCollection)
        # add a tree record entry to the 'PyloTree' array in the project record
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'PhyloTree': {treename:treefile}}})
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'PhyloTree'}})

    # add a character matrix to the project
    def newCharacterMatrixInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+"_"+"CharacterMatrix"+"_"+instancename
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
                        print "column: ",colnum, " title: ",columntitle
                        # add each attribute name and value as an entry in the dict
                        characterEntry[header[colnum]] = columntitle
                        # now insert the dictonary as a single entry in the collection
                    newCollection.insert(characterEntry)

        # add a  matrix record entry to the 'CharacterMatrix' array in the project record
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'CharacterMatrix': {instancename:filename}}})
        # make sure the character type exists in this project
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'CharacterMatrix'}})

    # add a character matrix to the project
    def newOccurrencesInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+"_"+"Occurrences"+"_"+instancename
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
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'Occurrences': {instancename:filename}}})
        # Add the occurrence data type in the project if the record isn't already there
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'Occurrences'}})

    # add sequences to the project
    def newSequencesInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+"_"+"Sequences"+"_"+instancename
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
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'Sequences': {instancename:filename}}})
        # make sure the sequence type exists in this project
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'Sequences'}})

   # add sequences to the project
    def newWorkflowInProject(self,instancename,filename,projectTitle):
        collectionName = self.prefixString+projectTitle+"_"+"Workflows"+"_"+instancename
        # create the new collection in mongo for sequence data
        newCollection = self.db[collectionName]
        print "uploading workflow to collection: ",collectionName

        for seq_record in SeqIO.parse(filename,"fasta"):
            print seq_record
            seqDict = dict()
            seqDict['id'] = seq_record.id
            seqDict['seq'] = repr(seq_record.seq)
            newCollection.insert(seqDict)

        # add a record entry to the 'Workflows' array in the project record
        self.db.ar_projects.update({"name": projectTitle}, { '$push': {u'Workflows': {instancename:filename}}})
        # make sure the workflow type exists in this project
        self.db.ar_projects.update({"name": projectTitle}, { '$addToSet': {u'datatypes': u'Workflows'}})
