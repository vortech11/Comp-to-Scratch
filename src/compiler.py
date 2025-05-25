print("importing...")

import json
import zipfile
import hashlib
import shutil
import pathlib

opcodeMap = json.load(open("src/OpcodeMap.json"))

print("starting...")

extension = ".scratch"
inname = "input"
outname = "output"

delimiters = [" "]

specialChar = [";", "+", "-", "*", "/"]

openbrackets = ["(", "{", "["]
closebrackets = [")", "}", "]"]

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

def createBlocks(blocks, parent, inputName=None):
    global blockIndex
    global sprite

    global opcodeMap

    previous = parent

    for index, item in enumerate(blocks):
        if item[0] in opcodeMap:

            blockIndex += 1

            blockName = "block" + str(blockIndex)

            opcode = item[0]
            sprite["blocks"][blockName] = {
                        "opcode": opcode,
                        "next": None,
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True
                    }

            blockInfo = opcodeMap[opcode]

            blockType = blockInfo["blocktype"]

            if blockType == "hat":
                previous = None

            if previous == None:
                sprite["blocks"][blockName]["x"] = 0
                sprite["blocks"][blockName]["y"] = 0
            else:
                sprite["blocks"][blockName]["topLevel"] = False
                sprite["blocks"][blockName]["parent"] = previous

                if inputName != None and index == 0:
                    if blockType == "reporter":
                        sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
                    elif blockType in ["boolean", "stack", "text"]:
                        sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
                else:
                    sprite["blocks"][previous]["next"] = blockName

            if len(blockInfo["inputs"]) > 0:
                blockInputType = blockInfo["inputtype"]
                blockInputs = blockInfo["inputs"]
                
                for inputIndex in range(0, len(item)-1):
                    match blockInputType[inputIndex]:
                        case "dropdown":
                            if "isMenu" in blockInfo:
                                sprite["blocks"][blockName]["shadow"] = True
                            else:
                                sprite["blocks"][blockName]["fields"][blockInputs[inputIndex]] = [item[inputIndex+1][0], None]
                        case "menu":
                            createBlocks([[blockInfo["dropdownID"], [item[inputIndex+1][0]]]], blockName, blockInputs[inputIndex])
                        case "broadcast":
                            sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [11, item[inputIndex+1][0]]]
                        case "color":
                            sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [9, item[inputIndex+1][0]]]
                        case "text":
                            if isinstance(item[inputIndex+1][0], list):
                                createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
                            else:
                                sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [10, item[inputIndex+1][0]]]
                        case "boolean":
                            createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
                        case "substack":
                            createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])

            sprite["blocks"][blockName] = sprite["blocks"][blockName]
            
            if blockType in ["cap", "c-block cap"]:
                previous = None
            else:
                previous = blockName

        
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

with open("input/" + inname+extension, "r") as file:
    lineTokens = [""]
    for line in file.readlines():
        isComment = False
        isString = False
        for index, character in enumerate(line):
            if character == "\"": isString = not isString
            elif isString: lineTokens[-1] += character
            elif character == "#": isComment = True
            elif character == "\n": isComment = False
            elif isComment: continue
            elif character_is_delimiter(line, index): lineTokens.append("")
            elif character == ",":
                lineTokens.append("]")
                lineTokens.append("[")
                lineTokens.append("")
            elif character in (specialChar + openbrackets + closebrackets): 
                lineTokens.append(character)
                lineTokens.append("")
            else: lineTokens[-1] += character

lineTokens = [token for token in lineTokens if token != ""]

tokenList = []
index = 0

lineTokens = createBranches()

print(lineTokens)

output = {"targets":[], "monitors":[], "extensions":[], "meta":{
                "semver": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0"
            }
        }

filesToBeCompressed = ["output/project.json"]

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

        spriteData = parse_commands(lineTokens[index])

        for attribute in spriteData:
            if attribute[0] == "script":
                createBlocks(attribute[1], None)

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
                        if not ("output/" + encodedName + ".svg") in filesToBeCompressed:
                            filesToBeCompressed.append("output/" + encodedName + ".svg")
                            shutil.copyfile("input/" + costumePath + ".svg", "output/" + encodedName + ".svg")
        
        output["targets"].append(sprite)
    elif character_is_bracket(lineTokens[index]) == -1:
        pass

    index += 1

output = json.dumps(output)
with open("output/project.json", "w") as file:
    file.write(output)

with zipfile.ZipFile("output/test.sb3", "w") as myzip:
    for file in filesToBeCompressed:
        myzip.write(file)

print("Done!")