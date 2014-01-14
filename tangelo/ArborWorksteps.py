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
            
        def setProjectName(self,projectname):
            self.projectName = projectname
            
        def setName(self,namestring):
            self.name = namestring;
            
        def getProjectName(self):
            return self.projectName
            
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

            

# utility class to represent information about flows between worksteps.  The will be a hierarchical
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

     
     
# This is a sample class that sets the profile for worksteps that process input to output
# invoking their processing on the data as it passes through
     
class DatasetCopyWorkstep(Workstep):
    def __init__(self):
        Workstep.__init__(self)
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
            raise TypeError

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
    
    def update(self):
        # if this is the last chain in the fitlter, then force initialization 
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
            self.execute()

    
    # run the filter.  This base class is a copy filter. A separate mongo connection
    # is opened and closed during the execution of the filter.  The filter's modified time
    # is updated to allow for pipeline execution behavior.
    
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
        # loop through all inputs and process all objects in the inputs
        for thisInput in self.inputs:
            inputcoll = db[thisInput.collectionName]
            # find all documents in this input (repeated for each input)
            queryResults = inputcoll.find()
            # write the documents into the output collection and indicate the output time changed
            for result in queryResults:
                outputcoll.insert(result)
        # rest the filter's modified time and assign it to the output object    
        self.outputInformation.modifiedTime = self.modifiedTime = time.time()
        connection.close()

                
# This workstep functions as a source that reads a collection and outputs the collection
# data when connected as the source of a pipeline
     
class DatasetSourceWorkstep(Workstep):
    def __init__(self):
        Workstep.__init__(self)
        self.inputType = "none"
        self.outputType = "data.arbor.any"
        self.databaseName = ''
        self.outputCollectionName = ''
        self.outputs = []
     
    def setSourceCollectionName(self,collectionName):
         self.outputCollectionName = collectionName
         
    # utility class to create unique collection names for worksteps within workflows. 
    def getOutputCollectionNameForWorkstep(self):
        if (self.outputCollectionName != ''):
            return self.outputCollectionName
        else:
            raise ValueError
    
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
        self.outputCollectionName = self.getOutputCollectionNameForWorkstep()
        outinfo.collectionName = self.outputCollectionName
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
                
#-------------------------------------------------------------
# Filtering workstep - an attribute can be selected and filtered on for GreaterThan, LessThan, NotEqual
#-------------------------------------------------------------                
class DatasetFilteringWorkstep(DatasetCopyWorkstep):
    def __init__(self):
        DatasetCopyWorkstep.__init__(self)
        self.filterAttribute = ""
        self.limitValue = 0.0
        self.testType = 'LessThan'
        
    # test type is GreaterThan, LessThan, NotEqual
    def setFilterTest(self,typestring):
        self.testType = typestring
        
    # determine which document attribute should be used as a parameter
    def setFilterAttribute(self,attrString):
        self.filterAttribute = attrString

    def setFilterValue(self,number):
        self.limitValue = number
        
   # run the filter.  The filter attribute and filter value are used to build a query for the 
   # source datasets.  Only documents matching the criteria are passed through the filter
    
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
        # loop through all inputs and process all objects in the inputs
        for thisInput in self.inputs:
            inputcoll = db[thisInput.collectionName]
            
            # find all documents in this input (repeated for each input) that match the 
            # test criteria.  If no criteria is specified, pass records through 
            
            for case in switch(self.testType):
                if case('GreaterThan'):
                    query = {self.filterAttribute : {'$gt' : self.limitValue}}
                    break
                if case ('LessThan'):
                    query = {self.filterAttribute : {'$lt' : self.limitValue}}
                    break
                if case ('NotEqual'):
                    query = {self.filterAttribute : {'$ne' : self.limitValue}}
                    break
                if case ('Equal'):
                    query = {self.filterAttribute : self.limitValue}
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