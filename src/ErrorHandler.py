import logging
logger = logging.getLogger(__name__)

from src.parser.scanner import Token
from src.parser.scanner import TokenType
from sys import exit

def parseError(token: Token, message: str):
        lexeme = None
        if token.type == TokenType.EOF:
            lexeme = "at end"
        else:
            lexeme = f"at '{token.lexeme}'"
        logger.error(f"From {token.filePath.name} on line {token.line} {lexeme}: {message}")
        logger.error("Error found in parsing file. Exiting...")
        exit()

def convError(token: Token, message: str):
    logger.error(f"From {token.filePath.name} on line {token.line}: {message}")
    logger.error("Error found in converting file. Exiting...")
    #assert False, "Exiting..."
    exit()

def warn(token: Token, message: str):
    logger.error(f"WARNING: From {token.filePath.name} on line {token.line}: {message}")