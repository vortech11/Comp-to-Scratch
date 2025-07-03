print("importing...")

import json
import zipfile
import hashlib
import shutil
from pathlib import Path
import sys
import warnings

from scriptHandler import createBlocks
from fileHandler import genTokens

scratchCompVersion = "0.3"

opcodeMap = json.load(open("src/OpcodeMap.json"))

print("starting...")

outputFolderName = "build"


spriteVars = {} # { varname: [ varcode, initial value ] }
spriteLists = {}
globalVars = {}
globalLists = {}


def gen_hash(string):
    if type(string) != str:
        string = str(string)
    return hashlib.md5(string.encode()).hexdigest()


def encodeAsset(assetType, assetPath, isDefault):
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
            shutil.copyfile(Path.cwd() / "src/Default Assets" / assetPath, 
                            Path(sys.argv[1]).parent / outputFolderName / (encodedName + ".svg"))
        else:
            shutil.copyfile(Path(sys.argv[1]).parent / assetPath, 
                            Path(sys.argv[1]).parent / outputFolderName / (encodedName + ".svg"))

assert len(sys.argv) > 1, "No file Selected!"

assert Path(sys.argv[1]).exists(), f"File '{sys.argv[1]}' does not exist."

(Path(sys.argv[1]).parent / outputFolderName).mkdir(exist_ok=True)

tokens = genTokens(sys.argv[1])

output = {"targets":[], "monitors":[], "extensions":[], "meta":{
                "semver": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Scratch Compiler v" + scratchCompVersion
            }
        }

filesToBeCompressed = [outputFolderName + "/project.json"]

blockIndex = 1

for command in tokens:
    if command[0] == "sprite":
        sprite = {"isStage":True, "name":"Stage", "variables":{}, "lists":{}, 
                  "broadcasts":{}, "blocks":{}, "comments":{}, "currentCostume":0, 
                  "costumes":[], "sounds":[], "volume":100, "layerOrder":0}

        if command[1] == "Stage":
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
        sprite["name"] = command[1]

        spriteVars = {}
        spriteLists = {}
        
        costumesInit = False

        spriteData = command[2]
        print(spriteData)

        for attribute in spriteData:
            if attribute[0] == "script":
                sprite, blockIndex, spriteVars, spriteLists = createBlocks(sprite, blockIndex, 
                                                                           spriteVars, globalVars, spriteLists, globalLists, 
                                                                           attribute[1], None)
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
                    encodeAsset("costume", costumePath, False)
                    
                            
            if attribute[0] == "sounds":
                for sound in attribute[1]:
                    encodeAsset("sound", sound, False)
        
        if not costumesInit:
            encodeAsset("costume", "blank.svg", True)
        
        output["targets"].append(sprite)

output = json.dumps(output)
with open(Path(sys.argv[1]).parent / outputFolderName / "project.json", "w") as file:
    file.write(output)

with zipfile.ZipFile(Path(sys.argv[1]).parent / outputFolderName / "test.sb3", "w") as myzip:
    for file in filesToBeCompressed:
        myzip.write(Path(sys.argv[1]).parent / file, Path(file).name)

print("Done!")