# -*- coding: utf-8 -*-
import pymongo

def recursive_build_newick(tree_coll, doc_id):
    nodeDoc = tree_coll.find_one({'_id':doc_id})
    clades = nodeDoc[u'clades'] # a list of doc ids
    newickString = "("
    for clade in clades:
      childDoc = tree_coll.find_one({'_id':clade})

      if childDoc.has_key(u'clades'):
        subNewickString = recursive_build_newick(tree_coll,clade)
        newickString += subNewickString

      if childDoc.has_key(u'name'):
        nodeName = childDoc[u'name']
        newickString += nodeName

      if childDoc.has_key(u'branch_length'):
        branchLength = childDoc[u'branch_length']
        newickString += ":%f" %(branchLength)
      else:
        print "Warning: this node has empty branch length"

      newickString += ","

    # remove the last "," and replace it with ")"
    newickString = newickString[:-1] + ")"
    return newickString

def recursive_build_phyloxml(tree_coll, doc_id, indent):
    nodeDoc = tree_coll.find_one({'_id':doc_id})
    indentStr = " " * indent

    # add new <clade> tag
    if nodeDoc.has_key(u'branch_length'):
      branchLength = nodeDoc[u'branch_length']
      phyloxmlString = indentStr + '<clade branch_length="%s">\n' % branchLength
    else:
      print "Warning: this node has empty branch length"
      phyloxmlString = indentStr + '<clade>\n'

    # add any clade-level elements
    phyloxmlString += writeCladeElements(nodeDoc, indent + 2)

    # recursively add any subclades
    if nodeDoc.has_key(u'clades'):
      clades = nodeDoc[u'clades'] # a list of doc ids
      for clade in clades:
        phyloxmlString += recursive_build_phyloxml(tree_coll, clade, indent + 2)

    # close this <clade> tag and return
    phyloxmlString += indentStr + '</clade>\n'
    return phyloxmlString

def initializePhyloXMLString(phylo):
  string = \
"""<phyloxml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.phyloxml.org" xsi:schemaLocation="http://www.phyloxml.org http://www.phyloxml.org/1.10/phyloxml.xsd">
<phylogeny rooted="true">
"""
  string += writeCladeElements(phylo, 2)
  if phylo.has_key(u'description'):
    string += '  <description>\n'
    string += '    %s\n' % phylo[u'description']
    string += '  </description>\n'
  return string

def writeCladeElements(clade, indent):
  indentStr = " " * indent
  string = ""

  if clade.has_key(u'name'):
    string += indentStr + '<name>\n'
    string += indentStr + '  %s\n' % clade[u'name']
    string += indentStr + '</name>\n'

  if clade.has_key(u'confidences'):
    confidences = clade['confidences']
    for i in range(0, len(confidences)):
      string += indentStr + '<confidence type="%s">\n' % confidences[i]['type']
      string += indentStr + '  %s\n' % confidences[i]['value']
      string += indentStr + '</confidence>\n'

  if clade.has_key(u'_color'):
    string += indentStr + '<color>\n'
    string += indentStr + '  <red>\n'
    string += indentStr + '    %s\n' % clade["_color"]["red"]
    string += indentStr + '  </red>\n'
    string += indentStr + '  <green>\n'
    string += indentStr + '    %s\n' % clade["_color"]["green"]
    string += indentStr + '  </green>\n'
    string += indentStr + '  <blue>\n'
    string += indentStr + '    %s\n' % clade["_color"]["blue"]
    string += indentStr + '  </blue>\n'
    string += indentStr + '</color>\n'

  if clade.has_key(u'properties'):
    properties = clade['properties']
    for i in range(0, len(properties)):
      property = properties[i]
      string += indentStr + '<property datatype="%s" ref="%s" applies_to="%s"' % \
        (property["datatype"], property["ref"], property["applies_to"])
      if property.has_key("unit"):
        string += ' unit="%s"' % property["unit"]
      string += '>\n'
      string += indentStr + '  %s\n' % property["value"]
      string += indentStr + '</property>\n'

  return string

def convertTreeToNewickString(tree_coll):
    phylo = tree_coll.find_one({'rooted':True})
    string = ""
    if (phylo is not None):
       doc_id = phylo[u'clades'][0] #point to the actual root
       # newick string ends with ";"
       string = recursive_build_newick(tree_coll, doc_id) + ";"
    else:
        print 'failed to find the root document in the tree collection'
    return string

def convertTreeToPhyloXMLString(tree_coll):
    phylo = tree_coll.find_one({'rooted':True})
    if (phylo is not None):
      string = initializePhyloXMLString(phylo)
      doc_id = phylo[u'clades'][0] #point to the acutal root
      string += recursive_build_phyloxml(tree_coll, doc_id, 2)
      string += '</phylogeny>\n'
      string += '</phyloxml>\n'
    else:
      print 'failed to find the root document in the tree collection'
    return string

def getHeadersForTable(table_coll):
    # create the header row.  If it contains a "name" field,
    # then ensure that this appears first.
    first_row = table_coll.find_one()
    string = ""
    if "name" in first_row.keys():
        string = "name,"
    for key in first_row.iterkeys():
        if key == "_id" or key == "name":
            continue
        string += key
        string += ","
    string = string[:-1] + "\n"
    return string

def convertTableToCSVString(table_coll):
    # get the header row
    string = getHeadersForTable(table_coll)

    hasNames = False
    if "name," in string:
        hasNames = True

    # create the contents rows
    for row in table_coll.find():
        if hasNames:
            string += row["name"]
            string += ","
        for key, value in row.iteritems():
            if key == "_id" or key == "name":
                continue
            string += value
            string += ","
        string = string[:-1] + "\n"

    string = string[:-1]
    return string
