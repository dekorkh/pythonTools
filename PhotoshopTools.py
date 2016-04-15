'''
Created on Oct 21, 2011

Functions for interfacing with Photoshop.

@author: dkorkh
'''

import ctypes
import fileTools
from PIL import Image
import os
import comtypes.client
import string

CH_RED = 1
CH_GREEN = 2
CH_BLUE = 3
CH_ALPHA = 4

class PS_Session():
    def __init__(self):
        self.session = comtypes.client.CreateObject("Photoshop.Application")
        self.activeDoc = None
        self.docs = {}
    
    def open(self, fp):
        '''open the file in photoshop'''
        self.docs[fp] = self.session.Open(fp)
    
    def switchToDoc(self,fp):
        self.session.ActiveDocument = self.docs[fp]
    
    def switchToChannel(self,ch,fp):
        doc = self.switchToDoc(fp)
        doc.ActiveChannels = (doc.Channels.Item[ch],)

def connectToPS():
    """Return the photoshop COM"""
    psApp = comtypes.client.CreateObject("Photoshop.Application")
    return psApp

def openFile(filePath):
    """Open the provided file using the current Photoshop session."""
    psApp = connectToPS()
    psApp.Open(filePath)

def getTextureSize(texturePath):
    """Return a Width, Height tuple of the given texture path"""
    textureFile = Image.open(texturePath)
    size = (textureFile.size)
    del textureFile
    return size

def newTGA(texturePath,textureWidth,textureHeight,alpha=False):
    """        
    """
    
    psApp = connectToPS()
    docName = texturePath.replace("\\","/")
    docName = docName.split("/")[-1]
    newDoc = psApp.documents.add(textureWidth,textureHeight,72,docName, 2)
    if alpha:
        newDoc.channels.Add()
        chanRed = newDoc.channels.item(1)
        chanGreen = newDoc.channels.item(2)
        chanBlue = newDoc.channels.item(3)
        newDoc.ActiveChannels = (chanRed,chanGreen,chanBlue)

def transferChannel(srcDoc,targetDoc,srcChannel,targetChannel):
    """
    Transfer the channel information to a target doc.
    srcChannel & targetChannel:
    1 = r
    2 = g
    3 = b
    5,6,7... = a,a1,a2...
    """
    psApp = connectToPS()
    
    srcDocName = srcDoc.replace("\\","/").split("/")[-1]
    targetDocName = targetDoc.replace("\\","/").split("/")[-1]

    srcDocObject = getDocByName(srcDocName,psApp.documents)
    targetDocObject = getDocByName(targetDocName,psApp.documents)
    
    srcChannelObject = srcDocObject.channels.item(srcChannel)
    targetChannelObject = targetDocObject.channels.item(targetChannel)
    
    psApp.ActiveDocument = srcDocObject
    srcDocObject.ActiveChannels = (srcChannelObject,)
    
    srcDocObject.Selection.SelectAll()
    srcDocObject.Selection.Copy()
    
    selArea = srcDocObject.Selection.Bounds
    selArea = ((selArea[1],selArea[0]),\
               (selArea[1],selArea[2]),\
               (selArea[2],selArea[3]),\
               (selArea[3],selArea[0]))
    
    psApp.ActiveDocument = targetDocObject
    targetDocObject.ActiveChannels = (targetChannelObject,)
    
    psApp.ActiveDocument = targetDocObject
    targetDocObject.Selection.Select(selArea)
    targetDocObject.Paste(False)
    
    sizeRatio = getWidthRatio(targetDocObject,srcDocObject)
    offset = targetDocObject.Selection.Bounds
    offsetX = offset[0]*-1
    offsetY = offset[1]*-1
    targetDocObject.Selection.translate(offsetX,offsetY)
    targetDocObject.Selection.resize(sizeRatio,sizeRatio,1)
    
def transferChannel2(app,srcDoc,targetDoc,srcChannel,targetChannel):
    """
    Transfer the channel information to a target doc.
    srcChannel & targetChannel:
    1 = r
    2 = g
    3 = b
    5,6,7... = a,a1,a2...
    """
    
    srcChannelObject = srcDoc.channels.item(srcChannel)
    targetChannelObject = targetDoc.channels.item(targetChannel)
    
    app.ActiveDocument = srcDoc
    srcDoc.ActiveChannels = (srcChannelObject,)
    
    srcDoc.Selection.SelectAll()
    srcDoc.Selection.Copy()
    
    selArea = srcDoc.Selection.Bounds
    selArea = ((selArea[1],selArea[0]),\
               (selArea[1],selArea[2]),\
               (selArea[2],selArea[3]),\
               (selArea[3],selArea[0]))
    
    app.ActiveDocument = targetDoc
    targetDoc.ActiveChannels = (targetChannelObject,)
    
    app.ActiveDocument = targetDoc
    targetDoc.Selection.Select(selArea)
    targetDoc.Paste(False)
    
    sizeRatio = getWidthRatio(targetDoc,srcDoc)
    offset = targetDoc.Selection.Bounds
    offsetX = offset[0]*-1
    offsetY = offset[1]*-1
    targetDoc.Selection.translate(offsetX,offsetY)
    targetDoc.Selection.resize(sizeRatio,sizeRatio,1)

def getDocByName(docName,doc_collection):
    """Return the reference to the doc object."""
    for doc in doc_collection:
        if doc.name == docName:
            return doc

def getWidthRatio(docA,docB):
    """Return % ratio between the width of docA to docB"""
    widthDocA = docA.width
    widthDocB = docB.width
    widthRatio = 100*(widthDocA/(widthDocB*1.0))
    return widthRatio

def save(docPath):
    psApp = connectToPS()
    docName = docPath.replace("\\","/").split("/")[-1]
    docObject = getDocByName(docName,psApp.documents)
    psApp.ActiveDocument = docObject
    if not os.access(docPath,os.F_OK):
        docObject.saveAs(docPath)

def moveAlphaToDiffuse(patternTexture,diffuseTexture):
    psApp = connectToPS()
    
    patternDoc = psApp.Open(patternTexture)
    diffuseDoc = psApp.Open(diffuseTexture)
    
    patternSize = getTextureSize(patternTexture)
    diffuseSize = getTextureSize(diffuseTexture)
    
    #get rid of the alpha in the diffuse if one exists
    if diffuseDoc.Channels.Count > 3:
        diffuseDoc.Channels.Item(4).Delete()
    
    #Get the size ratio of of pattern to diffuse file
    widthRatio = (diffuseSize[0]*1.0)/patternSize[0]
    heightRatio = (diffuseSize[1]*1.0)/patternSize[1]
    if widthRatio-heightRatio > .001:
        print "The aspect ratio doesn't match!"
        print patternTexture
        print diffuseTexture
    
    else:
        sizeBy = widthRatio*100
    
    #copy the blue channel of the pattern map into the diffuse map alpha
    psApp.ActiveDocument = patternDoc
    blueChannel = patternDoc.Channels.Item(3)
    patternDoc.ActiveChannels = (blueChannel,)
    res = ctypes.c_double(sizeBy)
    patternDoc.Selection.SelectAll()
    patternDoc.Selection.Copy()
    
    selArea = patternDoc.Selection.Bounds
    selArea = ((selArea[1],selArea[0]),\
               (selArea[1],selArea[2]),\
               (selArea[2],selArea[3]),\
               (selArea[3],selArea[0]))
    
    psApp.ActiveDocument = diffuseDoc
    diffuseDoc.Selection.Select(selArea)
    diffuseDoc.Channels.Add()
    diffuseDoc.ActiveChannels = (diffuseDoc.Channels.Item(4),)
    diffuseDoc.Paste(False)
    #get distance offset of the pasted selection
    delta = diffuseDoc.Selection.Bounds
    deltaX = ctypes.c_double(delta[0]*-1)
    deltaY = ctypes.c_double(delta[1]*-1)

    #translate selection by distance offset
    diffuseDoc.Selection.Translate(deltaX,deltaY)
    
    #diffuseDoc.Selection.Select(selArea)
    if sizeBy != 100:
        diffuseDoc.Selection.Resize(res,res,1)
    diffuseDoc.ActiveLayer.Invert()
    

    #Set the blue channel of the pattern map to black
    psApp.ActiveDocument = patternDoc
    blueChannel = patternDoc.Channels.Item(3)
    patternDoc.ActiveChannels = (blueChannel,)
    patternDoc.Selection.SelectAll()
    zero = ctypes.c_double(0.0)
    black = psApp.ForegroundColor
    black.RGB.HexValue = "000000"
    patternDoc.Selection.Fill(black)


    patternDoc.Save()
    psApp.ActiveDocument.Close()
    psApp.ActiveDocument = diffuseDoc
    diffuseDoc.Save()
    psApp.ActiveDocument.Close()

def consolidateSpec(specularTexture):
    psApp = connectToPS()

    specDoc = psApp.Open(specularTexture)
    specDocRed = specDoc.Channels.Item(1)
    specDocGreen = specDoc.Channels.Item(2)
    specDocBlue = specDoc.Channels.Item(3)
    bgLayer = specDoc.BackgroundLayer
    
    black = psApp.ForeGroundColor
    black.RGB.HexValue = "000000"
    
    blackLayer = specDoc.ArtLayers.Add()
    specDoc.Selection.Fill(black)
    blackLayer.Visible = False
    
    blueLayer = specDoc.ArtLayers.Add()
    specDoc.ActiveLayer = bgLayer
    specDoc.ActiveChannels = (specDocBlue,)
    specDoc.Selection.SelectAll()
    specDoc.Selection.Copy()
    specDoc.ActiveLayer = blueLayer
    specDoc.Paste()
    blueLayer.BlendMode = 8
    blueLayer.Visible = False
    
    greenLayer = specDoc.ArtLayers.Add()
    specDoc.ActiveLayer = bgLayer
    specDoc.ActiveChannels = (specDocGreen,)
    specDoc.Selection.SelectAll()
    specDoc.Selection.Copy()
    specDoc.ActiveLayer = greenLayer
    specDoc.Paste()
    greenLayer.BlendMode = 8
    greenLayer.Visible = False
    
    redLayer = specDoc.ArtLayers.Add()
    specDoc.ActiveLayer = bgLayer
    specDoc.ActiveChannels = (specDocRed,)
    specDoc.Selection.SelectAll()
    specDoc.Selection.Copy()
    specDoc.ActiveLayer = redLayer
    specDoc.Paste()
    redLayer.BlendMode = 8
    redLayer.Visible = False
    
    for layer in [blackLayer,redLayer,greenLayer,blueLayer]:
        layer.Visible = True
    
    specDoc.Selection.SelectAll()
    specDoc.Selection.Copy(True)
    specDoc.Paste()
    specDoc.Flatten()
    specDoc.ActiveChannels = (specDocBlue,)
    specDoc.Selection.Fill(black)
    specDoc.ActiveChannels = (specDocGreen,)
    specDoc.Selection.Fill(black)
    specDoc.ActiveChannels = (specDocRed, specDocGreen, specDocBlue)
    
    specDoc.Save()
    psApp.ActiveDocument.Close()

def hasWhiteSpec(specularTexture):
    """Return True if the passed texture has all white specular."""
    psApp = connectToPS()
    specDoc = psApp.Open(specularTexture)
    black = psApp.ForegroundColor
    black.RGB.HexValue = "000000"
    
    redChannel = specDoc.Channels.Item(1)
    redHisto = redChannel.Histogram
    
    
    size = getTextureSize(specularTexture)
    numberOfPixels = size[0]*size[1]
    
    if redHisto[255] >= numberOfPixels:
        specDoc.ActiveChannels = (redChannel,)
        specDoc.Selection.SelectAll()
        specDoc.Selection.Fill(black)

    specDoc.Save()
    specDoc.Close()

def stripAlphaChannel(texturepath):
    psApp = connectToPS()
    tex = psApp.Open(texturepath)
    if tex.Channels.Count > 3:
        tex.Channels.Item(4).Delete()
    tex.Save()
    tex.Close()

def temp_ConvertWepTextures(d_old, c_old, n_old, d_new, c_new, s_new, nx_new):    
    psApp = connectToPS()
    d_old_doc = psApp.Open(d_old)
    c_old_doc = psApp.Open(c_old)
    n_old_doc = psApp.Open(n_old)
    
    d_new_doc = psApp.Open(d_new)
    c_new_doc = psApp.Open(c_new)
    s_new_doc = psApp.Open(s_new)
    nx_new_doc = psApp.Open(nx_new)
    
    psApp.ActiveDocument = d_new_doc
    d_new_doc.ResizeImage(d_old_doc.width, d_old_doc.height)
    psApp.ActiveDocument = s_new_doc
    s_new_doc.ResizeImage(d_old_doc.width, d_old_doc.height)
    psApp.ActiveDocument = c_new_doc
    c_new_doc.ResizeImage(c_old_doc.width, c_old_doc.height)
    psApp.ActiveDocument = nx_new_doc
    nx_new_doc.ResizeImage(n_old_doc.width, n_old_doc.height)
    
    
    psApp.ActiveDocument = d_new_doc
    if d_new_doc.channels.Count < 4:
        d_new_doc.channels.Add()
    psApp.ActiveDocument = c_new_doc
    if c_new_doc.channels.Count < 4:
        c_new_doc.channels.Add()
    psApp.ActiveDocument = s_new_doc
    if s_new_doc.channels.Count < 4:
        s_new_doc.channels.Add()
    psApp.ActiveDocument = nx_new_doc
    if nx_new_doc.channels.Count > 3:
        nx_new_doc.channels.Item(4).Delete()

    black = psApp.ForegroundColor
    white = psApp.ForegroundColor
    black.RGB.HexValue = "000000"
    white.RGB.HexValue = "FFFFFF"
    for doc in [d_new_doc, c_new_doc, s_new_doc, nx_new_doc]:
        psApp.ActiveDocument = doc
        doc.Selection.SelectAll()
        for i in range(doc.channels.Count):
            channel = doc.channels.Item(i + 1)
            doc.ActiveChannels = (channel,)
            doc.Selection.Fill(black)
    
    psApp.ActiveDocument = d_new_doc
    d_new_doc.ActiveChannels = (d_new_doc.channels.Item(4),)
    d_new_doc.Selection.Fill(white)
            
    transferChannel2(psApp, d_old_doc, d_new_doc, 1, 1)
    transferChannel2(psApp, d_old_doc, d_new_doc, 2, 2)
    transferChannel2(psApp, d_old_doc, d_new_doc, 3, 3)
    transferChannel2(psApp, c_old_doc, d_new_doc, 3, 4)
    if d_old_doc.channels.Count > 3:
        transferChannel2(psApp, d_old_doc, s_new_doc, 4, 1)
        transferChannel2(psApp, d_old_doc, s_new_doc, 4, 4)
    transferChannel2(psApp, c_old_doc, c_new_doc, 1, 1)
    transferChannel2(psApp, c_old_doc, c_new_doc, 2, 2)
    if c_old_doc.channels.Count > 3:
        transferChannel2(psApp, c_old_doc, c_new_doc, 4, 4)
    transferChannel2(psApp, n_old_doc, nx_new_doc, 1, 1)
    transferChannel2(psApp, n_old_doc, nx_new_doc, 2, 2)
    transferChannel2(psApp, n_old_doc, nx_new_doc, 3, 3)
    
    psApp.ActiveDocument = d_new_doc
    d_new_doc.Save()
    d_new_doc.Close()
    psApp.ActiveDocument = c_new_doc
    c_new_doc.Save()
    c_new_doc.Close()
    psApp.ActiveDocument = s_new_doc
    s_new_doc.Save()
    s_new_doc.Close()
    psApp.ActiveDocument = nx_new_doc
    nx_new_doc.Save()
    nx_new_doc.Close()
    psApp.ActiveDocument = d_old_doc
    d_old_doc.Close()
    psApp.ActiveDocument = c_old_doc
    c_old_doc.Close()
    psApp.ActiveDocument = n_old_doc
    n_old_doc.Close()

def invertAlpha(texturePath):
    psApp = connectToPS()
    doc = psApp.Open(texturePath)
    alpha = doc.channels.Item(4)
    doc.ActiveChannels = (alpha,)
    doc.ActiveLayer.Invert()
    doc.Save()
    doc.Close()

if __name__=="__main__":
    
    #sourceTex = "C:/Night/src/texture_library/Weapons/Dagger/Weap_Dagger_Tier02a_Gothic_01_Blade_D.tga"
    #targetTex = "c:/deniskorkh/temp/newDoc2.tga"
    #newTGA(targetTex,600,600,True)
    #save(targetTex)
    #width, height = getTextureSize(sourceTex)
    #newTGA(targetTex,width*2,height*2,True)
    #openFile(sourceTex)
    #transferChannel(sourceTex,targetTex,1,3)
    
    """
    specularTexture = "C:/Night/src/texture_library/Costumes/Avatars/BodySlot/C_Bodyslot_Scale_T3_01_S.tga"
    
    hasWhiteSpec(specularTexture)
    """
    
    """
    patternDoc.Save()
    psApp.ActiveDocument.Close()
    psApp.ActiveDocument = diffuseDoc
    diffuseDoc.Save()
    psApp.ActiveDocument.Close()"""
    
    """
    patternDoc.Selection.SelectAll()
    print patternDoc.Channels.Count
    redChannel = patternDoc.Channels.Item(1)
    greenChannel = patternDoc.Channels.Item(2)
    blueChannel = patternDoc.Channels.Item(3)
    patternDoc.ActiveChannels = (redChannel,)
    res = ctypes.c_double(200.0)
    patternDoc.ActiveLayer.Resize(res,res,1)
    """

    