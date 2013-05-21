import tangelo

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
        else:
            return tangelo.HTTPStatusCode(400, "Bad request - got %d parameter(s), was expecting between 1 and 3")
    else:
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: %s" % (resource_type, ", ".join(allowed)))

@tangelo.restful
def put(resource, projname, **kwargs):
    if resource != "project":
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")

    api.newProject(projname)
    return "OK"

@tangelo.restful
def post(*pargs, **kwargs):
    return "projmgr.post()"

@tangelo.restful
def delete(resource, projname, datatype=None, dataset=None):
    if resource != "project":
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: project")

    if datatype is None and dataset is not None:
        return tangelo.HTTPStatusCode(400, "Bad arguments - you cannot specify a dataset without a datatype")

    if datatype is None:
        api.deleteProjectNamed(projname)
    else:
        api.deleteDataset(projname, datatype, dataset)

    return "OK"
