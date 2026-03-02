import logging
logger = logging.getLogger(__name__)

from src.fileGen.envObjects import Token

class Grammar:
    def getPrint(self) -> str:
        return f"()"
    
def error(token: Token, message: str):
    logger.error(f"From {token.filePath.name} on line {token.line}: {message}")
    logger.error("Error found in converting file")
    assert False, "Exiting..."