def parse_commands(command_list):
    def is_command_list(item):
        return isinstance(item, list) and len(item) > 0 and isinstance(item[0], str)
    
    result = []
    current_command = []

    i = 0
    while i < len(command_list):
        item = command_list[i]
        if isinstance(item, str):
            if current_command:
                result.append(current_command)
            current_command = [item]
        elif isinstance(item, list):
            if is_command_list(item):
                nested_commands = parse_commands(item)
                if len(nested_commands) == 1:
                    current_command.append(nested_commands[0])
                else:
                    current_command.append(nested_commands) # type: ignore
            else:
                current_command.append(item) # type: ignore
        i += 1

    if current_command:
        result.append(current_command)

    return result



commands = ['create', 'Stage', ['script', [], 'costumes', ['blank.svg'], 'sounds', []], 'create', 'cat', ['script', ['event_whenflagclicked', [], 'motion_movesteps', ['5'], 'event_whenkeypressed', ['space'], 'motion_gotoxy', ['3'], ['4'], 'control_if', ['operator_equals', ['1'], ['1']], ['motion_movesteps', ['5'], 'looks_say', ['hi'], 'control_if', ['operator_gt', ['7'], ['2']], ['motion_setx', ['5']]]], 'costumes', ['cat.svg']], 'create', 'man', ['script', ['event_whenflagclicked', [], 'motion_movesteps', ['10']], 'costumes', ['cat.svg'], ['blank.svg']]]
parsed = parse_commands(commands)
print(parsed)
