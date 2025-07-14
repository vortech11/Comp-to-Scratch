import json
import hashlib
import shutil
from pathlib import Path
import warnings
import logging
logger = logging.getLogger(__name__)

from src.scriptHandler import scriptHandler
from src.parser import genTokens

opcodeMap = json.load(open(Path(__file__).resolve().parent / "OpcodeMap.json"))

def gen_hash(string):
    if type(string) != str:
        string = str(string)
    return hashlib.md5(string.encode()).hexdigest()


def encodeAsset(sprite, assetType, assetPath, isDefault):
    if outputFolderName != None:
        assetName = Path(assetPath).stem
        assetExt = Path(assetPath).suffix
        encodedName = hashlib.md5(assetName.encode()).hexdigest()
        if assetType == "costume":
            sprite["costumes"].append(
                {
                    "name": assetName,
                    "bitmapResolution": 1,
                    "dataFormat": assetExt.removeprefix("."),
                    "assetId": encodedName,
                    "md5ext": encodedName + assetExt,
                    "rotationCenterX": 0,
                    "rotationCenterY": 0
                }
            )
        elif assetType == "sound":

            sprite["sounds"].append(
                {        
                    "name": assetName,
                    "assetId": encodedName,
                    "dataFormat": assetExt.removeprefix("."),
                    "format": "",
                    "rate": 48000,
                    "sampleCount": 40682,
                    "md5ext": encodedName + assetExt
                }
            )
        if not (outputFolderName + "/" + encodedName + ".svg") in filesToBeCompressed:
            filesToBeCompressed.append(outputFolderName + "/" + encodedName + ".svg")

            if isDefault:
                shutil.copyfile(Path(__file__).resolve().parent / "Default Assets" / assetPath, 
                                Path(filePath).parent / outputFolderName / (encodedName + ".svg"))
            else:
                shutil.copyfile(Path(filePath).parent / assetPath, 
                                Path(filePath).parent / outputFolderName / (encodedName + ".svg"))
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
            sprite, blockIndex, spriteVars, spriteLists = scriptHandler(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists
                                                                        ).createBlocks(filePath, attribute[1], None)
            for item, value in spriteVars.items():
                sprite["variables"][value[0]] = [item, value[1]]
            for item, value in spriteLists.items():
                sprite["lists"][value[0]] = [item, value[1]]
            
            if sprite["isStage"]:
                globalVars = spriteVars
                globalLists = spriteLists
            

        if attribute[0] == "costumes":
            for costumePath in attribute[1]:
                costumesInit = True
                sprite = encodeAsset(sprite, "costume", costumePath, False)
                
                        
        if attribute[0] == "sounds":
            for sound in attribute[1]:
                sprite = encodeAsset(sprite, "sound", sound, False)
    
    if not costumesInit:
        sprite = encodeAsset(sprite, "costume", "blank.svg", True)
    
    return sprite

def fillCommands(parentDirectory, tokens, filesToBeCompressedInput, outputFolderNameInput, filePathInput, blockIndexInput, globalData):
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
            fileTokens = genTokens(Path(parentDirectory) / command[1])
            importData = fillCommands(Path(Path(parentDirectory) / command[1]).parent, fileTokens, filesToBeCompressed, outputFolderName, filePath, blockIndex, [globalVars, globalLists])
            sprites.extend(importData[0])
    return (sprites, filesToBeCompressed)