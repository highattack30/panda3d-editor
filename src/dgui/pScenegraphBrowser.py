from pDirectTree import *
from core.pConfigDefs import *
from direct.showbase.DirectObject import DirectObject

class TreeGraphBrowser(DirectObject):
  def __init__(self, parent, treeWrapperRoot, includeTag,
               frameSize=(1,1),
               pos=(0,0,0),
               button1func=None,
               button1extraArgs=[],
               button2func=None,
               button2extraArgs=[],
               button3func=None,
               button3extraArgs=[],):
    self.browser = DirectTree(parent=parent, pos=pos, frameSize=frameSize)
    self.includeTag = includeTag
    self.button1funcCall=button1func
    self.button1extraArgs=button1extraArgs
    self.button2funcCall=button2func
    self.button2extraArgs=button2extraArgs
    self.button3funcCall=button3func
    self.button3extraArgs=button3extraArgs
    self.directTreeDict = dict()
    self.setRoot(treeWrapperRoot)
    
    self.accept(EVENT_MODELCONTROLLER_SELECTED_OBJECT_CHANGE, self.highlight)
    
    self.accept(EVENT_SCENEGRAPH_CHANGE_ROOT, self.setRoot)
  
  def destroy(self):
    print "E: TreeGraphBrowser.destroy: TODO!!!"
    self.browser.destroy()
    self.includeTag = None
    self.button1funcCall = None
    self.button1extraArgs = None
    self.button2funcCall = None
    self.button2extraArgs = None
    self.button3funcCall = None
    self.button3extraArgs = None
    self.ignoreAll()
    self.treeWrapperRoot = None
  
  def setRoot(self, treeWrapperRoot):
    self.treeWrapperRoot = treeWrapperRoot
    self.update()
  
  def highlight(self, treeNode):
    def parentOpen(directTreeNode):
      ''' open the parent nodes of the highlighted node, recursively
      '''
      if directTreeNode.parent:
        parentOpen(directTreeNode.parent)
      directTreeNode.open = True
    
    if self.treeWrapperRoot:
      if treeNode and treeNode in self.directTreeDict:
        directTreeItem = self.directTreeDict[treeNode]
        parentOpen(directTreeItem)
        self.browser.highlight([directTreeItem])
      else:
        self.browser.highlight([])
  
  def button1func(self, treeItem):
    self.button1funcCall(treeItem.sceneNp, *self.button1extraArgs)
  def button2func(self, treeItem):
    self.button2funcCall(treeItem.sceneNp, *self.button2extraArgs)
  def button3func(self, treeItem):
    self.button3funcCall(treeItem.sceneNp, *self.button3extraArgs)
  
  def rec(self, treeWrapperNode=None, treeWrapperParent=None):
    """ Used internally to recursively add the children of a nodepath
    to the scene graph browser."""
    if treeWrapperNode is not None:
      name = "("+treeWrapperNode.className+") "+treeWrapperNode.treeName
      
      if not treeWrapperNode in self.oldDirectTreeDict:
        # create new treeNode
        directTreeItem = DirectTreeItem(treeWrapperParent, name)
        directTreeItem.sceneNp = treeWrapperNode
        directTreeItem.button1Func=self.button1func
        directTreeItem.button2Func=self.button1func
        directTreeItem.button3Func=self.button1func
        directTreeItem.open = False
      else:
        # reuse old treenode
        directTreeItem = self.oldDirectTreeDict[treeWrapperNode]
        directTreeItem.setParent(treeWrapperParent)
        directTreeItem.clearChildrens()
        del self.oldDirectTreeDict[treeWrapperNode] # remove it from the old dict
      self.directTreeDict[treeWrapperNode] = directTreeItem
      
      for c in xrange(treeWrapperNode.getNumChildren()):
        treeWrapperChild = treeWrapperNode.getChildren(c)
        self.rec(treeWrapperChild, directTreeItem)
      return directTreeItem
    else:
      return None
  
  def update(self):
    ''' update the scenegraph, deleting old gui elements
    '''
    self.oldDirectTreeDict = self.directTreeDict.copy()
    self.directTreeDict = dict()
    directTreeParent = self.rec(self.treeWrapperRoot, None)
    # destroy the contents of the nodeDict
    for treeWrapperNode in self.oldDirectTreeDict.keys()[:]:
      directTreeItem = self.oldDirectTreeDict[treeWrapperNode]
      del directTreeItem.sceneNp
      directTreeItem.destroy()
      if directTreeItem in self.oldDirectTreeDict:
        del self.oldDirectTreeDict[directTreeItem]
    del self.oldDirectTreeDict
    self.browser.treeStructure = directTreeParent
    if self.treeWrapperRoot is not None:
      self.browser.render()
      self.browser.update()

SceneGraphBrowser = TreeGraphBrowser


if __name__ == '__main__' and True:
  from direct.directbase import DirectStart
  from pandac.PandaModules import *
  def createNestedSmileys(parent,depth,branch,color):
    parent.setColor(color,1000-depth)
    for d in range(depth):
      scale=.55
      kidSmileys=lilsmileyGeom.instanceUnderNode(parent,'kid_Smileys_'+str(id(parent)))
      kidSmileys.setX(d+1)
      kidSmileys.setScale(scale)
      kidSmileys.setR(60*((d%2)*2-1))
      color=color*.8
      color.setW(1)
      for b in range(branch):
        z=b-(branch-1)*.5
        kidSmiley=lilsmileyGeom.instanceUnderNode(kidSmileys,'smileyBranch_%i-%i' %(id(kidSmileys),b))
        kidSmiley.setPos(1,0,z*scale)
        kidSmiley.setScale(scale)
        kidSmiley.setR(-z*30)
        createNestedSmileys(kidSmiley,depth-1,branch,color)
  
  # some 3d nodes
  teapot=loader.loadModel('teapot')
  teapot.reparentTo(render)
  panda=loader.loadModel('zup-axis')
  panda.reparentTo(render)
  panda.setScale(.22)
  panda.setPos(4.5,-5,0)
  
  # some 2d nodes
  lilsmiley1=loader.loadModelCopy('misc/lilsmiley')
  lilsmiley1.reparentTo(aspect2d)
  lilsmileyGeom=lilsmiley1.find('**/poly')
  createNestedSmileys(lilsmiley1,3,2,Vec4(0,1,0,1))
  lilsmiley1.setX(render2d,-.7)
  lilsmiley1.setScale(.5)
  
  camera.setPos(11.06, -16.65, 8.73)
  camera.setHpr(42.23, -25.43, -0.05)
  camera.setTag('noSelect','')
  base.setBackgroundColor(.2,.2,.2,1)
  base.disableMouse()
  
  s = SceneGraphBrowser()
  
  import time, random, gc
  lastTime = time.time()
  modelList = list()
  for i in xrange(3):
    modelList.append(panda.copyTo( render ))
  while True:
    taskMgr.step()
    if time.time() - lastTime > 0.5:
      lastTime = time.time()
      numDel = random.randint(0, len(modelList)-1)
      #print "deleting", numDel
      for i in range(numDel, 0, -1):
        modelList[i].detachNode()
        modelList[i].removeNode()
        del modelList[i]
      numCreate = random.randint(0, 5)
      #print "creating", numCreate
      for i in xrange(numCreate):
        modelList.append(panda.copyTo( render ))
      s.update()
      gc.collect()
      gc.collect()
      print len(gc.get_objects())