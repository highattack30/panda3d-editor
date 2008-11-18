from direct.showbase.DirectObject import DirectObject
from direct.fsm.FSM import FSM
from pandac.PandaModules import *
from direct.task.Task import Task

from core.pConfigDefs import *
from core.pModelIdManager import modelIdManager
from core.pCameraController import cameraController
from core.pMouseHandler import mouseHandler

class ModelController( DirectObject ):
  def __init__( self ):
    self.__selectedModel = None
    self.__modelMode = MODEL_MODIFICATION_MODES[0]
    
    self.__selectedModel = None
    self.selectedObjectParent = None
    self.selectedObjectDistance = 0
    self.selectedObjectRelativePos = Vec3(0,0,0)
    self.__relativeModificationTo = render
    self.modelModeNode = NodePath('temp')
    
    #self.readingInputs = True
    
    self.createCollisionPicker()
    
    # create another ray which copy's the mouseray of the camera
    # using the real mouseray can cause problems
    self.mouseRayCameraNodePath = NodePath( 'editorMouseRayNodePath' )
    self.mouseRayCameraNodePath.reparentTo( base.camera )
    self.mouseRayNodePath = NodePath( 'editorMouseRayNodePath' )
    self.mouseRayNodePath.reparentTo( self.mouseRayCameraNodePath )
    
    # load axisCube, if that fails generate it and quit
    self.objectAxisCube = loader.loadModel( MODELCONTROLLER_AXISCUBE_MODEL )
    self.objectAxisCube.setTag( EXCLUDE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
    #self.objectAxisCube.reparentTo( render )
    if not self.objectAxisCube:
      print "E: axiscube.bam was missing, generating now"
      print "  - please restart the application now"
      import createAxisCube
      sys.exit()
    self.objectAxisCube.setLightOff()
    
    print "I: modelControllerClass: reading", MODEL_MODIFICATION_MODEL
    # arrows for movement and rotation
    #self.modelModificatorsNode = NodePath( 'modelModificatorsNode' )
    #self.modelModificatorsNode.setTag( EXCLUDE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
    modificatorsNode = loader.loadModel( MODEL_MODIFICATION_MODEL )
    self.modelModeNodes = list()
    for i in xrange(len(MODEL_MODIFICATION_MODES_FUNCTIONS)):
      parent = NodePath('modelModificationNode-%i' % i) # render.attachNewNode( 'modelModificationNode-%i' % i )
      #parent.hide()
      parent.setTag( EXCLUDE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
      parent.setLightOff()
      self.modelModeNodes.append( parent )
      for nameTag in MODEL_MODIFICATION_MODES_FUNCTIONS[i]:
        searchTag = '**/%s' % nameTag
        modificator = modificatorsNode.find( searchTag )
        print "  - searching", searchTag, "found", modificator
        modificator.reparentTo( parent )
        modificator.setTag( MODEL_MODIFICATOR_TAG, nameTag )
        #modificator.setTag( EXCLUDE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
        modelIdManager.setObject( modificator, nameTag )
        # arrows are hidden otherwise
        modificator.setBin("BT_unsorted", 40)
    
    self.enabled = False
  
  def toggle( self, state=None ):
    if state is None:
      state = not self.enabled
    
    if state:
      self.accept( 'mouse1', self.mouseButtonPress )
    else:
      self.ignoreAll()
  
  def mouseButtonPress( self ):
    #if self.readingInputs:
    pickedObj = self.getMouseOverNode()
    print "I: modelController.mouseButtonPress: pickedObj", pickedObj
    editModel = self.getMouseOverObjectModel(pickedObj)
    editToolSelection = self.getMouseOverObjectTool(pickedObj)
    editTool = self.getMouseOverObjectTool(pickedObj)
    if editTool:
      print "  - editTool selected", editTool
      self.editToolSetup( editTool )
    elif editModel:
      print "  - editModel selected", editModel
      self.selectModel( editModel )
    else:
      print "  - deselect"
      self.selectModel( None )
  
  def editToolSetup( self, editTool ):
    transX, transY, rotX, rotY, scaleX, scaleY = MODEL_MODIFICATION_FUNCTIONS[editTool]
    task = Task(self.editToolTask)
    
    print "I: modelController.editToolSetup:"
    print "   - selected:", self.__selectedModel
    print "   - relative:", self.__relativeModificationTo
    
    if self.__relativeModificationTo == self.__selectedModel:
      self.__modificationNode = self.__selectedModel
    else:
      # we are moving relative to some other node
      self.__origModelParent = self.__selectedModel.getParent()
      self.__modificationNode = self.__relativeModificationTo.attachNewNode( 'dummyNode' )
      self.__modificationNode.setPos( self.__selectedModel.getPos() )
      self.__selectedModel.wrtReparentTo( self.__modificationNode )
    
    taskMgr.add( task, 'editToolTask', extraArgs = [task,transX, transY, rotX, rotY, scaleX, scaleY], uponDeath=self.editToolCleanup )
    self.accept( 'mouse1-up', taskMgr.remove, ['editToolTask'] )
    mouseHandler.toggleMouseFixed( True )
  def editToolTask( self, task, transX, transY, rotX, rotY, scaleX, scaleY ):
    if task.frame: # dont run on first frame (mouse is not centered yet)
      #print "editToolTask", transX, transY, rotX, rotY, scaleX, scaleY
      mx,my = mouseHandler.getMousePos()
      dt = 0.1 #globalClock.getDt() * 10
      dPosX   = transX * mx * dt * 250
      dPosY   = transY * my * dt * 250
      dRotX   = rotX   * mx * dt * 250
      dRotY   = rotY   * my * dt * 250
      dScaleX = scaleX * mx * dt
      dScaleY = scaleY * my * dt
      
      self.__modificationNode.setPos( self.__modificationNode, dPosX )
      self.__modificationNode.setPos( self.__modificationNode, dPosY )
      self.__modificationNode.setHpr( self.__modificationNode, dRotX )
      self.__modificationNode.setHpr( self.__modificationNode, dRotY )
      self.__modificationNode.setScale( self.__modificationNode.getScale() + dScaleX )
      self.__modificationNode.setScale( self.__modificationNode.getScale() + dScaleY )
      
      self.__selectedModel.updateAllEntires()
      
      self.objectAxisCube.setScale( self.__modificationNode.getPos(render) )
    return task.cont
  def editToolCleanup( self, task ):
    # the modification node needs to be destroyed if it's not the __selectedModel
    if self.__modificationNode != self.__selectedModel:
        self.__selectedModel.wrtReparentTo( self.__origModelParent )
        self.__modificationNode.detachNode()
        self.__modificationNode.removeNode()
    
    mouseHandler.toggleMouseFixed( False )
    self.__setMode()
    self.__selectedModel.updateAllEntires()
  
  def selectNodePath( self, nodePath ):
    print "I: modelController.selectNodePath: nodePath", nodePath
    modelId = modelIdManager.getObjectId( nodePath )
#    print "modelId", modelId
    object = modelIdManager.getObject( modelId )
#    print "object", object
    self.selectModel( object )
  
  def selectModel( self, model=None ):
    print "I: modelController.selectModel", model
    if model is None:
      # no object has been selected
      print "  - deselect model"
      self.__unsetMode()
      self.__deselectModel()
      self.__selectedModel = None
    else:
      if model == self.__selectedModel:
        # the current model has been clicked again
        print "  - clicked same object again", self.__modelMode
        self.__unsetMode()
        curModelMode = MODEL_MODIFICATION_MODES.index( self.__modelMode )
        newModelMode = MODEL_MODIFICATION_MODES[(curModelMode+1) % len(MODEL_MODIFICATION_MODES)]
        self.__modelMode = newModelMode
        self.__setMode()
      else:
        # a new / different model has been clicked
        print "  - clicked new / different object"
        self.__unsetMode()
        self.__deselectModel()
        self.__selectedModel = model
        self.__modelMode = MODEL_MODIFICATION_MODES[0]
        self.__selectModel()
        self.__setMode()
  
  def getSelectedModel( self ):
    return self.__selectedModel
  
  def __selectModel( self ):
    if self.__selectedModel:
      self.__selectedModel.startEdit()
      #self.modelModificatorsNode.detachNode()
      
      self.objectAxisCube.reparentTo( render )
      self.objectAxisCube.setScale( self.__selectedModel.getPos(render) )
  
  def __deselectModel( self ):
    if self.__selectedModel:
      self.__selectedModel.stopEdit()
      #self.modelModificatorsNode.hide()
      self.objectAxisCube.detachNode()
  
  def __setMode( self ):
    if self.__selectedModel:
      if self.__modelMode == MODEL_MODIFICATION_MODE_TRANSLATE_LOCAL:
        self.modelModeNode = self.modelModeNodes[0]
        self.__relativeModificationTo = self.__selectedModel
      elif self.__modelMode == MODEL_MODIFICATION_MODE_TRANSLATE_GLOBAL:
        self.modelModeNode = self.modelModeNodes[0]
        self.__relativeModificationTo = render
      elif self.__modelMode == MODEL_MODIFICATION_MODE_ROTATE_LOCAL:
        self.modelModeNode = self.modelModeNodes[1]
        self.__relativeModificationTo = self.__selectedModel
      elif self.__modelMode == MODEL_MODIFICATION_MODE_ROTATE_GLOBAL:
        self.modelModeNode = self.modelModeNodes[1]
        self.__relativeModificationTo = render
      elif self.__modelMode == MODEL_MODIFICATION_MODE_SCALE_LOCAL:
        self.modelModeNode = self.modelModeNodes[2]
        self.__relativeModificationTo = self.__selectedModel
      elif self.__modelMode == MODEL_MODIFICATION_MODE_SCALE_GLOBAL:
        self.modelModeNode = self.modelModeNodes[2]
        self.__relativeModificationTo = render
      else:
        print "modelControllerClass.__setMode: unknown mode", self.__modelMode
      
      # get the objects radius
      try:
        r = self.__selectedModel.model.getBounds().getRadius()
      except:
        r = 1
      #print "object radius", r
      
      if False:
        #self.modelModeNode.reparentTo( render )
        # only keep the position / rotation on the model modificators
        self.modelModeNode.setMat( render, Mat4().identMat() )
        self.modelModeNode.setPos( render, self.__selectedModel.getPos(render) )
        self.modelModeNode.setHpr( render, self.__selectedModel.getHpr(self.__relativeModificationTo) )
        self.modelModeNode.setScale( render, r / 4. )
        self.modelModeNode.wrtReparentTo( self.__selectedModel )
        
        self.modelModeNode.setCollideMask( DEFAULT_EDITOR_COLLIDEMASK )
        self.modelModeNode.show()
      else:
        # the object's radius is changed when something is attached
        self.modelModeNode.detachNode()
        #r = self.__selectedModel.getBounds().getRadius()
        
        self.modelModeNode.reparentTo( render )
        self.modelModeNode.setMat( render, Mat4().identMat() ) #self.__selectedModel.getMat(render) )
        
        self.modelModeNode.setPos( render, self.__selectedModel.getPos( render ) )
        
        if self.__selectedModel == self.__relativeModificationTo:
          #print "self"
          if self.__relativeModificationTo == render:
            hpr = self.__selectedModel.getHpr()
          else:
            hpr = self.__selectedModel.getHpr( render )
        elif self.__relativeModificationTo == render:
          #print "vec3(0,0,0)"
          hpr = Vec3(0,0,0)
        #else:
          #print "parent"
          #hpr = self.__selectedModel.getHpr( render )
        self.modelModeNode.setHpr( render, hpr )
        self.modelModeNode.wrtReparentTo( self.__selectedModel )
        
        self.modelModeNode.setCollideMask( DEFAULT_EDITOR_COLLIDEMASK )
        self.modelModeNode.show()
  
  def __unsetMode( self ):
    self.modelModeNode.hide()
    self.modelModeNode.reparentTo( render )
    self.modelModeNode.setCollideMask( BitMask32.allOff() )
  
  # --- old version stuff  begin ---
  '''def startDrag( self ):
    # store object parameters
    self.selectedObjectParent = self.__selectedModel.getParent()
    self.selectedObjectDistance = self.__selectedModel.getDistance( base.camera )
    self.selectedObjectRelativePos = self.__selectedModel.getPos( base.camera ) - (self.getPickerRayDirection() * self.selectedObjectDistance)
    
    # add a movement task
    taskMgr.remove( 'editorMouseMoverTask' )
    taskMgr.add( self.mouseMoverTask, 'editorMouseMoverTask' )
    
    direction = self.getPickerRayDirection()
    self.mouseRayCameraNodePath.lookAt( Point3(direction) )
    self.mouseRayNodePath.setY( self.selectedObjectDistance )
    self.__selectedModel.wrtReparentTo( self.mouseRayNodePath )
    modelController.selectModel( self.__selectedModel )
    
    # show the cube position
    self.objectAxisCube.reparentTo( render )
    self.objectMover.reparentTo( render )
  
  def stopDrag( self ):
    self.__selectedModel.wrtReparentTo( self.selectedObjectParent )
    self.__selectedModel = None
    
    self.objectAxisCube.detachNode()
    self.objectMover.detachNode()
    
    taskMgr.remove( 'editorMouseMoverTask' )
  
  def mouseMoverTask( self, task ):
    direction = self.getPickerRayDirection()
    self.mouseRayCameraNodePath.lookAt( Point3(direction) )
    
    # scale the axisCube, to show the position of the object
    pos = self.__selectedModel.getPos( render )
    self.objectAxisCube.setScale( pos )
    self.objectMover.setPos( pos )
    #self.helpText[-1].setText( "object pos: %s" % str(pos) )
    
    return task.cont'''
  
  def createCollisionPicker( self ):
    #print "editor.editorClass.createCollisionPicker"
    self.editorCollTraverser    = CollisionTraverser()
    self.editorCollHandler      = CollisionHandlerQueue()
    self.editorPickerNode       = CollisionNode('mouseRay')
    self.editorPickerNodePath   = base.camera.attachNewNode(self.editorPickerNode)
    #self.editorPickerNodePath.show()
    self.editorPickerRay        = CollisionRay()
    self.editorPickerNode.addSolid( self.editorPickerRay )
    self.editorPickerNode.setFromCollideMask( DEFAULT_EDITOR_COLLIDEMASK )
    self.editorPickerNode.setIntoCollideMask( BitMask32.allOff() )
    self.editorCollTraverser.addCollider( self.editorPickerNodePath, self.editorCollHandler )
    
    #self.editorCollTraverser.showCollisions( render )
  
  def updatePickerRay( self ):
    #print "editor.editorClass.updatePickerRay"
    mx,my = mouseHandler.getMousePos()
    self.editorPickerRay.setFromLens(base.camNode, mx, my)
    return True
  
  def getMouseOverNode( self ):
    ''' get a object under the mouse
    '''
    if self.updatePickerRay():
      self.editorCollTraverser.traverse(render)
      #assume for simplicity's sake that myHandler is a CollisionHandlerQueue
      if self.editorCollHandler.getNumEntries() > 0:
        self.editorCollHandler.sortEntries() #this is so we get the closest object
        pickedObj=self.editorCollHandler.getEntry(0).getIntoNodePath()
        return pickedObj
    return None
  
  def getMouseOverObjectModel( self, pickedObj ):
    #print "editor.editorClass.getMouseOverObject"
    ''' get a object under the mouse
    '''
    #pickedObj = self.getMouseOverNode()
    if pickedObj:
      pickedObjTaggedParent=pickedObj.findNetTag(EDITABLE_OBJECT_TAG)
#      print "- found tag", pickedObjTaggedParent
      if not pickedObjTaggedParent.isEmpty():
        objectId = pickedObjTaggedParent.getNetTag(EDITABLE_OBJECT_TAG)
        object = modelIdManager.getObject( objectId )
#        print "- found:", objectId, object
        return object
    return None
  
  def getMouseOverObjectTool( self, pickedObj ):
    if pickedObj:
      pickedObjTaggedParent=pickedObj.findNetTag(MODEL_MODIFICATOR_TAG)
      if not pickedObjTaggedParent.isEmpty():
        objectId = pickedObjTaggedParent.getNetTag(MODEL_MODIFICATOR_TAG)
        return objectId # modelIdManager.getObject( objectId )
    return None
  
  def getPickerRayDirection( self, mousePos=None ): #posX, posY ):
    #print "editor.editorClass.getPickerRayDirection"
    ''' return the direction of the ray sent trought the mouse
    '''
    # the pickerRay cannot be changed anyway once it has been set in a frame (BUG?)
    if self.updatePickerRay():
      # get the mouse-ray direction
      direction = self.editorPickerRay.getDirection()
      mouseRayDirection = Vec3(direction.getX(), direction.getY(), direction.getZ())
      # and normalize it
      mouseRayDirection.normalize()
      return mouseRayDirection
  # --- old version stuff - end ---


modelController = ModelController()




if __name__ == '__main__':
  print "testing2"
  class dummy:
    def __init__( self, name ):
      self.name = name
    def __repr__( self ):
      return self.name
    def highlight( self, state ):
      print "highlight", self.name, state
  obj1 = dummy('a')
  obj2 = dummy('b')
  obj3 = dummy('c')
  modelController.selectModel( obj1 )
  modelController.selectModel( obj1 )
  modelController.selectModel( obj1 )
  modelController.selectModel( obj2 )
  modelController.selectModel( None )
  modelController.selectModel( obj3 )
  modelController.selectModel( obj3 )
  modelController.selectModel( None )