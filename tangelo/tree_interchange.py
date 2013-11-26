# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 08:16:45 2013

@author: clisle
"""

"""
This module provides routines for interchanging phylo trees between  APE (in R) 
and Arbor's TreeStore (noSQL-based) storage.

"""
import pymongo
from pymongo import Connection
from bson import ObjectId
import json
from json import JSONEncoder
import rpy2.robjects as robjects

# import pandas and dataframe for character matrix conversion 
import pandas
from pandas import DataFrame
import pandas.rpy.common as com


global_next_node = 0
global_next_edge = 0
global_leafname_list = []

# used to print out Mongo ObjectId's in json.dumps (SZ)
class MongoEncoder(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:            
            return JSONEncoder.default(obj, **kwargs)
            

# lookup taxa by name so we don't get the nodes scrambled in the APE tree
def returnTaxaNodeIndexFromSpecies(speciesName):
    global global_leafname_list
    for taxa in global_leafname_list:
        if taxa[1] == str(speciesName):
            #print "Leaf: returning ",taxa[0], " for ",speciesName
            return taxa[0]
    print "error in leafname lookup list for",speciesName
    return 1

def returnNextNewNodeIndex():
    global global_next_node
    global_next_node = global_next_node+1
    return global_next_node

def returnNextEdgeIndex():
    global global_next_edge
    global_next_edge = global_next_edge+1
    return global_next_edge

# traverse the tree and write out edge records to the treeHandler instance that has been created in the
# attached R interpreter.

def recursiveHelper(data_coll,child,nodeindex,edgeindex):
    results = data_coll.find({'_id':child})
    phylo = results[0]
    r = robjects.r
    if 'clades' in phylo:
        # this node is not a leaf, so traverse its children and store the edges
        counter = 1
        for child in phylo['clades']:
            #  peek into the child node.  If the node below this is a leaf, explicitly write out the child 
            #  node instead of continuing recursion below this
            childnode = data_coll.find({'_id':child})[0]
            if 'clades' not in childnode:
                # print out the taxa node directly, no more recursion.  New trees have names directly on the nodes,
                # legacy format uses taxonomies.scientific_name syntax instead, so check both places for the name
                if 'taxonomies' in childnode:
                    speciesNameString = childnode['taxonomies'][0]['scientific_name']
                elif 'name' in childnode:
                    speciesNameString = childnode['name']
                else:
                    speciesNameString = 'unknown'
                # we might be traversing in a different order than when taxa were inserted into the taxa list, so 
                # do a lookup on the name so we return the correct node index. This means taxa names have to be unique
                taxaIndex = returnTaxaNodeIndexFromSpecies(speciesNameString)
                # A function is used to allocate the edges indexes so the different branches of recursion don't
                # have node number clashes.                 
                newEdgeIndex = returnNextEdgeIndex()
                rCommand = 'setEdgeIndex(treeHandler,' + str(newEdgeIndex) + ',' + str(nodeindex) + ',' + str(taxaIndex) + ')'
                r(rCommand)    
                # if there are branch lengths in the dataset, copy them to the Tree handler for transfer to APE
                if 'branch_length' in childnode:
                    rCommand = 'setBranchLengthIndex(treeHandler,' + str(newEdgeIndex) + ',' + str(childnode['branch_length']) + ')'
                    r(rCommand)    
            else:
                # Case between two intermediate nodes.  write out this edge between parent and this child.  
                # Allocate nodes and edges globally to prevent number clashes between the branches of recursion.  
                dest_node_index = returnNextNewNodeIndex()
                newEdgeIndex = returnNextEdgeIndex()
                rCommand = 'setEdgeIndex(treeHandler,' + str(newEdgeIndex) + ',' + str(nodeindex) + ',' + str(dest_node_index) + ')'
                r(rCommand)  
                # if there are branch lengths in the dataset, copy them to the Tree handler for transfer to APE
                if 'branch_length' in childnode:
                    rCommand = 'setBranchLengthIndex(treeHandler,' + str(newEdgeIndex) + ',' + str(childnode['branch_length']) + ')'
                    r(rCommand)    

                # continue recursion down to the next intermediate node level
                recursiveHelper(data_coll,child,dest_node_index,newEdgeIndex)




def ConvertArborTreeIntoApe(tree_coll,apeTreeName):
    global global_leafname_list
    global global_next_node
    global global_next_edge
    
    search_dict = dict()
    r = robjects.r
    
    # if no arguments are given start with the document root (SZ)
    if not search_dict:
        search_dict['rooted'] = True
    
    results = tree_coll.find(search_dict)
    
    # lets make a new tree from it
    if results.count() == 1:
        # get the root of the tree
        phylo = results[0]
        
        # find total number of nodes in the tree. Adjust down one because we are 
        # going to index past the faux root, so there will be one less internal nodes
        totalNodeCount = tree_coll.count()-1
        
        # set out how many leaves are in the tree
        leaf_query = {'clades': {'$exists': 0}}
        leaf_result = tree_coll.find(leaf_query)
        leaf_count = leaf_result.count()
        print "found ", leaf_count, " leaves"
        rCommand = 'setNumberOfTaxa(treeHandler) <- ' + str(leaf_count)

        r(rCommand)
        
        # set how many internal nodes 
        internalNodeCount = totalNodeCount - leaf_count
        rCommand = 'setNumberOfInternalNodes(treeHandler) <- ' + str(internalNodeCount)
        r(rCommand)
        
        # set how many edges
        edgeCount = totalNodeCount-1
        rCommand = 'setNumberOfEdges(treeHandler) <- ' + str(edgeCount)
        r(rCommand)    
        
        # initialize tree storage
        r('initializeStorage(treeHandler)')
        
        print ""
        print "finished tree setup. Now add the taxa.."
        
        nodeCount = 1
        for leaf in leaf_result:
             # if it is the type of tree that has taxonomies and scientific_name, then handle this case
            if 'taxonomies' in leaf:
                speciesNameString = leaf['taxonomies'][0]['scientific_name']
            elif 'name' in leaf:
                speciesNameString = leaf['name']
            #print speciesNameString
            # add the leafnode into the APE tree
            rCommand = 'setTaxaIndex(treeHandler,' + str(nodeCount)+ ',' + '"' + str(speciesNameString) + '")'
            global_leafname_list.append([nodeCount,str(speciesNameString)])
            nodeCount = nodeCount + 1
            r(rCommand) 
        
        #print global_leafname_list
        
        # add the edges by traversing the whole tree.  The taxa are always numbered 1..leaf_count, the root 
        # is always the next node index after the taxa (with index leaf_count+1), the rest of the internal nodes 
        # have arbitary index values.  Start this traversal with the root. 
        
        root_query = {'rooted': True}
        rootNode = tree_coll.find(root_query)[0]
        rootNodeId = rootNode['_id']
        
        # the root is a singleton, which is an artifact of the way we loaded trees, so traverse past it one manual step.
        # there is always a single clades entry between the handle node and the top of the phylogeny, so we can pick out 
        # the first list entry. 
        
        subRootNodeId = rootNode['clades'][0]
        
        # initialize to the node numbers right after the taxa and start recursing down the tree
        global_next_node = leaf_count
        global_next_edge = 0
        recursiveHelper(tree_coll,subRootNodeId, returnNextNewNodeIndex(),global_next_edge)
        
        # print the state of the handler, then create an APE tree, print, and display it so we can compare the
        # representations and make sure the conversion was correct
        
        #r('print(treeHandler)')
        print 'apeTreeName is:',apeTreeName
        commandstring = 'buildGeigerTree(treeHandler,'+str(apeTreeName)+')'
        r(commandstring)
        return str(apeTreeName)
    else:
        print 'Search returned more zere or more than one object. Number of objects: ', results.count()
    


def ConvertArborCharacterMatrixIntoDataFrame(data_coll,matrix_name):      
    # query the whole collection to get a document for each row in the character matrix
    char_query = {}
    char_result = data_coll.find(char_query)
    print "matrix query:",char_result
    
    # initialize empty dictionary, then find out the column headers (which are python keys)
    outtable = dict()
    charkeys = char_result[0].keys()  
    # now loop for each separate column and initialize an empty list
    for chars in charkeys:
        outtable[chars]=[]      
    # now loop for each row in the character matrix    
    for mychar in char_result:
            # for each field in this document, add it to the column that corresponds to the 
            for mykey in mychar.keys():
                outtable[mykey].append(mychar[mykey])  
    pandas_df = DataFrame(outtable)  
    #print pandas_df[1:10]  
    matrix_in_R = pandas.rpy.common.convert_to_r_dataframe(pandas_df)
    # assign a known name to the R object and return this name, so we can get to the object again
    robjects.globalenv[str(matrix_name)] = matrix_in_R
    #print(type(matrix_name))
    #print (matrix_name)
    return str(matrix_name)
   

#  *********************************************
#  **** converting from APE to Arbor below *****
#  *********************************************

def printApeTree(apeTree):
    print "print overall apeTree:"
    print apeTree
    print "[0]:",apeTree[0]
    print "[1]:",apeTree[1]
    print "[2]:",apeTree[2]
    print "[3]:",apeTree[3]
    
# lookup taxa by name so we don't get the nodes scrambled in the APE tree
def returnNodeNameFromIndex(apeTree,index):
    if (len(apeTree[1])==1):
        leafIndex = 2
        countIndex = 1
    else:
        #print "alternative ape tree compondent order case"
        leafIndex = 1
        countIndex = 2
    leafCount = len(apeTree[leafIndex])
    #print "lookup for index:",index
    if index<leafCount+1:
        # node is a taxon, return the species name
        nodeName = apeTree[leafIndex][index-1]
    else:
        nodeName = 'node'+str(index)
    return nodeName

    # sometimes the tuples in phylo class instance are re-orderered.  the transformed tree seems to have the order:
    #[0]=edges, [1]=tiplabels, [2]=internalNodeCount, [3]= branchlengths, which has [1] and [2] switched
    #from the definition.  We will look and switch them if necessary

def addApeTreeNodesIntoTreeStore(apeTree,data_coll):
    if (len(apeTree[1])==1):
        leafIndex = 2
        countIndex = 1
    else:
        #print "alternative ape tree compondent order case"
        leafIndex = 1
        countIndex = 2
    # calculate how many nodes are here
    leafCount = len(apeTree[leafIndex])
    #printApeTree(apeTree)
    print "apeTree[countIndex]:",apeTree[countIndex]
    print "apeTree[countIndex][0]:",apeTree[countIndex][0]
    totalNodes = leafCount + int(apeTree[countIndex][0])
    # loop through the nodes and create a document for each one
    for index in range(1,totalNodes+1):
        node = dict()
        node['name'] = returnNodeNameFromIndex(apeTree,index)
        if index>leafCount:
            # node is not a taxon, so add an empty clade array
            node['clades'] = []
        data_coll.insert(node)
        
# traverse the edges of an apeTree and add the connectivity from the apeTree into the
# mongo collection representing the tree.  This method assumes the nodes have  been added previously.
        
def addApeTreeEdgesIntoTreeStore(apeTree,data_coll):
    # go through the edge table and add fields to the nodes in the collection
    edgeCount = len(apeTree[0])/2
    print "found edge count to be: ",edgeCount
    #print "edges:",apeTree[3]
    for edgeIndex in range(0,edgeCount):
        startNodeIndex = int(apeTree[0][edgeIndex])
        endNodeIndex = int(apeTree[0][edgeCount+edgeIndex])
        startNodeQuery = {'name': returnNodeNameFromIndex(apeTree,startNodeIndex)}
        endNodeQuery = {'name': returnNodeNameFromIndex(apeTree,endNodeIndex)}
        startNode = data_coll.find_one(startNodeQuery)
        endNode = data_coll.find_one(endNodeQuery)
        #print "edgeIndex: ",edgeIndex,"endnode:  ", endNode
        # add branch length to end node
        try:
            endNode['branch_length'] = apeTree[3][edgeIndex]
        except TypeError:
            print "error on edgeIndex or no branchlength:",edgeIndex
            
        #print "edgeIndex: ",edgeIndex,"endnode:  ", endNode
        data_coll.update(endNodeQuery,endNode)
        # add edge leaving start node and going to endnode
        startNode['clades'].append(endNode['_id'])
        data_coll.update(startNodeQuery,startNode)

# The Arbor treestore already has all its tree nodes, find the root of the tree and add 
# a handle node into the collection pointing to the root node.

def addHandleNodeIntoTreeStore(apeTree,data_coll):
    if (len(apeTree[1])==1):
        leafIndex = 2
        countIndex = 1
    else:
        #print "alternative ape tree compondent order case"
        leafIndex = 1
        countIndex = 2    
    leafCount = len(apeTree[leafIndex])
    # add the 'handle node' to the collection.  Find the root of the dataset by getting the node immediately after the last leaf
    rootNodeQuery = {'name': returnNodeNameFromIndex(apeTree,leafCount+1)}
    rootNode = data_coll.find_one(rootNodeQuery)
    handlenode = dict()
    #handlenode['name'] = ''
    handlenode['rooted'] = True
    handlenode['clades'] =  []
    handlenode['clades'].append(rootNode['_id'])
    data_coll.insert(handlenode)

# this erases the name attributes on internal nodes of the tree.  Names for taxon nodes are not affected

def clearInternalNodeNames(apeTree,data_coll):
    if (len(apeTree[1])==1):
        leafIndex = 2
        countIndex = 1
    else:
        print "alternative ape tree compondent order case"
        leafIndex = 1
        countIndex = 2    
    leafCount = len(apeTree[leafIndex])
    totalNodes = leafCount + int(apeTree[countIndex][0])
    for index in range(1,totalNodes+1):   
        if index>leafCount:
            # node is not a taxon, so remove its name entry
            nodeQuery = {'name': returnNodeNameFromIndex(apeTree,index)}
            internalNode = data_coll.find_one(nodeQuery)
            if 'name' in internalNode:
                del internalNode['name']
            data_coll.update(nodeQuery,internalNode)
    
# perform the steps that transform an apeTree (passed through the parameter variable) into
# a document collection stored in the Arbor TreeStore.  The steps are: (1)Nodes are created, (2) edges added,
# (3) handled node is created in the collection, and (4) names are erased for hierarchical nodes
    
def importApeTreeToArbor(apeTree,data_coll):  
    data_coll.drop()
    global global_next_node
    global global_next_edge
    global global_leafname_list
    global_next_node = 0
    global_next_edge = 0
    global_leafname_list = []
    addApeTreeNodesIntoTreeStore(apeTree,data_coll)
    addApeTreeEdgesIntoTreeStore(apeTree,data_coll)
    addHandleNodeIntoTreeStore(apeTree,data_coll)
    clearInternalNodeNames(apeTree,data_coll)
    
      
    