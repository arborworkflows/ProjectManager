import tangelo

from ArborFileManagerAPI import ArborFileManager
api = ArborFileManager()
api.initDatabaseConnection()

@tangelo.restful
def get(*pargs):
    if len(pargs) == 0:
        return tangelo.HTTPStatusCode(400, "Missing resource type")

    resource_type = pargs[0]
    allowed = ["project"]
    if resource_type == "project":
        if len(pargs) > 1:
            return tangelo.HTTPStatusCode(500, "Unimplemented - sorry!")
        else:
            return api.getListOfProjectNames()
    else:
        return tangelo.HTTPStatusCode(400, "Bad resource type '%s' - allowed types are: %s" % (resource_type, ", ".join(allowed)))

@tangelo.restful
def put(*pargs, **kwargs):
    return "projmgr.put()"

@tangelo.restful
def post(*pargs, **kwargs):
    return "projmgr.post()"

@tangelo.restful
def delete(*pargs, **kwargs):
    return "projmgr.delete()"
