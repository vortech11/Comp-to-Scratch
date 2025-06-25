import json
opcodeMap = json.load(open("src/OpcodeMap.json"))

def initAtrobutes(opcode, previous, index, inputName=None):
    global opcodeMap
    
    global blockIndex
    global sprite

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
        
        
        # I also forgot why I didn't just delete this before, I mean it is somewhat redundant, idk
        # If it causes problems, try it I guess
        #sprite["blocks"][previous]["next"] = blockName

        if inputName != None and index == 0:
            if opcodeMap[opcode]["blocktype"] == "reporter":  #I forgot why I made a distinction between these
                sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
            elif opcodeMap[opcode]["blocktype"] in ["boolean", "stack", "text"]:
                sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
        else:
            sprite["blocks"][previous]["next"] = blockName

    return blockName

def varTypeTree(value, blockName, inputName):
    global opcodeMap
    
    global sprite
    
    global spriteVars
    global globalVars
    
    global spriteLists
    global globalLists
    
    if value in spriteVars:
        outputValue = [1, [12, value, spriteVars[value][0]]]
    elif value in globalVars:
        outputValue = [1, [12, value, globalVars[value][0]]]
    elif value in spriteLists:
        outputValue = [1, [13, value, spriteLists[value][0]]]
    elif value in globalLists:
        outputValue = [1, [13, value, globalLists[value][0]]]
    else:
        outputValue = [1, [10, value]]
        
    sprite["blocks"][blockName]["inputs"][inputName] = outputValue

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
    expression = flatten_single_lists(expression)
    output = []
    for item in expression:
        if isinstance(item, list):
            output += ["["] + convertParenths(item) + ["]"]
        else:
            output.append(item)

    return output

def convertRPN(expression):
    expression = convertParenths(expression)
    print(expression)

    output = []
    stack = []
    
    global opcodeMap

    operatorMap = {
        "*": 3,
        "/": 3,
        "+": 2,
        "-": 2
    }

    for index, item in enumerate(expression):
        if not (item in operatorMap or item in opcodeMap):
            if item in ["[", "]"]:
                if item == "[":
                    stack.append(item)
                else:
                    while (len(stack) > 0) and (not stack[-1] == "["):
                        output.append(stack.pop())
                    stack.pop()
                    
                    if index + 1 < len(expression):
                        if stack[-1] in opcodeMap and not expression[index + 1] == "[":
                            output.append(stack.pop())
            else:
                output.append(item)
        else:
            if (len(stack) < 1) or (stack[-1] == "[") or (operatorMap[item] > operatorMap[stack[-1]]):
                stack.append(item)
            else:
                while (len(stack) > 0) and (stack[-1] in operatorMap) and (operatorMap[item] <= operatorMap[stack[-1]]):
                    output.append(stack.pop())
                stack.append(item)
    stack.reverse()
    return output + stack

def createExpressionBlocks(expression, blockName, inputName):
    operators = {
        "*":"operator_multiply", 
        "/":"operator_divide", 
        "+":"operator_add", 
        "-":"operator_subtract"
    }
    
    global sprite

    global opcodeMap

    parent = blockName

    expression = convertRPN(expression)
    
    print(expression)
    

    stack = []
    if len(expression) == 1:
        varTypeTree(expression[0], blockName, inputName)
    else:
        for item in expression:
            if item in operators or item in opcodeMap:
                if item in operators:
                    opcode = operators[item]
                else:
                    opcode = item
                    
                blockName = initAtrobutes(opcode, parent, 0, inputName)
                blockInputs = opcodeMap[opcode]["inputs"]
                
                for index in range(-1, (len(blockInputs) + 1) * -1, -1):
                    if isinstance(stack[index], list):
                        sprite["blocks"][blockName]["inputs"][blockInputs[abs(index) - 1]] = [1, stack[index][0]]
                        sprite["blocks"][blockName]["parent"] = stack[index][0]
                    else:
                        varTypeTree(stack[index], blockName, blockInputs[abs(index) - 1])

                for _ in range(len(blockInputs)):
                    stack.pop()
                stack.append([blockName])
            else:
                stack.append(item)

def createBlocks(spriteInput, blockIndexInput, spriteVarsInput, globalVarsInput, spriteListsInput, globalListsInput, blocks, parent, inputName=None):
    
    global sprite
    
    sprite = spriteInput
    global blockIndex
    blockIndex = blockIndexInput
    global spriteVars
    spriteVars = spriteVarsInput
    global globalVars
    globalVars = globalVarsInput
    global spriteLists
    spriteLists = spriteListsInput
    global globalLists
    globalLists = globalListsInput

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
                            createBlocks(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists, [[blockInfo["dropdownID"], [item[inputIndex+1][0]]]], blockName, blockInputs[inputIndex])
                        case "broadcast":
                            sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [11, item[inputIndex+1][0]]]
                        case "color":
                            sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [9, item[inputIndex+1][0]]]
                        case "text":
                            if isinstance(item[inputIndex+1][0], list):
                                #createBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
                                createExpressionBlocks(item[inputIndex+1][0], blockName, blockInputs[inputIndex])
                            else:
                                varTypeTree(item[inputIndex+1][0], blockName, blockInputs[inputIndex])
                        case "boolean":
                            createBlocks(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists, item[inputIndex+1], blockName, blockInputs[inputIndex])
                        case "substack":
                            createBlocks(sprite, blockIndex, spriteVars, globalVars, spriteLists, globalLists, item[inputIndex+1], blockName, blockInputs[inputIndex])
            
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
            
        elif (item[0] in spriteVars) or (item[0] in globalVars):
            
            if item[1] == "=":
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
        
        elif item[0] == "list":
            spriteLists[item[1]] = [item[1] + str(blockIndex), []]
            blockName = initAtrobutes("data_deletealloflist", previous, index)
            sprite["blocks"][blockName]["fields"]["LIST"] = [item[1], spriteLists[item[1]][0]]
            previous = blockName
            for expression in item[3::]:
                blockName = initAtrobutes("data_addtolist", previous, index)
                createExpressionBlocks(expression, blockName, "ITEM")
                sprite["blocks"][blockName]["fields"]["LIST"] = [item[1], spriteLists[item[1]][0]]
                previous = blockName
                
        elif (item[0] in spriteLists) or (item[0] in globalLists):
            
            if item[1] == "=":
                blockName = initAtrobutes("data_deletealloflist", previous, index)
                sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], spriteLists[item[0]][0]]
                previous = blockName
                if not (len(item[2::]) == 1 and len(item[2::][0])) == 0:
                    for expression in item[2::]:
                        blockName = initAtrobutes("data_addtolist", previous, index)
                        createExpressionBlocks(expression, blockName, "ITEM")
                        sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], spriteLists[item[0]][0]]
                        previous = blockName
            
            if item[1] == ".":
                
                if item[2] == "push":
                    blockName = initAtrobutes("data_addtolist", previous, index)
                    createExpressionBlocks(item[3], blockName, "ITEM")
                    sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], spriteLists[item[0]][0]]
                    previous = blockName
            
    return sprite, blockIndex, spriteVars, spriteLists
    