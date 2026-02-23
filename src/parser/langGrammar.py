from json import load

from src.parser.scanner import Token, TokenType

from src.fileGen.projectFile import ProjectFile
from src.fileGen.environment import Environment

from typing import Any

with open("src/OpcodeMap.json") as map:
    opcodeMap = load(map)

def unpack(value, index=0):
    return value[index] if isinstance(value, (tuple, list)) else value

class Grammar:
    def getPrint(self) -> str:
        return f"()"

class Expr(Grammar):
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous: str | None) -> Any:
        ...

class Assign(Expr):
    def __init__(self, name: Token, assignment: Token, value: Expr) -> None:
        self.name: Token = name
        self.assignment: Token = assignment
        self.value: Expr = value
    
    def getPrint(self) -> str:
        return f"{self.name.lexeme} = {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous):
        block = projectFile.addBlock("data_setvariableto", {}, {"VARIABLE": [self.name.lexeme, projectFile.getVarId(sprite, self.name.lexeme)]}, False, sprite, previous)
        
        operator = Token(TokenType.PLUS)
        match self.assignment.type:
            case TokenType.EQUAL:
                value = self.value.convert(projectFile, environment, sprite, block)
                projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value})
                return block
            case TokenType.PLUS_EQUAL: operator = Token(TokenType.PLUS)
            case TokenType.MINUS_EQUAL: operator = Token(TokenType.MINUS)
            case TokenType.STAR_EQUAL: operator = Token(TokenType.STAR)
            case TokenType.SLASH_EQUAL: operator = Token(TokenType.SLASH)
        
        subGramar = Binary(Variable(self.name), operator, self.value)
        subBlock = subGramar.convert(projectFile, environment, sprite, block)
        projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": subBlock})
        return block

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

        projectFile.setBlockAttribute(sprite, block, "inputs", {leftName: left, rightName: right})

        return [2, block]
        
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
        return [1, [10, str(self.value)]]
        
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
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        callee = self.callee.convert(projectFile, environment, sprite, previous)
        assert isinstance(callee, Token), "Function call must have callee as callable object"
        if callee.lexeme in opcodeMap:
            funcInfo = opcodeMap[callee.lexeme]
            assert len(self.arguments) <= len(funcInfo["inputs"]), "Function arity must be equal or less than the number of inputs"
            block = projectFile.addBlock(callee.lexeme, {}, {}, False, sprite, previous)
            inputs = {}
            arguments = {}
            for index, input in enumerate(self.arguments):
                match funcInfo["inputtype"][index]:
                    case "text":
                        inputs[funcInfo["inputs"][index]] = input.convert(projectFile, environment, sprite, block)
                    case "dropdown":
                        arguments[funcInfo["inputs"][index]] = input.convert(projectFile, environment, sprite, block)
                    case "menu":
                        ...

            projectFile.setBlockAttribute(sprite, block, "inputs", inputs)
            projectFile.setBlockAttribute(sprite, block, "arguments", arguments)
            projectFile.setBlockAttribute(sprite, block, "next", None)
            return block
        
        func = projectFile.getFunc(sprite, callee.lexeme)
        block = projectFile.addBlock("procedures_call", {}, {}, False, sprite, previous)

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
            inputs[func["parameterIdList"][index]] = input

        projectFile.setBlockAttribute(sprite, block, "inputs", inputs)
        projectFile.setBlockAttribute(sprite, block, "mutation", mutation)

        return block

class Get(Expr):
    def __init__(self, object: Expr, name: Token) -> None:
        self.object: Expr = object
        self.name: Token = name

    def getPrint(self):
        return f"{self.object.getPrint()}.{self.name}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        object = self.object.convert(projectFile, environment, sprite, previous)
        assert isinstance(object, Token), "Object Get must act upon an object"
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
            return [2, block]

        if projectFile.isSprite(object.lexeme):
            match self.name.lexeme:
                case "volume":
                    ...
    
class Set(Expr):
    def __init__(self, object: Expr, name: Token, value: Expr) -> None:
        self.object: Expr = object
        self.name: Token = name
        self.value: Expr = value

    def getPrint(self):
        return f"{self.object.getPrint()}.{self.name} = {self.value.getPrint()}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        object = self.object.convert(projectFile, environment, sprite, previous)
        assert isinstance(object, Token), "Object Get must act upon an object"
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

class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
        
    def getPrint(self):
        return f"{self.name}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if self.name.lexeme in opcodeMap:
            return self.name
        
        if projectFile.isSprite(self.name.lexeme):
            return self.name
        
        if projectFile.doesFuncExist(sprite, self.name.lexeme):
            return self.name
        
        if environment.isFuncParam(self.name.lexeme):
            inputName = self.name.lexeme
            block = projectFile.addBlock("argument_reporter_boolean", {}, {"VALUE": [inputName]}, False, sprite, previous, mendPrevious=False)
            return [2, block]
        
        if projectFile.isVar(sprite, self.name.lexeme):
            return [2, [12, self.name.lexeme, projectFile.getVarId(sprite, self.name.lexeme)]]

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
        topBlock = None
        bottomBlock = previous
        for statement in self.statements:
            block = statement.convert(projectFile, environment, sprite, bottomBlock)
            if (not unpack(block, 1) == previous) and topBlock is None:
                topBlock = unpack(block, 0)
            bottomBlock = unpack(block, 1)

        if topBlock is None:
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
    def __init__(self, declarationType: Token, name: Token, initializer: Expr | None) -> None:
        self.declarationType: Token = declarationType
        self.name: Token = name
        self.initializer: Expr | None = initializer
        
    def getPrint(self) -> str:
        if self.initializer == None:
            value = None
        else:
            value = self.initializer.getPrint()
        return f"var {self.name} {value}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        if self.declarationType.type == TokenType.VAR:
            projectFile.createVar(sprite, self.name.lexeme, "")
            block = projectFile.addBlock("data_setvariableto", {}, {"VARIABLE": [self.name.lexeme, projectFile.getVarId(sprite, self.name.lexeme)]}, False, sprite, previous)

            value = [1, [10, None]]
            if not self.initializer is None:
                value = self.initializer.convert(projectFile, environment, sprite, block)

            if value[0] == 2:
                literal = ""
            elif value[1][1] is None:
                value[1][1] = ""
                literal = ""
            else:
                value[1][1] = str(value[1][1])
                literal = value[1][1]
            
            projectFile.setVarDefault(sprite, self.name.lexeme, literal)
            projectFile.setBlockAttribute(sprite, block, "inputs", {"VALUE": value})
            return block
        if self.declarationType.type == TokenType.LIST:
            ...

class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: Stmt) -> None:
        self.name: Token = name
        self.params: list[Token] = params
        self.body: Stmt = body
    
    def getPrint(self) -> str:
        params = ", ".join([str(param) for param in self.params])
        return f"func {self.name} ({params}) {{{self.body}}}"
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite: str, previous):
        match self.name.lexeme:
            case "main": opcode = "event_whenflagclicked"
            case "keyPressed": opcode = "event_whenkeypressed"
            case _: opcode = None

        if not opcode is None:
            params: list[Expr] = [Literal(value) for value in self.params]
            block = Call(Variable(Token(TokenType.IDENTIFIER, opcode, None, 0)), Token(TokenType.LEFT_PAREN, "(", None, 0), params).convert(projectFile, environment, sprite, None)
            endBlock = self.body.convert(projectFile, environment, sprite, block)
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

        textParamData = []
        for paramlist in [ids, names, defaults]:
            #paramlist = ["false" if item is False else "true" if item is True else item for item in paramlist]
            textParamData.append(f"[{",".join([f"\"{item}\"" for item in paramlist])}]")

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

        funcEnvironment = Environment(environment, {"name": self.name.lexeme, "argumentNames": names,})
        projectFile.createFunc(sprite, self.name.lexeme, proccode, ids, textParamData[0], warp)

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
        
        inputs = {"CONDITION" : condition, "SUBSTACK": thenBranch}        

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
        projectFile.setBlockAttribute(sprite, block, "inputs", {"CONDITION": expression, "SUBSTACK": statement})
        projectFile.setBlockAttribute(sprite, block, "next", None)
        return block
        
    
class CostumeStmt(Stmt):
    def __init__(self, name: Token, path: Token) -> None:
        self.name: Token = name
        self.path: Token = path
    
    def convert(self, projectFile: ProjectFile, environment: Environment, sprite, previous):
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
        spriteEnvironment = Environment(None, None)
        self.body.convert(projectFile, spriteEnvironment, self.name.lexeme, None)

def printAST(grammar: Grammar):
    print(f"{grammar.getPrint()}")