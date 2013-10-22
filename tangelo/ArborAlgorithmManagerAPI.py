# -*- coding: utf-8 -*-
"""
Created on 21 October 2013

@author: clisle

This API manages the algorithms installed in Arbor for execution on datasets available 
in the Arbor Treestore. 

Requirements:
    - mongoDB instance used to store metadata
    - pymongo, csv packages for python
"""


import pymongo
from bson import ObjectId
from pymongo import Connection
import json
import csv

# import the recursive algorithm to process phyloXML records and create a mongo collection
import phyloimport_algorithm

# import the algorithm to add a root to unrooted trees 
import root_phylotree_algorithm

class ArborAlgorithmManager:
    
    def __init__(self):  
        
        # holder for the File Manager API object reference        
        self.projectapi = {}
        
    # Setup the list of the algorithms installed in Arbor.  We want to make this
    # dynamic via plug-in techniques later, but this direct declaration will allow us to 
    # create a prototype for the PIs to test. 
        
    def initAlgorithmLibrary(self):
        # setup the algorithms to run.  Th
          self.arbor_algorithm_dictionary = {
            'Root The Tree': self.rootTheTree,
            'Fit Continuous': self.fitContinuous
        }
        
    def setProjectManagerAPI(self,projectAPIObject):
        self.projectapi = projectAPIObject
                
    def returnListOfLoadedAlgorithms(self,):
        names = []
        for key in self.arbor_algorithm_dictionary.keys():
            names.append(key)
        return names
        
      
    # --------- running Algorithms ---------------

    # Invoke the function selected from the function dictionary, which acts as a a displatching mechanism.
      
    # TODO: add checking logic here to make sure appropriate data types are defined for algorithms
    # before running them.  All algorithms could have a list of data they depend on and it would get checked 
    def runAlgorithmByName(self,algoString, projectname='none',treename='none',matrixname='none',charactername='none'):
        print "proj:",projectname,"tree:",treename,"matrix:",matrixname,"chars:",charactername
        print "running ",algoString, "on tree: ",treename
        self.arbor_algorithm_dictionary[str(algoString)](projectname,treename,matrixname,charactername)
        print "algorithm complete"

    def rootTheTree(self,proj,tree,matrix,chars):
        tree_collection = self.projectapi.returnCollectionForObjectByName(proj,'PhyloTree',tree)
        #root_phylotree_algorithm.addRootToTree(tree_collection)
        root_phylotree_algorithm.addRootToTreeSeparateConnection('localhost','xdata',27017,tree_collection,verbose=False)

   
    def fitContinuous(self,proj,tree,matrix,chars):
        #matrixInstances = self.api.getListOfDatasetsByProjectAndType(projectname,'CharacterMatrix')
        #treeInstances = self.api.getListOfDatasetsByProjectAndType(projectname,'PhyloTree')
        tree_collection = self.projectapi.returnCollectionForObjectByName(proj,'PhyloTree',tree)
        pass
   