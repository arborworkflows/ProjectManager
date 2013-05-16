import tangelo

@tangelo.restful
def get(*pargs, **kwargs):
    return "projmgr.get()"

@tangelo.restful
def put(*pargs, **kwargs):
    return "projmgr.put()"

@tangelo.restful
def post(*pargs, **kwargs):
    return "projmgr.post()"

@tangelo.restful
def delete(*pargs, **kwargs):
    return "projmgr.delete()"
