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
            

def addRootToTreeSeparateConnection(system,database,port,data_collection_string,verbose=False):

  
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