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

specialChar = [";"]

doubleChar = ["=", "+", "-", "*", "/"]

openbrackets = ["(", "{", "["]
closebrackets = [")", "}", "]"]


spriteVars:dict = {} # { varname: [ varcode, initial value ] }
globalVars = {}

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

#thank you copilot for some trash
def flatten_single_lists(obj):
    """Recursively flatten lists that contain only a single list."""
    if isinstance(obj, list):
        # Flatten lists with a single list element
        while isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], list):
            obj = obj[0]
        # Recursively process each element
        return [flatten_single_lists(item) for item in obj]
    return obj

def convertParenths(expression):
    print(expression)
    expression = flatten_single_lists(expression)
    print(expression)
    output = []
    for item in expression:
        if isinstance(item, list):
            output += ["["] + convertParenths(item) + ["]"]
        else:
            output.append(item)

    return output

def convertRPN(expression):
    expression = convertParenths(expression)

    output = []
    stack = []

    operatorMap = {
        "*": 3,
        "/": 3,
        "+": 2,
        "-": 2
    }

    for item in expression:
        if not item in operatorMap:
            if item in ["[", "]"]:
                if item == "[":
                    stack.append(item)
                else:
                    while (len(stack) > 0) and (not stack[-1] == "["):
                        output.append(stack.pop())
                    stack.pop()
            else:
                output.append(item)
        else:
            if (len(stack) < 1) or (stack[-1] == "[") or (operatorMap[item] > operatorMap[stack[-1]]):
                stack.append(item)
            else:
                while (len(stack) > 0) and (operatorMap[item] <= operatorMap[stack[-1]]):
                    output.append(stack.pop())
                stack.append(item)
    stack.reverse()
    return output + stack

def initAtrobutes(opcode, previous, index, inputName=None):
    global blockIndex
    global sprite
    global spriteVars
    global opcodeMap

    blockIndex += 1
    blockName = "block" + str(blockIndex)
    sprite["blocks"][blockName] = {
                "opcode": opcode,
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True
            }
    if previous == None:
        sprite["blocks"][blockName]["x"] = 0
        sprite["blocks"][blockName]["y"] = 0
    else:
        sprite["blocks"][blockName]["topLevel"] = False
        sprite["blocks"][blockName]["parent"] = previous
        
        sprite["blocks"][previous]["next"] = blockName

        if inputName != None and index == 0:
            if opcodeMap[opcode]["blocktype"] == "reporter":  #I forgot why I made a distinction between these
                sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
            elif opcodeMap[opcode]["blocktype"] in ["boolean", "stack", "text"]:
                sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
        else:
            sprite["blocks"][previous]["next"] = blockName

    return blockName

def createExpressionBlocks(expression, blockName, inputName):
    operators = {
        "*":"operator_multiply", 
        "/":"operator_divide", 
        "+":"operator_add", 
        "-":"operator_subtract"
    }

    global blockIndex
    global sprite
    global spriteVars
    global opcodeMap

    parent = blockName

    expression = convertRPN(expression)

    stack = []
    for item in expression:
        if item in operators:
            blockName = initAtrobutes(operators[item], parent, 0, inputName)
            blockInputs = opcodeMap[operators[item]]["inputs"]
            for index in [-1, -2]:
                if isinstance(stack[index], list):
                    sprite["blocks"][blockName]["inputs"][blockInputs[index]] = [1, stack[index][0]]
                    sprite["blocks"][blockName]["parent"] = stack[index][0]
                elif stack[index] in spriteVars:
                    sprite["blocks"][blockName]["inputs"][blockInputs[index]] = [1, [12, item], spriteVars[stack[index][0]][0]]
                elif stack[index] in globalVars:
                    sprite["blocks"][blockName]["inputs"][blockInputs[index]] = [1, [12, item, globalVars[stack[index]][0]]]
                else:
                    sprite["blocks"][blockName]["inputs"][blockInputs[index]] = [1, [10, stack[index]]]

            stack.pop()
            stack.pop()
            stack.append([blockName])
        else:
            stack.append(item)

def createBlocks(blocks, parent, inputName=None):
    global blockIndex
    global sprite
    global spriteVars

    global opcodeMap

    previous = parent

    for index, item in enumerate(blocks):
        if item[0] in opcodeMap:

            opcode = item[0]

            blockInfo = opcodeMap[opcode]

            blockType = blockInfo["blocktype"]

            if blockType == "hat":
                previous = None

            blockName = initAtrobutes(opcode, previous, index, inputName)

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
                                if item[inputIndex+1][0] in spriteVars:
                                    sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [12, item[inputIndex+1][0], spriteVars[item[inputIndex+1][0]][0]]]
                                elif item[inputIndex+1][0] in globalVars:
                                    sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [12, item[inputIndex+1][0], globalVars[item[inputIndex+1][0]][0]]]
                                else:
                                    sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [10, item[inputIndex+1][0]]]
                        case "boolean":
                            createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
                        case "substack":
                            createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
            
            if blockType in ["cap", "c-block cap"]:
                previous = None
            else:
                previous = blockName

        elif item[0] == "var":
            spriteVars[item[1]] = [item[1] + str(blockIndex), item[3]]

            blockName = initAtrobutes("data_setvariableto", previous, index)
            createExpressionBlocks(item[3::], blockName, "VALUE")
            sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[1], spriteVars[item[1]][0]]

            previous = blockName
        
        elif item[1] == "=":
            blockName = initAtrobutes("data_setvariableto", previous, index)

            createExpressionBlocks(item[2::], blockName, "VALUE")
            if item[0] in spriteVars:
                sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], spriteVars[item[0]][0]]
            else:
                sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], globalVars[item[0]][0]]
            previous = blockName
        
        elif item[1] == "+=":
            blockName = initAtrobutes("data_changevariableby", previous, index)
            
            createExpressionBlocks(item[2::], blockName, "VALUE")
            if item[0] in spriteVars:
                sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], spriteVars[item[0]][0]]
            else:
                sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], globalVars[item[0]][0]]
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

        spriteVars = {}

        spriteData = parse_commands(lineTokens[index])
        print(spriteData)

        for attribute in spriteData:
            if attribute[0] == "script":
                createBlocks(attribute[1], None)
                for item, value in spriteVars.items():
                    sprite["variables"][value[0]] = [item, value[1]]
                if sprite["isStage"]:
                    globalVars = spriteVars
                

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