import json
from src.opcodeAlias import aliases
from pathlib import Path
from src.parser import genTokens
import warnings
import logging
logger = logging.getLogger(__name__)

opcodeMap = json.load(open(Path(__file__).resolve().parent / "OpcodeMap.json"))

class scriptHandler:
    def __init__(self, spriteInput, blockIndexInput, spriteVarsInput, globalVarsInput, spriteListsInput, globalListsInput):
        self.operatorMap = {
            "*": 3,
            "/": 3,
            "+": 2,
            "-": 2
        }
        
        self.funcSignatures = {} # { funcName: { inputNames: [ inputName ], inputDataTypes: [ dataType ], inputIds: [ inputId ] } }
        self.currentFunc = None # funcName
        

        self.sprite = spriteInput
        self.blockIndex = blockIndexInput
        
        self.spriteVars = spriteVarsInput
        self.globalVars = globalVarsInput
        self.spriteLists = spriteListsInput
        self.globalLists = globalListsInput
        
        self.dependencies = []
        
        self.staticVars = []
        self.varsToBeDeleted = []

    def initAtrobutes(self, opcode, previous, index, inputName=None):
        global opcodeMap

        self.blockIndex += 1
        blockName = "block" + str(self.blockIndex)
        self.sprite["blocks"][blockName] = {
                    "opcode": opcode,
                    "next": None,
                    "parent": None,
                    "inputs": {},
                    "fields": {},
                    "shadow": False,
                    "topLevel": True
                }
        if previous == None:
            self.sprite["blocks"][blockName]["x"] = 0
            self.sprite["blocks"][blockName]["y"] = 0
        else:
            self.sprite["blocks"][blockName]["topLevel"] = False
            self.sprite["blocks"][blockName]["parent"] = previous


            # I also forgot why I didn't just delete this before, I mean it is somewhat redundant, idk
            # If it causes problems, try it I guess
            #self.sprite["blocks"][previous]["next"] = blockName

            if inputName != None and index == 0:
                self.sprite["blocks"][previous]["inputs"][inputName] = [1, blockName]
            else:
                self.sprite["blocks"][previous]["next"] = blockName

        return blockName
    
    def mendParent(self):
        return "block" + str(self.blockIndex)

    def varTypeTree(self, value, blockName, inputName):
        global opcodeMap
        
        if value in self.spriteVars:
            outputValue = [1, [12, value, self.spriteVars[value][0]]]
        elif value in self.globalVars:
            outputValue = [1, [12, value, self.globalVars[value][0]]]
        elif value in self.spriteLists:
            outputValue = [1, [13, value, self.spriteLists[value][0]]]
        elif value in self.globalLists:
            outputValue = [1, [13, value, self.globalLists[value][0]]]
        elif self.currentFunc != None and (value in self.funcSignatures[self.currentFunc]["inputNames"] or value in self.funcSignatures[self.currentFunc]["returns"]):
            if value in self.funcSignatures[self.currentFunc]["inputNames"]:
                if self.funcSignatures[self.currentFunc]["inputDataTypes"][self.funcSignatures[self.currentFunc]["inputNames"].index(value)] == "%s":
                    tempBlock = self.initAtrobutes("argument_reporter_string_number", blockName, 0, inputName)
                else:
                    tempBlock = self.initAtrobutes("argument_reporter_boolean", blockName, 0, inputName)
            else:
                if self.funcSignatures[self.currentFunc]["returnDataTypes"][self.funcSignatures[self.currentFunc]["returns"].index(value)] == "%s":
                    tempBlock = self.initAtrobutes("argument_reporter_string_number", blockName, 0, inputName)
                else:
                    tempBlock = self.initAtrobutes("argument_reporter_boolean", blockName, 0, inputName)
            self.sprite["blocks"][tempBlock]["inputs"] = {}
            self.sprite["blocks"][tempBlock]["fields"]["VALUE"] = [value, None]
            outputValue = [1, tempBlock]
        elif value in self.staticVars:
            tempblock = self.initAtrobutes("data_itemoflist", blockName, 0, inputName)
            if "value" in self.spriteLists:
                self.sprite["blocks"][tempblock]["fields"]["LIST"] = ["value", self.spriteLists["value"][0]]
            else:
                self.sprite["blocks"][tempblock]["fields"]["LIST"] = ["value", self.globalLists["value"][0]]
            secondBlock = self.initAtrobutes("data_itemnumoflist", tempblock, 0, "INDEX")
            if "key" in self.spriteLists:
                self.sprite["blocks"][secondBlock]["fields"]["LIST"] = ["key", self.spriteLists["key"][0]]
            else:
                self.sprite["blocks"][secondBlock]["fields"]["LIST"] = ["key", self.globalLists["key"][0]]
            self.sprite["blocks"][secondBlock]["inputs"]["ITEM"] = [1, [10, value]]
            outputValue = [1, tempblock]
        else:
            outputValue = [1, [10, value]]

        self.sprite["blocks"][blockName]["inputs"][inputName] = outputValue

    def solveFullList(self, expression):

        for index, item in enumerate(expression):
            if item in self.spriteLists or item in self.globalLists:
                if index + 1 < len(expression):
                    if not expression[index + 1] == "[":
                        expression.insert(index + 1, "[")
                        expression.insert(index + 2, "Whole")
                        expression.insert(index + 3, "]")
                else:
                    expression.append("[")
                    expression.append("Whole")
                    expression.append("]")

        return expression

    def itemIsSpecialFunc(self, item):
        global opcodeMap
        funcs = [
            opcodeMap,
            self.spriteLists,
            self.globalLists,
            ["len", "indexOf", "contains", "sqrt", "abs"],
            self.funcSignatures
        ]
        
        for func in funcs:
            if item in func:
                return True
            
        return False

    def itemIsFunc(self, item):
        global opcodeMap
        
        funcs = [
            self.operatorMap,
        ]

        for func in funcs:
            if self.itemIsSpecialFunc(item) or item in func:
                return True

        return False

    #thank you copilot for some trash
    def flatten_single_lists(self, obj):
        """Recursively flatten lists that contain only a single list."""
        if isinstance(obj, list):
            # Flatten lists with a single list element
            while isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], list):
                obj = obj[0]
            # Recursively process each element
            return [self.flatten_single_lists(item) for item in obj]
        return obj

    def convertParenths(self, expression):
        expression = self.flatten_single_lists(expression)
        output = []
        for item in expression:
            if isinstance(item, list):
                output += ["["] + self.convertParenths(item) + ["]"]
            else:
                output.append(item)

        return output

    def convertRPN(self, expression):
        expression = self.convertParenths(expression)
        expression = self.solveFullList(expression)

        output = []
        stack = []

        global opcodeMap

        for index, item in enumerate(expression):
            if not self.itemIsFunc(item):
                if item in ["[", "]"]:
                    if item == "[":
                        stack.append(item)
                    else:
                        while (len(stack) > 0) and (not stack[-1] == "["):
                            output.append(stack.pop())
                        stack.pop()

                        if len(stack) > 0:
                            if index + 1 < len(expression):
                                if self.itemIsSpecialFunc(stack[-1]) and not expression[index + 1] == "[":
                                    output.append(stack.pop())
                else:
                    output.append(item)
            else:
                if item in self.operatorMap:
                    if (len(stack) < 1) or (stack[-1] == "[") or (self.operatorMap[item] > self.operatorMap[stack[-1]]):
                        stack.append(item)
                    else:
                        while (len(stack) > 0) and (stack[-1] in self.operatorMap) and (self.operatorMap[item] <= self.operatorMap[stack[-1]]):
                            output.append(stack.pop())
                        stack.append(item)
                else:
                    stack.append(item)
        stack.reverse()
        return output + stack

    def createExpressionBlocks(self, expression, blockName, inputName):
        operators = {
            "*":"operator_multiply", 
            "/":"operator_divide", 
            "+":"operator_add", 
            "-":"operator_subtract"
        }

        global opcodeMap
        
        topBlock = blockName

        parent = blockName
        
        returnBlock = blockName
        
        expression = self.flatten_single_lists(expression)

        expression = self.convertRPN([expression])
        
        stack = []
        if len(expression) == 1:
            self.varTypeTree(expression[0], blockName, inputName)
        else:
            for itemIndex, item in enumerate(expression):
                if self.itemIsFunc(item):
                    if item in operators:
                        opcode = operators[item]
                    elif item in opcodeMap:
                        opcode = item
                    elif item in self.funcSignatures:
                        opcode = None
                        funcInputs = []
                        for _ in self.funcSignatures[item]["inputNames"]:
                            funcInputs.append([stack.pop()])
                        funcInputs.reverse()
                        topperBlock = self.sprite["blocks"][topBlock]["parent"]
                        tempVarName = f"temp{self.blockIndex}"
                        tempBlockName = self.callFunc("createVar", [[tempVarName], [0]], topperBlock)
                        funcInputs.append([tempVarName])
                        tempBlockName = self.callFunc(item, funcInputs, tempBlockName)
                        self.sprite["blocks"][topBlock]["parent"] = tempBlockName
                        self.sprite["blocks"][tempBlockName]["next"] = topBlock
                        stack.append(tempVarName)
                        self.staticVars.append(tempVarName)
                        if len(expression) == len(funcInputs):
                            self.varTypeTree(stack[-1], blockName, inputName)
                        returnBlock = self.callFunc("deleteVar", [[tempVarName]], returnBlock)
                        
                    elif item in self.spriteLists:
                        if stack[-1] == "Whole":
                            if len(expression) > 2:
                                if expression[itemIndex+1] == "len":
                                    opcode = None
                                    stack.pop()
                                    stack.append(item)
                                elif expression[itemIndex+2] == "indexOf":
                                    opcode = None
                                    stack.append(item)
                                else:
                                    opcode = "data_listcontents"
                            else:
                                opcode = "data_listcontents"
                        else:
                            opcode = "data_itemoflist"
                    elif item == "len":
                        opcode = "data_lengthoflist"
                    elif item == "indexOf":
                        opcode = "data_itemnumoflist"
                    elif item in ["sqrt", "abs"]:
                        opcode = "operator_mathop"
                    else:
                        opcode = "motion_movesteps"

                    if opcode != None:
                        blockName = self.initAtrobutes(opcode, parent, 0, inputName)
                        blockInputs = opcodeMap[opcode]["inputs"]

                        if item in self.spriteLists or item in self.globalLists:
                            if stack[-1] == "Whole":
                                if item in self.spriteLists:
                                    self.sprite["blocks"][blockName]["fields"][blockInputs[0]] = [item, self.spriteLists[item][0]]
                                else:
                                    self.sprite["blocks"][blockName]["fields"][blockInputs[0]] = [item, self.globalLists[item][0]]
                            else:
                                if item in self.spriteLists:
                                    self.sprite["blocks"][blockName]["fields"][blockInputs[1]] = [item, self.spriteLists[item][0]]
                                else:
                                    self.sprite["blocks"][blockName]["fields"][blockInputs[1]] = [item, self.globalLists[item][0]]
                                blockInputs = [blockInputs[0]]
                        elif item == "len":
                            if stack[-1] in self.spriteLists:
                                self.sprite["blocks"][blockName]["fields"]["LIST"] = [stack[-1], self.spriteLists[stack[-1]][0]]
                            else:
                                self.sprite["blocks"][blockName]["fields"]["LIST"] = [stack[-1], self.globalLists[stack[-1]][0]]
                        elif item == "indexOf":
                            if stack[-2] in self.spriteLists:
                                self.sprite["blocks"][blockName]["fields"]["LIST"] = [stack[-2], self.spriteLists[stack[-2]][0]]
                            else:
                                self.sprite["blocks"][blockName]["fields"]["LIST"] = [stack[-2], self.globalLists[stack[-2]][0]]
                            blockInputs = [blockInputs[0]]
                        elif item in ["sqrt", "abs"]:
                            self.sprite["blocks"][blockName]["fields"][blockInputs[0]] = [item, None]
                            blockInputs = [blockInputs[1]]
                        for index in range(-1, (len(blockInputs) + 1) * -1, -1):
                            if isinstance(stack[index], list):
                                self.sprite["blocks"][blockName]["inputs"][blockInputs[len(blockInputs) - abs(index)]] = [1, stack[index][0]]
                                self.sprite["blocks"][blockName]["parent"] = stack[index][0]
                            else:
                                self.varTypeTree(stack[index], blockName, blockInputs[len(blockInputs) - abs(index)])

                        for _ in range(len(blockInputs)):
                            stack.pop()
                        stack.append([blockName])
                else:
                    stack.append(item)
        
        return returnBlock

    def createLogicOperator(self, opcode, expression, inputs, blockName):
        blockName = self.initAtrobutes(opcode, blockName, 0, inputs[0])
        self.createExpressionBlocks(expression[0], blockName, inputs[1])
        self.createExpressionBlocks(expression[2], blockName, inputs[2])

    def executeSingleBool(self, expression, blockName, inputName):
        if self.currentFunc != None and expression[0] in self.funcSignatures[self.currentFunc]["inputNames"]:
            tempBlock = self.initAtrobutes("argument_reporter_boolean", blockName, 0, inputName)
            self.sprite["blocks"][tempBlock]["inputs"] = {}
            self.sprite["blocks"][tempBlock]["fields"]["VALUE"] = [expression, None]
            self.sprite["blocks"][blockName]["inputs"][inputName] = [1, tempBlock]
        elif expression[0] == "contains":
            midblock = self.initAtrobutes("data_listcontainsitem", blockName, 0, inputName)
            if expression[1][0] in self.spriteLists:
                self.sprite["blocks"][midblock]["fields"]["LIST"] = [expression[1][0], self.spriteLists[expression[1][0]][0]]
            else:
                self.sprite["blocks"][midblock]["fields"]["LIST"] = [expression[1][0], self.globalLists[expression[1][0]][0]]
            self.createExpressionBlocks(expression[2], midblock, "ITEM")
        else:
            match expression[1]:
                case ">":
                    self.createLogicOperator("operator_gt", expression, [inputName, "OPERAND1", "OPERAND2"], blockName)
                case "<":
                    self.createLogicOperator("operator_lt", expression, [inputName, "OPERAND1", "OPERAND2"], blockName)
                case "==":
                    self.createLogicOperator("operator_equals", expression, [inputName, "OPERAND1", "OPERAND2"], blockName)
                case ">=":
                    blockName = self.initAtrobutes("operator_or", blockName, 0, inputName)
                    midBlock = blockName
                    self.createLogicOperator("operator_gt", expression, ["OPERAND1", "OPERAND1", "OPERAND2"], midBlock)
                    self.createLogicOperator("operator_equals", expression, ["OPERAND2", "OPERAND1", "OPERAND2"], midBlock)
                case "<=":
                    blockName = self.initAtrobutes("operator_or", blockName, 0, inputName)
                    midBlock = blockName
                    self.createLogicOperator("operator_lt", expression, ["OPERAND1", "OPERAND1", "OPERAND2"], midBlock)
                    self.createLogicOperator("operator_equals", expression, ["OPERAND2", "OPERAND1", "OPERAND2"], midBlock)
                case "!=":
                    blockName = self.initAtrobutes("operator_not", blockName, 0, inputName)
                    self.createLogicOperator("operator_equals", expression, ["OPERAND", "OPERAND1", "OPERAND2"], blockName)
        
    def createBoolean(self, expression, blockName, inputName):
        self.executeSingleBool(expression, blockName, inputName)
        
                    
    def applyFuncSig(self, blockName, funcName):
        self.sprite["blocks"][blockName]["mutation"]["argumentnames"] = "[" + ",".join(["\"" + str(element) + "\"" for element in self.funcSignatures[funcName]["inputNames"] + self.funcSignatures[funcName]["returns"]]) + "]"
        self.sprite["blocks"][blockName]["mutation"]["argumentids"] = "[" + ",".join(["\"" + str(element) + "\"" for element in self.funcSignatures[funcName]["inputIds"] + self.funcSignatures[funcName]["returns"]]) + "]"
        self.sprite["blocks"][blockName]["mutation"]["argumentdefaults"] = "[" + ",".join(["\"" + "false" + "\"" if element == "%b" else "\"\"" for element in self.funcSignatures[funcName]["inputDataTypes"] + self.funcSignatures[funcName]["returnDataTypes"]]) + "]"
        self.sprite["blocks"][blockName]["mutation"]["proccode"] = funcName + " " + " ".join(self.funcSignatures[funcName]["inputDataTypes"] + self.funcSignatures[funcName]["returnDataTypes"])
        
    def requireDep(self, dep, filePath, previous):
        if not dep in self.dependencies:
            func = self.currentFunc
            blockName = previous
            file = Path(__file__).resolve().parent / "packages" / dep
            if file.exists():
                self.createBlocks(Path(__file__).resolve().parent / "placeholder.txt", [["import", f"packages/{dep}"]], None)
            else:
                file = Path(filePath).resolve().parent / dep
                if file.exists():
                    self.createBlocks(Path(filePath).resolve().parent / "placeholder.txt", [["import", dep]], None)
                else:
                    assert False, f"Dependency {dep} does not exist"
            previous = blockName
            self.currentFunc = func
            self.dependencies.append(dep)
            
        return previous
        
        
    def executeScript(self, blocks, parent, inputName):
        return self.createBlocks(None, blocks, parent, inputName)[4]
    
    def callFunc(self, funcName, inputs, parent, index=0, inputName=None):
        blockName = self.initAtrobutes("procedures_call", parent, index, inputName)
        self.sprite["blocks"][blockName]["mutation"] = {
            "tagName": "mutation", 
            "children": [], 
            "proccode": funcName + " " + " ".join([element for element in self.funcSignatures[funcName]["inputDataTypes"] + self.funcSignatures[funcName]["returnDataTypes"]]), 
            "argumentids": "[" + ",".join(["\"" + str(element) + "\"" for element in self.funcSignatures[funcName]["inputIds"] + self.funcSignatures[funcName]["returns"]]) + "]", 
            "warp": "true"
        }
        returnName = blockName

        if len(inputs[0]) != 0:
            for i in range(len(inputs)):
                if i < len(self.funcSignatures[funcName]["inputNames"]):
                    if self.funcSignatures[funcName]["inputDataTypes"][i] == "%s":
                        if self.currentFunc != None and self.funcSignatures[funcName]["inputNames"][i] == "varName" and ((not inputs[i][0] in self.funcSignatures[self.currentFunc]["inputNames"]) and (not inputs[i][0] in self.funcSignatures[self.currentFunc]["returns"])) and (not inputs[i][0] == "varName"):
                            self.sprite["blocks"][blockName]["inputs"][self.funcSignatures[funcName]["inputIds"][i]] = [1, [10, inputs[i][0]]]
                        elif self.currentFunc == None and self.funcSignatures[funcName]["inputNames"][i] == 'varName' and inputs[i][0] != "varName":
                            self.sprite["blocks"][blockName]["inputs"][self.funcSignatures[funcName]["inputIds"][i]] = [1, [10, inputs[i][0]]]
                        else:
                            returnName = self.createExpressionBlocks(inputs[i], blockName, self.funcSignatures[funcName]["inputIds"][i])
                    else:
                        self.createBoolean(self.flatten_single_lists(inputs[i]), blockName, self.funcSignatures[funcName]["inputIds"][i])
                else:
                    returnIndex = i % len(self.funcSignatures[funcName]["inputNames"])
                    if self.funcSignatures[funcName]["returnDataTypes"][returnIndex] == "%s":
                        returnName = self.createExpressionBlocks(inputs[i], blockName, self.funcSignatures[funcName]["returns"][returnIndex])
                    else:
                        self.createBoolean(self.flatten_single_lists(inputs[i]), blockName, self.funcSignatures[funcName]["returns"][returnIndex])
        return returnName

    def createBlocks(self, filePath, blocks, parent, inputName=None):
        global opcodeMap
        
        previousIf = None

        previous = parent

        for index, item in enumerate(blocks):
            logger.debug(item)
            if item[0] in opcodeMap or item[0] in aliases:

                if item[0] in aliases:
                    opcode = aliases[item[0]]
                else:
                    opcode = item[0]

                blockInfo = opcodeMap[opcode]

                blockType = blockInfo["blocktype"]

                if blockType == "hat":
                    previous = None
                    self.currentFunc = None

                blockName = self.initAtrobutes(opcode, previous, index, inputName)
                
                if opcode == "control_if":
                    previousIf = blockName
                
                returnName = blockName

                if len(blockInfo["inputs"]) > 0:
                    blockInputType = blockInfo["inputtype"]
                    blockInputs = blockInfo["inputs"]
                    for inputIndex in range(0, len(item)-1):
                        match blockInputType[inputIndex]:
                            case "dropdown":
                                if "isMenu" in blockInfo:
                                    self.sprite["blocks"][blockName]["shadow"] = True
                                else:
                                    self.sprite["blocks"][blockName]["fields"][blockInputs[inputIndex]] = [item[inputIndex+1][0], None]
                            case "menu":
                                self.createBlocks(filePath, [[blockInfo["dropdownID"], [item[inputIndex+1][0]]]], blockName, blockInputs[inputIndex])
                            case "broadcast":
                                self.sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [11, item[inputIndex+1][0]]]
                            case "color":
                                self.sprite["blocks"][blockName]["inputs"][blockInputs[inputIndex]] = [1, [9, item[inputIndex+1][0]]]
                            case "text":
                                returnName = self.createExpressionBlocks(item[inputIndex+1], blockName, blockInputs[inputIndex])
                            case "boolean":
                                if not isinstance(self.flatten_single_lists(item[inputIndex+1])[0], list
                                                  ) and (self.flatten_single_lists(item[inputIndex+1])[0] in opcodeMap or self.flatten_single_lists(item[inputIndex+1])[0] in aliases):
                                    self.createBlocks(filePath, item[inputIndex+1], blockName, blockInputs[inputIndex])
                                else:
                                    self.createBoolean(self.flatten_single_lists(item[inputIndex+1]), blockName, blockInputs[inputIndex])
                            case "substack":
                                self.createBlocks(filePath, item[inputIndex+1], blockName, blockInputs[inputIndex])

                if blockType in ["cap", "c-block cap"]:
                    previous = None
                    self.currentFunc = None
                else:
                    previous = returnName

            elif item[0] == "var":
                blockName = self.initAtrobutes("data_setvariableto", previous, index, inputName)
                self.spriteVars[item[1]] = [item[1] + str(self.blockIndex), 0]
                returnName = blockName
                if len(item) > 3:
                    returnName = self.createExpressionBlocks(item[3::], blockName, "VALUE")
                else:
                    returnName = self.createExpressionBlocks([0], blockName, "VALUE")
                self.sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[1], self.spriteVars[item[1]][0]]
                previous = returnName

            elif (item[0] in self.spriteVars) or (item[0] in self.globalVars):

                if item[1] == "=":
                    blockName = self.initAtrobutes("data_setvariableto", previous, index, inputName)
                    returnName = blockName
                    returnName = self.createExpressionBlocks(item[2::], blockName, "VALUE")

                elif item[1] == "+=":
                    blockName = self.initAtrobutes("data_changevariableby", previous, index, inputName)
                    returnName = blockName
                    returnName = self.createExpressionBlocks(item[2::], blockName, "VALUE")

                elif item[1] == "++":
                    blockName = self.initAtrobutes("data_changevariableby", previous, index, inputName)
                    returnName = blockName
                    returnName = self.createExpressionBlocks(["1"], blockName, "VALUE")

                else:
                    blockName = self.initAtrobutes("data_setvariableto", previous, index, inputName)
                    returnName = blockName
                    returnName = self.createExpressionBlocks([item[0]], blockName, "VALUE")

                if item[0] in self.spriteVars:
                    self.sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], self.spriteVars[item[0]][0]]
                else:
                    self.sprite["blocks"][blockName]["fields"]["VARIABLE"] = [item[0], self.globalVars[item[0]][0]]
                previous = returnName

            elif item[0] == "list":
                self.spriteLists[item[1]] = [item[1] + str(self.blockIndex), []]
                blockName = self.initAtrobutes("data_deletealloflist", previous, index, inputName)
                self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[1], self.spriteLists[item[1]][0]]
                previous = blockName
                if len(item) > 2:
                    if len(item[3]) != 0:
                        for expression in item[3::]:
                            blockName = self.initAtrobutes("data_addtolist", previous, index)
                            self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[1], self.spriteLists[item[1]][0]]
                            previous = self.createExpressionBlocks(expression, blockName, "ITEM")

            elif (item[0] in self.spriteLists) or (item[0] in self.globalLists):

                if item[1] == "=":
                    blockName = self.initAtrobutes("data_deletealloflist", previous, index, inputName)
                    self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], self.spriteLists[item[0]][0]]
                    previous = blockName
                    if not (len(item[2::]) == 1 and len(item[2::][0]) == 0):
                        for expression in item[2::]:
                            blockName = self.initAtrobutes("data_addtolist", previous, index)
                            self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], self.spriteLists[item[0]][0]]
                            previous = self.createExpressionBlocks(expression, blockName, "ITEM")

                elif item[1] == ".":

                    if item[2] == "push":
                        blockName = self.initAtrobutes("data_addtolist", previous, index, inputName)
                        previous = self.createExpressionBlocks(item[3], blockName, "ITEM")
                    elif item[2] == "insert":
                        blockName = self.initAtrobutes("data_insertatlist", previous, index, inputName)
                        previous = self.createExpressionBlocks(item[3], blockName, "INDEX")
                        self.createExpressionBlocks(item[4], blockName, "ITEM")
                    elif item[2] == "remove":
                        blockName = self.initAtrobutes("data_deleteoflist", previous, index, inputName)
                        previous = self.createExpressionBlocks(item[3], blockName, "INDEX")
                    else:
                        assert False, "Accessing method of list that does not exist"
                    
                    self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], self.spriteLists[item[0]][0]]
                    previous = blockName
                    
                elif isinstance(item[1], list):
                    if len(item) > 2 and item[2] == "=":
                        blockName = self.initAtrobutes("data_replaceitemoflist", previous, index, inputName)
                        self.sprite["blocks"][blockName]["fields"]["LIST"] = [item[0], self.spriteLists[item[0]][0]]
                        previous = self.createExpressionBlocks(item[1], blockName, "INDEX")
                        self.createExpressionBlocks(item[3::], blockName, "ITEM")

            elif item[0] == "static":
                self.requireDep("static.scratch", filePath, previous)
                
                self.staticVars.append(item[1])
                if self.currentFunc != None:
                    self.varsToBeDeleted.append(item[1])
                if len(item) > 2:
                    previous = self.executeScript([["createVar", [item[1]], [item[3::]]]], previous, inputName)
                else:
                    previous = self.executeScript([["createVar", [item[1]], [0]]], previous, inputName)
                    
            elif item[0] in self.staticVars:
                if item[1] == "=":
                    previous = self.executeScript([["setVar", [item[0]], [item[2::]]]], previous, inputName)
                    
                elif item[1] == "+=":
                    previous = self.executeScript([["changeVar", [item[0]], [item[2::]]]], previous, inputName)
                    
                elif item[1] == "++":
                    previous = self.executeScript([["changeVar", [item[0]], [1]]], previous, inputName)
                
            elif item[0] == "del":
                if item[1] in self.staticVars:
                    previous = self.executeScript([["deleteVar", [item[1]]]], previous, inputName)
                    self.staticVars.remove(item[1])
                
            elif item[0] == "while":
                blockName = self.initAtrobutes("control_repeat_until", previous, index, inputName)
                topBlock = blockName
                blockName = self.initAtrobutes("operator_not", blockName, 0, "CONDITION")
                self.createBoolean(self.flatten_single_lists(item[1]), blockName, "OPERAND")
                self.createBlocks(filePath, item[2], topBlock, "SUBSTACK")

                previous = topBlock

            elif item[0] == "func":
                blockName = self.initAtrobutes("procedures_definition", None, 0)
                topBlock = blockName
                blockName = self.initAtrobutes("procedures_prototype", blockName, 0, "custom_block")
                self.sprite["blocks"][blockName]["shadow"] = True
                self.sprite["blocks"][blockName]["mutation"] = {
                    "tagName": "mutation", 
                    "children": [], 
                    "proccode": item[1], 
                    "argumentids": "[]", 
                    "argumentnames": "[]", 
                    "argumentdefaults": "[", 
                    "warp": "true"
                }

                self.funcSignatures[item[1]] = { 
                    "inputNames": [], 
                    "inputDataTypes": [], 
                    "inputIds": [],
                    "returns": [],
                    "returnDataTypes": [],
                    "funcProtoName": None
                }
                self.funcSignatures[item[1]]["funcProtoName"] = blockName
                if len(item[2]) != 0:
                    for i in range(len(item)-3):
                        self.funcSignatures[item[1]]["inputNames"].append(self.flatten_single_lists(item[i+2])[0])
                        self.funcSignatures[item[1]]["inputIds"].append(str(self.flatten_single_lists(item[i+2])[0]) + str(self.blockIndex))
                        # New Tech Discovered!
                        # The stuff commented out is automatically generated by scratch!
                        if len(self.flatten_single_lists(item[i+2])) == 1 or self.flatten_single_lists(item[i+2])[1] == "text":
                            #self.sprite["blocks"][self.initAtrobutes("argument_reporter_string_number", blockName, 0, self.flatten_single_lists(item[i+2])[0])]["fields"]["VALUE"] = [self.flatten_single_lists(item[i+2])[0], None]
                            self.funcSignatures[item[1]]["inputDataTypes"].append("%s")


                        elif self.flatten_single_lists(item[i+2])[1] == "bool":
                            #self.sprite["blocks"][self.initAtrobutes("argument_reporter_boolean", blockName, 0, self.flatten_single_lists(item[i+2])[0])]["fields"]["VALUE"] = [self.flatten_single_lists(item[i+2])[0], None]
                            self.funcSignatures[item[1]]["inputDataTypes"].append("%b")

                self.applyFuncSig(blockName, item[1])

                self.currentFunc = item[1]

                previous = self.createBlocks(filePath, item[-1], topBlock)[4]
                
                for var in self.varsToBeDeleted:
                    previous = self.callFunc("deleteVar", [[var]], previous)

                previous = None

            elif item[0] in self.funcSignatures:
                previous = self.callFunc(item[0], item[1::], previous, index, inputName)
            
            elif self.currentFunc != None and item[0] == "return":
                self.funcSignatures[self.currentFunc]["returns"].append("input")
                self.funcSignatures[self.currentFunc]["returnDataTypes"].append("%s")
                self.applyFuncSig(self.funcSignatures[self.currentFunc]["funcProtoName"], self.currentFunc)
                
                self.requireDep("static.scratch", filePath, previous)
                
                previous = self.callFunc("setVar", [["input"], [item[1::]]], previous, index, inputName)

            elif item[0] == "for":
                previous = self.executeScript([item[1][0]], previous, inputName)

                blockName = self.initAtrobutes("control_repeat_until", previous, index, inputName)
                topBlock = blockName
                blockName = self.initAtrobutes("operator_not", blockName, 0, "CONDITION")
                self.createBoolean(self.flatten_single_lists(item[1][1]), blockName, "OPERAND")
                newSubstack = item[2]
                newSubstack.append(item[1][2])
                self.createBlocks(filePath, newSubstack, topBlock, "SUBSTACK")
                previous = topBlock
                if item[1][0][0] == "static":
                    previous = self.executeScript([["del", item[1][0][1]]], previous, inputName)

            elif item[0] == "import":
                parentDirectory = Path(filePath).parent
                fileCommands = genTokens(parentDirectory / item[1])
                for command in fileCommands:
                    if command[0] == "export":
                        self.createBlocks(parentDirectory / item[1], command[1], previous)
                        previous = self.mendParent()
                        
            elif item[0] == "else":
                self.sprite["blocks"][previous]["opcode"] = "control_if_else"
                self.createBlocks(filePath, item[1], previous, "SUBSTACK2")
                
            elif item[0] == "elif":
                self.sprite["blocks"][previousIf]["opcode"] = "control_if_else"
                blockName = self.initAtrobutes("control_if", previousIf, 0, "SUBSTACK2")
                self.createBoolean(item[1], blockName, "CONDITION")
                self.createBlocks(filePath, item[2], blockName, "SUBSTACK")
                previousIf = blockName
                
            elif item[0] == "require":
                previous = self.requireDep(item[1], filePath, previous)

            else:
                warnings.warn(f"Comand {item} not recognized")
                
            if previous != None and not self.sprite["blocks"][previous]["opcode"] in ["control_if", "control_if_else"] and previousIf != None:
                previousIf = None

        return self.sprite, self.blockIndex, self.spriteVars, self.spriteLists, previous
