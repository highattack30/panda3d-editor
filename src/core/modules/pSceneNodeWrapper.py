
from core.modules.pVirtualNodeWrapper import VirtualNodeWrapper
from core.pConfigDefs import *

DEBUG = False

class SceneNodeWrapper(VirtualNodeWrapper):
  ''' this node contains a scene (so that a scene may contain other scenes)
  PROBLEM's:
  modelIdManager should be part of this node
  -> modelIdManager must be given to object when loading (not a global class)
  objects loaded from this scene should not be mutable, when loaded as subscene
  objects loaded from this scene should be mutable, when loaded as parent scene
  '''
  def onCreateInstance(self, parent, filepath):
    # create instance of this class
    name='SceneNode'
    objectInstance = super(SceneNodeWrapper, self).onCreateInstance(parent, name)
    objectInstance.setScene(filepath)
    return objectInstance
  onCreateInstance = classmethod(onCreateInstance)
  
  def __init__(self, parent, name='SceneNode'):
    self.objectInstance = None
    VirtualNodeWrapper.__init__(self, parent, name, SCENE_WRAPPER_DUMMYOBJECT) 
  
  def setScene(self, sceneFilepath):
    # load the scene
    
    def loadRecursiveChildrens(eggParentData, parent, transform, filepath, loadedObjects):
      if type(eggParentData) == EggData:
        # search the childrens
        for childData in eggParentData.getChildren():
          # search the children
          parent, loadedObjects = loadRecursiveChildrens(childData, parent, transform, filepath, loadedObjects)
      
      elif type(eggParentData) == EggGroup:
        
        # a eggGroup modifies the matrix of the model
        if type(eggParentData) == EggGroup:
          # convert the matrix from double to single
          mat4d = eggParentData.getTransform3d()
          mat4 = Mat4()
          for x in xrange(4):
              for y in xrange(4):
                  mat4.setCell(x, y, mat4d.getCell(x,y))
          # multiply the matrix for later applial onto model
          transform = mat4 * transform
        
        if eggParentData.hasTag(MODEL_WRAPPER_TYPE_TAG):
          wrapperType = eggParentData.getTag(MODEL_WRAPPER_TYPE_TAG)
          wrapperTypeDecap = wrapperType[0].lower() + wrapperType[1:]
          try:
            # import the module responsible for handling the data
            module = __import__('core.modules.p%s' % wrapperType, globals(), locals(), [wrapperType], -1)
            # load the eggParentData using the module
            object = getattr(module, wrapperType).loadFromEggGroup(eggParentData, parent, filepath)
            # append loaded object to list
            loadedObjects.append([object, eggParentData])
          except:
            print "W: EditorClass.loadEggModelsFile: unknown or invalid entry"
            traceback.print_exc()
            print "W: --- start of invalid data ---"
            print eggParentData
            print "W: --- end of invalid data ---"
            object = parent.attachNewNode('%s-failed' % wrapperType)
          if object is not None:
            # apply the transformation on the object
            object.setMat(transform)
            transform = Mat4.identMat()
            # if it contains additional childrens recurse into them
            for childData in eggParentData.getChildren()[1:]:
              # search the children
              loadRecursiveChildrens(childData, object, transform, filepath, loadedObjects)
          else:
            print "E: core.EditorClass.loadEggModelsFile: no object returned (most likely error in module)"
            print "  -", wrapperType
        else:
          # search for childrens
          for childData in eggParentData.getChildren():
            # search the children
            parent, loadedObjects = loadRecursiveChildrens(childData, parent, transform, filepath, loadedObjects)
      else:
        if DEBUG:
          print "W: EditorApp.loadEggModelsFile.loadRecursiveChildrens:"
          print "   - skipping unkown eggData", type(eggParentData)
      
      return parent, loadedObjects
    
    if sceneFilepath != None and sceneFilepath != '' and sceneFilepath != ' ':
      p3filename = Filename.fromOsSpecific(sceneFilepath)
      p3filename.makeAbsolute()
      # destroy old models
      #self.destroyAllModels()
      
      eggData = EggData()
      eggData.read(p3filename)
      
      # the absolute path of the file we load, referenced files are relative
      # to this path
      
      filepath = p3filename.getDirname()
      #filepath = str(Filename.fromOsSpecific(filepath))
      
      # add the path to the model-path
      from pandac.PandaModules import getModelPath
      getModelPath().appendPath(filepath)
      # read the eggData
      parent, loadedObjects = loadRecursiveChildrens(eggData, self, Mat4.identMat(), filepath, list())
      
      for objectInstance, eggData in loadedObjects:
        objectInstance.loadFromData( eggData, filepath )
      
      self.sceneFilepath = sceneFilepath
      
      # refresh the scenegraphbrowser
      #messenger.send(EVENT_SCENEGRAPHBROWSER_REFRESH)
  
  def enableEditmode(self):
    VirtualNodeWrapper.enableEditmode(self)
    '''if self.getCurrentOrNextState() == 'WorldEditMode':
      # enable the editing on the objects when editing is enabled
      for model in modelIdManager.getAllModels():
        try:
          model.enableEditmode()
        except:
          pass # some objects are not part of the scene (like arrows to move etc.)
      # select no model
      modelController.selectModel(None)'''
  
  def disableEditmode(self):
    VirtualNodeWrapper.disableEditmode(self)
  
  def destroy(self):
    VirtualNodeWrapper.destroy(self)
    # destroy the scene
    self.sceneFilepath
  
  def getSaveData(self, relativeTo):
    objectInstance = VirtualNodeWrapper.getSaveData(self, relativeTo)
    self.setExternalReference(self.sceneFilepath, relativeTo, objectInstance)
    return objectInstance
  
  def loadFromData(self, eggGroup, filepath):
    extRefFilename = self.getExternalReference(eggGroup, filepath)
    self.setScene(extRefFilename)
    VirtualNodeWrapper.loadFromData(self, eggGroup, filepath)
  
  def makeInstance(self, original):
    ''' make a instance of this node somewhere else '''
    objectInstance = super(SceneNodeWrapper, self).makeInstance(original)
    objectInstance.setScene(original.sceneFilepath)
    return objectInstance
  makeInstance = classmethod(makeInstance)