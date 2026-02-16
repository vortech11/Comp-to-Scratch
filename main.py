import json
from zipfile import ZipFile
from pathlib import Path
from shutil import copyfile
import sys
import warnings
import logging
logger = logging.getLogger(__name__)

from src.parser.scanner import Scanner
from src.parser.parser import Parser
from src.fileGen.converter import FileGenerator

scratchCompVersion = "0.3.0b"
outputFolderName = "build"

def loadFile(filePath: Path) -> str:
    with open(filePath, "r") as file:
        fileData = ""
        for line in file:
            fileData += line
    
    return fileData

def saveFile(filePath: Path, fileContents: dict, filesToCoppy: dict):
    filesToBeCompressed: list[Path] = []

    output = json.dumps(fileContents)
    with open(filePath.parent / outputFolderName / "project.json", "w") as file:
        file.write(output)

    filesToBeCompressed.append(Path(outputFolderName) / "project.json")

    for fromPath, toPath in filesToCoppy.items():
        path = filePath.parent / outputFolderName / toPath
        copyfile(filePath.parent / fromPath, path)
        filesToBeCompressed.append(path)


    with ZipFile(filePath.parent / outputFolderName / "test.sb3", "w") as myzip:
        for file in filesToBeCompressed:
            myzip.write(filePath.parent / file, Path(file).name)

def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Started")

    assert len(sys.argv) > 1, "No file Selected!"

    assert Path(sys.argv[1]).exists(), f"File '{sys.argv[1]}' does not exist."
    filePath: Path = Path(sys.argv[1]).resolve()

    (filePath.parent / outputFolderName).mkdir(exist_ok=True)

    fileText = loadFile(filePath)
    scanner = Scanner(fileText)
    tokens = scanner.scanTokens()
    parser = Parser(tokens)
    fileAST = parser.parse()
    generator = FileGenerator(fileAST)
    project = generator.generate()
    saveFile(filePath, project.fileDict, project.files)
            
    logger.info("Finished")
            
if __name__ == "__main__":
    main()