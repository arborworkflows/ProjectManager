# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 23:00:12 2013

@author: clisle
"""
import ArborWorksteps
from ArborWorksteps import switch

import bson.json_util

from GlobalDefinitions import *

class WorkflowManager:
    def __init__(self):
        global algorithms
        self.worksteps = dict()
        self.workflowName = 'default'
        self.databaseName = 'arbor'
        self.projectName = 'workflows'
        self.arbor_workstep_dictionary = dict()
        self.algorithmsDefined = False
        # this workflow manager might be started with algorithms defined, so worksteps involving
        # Arbor algorithms can be executed, if so save the pointer
        if algorithms != None:
            self.algorithmManager = algorithms
            self.algorithmsDefined = True

        # keep a list of all steps where output is used by another step, these are internal
        # nodes and will be executed implicitly
        self.internalSteps = []
        self.initWorkstepLibrary()

    # Setup the list of the worksteps installed in Arbor.  We want to make this
    # dynamic via plug-in techniques later, but this direct declaration will allow us to
    # create a prototype for the PIs to test with

    def initWorkstepLibrary(self):
        # setup the worksteps to run.  This dictionary can be used as a dispatching tool for selecting worksteps
        # dynamically.
        self.arbor_workstep_list = [
            'DatasetSource',
            'DatasetFilter',
            'DatasetCopy',
            'SpecTableSource',
            'FitContinuous'
        ]

    def returnListOfLoadedWorksteps(self):
        # for algorithms, we used a disctionary as a dispatcher, here we are using only a list
        #names = []
        #for key in self.arbor_workstep_list.keys():
        #    names.append(key)
        return self.arbor_workstep_list


    def setDatabaseName(self,dbname):
        self.databaseName = dbname

    def setProjectName(self,projname):
        self.projectName = projname

    def setWorkflowName(self,wfname):
        self.workflowName = wfname

    def testWorkstepExists(self,workstepname):
        # validate that the objects exist
        try:
            temp = self.worksteps[workstepname]
        except:
            return False
        return True

#     # initialize the correct type of worktep, depending on the user's input
    def addWorkstepToWorkflow(self,worksteptype, workstepname):
        print "preparing to add step type of",worksteptype," named ",workstepname
        # add test to see if we already have a workstep by this name
        if workstepname in self.worksteps:
            print "another workstep with the name ",workstepname ,"already exists in this workflow"
            raise TypeError
        else:
            foundMatch = False
            for case in switch(worksteptype):
                if case('DatasetSource') or case('arbor.analysis.datasetsource'):
                    newStep = ArborWorksteps.DatasetSourceWorkstep()
                    newStep.setSourceCollectionName('anolis.CharacterMatrix.anolis_chars')
                    foundMatch = True
                    break
                if case('DatasetFilter') or case('arbor.analysis.datasetfilter'):
                    newStep = ArborWorksteps.DatasetFilteringWorkstep()
                    foundMatch = True
                    break
                if case('DatasetCopy') or case('arbor.analysis.datasetcopy'):
                    newStep = ArborWorksteps.DatasetCopyWorkstep()
                    foundMatch = True
                    break
                if case('SpecTableSource') or case('arbor.analysis.spectablesource'):
                    newStep = ArborWorksteps.DatasetSpecTableSourceWorkstep()
                    foundMatch = True
                    break
                if case('FitContinuous') or case('arbor.analysis.fitcontinuous'):
                    newStep = ArborWorksteps.GeigerFitContinuousWorkstep()
                    foundMatch = True
                    break
            if foundMatch:
                print "creating step ",workstepname
                newStep.setName(workstepname)
                newStep.setDatabaseName(self.databaseName)
                newStep.setProjectName(self.projectName)
                self.worksteps[workstepname] = newStep
                print "there are now",len(self.worksteps.keys()), " steps"

    # initialize the correct type of workstep, depending on the user's input
    def addWorkstepWithParametersToWorkflow(self,worksteptype, workstepname,parameters):
        print "preparing to add step type of",worksteptype," named ",workstepname
        # add test to see if we already have a workstep by this name
        if workstepname in self.worksteps:
            print "another workstep with the name ",workstepname ,"already exists in this workflow"
            raise TypeError
        else:
            foundMatch = False
            for case in switch(worksteptype):
                if case('DatasetSource') or case('arbor.analysis.datasetsource'):
                    newStep = ArborWorksteps.DatasetSourceWorkstep()
                    foundMatch = True
                    break
                if case('DatasetFilter') or case('arbor.analysis.datasetfilter'):
                    newStep = ArborWorksteps.DatasetFilteringWorkstep()
                    foundMatch = True
                    break
                if case('DatasetCopy') or case('arbor.analysis.datasetcopy'):
                    newStep = ArborWorksteps.DatasetCopyWorkstep()
                    foundMatch = True
                    break
                if case('SpecTableSource') or case('arbor.analysis.spectablesource'):
                    newStep = ArborWorksteps.DatasetSpecTableSourceWorkstep()
                    foundMatch = True
                    break
                if case('FitContinuous') or case('arbor.analysis.geigerfitcontinuous'):
                    newStep = ArborWorksteps.GeigerFitContinuousWorkstep()
                    foundMatch = True
                    break
            if foundMatch:
                print "creating step ",workstepname
                newStep.setName(workstepname)
                newStep.setDatabaseName(self.databaseName)
                newStep.setProjectName(self.projectName)
                newStep.setParameters(parameters)
                self.worksteps[workstepname] = newStep
                print "there are now",len(self.worksteps.keys()), " steps"
                newStep.printSelf()


    # set a parameter in a workstep.  This violates information hiding at the workstep level,
    #  but avoids the need for parameter setting machinery for now..
    def setWorkstepParameter(self,workstepname,parametername, value):
        if self.testWorkstepExists(workstepname):
            setattr(self.worksteps[workstepname],parametername,value)
            return True
        else:
            return False

    # return the parameters of a currently loaded workstep, so they can be displayed or browsed through an interface
    def returnWorkstepParameters(self,stepName):
        return self.worksteps[stepName].parameters

    # connect an output of one step to the input of another.  The datatype is used
    # to determine the correct output/input combinations to connect
    def connectStepsInWorkflow(self,sourceStepName,destStepName,datatype):
        # validate that the objects exist
        if not self.testWorkstepExists(sourceStepName):
            print "workflow mgr: source workstep not found in workflow:",sourceStepName
        if not self.testWorkstepExists(destStepName):
            print "workflow mgr: destination workstep not found in workflow: ",destStepName
        # connect them together.  This is initially simplified because we are only dealing with single
        # input and single output filters currently.  This can be expanded later if this approach proves to be worthwhile
        # Type checking is done at the workstep level, catch error here if a type mismatch has occurred.
        try:
            source = self.worksteps[sourceStepName]
            dest = self.worksteps[destStepName]
            dest.addInput(source.getOutput())
            # record the source in the internal step list
            self.internalSteps.append(sourceStepName)
        except TypeError:
            print "workflow mgr: type mismatch between filters ",sourceStepName, " and ", destStepName

    def executeWorkflow(self,algorithms=None):
        # look through the worksteps and fire off all the ones that are not in the internal step
        # list.  This will assure that all steps are executed without unnecessary repeat execution
        # of the internal steps.
        for step in self.worksteps:
            if not (step in self.internalSteps):
                print "workflow mgr: executing step:",step

                # some worksteps might use Arbor algorithms, so we need to pass a reference
                # to the instantiated algorithms to the worksteps so algorithms can be executed

                if algorithms != None:
                    self.worksteps[step].update(algorithms)
                else:
                    self.worksteps[step].update()

    def printWorkflow(self):
        for step in self.worksteps:
            self.worksteps[step].printSelf()

    def cleanupInternalSteps(self):
        # for all internal steps in this workflow,  drop the output collections to clean
        # out any intermediate results
        for stepname in self.internalSteps:
            print "deleting output of step:",stepname
            thisStep = self.worksteps[stepname]
            thisStep.deleteOutput()

    def cleanupAllSteps(self):
        # for all steps in workflow, delete output
        for stepname in self.worksteps:
            print "deleting output of step:",stepname
            thisStep = self.worksteps[stepname]
            thisStep.deleteOutput()

    def loadFrom(self,wfRecord):
        print "workflowmgr: loadFrom begin on record:",bson.json_util.dumps(wfRecord)
        if wfRecord['name']:
            self.workflowName = wfRecord['name']
        for step in wfRecord["analyses"]:
            print "found analysis:", step["name"]
            self.addWorkstepWithParametersToWorkflow(step["type"], step["name"], step['parameters'])

        for connection in wfRecord["connections"]:
            print "found connection"
            self.connectStepsInWorkflow(connection['output'], connection['input'], 'arbor.any')
        print "workflowmgr: loadFrom complete"
        print "there are now",len(self.worksteps.keys()), " steps"

    # serialize the list of steps in this workflow along with the connection information.  Connectivity is hard
    # to discover because it is represented implicitly through the addInput(getOutput()) assignments, so we have to
    # peek into the 'inputs' field of each analysis and decide if there are any records there to stream out.

    def serialize(self):
        serializedict = dict()
        serializedict['analyses']= []
        serializedict['connections'] = []
        serializedict['name']= self.workflowName
        print 'serializing ',len(self.worksteps), ' steps'
        connectionlist = []
        for key in self.worksteps.keys():
            step = self.worksteps[key]
            stepattribs = dict()
            stepattribs['name']=getattr(step,'name')
            stepattribs['type']=getattr(step,'type')

            # workstep specific parameters handled here for now.  This will be handled better when parsing
            # is driven by the analysis spec
            stepattribs['parameters']=getattr(step,'parameters')

            # if there is an input dataset feeding this workstep, record the connection:
            # if this is a source object, it doesn't have an input field, so skip  looking for an input
            if (getattr(step,'type') == "DatasetSource") or (getattr(step,"type") == 'arbor.analysis.datasetsource'):
                pass
            elif (len(getattr(step,'inputs')) > 0):
                # this step has an input so find it and record the connection
                for inputStep in getattr(step,'inputs'):
                    thisConnect = dict()
                    # return the name of the object referenced by the information object
                    thisConnect['output'] = getattr(getattr(inputStep,'sourceObject'),'name')
                    thisConnect['input'] = getattr(step,'name')
                    connectionlist.append(thisConnect)
            print stepattribs
            serializedict['analyses'].append(stepattribs)
        # only output an entry if there is a connection and traverse the list so each connection is in a flat
        # list stored at the workflow level.
        if (connectionlist) and (len(connectionlist) > 0):
            for connection in connectionlist:
                serializedict['connections'].append(connection)
        return serializedict

    # add or update the value of a parameter attached to a workstep in this workflow.
    # if there is no corresponding attribute, then it will be added.  If the parameter is
    # already present, its value will be updated.
    def updateParameterOfWorkstep(self,stepName,parameterName,parameterValue):
        thisStep = self.worksteps[stepName]
        #setattr(thisStep,parameterName,parameterValue)
        thisStep.setParameter(parameterName,parameterValue)

    # --------
    # Several workflows are hand constructed in the methods below to serve as tests
    # --------

    # single linear flow through two copy filters
    def buildworkflow1(self):
        source1 = ArborWorksteps.DatasetSourceWorkstep()
        source1.setName('source1')
        source1.setDatabaseName('arbor')
        source1.setSourceCollectionName('analyses')
        ws1 = ArborWorksteps.DatasetCopyWorkstep()
        ws1.setName('firststep')
        ws1.addInput(source1.getOutput())
        ws1.setDatabaseName('arbor')
        ws1.setProjectName('anolis')
        ws2 = ArborWorksteps.DatasetCopyWorkstep()
        ws2.setName('secondStep')
        ws2.setProjectName('anolis')
        ws2.setDatabaseName('arbor')
        ws2.addInput(ws1.getOutput())
        ws2.update()
        ws1.printSelf()
        ws2.printSelf()

    # repeat test1 using the workflow manager api
    def buildworkflow1api(self):
        self.setDatabaseName('arbor')
        self.addWorkstepToWorkflow('DatasetSource','source1')
        self.setWorkstepParameter('source1','outputCollectionName','analyses')
        self.addWorkstepToWorkflow('DatasetCopy','firststep_api')
        self.addWorkstepToWorkflow('DatasetCopy','secondstep_api')
        self.connectStepsInWorkflow('source1','firststep_api','arbor.table')
        self.connectStepsInWorkflow('firststep_api','secondstep_api','arbor.table')
        self.printWorkflow()
        self.executeWorkflow()
        self.printWorkflow()


    # source feeeding a copy filter and a selection (awesomness > 0)
    def buildworkflow2(self):
        source1 = ArborWorksteps.DatasetSourceWorkstep()
        source1.setName('source1')
        source1.setDatabaseName('xdata')
        source1.setSourceCollectionName('anolis_chars')
        ws1 = ArborWorksteps.DatasetCopyWorkstep()
        ws1.setName('firststep')
        ws1.addInput(source1.getOutput())
        ws1.setDatabaseName('xdata')
        ws1.setProjectName('anolis')
        ws2 = ArborWorksteps.DatasetFilteringWorkstep()
        ws2.setName('awesomeGTzero')
        ws2.setProjectName('anolis')
        ws2.setDatabaseName('xdata')
        ws2.setFilterAttribute('awesomeness')
        ws2.setFilterTest('GreaterThan')
        ws2.setFilterValue(0.0)
        ws2.addInput(ws1.getOutput())
        ws2.update()
        ws1.printSelf()
        ws2.printSelf()

    # interesection of two filters to pass only  0 < awesomness < 0.4
    def buildworkflow3(self):
        source1 = ArborWorksteps.DatasetSourceWorkstep()
        source1.setName('source1')
        source1.setDatabaseName('xdata')
        source1.setSourceCollectionName('anolis_chars')

        ws2 = ArborWorksteps.DatasetFilteringWorkstep()
        ws2.setName('awesomeGTzero')
        ws2.setProjectName('anolis')
        ws2.setDatabaseName('xdata')
        ws2.setFilterAttribute('awesomeness')
        ws2.setFilterTest('GreaterThan')
        ws2.setFilterValue(0.0)
        ws2.addInput(source1.getOutput())

        ws3 = ArborWorksteps.DatasetFilteringWorkstep()
        ws3.setName('awesomeLTfour')
        ws3.setProjectName('anolis')
        ws3.setDatabaseName('xdata')
        ws3.setFilterAttribute('awesomeness')
        ws3.setFilterTest('LessThan')
        ws3.setFilterValue(0.4)
        ws3.addInput(ws2.getOutput())
        ws3.update()

        ws1 = ArborWorksteps.DatasetCopyWorkstep()
        ws1.setName('firststep')
        ws1.addInput(source1.getOutput())
        ws1.setDatabaseName('xdata')
        ws1.setProjectName('anolis')

        ws2.printSelf()
        ws3.printSelf()

    # union operation
    def buildworkflow4(self):
        source1 = ArborWorksteps.DatasetSourceWorkstep()
        source1.setName('source1')
        source1.setDatabaseName('xdata')
        source1.setSourceCollectionName('anolis_chars')

        ws2 = ArborWorksteps.DatasetFilteringWorkstep()
        ws2.setName('awesomeGTone')
        ws2.setProjectName('anolis')
        ws2.setDatabaseName('xdata')
        ws2.setFilterAttribute('awesomeness')
        ws2.setFilterTest('GreaterThan')
        ws2.setFilterValue(1.5)
        ws2.addInput(source1.getOutput())

        ws3 = ArborWorksteps.DatasetFilteringWorkstep()
        ws3.setName('awesomeLTfour')
        ws3.setProjectName('anolis')
        ws3.setDatabaseName('xdata')
        ws3.setFilterAttribute('awesomeness')
        ws3.setFilterTest('LessThan')
        ws3.setFilterValue(-0.4)
        ws3.addInput(source1.getOutput())
        # partial pipeline execution to see if it works
        #ws3.update()

        ws1 = ArborWorksteps.DatasetCopyWorkstep()
        ws1.setName('union')
        ws1.addInput(ws2.getOutput())
        ws1.addInput(ws3.getOutput())
        ws1.setDatabaseName('xdata')
        ws1.setProjectName('anolis')
        #ws1.update()

        ws4 = ArborWorksteps.DatasetFilteringWorkstep()
        ws4.setName('notCuba')
        ws4.setProjectName('anolis')
        ws4.setDatabaseName('xdata')
        ws4.setFilterAttribute('island')
        ws4.setFilterTest('NotEqual')
        ws4.setFilterValue('Cuba')
        ws4.addInput(ws1.getOutput())
        #ws4.update()

        ws5 = ArborWorksteps.DatasetFilteringWorkstep()
        ws5.setName('notHispaniolaOrCuba')
        ws5.setProjectName('anolis')
        ws5.setDatabaseName('xdata')
        ws5.setFilterAttribute('island')
        ws5.setFilterTest('NotEqual')
        ws5.setFilterValue('Hispaniola')
        ws5.addInput(ws4.getOutput())
        #ws5.update()

        ws6 = ArborWorksteps.DatasetFilteringWorkstep()
        ws6.setName('occultus')
        ws6.setProjectName('anolis')
        ws6.setDatabaseName('xdata')
        ws6.setFilterAttribute('species')
        ws6.setFilterTest('Equal')
        ws6.setFilterValue('occultus')
        ws6.addInput(ws5.getOutput())
        ws6.update()

        ws2.printSelf()
        ws3.printSelf()
        ws1.printSelf()
        ws4.printSelf()
        ws5.printSelf()
        ws6.printSelf()

    # repeat test1 using the workflow manager api.   This isn't exactly the same as workflow 4.
    # one filter (notHispaniolaOrCuba) is not present here, because it isn't needed to show the
    # API approach is working

    def buildworkflow4api(self):
        self.setDatabaseName('xdata')
        self.addWorkstepToWorkflow('DatasetSource','source1')
        self.setWorkstepParameter('source1','outputCollectionName','anolis_chars')

        self.addWorkstepToWorkflow('DatasetFilter','awesomeGT_api')
        self.setWorkstepParameter('awesomeGT_api','filterAttribute','awesomeness')
        self.setWorkstepParameter('awesomeGT_api','limitValue',1.9)
        self.setWorkstepParameter('awesomeGT_api','testType','GreaterThan')
        self.connectStepsInWorkflow('source1','awesomeGT_api','arbor.table')

        self.addWorkstepToWorkflow('DatasetFilter','awesomeLT_api')
        self.setWorkstepParameter('awesomeLT_api','filterAttribute','awesomeness')
        self.setWorkstepParameter('awesomeLT_api','limitValue',-0.7)
        self.setWorkstepParameter('awesomeLT_api','testType','LessThan')
        self.connectStepsInWorkflow('source1','awesomeLT_api','arbor.table')

        self.addWorkstepToWorkflow('DatasetCopy','union_api')
        self.connectStepsInWorkflow('awesomeGT_api','union_api','arbor.table')
        self.connectStepsInWorkflow('awesomeLT_api','union_api','arbor.table')

        self.addWorkstepToWorkflow('DatasetFilter','notCuba_api')
        self.setWorkstepParameter('notCuba_api','filterAttribute','island')
        self.setWorkstepParameter('notCuba_api','limitValue','Cuba')
        self.setWorkstepParameter('notCuba_api','testType','NotEqual')
        self.connectStepsInWorkflow('union_api','notCuba_api','arbor.table')

        self.addWorkstepToWorkflow('DatasetFilter','occultus_api')
        self.setWorkstepParameter('occultus_api','filterAttribute','species')
        self.setWorkstepParameter('occultus_api','limitValue','occultus')
        self.setWorkstepParameter('occultus_api','testType','Equal')
        self.connectStepsInWorkflow('notCuba_api','occultus_api','arbor.table')

        self.executeWorkflow()
        self.printWorkflow()

