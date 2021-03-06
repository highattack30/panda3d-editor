__all__ = ["SceneGraphTree"]

from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import NodePath
import wx

# Local imports
from core.pModelController import modelController
from core.pModelIdManager import modelIdManager
from core.pConfigDefs import *

class SceneGraphTree(wx.TreeCtrl, DirectObject):
  """A treeview object to show the Scene Graph."""
  def __init__(self, parent):
    wx.TreeCtrl.__init__(self, parent, style = wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE | wx.SUNKEN_BORDER)
    
    # Create an imagelist and add some images
    self.imgList = wx.ImageList(16, 16)
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/properties.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/script.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/sun.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/sphere.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/mountain.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/water.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/character.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/pyramid.png").toOsSpecific()))
    #self.imgList.Add(wx.Bitmap(Filename(APP_PATH+"content/gui/light.png").toOsSpecific()))
    self.AssignImageList(self.imgList)
    self.ignoreSelChange = False
    self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelChange)
    
    self.treeRoot = None
    
    self.modelDict = {}
    self.reload()
    
    self.accept(EVENT_SCENEGRAPH_REFRESH, self.reload)
    self.accept(EVENT_MODELCONTROLLER_SELECTED_OBJECT_CHANGE, self.selectNodePath)
    self.accept(EVENT_SCENEGRAPH_CHANGE_ROOT, self.setRoot)
  
  def onSelChange(self, item):
    """This event gets invoked when the selection gets changed on the tree view."""
    if self.ignoreSelChange: return
    if not isinstance(item, wx.TreeItemId):
      item = item.GetItem()
    modelController.selectObject(self.GetItemPyData(item))
  
  def selectNodePath(self, model):
    """Selects the given NodePath in the tree."""
    if model in self.modelDict:
      treeItem = self.modelDict[model]
      self.ignoreSelChange = True
      self.SelectItem(treeItem)
      self.ignoreSelChange = False
  
  def setRoot(self, treeRoot):
    self.treeRoot = treeRoot
    self.reload()
  
  def reload(self):
    """Clears the tree view and reloads it based on the scene graph."""
    self.DeleteAllItems()
    self.modelDict.clear()
    
    if self.treeRoot is not None:
      # Create the root render node
      renderId = self.AddRoot("render")
      # render should send a pydata None (deselects all models)
      self.SetItemPyData(renderId, None)
      self.__appendChildren(renderId, self.treeRoot)
      self.modelDict[None] = renderId
      self.Expand(renderId)
      # Force a select event.
      self.onSelChange(renderId)
  
  def __appendChildren(self, treeParent, nodePath):
    """Used internally to recursively add the children of a nodepath to the scene graph browser."""
    for c in xrange(nodePath.getNumChildren()):
      childNodePath = nodePath.getChildren(c)
      childModel = modelIdManager.getObject(modelIdManager.getObjectId(childNodePath))
      #if childNodePath.hasTag(ENABLE_SCENEGRAPHBROWSER_MODEL_TAG):
      if True:
        treeItem = self.AppendItem(treeParent, childNodePath.getName())
        self.SetItemPyData(treeItem, childModel)
        self.modelDict[childNodePath] = treeItem
        # Iterate through the children
        self.__appendChildren(treeItem, childNodePath)

