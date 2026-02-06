
class ProjectFile:
    def __init__(self) -> None:
        self.fileDict = {
            "targets": [],
            "monitors": [],
            "extensions": [],
            "meta": {
                "server": "3.0.0",
                "vm": "11.0.0-beta.2",
                "agent": "Scratch Compiler v1.0.0"
            }
        }
        self.currentBlock = 0
    
    def getBlockName(self, blockNum=None) -> str:
        if blockNum is None:
            return f"Block{self.currentBlock}"
        return f"Block{blockNum}"
    
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
    
    def addCostume(self, sprite, name, dataFormat, rotationCenter:tuple):
        self.fileDict["targets"][sprite]["costumes"].append(
            {
                "name": name,
                "dataFormat": dataFormat,
                "assetId": "",
                "md5ext": "",
                "rotationCenterX": rotationCenter[0],
                "rotationCenterY": rotationCenter[1]
            }
        )
    
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
    