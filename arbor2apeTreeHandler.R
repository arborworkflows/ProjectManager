# C. Lisle
# KnowledgeVis, LLC
# November 2013

# declare a new S4 style class in R that provides an interface to pass phylogenetic data between Python and R.
# First, we declare only the instance variables and their types.  This arbor2apeTreeHandler class can represent an APE
# tree, which is a 4-tuple (numNodes,taxaNames,edge table, branch_lengths).  "preInitialized" is a state variable
# that indicates how initialized the object is.  It set to TRUE when prerequisites are completed for creating
# the edge Table.  "fullyInitialized" is set after the tables and lists are allocated.

# To test the class, read in the definition, then paste the following lines (uncommented) into the R console.
# The result will be a display of the class contents with an entry into each type of tree metadata to test the
# setter functions.


" Example of creating a small tree through the API and converting it to an APE tree.

           Root (Node=4)
           /   \
          /      D (Node=5)
     A (N=1)    /  \
               /     \
            B (N=2)   C (node=3)

"

# Here are the commands to initialize the class and create and plot the APE tree:

#t2 = new("arbor2apeTreeHandler")
#setNumberOfEdges(t2) <- 6
#setNumberOfInternalNodes(t2) <- 3
#setNumberOfTaxa(t2) <- 4
#initializeStorage(t2)
#setTaxaIndex(t2,1,"A")
#setTaxaIndex(t2,2,"B")
#setTaxaIndex(t2,3,"C")
#setTaxaIndex(t2,4,"D")
#setEdgeIndex(t2,1,5,6)
#setEdgeIndex(t2,2,5,7)
#setEdgeIndex(t2,3,6,1)
#setEdgeIndex(t2,4,6,2)
#setEdgeIndex(t2,5,7,3)
#setEdgeIndex(t2,6,7,4)
#setBranchLengthIndex(t1, 2, 5.678)
#buildGeigerTree(t2,myNewTree)
#plot(myNewTree)

# dependency needed for conversion to APE trees
library(geiger)

#**************************
# Class Definition
#**************************


setClass(
  "arbor2apeTreeHandler",
  representation(
    numNodes = "numeric",
    numTaxa = "numeric",
    numEdges = "numeric",
    edgeTable = "matrix",
    taxaNames = "array",
    branch_lengths = "array",
    preInitialized = "logical",
    fullyInitialized = "logical"
  ),

  # set the initial state to have no nodes and an empty taxa and branch length lists.  The edge table
  # is not initialized for the empty object, because the matrix will be instantiated during initialize-storage

  prototype(
     numNodes = 0,
     numTaxa = 0,
     numEdges = 0,
     preInitialized = FALSE,
     fullyInitialized = FALSE
  )
)

#**************************
# Methods Name Declarations
#**************************

# methods on the object have to be first declared in the R namespace as generic functions, before the actual
# method code is assigned to the new class.  Below is a declaration of the name of each method defined on the class.
# The arguments declared here must match the arguments declared in the method body below.  Note the "<-" syntax
# for setters that are to be used with the assignment R operator.

setGeneric (
        name= "setNumberOfInternalNodes<-",
        def=function(object,value){standardGeneric("setNumberOfInternalNodes<-")}
)

setGeneric (
        name= "setNumberOfTaxa<-",
        def=function(object,value){standardGeneric("setNumberOfTaxa<-")}
)
setGeneric (
        name= "setNumberOfEdges<-",
        def=function(object,value){standardGeneric("setNumberOfEdges<-")}
)


setGeneric (
        name="initializeStorage",
        def=function(object){standardGeneric("initializeStorage")}
)

setGeneric (
        name="testForInitialized",
        def=function(.Object){standardGeneric("testForInitialized")}
)

setGeneric(
        name="setTaxaIndex",
        def=function(object,taxaindex,taxaname){standardGeneric("setTaxaIndex")}
)

setGeneric(
        name="setEdgeIndex",
        def=function(object,edgeindex,edgesource,edgedestination){standardGeneric("setEdgeIndex")}
)

setGeneric(
        name="setBranchLengthIndex",
        def=function(object,index, branchlength){standardGeneric("setBranchLengthIndex")}
)

setGeneric(
        name="buildGeigerTree",
        def=function(object,treename){standardGeneric("buildGeigerTree")}
)


#*********************
# Methods
#*********************

# method to set the total number of nodes in the tree.  A replace method has to be used to
# assign a modified value to the object (the class instance).

setReplaceMethod(f="setNumberOfInternalNodes",
   signature="arbor2apeTreeHandler",
   definition = function(object,value) {
        cat("setting value of numNodes\n")
        print(value)
        object@numNodes <- value
        testForInitialized(object)
        return (object)
   }
)

setReplaceMethod(f="setNumberOfTaxa",
   signature="arbor2apeTreeHandler",
   definition = function(object,value) {
        cat("setting value of numTaxa\n")
        print(value)
        object@numTaxa <- value
        testForInitialized(object)
        return (object)
   }
)

setReplaceMethod(f="setNumberOfEdges",
   signature="arbor2apeTreeHandler",
   definition = function(object,value) {
        cat("setting value of numEdges\n")
        print(value)
        object@numEdges <- value
        testForInitialized(object)
        return (object)
   }
)



# Check that the number of nodes, edges, and taxa have all been initialized.  Once all three have been
# set, then we can set the "initialized" instance variable.  This variable is used as a gate to avoid the
# table being setup with an incorrect size and causing runtime errors.
#
# Note: this is a method that modifies the object itself. This requires namespace tricks to accomplish.  Generally
# every R function operations in its own namespace and there is no way to have instance variables available, even
# to a method.  Here we find the name of the variable using 'deparse' and assign a value to the object in the
# "parent's namespace".
#

setMethod(f="testForInitialized",
   signature="arbor2apeTreeHandler",
   definition = function(.Object) {
        nameObject <- deparse(substitute(.Object))
        if (.Object@numNodes > 0) {
            if (.Object@numEdges > 0) {
                if (.Object@numTaxa > 0) {
                    .Object@preInitialized <- TRUE
                    cat("setting object initialized to TRUE\n")
                    # cause side-effect by assigning value in parent's namespace
                    assign(nameObject,.Object,envir=parent.frame())
                    return(invisible())
                }
            }
        }
   }
)


# Check that the object is ready for allocating arrays.  If so, allocate and set the object state.
setMethod(f="initializeStorage",
   signature="arbor2apeTreeHandler",
   definition = function(object) {
        # keep this line first, see description in other functions
        objectName <- deparse(substitute(object))
        if (object@preInitialized == TRUE) {
          cat("initializing the edge table")
          # initialize the edgeTable by assigning the size of the matrix and filling it with zeros
          numElements = object@numEdges
          object@edgeTable <- matrix(0,nrow=numElements,ncol=2)
          object@taxaNames <- array(dim=object@numTaxa)
          object@branch_lengths <- array(dim=object@numEdges)
          # indicate that object is really ready for data
          object@fullyInitialized <- TRUE
          # cause side-effect by assigning value in parent's namespace
          assign(objectName,object,envir=parent.frame())
          return(invisible())
        }
        else
          print("TreeMgr: error; attempt to initialize storage before setting all control variables numEdges, etc.")
   }
)

#******
# Methods to set values in the tree
#******

# This method sets the text string value for an entry in the taxaNames list (corresponding to APE's tip.name array)
# The arguments are the index to set and the character string to assign.

setMethod(f="setTaxaIndex",
  signature="arbor2apeTreeHandler",
  definition=function(object,taxaindex,taxaname){
    # this objectName lookup seems to have to be done BEFORE the variable is referenced?  It works when it is
    # the first line, but not when it is later in the function..
    objectName <- deparse(substitute(object))
    #set the taxa name at location "index" to value "name"
    object@taxaNames[taxaindex] <- taxaname
    # cause side effect to update the object

    assign(objectName,object,envir=parent.frame())
    return(invisible())
  }
)

# this method sets the entry in the edge table.  It is called with the index, the source node, and the destination node

setMethod(f="setEdgeIndex",
  signature="arbor2apeTreeHandler",
  definition=function(object,edgeindex, edgesource, edgedestination){
    objectName <- deparse(substitute(object))
    #set the taxa name at location "index" to value "name"
    object@edgeTable[edgeindex,1] <- edgesource
    object@edgeTable[edgeindex,2] <- edgedestination
    # cause side effect to update the object
    assign(objectName,object,envir=parent.frame())
    return(invisible())
  }
)

# this method sets an entry in the branch_length array to the numeric value passed in the branchlength argument

setMethod(f="setBranchLengthIndex",
  signature="arbor2apeTreeHandler",
  definition=function(object,index, branchlength){
    objectName <- deparse(substitute(object))
    #set the branch length at location "index" to value "branchlength"
    object@branch_lengths[index] <- branchlength
    # cause side effect to update the object
    assign(objectName,object,envir=parent.frame())
    return(invisible())
  }
)


# build an APE tree from the data stored in the instance variables

setMethod(f="buildGeigerTree",
  signature="arbor2apeTreeHandler",
  definition=function(object,treename) {
  treeObjectName <- deparse(substitute(treename))
  # copy the edges
  treeEdges <- matrix(0,nrow=object@numEdges,ncol=2)

  for (index in 1:object@numEdges) {
    treeEdges[index,1] <- object@edgeTable[index,1]
    treeEdges[index,2] <- object@edgeTable[index,2]
  }
  # copy the taxanames
  newTaxaNames  <- array(dim=object@numTaxa)
  for (index in 1:object@numTaxa) {
    newTaxaNames[index] <- object@taxaNames[index]
  }
  # initialize all branch-lengths to 1.0.  Test that the branch lengths are defined before
  # copying them over.  If branches are not assigned, the default of 1.0 is given to each node.
  # The test is performed by examining that values are not = NA (not allocated)
  newBranchLengths <- array(1.0,dim=object@numEdges)
  for (index in 1:object@numEdges) {
    if (!is.na(object@branch_lengths[index])) {
        newBranchLengths[index] <- object@branch_lengths[index]
    }
  }
  # create the 4-tuple that is an APE tree, including optional branch lengths
  treename <- list(edge = treeEdges,
                        tip.label = newTaxaNames,
                        Nnode = object@numNodes,
                        edge.length = newBranchLengths)
  # set the classname of the APE tree
  class(treename) <- "phylo"
  assign(treeObjectName,treename,envir=parent.frame())
   print("build APE/Geiger tree completed.")
  return(invisible())
  }
)
