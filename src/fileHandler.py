

delimiters = [" ", ":"]

specialChar = [";", "."]

inputDoubleDelimiter = [">", "<", "==", ">=", "<=", "!="]

doubleChar = ["=", "+", "-", "*", "/", ">", "<", "!"]

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

def createBoolBrackets(lineTokens):
    outTokens = []
    lastOpenBracket = None
    for item in lineTokens:
        if item in openbrackets and lastOpenBracket != "Close":
            outTokens.append("[")
            lastOpenBracket = len(outTokens)
        elif item in closebrackets and lastOpenBracket == "Close":
            outTokens.append("]")
            outTokens.append("]")
            lastOpenBracket = None
        elif item in inputDoubleDelimiter:
            if isinstance(lastOpenBracket, int):
                outTokens.insert(lastOpenBracket, "[")
                lastOpenBracket = "Close"
            outTokens.append("]")
            outTokens.append(item)
            outTokens.append("[")
        else:
            outTokens.append(item)
    
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
            startStack.pop()
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
    
    lineTokens = createBoolBrackets(lineTokens)
    brancher = branchHandler()
    lineTokens = brancher.createBranches(lineTokens)
    
    
    
    return lineTokens