

class Environment:
    def __init__(self, parent: Environment | None, funcSig: dict | None) -> None:
        self.parent: Environment | None = parent

        """
            {
            "name": [], 
            "argumentNames": [],
            }
        """
        self.func: None | dict = funcSig

        self.smartPointers = []

    def getFuncSig(self):
        if not self.func is None:
            return self.func

        if not self.parent is None:
            return self.parent.getFuncSig()
        
        return None

    def isFuncParam(self, name: str) -> bool:
        funcSig = self.getFuncSig()
        if funcSig is None:
            return False
        if name in funcSig["argumentNames"]:
            return True
        return False

    def setFuncData(self, name, argumentNames):
        if not self.func is None:
            self.func["name"] = name
            self.func["argumentNames"] = argumentNames
        if not self.parent is None:
            self.parent.setFuncData(name, argumentNames)

    def isSmartPointer(self, name) -> bool:
        if name in self.smartPointers:
            return True
        
        if self.parent is None:
            return False
        
        return self.parent.isSmartPointer(name)
        
    def createSmartPointer(self, name):
        self.smartPointers.append(name)