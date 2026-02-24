from src.parser.scanner import Token

class ObjMethod:
    def __init__(self, object: Token, name: Token) -> None:
        self.object = object
        self.name = name
