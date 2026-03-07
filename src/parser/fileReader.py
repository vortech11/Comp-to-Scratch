def loadFile(fileName) -> str:
    with open(fileName, "r") as file:
        fileData = ""
        for line in file:
            fileData += line
    
    return fileData