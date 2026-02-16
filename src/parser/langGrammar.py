from json import load

from src.parser.scanner import Token, TokenType

from src.fileGen.projectFile import ProjectFile

from typing import Any

with open("src/OpcodeMap.json") as map:
    opcodeMap = load(map)

def unpack(value, index=0):
    return value[index] if isinstance(value, (tuple, list)) else value

class Grammar:
    def getPrint(self) -> str:
        return f"()"

class Expr(Grammar):
    def convert(self, projectFile: ProjectFile, sprite: str, previous: str | None) -> Any:
        ...

class Assign(Expr):
    def __init__(self, name: Token, value: Expr) -> None:
        self.name: Token = name
        self.value: Expr = value
    
    def getPrint(self) -> str:
        return f"{self.name.lexeme} = {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, sprite, previous):
        block = projectFile.addBlock("data_setvariableto", {}, {"VARIABLE": [self.name.lexeme, self.name.lexeme]}, False, sprite, previous)
        value = self.value.convert(projectFile, sprite, block)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value})
        return block

class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left: Expr = left
        self.operator: Token = operator
        self.right: Expr = right
        
    def getPrint(self) -> str:
        return f"{self.operator} ({self.left.getPrint()}) ({self.right.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, sprite, previous=None):
        match self.operator.type:
            case TokenType.EQUAL_EQUAL: opcode = "operator_equals"
            case TokenType.BANG_EQUAL: opcode = ""
            case TokenType.GREATER: opcode = "operator_gt"
            case TokenType.GREATER_EQUAL: opcode = ""
            case TokenType.LESS: opcode = "operator_lt"
            case TokenType.LESS_EQUAL: opcode = ""
            
            case TokenType.PLUS: opcode = "operator_add"
            case TokenType.MINUS: opcode = "operator_subtract"
            case TokenType.STAR: opcode = "operator_multiply"
            case TokenType.SLASH: opcode = "operator_divide"
            
            case TokenType.AND: opcode = "operator_and"
            case TokenType.OR: opcode = "operator_or"

            case _ : opcode = ""
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous, mendPrevious=False)


        left = self.left.convert(projectFile, sprite, block)
        right = self.right.convert(projectFile, sprite, block)

        leftName = opcodeMap[opcode]["inputs"][0]
        rightName = opcodeMap[opcode]["inputs"][1]

        projectFile.setBlockAttribute(sprite, block, "inputs", {leftName: left, rightName: right})

        return [2, block]
        
class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
    
    def getPrint(self) -> str:
        return f"group {self.expression.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        return self.expression.convert(projectFile, sprite, previous)
        
class Literal(Expr):
    def __init__(self, value):
        self.value = value
        
    def getPrint(self) -> str:
        match self.value:
            case str():
                return f'"{self.value}"'
            case _:
                return f"{self.value}"
            
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        return [1, [10, str(self.value)]]
        
class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator: Token = operator
        self.right: Expr = right
    
    def getPrint(self) -> str:
        return f"{self.operator} ({self.right.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        match self.operator.type:
            case TokenType.BANG:
                opcode = "operator_not"
            case TokenType.MINUS:
                opcode = "operator_subtract"
            case _:
                opcode = ""
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous, mendPrevious=False)

        right = self.right.convert(projectFile, sprite, block)

        if opcode == "operator_not":
            projectFile.setBlockAttribute(sprite, block, "inputs", {"OPERAND": right})
        elif opcode == "operator_subtract":
            projectFile.setBlockAttribute(sprite, block, "inputs", {"NUM1": [1, [10, "0"]], "NUM2": right})

        return [2, block]
    
class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee: Expr = callee
        self.paren: Token = paren
        self.arguments: list[Expr] = arguments
    
    def getPrint(self):
        listPrintArgs = [arg.getPrint() for arg in self.arguments]
        printArgs = ", ".join(listPrintArgs)
        return f"{self.callee.getPrint()} {self.paren} ({printArgs})"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        callee = self.callee.convert(projectFile, sprite, previous)
        assert isinstance(callee, Token), "Function call must have callee as callable object"
        

class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
        
    def getPrint(self):
        return f"{self.name}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        if self.name.lexeme in opcodeMap:
            return self.name
        
        if projectFile.isVar(sprite, self.name.lexeme):
            return [2, [12, self.name.lexeme, self.name.lexeme]]

class Stmt(Grammar):
    def convert(self, projectFile: ProjectFile, sprite: str, previous: str | None) -> Any:
        ...

class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements: list[Stmt] = statements
    
    def getPrint(self) -> str:
        output = []
        for statement in self.statements:
            output.append(statement.getPrint())
        return f"{'\n'.join(output)}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        prev = previous
        references = []
        for statement in self.statements:
            references.append(statement.convert(projectFile, sprite, prev))
            prev = unpack(references[-1], 1)

        if len(references) > 0:
            return unpack(references[0]), unpack(references[-1], 1)
        return None
    
class Expression(Stmt):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
        
    def getPrint(self) -> str:
        return f"{self.expression.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        return self.expression.convert(projectFile, sprite, previous)
        
class Print(Stmt):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression

    def getPrint(self) -> str:
        return f"print ({self.expression.getPrint()})"

class Return(Stmt):
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword: Token = keyword
        self.value: Expr | None = value
    
    def getPrint(self) -> str:
        value = ""
        if not self.value is None:
            value = self.value.getPrint()
        return f"{self.keyword.lexeme} {value}"
    
class Var(Stmt):
    def __init__(self, name: Token, initializer: Expr | None) -> None:
        self.name: Token = name
        self.initializer: Expr | None = initializer
        
    def getPrint(self) -> str:
        if self.initializer == None:
            value = None
        else:
            value = self.initializer.getPrint()
        return f"var {self.name} {value}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        block = projectFile.addBlock("data_setvariableto", {}, {"VARIABLE": [self.name.lexeme, self.name.lexeme]}, False, sprite, previous)

        value = [1, [10, None]]
        if not self.initializer is None:
            value = self.initializer.convert(projectFile, sprite, block)

        if value[1][1] is None:
            value[1][1] = ""
        
        value[1][1] = str(value[1][1])
        
        projectFile.define(sprite, self.name.lexeme, value[1][1])
        projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value})
        return block

class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: Stmt) -> None:
        self.name: Token = name
        self.params: list[Token] = params
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        params = ", ".join([str(param) for param in self.params])
        return f"func {self.name} ({params}) {{{self.body}}}"

class IfStmt(Stmt):
    def __init__(self, condition: Expr, thenBranch: Stmt, elseBranch: Stmt | None) -> None:
        self.condition: Expr = condition
        self.thenBranch: Stmt = thenBranch
        self.elseBranch: Stmt | None = elseBranch

    def getPrint(self) -> str:
        return f"if ({self.condition.getPrint()}) {{{self.thenBranch.getPrint()}}}"
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        if self.elseBranch is None:
            opcode = "control_if"
        else:
            opcode = "control_if_else"
        
        block = projectFile.addBlock(opcode, {}, {}, False, sprite, previous)

        condition = self.condition.convert(projectFile, sprite, block)
        
        thenBranch = unpack(self.thenBranch.convert(projectFile, sprite, block))
        thenBranch = [2, thenBranch]
        
        inputs = {"CONDITION" : condition, "SUBSTACK": thenBranch}        

        if not self.elseBranch is None:
            elseBranch = unpack(self.elseBranch.convert(projectFile, sprite, block))
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
    
    def convert(self, projectFile: ProjectFile, sprite: str, previous):
        block = projectFile.addBlock("control_repeat_until", {}, {}, False, sprite, previous)
        expression = Unary(Token(TokenType.BANG, "!", "!", 0), self.expression)
        expression = expression.convert(projectFile, sprite, block)
        statement = unpack(self.statement.convert(projectFile, sprite, block))
        statement = [2, statement]
        projectFile.setBlockAttribute(sprite, block, "inputs", {"CONDITION": expression, "SUBSTACK": statement})
        projectFile.setBlockAttribute(sprite, block, "next", None)
        return block
        
    
class CostumeStmt(Stmt):
    def __init__(self, name: Token, path: Token) -> None:
        self.name: Token = name
        self.path: Token = path
    
    def convert(self, projectFile: ProjectFile, sprite, previous):
        projectFile.addCostume(sprite, self.name.lexeme, self.path.lexeme, (1, 1))
        return previous

class FileStmt(Grammar):
    def convert(self, projectFile: ProjectFile):
        ...

class Sprite(FileStmt):
    def __init__(self, name: Token, body: Stmt) -> None:
        self.name: Token = name
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        return f"sprite {self.name.lexeme} {{{self.body.getPrint()}}}"
    
    def convert(self, projectFile: ProjectFile):
        isStage = self.name.lexeme == "Stage"
        projectFile.addSprite(self.name.lexeme, isStage)
        self.body.convert(projectFile, self.name.lexeme, None)

def printAST(grammar: Grammar):
    print(f"{grammar.getPrint()}")