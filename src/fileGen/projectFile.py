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
                "vm": "11.0.0-beta.2",
                "agent": "Scratch Compiler v0.3.0b"
            }
        }

        self.spriteList: list[str] = []

        self.files: list[list[Path]] = []

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

    def addBlock(self, opcode, inputs, fields, shadow, topLevel, sprite, previous=None):
        self.currentBlock += 1
        blockName = self.getBlockName()
        self.fileDict["targets"][self.getSpriteIndex(sprite)][blockName] = {
            "opcode": opcode,
            "next": None,
            "parent": previous,
            "inputs": inputs,
            "fields": fields,
            "shadow": shadow,
            "topLevel": topLevel
        }
        return self.currentBlock
    
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

        self.files.append([Path(path), Path(assetId + suffix)])
    
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

    def getBlock(self, sprite, name):
        return self.fileDict["targets"][self.getSpriteIndex(sprite)]["blocks"][name]
    