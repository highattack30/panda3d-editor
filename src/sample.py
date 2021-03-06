#!/usr/bin/env python

''' sample showing the usage of the editor in scene loading
'''


from pandac.PandaModules import *

from direct.showbase.DirectObject import DirectObject


KEYBINDINGS = {
    'w': [Vec3(0,20,0), Vec3(0,0,0)],
    's': [Vec3(0,-20,0), Vec3(0,0,0)],
    'q': [Vec3(-10,0,0), Vec3(0,0,0)],
    'e': [Vec3(10,0,0), Vec3(0,0,0)],
    'a': [Vec3(0,0,0), Vec3(45,0,0)],
    'd': [Vec3(0,0,0), Vec3(-45,0,0)],
}

class Player(DirectObject):
  def __init__(self, editorInstance):
    self.terrain = modelIdManager.getObjectByName('terrain.png')[0]
    #self.terrain.terrain.getRoot().setRenderModeWireframe()
    self.playerNode = render.attachNewNode('playerPos')
    self.playerNode.setPos(0,0,0)
    self.focalPoint = self.playerNode.attachNewNode('focalPoint')
    self.focalPoint.setPos(0,100,0)
    base.camera.reparentTo(self.playerNode)
    base.camera.setPos(0,-25,50)
    base.camera.lookAt(self.playerNode, Point3(0,0,10))
    base.camLens.setFar(2000)
    taskMgr.add(self.update, 'update')
    taskMgr.doMethodLater(0.1, self.focusUpdate, 'focusupdate')
    
    self.pressedKeys = dict()
    for key in KEYBINDINGS.keys():
      self.accept(key, self.keyPress, [key, True])
      self.accept(key+"-up", self.keyPress, [key, False])
    
    self.accept('t', editorInstance.toggle)
  
  def keyPress(self, key, state):
    self.pressedKeys[key] = state
  
  def update(self, task):
    dt = globalClock.getDt()
    for key, state in self.pressedKeys.items():
      if state:
        mov, rot = KEYBINDINGS[key]
        self.playerNode.setPos(self.playerNode, mov*dt)
        self.playerNode.setHpr(self.playerNode, rot*dt)
    
    # get elevation of the player on the terrain
    elevation = self.terrain.getHeight(self.playerNode.getPos(render))
    self.playerNode.setZ( render, elevation + 3 )
    
    return task.cont
  
  def focusUpdate(self, task):
    self.terrain.cameraFocusUpdate(self.focalPoint.getPos(render))
    
    return task.again

if __name__ == '__main__':
  loadPrcFileData("", "show-frame-rate-meter #t")
  loadPrcFileData("", "sync-video #f")
  loadPrcFileData("", "audio-library-name null")
  from direct.directbase import DirectStart
  from core.pMain import *
  
  #base.disableMouse()
  
  editor = EditorClass(render, 'dgui')
  editor.loadEggModelsFile("examples/mytestscene.egs")
  #render.flattenMedium()
  
  player = Player(editor)
  
  print "all objects"
  for obj in modelIdManager.getAllObjects():
    print "  -", obj.getName()
  
  run()
