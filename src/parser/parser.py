from langGrammar import *
import logging
logger = logging.getLogger(__name__)

class Parser:
    def __init__(self, tokens: list[Token]):
        self.current: int = 0
        self.tokens: list[Token] = tokens
        
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
        logger.error(f"{token.line} {lexeme} {message}")
    
    def consume(self, type: TokenType, message, offset=0, advance=True):
        if self.match([type], advance, offset):
            return self.getToken()
        
        self.error(self.getNextToken(), message)
        return Token(TokenType.NULL, "", None, 0)
    
    def expression(self):
        return self.assignment()
    
    def assignment(self) -> Expr:
        expr: Expr = self.logical_or()
        
        if self.match([TokenType.EQUAL]):
            equals: Token = self.getToken()
            self.advance()
            value = self.assignment()
            
            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)
            
            self.error(equals, "Invalid assignment target.")
            
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
        if self.match([TokenType.ELSE], offset=-1):
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
        elif self.match([TokenType.VAR]):
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
            case _:
                return self.expressionStatement()
    
    def varDeclaration(self):
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        
        initializer: Expr | None = None
        if self.match([TokenType.EQUAL]):
            self.advance()
            initializer = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)
    
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
    
    def declaration(self):
        match self.getToken().type:
            case TokenType.FUNC:
                return self.funcDeclaration("function")
            case TokenType.VAR:
                return self.varDeclaration()
            case _:
                return self.statement()
    
    def parse(self):
        tokenList = []
        while not self.isAtEnd():
            tokenList.append(self.declaration())
            self.advance()
        return tokenList

        