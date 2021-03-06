__all__ = ["VTerrain", "VTextureMapMode"]
"""
Original version written by pro-rsoft
with permission to use it in the editor
"""

from pandac.PandaModules import PNMImage, GeoMipTerrain, NodePath, Texture, TextureStage, TexturePool
from pShader import ShaderWriter

# Okay, there's an issue here. The code needs a GSG instance to determine if shaders are supported.
# But, currently the terrain might already get created before theres any GSG. So, currently we're
# assuming that shasders are supported.
# We'll need to find a solution for this.

class VTextureMapMode:
  Multiply = 0
  Add = 1
  AddMinusHalf = 2
  
  @staticmethod
  def FromString(string):
    """Converts a string to a VTextureMapMode."""
    string = string.lower()
    if string == "multiply":
      return VTextureMapMode.Multiply
    elif string == "add":
      return VTextureMapMode.Add
    elif string == "addminushalf":
      return VTextureMapMode.AddMinusHalf
    else:
      raise ValueError, "Invalid value for TextureMapMode!"

class ShaderNode:
  """Represents a terrain mesh."""
  def __init__(self, parent):
    self.Root = parent
    #self.Root.reparentTo(parent)
    
    """This dictionary requires some explanation.
    Items in this dict should be like (AlphaMapPath, channel) : TexPath
    For example, if your map's settings.ini looks like this:
      AlphaMap0 = terrain-d0.png.RED
      AlphaMap1 = terrain-alphamap.png
      DetailTex0 = grass.png
      DetailTex1 = desert.jpeg
      DetailScale0 = 20.0
      DetailScale1 = 10.0 14.0
    Then the dictionary should look like:
      {(Texture("terrain-d0.png"), "r") : ("grass.png", (20.0, 20.0)),
       (Texture("terrain-alphamap.png"), "r") : "desert.jpeg", (10.0, 14.0)}
    Yes, even the greyscale maps should define a channel."""
    self.AlphaMaps = {}
    self.TextureLightMap = None # Combined
    self.LightMap = None
    self.TextureMap = None
    self.TextureMapMode = VTextureMapMode.Multiply
    self.loadedMaps = {}
  
  def SetTextureMap(self, texmap):
    """Sets the texture map."""
    if texmap == None or texmap == "": self.TextureMap = None
    if isinstance(texmap, Texture):
      self.TextureMap = texmap
    else:
      if not self.loadedMaps.has_key(texmap):
        self.loadedMaps[texmap] = loader.loadTexture(texmap)
        self.loadedMaps[texmap].reload()
      self.TextureMap = self.loadedMaps[texmap]
  
  def SetLightMap(self, texmap):
    """Sets the lightmap."""
    if texmap == None or texmap == "": self.LightMap = None
    if isinstance(texmap, Texture):
      self.LightMap = texmap
    else:
      if not self.loadedMaps.has_key(texmap):
        self.loadedMaps[texmap] = loader.loadTexture(texmap)
        self.loadedMaps[texmap].reload()
      self.LightMap = self.loadedMaps[texmap]
  
  def SetTextureLightMap(self, texmap):
    """Sets the combined texture and light map. The light map is stored
    here in the alpha channel of the texture map. If this is set, both the
    texture map and light map are ignored."""
    if texmap == None or texmap == "": self.TextureLightMap = None
    if isinstance(texmap, Texture):
      self.TextureLightMap = texmap
    else:
      if not self.loadedMaps.has_key(texmap):
        self.loadedMaps[texmap] = loader.loadTexture(texmap)
        self.loadedMaps[texmap].reload()
      self.TextureLightMap = self.loadedMaps[texmap]
  
  def AddAlphaMap(self, detailtex, alphamap, alphamapchannel = "r", texscale = (1.0, 1.0)):
    """Adds an alpha map to the AlphaMaps dictionary. Alternatively, you
    can also set the dict yourself, but no validation will be done then."""
    # Validate the input
    alphamapchannel = alphamapchannel.lower()
    assert alphamapchannel in ["r", "g", "b", "a"]
    if isinstance(texscale, float) or isinstance(texscale, int) or isinstance(texscale, long):
      texscale = (texscale, texscale)
    elif len(texscale) == 1:
      texscale = (texscale[0], texscale[0])
    if texscale == 1 or texscale == (1, 1):
      texscale = None
    if not self.loadedMaps.has_key(alphamap):
      self.loadedMaps[alphamap] = loader.loadTexture(alphamap)
      self.loadedMaps[alphamap].reload()
    alphamap = self.loadedMaps[alphamap]
    detailTex = loader.loadTexture(detailtex)
    detailTex.reload()
    self.AlphaMaps[(alphamap, alphamapchannel)] = (detailTex, texscale)
  
  def Initialize(self):
    """Initializes the terrain (generates it and calls Texture()) and
    adds the task to regenerate it."""
    self.Texture()
  
  def Texture(self):
    """Applies textures and if needed shaders to the terrain.
    Call this initially, and whenever you have changed the size of some important textures,
    or added/removed some textures or changed the lighting mode.
    This function is automatically called by Initialize()."""    
    if self.TextureMap == "": self.TextureMap = None
    if self.LightMap == "": self.LightMap = None
    
    # Does it have a detail map?
    if len(self.AlphaMaps) > 0:
      self._textureDetailed()
    elif self.TextureMap != None:
      self.Root.setTexture(self.TextureMap, 1)
      if self.LightMap != None:
        ts = TextureStage("LightMap")
        ts.setMode(TextureStage.MModulate)
        ts.setSort(2)
        self.Root.setTexture(ts, self.LightMap, 2)
    elif self.LightMap != None:
      self.Root.setTexture(ts, self.LightMap, 1)
  
  def _textureDetailed(self):
    """Internal function which textures the terrain using detail maps and detail textures, and applies shaders."""
    # Create a VShader to form a shader
    Cg = ShaderWriter()
    # Vertex program
    Cg.Vertex.AddInputs("vtx_position", "vtx_texcoord0", "mat_modelproj")
    Cg.Vertex.AddOutputs("l_texcoord0", "l_position")
    Cg.Vertex += "l_position = mul(mat_modelproj, vtx_position);"
    Cg.Vertex += "l_texcoord0 = vtx_texcoord0;"
    
    # Now the fragment program
    Cg.Fragment.AddInputs("l_texcoord0")
    Cg.Fragment.AddOutputs("o_color")
    
    TextureMapping = {}
    # Loop through the alpha maps and fill in a scale
    for (dm, chan), (tex, scale) in self.AlphaMaps.items():
      if (dm, None) not in TextureMapping.keys():
        TextureMapping[(dm, None)] = None
      if scale == 1 or scale == (1, 1): scale = None
      if (tex, scale) not in TextureMapping.keys():
        TextureMapping[(tex, scale)] = None
    
    # Add the texturelightmap, texturemap and lightmap too
    if self.TextureLightMap != None:
      if (self.TextureLightMap, None) not in TextureMapping.keys():
        TextureMapping[(self.TextureLightMap, None)] = None
    else:
      if self.TextureMap != None and (self.TextureMap, None) not in TextureMapping.keys():
        TextureMapping[(self.TextureMap, None)] = None
      if self.LightMap != None and (self.LightMap, None) not in TextureMapping.keys():
        TextureMapping[(self.LightMap, None)] = None
    
    # Now loop through these again, apply them
    for tx, scale in TextureMapping.keys():
      # Load and apply the textures
      num, ts = Cg.AddNewTextureStage(tx.getTextureType())
      self.Root.setTexture(ts, tx, -10+ts.getSort())
      TextureMapping[(tx, scale)] = num
      if scale == None or scale == 1 or scale == (1, 1):
        Cg.Fragment += "float4 tex%s = tex2D(tex_%s, l_texcoord0);" % (num, num)
      elif scale[0] == scale[1]:
        Cg.Fragment += "float4 tex%s = tex2D(tex_%s, l_texcoord0 * %f);" % (num, num, scale[0])
      else:
        Cg.Fragment += "float4 tex%s = tex2D(tex_%s, l_texcoord0 * float2(%f, %f));" % ((num, num) + (scale, ))
    
    Cg.Fragment += "o_color = float4(0.0, 0.0, 0.0, 0.0);"
    # Loop *again*, but now we're really blending
    #print self.AlphaMaps
    for (dm, chan), ts in self.AlphaMaps.items():
      dmNum = TextureMapping[(dm, None)]
      #print TextureMapping
      txNum = TextureMapping[ts]
      Cg.Fragment += "o_color += tex%d.%s * tex%d;" % (dmNum, chan, txNum)
    
    # Look whether a texture map is available
    if self.TextureLightMap != None or self.TextureMap != None:
      if self.TextureLightMap != None:
        num = TextureMapping[(self.TextureLightMap, None)]
      else:
        num = TextureMapping[(self.TextureMap, None)]
      if self.TextureMapMode == VTextureMapMode.Multiply:
        Cg.Fragment += "o_color *= tex%d;" % num
      elif self.TextureMapMode == VTextureMapMode.Add:
        Cg.Fragment += "o_color += tex%d;" % num
      elif self.TextureMapMode == VTextureMapMode.AddMinusHalf:
        Cg.Fragment += "o_color += tex%d - 0.5;" % num
      else:
        raise ValueError, "Invalid value for TextureMapMode!"
    
    # Look whether a lightmap is available
    if self.TextureLightMap != None:
      num = TextureMapping[(self.TextureLightMap, None)]
      Cg.Fragment += "o_color *= tex%d.a;" % num
    elif self.LightMap != None:
      num = TextureMapping[(self.LightMap, None)]
      Cg.Fragment += "o_color *= tex%d;" % num
    
    # Finalize, and make and apply the shader
    Cg.Fragment += "o_color.a = 1.0;"
    self.Root.setShader(Cg.Make())
  
  def destroy(self):
    print "I: ShaderNode.destroy"
    #for tex, x in TextureMapping:
    #  TexturePool.releaseTexture(tex)
    for [alphamap, alphamapchannel], [detailTex, texscale] in self.AlphaMaps.items():
      TexturePool.releaseTexture(alphamap)
      TexturePool.releaseTexture(detailTex)
    self.Root.clearShader()
    self.Root.clearTexture()

if __name__ == '__main__':
  from direct.directbase import DirectStart
  from pandac.PandaModules import *
  n = NodePath('s')
  n.reparentTo(render)
  a = ShaderNode(n)
  tex0 = 'examples/terrain-mix.png'
  tex1 = 'examples/grass.png'
  tex2 = 'examples/dirt.png'
  tex3 = 'examples/stone.png'
  #a.SetTextureMap(tex0)
  a.AddAlphaMap(tex1, tex0, alphamapchannel = "r", texscale = 5)
  a.AddAlphaMap(tex2, tex0, alphamapchannel = "g", texscale = 5)
  a.AddAlphaMap(tex3, tex0, alphamapchannel = "b", texscale = 50)
  terrain = GeoMipTerrain('test')
  terrain.setHeightfield(Filename('examples/height.png'))
#  terrainNode = terrain.getRoot()
  terrain.getRoot().reparentTo(n)
  terrain.getRoot().setSz(25)
  terrain.generate()
  a.Initialize()

  run()
