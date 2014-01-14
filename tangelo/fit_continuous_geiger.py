# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 09:11:01 2013

@author: clisle
"""

# import utilities to exchange trees and matrices between APE/Geiger and Arbor

from tree_interchange import *

def InvokeFitContinuous(tree_collection_name,tree_coll,matrix_collection_name,matrix_coll, character, model_parameter, out_collection_name,verbose):
    # first convert tree to an APE tree
    ape_tree_in_R = ConvertArborTreeIntoApe(tree_coll,tree_collection_name)
    # then convert the character matrix in a data.frame in R
    char_matrix_in_R = ConvertArborCharacterMatrixIntoDataFrame(matrix_coll,matrix_collection_name)
    
    # get the shortcut for the r interpreter
    r = robjects.r
    
    # fitContinuous is defined in the geiger library
    r('library(geiger)')

    # set the row names of the table to be indexed by the 'species' attribute
    commandstr = 'row.names('+char_matrix_in_R+') <- '+ char_matrix_in_R +'$species'
    if verbose:
        print  "commandstr:",commandstr
    r(commandstr)

    commandstr = 'selectedchar<- ' + char_matrix_in_R +'["'+character+'"]'
    if verbose:
        print "commandstr:",commandstr
    r(commandstr)
    
    if verbose:
        print "character table to test for phylosignal:"
        r('str(selectedchar)')
    
    #r('svl_named <- as.numeric(svl$SVL)')
    commandstr = 'selectedchar_named <- as.numeric(selectedchar$'+character+')'
    if verbose:
        print commandstr
    r(commandstr)
    r('names(selectedchar_named) <- rownames(selectedchar)')
   
    commandstr = 'modelResult<-fitContinuous(selectedchar_named,phy='+ ape_tree_in_R +', model='+model_parameter+')'
    if verbose:
        print "commandstr:",commandstr
    r(commandstr)

    r('print(modelResult$opt$alpha)')
    r('print(modelResult$opt$aic)')
    r('print(modelResult$opt$aicc)')

    # now change the tree branch lengths to reflect the model fitting       
    print "creating output tree"
    commandstr = 'transformedTree<-transform('+ape_tree_in_R+', '+model_parameter+ ', modelResult$opt$alpha)'
    if verbose:
        print commandstr
    r(commandstr)
        # now store the tree in APE format as a new dataset in Arbor
    transformedTree = r['transformedTree']
    #r('save(transformedTree,file="transformedTree")')
    
        
    #r('str(transformedTree)')
    importApeTreeToArbor(transformedTree,out_collection_name)
    


def FitContinuousBySeparateConnection(system,database,port,tree_collection_name,matrix_collection_name,character, parameters,output_tree_collection_name,verbose):
   
    connection = Connection(system, port)
    db = connection[database]    
    tree_coll = db[str(tree_collection_name)]
    matrix_coll = db[str(matrix_collection_name)]
    out_tree_coll = db[str(output_tree_collection_name)]

    # startup up an R interpreter to do the processing.  We will be converting a tree, so create a tree handler
    robjects.r("library('geiger')")
    r = robjects.r
    r('source("/Users/clisle/Projects/Arbor/code/python-R-integration/arbor2apeTreeHandler.R")')
    r('treeHandler = new("arbor2apeTreeHandler")')

    
    result = InvokeFitContinuous(tree_collection_name, tree_coll, matrix_collection_name,matrix_coll, character, parameters, out_tree_coll,verbose)
    if (connection):
        connection.close()
    return result
    
