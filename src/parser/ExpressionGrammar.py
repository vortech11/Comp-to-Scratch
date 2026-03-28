from json import load
from pathlib import Path
import importlib.resources as resources
import logging
logger = logging.getLogger(__name__)

from sys import exit
from src.parser.scanner import Token, TokenType

from src.parser.UniversalGrammar import Grammar

from src.ErrorHandler import convError as error

from src.fileGen.projectFile import ProjectFile
from src.fileGen.environment import Environment
from src.fileGen.envObjects import *

from typing import Any

opcodeMap: dict = {}

def loadAliases():
    global opcodeMap
    assert isinstance(__package__, str)
    ROOT_PACKAGE = __package__.split('.')[0]
    PROJECT_ROOT = Path(resources.files(ROOT_PACKAGE)) # type: ignore
    filePath = PROJECT_ROOT / "OpcodeMap.json"
    with open(filePath) as file:
        opcodeMap = load(file)

loadAliases()

class Expr(Grammar):
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous: str | None) -> Any:
        ...

mathFuncs = {
    "abs": "abs",
    "floor": "floor",
    "ceil": "ceiling",
    "sqrt": "sqrt",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
    "ln": "ln",
    "log": "log",
    "ePow": "e ^",
    "tenPow": "10 ^",
}

class Assign(Expr):
    def __init__(self, name: Token | Expr, assignment: Token, value: Expr) -> None:
        self.name: Token | Expr = name
        self.assignment: Token = assignment
        self.value: Expr = value
    
    def getPrint(self) -> str:
        if isinstance(self.name, Token):
            return f"{self.name.lexeme} = {self.value.getPrint()}"
        return f"{self.name.getPrint()} = {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous):
        if isinstance(self.name, Expr) or projectFile.isDumbPointer(sprite, self.name.lexeme) or environment.isSmartPointer(self.name.lexeme):
            match self.assignment.type:
                case TokenType.EQUAL: operator = "setVar"
                case TokenType.PLUS_EQUAL: operator = "addVar"
                case TokenType.MINUS_EQUAL: operator = "minusVar"
                case TokenType.STAR_EQUAL: operator = "multVar"
                case TokenType.SLASH_EQUAL: operator = "divVar"
                case _: operator = "setVar"
            if isinstance(self.name, Token):
                name = Literal(self.name.lexeme)
            else:
                name = self.name
            gram = Call(Variable(Token(TokenType.IDENTIFIER, operator)), Token(TokenType.LEFT_PAREN), [name, self.value])
            block = gram.convert(projectFile, environment, sprite, previous)
            return block
        
        if not projectFile.isVar(sprite, self.name.lexeme):
            error(self.name, f"Variable '{self.name}' is not defined")

        block = projectFile.addBlock(
            "data_setvariableto", {}, 
            {"VARIABLE": VarRef(self.name.lexeme, projectFile.getVarId(sprite, self.name.lexeme)).getReference()}, 
            False, sprite, previous)
        
        operator = Token(TokenType.PLUS)
        match self.assignment.type:
            case TokenType.EQUAL:
                value = self.value.convert(projectFile, environment, sprite, block)
                projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value.format()})
                return block
            case TokenType.PLUS_EQUAL: operator = Token(TokenType.PLUS)
            case TokenType.MINUS_EQUAL: operator = Token(TokenType.MINUS)
            case TokenType.STAR_EQUAL: operator = Token(TokenType.STAR)
            case TokenType.SLASH_EQUAL: operator = Token(TokenType.SLASH)
        
        subGramar = Binary(Variable(self.name), operator, self.value)
        subBlock = subGramar.convert(projectFile, environment, sprite, block)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": subBlock.format()})
        return block

class SetPointerFunc(Expr):
    def __init__(self, name: Token | Expr, func: Expr):
        self.name: Token | Expr = name
        self.func: Expr = func

    def getPrint(self) -> str:
        return f"{self.name} {self.func.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if not isinstance(self.func, Call):
            if isinstance(self.name, Token):
                token = self.name
            else:
                token = Token(TokenType.IDENTIFIER)
            error(token, "Cannot set pointer value to object not of type FunctionCall")
            exit()
        if isinstance(self.name, Token):
            name = Literal(self.name.lexeme)
        else:
            name = self.name
        funcGram = Call(self.func.callee, self.func.paren, self.func.arguments + [name])
        funcBlock = funcGram.convert(projectFile, environment, sprite, previous) # type: ignore
        return funcBlock

class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left: Expr = left
        self.operator: Token = operator
        self.right: Expr = right
        
    def getPrint(self) -> str:
        return f"{self.operator} ({self.left.getPrint()}) ({self.right.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous=None):
        if self.operator.type in [TokenType.BANG_EQUAL, TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL]:
            match self.operator.type:
                case TokenType.BANG_EQUAL:
                    gram = Unary(
                        Token(TokenType.BANG, "!", None, 0), 
                        Binary(self.left, Token(TokenType.EQUAL_EQUAL, "==", None, 0), self.right)
                    )
                case TokenType.GREATER_EQUAL:
                    gram = Binary(
                        Binary(self.left, Token(TokenType.GREATER, ">", None, 0), self.right), 
                        Token(TokenType.OR, "or", None, 0), 
                        Binary(self.left, Token(TokenType.EQUAL_EQUAL, "==", None, 0), self.right)
                    )
                case TokenType.LESS_EQUAL:
                    gram = Binary(
                        Binary(self.left, Token(TokenType.GREATER, "<", None, 0), self.right), 
                        Token(TokenType.OR, "or", None, 0), 
                        Binary(self.left, Token(TokenType.EQUAL_EQUAL, "==", None, 0), self.right)
                    )
                case _:
                    gram = Expr()

            return gram.convert(projectFile, environment, sprite, previous)


        match self.operator.type:
            case TokenType.EQUAL_EQUAL: opcode = "operator_equals"
            case TokenType.GREATER: opcode = "operator_gt"
            case TokenType.LESS: opcode = "operator_lt"
            
            case TokenType.PLUS: opcode = "operator_add"
            case TokenType.MINUS: opcode = "operator_subtract"
            case TokenType.STAR: opcode = "operator_multiply"
            case TokenType.SLASH: opcode = "operator_divide"
            
            case TokenType.AND: opcode = "operator_and"
            case TokenType.OR: opcode = "operator_or"

            case _ : opcode = ""
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous, mendPrevious=False)


        left = self.left.convert(projectFile, environment, sprite, block)
        right = self.right.convert(projectFile, environment, sprite, block)

        leftName = opcodeMap[opcode]["inputs"][0]
        rightName = opcodeMap[opcode]["inputs"][1]

        projectFile.setBlockAttribute(sprite, block, "inputs", {leftName: left.format(), rightName: right.format()})

        return ExprRef(block)
        
class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
    
    def getPrint(self) -> str:
        return f"group {self.expression.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        return self.expression.convert(projectFile, environment, sprite, previous)
        
class Literal(Expr):
    def __init__(self, value):
        self.value = value
        
    def getPrint(self) -> str:
        match self.value:
            case str():
                return f'"{self.value}"'
            case _:
                return f"{self.value}"
            
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if isinstance(self.value, bool):
            if self.value is True:
                value = Literal("1")
            else:
                value = Literal("0")
            gram = Binary(Literal("1"), Token(TokenType.EQUAL_EQUAL), value)
            block = gram.convert(projectFile, environment, sprite, previous)
            if not isinstance(block, ExprRef):
                error(Token(TokenType.IDENTIFIER), "Internal Error; Struggling with boolean literal, try again.")
            return block
        
        if isinstance(self.value, float):
            self.value = f"{self.value:g}"

        return LiteralRef(self.value)
        
class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator: Token = operator
        self.right: Expr = right
    
    def getPrint(self) -> str:
        return f"{self.operator} ({self.right.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        match self.operator.type:
            case TokenType.BANG:
                opcode = "operator_not"
            case TokenType.MINUS:
                opcode = "operator_subtract"
            case _:
                opcode = ""
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous, mendPrevious=False)

        right = self.right.convert(projectFile, environment, sprite, block)

        if opcode == "operator_not":
            projectFile.setBlockAttribute(sprite, block, "inputs", {"OPERAND": right.format()})
        elif opcode == "operator_subtract":
            projectFile.setBlockAttribute(sprite, block, "inputs", {"NUM1": LiteralRef("0").format(), "NUM2": right.format()})

        return ExprRef(block)
    
class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee: Expr = callee
        self.paren: Token = paren
        self.arguments: list[Expr] = arguments
    
    def getPrint(self):
        listPrintArgs = [arg.getPrint() for arg in self.arguments]
        printArgs = ", ".join(listPrintArgs)
        return f"{self.callee.getPrint()} {self.paren} ({printArgs})"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        callee = self.callee.convert(projectFile, environment, sprite, previous)

        if isinstance(callee, ObjMethod):
            opcode = ""
            gramArgs = []
            addValue = 0
            listGram = Variable(Token(TokenType.IDENTIFIER, callee.object.name))
            match callee.name.lexeme:
                case "add": 
                    opcode = "data_addtolist"
                    gramArgs = self.arguments + [listGram]
                case "clear": 
                    opcode = "data_deletealloflist"
                    gramArgs: list[Expr] = [listGram]
                case "index":
                    opcode = "data_itemnumoflist"
                    gramArgs = self.arguments + [listGram]
                    addValue = -1
                case "remove":
                    opcode = "data_deleteoflist"
                    gramArgs = [Binary(self.arguments[0], Token(TokenType.PLUS), Literal(1)), listGram]
                    addValue = 1
                case "contains":
                    opcode = "data_listcontainsitem"
                    gramArgs = [listGram] + self.arguments
                case "insert":
                    opcode = "data_insertatlist"
                    gramArgs = [self.arguments[0], Binary(self.arguments[1], Token(TokenType.PLUS), Literal(1)), listGram]
                case _:
                    error(self.paren, f"List operation {callee.name.lexeme} not supported.")
            blockGramar = Call(Variable(Token(TokenType.IDENTIFIER, opcode, line=self.paren.line)), self.paren, gramArgs)
            args = {"LIST": callee.object.getReference()}
            if opcode in ["data_itemnumoflist"]:
                subBlock = projectFile.addBlock("operator_add", {}, {}, False, sprite, previous, False)
                block = blockGramar.convert(projectFile, environment, sprite, subBlock)
                projectFile.setBlockAttribute(sprite, subBlock, "next", None)
                projectFile.setBlockAttribute(sprite, subBlock, "inputs", {"NUM1": block.format(), "NUM2": LiteralRef(addValue).format()})
                projectFile.setBlockAttribute(sprite, block, "fields", args) # type: ignore
                return ExprRef(subBlock)
            
            block = blockGramar.convert(projectFile, environment, sprite, previous)
            
            match block:
                case ExprRef():
                    blockName = block.getName()
                    projectFile.setBlockAttribute(sprite, blockName, "fields", args)
                    return ExprRef(blockName)
                case str():
                    projectFile.setBlockAttribute(sprite, block, "fields", args)
                    return block
                case _:
                    error(self.paren, f"Internal Error: block return is not of type expected type, is instead {type(block)}")

        if not isinstance(callee, Token):
            error(self.paren, f"Function call must have callee as callable object, not '{callee}'")
            exit()
        if callee.lexeme in mathFuncs:
            opcode = "operator_mathop"
            blockGram = Call(Variable(Token(TokenType.IDENTIFIER, opcode)), Token(TokenType.LEFT_PAREN), [Literal(mathFuncs[callee.lexeme])] + self.arguments)
            block = blockGram.convert(projectFile, environment, sprite, previous)
            return block
        if callee.lexeme in opcodeMap:
            funcInfo = opcodeMap[callee.lexeme]
            if len(self.arguments) > len(funcInfo["inputs"]):
                error(self.paren, f"Function \"{callee.lexeme}\" arity must be equal or less than the number of inputs, {self.arguments}")
            if funcInfo["blocktype"] in ["reporter", "boolean"]:
                mendPrevious = False
            else:
                mendPrevious = True
            block = projectFile.addBlock(callee.lexeme, {}, {}, False, sprite, previous, mendPrevious)
            inputs = {}
            arguments = {}
            for index, input in enumerate(self.arguments):
                match funcInfo["inputtype"][index]:
                    case "text" | "color":
                        inputBlock = input.convert(projectFile, environment, sprite, block)
                        ## TODO: fix
                        #//if not isinstance(inputBlock, list):
                        #    inputBlock = [2, inputBlock]
                        inputs[funcInfo["inputs"][index]] = inputBlock.format()
                    case "dropdown":
                        inputReference = input.convert(projectFile, environment, sprite, block)
                        if isinstance(inputReference, (ListRef, VarRef)):
                            arguments[funcInfo["inputs"][index]] = inputReference.getReference()
                        elif isinstance(inputReference, LiteralRef):
                            arguments[funcInfo["inputs"][index]] = inputReference.getReference()
                        else:
                            error(self.paren, f"PANIC: Internal Error: WHAT IS SUPPOSED TO HAPPEN WITH 'inputReference' as type {type(inputReference)}?")
                    case "menu":
                        inputReference = input.convert(projectFile, environment, sprite, block)
                        if isinstance(inputReference, LiteralRef):
                            error(self.paren, f"Scratch block menu with text input is not supported. Good luck, use a different input")
                        inputs[funcInfo["inputs"][index]] = inputReference.format()

            projectFile.setBlockAttribute(sprite, block, "inputs", inputs)
            projectFile.setBlockAttribute(sprite, block, "fields", arguments)
            projectFile.setBlockAttribute(sprite, block, "next", None)
            if funcInfo["blocktype"] in ["reporter", "boolean"]:
                return ExprRef(block)
            else:
                return block
        
        func = projectFile.getFunc(sprite, callee.lexeme)
        firstBlock = previous
        #for returnName in func["returnVariables"]:
        #    blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "createVar")), Token(TokenType.LEFT_PAREN), [Literal(returnName), Literal("")])
        #    firstBlock = blockGram.convert(projectFile, environment, sprite, firstBlock)

        block = projectFile.addBlock("procedures_call", {}, {}, False, sprite, firstBlock)

        mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": func["proccode"],
            "argumentids": func["parameterIdText"],
            "warp": func["warp"]
        }

        inputs = {}

        for index, argument in enumerate(self.arguments):
            input = argument.convert(projectFile, environment, sprite, block)
            inputs[func["parameterIdList"][index]] = input.format()

        projectFile.setBlockAttribute(sprite, block, "inputs", inputs)
        projectFile.setBlockAttribute(sprite, block, "mutation", mutation)

        lastBlock = block
        #for returnName in func["returnVariables"]:
        #    blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "deleteVar")), Token(TokenType.LEFT_PAREN), [Literal(returnName)])
        #    lastBlock = blockGram.convert(projectFile, environment, sprite, lastBlock) # type: ignore

        return lastBlock

class ListIndex(Expr):
    def __init__(self, object, bracket, index) -> None:
        self.object: Expr = object
        self.bracket: Token = bracket
        self.index: Expr = index

    def getPrint(self):
        return f"{self.object.getPrint()}[{self.index.getPrint()}]"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        listReference = self.object.convert(projectFile, environment, sprite, previous)

        if not isinstance(listReference, ListRef):
            error(self.bracket, "Item before list index operation must be indexable")
            exit()

        block = projectFile.addBlock("data_itemoflist", {}, {}, False, sprite, previous, False)
        addBlock = projectFile.addBlock("operator_add", {}, {}, False, sprite, block, False)
        indexBlock = self.index.convert(projectFile, environment, sprite, addBlock)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"INDEX": ExprRef(addBlock).format()})
        projectFile.setBlockAttribute(sprite, block, "fields", {"LIST": listReference.getReference()})
        projectFile.setBlockAttribute(sprite, addBlock, "inputs", {"NUM1": indexBlock.format(), "NUM2": LiteralRef("1").format()})
        projectFile.setBlockAttribute(sprite, addBlock, "next", None)
        return ExprRef(block)
    
class ListSetIndex(Expr):
    def __init__(self, object, assignment, value) -> None:
        self.object: Expr = object
        self.assignment: Token = assignment
        self.value: Expr = value
    
    def getPrint(self) -> str:
        return f"{self.object.getPrint()} {self.assignment} {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if not isinstance(self.object, ListIndex):
            error(self.assignment, "Internal Error: in ListSetIndex, obj is not ListIndex")
            exit()
        if not isinstance(self.object.object, Variable):
            error(self.assignment, "Language does not support multidementional arrays")
            exit()
        list = self.object.object.convert(projectFile, environment, sprite, previous)
        if not isinstance(list, ListRef):
            error(self.assignment, "💔")
            assert False
        listName = list.name
        block = projectFile.addBlock("data_replaceitemoflist", {}, {"LIST": [listName, projectFile.getListId(sprite, listName)]}, False, sprite, previous)
        indexGram = Binary(self.object.index, Token(TokenType.PLUS), Literal(1))
        index = indexGram.convert(projectFile, environment, sprite, block)
        if self.assignment.type == TokenType.EQUAL:
            value = self.value.convert(projectFile, environment, sprite, block)
        else:
            match self.assignment.type:
                case TokenType.PLUS_EQUAL: opcode = "operator_add"
                case TokenType.MINUS_EQUAL: opcode = "operator_subtract"
                case TokenType.STAR_EQUAL: opcode = "operator_multiply"
                case TokenType.SLASH_EQUAL: opcode = "operator_divide"
                case _: opcode = "operator_add"
    
            valueBlock = projectFile.addBlock(opcode, {}, {}, False, sprite, block)
            value = self.value.convert(projectFile, environment, sprite, valueBlock)
            listRef = self.object.convert(projectFile, environment, sprite, valueBlock)
            projectFile.setBlockAttribute(sprite, valueBlock, "next", None)
            projectFile.setBlockAttribute(sprite, valueBlock, "inputs", {"NUM1": listRef.format(), "NUM2": value.format()})
            value = ExprRef(valueBlock)

        projectFile.setBlockAttribute(sprite, block, "next", None)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"INDEX": index.format(), "ITEM": value.format()})
        return block
        

class Get(Expr):
    def __init__(self, object: Expr, name: Token) -> None:
        self.object: Expr = object
        self.name: Token = name

    def getPrint(self):
        return f"{self.object.getPrint()}.{self.name}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        object = self.object.convert(projectFile, environment, sprite, previous)
        if isinstance(object, ListRef):
            match self.name.lexeme:
                case "length":
                    block = projectFile.addBlock("data_lengthoflist", {}, {"LIST": [object.name, object.id]}, False, sprite, previous, False)
                    return ExprRef(block)
            return ObjMethod(object, self.name)

        if not isinstance(object, Token):
            error(self.name, "Object Get must act upon an object")
            exit()
        if object.type == TokenType.THIS:
            opcode = ""
            match self.name.lexeme:
                case "x": opcode = "motion_xposition"
                case "y": opcode = "motion_yposition"
                case "direction": opcode = "motion_direction"
                case "size": opcode = "looks_size"
                case "volume": opcode = "sound_volume"
                case "answer": opcode = "sensing_answer" # don't know how well this will work
                case "mouseX": opcode = "sensing_mousex"
                case "mouseY": opcode = "sensing_mousey"
                case "loudness": opcode = "sensing_loudness" # mabey
                case "timer": opcode = "sensing_timer" # mabey
            
            block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous, False)
            return ExprRef(block)

        if projectFile.isSprite(object.lexeme):
            match self.name.lexeme:
                case "volume":
                    ...

        error(self.name, f"Object {self.object} or name {self.name.lexeme} is unsupported.")
    
class Set(Expr):
    def __init__(self, object: Expr, name: Token, value: Expr) -> None:
        self.object: Expr = object
        self.name: Token = name
        self.value: Expr = value

    def getPrint(self):
        return f"{self.object.getPrint()}.{self.name} = {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        object = self.object.convert(projectFile, environment, sprite, previous)
        if not isinstance(object, Token):
            error(self.name, "Object Get must act upon an object")
        if object.type == TokenType.THIS:
            opcode = ""
            match self.name.lexeme:
                case "x": opcode = "motion_setx"
                case "y": opcode = "motion_sety"
                case "direction": opcode = "motion_pointindirection"
                case "rotationStyle": opcode = "motion_setrotationstyle"
                case "currentCostume": opcode = "looks_switchcostumeto"
                case "size": opcode = "looks_setsizeto"
                case "volume": opcode = "sound_setvolumeto"
                case "dragMode": opcode = "sensing_setdragmode"

            blockGram = Call(Variable(Token(TokenType.IDENTIFIER, opcode)), Token(TokenType.LEFT_PAREN), [self.value])

            block = blockGram.convert(projectFile, environment, sprite, previous)
            return block
    
class This(Expr):
    def __init__(self, keyword: Token) -> None:
        self.keyword: Token = keyword
    
    def getPrint(self):
        return f"{self.keyword.lexeme}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        return self.keyword

class PointerDereference(Expr):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
    
    def getPrint(self) -> str:
        return f"*{self.expression.getPrint}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        topBlock = projectFile.addBlock("data_itemoflist", {}, {"LIST": ["value", projectFile.getListId(sprite, "value")]}, False, sprite, previous, False)
        bottomBlock = projectFile.addBlock("data_itemnumoflist", {}, {"LIST": ["key", projectFile.getListId(sprite, "key")]}, False, sprite, previous, False)
        varName = self.expression.convert(projectFile, environment, sprite, previous)
        projectFile.setBlockAttribute(sprite, bottomBlock, "inputs", {"ITEM": varName.format()})
        projectFile.setBlockAttribute(sprite, topBlock, "inputs", {"INDEX": BlockRef(bottomBlock).format()})
        return BlockRef(topBlock)

class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
        
    def getPrint(self):
        return f"{self.name}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        varName = self.name.lexeme
        if varName in opcodeMap:
            return self.name
        
        if projectFile.isSprite(varName):
            return self.name
        
        if projectFile.doesFuncExist(sprite, varName):
            return self.name
        
        if varName in mathFuncs:
            return self.name
        
        if projectFile.isConst(sprite, varName):
            return Literal(projectFile.getConstValue(sprite, varName)).convert(projectFile, environment, sprite, previous)
        
        if environment.isFuncParam(varName):
            block = projectFile.addBlock("argument_reporter_boolean", {}, {"VALUE": [varName]}, False, sprite, previous, mendPrevious=False)
            return ExprRef(block)
        
        if projectFile.isList(sprite, varName):
            return ListRef(varName, projectFile.getListId(sprite, varName))
        
        if projectFile.isDumbPointer(sprite, varName) or environment.isSmartPointer(varName):
            return PointerDereference(Literal(varName)).convert(projectFile, environment, sprite, previous)

        if projectFile.isVar(sprite, varName):
            return VarRef(varName, projectFile.getVarId(sprite, varName))

        error(self.name, f"Variable '{self.name.lexeme}' is not defined.")

