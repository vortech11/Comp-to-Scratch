import json
import zipfile
import hashlib
import shutil
import pathlib

print("starting...")

extension = ".scratch"
inname = "input"
outname = "output"

def character_is_delimiter(line, index):
    delimiters = [" ", ";"]
    if line[index] in delimiters:
        if line[-1] != "": return True
    else:
        return False
    
def character_is_bracket(character):
    openbrackets = ["(", "{", "["]
    closebrackets = [")", "}", "]"]
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

with open("input/" + inname+extension, "r") as file:
    lineTokens = [""]
    for line in file.readlines():
        comment = 0
        for index, character in enumerate(line):
            if character == "#": comment = 1
            elif character == "\n": comment = 0
            elif comment == 1: continue
            elif character_is_delimiter(line, index): lineTokens.append("")
            elif character_is_bracket(character) != 0: 
                if lineTokens[-1] == "": lineTokens[-1] += character
                else: lineTokens.append(character)
                lineTokens.append("")
            else: lineTokens[-1] += character

lineTokens = [token for token in lineTokens if token != ""]

output = {"targets":[], "monitors":[], "extensions":[], "meta":{
                "semver": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0"
            }
        }

filesToBeCompressed = ["output/project.json"]

index = 0
indent = 0
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
                blockIndex = 0
                index += 1
                indent += 1
                while indent > 1:
                    index += 1
                    if character_is_bracket(lineTokens[index]) != 0:
                        indent += character_is_bracket(lineTokens[index])
                    else:
                        sprite["blocks"][gen_hash(blockIndex+1)] = {
                            "opcode": lineTokens[index],
                            "next": None,
                            "parent": None,
                            "inputs": {},
                            "fields": {},
                            "shadow": False,
                            "topLevel": True,
                            "x": 0,
                            "y": 0
                        }
                        blockIndex += 1
                    
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