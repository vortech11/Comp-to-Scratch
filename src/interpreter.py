import json
import hashlib
import shutil
from pathlib import Path
import warnings
import logging
from PIL import Image
import xml.etree.ElementTree as ET
logger = logging.getLogger(__name__)

from src.scriptHandler import scriptHandler
from src.parser import genTokens

opcodeMap = json.load(open(Path(__file__).resolve().parent / "OpcodeMap.json"))

def gen_hash(string):
    if type(string) != str:
        string = str(string)
    return hashlib.md5(string.encode()).hexdigest()


def encodeAsset(sprite, assetType, assetInputPath, isDefault, center=None):
    global filePath
    
    if outputFolderName != None:
        assetName = Path(assetInputPath).stem
        assetExt = Path(assetInputPath).suffix
        encodedName = hashlib.md5(assetName.encode()).hexdigest()
        if assetType == "costume":
            spriteData = {
                "name": assetName,
                "dataFormat": assetExt.removeprefix("."),
                "assetId": encodedName,
                "md5ext": encodedName + assetExt,
                "rotationCenterX": 0,
                "rotationCenterY": 0
            }
            
            if center == None:
                if isDefault is True:
                    assetPath = Path(__file__).resolve().parent / "Default Assets" / assetInputPath
                else:
                    assetPath = Path(filePath).parent / assetInputPath
                    
                if assetExt == ".png":
                    with Image.open(assetPath) as img:
                        width, height = img.size
                    #spriteData["bitmapResolution"] = 4
                elif assetExt == ".svg":
                    tree = ET.parse(assetPath)
                    root = tree.getroot()
                    
                    width = root.attrib.get('width')
                    height = root.attrib.get('height')
                else:
                    width, height = (0, 0)
            else:
                width, height = center
            
            try:
                spriteData["rotationCenterX"] = float(width) / 2 if width is not None else 0
            except (ValueError, TypeError):
                spriteData["rotationCenterX"] = 0
            try:
                spriteData["rotationCenterY"] = float(height) / 2 if height is not None else 0
            except (ValueError, TypeError):
                spriteData["rotationCenterY"] = 0
            
            
            sprite["costumes"].append(spriteData)
            
        elif assetType == "sound":

            sprite["sounds"].append(
                {        
                    "name": assetName,
                    "assetId": encodedName,
                    "dataFormat": assetExt.removeprefix("."),
                    "format": "",
                    #"rate": 48000,
                    #"sampleCount": 40682,
                    "md5ext": encodedName + assetExt
                }
            )
        if not (outputFolderName + "/" + encodedName + assetExt) in filesToBeCompressed:
            filesToBeCompressed.append(outputFolderName + "/" + encodedName + assetExt)

            if isDefault:
                shutil.copyfile(Path(__file__).resolve().parent / "Default Assets" / assetInputPath, 
                                Path(filePath).parent / outputFolderName / (encodedName + assetExt))
            else:
                shutil.copyfile(Path(filePath).parent / assetInputPath, 
                                Path(filePath).parent / outputFolderName / (encodedName + assetExt))
    return sprite

def createSprite(spriteName, spriteData):
    global blockIndex
    global globalVars
    global globalLists
    
    sprite = {"isStage":True, "name":"Stage", "variables":{}, "lists":{}, 
                "broadcasts":{}, "blocks":{}, "comments":{}, "currentCostume":0, 
                "costumes":[], "sounds":[], "volume":100, "layerOrder":0}

    if spriteName == "Stage":
        sprite["tempo"] = 60
        sprite["videoTransparency"] = 50
        sprite["videoState"] = "on"
        sprite["textToSpeechLanguage"] = None
    else:
        sprite["isStage"] = False
        sprite["visible"] = True
        sprite["x"] = 0
        sprite["y"] = 0
        sprite["size"] = 100
        sprite["direction"] = 90
        sprite["draggable"] = False
        sprite["rotationStyle"] = "all around"
        sprite["layerOrder"] = 1
    sprite["name"] = spriteName

    spriteVars = {}
    spriteLists = {}
    
    costumesInit = False

    #print(spriteData)

    for attribute in spriteData:
        if attribute[0] == "script":
            sprite, blockIndex, spriteVars, spriteLists, x = scriptHandler(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists
                                                                        ).createBlocks(filePath, attribute[1], None)
            for item, value in spriteVars.items():
                sprite["variables"][value[0]] = [item, value[1]]
            for item, value in spriteLists.items():
                sprite["lists"][value[0]] = [item, value[1]]
            
            if sprite["isStage"]:
                globalVars = spriteVars
                globalLists = spriteLists
            

        if attribute[0] == "costumes":
            for costumePath in attribute[1::]:
                center = None
                if len(costumePath[0][1::]) > 0:
                    for attribute2 in costumePath[0][1::]:
                        print(costumePath[0])
                        if not (isinstance(attribute2, list) and len(attribute2) == 0):
                            if attribute2[0] == "center":
                                if attribute2[1] == "center":
                                    print("center")
                                    center = None
                                else:
                                    center = [attribute2[1][0], attribute2[2][0]]
                                    print(center)
                
                costumesInit = True
                sprite = encodeAsset(sprite, "costume", costumePath[0][0], False, center)
                
                
                        
        if attribute[0] == "sounds":
            for sound in attribute[1::]:
                sprite = encodeAsset(sprite, "sound", sound[0], False)
    
    if not costumesInit:
        sprite = encodeAsset(sprite, "costume", "blank.svg", True)
    
    return sprite

def fillCommands(filePathInput, tokens, filesToBeCompressedInput, outputFolderNameInput, blockIndexInput, globalData):
    global filesToBeCompressed
    filesToBeCompressed = filesToBeCompressedInput
    global outputFolderName
    outputFolderName = outputFolderNameInput
    global filePath
    filePath = filePathInput
    global blockIndex
    blockIndex = blockIndexInput
    global globalVars
    globalVars = globalData[0]
    global globalLists
    globalLists = globalData[1]
    
    sprites = []
    for command in tokens:
        if command[0] == "sprite":
            sprites.append(createSprite(command[1], command[2]))
        elif command[0] == "import":
            fileTokens = genTokens(Path(filePath).parent / command[1])
            importData = fillCommands(Path(Path(filePath).parent / command[1]), fileTokens, filesToBeCompressed, outputFolderName, blockIndex, [globalVars, globalLists])
            sprites.extend(importData[0])
    return (sprites, filesToBeCompressed)