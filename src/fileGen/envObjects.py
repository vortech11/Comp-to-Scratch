from src.parser.scanner import Token

class ObjMethod:
    def __init__(self, object: ListRef, name: Token) -> None:
        self.object: ListRef = object
        self.name = name

class LiteralRef:
    def __init__(self, value) -> None:
        self.value = value

    def getReference(self):
        return [str(self.value), None]
    
    def format(self):
        return [1, [10, str(self.value)]]

class ListRef:
    def __init__(self, listName: str, listId: str) -> None:
        self.name: str = listName
        self.id: str = listId
    
    def format(self):
        return [2, [13, self.name, self.id]]
    
    def getReference(self):
        return [self.name, self.id]

class VarRef:
    def __init__(self, varName: str, varId: str) -> None:
        self.name: str = varName
        self.id: str = varId
    
    def format(self):
        return [2, [12, self.name, self.id]]

    def getReference(self):
        return [self.name, self.id]

class ExprRef:
    def __init__(self, blockName: str) -> None:
        self.blockName: str = blockName
    
    def getName(self):
        return self.blockName

    def format(self) -> list:
        return [2, self.blockName]

class BlockRef:
    def __init__(self, blockName: str) -> None:
        self.blockName: str = blockName
    
    def getName(self, blockIndex=0):
        return self.blockName

    def format(self, blockIndex=0) -> list:
        return [2, self.blockName]

class StackBlockRef:
    def __init__(self, topBlockName: str, bottomBlockName: str) -> None:
        self.topBlock: str = topBlockName
        self.bottomBlock: str = bottomBlockName
    
    def getName(self, blockIndex=0):
        if blockIndex == 0:
            return self.topBlock
        return self.bottomBlock

    def format(self, blockIndex=0):
        if blockIndex == 0:
            return [2, self.topBlock]
        return [2, self.bottomBlock]
