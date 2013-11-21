# -*- coding: utf-8 -*-

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
   
   
def InvokePicantePhyloSignal(tree_collection_name,tree_coll,matrix_collection_name,matrix_coll):
    # first convert tree to an APE tree
    ape_tree_in_R = ConvertArborTreeIntoApe(tree_coll,tree_collection_name)
    # then convert the character matrix in a data.frame in R
    char_matrix_in_R = ConvertArborCharacterMatrixIntoDataFrame(matrix_coll,matrix_collection_name)
    
    r = robjects.r
    r('library(picante)')

    #anoleData<-read.csv("anolisDataAppended.csv", row.names=1)
    
    # measure phylogenetic signal
    # we will concentrate on one trait: SVL

    # look at table as it is read out of Arbor
    #r('save('+char_matrix_in_R+',file="apematrix")')

    # set the row names of the table to be indexed by the 'species' attribute
    commandstr = 'row.names('+char_matrix_in_R+') <- '+ char_matrix_in_R +'$species'
    print  "commandstr:",commandstr
    r(commandstr)

  
    
    #svl<-anoleData[,1]
    commandstr = 'svl<- ' + char_matrix_in_R +'["SVL"]'
    print "commandstr:",commandstr
    r(commandstr)
    
    r('svl_named <- as.numeric(svl$SVL)')
    r('names(svl_named) <- rownames(svl)')
    r('print(svl_named)')

    # the matrix doesn't have row.names yet, so assign by the species column instead
    #names(svl)<-rownames(anoleData)
    #commandstr = 'row.names(svl) <-  row.names('+char_matrix_in_R+')'
    #print  "commandstr:",commandstr
    #r(commandstr)
    #r('print(svl)')
    
    # Names and data match - so data integrator might be needed at this step 
    # (in general) but is not needed in this case.
    
    # now we can test for signal
    #res1<-phylosignal(svl, anoleTree)
    print "ape tree printed by R:"
    r('print('+str(ape_tree_in_R)+')')
    
    #r('save('+ape_tree_in_R+',file="apetree")')
    #r('save('+char_matrix_in_R+',file="apematrix")')
    commandstr = 'res1<-phylosignal(svl_named,phy='+ ape_tree_in_R +')'
    print "commandstr:",commandstr
    r(commandstr)
    
    # the IMPORTANT PARTS of this output are:
    #res1$K # the value of the test statistic
    #res1$PIC.variance.P # the P value
    
    r('print(res1$K)')
    
    
    

def CalculatePhylogeneticSignalBySeparateConnection(system,database,port,tree_collection_name,matrix_collection_name,verbose):
   
    connection = Connection(system, port)
    db = connection[database]    
    tree_coll = db[str(tree_collection_name)]
    matrix_coll = db[str(matrix_collection_name)]

    # startup up an R interpreter to do the processing.  We will be converting a tree, so create a tree handler
    robjects.r("library('geiger')")
    r = robjects.r
    r('source("/Users/clisle/Projects/Arbor/code/python-R-integration/arbor2apeTreeHandler.R")')
    r('treeHandler = new("arbor2apeTreeHandler")')

    
    result = InvokePicantePhyloSignal(tree_collection_name, tree_coll, matrix_collection_name,matrix_coll)
    if (connection):
        connection.close()
    return result
    