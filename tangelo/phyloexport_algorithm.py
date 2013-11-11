# -*- coding: utf-8 -*-

from Bio import Phylo
from Bio.Phylo import BaseTree

import pymongo
import logging
from bson.objectid import ObjectId


def recursive_build_newick(tree_coll, doc_id):
    nodeDoc = tree_coll.find_one({'_id':doc_id})
    clades = nodeDoc['clades'] # a list of doc ids
    newickString = "("
    for clade in clades:
      childDoc = tree_coll.find_one({'_id':clade})
      nodeName = childDoc[u'name'] 
      branchLength = childDoc[u'branch_length']
      if childDoc.has_key('clades'):
        subNewickString = recursive_build_newick(tree_coll,clade)
        newickString += subNewickString
      newickString += nodeName + ":%f" %(branchLength)
      newickString += ","

    # remove the last "," and replace it with ")"
    newickString = newickString[:-1] + ") "
    return newickString

def convertTreeToNewickString(tree_coll):
    phylo = tree_coll.find_one({'rooted':True})
    if phylo:
       doc_id = phylo['clades'][0]#point to the acutally root
       # newick string ends with ";"
       newickString = recursive_build_newick(tree_coll, doc_id) + ";"
    else:
        print 'failed to find the root document in the tree collection'

    return newickString
