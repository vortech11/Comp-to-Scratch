from src.parser.StatementGrammar import *
from src.parser.scanner import Scanner
from src.parser.fileReader import loadFile
from pathlib import Path
import importlib.resources as resources
import logging
logger = logging.getLogger(__name__)

class Parser:
    def __init__(self, tokens: list[Token], directory, parent=None, defaultSprite=None):
        self.current: int = 0
        self.tokens: list[Token] = tokens
        self.directory: Path = directory
        self.requires: dict = {}
        self.parent: Parser | None = parent

        self.currentSprite = None
        self.defaultSprite = defaultSprite

    def isPathPackage(self, path) -> Path | None:
        assert isinstance(__package__, str)
        ROOT_PACKAGE = __package__.split('.')[0]
        PROJECT_ROOT = Path(resources.files(ROOT_PACKAGE)) # type: ignore
        filePath = PROJECT_ROOT / "packages" / path
        if filePath.exists():
            return filePath.resolve()
        return None

    def packageImported(self, packageName, context=1|2) -> bool:
        match context:
            case 1:
                if packageName in self.requires.keys:
                    return True
            case 2:
                if not self.currentSprite is None:
                    if packageName in self.requires[self.currentSprite]:
                        return True
        if not self.parent is None:
            return self.parent.packageImported(packageName, context)
        return False
    
    def updateRequirements(self, sprite, packageName):
        if sprite is None:
            if self.parent is None:
                self.requires[packageName] = None
                return
            self.parent.updateRequirements(sprite, packageName)
            return
        if self.currentSprite == sprite:
            self.requires[sprite][packageName] = None
            return
        if not self.parent is None:
            self.parent.updateRequirements(sprite, packageName)
            return
        "🤔"

    def getToken(self, offset=0) -> Token:
        return self.tokens[self.current + offset]
        
    def getNextToken(self, offset = 0) -> Token:
        return self.tokens[self.current + 1 + offset]
    
    def isAtEnd(self, offset=0) -> bool:
        return self.getToken(offset).type == TokenType.EOF
        
    def advance(self):
        self.current += 1
    
    """
    Checks if the NEXT token is in an input list and ADVANCES to next token if true
    Optional advance
    Optional check offset
    """
    def match(self, tokenTypes: list[TokenType], advance=True, offset=0):
        matching = self.getNextToken(offset).type in tokenTypes
        if matching and advance: 
            self.advance()
        return matching

    def error(self, token: Token, message: str):
        lexeme = None
        if token.type == TokenType.EOF:
            lexeme = "at end"
        else:
            lexeme = f"at '{token.lexeme}'"
        logger.error(f"From {token.filePath.name} on line {token.line} {lexeme}: {message}")
        logger.error("Error found in parsing file. Exiting...")
        exit()
    
    def consume(self, type: TokenType, message, offset=0, advance=True):
        if self.match([type], advance, offset):
            return self.getToken()
        
        self.error(self.getNextToken(), message)
        return Token(TokenType.NULL, "", None, 0)
    
    def expression(self):
        return self.assignment()
    
    def assignment(self) -> Expr:
        expr: Expr = self.logical_or()
        
        if self.match([TokenType.EQUAL, TokenType.PLUS_EQUAL, TokenType.MINUS_EQUAL, TokenType.STAR_EQUAL, TokenType.SLASH_EQUAL]):
            assignment: Token = self.getToken()
            self.advance()
            value = self.assignment()
            
            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, assignment, value)
            elif isinstance(expr, ListIndex):
                return ListSetIndex(expr, assignment, value)
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value)
            
            self.error(assignment, "Invalid assignment target.")
        
        elif self.match([TokenType.LEFT_ARROW]):
            assignment: Token = self.getToken()
            self.advance()
            func = self.funcCall()
            if isinstance(expr, Variable):
                name = expr.name
                return SetPointerFunc(name, func)
            self.error(assignment, "Invalid assignment target.") 
            
        return expr
    
    def logical_or(self) -> Expr:
        expr: Expr = self.logical_and()
        
        if self.match([TokenType.OR]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.logical_and()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def logical_and(self) -> Expr:
        expr: Expr = self.equality()
        
        if self.match([TokenType.AND]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.equality()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def equality(self) -> Expr:
        expr: Expr = self.comparison()
        
        while self.match([TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.comparison()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def comparison(self) -> Expr:
        expr: Expr = self.term()
        
        while self.match([TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.term()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def term(self) -> Expr:
        expr: Expr = self.factor()
        
        while self.match([TokenType.MINUS, TokenType.PLUS]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.factor()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def factor(self) -> Expr:
        expr: Expr = self.unary()
        
        while self.match([TokenType.SLASH, TokenType.STAR]):
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.unary()
            expr = Binary(expr, operator, right)
            
        return expr
    
    def unary(self) -> Expr:
        if self.getToken().type in [TokenType.BANG, TokenType.MINUS]:
            operator: Token = self.getToken()
            self.advance()
            right: Expr = self.unary()
            return Unary(operator, right)
        
        return self.funcCall()
    
    def funcCall(self) -> Expr:
        expr: Expr = self.primary()

        while True:
            if self.match([TokenType.LEFT_PAREN]):
                expr = self.finishCall(expr)
            elif self.match([TokenType.DOT]):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            elif self.match([TokenType.LEFT_BRACKET], False):
                bracket = self.consume(TokenType.LEFT_BRACKET, "")
                self.advance()                
                tmp = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expect right bracket ']' after list index.")
                expr = ListIndex(expr, bracket, tmp)
            else:
                break
        
        return expr

    def finishCall(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []
        if not self.getNextToken().type == TokenType.RIGHT_PAREN:
            self.advance()
            arguments.append(self.expression())
            while self.match([TokenType.COMMA]):
                self.advance()
                arguments.append(self.expression())
        
        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments")
        return Call(callee, paren, arguments)

    def primary(self) -> Expr:
        match self.getToken().type:
            case TokenType.FALSE: return Literal(False)
            case TokenType.TRUE: return Literal(True)
            case TokenType.NULL: return Literal(None)
            case TokenType.NUMBER | TokenType.STRING: return Literal(self.getToken().literal)
            case TokenType.LEFT_PAREN: 
                self.advance()
                expr: Expr = self.expression()
                self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
                return Grouping(expr)
            
            case TokenType.THIS: return This(self.getToken())
            case TokenType.IDENTIFIER: return Variable(self.getToken())
            
            case _: 
                self.error(self.getToken(), "Expect expression")
                return Expr()
    
    def printStatement(self):
        value: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)
    
    def expressionStatement(self):
        expr: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Expression(expr)
    
    def ifStatement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after if.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.", offset=-1)
        
        thenBranch: Stmt = self.statement()
        elseBranch: Stmt | None = None
        if self.match([TokenType.ELSE]):
            self.advance()
            elseBranch = self.statement()
        
        return IfStmt(condition, thenBranch, elseBranch)
        
    def block(self):
        statements: list[Stmt] = []

        while not (self.getToken().type in [TokenType.RIGHT_BRACE]):
            statements.append(self.declaration())
            self.advance()
        
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.", -1, advance=False)
        block = Block(statements)
        return block
    
    def whileStatement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.", -1)
        body: Stmt = self.statement()

        return WhileStmt(condition, body)
    
    def forStatement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        
        initializer: Stmt | None = None
        condition: Expr | None = None
        increment: Expr | None = None

        if self.match([TokenType.SEMICOLON]):
            pass
        elif self.match([TokenType.VAR, TokenType.DUMB_POINTER, TokenType.SMART_POINTER]):
            initializer = self.varDeclaration()
        else:
            initializer = self.expressionStatement()

        if not self.getNextToken().type == TokenType.SEMICOLON:
            self.advance()
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        if not self.getNextToken().type == TokenType.RIGHT_PAREN:
            self.advance()
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        self.advance()

        body: Stmt = self.statement()


        if not increment is None:
            body = Block([
                body,
                Expression(increment)
            ])
        
        if condition is None: 
            condition = Literal(True)
        
        body = WhileStmt(condition, body)

        if not initializer is None:
            body = Block([
                initializer, 
                body
            ])
        
        return body
    
    def returnStatement(self):
        keyword: Token = self.getToken()
        value: Expr | None = None
        if not self.getNextToken().type == TokenType.SEMICOLON:
            self.advance()
            value = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)
    
    def importStmt(self):
        token = self.getToken()
        filePathToken = self.consume(TokenType.STRING, "Expect path to import after import keyword.")
        possiblePackage = self.isPathPackage(filePathToken.lexeme)
        if possiblePackage is None:
            filePath: Path = self.directory.parent / Path(filePathToken.lexeme)
        else:
            filePath = possiblePackage
        if token.type == TokenType.REQUIRE:
            if self.packageImported(str(filePath), 2):
                self.consume(TokenType.SEMICOLON, "Expect semicolon after import keyword.")
                return Block([])
            self.updateRequirements(self.defaultSprite, str(filePath))
        text = loadFile(filePath)
        scanner = Scanner(text, str(filePath))
        tokens = scanner.scanTokens()
        sprite = self.defaultSprite
        if not self.currentSprite is None:
            sprite = self.currentSprite
        parser = Parser(tokens, filePath, self, sprite)
        fullGramar = parser.parse()
        self.consume(TokenType.SEMICOLON, "Expect semicolon after import keyword.")

        exports = [fileStmt.body for fileStmt in fullGramar if isinstance(fileStmt, Export)]

        return Block(exports)
    
    def deleteStatement(self):
        varName = self.consume(TokenType.IDENTIFIER, "Expect pointer name after del keyword.")
        self.consume(TokenType.SEMICOLON, "Expect semicolon after varname in del statement.")
        return Delete(varName)

    def statement(self):
        match self.getToken().type:
            case TokenType.PRINT:
                self.advance()
                return self.printStatement()
            case TokenType.RETURN:
                return self.returnStatement()
            case TokenType.IF:
                return self.ifStatement()
            case TokenType.LEFT_BRACE:
                self.advance()
                return self.block()
            case TokenType.WHILE:
                return self.whileStatement()
            case TokenType.FOR:
                return self.forStatement()
            case TokenType.IMPORT | TokenType.REQUIRE:
                return self.importStmt()
            case TokenType.DEL:
                return self.deleteStatement()
            case _:
                return self.expressionStatement()
    
    def varDeclaration(self):
        declarationType: Token = self.getToken()
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        
        initializer: Expr | list[Expr] | None = None
        if self.match([TokenType.EQUAL]):
            self.advance()
            if declarationType.type in [TokenType.VAR, TokenType.DUMB_POINTER, TokenType.SMART_POINTER]:
                initializer = self.expression()
            elif declarationType.type == TokenType.LIST:
                if not self.match([TokenType.RIGHT_BRACKET]):
                    initializer = []
                    while not self.getToken().type == TokenType.RIGHT_BRACKET:
                        self.advance()
                        initializer.append(self.expression())
                        self.advance()
                else:
                    initializer = []
        elif self.match([TokenType.LEFT_ARROW]):
            self.advance()
            if declarationType.type in [TokenType.DUMB_POINTER, TokenType.SMART_POINTER]:
                func = self.funcCall()
                self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
                return DefPointerFunc(declarationType, name, func)
        
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(declarationType, name, initializer) # type: ignore
    
    def funcDeclaration(self, kind: str):
        name: Token = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")

        
        parameters: list[Token] = []
        if not self.getNextToken().type == TokenType.RIGHT_PAREN:
            parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))
            while self.match([TokenType.COMMA]):
                parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before " + kind + " body.")

        self.advance()

        body: Stmt = self.block()
        return Function(name, parameters, body)
    
    def costumeDeclaration(self):
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect name of costume.")
        path: Token = self.consume(TokenType.STRING, "Expect costume path after costume name.")
        self.consume(TokenType.SEMICOLON, "Expect semicolon after costume path.")

        return CostumeStmt(name, path)
    
    def declaration(self):
        match self.getToken().type:
            case TokenType.FUNC:
                return self.funcDeclaration("function")
            case TokenType.VAR | TokenType.LIST | TokenType.DUMB_POINTER | TokenType.SMART_POINTER:
                return self.varDeclaration()
            case TokenType.COSTUME:
                return self.costumeDeclaration()
            case _:
                return self.statement()
            
    def sprite(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect name of sprite after sprite keyword.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after sprite name.")
        self.advance()
        self.currentSprite = name.lexeme
        self.requires[name.lexeme] = {}
        body = self.block()
        self.currentSprite = self.defaultSprite
        return Sprite(name, body)
    
    def importFileStmt(self):
        token = self.getToken()
        filePathToken = self.consume(TokenType.STRING, f"Expect path to import after {token.lexeme} keyword.")
        possiblePackage = self.isPathPackage(filePathToken.lexeme)
        if possiblePackage is None:
            filePath: Path = self.directory.parent / Path(filePathToken.lexeme)
        else:
            filePath = possiblePackage
        if token.type == TokenType.REQUIRE:
            if self.packageImported(str(filePath), 1):
                return []
            self.requires[str(filePath)] = None
        text = loadFile(filePath)
        scanner = Scanner(text, str(filePath))
        tokens = scanner.scanTokens()
        parser = Parser(tokens, filePath, self)
        gramar = parser.parse()
        self.consume(TokenType.SEMICOLON, "Expect semicolon after import keyword.")
        return gramar
    
    def exportFileStmt(self):
        self.consume(TokenType.LEFT_BRACE, "Expect block statement after export keyword.")
        self.advance()
        body = self.block()
        return Export(body)
            
    def fileStatement(self):
        match self.getToken().type:
            case TokenType.SPRITE:
                return [self.sprite()]
            case TokenType.IMPORT | TokenType.REQUIRE:
                return self.importFileStmt()
            case TokenType.EXPORT:
                return [self.exportFileStmt()]
            case _:
                return []
    
    def parse(self) -> list[FileStmt]:
        tokenList = []
        while not self.isAtEnd():
            tokenList.extend(self.fileStatement())
            self.advance()
        return tokenList

        