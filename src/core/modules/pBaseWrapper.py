from pandac.PandaModules import *
from direct.gui.DirectGui import *

from core.pModelIdManager import modelIdManager
from core.pConfigDefs import *
#from lib.filebrowser import FG
#from lib.directWindow.src.directWindow import DirectWindow

class BaseWrapper( NodePath ):
  def __init__( self, name=None, parent=None ):
    print "I: BaseWrapper.__init__:", name, parent
    self.mutableParameters = {
        'posX': ['float', 'getX', 'setX']
      , 'posY': ['float', 'getY', 'setY']
      , 'posZ': ['float', 'getZ', 'setZ']
      , 'H': ['float', 'getH', 'setH']
      , 'P': ['float', 'getP', 'setP']
      , 'R': ['float', 'getR', 'setR']
      , 'scaleX': ['float', 'getSx', 'setSx']
      , 'scaleY': ['float', 'getSy', 'setSy']
      , 'scaleZ': ['float', 'getSz', 'setSz']
      , 'transparency': ['bool', 'getTransparency', 'setTransparency' ]
      , 'nodeName': ['str', 'getName', 'setName' ]
    }
    self.mutableParametersSorting = [
      'posX', 'posY', 'posZ'
    , 'H', 'P', 'R'
    , 'scaleX', 'scaleY', 'scaleZ'
    , 'transparency'
    , 'nodeName'
    ]
    self.buttonsWindow = None
    
    # get a uniq id for this object
    self.id = modelIdManager.getId()
    # define a name for this object
    if name is None:
      name = 'BaseWrapper'
    name = '%s-%s' % (name, self.id)
    NodePath.__init__( self, name )
    # store this object
    modelIdManager.setObject( self, self.id )
    # reparent this nodePath
    if parent is None:
      parent = render
    self.reparentTo( parent )
    # make this a editable object
    self.setTag( EDITABLE_OBJECT_TAG, self.id )
    self.setTag( ENABLE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
  
  def destroy( self ):
    self.detachNode()
    self.removeNode()
  
  def onCreate( self ):
    # open a file dialog
    # create a instance of NodePathWrapper
    return BaseWrapper()
  onCreate = classmethod(onCreate)
  def getSaveData( self ):
    # returns a eggGroup containing the data of this object
    pass
  
  def enableEditmode( self ):
    # enables the edit methods of this object
    # makes it pickable etc.
    # edit mode is enabled
    
    # make this a editable object
    self.setTag( EDITABLE_OBJECT_TAG, self.id )
    self.setTag( ENABLE_SCENEGRAPHBROWSER_MODEL_TAG, '' )
  def disableEditmode( self ):
    # disables the edit methods of this object
    # -> performance increase
    # edit mode is disabled
    pass
  
  def startEdit( self ):
    # the object is selected to be edited
    # creates a directFrame to edit this object
    #self.createEditWindow()
    pass
  def stopEdit( self ):
    # the object is deselected from being edited
    #self.destroyEditWindow()
    pass
  
  '''def createEditWindow( self ):
    print "I: baseWrapper.createEditWindow"
    if self.buttonsWindow is None:
      self.buttonsWindow = DirectWindow( title='%s-editWindow' % self.getName()
                                        , pos = ( .63, 0 )
                                        , maxSize = ( .8, 1 )
                                        , minSize = ( .8, 1 )
                                       )
      self.parameterEntries = dict()
      for i in xrange(len(self.mutableParametersSorting)):
        paramName = self.mutableParametersSorting[i]
        paramType, getter, setter = self.mutableParameters[paramName]
        if paramType == 'str' or paramType == 'float' or paramType == 'int':
          paramLabel = DirectLabel( text = paramName
                                  , parent = self.buttonsWindow
                                  , scale=.05
                                  , pos = (0.20, 0, .9 - i*0.1)
                                  , text_align = TextNode.ARight )
          paramEntry = DirectEntry( text = ""
                                  , scale=.05
                                  , pos = (0.25, 0, .9 - i*0.1)
                                  , parent = self.buttonsWindow
                                  , initialText="Type Something"
                                  , numLines = 1
                                  , focus=0
                                  , focusOutCommand=self.setEntry
                                  , focusOutExtraArgs=[paramName]
                                  , command=self.setEntry
                                  , extraArgs=[paramName]
                                  , text_align = TextNode.ALeft)
        else:
          paramEntry = None
        self.parameterEntries[paramName] = paramEntry
      self.updateAllEntires()
  
  def destroyEditWindow( self ):
    print "I: baseWrapper.destroyEditWindow"
    if self.buttonsWindow:
      for paramName, paramEntry in self.parameterEntries.items():
        paramType, getter, setter = self.mutableParameters[paramName]
        if paramType == 'str' or paramType == 'float' or paramType == 'int':
          paramEntry.removeNode()
          paramEntry.detachNode()
      self.buttonsWindow.removeNode()
      self.buttonsWindow.detachNode()
    self.buttonsWindow = None'''
  
  def setEntry( self, *parameters ):
    if self.buttonsWindow:
      if len(parameters) == 2:
        paramValue, paramName=parameters
      elif len(parameters) == 1:
        paramName = parameters[0]
        paramValue = self.parameterEntries[paramName].get()
      else:
        return
      paramEntry = self.parameterEntries[paramName]
      paramType, getter, setter = self.mutableParameters[paramName]
      if paramType == 'float':
        floatVal = float(paramValue)
        execCmd = 'setValue = str("%.3f")' % floatVal
        #execCmd = 'setValue = "%s" % (%s(%s))' % (paramType, paramValue)
      elif paramType == 'str':
        execCmd = 'setValue = %s' % paramValue
      elif paramType == 'int':
        execCmd = 'setValue = str(%s(%s))' % (paramType, paramValue)
      exec( execCmd )
      execCmd = 'self.%s( %s )' % (setter, setValue)
      exec( execCmd )
      
      #print "done"
      self.updateAllEntires()
  
  def updateAllEntires( self ):
    if self.buttonsWindow:
      for paramName, [paramType, getter, setter] in self.mutableParameters.items():
        if paramType == 'float':
          execCmd = 'currentValue = self.%s()' % getter
          exec( execCmd )
          currentValue = '%.3f' % currentValue
        elif paramType == 'str' or paramType == 'int':
          execCmd = 'currentValue = self.%s()' % getter
          exec( execCmd )
        else:
          currentValue = ''
        
        if paramName is not None:
          if self.parameterEntries[paramName] is not None:
            self.parameterEntries[paramName].enterText(str(currentValue))




if __name__ == '__main__':
  print "testing notdePathWrapper"
  a = BaseWrapper.onCreate( 'test2' )
  print a.name