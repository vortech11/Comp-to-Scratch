from src.parser.langGrammar import *

class projectFile:
    def __init__(self) -> None:
        self.fileDict = {}
        self.currentBlock = 0
    
    def getBlockName() -> str:
        return f"Block{self.currentBlock}"
    
    def addSprite(self, name="Stage", isStage=True):
        self.fileDict[name] = {
            "isStage": isStage,
            "name": name,
            "variables": {},
            "lists": {},
            "broadcasts": {},
            "blocks": {},
            "comments": {},
            "currentCostume": 0,
            "costumes": {},
            "sounds": {},
            "volume": 100,
            "layerOrder": 1,
            "visible": True,
            "x": 0,
            "y": 0,
            "size": 100,
            "direction": 90,
            "draggable": False,
            "rotationStyle": "all around"
        }
    
    def addBlock(self, opcode, inputs, fields, shadow, topLevel, sprite, previous=None):
        self.currentBlock += 1
        blockName = self.getBlockName()
        self.fileDict[sprite][blockName] = {
            "opcode": opcode,
            "next": None,
            "parent": previous,
            "inputs": inputs,
            "fields": fields,
            "shadow": shadow,
            "topLevel": topLevel
        }
        return self.currentBlock
    
    def addCostume(self, name, dataFormat, rotationCenter:tuple):
        ...

def convertAST(AST):
    ...