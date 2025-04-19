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

delimiters = [" ", ";", ","]

specialChar = ["\"", "+", "-", "*", "/"]

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

def createBlock(opcode, inputs, parent):
    global blockIndex
    global sprite

    global opcodeMap

    block = {
                "opcode": opcode,
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True
            }
    
    if parent == None:
        block["x"] = 0
        block["y"] = 0
    else:
        block["topLevel"] = False
        block["parent"] = parent

        sprite["blocks"][parent]["next"] = "block" + str(blockIndex)

    blockIndex += 1

    blockInfo = opcodeMap[opcode]

    if len(inputs) != 0:
        blockInputType = blockInfo["inputtype"]
        blockInputs = blockInfo["inputs"]

        for x, inputType in enumerate(blockInputType):
            input = blockInputs[x]
            if inputType == "dropdown":
                block["fields"][input] = [inputs[x], None]
            elif inputType == "menu":
                sprite["blocks"][blockIndex + 1] = createBlock(blockInfo["dropdownID"], [inputs[x]], "block" + str(blockIndex))
                block["inputs"][input] = [1, blockIndex]
            elif inputType == "broadcast":
                block["inputs"][input] = [1, [11, inputs[x]]]
            elif inputType == "color":
                block["inputs"][input] = [1, [9, inputs[x]]]
            elif inputType == "text":
                block["inputs"][input] = [1, [10, inputs[x]]]

    return block
        


with open("input/" + inname+extension, "r") as file:
    lineTokens = [""]
    for line in file.readlines():
        comment = 0
        for index, character in enumerate(line):
            if character == "#": comment = 1
            elif character == "\n": comment = 0
            elif comment == 1: continue
            elif character_is_delimiter(line, index): lineTokens.append("")
            elif character in (specialChar + openbrackets + closebrackets): 
                if lineTokens[-1] == "": lineTokens[-1] += character
                else: lineTokens.append(character)
                lineTokens.append("")
            else: lineTokens[-1] += character

lineTokens = [token for token in lineTokens if token != ""]

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
        indent += 1

        while indent > 0:
            index += 1
            indent += character_is_bracket(lineTokens[index])
            if lineTokens[index] == "script":
                blockIndex = 1
                previousBlock = ""
                isTopLevel = True
                index += 1
                indent += 1
                while indent > 1:
                    index += 1
                    if character_is_bracket(lineTokens[index]) != 0:
                        indent += character_is_bracket(lineTokens[index])
                    else:
                        opcode = lineTokens[index]

                        blockSyntax = opcodeMap[opcode]
                        blockType = blockSyntax["blocktype"]
                        blockInputs = blockSyntax["inputs"]
  
                        if(blockType == "hat"):
                            isTopLevel = True


                        index += 2
                        inputValues = []
                        for input in blockInputs:
                            inputValues.append(lineTokens[index])
                            index += 1

                        if isTopLevel:
                            previous = None
                        else:
                            previous = "block" + str(blockIndex-1)

                        sprite["blocks"]["block" + str(blockIndex-1)] = createBlock(opcode, inputValues, previous)

                        if(blockType == "cap"):
                            isTopLevel = True
                        else:
                            isTopLevel = False
                    
            if lineTokens[index] == "costumes":
                index += 1
                indent += 1
                while indent > 1:
                    index += 1
                    if character_is_bracket(lineTokens[index]) != 0:
                        indent += character_is_bracket(lineTokens[index])
                    else:
                        costume = pathlib.Path(lineTokens[index]).stem
                        costumeName = hashlib.md5(costume.encode()).hexdigest()
                        sprite["costumes"].append(
                            {
                                "name": lineTokens[index],
                                "bitmapResolution": 1,
                                "dataFormat": "svg",
                                "assetId": costumeName,
                                "md5ext": costumeName + ".svg",
                                "rotationCenterX": 0,
                                "rotationCenterY": 0
                            }
                        )
                        filesToBeCompressed.append("output/" + costumeName + ".svg")
                        shutil.copyfile("input/" + costume + ".svg", "output/" + costumeName + ".svg")
        
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