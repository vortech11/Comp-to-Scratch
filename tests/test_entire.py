from pathlib import Path
from src.compiler import fillCommands
from src.fileHandler import genTokens

def test_sprites():
    fileName = Path().cwd() / "tests/testCode/entireTest.scratch"
    tokens = genTokens(fileName)
    sprites = fillCommands(Path().cwd() / "tests/testCode", tokens, [], None, fileName, 1, [{}, {}])[0]
    print(sprites)
    assert sprites == [
        {'isStage': True, 
            'name': 'Stage', 
            'variables': {}, 
            'lists': {}, 
            'broadcasts': {}, 
            'blocks': {}, 
            'comments': {}, 
            'currentCostume': 0, 
            'costumes': [], 
            'sounds': [], 
            'volume': 100, 
            'layerOrder': 0, 
            'tempo': 60, 
            'videoTransparency': 50, 
            'videoState': 'on', 
            'textToSpeechLanguage': None
        }, 
        {
            'isStage': False, 
            'name': 'cat', 
            'variables': {'i9': ['i', 0]}, 
            'lists': {'distances3': ['distances', []]}, 
            'broadcasts': {}, 
            'blocks': {
                'block2': {
                    'opcode': 'event_whenflagclicked', 
                    'next': 'block3', 'parent': None, 
                    'inputs': {}, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': True, 
                    'x': 0, 
                    'y': 0
                }, 
                'block3': {
                    'opcode': 'motion_gotoxy', 
                    'next': 'block4', 
                    'parent': 'block2', 
                    'inputs': {
                        'X': [1, [10, '0']], 
                        'Y': [1, [10, '0']]
                    }, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block4': {
                    'opcode': 'data_deletealloflist', 
                    'next': 'block5', 
                    'parent': 'block3', 
                    'inputs': {}, 
                    'fields': {
                        'LIST': ['distances', 'distances3']
                    }, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block5': {
                    'opcode': 'data_addtolist', 
                    'next': 'block6', 
                    'parent': 'block4', 
                    'inputs': {'ITEM': [1, [10, '10']]}, 
                    'fields': {'LIST': ['distances', 'distances3']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block6': {
                    'opcode': 'data_addtolist', 
                    'next': 'block7', 
                    'parent': 'block5', 
                    'inputs': {'ITEM': [1, [10, '23']]}, 
                    'fields': {'LIST': ['distances', 'distances3']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block7': {
                    'opcode': 'data_addtolist', 
                    'next': 'block8', 
                    'parent': 'block6', 
                    'inputs': {'ITEM': [1, [10, '56']]}, 
                    'fields': {'LIST': ['distances', 'distances3']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block8': {
                    'opcode': 'data_addtolist', 
                    'next': 'block9', 
                    'parent': 'block7', 
                    'inputs': {'ITEM': [1, [10, '11']]}, 
                    'fields': {'LIST': ['distances', 'distances3']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block9': {
                    'opcode': 'data_setvariableto', 
                    'next': 'block10', 
                    'parent': 'block8', 
                    'inputs': {'VALUE': [1, [10, '0']]}, 
                    'fields': {'VARIABLE': ['i', 'i9']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block10': {
                    'opcode': 'control_repeat_until', 
                    'next': None, 
                    'parent': 'block9', 
                    'inputs': {
                        'CONDITION': [1, 'block11'], 
                        'SUBSTACK': [1, 'block14']
                    }, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block11': {
                    'opcode': 'operator_not', 
                    'next': None, 
                    'parent': 'block10', 
                    'inputs': {'OPERAND': [1, 'block12']}, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block12': {
                    'opcode': 'operator_lt', 
                    'next': None, 
                    'parent': 'block11', 
                    'inputs': {
                        'OPERAND1': [1, [12, 'i', 'i9']], 
                        'OPERAND2': [1, 'block13']
                    }, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block13': {
                    'opcode': 'data_lengthoflist', 
                    'next': None, 'parent': 'block12', 
                    'inputs': {'LIST': [1, [13, 'distances', 'distances3']]}, 
                    'fields': {'LIST': ['distances', 'distances3']}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block14': {
                    'opcode': 'control_if', 
                    'next': 'block18', 
                    'parent': 'block10', 
                    'inputs': {
                        'CONDITION': [1, 'block15'], 
                        'SUBSTACK': [1, 'block17']
                    }, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block15': {
                    'opcode': 'operator_not', 
                    'next': None, 
                    'parent': 'block14', 
                    'inputs': {'OPERAND': [1, 'block16']}, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block16': {
                    'opcode': 'operator_equals', 
                    'next': None, 
                    'parent': 'block15', 
                    'inputs': {
                        'OPERAND1': [1, [12, 'i', 'i9']], 
                        'OPERAND2': [1, [10, '1']]
                    }, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block17': {
                    'opcode': 'motion_movesteps', 
                    'next': None, 
                    'parent': 'block14', 
                    'inputs': {'STEPS': [1, [13, 'distances', 'distances3']]}, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block18': {
                    'opcode': 'control_wait', 
                    'next': 'block19', 
                    'parent': 'block14', 
                    'inputs': {'DURATION': [1, [10, '.5']]}, 
                    'fields': {}, 
                    'shadow': False, 
                    'topLevel': False
                }, 
                'block19': {
                    'opcode': 'data_changevariableby', 
                    'next': None, 'parent': 'block18', 
                    'inputs': {'VALUE': [1, [10, '1']]}, 
                    'fields': {'VARIABLE': ['i', 'i9']}, 
                    'shadow': False, 
                    'topLevel': False
                }
            }, 
            'comments': {}, 
            'currentCostume': 0, 
            'costumes': [], 
            'sounds': [], 
            'volume': 100, 
            'layerOrder': 1, 
            'visible': True, 
            'x': 0, 
            'y': 0, 
            'size': 100, 
            'direction': 90, 
            'draggable': False, 
            'rotationStyle': 'all around'
        }
    ]