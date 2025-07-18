import json
import zipfile
from pathlib import Path
from src.interpreter import fillCommands
import sys
import warnings
import logging
logger = logging.getLogger(__name__)
from src.parser import genTokens

def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Started")
    scratchCompVersion = "0.3.0"

    outputFolderName = "build"

    assert len(sys.argv) > 1, "No file Selected!"

    assert Path(sys.argv[1]).exists(), f"File '{sys.argv[1]}' does not exist."

    (Path(sys.argv[1]).parent / outputFolderName).mkdir(exist_ok=True)

    tokens = genTokens(sys.argv[1])

    output = {"targets":[], "monitors":[], "extensions":[], "meta":{
                    "semver": "3.0.0",
                    "vm": "11.0.0-beta.2",
                    "agent": "Scratch Compiler v" + scratchCompVersion
                }
            }

    filesToBeCompressed = [outputFolderName + "/project.json"]

    blockIndex = 1

    tokens = genTokens(sys.argv[1])
    output["targets"], filesToBeCompressed = fillCommands(Path(sys.argv[1]).resolve(), tokens, filesToBeCompressed, outputFolderName, blockIndex, [{}, {}])

    output = json.dumps(output)
    with open(Path(sys.argv[1]).parent / outputFolderName / "project.json", "w") as file:
        file.write(output)

    with zipfile.ZipFile(Path(sys.argv[1]).parent / outputFolderName / "test.sb3", "w") as myzip:
        for file in filesToBeCompressed:
            myzip.write(Path(sys.argv[1]).parent / file, Path(file).name)
            
    logger.info("Finished")
            
if __name__ == "__main__":
    main()