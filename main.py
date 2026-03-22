# nuitka-project: --mode=app
# nuitka-project: --python-flag=safe_path
# nuitka-project: --python-flag=no_site
# nuitka-project: --python-flag=isolated
# nuitka-project: --python-flag=dont_write_bytecode
# nuitka-project: --include-package=src
# nuitka-project: --include-package-data=src
# nuitka-project: --remove-output
# nuitka-project-if: {OS} in {"Linux"}:
#   nuitka-project-if: {Arch} in {"x86_64"}:
#     nuitka-project: --output-filename=scratch-linux-x86_64
#   nuitka-project-if: {Arch} in ("arm64", "aarch64"):
#     nuitka-project: --output-filename=scratch-linux-arm64
# nuitka-project-if: {OS} in {"Windows"}:
#   nuitka-project: --output-filename=scratch-windows-x86_64.exe
# nuitka-project-if: {OS} in {"Darwin"}:
#   nuitka-project: --output-filename=scratch-darwin-x86_64
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
from time import perf_counter

from sys import exit

from src.parser.fileReader import loadFile
from src.parser.scanner import Scanner
from src.parser.parser import Parser
from src.fileGen.converter import FileGenerator
from src.parser.StatementGrammar import formatAST

scratchCompVersion = "2.1.0"
outputFolderName = "build"

def saveFile(filePath: Path, fileContents: dict, filesToCoppy: dict, projectName: str):
    filesToBeCompressed: list[Path] = []

    output = json.dumps(fileContents)
    with open(filePath.parent / outputFolderName / "project.json", "w") as file:
        file.write(output)

    filesToBeCompressed.append(Path(outputFolderName) / "project.json")

    for fromPath, toPath in filesToCoppy.items():
        path = filePath.parent / outputFolderName / toPath
        copyfile(filePath.parent / fromPath, path)
        filesToBeCompressed.append(path)


    with ZipFile(filePath.parent / outputFolderName / f"{projectName}.sb3", "w") as myzip:
        for file in filesToBeCompressed:
            myzip.write(filePath.parent / file, Path(file).name)

comandLineOptions: dict = {
    "-v --version": "Gets the version of the compiler.",
    "-help": "Prints the list of commands and arguments for the compiler.",
    "-name [ projectName ]": "Sets the name of the project."
}

comandKeyLength = max([len(key) for key in comandLineOptions.keys()])

def printHelp():
    print(f"Usage: scratch [option] ... [filename]")
    print(f"Options:")
    for arg, description in comandLineOptions.items():
        print(f"{arg:<{comandKeyLength}} : {description}")

def printVersion():
    print(f"Scratch Script Compiler v{scratchCompVersion}")

def main():
    loggingLevel = logging.INFO
    #loggingLevel = logging.DEBUG
    logging.basicConfig(
        level=loggingLevel,
        format='%(levelname)s - %(message)s'
    )

    sys.argv = sys.argv[1::]
    if len(sys.argv) == 0:
        printVersion()
        printHelp()
        exit()

    fileName = sys.argv[-1]
    if len(sys.argv) == 1 and fileName[0] == "-":
        fileName = None
        compilerOptions = [sys.argv[-1]]
    else:
        compilerOptions = sys.argv[:-1]
    
    projectName = None

    i = 0
    while i < len(compilerOptions):
        option = compilerOptions[i]
        match option:
            case "-v" | "--version":
                printVersion()
                exit()
            case "-help":
                printHelp()
                exit()
            case "-name":
                i += 1
                projectName = compilerOptions[i]
        i += 1

    if fileName is None:
        print(f"File name not specified.")
        print(f"Try running 'scratch [filename]'")
        exit()

    if not Path(fileName).exists():
        print(f"File '{fileName}' does not exist.")
        exit()
    
    logger.info("Started")
    startTime = perf_counter()
    
    filePath: Path = Path(fileName).resolve()

    if projectName == None:
        projectName = filePath.stem

    (filePath.parent / outputFolderName).mkdir(exist_ok=True)

    fileText = loadFile(filePath)
    scanner = Scanner(fileText, str(filePath))
    tokens = scanner.scanTokens()
    parser = Parser(tokens, filePath)
    fileAST = parser.parse()
    logger.debug(formatAST(fileAST))
    generator = FileGenerator(fileAST)
    project = generator.generate()
    saveFile(filePath, project.fileDict, project.files, projectName)
    
    endTime = perf_counter()
    totalTime = endTime - startTime
    logger.info("Finished")
    logger.info(f"Compile took {totalTime:.4f} seconds")
            
if __name__ == "__main__":
    main()
