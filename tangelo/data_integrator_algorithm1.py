# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 09:11:01 2013

@author: clisle
"""

# import utilities to exchange trees and matrices between APE/Geiger and Arbor

from tree_interchange import *

def InvokeDataIntegrator(tree_collection_name,tree_coll,matrix_collection_name,matrix_coll, out_tree_collection_name,verbose):
    # first convert tree to an APE tree
    ape_tree_in_R = ConvertArborTreeIntoApe(tree_coll,tree_collection_name)
    # then convert the character matrix in a data.frame in R
    char_matrix_in_R = ConvertArborCharacterMatrixIntoDataFrame(matrix_coll,matrix_collection_name)

    # get the shortcut for the r interpreter
    r = robjects.r

    # DataIntegrator is defined in the geiger library
    r('library(geiger)')

    # set the row names of the table to be indexed by the 'species' attribute
    commandstr = 'row.names('+char_matrix_in_R+') <- '+ char_matrix_in_R +'$species'
    if verbose:
        print  "commandstr:",commandstr
    r(commandstr)

    commandstr = 'modelResult<-treedata(phy='+ ape_tree_in_R +', data='+char_matrix_in_R+',sort=FALSE)'
    if verbose:
        print "commandstr:",commandstr
    r(commandstr)

    r('print(modelResult$phy)')
    #r('print(modelResult$dat)')
    r('cleanedTree <- modelResult$phy')
    r('cleanedMatrix <- modelResult$dat')
    cleanedTree = r['cleanedTree']
    cleanedMatrix = r['cleanedMatrix']
    importApeTreeToArbor(cleanedTree,out_tree_collection_name)

    r('print(typeof(cleanedMatrix))')
    r('print(class(cleanedMatrix))')
    # since we only have one output currently, return the matrix.  The tree has been written out already
    return cleanedMatrix




def DataIntegratorBySeparateConnection(system,database,port,
                                      tree_collection_name,matrix_collection_name,
                                      output_tree_collection_name,
                                      verbose):

    connection = Connection(system, port)
    db = connection[database]
    tree_coll = db[str(tree_collection_name)]
    matrix_coll = db[str(matrix_collection_name)]
    out_tree_coll = db[str(output_tree_collection_name)]

    # startup up an R interpreter to do the processing.  We will be converting a tree, so create a tree handler
    robjects.r("library('geiger')")
    r = robjects.r
    #r('source("/Users/clisle/Projects/Arbor/code/python-R-integration/arbor2apeTreeHandler.R")')
    r('source("arbor2apeTreeHandler.R")')
    r('treeHandler = new("arbor2apeTreeHandler")')


    result = InvokeDataIntegrator(tree_collection_name, tree_coll, matrix_collection_name,matrix_coll,  out_tree_coll,verbose)
    if (connection):
        connection.close()
    return result

