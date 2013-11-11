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
    allowed = ["project"]
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
            return api.getDatasetAsTextString(project, datatype, dataset, stringFormat)
        else:
            return tangelo.HTTPStatusCode(400, "Bad request - got %d parameter(s), was expecting between 1 and 5")
    else:
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: %s" % (resource_type, ", ".join(allowed)))

@tangelo.restful
def put(resource, projname, datasetname=None, data=None, filename=None, filetype=None, **kwargs):
    if resource != "project":
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")

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

        api.newTreeInProjectFromString(datasetname, data, projname, filename, filetype)

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
