import tangelo
import pymongo
import bson.json_util

from ArborFileManagerAPI import ArborFileManager
api = ArborFileManager()
api.initDatabaseConnection()

@tangelo.restful
def get(*pargs, **query_args):
    if len(pargs) == 0:
        return tangelo.HTTPStatusCode(400, "Missing resource type")

    resource_type = pargs[0]
    allowed = ["project", "analysis","collection", "workflow"]
    if resource_type == "project":
        if len(pargs) == 1:
            return api.getListOfProjectNames()
        elif len(pargs) == 2:
            project = pargs[1]
            return api.getListOfTypesForProject(project)
        elif len(pargs) == 3:
            project = pargs[1]
            datatype = pargs[2]
            return api.getListOfDatasetsByProjectAndType(project, datatype)
        elif len(pargs) == 4:
            project = pargs[1]
            datatype = pargs[2]
            dataset = pargs[3]
            coll = api.db[api.returnCollectionForObjectByName(project, datatype, dataset)]
            return bson.json_util.dumps(list(coll.find()))
        elif len(pargs) == 5:
            project = pargs[1]
            datatype = pargs[2]
            dataset = pargs[3]
            stringFormat = pargs[4]
            string =  api.getDatasetAsTextString(project, datatype, dataset, stringFormat)
            return string
        else:
            return tangelo.HTTPStatusCode(400, "Bad request - got %d parameter(s), was expecting between 1 and 5")
    elif resource_type == "analysis":
        if len(pargs) == 1:
            return api.getListOfAnalysisNames()
        elif len(pargs) == 2:
            analysis_name = pargs[1]
            coll = api.db[api.returnCollectionForAnalysisByName(analysis_name)]
            return bson.json_util.dumps(list(coll.find()))
        elif len(pargs) == 3:
            analysis_name = pargs[1]
            coll = api.db[api.returnCollectionForAnalysisByName(analysis_name)]
            return coll.find_one()["analysis"]["script"]

    # add a collection option to return the database and collection name for an object in the
    # Arbor treestore.  This 'information hiding violation' of the treestore allows for low-level
    # clients to connect and work directly with the mongo database, should it be needed.  This level
    # is used in the phylomap application.
    elif resource_type == "collection":
        if len(pargs) == 4:
            project = pargs[1]
            datatype = pargs[2]
            dataset = pargs[3]
            collname = api.returnCollectionForObjectByName(project, datatype, dataset)
            dbname = api.getMongoDatabase()
            dbhost = api.getMongoHost()
            dbport = api.getMongoPort()
            return bson.json_util.dumps({'host':dbhost,'port':dbport,'db': dbname,'collection': collname})

    # if workflow is specified as the resource type, then list the workflows in a project or display the
    # information about a particular workflow
    elif resource_type == "workflow":
        if len(pargs) == 2:
            project = pargs[1]
            return api.getListOfDatasetsByProjectAndType(project,"Workflow")
        if len(pargs) == 3:
            project = pargs[1]
            workflowName = pargs[2]
            print("REST: getting status of workflow:",workflowName)
            return bson.json_util.dumps(api.getStatusOfWorkflow(workflowName,project))
        else:
            return tangelo.HTTPStatusCode(400, "Workflow resource requires 2 or 3 positional arguments")
    else:
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: %s" % (resource_type, ", ".join(allowed)))

# Jan 2014 - added support for workflows as a datatype inside projects.  new workflow-only named types are
# defined here to allow workflows to be created and run through the REST interface
#

@tangelo.restful
def put(resource, projname, datasetname=None, data=None, filename=None, filetype=None,
            workflowName = None, stepName=None, stepType=None, inputStepName=None, outputStepName=None,
            inPortName=None,outPortName=None,operation=None, parameterName=None, parameterValue=None,
            parameterValueNumber=None,flowType=None,dataType=None, **kwargs):
    if (resource != "project") and (resource != "workflow"):
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")
    if resource == "project":
        if datasetname is None:
            api.newProject(projname)
        else:
            if filename is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'filename'")

            if filetype is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'filetype'")

            if data is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'data'")

            if datasetname is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'datasetname'")

            # user wants to upload a tree or a character matrix
            if filetype == "newick" or filetype == "phyloxml":
                api.newTreeInProjectFromString(datasetname, data, projname, filename, filetype)
            if (filetype == "csv" and dataType is None) or (filetype == "csv" and dataType=='CharacterMatrix'):
                api.newCharacterMatrixInProjectFromString(datasetname, data, projname, filename)
            if filetype == "csv" and dataType=="Occurrences":
                api.newOccurrencesInProjectFromString(datasetname, data, projname)

    # workflow creation
    #  arborapi: /workflow/projname/workflowname - creates new empty workflow
    #  arborapi: /workflow/projname/workflowname//
    if resource == "workflow":
            # the user wants to create a new, empty workflow
            if operation == "newWorkflow":
                api.newWorkflowInProject(workflowName, projname)
            if operation == "newWorkstepInWorkflow":
                    api.newWorkstepInWorkflow(workflowName, stepType, stepName, projname)

            # allow user to add a parameter to a workstep or update the value of the parameter. There
            # is currently a limitation that all values are strings, e.g. "2.4" instead of 2.4.
            if operation == "updateWorkstepParameter":
                # if a float argument is sent, use this as the value for the parameter, instead of the
                # string.  A conversion is done to float to assure numberic values
                if parameterValueNumber != None:
                    print "found number filter value"
                    parameterValue = float(parameterValueNumber)
                api.updateWorkstepParameter(workflowName, stepName, parameterName, parameterValue, projname)
            if operation == "connectWorksteps":
                #api.connectStepsInWorkflow(workflowName,outStepName,outPortName,inStepName,inPortName,projname)
                api.connectStepsInWorkflow(workflowName,outputStepName,inputStepName,projname)
            if operation == "executeWorkflow":
                api.executeWorkflowInProject(workflowName,projname)
            if operation == "updateWorkflowFromString":
                print "received request to update workflow: ",workflowName
                api.updateExistingWorkflowInProject(workflowName,data,projname)
    return "OK"

@tangelo.restful
def post(*pargs, **kwargs):
    return "projmgr.post()"

@tangelo.restful
def delete(resource, projname, datatype=None, dataset=None):
    if resource != "project":
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")

    # (This is expressing xor)
    if (datatype is None) != (dataset is None):
        return tangelo.HTTPStatusCode(400, "Bad arguments - 'datatype' and 'dataset' must both be specified if either one is specified")

    if datatype is None:
        api.deleteProjectNamed(projname)
    else:
        api.deleteDataset(projname, datatype, dataset)

    return "OK"
