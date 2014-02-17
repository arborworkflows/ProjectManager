# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 09:00:25 2013

@author: clisle
"""

import pymongo
from bson import ObjectId
from pymongo import Connection
import json
import time

# needed to import R-based algorithms from Geiger and Picante
from ArborAlgorithmManagerAPI import ArborAlgorithmManager

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

# this is the abstract definition of a workstep inside a workflow.  Worksteps have a name,
# an update method, and an execute method.  The semantics are similar to the original VTK
# pipeline, where "update" is called on a workstep, and it will, invoke update on its predecessor
# filters, if needed.

class Workstep(object):
        def __init__(self):
            self.name = 'default'
            self.projectName = 'default'
            self.modifiedTime = -9999
            # added parameters array so can be serialized for all classes
            self.parameters = dict()

        def setProjectName(self,projectname):
            self.projectName = projectname

        def setName(self,namestring):
            self.name = namestring;

        def getProjectName(self):
            return self.projectName

        # subclasses will have a variety of parameters, put them all in a named
        # keystore for consistency.  This will enable serialization of all parameters to storage
        def setParameter(self,parameterName,parameterValue):
            self.parameters[parameterName] = parameterValue

        # when a workstep is serialized from storage, all of its parameters are available in a single dict,
        # so just asssign the
        def setParameters(self,parameterDictionary):
            self.parameters = parameterDictionary

        # method that is called to make sure the output of a workstep is current/
        # this method will contain whatever tests are needed to determine if the filter
        # needs to be run

        def update(self):
            raise NotImplementedError
            self.execute()

        # internal method that is invoked by the update method when the output needs to
        # be generated. This is where the actual "processing" of a filter is done. When
        # execute is finished, there should be output written into the output location,
        # whatever that location is (may vary depending on the subclass?)

        def execute(self):
            self.writeOutput()
            raise NotImplementedError

        def writeOutput(self):
            # write output here
            pass

# define a custom class for exceptions
class WorkstepException(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)

# utility class to represent information about flows between worksteps.  It is expected that there will be a hierarchical
# class definition of data types

class WorkstepInformationObject:
    def __init__(self):
        self.type = 'data.arbor.any'
        self.collectionName = 'default'
        self.sourceObject = None
        # this is set by the filter when output is generated
        self.modifiedTime = -9999

    def typeMatches(self,typedefinition):
        return self.type == typedefinition

    def setSourceObject(self,objectPtr):
        self.sourceObject = objectPtr

    def printSelf(self):
        print "infoObject: ",self.modifiedTime, self.type, self.collectionName




# This is the workstep type which outputs a dataset spec, not the dataset itself.  The spec is defined
# as a table with the tuple (project,datatype,datasetname) contained in the output.  This class stores the spec
# table in the output collection when it executes.  This source is used when server-side processing algorithms with the
# ability to directly read the data are the following steps in the workflow, as no actual dataset information comes out
# of this step, only the specification for which dataset the user is interested in processing.

class DatasetSpecTableSourceWorkstep(Workstep):
    def __init__(self):
        Workstep.__init__(self)
        self.type = "arbor.analysis.spectablesource"
        self.inputType = "data.table.spectable"
        self.outputType = "data.table.spectable"
        self.databaseName = ''
        self.outputInformation = WorkstepInformationObject()
        self.inputs = []
        self.outputInitialized = False;

    # utility class to create unique collection names for worksteps within workflows.
    def getOutputCollectionNameForWorkstep(self):
        newname = self.projectName+"."+self.name
        return newname

    # set the database to read/write to
    def setDatabaseName(self,dbname):
        self.databaseName = dbname;

    # this is a source object, no action performed on addInput
    def addInput(self,OutputInformation):
        pass

    # output the type and the collection value
    def getOutput(self):
        outinfo = self.outputInformation
        outinfo.sourceObject = self
        outinfo.type = self.outputType
        outinfo.collectionName = self.getOutputCollectionNameForWorkstep()
        #print self.name," sending outinfo object:"
        #outinfo.printSelf()
        self.outputInitialized = True;
        return outinfo

    def printSelf(self):
        print "workstep: ",self.name, " time: ",self.modifiedTime
        print "    output collection: ",self.outputInformation.collectionName
        for p in self.parameters:
            print "    paramter ", p, " = ",self.parameters[p]


    def InputTypeMatches(self,informationObject):
        # return true if the type passed is the type of data we are expecting
        return informationObject.typeMatches(self.inputType)

    # this method examines the input to see if any change has occurred.  The
    # input information objects are examined.  The execute method is called if
    # needed to generate updated output because input(s) have been modified.

    def update(self):
        # if this is the last chain in the fitlter, then force initialization
        # by hand before the first update call
        if  not self.outputInitialized:
            self.getOutput()
        # since this only updates a spec, just run each time
        self.execute()

    # run the filter.  This reads the parameters and outputs a table containing
    # the parameter information

    def execute(self):
        print self.name+" executing"
        # setup mongo connection and look through all input collections, copying
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()
        # loop through all parameters on this filter and output a line in the collection
        # for each parameter as a key/value pair
        for thisparam in self.parameters:
            outdict = dict()
            outdict['key'] = thisparam
            outdict['value'] = self.parameters[thisparam]
            # find all documents in this input (repeated for each input)
            outputcoll.insert(outdict)
            #  pause the writer enough to allow the write to complete? Found example code here:
            #  http://sourceforge.net/u/rick446/random/ci/master/tree/lib.py
            db.last_status()
        # rest the filter's modified time and assign it to the output object
        self.outputInformation.modifiedTime = self.modifiedTime = time.time()
        connection.close()

    # delete output collection so there is nothing left in the database.  This is inherited to subclasses
    # as well, so DatasetFilterWorksteps also have this defined.

    def deleteOutput(self):
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()





# This is a sample class that sets the profile for worksteps that process input to output
# invoking their processing on the data as it passes through

class DatasetCopyWorkstep(Workstep):
    def __init__(self):
        Workstep.__init__(self)
        self.type = "arbor.analysis.datasetcopy"
        self.inputType = "data.arbor.any"
        self.outputType = "data.arbor.any"
        self.databaseName = ''
        self.outputInformation = WorkstepInformationObject()
        self.inputs = []
        self.outputInitialized = False;

    # utility class to create unique collection names for worksteps within workflows.
    def getOutputCollectionNameForWorkstep(self):
        newname = self.projectName+"."+self.name
        return newname

    # set the database to read/write to
    def setDatabaseName(self,dbname):
        self.databaseName = dbname;

    # define the workstep input to be connected to the output information of another step,
    # The output information is a tuple: [parent_workstate_name,datatype_declaration,collection_name]
    def addInput(self,OutputInformation):
        if self.InputTypeMatches(OutputInformation):
            self.inputs.append(OutputInformation)
            print self.name," input list is now:"
            for thisInput in self.inputs:
                print "      input: ",thisInput.sourceObject.name, " time: ",thisInput.sourceObject.modifiedTime
        else:
            raise WorkstepException("type mismatch at input of workstep "+self.name)

    # output the type and the collection value
    def getOutput(self):
        outinfo = self.outputInformation
        outinfo.sourceObject = self
        outinfo.type = self.outputType
        outinfo.collectionName = self.getOutputCollectionNameForWorkstep()
        print self.name," sending outinfo object:"
        outinfo.printSelf()
        self.outputInitialized = True;
        return outinfo

    def printSelf(self):
        print "workstep: ",self.name, " time: ",self.modifiedTime
        for thisInput in self.inputs:
            print "input: ",thisInput.sourceObject.name, " time: ",thisInput.sourceObject.modifiedTime
        print "output collection: ",self.outputInformation.collectionName


    def InputTypeMatches(self,informationObject):
        # return true if the type passed is the type of data we are expecting
        return informationObject.typeMatches(self.inputType)

    # this method examines the input to see if any change has occurred.  The
    # input information objects are examined.  The execute method is called if
    # needed to generate updated output because input(s) have been modified.
    # Execute methods might require access to Arbor algorithms in R.  If so,
    # the method will be called with the optional algorithmSubsystem parameter defined.

    def update(self,algorithmSubsystem=None):
        # if this is the last chain in the filter, then force initialization
        # by hand before the first update call
        if  not self.outputInitialized:
            self.getOutput()
        print self.name," update called"
        filterNeedsToBeRun = False;
        # go through all inputs and see if any of them have changed. If so,
        # then we need to re-run this filter
        for thisInput in self.inputs:
            print "requesting update of input: ",thisInput.sourceObject.name
            thisInput.sourceObject.update()
            # if the previous step hasn't run yet, invoke it
            print "comparing source time of ",thisInput.modifiedTime, " with ",self.modifiedTime
            if thisInput.modifiedTime > self.modifiedTime:
                # input has changed since this filter executed, so mark for execution
                filterNeedsToBeRun = True;
        # if this filter needs to run, then run it and clear out the modified flags on the inputs
        if filterNeedsToBeRun:
            if algorithmSubsystem == None:
                self.execute()
            else:
                self.execute(algorithmSubsystem)

    # run the filter.  This base class is a copy filter. A separate mongo connection
    # is opened and closed during the execution of the filter.  The filter's modified time
    # is updated to allow for pipeline execution behavior.

    def execute(self, algorithms=None):
        print self.name+" executing"
        # setup mongo connection and look through all input collections, copying
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()
        # loop through all inputs and process all objects in the inputs
        for thisInput in self.inputs:
            inputcoll = db[thisInput.collectionName]
            # find all documents in this input (repeated for each input)
            queryResults = inputcoll.find()
            print "found that ", thisInput.collectionName," has ",queryResults.count(), " records"
            # write the documents into the output collection and indicate the output time changed
            for result in queryResults:
                outputcoll.insert(result)
            #  pause the writer enough to allow the write to complete? Found example code here:
            #  http://sourceforge.net/u/rick446/random/ci/master/tree/lib.py
            db.last_status()
        # rest the filter's modified time and assign it to the output object
        self.outputInformation.modifiedTime = self.modifiedTime = time.time()
        connection.close()

    # delete output collection so there is nothing left in the database.  This is inherited to subclasses
    # as well, so DatasetFilterWorksteps also have this defined.

    def deleteOutput(self):
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()

# This workstep functions as a source that reads a collection and outputs the collection
# data when connected as the source of a pipeline.  It has one parameter, which is the name of the
# dataset (stored in a mongo collection) to be steamed out from this workstep.

class DatasetSourceWorkstep(Workstep):
    def __init__(self):
        Workstep.__init__(self)
        self.inputType = "none"
        self.type = "arbor.analysis.datasetsource"
        self.outputType = "data.arbor.any"
        self.databaseName = ''
        self.outputs = []
        # setup the parameter for this filter with a enpty dataset name
        self.parameters['dataset'] = ''

    def setSourceCollectionName(self,collectionName):
        self.parameters['dataset'] = collectionName


    # utility class to create unique collection names for worksteps within workflows.
    def getOutputCollectionNameForWorkstep(self):
        if (self.parameters['dataset'] != ''):
            return self.parameters['dataset']
        else:
            raise WorkstepException("unspecified dataset on Dataset Source workstep")

    # set the database to read/write to
    def setDatabaseName(self,dbname):
        self.databaseName = dbname;

    # AddInput doesn't do anything for a source object
    def addInput(self,OutputInformation):
        pass

    # output the type and the collection value
    def getOutput(self):
        outinfo = WorkstepInformationObject()
        outinfo.type = self.outputType
        outinfo.sourceObject = self
        outinfo.collectionName = self.getOutputCollectionNameForWorkstep()
        outinfo.modifiedTime = time.time()
        return outinfo

    def printSelf(self):
        print "dataset source workstep: ",self.name, " time: ",self.modifiedTime
        print "output collection: ",self.getOutputCollectionNameForWorkstep()

    # since this is a source pointing to an existing collections, then
    # nothing is done by the update and execute methods.

    def update(self):
        pass

    # run the filter.  This base class is a copy filter.
    def execute(self):
       pass

    # since this is a database source object, we don't want to accidentally delete the source
    # collection, so this message doesn't do anything for the Dataset source workstep type
    def deleteOutput(self):
        pass

#-------------------------------------------------------------
# Filtering workstep - an attribute can be selected and filtered on for GreaterThan, LessThan, NotEqual
#-------------------------------------------------------------
class DatasetFilteringWorkstep(DatasetCopyWorkstep):
    def __init__(self):
        DatasetCopyWorkstep.__init__(self)
        self.type = 'arbor.analysis.datasetfilter'
        # these were replaced to use parameters instead
        #self.filterAttribute = ""
        #self.limitValue = 0.0
        #self.testType = 'LessThan'
        self.parameters['filterAttribute'] = ''
        self.parameters['filterValue'] = 0.0
        self.parameters['filterOperation'] = 'LessThan'

    # test type is GreaterThan, LessThan, NotEqual
    def setFilterTest(self,typestring):
        self.parameters['filterOperation'] = typestring

    # determine which document attribute should be used as a parameter
    def setFilterAttribute(self,attrString):
         self.parameters['filterAttribute'] = attrString

    def setFilterValue(self,number):
        self.parameters['filterValue'] = number

   # run the filter.  The filter attribute and filter value are used to build a query for the
   # source datasets.  Only documents matching the criteria are passed through the filter

    def execute(self,algorithms=None):
        print self.name+" executing"
        # setup mongo connection and look through all input collections, copying
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()
        # loop through all inputs and process all objects in the inputs
        for thisInput in self.inputs:
            inputcoll = db[thisInput.collectionName]

            # find all documents in this input (repeated for each input) that match the
            # test criteria.  If no criteria is specified, pass records through

            for case in switch(self.parameters['filterOperation']):
                if case('GreaterThan'):
                    query = {self.parameters['filterAttribute'] : {'$gt' : self.parameters['filterValue']}}
                    break
                if case ('LessThan'):
                    query = {self.parameters['filterAttribute'] : {'$lt' : self.parameters['filterValue']}}
                    break
                if case ('NotEqual'):
                    query = {self.parameters['filterAttribute'] : {'$ne' : self.parameters['filterValue']}}
                    break
                if case ('Equal') or case('EqualTo'):
                    query = {self.parameters['filterAttribute'] : self.parameters['filterValue']}
                    break
            print "query used was: ",query
            queryResults = inputcoll.find(query)

            # write the documents into the output collection and indicate the output time changed
            for result in queryResults:
                outputcoll.insert(result)
        # rest the filter's modified time and assign it to the output object
        self.outputInformation.modifiedTime = self.modifiedTime = time.time()
        print self.name," passed ",outputcoll.count(), " records"
        connection.close()



#-------------------------------------------------------------
# fitContinuous workstep - this expects two inputs.  The first is the tree, the second is the matrix
# this needs to be expanded to have named ports but we want to try this first to evaluate if the
# approach works.
#-------------------------------------------------------------
class GeigerFitContinuousWorkstep(DatasetCopyWorkstep):
    def __init__(self):
        global algorithms
        DatasetCopyWorkstep.__init__(self)
        self.type = 'arbor.analysis.geigerfitcontinuous'
        self.inputType = 'data.table.spectable'

    # since this will receive spec tables as inputs describing the tree and table, check for the
    # correct types.
    # ACTION - replace with type checking of separate ports eventually (tree and characters, etc.)
    def InputTypeMatches(self,informationObject):
        # return true if the type passed is the type of data we are expecting
        return informationObject.typeMatches(self.inputType)

    def execute(self, algorithmSubsystem=None):
        # we need to use the pre-existing, global instance of Arbor algorithms,
        # so reference the global here.
        global algorithms

        print self.name+" executing"
        # setup mongo connection and look through all input collections, copying
        connection = Connection('localhost', 27017)
        if len(self.databaseName)>0:
            db = connection[self.databaseName]
        else:
            db = connection['arbor']
        outputcoll = db[self.outputInformation.collectionName]
        # clear out the output to prepare for running an algorithm
        outputcoll.drop()

        # check that we have both inputs needed (tree and matrix specs).  If so, then read the
        # dataset spec records
        # from the input collections and use the dataset references to invoke the algorithm, which
        # requires just the references (since the algorithm opens the collections directly).

        if len(self.inputs) == 2:
            treeSpecCollection = db[self.inputs[0].collectionName]
            matrixSpecCollection = db[self.inputs[1].collectionName]
            treequery = dict()
            treequery['key'] = 'project'
            treeProjectName = treeSpecCollection.find(treequery)[0]['value']
            treequery2 = dict()
            treequery2['key'] = 'dataset'
            treeDatasetName = treeSpecCollection.find(treequery2)[0]['value']
            print "treeProject:",treeProjectName," dataset:",treeDatasetName
            matrixQuery = dict()
            matrixQuery['key'] = 'dataset'
            matrixDatasetName = matrixSpecCollection.find(treequery2)[0]['value']
            # all datasets have to be in the same project for the algorithms to look them up
            # so all we need to read is the dataset name for the character matrix, use the
            # rest of the information from the tree dataset
            print "matrix Project:",treeProjectName," dataset:",matrixDatasetName

            # check that the two needed parameters (character and outputTree) are defined
            # for this workstep instance, attempt processing only if they are defined. If everything
            # is available, run the algorithm on the selected datasets.  We use the pre-allocated version
            # of the

            if ('character' in self.parameters) and ('outputTree' in self.parameters):
                print "fitContinuous: found selected character defined as: ",self.parameters['character']
                print "fitContinuous: found outputTree defined as: ",self.parameters['outputTree']

                # only attempt to run the analysis if the algorithm subsystem is defined. This relies
                # on the global algorithms definition
                if algorithmSubsystem != None:
                    print "fitContinous: running algorithm"
                    algorithmSubsystem.fitContinuous(self.databaseName,treeProjectName,treeDatasetName, matrixDatasetName,
                          self.parameters['selectedCharacter'],self.parameters['outputTree'])
                else:
                    print "fitContinous:  couldn't connect with AlgorithmManager instance.. skipping"
            else:
                print "fitContinuous: Please define both a character parameter and an outputtree parameter before running fitContinuous"
        else:
            print "fitContinuous: Exactly two inputs (a treeSpec and matrixSpec) are required"


        # write the documents into the output collection and indicate the output time changed
        #for result in queryResults:
        #    outputcoll.insert(result)
        # rest the filter's modified time and assign it to the output object
        self.outputInformation.modifiedTime = self.modifiedTime = time.time()
        print self.name," completed fit continuous workstep "
        connection.close()