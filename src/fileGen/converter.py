from src.fileGen.projectFile import ProjectFile
from src.parser.StatementGrammar import *

class FileGenerator:
    def __init__(self, ast: list[FileStmt]) -> None:
        self.file = ProjectFile()
        self.AST = ast
    
    def generate(self) -> ProjectFile:
        for statement in self.AST:
            statement.convert(self.file)

        return self.file