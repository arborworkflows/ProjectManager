# -*- coding: utf-8 -*-

import pymongo
from pymongo import Connection
from bson import ObjectId
import json
from json import JSONEncoder


# used to print out Mongo ObjectId's in json.dumps (SZ)
class MongoEncoder(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:            
            return JSONEncoder.default(obj, **kwargs)
            

# returns [phylo_tree, leftmost_child, rightmost_child]
def recursiveHelper(node,data_coll):
    results = data_coll.find({'_id':node})
    phylo = results[0]
    if 'clades' in phylo:
	childlist = phylo['clades']
	print "child nodes are: ",childlist
	    
	if len(childlist) == 1:
	    subtree_info = recursiveHelper(childlist[0],data_coll)
	    phylo['clades'][0] = subtree_info[0]
            # fixed errors if only one child (SZ)
            if len(subtree_info) > 2:
		newName = subtree_info[1] + ":" + subtree_info[2]
            else:
                newName = subtree_info[1]
			
	    phylo['name'] = newName;
	    data_coll.update({'_id': node},{'$set': {'name': newName}})
	    del phylo['_id']
            # see above (SZ)
            if len(subtree_info) > 2:
                return [phylo, subtree_info[1], subtree_info[2]]
            else:
                return [phylo, subtree_info[1]]
	
	# assumption: exactly two children
	left_subtree_info = recursiveHelper(childlist[0],data_coll)
	phylo['clades'][0] = left_subtree_info[0]
	right_subtree_info = recursiveHelper(childlist[1],data_coll)
	phylo['clades'][1] = right_subtree_info[0]
	# do we need to consider other children? Can expand to expect more.
	
	if len(left_subtree_info) == 2:
	    leftmost_child = left_subtree_info[1]
	else:
	    leftmost_child = left_subtree_info[1]
	if len(right_subtree_info) == 2:
	    rightmost_child = right_subtree_info[1]
	else:
	    rightmost_child = right_subtree_info[2]
	newName = leftmost_child + ':' + rightmost_child
	phylo['name'] = newName;
	data_coll.update({'_id': node},{'$set': {'name': newName}})
	print 'updating stuff'
	del phylo['_id']
	return [phylo, leftmost_child, rightmost_child]
    
    # leaf, so set scientific name as display name.
    leaf_name = phylo['name']
    phylo['name'] = leaf_name;
    data_coll.update({'_id': node},{'$set': {'display_name': leaf_name}})
    del phylo['_id']
    return [phylo, leaf_name]


def AssignHierarchicalNames(data_coll):
    search_dict = dict()
    search_dict['rooted'] = True
    results = data_coll.find(search_dict)

    # lets make a new tree from it
    if results.count() == 1:
        phylo = results[0]
        nodeid = phylo['_id']
        newTreeInfo = recursiveHelper(phylo['_id'],data_coll)
        phylotree = newTreeInfo[0]
        #print json.dumps(phylotree, cls=MongoEncoder, sort_keys=True, indent=2)
    else:
        print 'your search returned more than one object ', results.count()

def AssignHierarchicalNamesSeparateConnection(system,database,port,tree_collection_name,verbose):
   
    connection = Connection(system, port)
    db = connection[database]    
    data_coll = db[str(tree_collection_name)]
    AssignHierarchicalNames(data_coll)
    if (connection):
        connection.close()