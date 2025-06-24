print("importing...")

import json
import zipfile
import hashlib
import shutil
import pathlib
import sys

from scriptHandler import createBlocks

opcodeMap = json.load(open("src/OpcodeMap.json"))

print("starting...")

extension = ".scratch"
outputFolderName = "build"

delimiters = [" "]

specialChar = [";"]

doubleChar = ["=", "+", "-", "*", "/"]

openbrackets = ["(", "{", "["]
closebrackets = [")", "}", "]"]

spriteVars = {} # { varname: [ varcode, initial value ] }
spriteLists = {}
globalVars = {}
globalLists = {}

def character_is_delimiter(line, index):
    global delimiters
    if line[index] in delimiters:
        if line[-1] != "": return True
    else:
        return False
    
def character_is_bracket(character):
    global openbrackets
    global closebrackets
    if character in closebrackets:
        return -1
    elif character in openbrackets:
        return 1
    else:
        return 0

def gen_hash(string):
    if type(string) != str:
        string = str(string)
    return hashlib.md5(string.encode()).hexdigest()

        
def createBranches():
    global index
    global lineTokens

    commands = []

    while index < len(lineTokens):
        token = lineTokens[index]
        if token in openbrackets:
            index += 1
            commands.append(createBranches())
        elif token in closebrackets:
            index += 1
            return commands
        else:
            commands.append(token)
            index += 1
    
    return commands

def parse_commands(command_list):
    def parse_block(lst):
        result : list = []
        current : list = []
        if len(lst) > 1:
            for item in lst:
                if item == ";":
                    if current:
                        result.append(current)
                    current = []
                elif isinstance(item, list):
                    parsed = parse_block(item)
                    current.append(parsed)
                else:
                    current.append(item)
            if current:
                result.append(current)
            return result
        else:
            return lst

    return parse_block(command_list)

assert len(sys.argv) > 1, "No file Selected!"

assert pathlib.Path(sys.argv[1]).exists(), f"File '{sys.argv[1]}' does not exist."

(pathlib.Path(sys.argv[1]).parent / outputFolderName).mkdir(exist_ok=True)

with open(sys.argv[1], "r") as file:
    lineTokens = [""]
    for line in file.readlines():
        isComment = False
        isString = False
        isDouble = False
        for index, character in enumerate(line):
            if character == "\"": isString = not isString
            elif isString: lineTokens[-1] += character
            elif character == "#": isComment = True
            elif character == "\n": isComment = False
            elif isComment: continue
            elif character_is_delimiter(line, index): lineTokens.append("")
            elif character in (specialChar + openbrackets + closebrackets): 
                lineTokens.append(character)
                lineTokens.append("")
            elif isDouble == True:
                if character in doubleChar:
                    lineTokens[-1] += character
                    lineTokens.append("")
                    isDouble = False
                else:
                    lineTokens.append(character)
                    isDouble = False
            elif character in doubleChar: 
                lineTokens.append(character)
                isDouble = True
            elif character == ",":
                lineTokens.append("]")
                lineTokens.append("[")
                lineTokens.append("")
            else: lineTokens[-1] += character

lineTokens = [token for token in lineTokens if token != ""]

tokenList = []
index = 0

lineTokens = createBranches()

#print(lineTokens)

output = {"targets":[], "monitors":[], "extensions":[], "meta":{
                "semver": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0"
            }
        }

filesToBeCompressed = [outputFolderName + "/project.json"]

index = 0
indent = 0
blockIndex = 1

while index < len(lineTokens):
    if lineTokens[index] == "create":
        sprite = {"isStage":True, "name":"Stage", "variables":{}, "lists":{}, 
                  "broadcasts":{}, "blocks":{}, "comments":{}, "currentCostume":0, 
                  "costumes":[], "sounds":[], "volume":100, "layerOrder":0}
        index += 1

        if lineTokens[index] == "Stage":
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
        sprite["name"] = lineTokens[index]
        index += 1

        spriteVars = {}
        spriteLists = {}

        spriteData = parse_commands(lineTokens[index])
        print(spriteData)

        for attribute in spriteData:
            if attribute[0] == "script":
                sprite, blockIndex, spriteVars, spriteLists = createBlocks(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists, attribute[1], None)
                for item, value in spriteVars.items():
                    sprite["variables"][value[0]] = [item, value[1]]
                for item, value in spriteLists.items():
                    sprite["lists"][value[0]] = [item, value[1]]
                
                if sprite["isStage"]:
                    globalVars = spriteVars
                    globalLists = spriteLists
                

            if attribute[0] == "costumes":
                for costumeName in attribute[1]:
                        costumePath = pathlib.Path(costumeName).stem
                        encodedName = hashlib.md5(costumePath.encode()).hexdigest()
                        sprite["costumes"].append(
                            {
                                "name": costumeName,
                                "bitmapResolution": 1,
                                "dataFormat": "svg",
                                "assetId": encodedName,
                                "md5ext": encodedName + ".svg",
                                "rotationCenterX": 0,
                                "rotationCenterY": 0
                            }
                        )
                        if not (outputFolderName + "/" + encodedName + ".svg") in filesToBeCompressed:
                            filesToBeCompressed.append(outputFolderName + "/" + encodedName + ".svg")
                            
                            
                            shutil.copyfile(pathlib.Path(sys.argv[1]).parent / (costumePath + ".svg"), 
                                            pathlib.Path(sys.argv[1]).parent / outputFolderName / (encodedName + ".svg"))
        
        output["targets"].append(sprite)
    elif character_is_bracket(lineTokens[index]) == -1:
        pass

    index += 1

output = json.dumps(output)
with open(pathlib.Path(sys.argv[1]).parent / outputFolderName / "project.json", "w") as file:
    file.write(output)

with zipfile.ZipFile(pathlib.Path(sys.argv[1]).parent / outputFolderName / "test.sb3", "w") as myzip:
    for file in filesToBeCompressed:
        myzip.write(pathlib.Path(sys.argv[1]).parent / file, pathlib.Path(file).name)

print("Done!")