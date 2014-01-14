# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 23:00:12 2013

@author: clisle
"""
import ArborWorksteps
from ArborWorksteps import switch

class WorkflowManager:
    def __init__(self):
        self.worksteps = dict()
        self.databaseName = 'arbor'
        self.projectName = 'workflows'
        # keep a list of all steps where output is used by another step, these are internal
        # nodes and will be executed implicitly
        self.internalSteps = []
    
    def setDatabaseName(self,dbname):
        self.databaseName = dbname

    def setProjectName(self,projname):
        self.projectName = projname
        
    def testWorkstepExists(self,workstepname):
        # validate that the objects exist
        try:
            temp = self.worksteps[workstepname]
        except:
            return False
        return True           

    # initialize the correct type of worktep, depending on the user's input  
    def addWorkstepToWorkflow(self,worksteptype, workstepname):
        foundMatch = False
        for case in switch(worksteptype):
                if case('DatasetSource'):
                    newStep = ArborWorksteps.DatasetSourceWorkstep()
                    foundMatch = True
                    break
                if case('DatasetFilter'):
                    newStep = ArborWorksteps.DatasetFilteringWorkstep()
                    foundMatch = True
                    break        
                if case('DatasetCopy'):
                    newStep = ArborWorksteps.DatasetCopyWorkstep()
                    foundMatch = True
                    break
        if foundMatch:
            print "creating step ",workstepname
            newStep.setName(workstepname) 
            newStep.setDatabaseName(self.databaseName) 
            newStep.setProjectName(self.projectName)              
            self.worksteps[workstepname] = newStep

    # set a parameter in a workstep.  This violates information hiding at the workstep level,
    #  but avoids the need for parameter setting machinery for now..
    def setWorkstepParameter(self,workstepname,parametername, value):
        if self.testWorkstepExists(workstepname):
            setattr(self.worksteps[workstepname],parametername,value)
            return True
        else:
            return False
        

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

    def executeWorkflow(self):
        # look through the worksteps and fire off all the ones that are not in the internal step
        # list.  This will assure that all steps are executed without unnecessary repeat execution
        # of the internal steps.
        for step in self.worksteps:
            if not (step in self.internalSteps):
                print "workflow mgr: executing step:",step
                self.worksteps[step].update()

    def printWorkflow(self):
        for step in self.worksteps:
            self.worksteps[step].printSelf()


    def cleanupOutput():
        # for all steps in workflow, query the output collection and drop it to clean
        # out any intermediate results
        pass
    
    def loadFrom(self,instancename, projectTitle):
        print "workflowmgr: loadFrom not implemented"
        pass

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
  
