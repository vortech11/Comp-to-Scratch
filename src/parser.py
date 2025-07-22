import logging
logger = logging.getLogger(__name__)

delimiters = [" ", ":"]

specialChar = [";", "."]

inputDoubleDelimiter = [">", "<", "==", ">=", "<=", "!="]

doubleChar = ["=", "+", "-", "*", "/", ">", "<", "!"]

openbrackets = ["(", "{", "["]
closebrackets = [")", "}", "]"]

booldelimeters = ["and", "or"]

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

def parseFile(filePath):
    with open(filePath, "r") as file:
        lineTokens = [""]
        isString = False
        for line in file.readlines():
            isComment = False
            isDouble = False
            for index, character in enumerate(line):
                if character == "\"": isString = not isString
                elif character == "#": isComment = True
                elif character == "\n": isComment = False
                elif isComment: continue
                elif isString: lineTokens[-1] += character
                elif character_is_delimiter(line, index): lineTokens.append("")
                elif character in (specialChar + openbrackets + closebrackets): 
                    lineTokens.append(character)
                    lineTokens.append("")
                    if character == "}":
                        lineTokens.append(";")
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
    
    return lineTokens

def createBoolBrackets(lineTokens, delimiter, disallow, splitBrackets):
    outTokens = []
    lastOpenBracket: list = []
    levelOfSplit = 0
    mode = None
    for index, item in enumerate(lineTokens):
        if item in openbrackets:
            if not (len(outTokens) > 2 and outTokens[-2] in disallow):
                outTokens.append("[")
                lastOpenBracket.append(len(outTokens))
        elif item in closebrackets:
            if len(lineTokens) > index + 2:
                print(lineTokens[index+2], outTokens)
            
            if not (len(lineTokens) > index + 2 and lineTokens[index+2] in disallow):
                outTokens.append("]")
                if lastOpenBracket:
                    lastOpenBracket.pop()
                #print(len(lastOpenBracket), levelOfSplit, outTokens)
                if mode == "Close" and len(lastOpenBracket) == levelOfSplit:
                    outTokens.append("]")
        elif item in delimiter:
            print(lastOpenBracket[-1])
            outTokens.insert(lastOpenBracket[-1], "[")
            mode = "Close"
            if splitBrackets:
                levelOfSplit = len(lastOpenBracket) - 1
            else:
                levelOfSplit = len(lastOpenBracket)
            
            if splitBrackets:
                outTokens.append("]")
                
            outTokens.append(item)
            
            if splitBrackets:
                outTokens.append("[")
        else:
            outTokens.append(item)
    
    return outTokens

def addBracketsForKeyword(tokens):
    outTokens = []
    for token in tokens:
        if token in booldelimeters:
            outTokens.append("]")
            outTokens.append("]")
            outTokens.append(token)
            outTokens.append("[")
            outTokens.append("[")
        else:
            outTokens.append(token)
    return outTokens

def removeBracketsForKeyword(tokens, delimeter):
    outTokens = []
    toSkipOver = False
    for token in tokens:
        if token in delimeter:
            outTokens.pop()
            outTokens.append(token)
            toSkipOver = True
        elif toSkipOver:
            toSkipOver = False
        else:
            outTokens.append(token)
    return outTokens

class branchHandler():
    def __init__(self):
        self.index = 0
    
    
    def createBranches(self, lineTokens):

        commands = []
        

        while self.index < len(lineTokens):
            token = lineTokens[self.index]
            if token in openbrackets:
                self.index += 1
                commands.append(self.createBranches(lineTokens))
            elif token in closebrackets:
                self.index += 1
                return commands
            else:
                commands.append(token)
                self.index += 1

        return commands

def split_commands(tokenList):
    outList: list = []
    startStack: list = [[0]]
    for token in tokenList:
        if token in openbrackets:
            startStack.append(len(outList))
            outList.append(token)
        elif token in closebrackets:
            index = startStack.pop()
            if isinstance(index, list) and index[0] != len(outList):
                outList.insert(index[0], "[")
                outList.append("]")
            outList.append(token)
        elif token == ";":
            if isinstance(startStack[-1], list):
                index = startStack.pop()[0]
            else:
                index = startStack.pop()
            outList.insert(index, "[")
            outList.append("]")
            startStack.append([len(outList)])
        else:
            outList.append(token)
    return outList
            

def genTokens(filePath):
    lineTokens = parseFile(filePath)

    lineTokens = [token for token in lineTokens if token != ""]
    
    lineTokens = split_commands(lineTokens)
    
    lineTokens = addBracketsForKeyword(lineTokens)
    
    lineTokens = createBoolBrackets(lineTokens, inputDoubleDelimiter, booldelimeters, True)
    
    print(lineTokens)
    
    lineTokens = removeBracketsForKeyword(lineTokens, booldelimeters)
    
    lineTokens = createBoolBrackets(lineTokens, booldelimeters, [], True)
    
    print(lineTokens)
    
    brancher = branchHandler()
    lineTokens = brancher.createBranches(lineTokens)
    
    print(lineTokens)
    
    return lineTokens