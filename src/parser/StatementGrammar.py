from json import load
from sys import exit
from pathlib import Path
import importlib.resources as resources
import logging
logger = logging.getLogger(__name__)

from src.parser.scanner import Token, TokenType

from src.parser.UniversalGrammar import Grammar
from src.parser.ExpressionGrammar import *

from src.ErrorHandler import convError as error
from src.ErrorHandler import warn

from src.fileGen.projectFile import ProjectFile
from src.fileGen.environment import Environment
from src.fileGen.envObjects import *

from typing import Any

opcodeMap: dict = {}

def getProjectRoot() -> Path:
    assert isinstance(__package__, str)
    ROOT_PACKAGE = __package__.split('.')[0]
    PROJECT_ROOT = Path(resources.files(ROOT_PACKAGE)) # type: ignore
    return PROJECT_ROOT

def loadAliases():
    global opcodeMap
    filePath = getProjectRoot() / "OpcodeMap.json"
    with open(filePath) as file:
        opcodeMap = load(file)

loadAliases()

def unpack(value, index=0):
    return value[index] if isinstance(value, (tuple, list)) else value

def formatFuncArgs(ids: list[str], names: list[str], defaults: list[str]):
    textParamData = []
    for paramlist in [ids, names, defaults]:
        #paramlist = ["false" if item is False else "true" if item is True else item for item in paramlist]
        textParamData.append(f"[{",".join([f"\"{item}\"" for item in paramlist])}]")
    return textParamData


class Stmt(Grammar):
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous: str | None) -> Any:
        ...

class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements: list[Stmt] = statements
    
    def getPrint(self) -> str:
        output = []
        for statement in self.statements:
            output.append(statement.getPrint())
        return f"{'\n'.join(output)}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        subEnv: Environment = Environment(environment, environment.func)
        topBlock = None
        bottomBlock = previous
        for statement in self.statements:
            block = statement.convert(projectFile, subEnv, sprite, bottomBlock)
            if isinstance(block, (ExprRef, LiteralRef, ListRef, VarRef)):
                continue
            if (not unpack(block, 1) == previous) and topBlock is None:
                if unpack(block, 0) == 2:
                    topBlock = unpack(block, 1)
                else:
                    topBlock = unpack(block, 0)
            bottomBlock = unpack(block, 1)

        for pointer in subEnv.smartPointers:
            blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "deleteVar")), Token(TokenType.LEFT_PAREN), [Literal(pointer)])
            bottomBlock = blockGram.convert(projectFile, subEnv, sprite, bottomBlock) # type: ignore

        if topBlock is None:
            if bottomBlock is previous:
                return None
            return bottomBlock
        return topBlock, bottomBlock
    
class Expression(Stmt):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
        
    def getPrint(self) -> str:
        return f"{self.expression.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        return self.expression.convert(projectFile, environment, sprite, previous)
        
class Print(Stmt):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression

    def getPrint(self) -> str:
        return f"print ({self.expression.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        #print(self.expression.convert(projectFile, environment, sprite, previous))
        #print(self.expression.getPrint())
        return previous

class Return(Stmt):
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword: Token = keyword
        self.value: Expr | None = value
    
    def getPrint(self) -> str:
        value = ""
        if not self.value is None:
            value = self.value.getPrint()
        return f"{self.keyword.lexeme} {value}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        #error(self.keyword, "Return keyword not implamented yet: don't use it!")
        if environment.func is None:
            error(self.keyword, "Current func is None")
            assert False

        currentFuncName = environment.func["name"]
        funcSig = projectFile.funcs[sprite][currentFuncName]
        argumentIdList = funcSig["parameterIdList"]
        argumentNameList = funcSig["parameterNameList"]
        argumentDefaultList = funcSig["perameterDefaultList"]
        nextIndex = len(argumentIdList)
        inputName = "return"
        fullInputName = f"{inputName}{nextIndex}"
        argumentIdList.append(fullInputName)
        argumentNameList.append(inputName)
        argumentDefaultList.append("")
        funcSig["proccode"] += " %s"
        funcSig["parameterIdList"] = argumentIdList
        funcSig["parameterNameList"] = argumentNameList
        funcSig["perameterDefaultList"] = argumentDefaultList
        funcSig["returnVariables"].append(fullInputName)
        textParamData = formatFuncArgs(argumentIdList, argumentNameList, argumentDefaultList)
        funcSig["parameterIdText"] = textParamData[0]
        projectFile.funcs[sprite][currentFuncName] = funcSig
        mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": funcSig["proccode"],
            "argumentids": textParamData[0],
            "argumentnames": textParamData[1],
            "argumentdefaults": textParamData[2],
            "warp": funcSig["warp"]
        }
        projectFile.setBlockAttribute(sprite, funcSig["blockName"], "mutation", mutation)
        environment.setFuncData(currentFuncName, argumentNameList)

        if self.value is None:
            return previous
        
        blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "setVar")), Token(TokenType.LEFT_PAREN), [Variable(Token(TokenType.IDENTIFIER, inputName)), self.value])
        block = blockGram.convert(projectFile, environment, sprite, previous)
        return block

class DefPointerFunc(Stmt):
    def __init__(self, declarationType: Token, name: Token | Expr, func: Expr):
        self.declarationType: Token = declarationType
        self.name: Token | Expr = name
        self.func: Expr = func

    def getPrint(self) -> str:
        return f"{self.declarationType} {self.name} {self.func.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        varGram = Var(None, self.declarationType, self.name, Literal(""))
        varBlock = varGram.convert(projectFile, environment, sprite, previous)
        if not isinstance(self.func, Call):
            error(self.declarationType, "Cannot set pointer value to object not of type FunctionCall")
            exit()
        if isinstance(self.name, Token):
            name = Literal(self.name.lexeme)
        elif isinstance(self.name, PointerDereference):
            name = self.name.expression
        else:
            error(self.declarationType, "Panic! Internal Error: I don't know what is supposed to happen here.")
            exit()
        funcGram = Call(self.func.callee, self.func.paren, self.func.arguments + [name])
        funcBlock = funcGram.convert(projectFile, environment, sprite, varBlock) # type: ignore
        return funcBlock

class Var(Stmt):
    def __init__(self, constant: Token | None, declarationType: Token, name: Token | Expr, initializer: Expr | None) -> None:
        self.constant: Token | None = constant
        self.declarationType: Token = declarationType
        self.name: Token | Expr = name
        self.initializer: Expr | list[Expr] | Literal | None = initializer
        
    def getPrint(self) -> str:
        if self.constant is None:
            constant = ""
        else:
            constant = self.constant.lexeme
        if self.initializer == None:
            value = None
        elif isinstance(self.initializer, list):
            value = ", ".join([value.getPrint() for value in self.initializer])
        else:
            value = self.initializer.getPrint()
        if isinstance(self.name, Expr):
            name = self.name.getPrint()
        else:
            name = self.name.lexeme
        
        return f"{constant} {self.declarationType.lexeme} {name} {value}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if not self.constant is None:
            if not isinstance(self.name, Token):
                error(self.constant, "Name of constant cannot be an expression.")
                exit()
            if not isinstance(self.initializer, Literal):
                error(self.constant, "Initializer of constant variable must be a literal.")
                exit()
            #if isinstance(self.initializer.value, bool):
            #    error(self.constant, "Initializer of constant variable cannot be boolean.")
            projectFile.createConst(sprite, self.name.lexeme, self.initializer.value)
            return previous

        if self.declarationType.type in [TokenType.DUMB_POINTER, TokenType.SMART_POINTER]:
            if self.initializer is None:
                initializer = Literal("")
            elif isinstance(self.initializer, list):
                error(self.declarationType, "Initializer to pointer declaration cannot be list")
                assert False
            else:
                initializer = self.initializer
            
            if isinstance(self.name, Token):
                name = Literal(self.name.lexeme)
            
                if self.declarationType.type == TokenType.DUMB_POINTER:
                    if environment.isSmartPointer(self.name.lexeme):
                        warn(self.declarationType, "Dumb pointer is being created with the same name as a smart pointer of higher scope!")
                    projectFile.createDumbPointer(sprite, self.name.lexeme)
                else:
                    if projectFile.isDumbPointer(sprite, self.name.lexeme):
                        warn(self.declarationType, "Smart pointer is being created with the same name as a dumb pointer!")
                    environment.createSmartPointer(self.name.lexeme)
            elif isinstance(self.name, PointerDereference):
                if self.declarationType.type == TokenType.SMART_POINTER:
                    error(self.declarationType, "Cannot create smart pointer with variable name.")
                name = self.name.expression
            else:
                error(self.declarationType, "Panic! Internal Error: I don't know what is supposed to happen here.")
                exit()
            blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "createVar")), Token(TokenType.LEFT_PAREN), [name, initializer])
            block = blockGram.convert(projectFile, environment, sprite, previous)
            return block

        if isinstance(self.name, Expr):
            error(self.declarationType, "Cannot declare a design time variable of a variable name.")
            exit()

        if self.declarationType.type == TokenType.VAR:
            if isinstance(self.initializer, list):
                error(self.name, "For var declaration, initializer cannot be list. Use list data type for list values")
                exit()
            projectFile.createVar(sprite, self.name.lexeme, "")
            if self.initializer is None:
                return
            block = projectFile.addBlock("data_setvariableto", {}, {"VARIABLE": [self.name.lexeme, projectFile.getVarId(sprite, self.name.lexeme)]}, False, sprite, previous)

            value = self.initializer.convert(projectFile, environment, sprite, block)

            if isinstance(value, LiteralRef):
                literal = value.value
            else:
                literal = ""
            
            projectFile.setVarDefault(sprite, self.name.lexeme, literal)
            projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value.format()})
            return block
        
        if self.declarationType.type == TokenType.LIST:
            projectFile.createList(sprite, self.name.lexeme, [])
            if self.initializer is None:
                return previous
            if isinstance(self.initializer, list):
                exprInitializer = self.initializer
            else:
                exprInitializer = [self.initializer]
            
            StmtClear = [Call(Get(Variable(self.name), Token(TokenType.IDENTIFIER, "clear", line=self.name.line)), Token(TokenType.LEFT_PAREN, line=self.name.line), [])]
            if not len(exprInitializer) == 0:
                StmtInitializer = [
                    Call(
                        Get(Variable(self.name), Token(TokenType.IDENTIFIER, "add", line=self.name.line)), 
                        Token(TokenType.LEFT_PAREN, line=self.name.line), 
                        [expression]
                    ) for expression in exprInitializer
                ]
                initializerGrammar = Block(StmtClear + StmtInitializer) # type: ignore
            else:
                initializerGrammar = Block(StmtClear) # type: ignore

            return initializerGrammar.convert(projectFile, environment, sprite, previous)
        
        

class Delete(Stmt):
    def __init__(self, var: Token | Expr):
        self.var: Token | Expr = var
    
    def getPrint(self) -> str:
        return f"del {self.var}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if isinstance(self.var, Token):
            if not projectFile.isDumbPointer(sprite, self.var.lexeme):
                if environment.isSmartPointer(self.var.lexeme):
                    error(self.var, "Cannot delete smart pointer!")
                error(self.var, "Cannot delete object that is not of type pointer.")
            name = Literal(self.var.lexeme)
        else:
            if isinstance(self.var, PointerDereference):
                name = self.var.expression
            else:
                error(Token(TokenType.IDENTIFIER), "Panic! Internal Error: I don't know what is supposed to happen here.")
                exit()
        blockGram = Call(Variable(Token(TokenType.IDENTIFIER, "deleteVar")), Token(TokenType.LEFT_PAREN), [name])
        block = blockGram.convert(projectFile, environment, sprite, previous)
        return block

class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: Stmt) -> None:
        self.name: Token = name
        self.params: list[Token] = params
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        params = ", ".join([str(param) for param in self.params])
        return f"func {self.name} ({", ".join(params)}) {{\n{self.body.getPrint()}\n}}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        match self.name.lexeme:
            case "main": opcode = "event_whenflagclicked"
            case "keyPressed": opcode = "event_whenkeypressed"
            case _: opcode = None

        if not opcode is None:
            params: list[Expr] = [Literal(value) for value in self.params]
            block = Call(Variable(Token(TokenType.IDENTIFIER, opcode, None, 0)), Token(TokenType.LEFT_PAREN, "(", None, 0), params).convert(projectFile, environment, sprite, None)
            endBlock = self.body.convert(projectFile, environment, sprite, block) # type: ignore
            return previous
        
        block = projectFile.addBlock("procedures_definition", {}, {}, False, sprite)
        prototype = projectFile.addBlock("procedures_prototype", {}, {}, True, sprite, block, mendPrevious=False)

        prototypeInputs = {}

        inputTypes = []
        ids = []
        names = []
        defaults = []

        for param in self.params:
            name = param.lexeme
            inputType = "%s"
            inputId = f"{name}{len(names)}"

            names.append(name)
            inputTypes.append(inputType)
            ids.append(inputId)
            
            defaults.append("")
            
            inputBlock = projectFile.addBlock("argument_reporter_string_number", {}, {"VALUE": [name, None]}, True, sprite, prototype, mendPrevious=False)
            prototypeInputs[inputId] = [1, inputBlock]

        textParamData = formatFuncArgs(ids, names, defaults)

        proccode = f"{self.name.lexeme} {" ".join(inputTypes)}"
        warp = "true"

        mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": proccode,
            "argumentids": textParamData[0],
            "argumentnames": textParamData[1],
            "argumentdefaults": textParamData[2],
            "warp": "true"
        }

        projectFile.setBlockAttribute(sprite, prototype, "mutation", mutation)
        projectFile.setBlockAttribute(sprite, prototype, "inputs", prototypeInputs)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"custom_block": [1, prototype]})

        funcEnvironment = Environment(environment, {"name": self.name.lexeme, "argumentNames": names})
        projectFile.createFunc(sprite, self.name.lexeme, proccode, ids, names, defaults, textParamData[0], warp, prototype, [])

        lastBlock = unpack(self.body.convert(projectFile, funcEnvironment, sprite, block), 1)
        return previous

class IfStmt(Stmt):
    def __init__(self, condition: Expr, thenBranch: Stmt, elseBranch: Stmt | None) -> None:
        self.condition: Expr = condition
        self.thenBranch: Stmt = thenBranch
        self.elseBranch: Stmt | None = elseBranch

    def getPrint(self) -> str:
        return f"if ({self.condition.getPrint()}) {{{self.thenBranch.getPrint()}}}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if self.elseBranch is None:
            opcode = "control_if"
        else:
            opcode = "control_if_else"
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous)

        condition = self.condition.convert(projectFile, environment, sprite, block)
        
        thenBranch = unpack(self.thenBranch.convert(projectFile, environment, sprite, block))
        thenBranch = [2, thenBranch]
        
        inputs = {"CONDITION" : condition.format(), "SUBSTACK": thenBranch}        

        if not self.elseBranch is None:
            elseBranch = unpack(self.elseBranch.convert(projectFile, environment, sprite, block))
            elseBranch = [2, elseBranch]
            inputs["SUBSTACK2"] = elseBranch

        projectFile.setBlockAttribute(sprite, block, "inputs", inputs)
        projectFile.setBlockAttribute(sprite, block, "next", None)

        return block

class WhileStmt(Stmt):
    def __init__(self, expression: Expr, statement: Stmt) -> None:
        self.expression: Expr = expression
        self.statement: Stmt = statement

    def getPrint(self) -> str:
        return f"while ({self.expression.getPrint()}) {{{self.statement.getPrint()}}}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        block = projectFile.addBlock("control_repeat_until", {}, {}, False, sprite, previous)
        expression = Unary(Token(TokenType.BANG, "!", "!", 0), self.expression)
        expression = expression.convert(projectFile, environment, sprite, block)
        statement = unpack(self.statement.convert(projectFile, environment, sprite, block))
        statement = [2, statement]
        projectFile.setBlockAttribute(sprite, block, "inputs", {"CONDITION": expression.format(), "SUBSTACK": statement})
        projectFile.setBlockAttribute(sprite, block, "next", None)
        return block

class LoopStmt(Stmt):
    def __init__(self, expression: Expr, statement: Stmt):
        self.expression: Expr = expression
        self.statement: Stmt = statement

    def getPrint(self) -> str:
        return f"loop ({self.expression.getPrint()}) {{{self.statement.getPrint()}}}"

    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        block = projectFile.addBlock("control_repeat", {}, {}, False, sprite, previous)
        expression = self.expression.convert(projectFile, environment, sprite, block)
        statement = unpack(self.statement.convert(projectFile, environment, sprite, block))
        statement = [2, statement]
        projectFile.setBlockAttribute(sprite, block, "inputs", {"TIMES": expression.format(), "SUBSTACK": statement})
        projectFile.setBlockAttribute(sprite, block, "next", None)
        return block

class ForeverStmt(Stmt):
    def __init__(self, statement: Stmt):
        self.statement: Stmt = statement

    def getPrint(self) -> str:
        return f"forever {{{self.statement.getPrint()}}}"

    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        block = projectFile.addBlock("control_forever", {}, {}, False, sprite, previous)
        statement = unpack(self.statement.convert(projectFile, environment, sprite, block))
        statement = [2, statement]
        projectFile.setBlockAttribute(sprite, block, "inputs", {"SUBSTACK": statement})
        projectFile.setBlockAttribute(sprite, block, "next", None)
        return block

class CostumeStmt(Stmt):
    def __init__(self, name: Token, relative: Token, path: Token, centerX: int | None, centerY: int | None) -> None:
        self.name: Token = name
        self.relative: Token = relative
        self.path: Token = path
        self.centerX: int | None = centerX
        self.centerY: int | None = centerY

    def getPrint(self) -> str:
        return f"costume {self.name} {self.path}"
    
    def updateToDefault(self, path: str) -> str:
        filePath = getProjectRoot() / "Default-Assets" / path
        if filePath.exists():
            return str(filePath)
        return path

    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous):
        filePath = self.updateToDefault(self.relative.lexeme)
        if filePath == self.relative.lexeme:
            filePath = self.path.lexeme
        projectFile.addCostume(sprite, self.name.lexeme, filePath, (self.centerX, self.centerY))
        return previous

class SoundStmt(Stmt):
    def __init__(self, name: Token, relative: Token, path: Token) -> None:
        self.name: Token = name
        self.relative: Token = relative
        self.path: Token = path

    def getPrint(self) -> str:
        return f"costume {self.name} {self.path}"
    
    def updateToDefault(self, path: str) -> str:
        filePath = getProjectRoot() / "Default-Assets" / path
        if filePath.exists():
            return str(filePath)
        return path

    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous):
        filePath = self.updateToDefault(self.relative.lexeme)
        if filePath == self.relative.lexeme:
            filePath = self.path.lexeme
        projectFile.addSound(sprite, self.name.lexeme, filePath)
        return previous

class FileStmt(Grammar):
    def convert(self, projectFile: ProjectFile):
        ...

class Sprite(FileStmt):
    def __init__(self, name: Token, body: Stmt) -> None:
        self.name: Token = name
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        return f"sprite {self.name.lexeme} {{\n{self.body.getPrint()}\n}}"
    
    def convert(self, projectFile: ProjectFile):
        isStage = self.name.lexeme == "Stage"
        projectFile.addSprite(self.name.lexeme, isStage)
        spriteEnvironment = Environment(None, None)
        self.body.convert(projectFile, spriteEnvironment, self.name.lexeme, None)
        projectFile.addDefaultCostume(self.name.lexeme, str(getProjectRoot() / "Default-Assets" / "blank.svg"), "blank")

class Export(FileStmt):
    def __init__(self, body) -> None:
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        return f"export {self.body.getPrint()}"
    
    def convert(self, projectFile: ProjectFile):
        return

def formatAST(grammar: list[Any]) -> str:
    return "\n".join([gram.getPrint() for gram in grammar])

def printAST(grammar: Grammar):
    print(f"{grammar.getPrint()}")