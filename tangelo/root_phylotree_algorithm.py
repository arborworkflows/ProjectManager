# Roots a tree in a MongoDB collection by querying, for each node document n, whether there exists a
# document d such that n appears in the clades/children of d. To increase the verbosity of the output,
# use the --verbose argument when running this script.
#
# author: Anthony Wehrer


import pymongo
from bson import ObjectId
from pymongo import Connection
import json
import random
import time

# this helper routine is used in a legacy fashion by the OpenTree import demonstration. It is also used as a primitive
# in algorithms below for tree management in Arbor's Alogorithms API

def addRootToTree(data_coll,verbose=False):

    print "Legacy use of addRootToTree. Please replace with separate Arbor Treestore connection"     
    start_time = time.time()
    results = data_coll.find()
    documentCount = results.count()
    newRootID = None
    
    if verbose:
        print str(documentCount) + ' documents to be checked (at most)...0% searched'
    
    # for each node document in the collection
    for i in range(documentCount):
        nodeDoc = results[i]
        nodeID = nodeDoc['_id']
        parent = data_coll.find({'clades': nodeID}).limit(1) # search for a parent of this node document
        try: # try-except faster than using count
            parent[0]
        except IndexError: # if we reach here, that means this document has not parents and thus qualifies as a root
            if verbose:
                print '--> Root-able at document with Object ID ' + str(nodeID) + ', ' + str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
            newRootID = nodeID # record the new root
            break
        # progress indication (enabled if verbose option used)
        if verbose and (((i + 1) % 5000) == 0 or (i + 1) == documentCount):
            print str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
    
    # We ought to have found a root. Otherwise, this is not a tree.
    if newRootID is None:
        raise Exception('Error: No root to be found. The collection ' + data_coll + ' does not contain a tree structure.')
    else:
        data_coll.update({'_id': newRootID}, {'$set': {'rooted': True}})
        end_time = time.time()
        if verbose:
            print 'Tree is now rooted. Procedure took ' + str(end_time - start_time) + ' seconds to complete'


# this utility is used in the copy subtree function below.  This helper function duplicates the 
# structure of a tree in collection 'existing_coll'. 

def recursiveCopyHelper(child,existing_coll,new_coll):
    results = existing_coll.find({'_id':ObjectId(str(child))})
    phylo = results[0]
    new_coll.insert(phylo)
    # if there are any children, continue recursing
    if 'clades' in phylo:
        for child in phylo['clades']:
            childquery = {'_id':ObjectId(str(child))}
            childresults = existing_coll.find(childquery)
            #print "childquery: ",childquery, "results: ",childresults[0]
            if childresults.count() ==1:
                new_coll.insert(childresults[0])
                newchild_id = new_coll.find(childresults[0])[0]['_id']
                new_coll.update(phylo,{'$addToSet' : {'clades': newchild_id}})
                recursiveCopyHelper(child,existing_coll,new_coll)
            else:
                print" recursiveCopy: error finding child in existing tree: ",childquery
    else:
        # this is a leaf node, insert it and terminate the recursion
        phylo['_id'] = str(phylo['_id'])
        #new_coll.insert(phylo)
        del phylo


# Assuming a connection is open, start at a given node ID and copy recursively from this node
# into a new collection.   All new nodes are created, so this is a deep copy of an existing
# tree stored in the existing collection, "existing_coll" into the new collection "new_coll" 

def copySubtreeFromStartingNodeToNewCollection(existing_coll,rootnode,new_coll):
    rootnodequery = {'_id': ObjectId(str(rootnode))}
    print "copySubtree: rootnode = ",rootnode," query= ",rootnodequery
    results = existing_coll.find(rootnodequery)
    if results.count() == 1:
        phylo = results[0]
        #print "phylo=",phylo
        phylotree = recursiveCopyHelper(phylo['_id'],existing_coll,new_coll)
    else:
        print 'Search returned more zere or more than one object. Number of objects: ', results.count()


# utility routine.  Assuming a connection is open, search a tree collection for what would be the root and return the id

def returnRootNodeInTree(data_collection,verbose=False):
    results = data_collection.find()
    documentCount = results.count()
    newRootID = None
    
    if verbose:
        print str(documentCount) + ' documents to be checked (at most)...0% searched'
    
    # for each node document in the collection
    for i in range(documentCount):
        nodeDoc = results[i]
        nodeID = nodeDoc['_id']
        parent = data_collection.find({'clades': nodeID}).limit(1) # search for a parent of this node document
        try: # try-except faster than using count
            parent[0]
        except IndexError: # if we reach here, that means this document has not parents and thus qualifies as a root
            if verbose:
                print '--> Root-able at document with Object ID ' + str(nodeID) + ', ' + str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
            newRootID = nodeID # record the new root
            break
        # progress indication (enabled if verbose option used)
        if verbose and (((i + 1) % 5000) == 0 or (i + 1) == documentCount):
            print str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
    
    # We ought to have found a root. Otherwise, this is not a tree.
    if newRootID is None:
        raise Exception('Error: No root to be found. The collection ' + data_coll + ' does not contain a tree structure.')
    else:
        return newRootID
            
  
# ----- Arbor Algorithm ----       
# root a tree in-place in the Arbor Treestore by looking for the node which doesn't have a parent. This doesn't allow arbitrary
# rooting, which is sometimes needed biologically. It is used to enable the phylotree app to properly browse tree datasets.
            
def addRootToTreeInPlaceSeparateConnection(system,database,port,data_collection_string,verbose=False):

    start_time = time.time()
    connection = Connection(system, port)
    db = connection[database]    
    
    # st() necessary to convert from QString to string type
    data_coll = db[str(data_collection_string)]
    print 'coll name is: ',data_collection_string
    print data_coll.find()
    results = data_coll.find()
    documentCount = results.count()
    newRootID = None
    
    if verbose:
        print str(documentCount) + ' documents to be checked (at most)...0% searched'
    
    # for each node document in the collection
    for i in range(documentCount):
        nodeDoc = results[i]
        nodeID = nodeDoc['_id']
        parent = data_coll.find({'clades': nodeID}).limit(1) # search for a parent of this node document
        try: # try-except faster than using count
            parent[0]
        except IndexError: # if we reach here, that means this document has not parents and thus qualifies as a root
            if verbose:
                print '--> Root-able at document with Object ID ' + str(nodeID) + ', ' + str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
            newRootID = nodeID # record the new root
            break
        # progress indication (enabled if verbose option used)
        if verbose and (((i + 1) % 5000) == 0 or (i + 1) == documentCount):
            print str(i + 1) + '/' + str(documentCount) + ' documents checked...'+ str(int(((i + 1) / float(documentCount)) * 100)) + '% searched'
    
    # We ought to have found a root. Otherwise, this is not a tree.
    if newRootID is None:
        raise Exception('Error: No root to be found. The collection ' + data_coll + ' does not contain a tree structure.')
    else:
        data_coll.update({'_id': newRootID}, {'$set': {'rooted': True}})
        end_time = time.time()
        if verbose:
            print 'Tree is now rooted. Procedure took ' + str(end_time - start_time) + ' seconds to complete'       
    
    if connection:
        connection.close()
        
 
 # this algorithm creates a new ouput tree in a new collection by copying the tree first and then running the in-place algorithm
def copyAndAddRootToTreeSeparateConnection(system,database,port,data_collection_string,output_collection_string, verbose=False):  
    start_time = time.time()
    connection = Connection(system, port)
    db = connection[database]   

    # open existing and new tree collections 
    existing_coll = db[str(data_collection_string)]
    data_coll = db[str(output_collection_string)]   

    # we can't just copy records from the existng tree collection to the new tree collection, because the nodes reference
    # each other through object IDs.  Therefore, we have to actually traverse the tree
    rootnode = returnRootNodeInTree(existing_coll,verbose)
    # starting at the root will copy the entire tree
    copySubtreeFromStartingNodeToNewCollection(existing_coll,rootnode,data_coll)
    # now root the new copy of the tree
    addRootToTree(data_coll,verbose)
    
    end_time = time.time()
    if verbose:
        print 'Tree is Copied and rooted. Procedure took ' + str(end_time - start_time) + ' seconds to complete'       
    
    if connection:
        connection.close()      
        
        
  # this algorithm creates a new ouput tree in a new collection by copying the tree nodes during a recursive traversal
def copyTreeSeparateConnection(system,database,port,data_collection_string,output_collection_string, verbose=False):  
    start_time = time.time()
    connection = Connection(system, port)
    db = connection[database]   

    # open existing and new tree collections 
    existing_coll = db[str(data_collection_string)]
    data_coll = db[str(output_collection_string)]   

    # we can't just copy records from the existng tree collection to the new tree collection, because the nodes reference
    # each other through object IDs.  Therefore, we have to actually traverse the tree
    rootnode = returnRootNodeInTree(existing_coll,verbose)
    # starting at the root will copy the entire tree
    copySubtreeFromStartingNodeToNewCollection(existing_coll,rootnode,data_coll)
   
    end_time = time.time()
    if verbose:
        print 'Tree is Copied and rooted. Procedure took ' + str(end_time - start_time) + ' seconds to complete'       
    
    if connection:
        connection.close()             