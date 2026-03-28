from hashlib import md5
from pathlib import Path
from sys import exit
from PIL import Image
import xml.etree.ElementTree as ET
from tinytag import TinyTag


# Thank you AI for this horible piece of code you have given me. It means a lot.
def get_svg_dimensions(filename):
    """Parses an SVG file and returns its width and height from attributes."""
    # Define the SVG namespace
    namespace = {'svg': 'http://www.w3.org/2000/svg'}

    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        # Try to get width and height from attributes, handling potential units (e.g., 'px', 'pt')
        width_str = root.get('width')
        height_str = root.get('height')

        if width_str and height_str:
            # Remove non-numeric characters like 'px' or 'pt' for simple cases
            width = float(''.join(filter(lambda x: x.isdigit() or x == '.', width_str)))
            height = float(''.join(filter(lambda x: x.isdigit() or x == '.', height_str)))
            return width, height
        else:
            # If width/height attributes are missing, check viewBox
            viewbox_str = root.get('viewBox')
            if viewbox_str:
                _, _, width, height = map(float, viewbox_str.split())
                return width, height
            else:
                return "Dimensions not explicitly defined in width/height or viewBox attributes."

    except ET.ParseError as e:
        return f"Error parsing SVG file: {e}"
    except ValueError as e:
        return f"Error converting dimensions to float: {e}"

def get_audio_data(filename):
    tag = TinyTag.get(filename)
    sample_rate = tag.samplerate
    if tag.duration and sample_rate:
        sample_count = int(tag.duration * sample_rate)
        return sample_rate, sample_count
    print(f"Error: Audio file {filename} does not have duration/rate")
    exit()

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

        self.funcs = {}

        self.dumbPointers: dict[str, list[str]] = {}

        self.currentBlock = 0

        self.consts: dict[str, dict] = {}
    
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
        self.dumbPointers[name] = []
        self.consts[name] = {}

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
    
    def addCostume(self, sprite: str, name: str, path: str, rotationCenter: tuple):
        assetId = self.genHash(path)
        suffix = Path(path).suffix
        dataFormat = suffix.removeprefix(".")

        if rotationCenter[0] is None:
            if dataFormat == "svg":
                svgCenter = get_svg_dimensions(path)
                if isinstance(svgCenter, str):
                    print(f"WARNING: {svgCenter}; setting image center to (0, 0).")
                    rotationCenter = (0, 0)
                else:
                    rotationCenter = get_svg_dimensions(path)[0] / 2, get_svg_dimensions(path)[1] / 2  # type: ignore
            else:
                try:
                    with Image.open(path) as img:
                        rotationCenter = img.size[0] / 2, img.size[1] / 2
                except IOError:
                    print(f"WARNING: Error attempting to get center of file {path}; setting image center to (0, 0).")
                    rotationCenter = (0, 0)

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
    
    def addSound(self, sprite: str, name: str, path: str):
        assetId = self.genHash(path)
        suffix = Path(path).suffix
        dataFormat = suffix.removeprefix(".")

        rate, sampleCount = get_audio_data(path)

        self.fileDict["targets"][self.getSpriteIndex(sprite)]["sounds"].append(
            {
                "name": name,
                "assetId": assetId,
                "dataFormat": dataFormat,
                "rate": rate,
                "sampleCount": sampleCount,
                "md5ext": assetId + suffix
            }
        )

        self.files[str(Path(path))] = Path(assetId + suffix)
    
    def addDefaultCostume(self, sprite: str, path: str, name: str="", rotationCenter: tuple=(1, 1)):
        if len(self.fileDict["targets"][self.getSpriteIndex(sprite)]["costumes"]) == 0:
            self.addCostume(sprite, name, path, rotationCenter)

    def getBlock(self, sprite: str, name: str) -> dict:
        return self.fileDict["targets"][self.getSpriteIndex(sprite)]["blocks"][name]

    def isSprite(self, name: str) -> bool:
        return name in self.spriteList

    def createVar(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"][f"{name}{self.currentBlock}"] = [name, value]

    def createConst(self, sprite: str, name: str, value):
        self.consts[sprite][name] = value
    
    def isConst(self, sprite: str, name: str):
        return name in self.consts[sprite]
    
    def getConstValue(self, sprite: str, name: str):
        return self.consts[sprite][name]

    def setVarDefault(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["variables"][self.getVarId(sprite, name)] = [name, value]

    def createList(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"][f"{name}{self.currentBlock}"] = [name, value]

    def setListDefault(self, sprite: str, name: str, value):
        self.fileDict["targets"][self.getSpriteIndex(sprite)]["lists"][self.getVarId(sprite, name)] = [name, value]

    def createDumbPointer(self, sprite: str, name: str):
        self.dumbPointers[sprite].append(name)
    
    def isDumbPointer(self, sprite: str, name: str):
        return name in self.dumbPointers[sprite]

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

    def createFunc(
            self, 
            sprite: str, 
            name: str, 
            proccode: str, 
            parameterIdList: list[str], 
            parameterNameList: list[str], 
            parameterDefaultList: list[str], 
            parameterIdText: str, 
            warp: str, 
            blockName: str, 
            returnVariables: list[str]
        ):
        
        self.funcs[sprite][name] = {
            "proccode": proccode, 
            "parameterIdList": parameterIdList, 
            "parameterNameList": parameterNameList,
            "perameterDefaultList": parameterDefaultList, 
            "parameterIdText": parameterIdText,
            "warp": warp,
            "blockName": blockName, # Reference to the prototype portion
            "returnVariables": returnVariables 
        }
    
    def doesFuncExist(self, sprite, funcName):
        return funcName in self.funcs[sprite]
    
    def getFunc(self, sprite, funcName):
        if not self.doesFuncExist(sprite, funcName):
            exit()
        return self.funcs[sprite][funcName]