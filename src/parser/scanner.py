from enum import Enum, auto
from pathlib import Path
import importlib.resources as resources
from sys import exit
import logging
logger = logging.getLogger(__name__)

from re import sub
from json import load

aliases: dict = {}

def loadAliases():
    global aliases
    assert isinstance(__package__, str)
    ROOT_PACKAGE = __package__.split('.')[0]
    PROJECT_ROOT = Path(resources.files(ROOT_PACKAGE)) # type: ignore
    filePath = PROJECT_ROOT / "parser/opcodeMacros.json"
    with open(filePath) as file:
        aliases = load(file)

loadAliases()

from pathlib import Path

class TokenType(Enum):
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    DOT = auto()
    SEMICOLON = auto()
    
    PLUS = auto()
    PLUS_EQUAL = auto()
    MINUS = auto()
    MINUS_EQUAL = auto()
    STAR = auto()
    STAR_EQUAL = auto()
    SLASH = auto()
    SLASH_EQUAL = auto()

    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUNC = auto()
    FOR = auto()
    IF = auto()
    NULL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()

    SPRITE = auto()
    COSTUME = auto()
    SOUND = auto()

    LIST = auto()
    DUMB_POINTER = auto()
    SMART_POINTER = auto()

    IMPORT = auto()
    EXPORT = auto()
    REQUIRE = auto()

    DEL = auto()

    LEFT_ARROW = auto()

    LOOP = auto()

keywords = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "func": TokenType.FUNC,
    "if": TokenType.IF,
    "null": TokenType.NULL,
    "or": TokenType.OR,
    "DEBUG": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
    "sprite": TokenType.SPRITE,
    "costume": TokenType.COSTUME,
    "sound": TokenType.SOUND,
    "list": TokenType.LIST,
    "import": TokenType.IMPORT,
    "export": TokenType.EXPORT,
    "require": TokenType.REQUIRE,
    "ptr": TokenType.SMART_POINTER,
    "dptr": TokenType.DUMB_POINTER,
    "del": TokenType.DEL,
    "loop": TokenType.LOOP,
}

class Token:
    def __init__(self, type: TokenType, lexeme: str="", literal=None, line: int=0, filePath: Path = Path()) -> None:
        self.type: TokenType = type
        self.lexeme: str = lexeme
        self.literal = literal
        self.filePath: Path = Path(filePath)
        self.line: int = line
        
    def __repr__(self):
        return f"{self.type}"
    
    def __str__(self):
        #return f"{self.type} {self.lexeme} {self.literal} {self.line}"
        return f"{self.type} {self.lexeme}"
        #return f"{self.type}"

class Scanner:
    def __init__(self, source: str, filePath: str) -> None:
        for key, value in aliases.items():
            source = sub(key, value, source)
        self.source: str = source
        self.filePath: str = filePath
        self.tokens: list[Token] = []
        self.start: int = 0
        self.current: int = 0
        self.line: int = 1

    def isAtEnd(self, offset=0) -> bool:
        return self.current + offset >= len(self.source)
    
    def getChar(self) -> str:
        return self.source[self.current]
    
    def getNextChar(self, offset=0) -> str:
        if self.isAtEnd(1+offset):
            return "\0"
        return self.source[self.current + 1 + offset]
    
    def advance(self) -> None:
        self.current += 1
    
    def addToken(self, type, literal=None):
        lexeme = self.source[self.start:self.current+1]
        self.tokens.append(Token(type, lexeme, literal, self.line, Path(self.filePath)))
        
    def scanString(self):
        self.start += 1
        while not self.getNextChar() in ['"', "\0"]:
            self.advance()
        if self.getNextChar() == "\0":
            logger.error(f"{self.line} | Error: Unterminated String.")
            exit()
        
        self.addToken(TokenType.STRING, self.source[self.start:self.current+1])
        self.advance()
    
    def scanDigit(self):
        while self.getNextChar().isdigit():
            self.advance()
        if self.getNextChar() == "." and self.getNextChar(1).isdigit():
            self.advance()
            while self.getNextChar().isdigit():
                self.advance()
        self.addToken(TokenType.NUMBER, float(self.source[self.start:self.current+1]))
        
    def identifier(self):
        while self.getNextChar().isalnum() or self.getNextChar() == "_":
            self.advance()
        text = self.source[self.start:self.current+1]
        if text in keywords:
            type: TokenType = keywords[text]
            self.addToken(type)
        else:
            self.addToken(TokenType.IDENTIFIER)
    
    def scanToken(self) -> None:
        char = self.getChar()
        match char:
            case '(': self.addToken(TokenType.LEFT_PAREN)
            case ')': self.addToken(TokenType.RIGHT_PAREN)
            case '{': self.addToken(TokenType.LEFT_BRACE)
            case '}': self.addToken(TokenType.RIGHT_BRACE)
            case '[': self.addToken(TokenType.LEFT_BRACKET)
            case ']': self.addToken(TokenType.RIGHT_BRACKET)
            case ',': self.addToken(TokenType.COMMA)
            case '.': self.addToken(TokenType.DOT)
            case ';': self.addToken(TokenType.SEMICOLON)
            
            case '+': 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.PLUS_EQUAL)
                else:
                    self.addToken(TokenType.PLUS)
            case '-': 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.MINUS_EQUAL)
                else:
                    self.addToken(TokenType.MINUS)
            case '*': 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.STAR_EQUAL)
                else:
                    self.addToken(TokenType.STAR)
            
            case "!": 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.BANG_EQUAL)
                else:
                    self.addToken(TokenType.BANG)
            case "=": 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.EQUAL_EQUAL)
                else:
                    self.addToken(TokenType.EQUAL)
            case ">": 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.GREATER_EQUAL)
                else:
                    self.addToken(TokenType.GREATER)
            case "<": 
                if self.getNextChar() == "=":
                    self.advance()
                    self.addToken(TokenType.LESS_EQUAL)
                elif self.getNextChar() == "<":
                    self.advance()
                    self.addToken(TokenType.LEFT_ARROW)
                else:
                    self.addToken(TokenType.LESS)
            
            case "/":
                if self.getNextChar() == "/":
                    while not self.getNextChar() in ["\n", "\0"]:
                        self.advance()
                elif self.getNextChar(1) == "=":
                    self.advance()
                    self.addToken(TokenType.SLASH_EQUAL)
                else:
                    self.addToken(TokenType.SLASH)
                    
            case '"': self.scanString()
                    
            case " " | "\r" | "\t": pass
                    
            case "\n": self.line += 1
            
            case _: 
                if char.isdigit():
                    self.scanDigit()
                elif char.isalpha() or char == "_":
                    self.identifier()
                else:
                    logger.error(f"{self.line} | Error: Unexpected character {char}")
                    exit()
        
        self.advance()

    def scanTokens(self) -> list[Token]:
        while not self.isAtEnd():
            self.start = self.current
            self.scanToken()
        
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens