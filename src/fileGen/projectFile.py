from hashlib import md5
from pathlib import Path

class ProjectFile:
    def __init__(self) -> None:
        self.fileDict = {
            "targets": [],
            "monitors": [],
            "extensions": [],
            "meta": {
                "semver": "3.0.0",
                "vm": "12.7.0",
                "agent": "Scratch Compiler v0.3.0b"
            }
        }

        self.spriteList: list[str] = []

        self.files: dict = {}

        self.funcs = {

        }

        self.currentBlock = 0
    
    def getBlockName(self, blockNum=None) -> str:
        if blockNum is None:
            return f"Block{self.currentBlock}"
        return f"Block{blockNum}"
    
    def genHash(self, path: str):
        #assert Path(path).exists(), f"File '{path}' does not exist."
        return md5(Path(path).name.encode()).hexdigest()
    
    def getSpriteIndex(self, name) -> int:
        return self.spriteList.index(name)
    
    def addSprite(self, name="Stage", isStage=True):
        sprite = {
            "isStage": isStage,
            "name": name,
            "variables": {},
            "lists": {},
            "broadcasts": {},
            "blocks": {},
            "comments": {},
            "currentCostume": 0,
            "costumes": [],
            "sounds": [],
            "volume": 100,
            "layerOrder": 0
        }

        if isStage:
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

        self.fileDict["targets"].append(sprite)
        self.spriteList.append(name)
        self.funcs[name] = {}

    def addBlock(self, opcode: str, inputs: dict, fields: dict, shadow: bool, sprite: str, previous=None, mendPrevious=True):
        self.currentBlock += 1
        blockName = self.getBlockName()
        if previous is None:
            topLevel = True
        else:
            topLevel = False

        if (not previous is None) and (mendPrevious is True):
            self.setBlockAttribute(sprite, previous, "next", blockName)

        block = {
            "opcode": opcode,
            "next": None,
            "parent": previous,
            "inputs": inputs,
            "fields": fields,
            "shadow": shadow,
            "topLevel": topLevel
        }

        if topLevel:
            block["x"] = 0
            block["y"] = 0

        self.fileDict["targets"][self.getSpriteIndex(sprite)]["blocks"][blockName] = block
        return blockName
    
    def setBlockAttribute(self, sprite: str, blockName: str, attribute: str, value):
        spriteIndex = self.getSpriteIndex(sprite)
        self.fileDict["targets"][spriteIndex]["blocks"][blockName][attribute] = value
    
    def addCostume(self, sprite: str, name: str, path: str, rotationCenter:tuple):
        assetId = self.genHash(path)
        suffix = Path(path).suffix
        dataFormat = suffix.removeprefix(".")

        self.fileDict["targets"][self.getSpriteIndex(sprite)]["costumes"].append(
            {
                "name": name,
                "dataFormat": dataFormat,
                "assetId": assetId,
                "md5ext": assetId + suffix,
                "rotationCenterX": rotationCenter[0],
                "rotationCenterY": rotationCenter[1]
            }
        )

        self.files[str(Path(path))] = Path(assetId + suffix)
    
    def addSound(self, sprite, name, dataFormat, rate, sampleCount):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["sounds"].append(
            {
                "name": name,
                "assetId": "",
                "dataFormat": dataFormat,
                "format": "",
                "rate": rate,
                "sampleCount": sampleCount,
                "md5ext": ""
            }
        )

    def getBlock(self, sprite: str, name: str) -> dict:
        return self.fileDict["targets"][self.getSpriteIndex(sprite)]["blocks"][name]

    def isSprite(self, name: str) -> bool:
        return name in self.spriteList

    def createVar(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"][f"{name}{self.currentBlock}"] = [name, value]

    def setVarDefault(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"][self.getVarId(sprite, name)] = [name, value]

    def createList(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"][f"{name}{self.currentBlock}"] = [name, value]

    def setListDefault(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"][self.getVarId(sprite, name)] = [name, value]

    def getVarId(self, sprite: str, name: str) -> str:
        for key, value in self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"].items():
            if value[0] == name:
                return key
        return ""
    
    def getListId(self, sprite: str, name: str) -> str:
        for key, value in self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"].items():
            if value[0] == name:
                return key
        return ""

    def isVar(self, sprite: str, name: str) -> bool:
        for _, value in self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"].items():
            if value[0] == name:
                return True
        return False
    
    def isList(self, sprite: str, name: str) -> bool:
        for _, value in self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"].items():
            if value[0] == name:
                return True
        return False

    def createFunc(self, sprite, name, proccode, parameterIdList, parameterIdText, warp):
        self.funcs[sprite][name] = {
            "proccode": proccode, 
            "parameterIdList": parameterIdList, 
            "parameterIdText": parameterIdText,
            "warp": warp
        }
    
    def doesFuncExist(self, sprite, funcName):
        return funcName in self.funcs[sprite]
    
    def getFunc(self, sprite, funcName):
        assert self.doesFuncExist(sprite, funcName)
        return self.funcs[sprite][funcName]