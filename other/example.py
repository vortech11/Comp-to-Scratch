

operatorMap = {
    "*": 3,
    "/": 3,
    "+": 2,
    "-": 2
}




def removeParenths(expression):
    output = []
    for item in expression:
        if isinstance(item, list):
            output += ["["] + removeParenths(item[0]) + ["]"]
        else:
            output.append(item)

    return output

def convertRPN(expression):
    expression = removeParenths(expression)

    output = []
    stack = []

    operatorMap = {
        "*": 3,
        "/": 3,
        "+": 2,
        "-": 2
    }

    for item in expression:
        if not item in operatorMap:
            if item in ["[", "]"]:
                if item == "[":
                    stack.append(item)
                else:
                    while (len(stack) > 0) and (not stack[-1] == "["):
                        output.append(stack.pop())
                    stack.pop()
            else:
                output.append(item)
        else:
            if (len(stack) < 1) or (stack[-1] == "[") or (operatorMap[item] > operatorMap[stack[-1]]):
                stack.append(item)
            else:
                while (len(stack) > 0) and (operatorMap[item] <= operatorMap[stack[-1]]):
                    output.append(stack.pop())
                stack.append(item)
    stack.reverse()
    return output + stack


inputstr = [[['3', '-', '2']], '*', '4']

#inputstr = ['3', '-', '2', '*', '4']

print(convertRPN(inputstr))