from pathlib import Path
from src.compiler import fillCommands
from src.fileHandler import genTokens

def test_sprites():
    fileName = Path().cwd() / "tests/testCode/entireTest.scratch"
    tokens = genTokens(fileName)
    print(tokens)
    sprites = fillCommands("testCode", tokens, [], None, fileName, 1, [{}, {}])
    print(sprites)
    assert 1 == 1