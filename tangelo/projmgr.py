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
        if len(pargs) > 1:
            project = pargs[1]
            q = query_args.get("q")
            allowed_q = ["types"]
            if q == "types":
                return api.getListOfTypesForProject(project)
            else:
                return tangelo.HTTPStatusCode(400, "Missing or bad q parameter.  Allowed options are: %s" % (", ".join(allowed_q)))
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
