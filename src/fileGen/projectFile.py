from hashlib import md5
from pathlib import Path

class ProjectFile:
    def __init__(self) -> None:
        self.fileDict = {
            "targets": {},
            "monitors": [],
            "extensions": [],
            "meta": {
                "server": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Scratch Compiler v0.3.0b"
            }
        }

        self.files: list[list[Path]] = []

        self.currentBlock = 0
    
    def getBlockName(self, blockNum=None) -> str:
        if blockNum is None:
            return f"Block{self.currentBlock}"
        return f"Block{blockNum}"
    
    def genHash(self, path: str):
        #assert Path(path).exists(), f"File '{path}' does not exist."
        return md5(Path(path).name.encode()).hexdigest()
    
    def addSprite(self, name="Stage", isStage=True):
        self.fileDict["targets"][name] = {
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
        self.fileDict["targets"][sprite][blockName] = {
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

        self.fileDict["targets"][sprite]["costumes"].append(
            {
                "name": name,
                "dataFormat": dataFormat,
                "assetId": assetId,
                "md5ext": assetId + dataFormat,
                "rotationCenterX": rotationCenter[0],
                "rotationCenterY": rotationCenter[1]
            }
        )

        self.files.append([Path(path), Path(assetId + suffix)])
    
    def addSound(self, sprite, name, dataFormat, rate, sampleCount):
        self.fileDict["targets"][sprite]["sounds"].append(
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
        return self.fileDict["targets"][sprite]["blocks"][name]
    