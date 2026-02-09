from src.parser.scanner import Token, TokenType

from src.fileGen.projectFile import ProjectFile

class Grammar:
    def getPrint(self) -> str:
        return f"()"

class Expr(Grammar):
    def convert(self, projectFile: ProjectFile, sprite, previous):
        ...

class Assign(Expr):
    def __init__(self, name: Token, value: Expr) -> None:
        self.name: Token = name
        self.value: Expr = value
    
    def getPrint(self) -> str:
        return f"{self.name.lexeme} = {self.value.getPrint()}"

class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left: Expr = left
        self.operator: Token = operator
        self.right: Expr = right
        
    def getPrint(self) -> str:
        return f"{self.operator} ({self.left.getPrint()}) ({self.right.getPrint()})"
    
    def convert(self, projectFile: ProjectFile, sprite, previous=None):
        if previous is None:
            topLevel = True
        else:
            topLevel = False
        
        #left = self.left.convert(projectFile, sprite)
        #right = self.right.convert(projectFile, sprite)
        #
        #opcode = ""
        #
        #match self.operator.type:
        #    case TokenType.PLUS: opcode = "operator_add"
        #        
        #projectFile.addBlock(
        #    opcode, 
        #    {"NUM1": left, "NUM2": right}, 
        #    {}, 
        #    False, 
        #    topLevel, 
        #    sprite, 
        #    previous
        #)
        
class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
    
    def getPrint(self) -> str:
        return f"group {self.expression.getPrint()}"
        
class Literal(Expr):
    def __init__(self, value):
        self.value = value
        
    def getPrint(self) -> str:
        match self.value:
            case str():
                return f'"{self.value}"'
            case _:
                return f"{self.value}"
        
class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator: Token = operator
        self.right: Expr = right
    
    def getPrint(self) -> str:
        return f"{self.operator} ({self.right.getPrint()})"
    
class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee: Expr = callee
        self.paren: Token = paren
        self.arguments: list[Expr] = arguments
    
    def getPrint(self):
        listPrintArgs = [arg.getPrint() for arg in self.arguments]
        printArgs = ", ".join(listPrintArgs)
        return f"{self.callee.getPrint()} {self.paren} ({printArgs})"
    
    def convert(self, projectFile: ProjectFile, sprite: str):
        ...

class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
        
    def getPrint(self):
        return f"{self.name}"

class Stmt(Grammar):
    ...

class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements: list[Stmt] = statements
    
    def getPrint(self) -> str:
        output = []
        for statement in self.statements:
            output.append(statement.getPrint())
        return f"{'\n'.join(output)}"
    
    def convert(self, projectFile: ProjectFile, sprite: str):
        for statement in self.statements:
            statement.convert(projectFile, sprite) # type: ignore
    
class Expression(Stmt):
    def __init__(self, expression: Expr):
        self.expression: Expr = expression
        
    def getPrint(self) -> str:
        return f"{self.expression.getPrint()}"
        
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

class WhileStmt(Stmt):
    def __init__(self, expression: Expr, statement: Stmt) -> None:
        self.expression = expression
        self.statement = statement

    def getPrint(self) -> str:
        return f"while ({self.expression.getPrint()}) {{{self.statement.getPrint()}}}"
    
class CostumeStmt(Stmt):
    def __init__(self, name: Token, path: Token) -> None:
        self.name: Token = name
        self.path: Token = path
    
    def convert(self, projectFile: ProjectFile, sprite):
        projectFile.addCostume(sprite, self.name.lexeme, self.path.lexeme, (1, 1))

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
        self.body.convert(projectFile, self.name.lexeme) # type: ignore

def printAST(grammar: Grammar):
    print(f"{grammar.getPrint()}")