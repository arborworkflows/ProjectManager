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
    allowed = ["project", "analysis"]
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
    else:
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: %s" % (resource_type, ", ".join(allowed)))

@tangelo.restful
def put(resource, projname, datasetname=None, data=None, objname=None, objtype=None, **kwargs):
    if (resource != "project") and (resource != "workflow"):
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")
    if resource == "project":
        if datasetname is None:
            api.newProject(projname)
        else:
            if objname is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'objname'")

            if objtype is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'objtype'")

            if data is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'data'")

            if datasetname is None:
                return tangelo.HTTPStatusCode(400, "Missing argument 'datasetname'")

            # user wants to upload a tree or a character matrix
            if objtype == "newick" or objtype == "phyloxml":
                api.newTreeInProjectFromString(datasetname, data, projname, objname, objtype)
            if objtype == "csv":
                api.newCharacterMatrixInProjectFromString(datasetname, data, projname, objname)

    # workflow creation
    #  arborapi: /workflow/projname/workflowname - creates new empty workflow
    #  arborapi: /workflow/projname/workflowname//
    if resource == "workflow":
            # the user wants to create a new, empty workflow
            if (data is None) and (objtype is None) and (objname is None):
                api.newWorkflowInProject(datasetname, projname)
            else:
                if (data == "workstep"):
                    api.newWorkstepInWorkflow(datasetname, objtype, objname, projname)

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
