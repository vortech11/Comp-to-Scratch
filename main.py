# nuitka-project: --mode=app
# nuitka-project: --python-flag=safe_path
# nuitka-project: --python-flag=no_site
# nuitka-project: --python-flag=isolated
# nuitka-project: --python-flag=dont_write_bytecode
# nuitka-project: --include-package=src
# nuitka-project: --include-package-data=src
# nuitka-project: --remove-output
# nuitka-project: --output-filename=scratch-{OS}-{Arch}
# nuitka-project: --linux-icon=./scratch-docs/docs/assets/cat.png
# nuitka-project: --windows-icon-from-ico=./scratch-docs/docs/assets/cat.ico

import json
from zipfile import ZipFile
from pathlib import Path
from shutil import copyfile
import sys
import warnings
import logging
logger = logging.getLogger(__name__)

from src.parser.fileReader import loadFile
from src.parser.scanner import Scanner
from src.parser.parser import Parser
from src.fileGen.converter import FileGenerator
from src.parser.StatementGrammar import formatAST

scratchCompVersion = "2.0.7S"
outputFolderName = "build"

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
    loggingLevel = logging.INFO
    #loggingLevel = logging.DEBUG
    logging.basicConfig(level=loggingLevel)
    logger.info("Started")

    if len(sys.argv) == 0:
        print("No file Selected!")
        exit()

    if not Path(sys.argv[1]).exists():
        print(f"File '{sys.argv[1]}' does not exist.")
        exit()
    
    filePath: Path = Path(sys.argv[1]).resolve()

    (filePath.parent / outputFolderName).mkdir(exist_ok=True)

    fileText = loadFile(filePath)
    scanner = Scanner(fileText, str(filePath))
    tokens = scanner.scanTokens()
    parser = Parser(tokens, filePath)
    fileAST = parser.parse()
    logger.debug(formatAST(fileAST))
    generator = FileGenerator(fileAST)
    project = generator.generate()
    saveFile(filePath, project.fileDict, project.files)
            
    logger.info("Finished")
            
if __name__ == "__main__":
    main()