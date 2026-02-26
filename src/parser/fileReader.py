from pathlib import Path

def loadFile(fileName) -> str:
    filePath: Path = Path(fileName).resolve()
    print(filePath)
    with open(fileName, "r") as file:
        fileData = ""
        for line in file:
            fileData += line
    
    return fileData