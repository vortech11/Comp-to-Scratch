import logging
logger = logging.getLogger(__name__)

from src.fileGen.envObjects import Token

class Grammar:
    def getPrint(self) -> str:
        return f"()"
    