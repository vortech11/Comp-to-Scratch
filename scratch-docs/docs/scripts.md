# Sprite Scripts

The scripts of a sprite are the meat and potatoes of a project. Each function or command equates to one or more scratch blocks that gets created on compile. 

## Stacking

Scratch blocks are able to stack on top of one another. This happens in scratch script automatically when two functions gets called after one another. 

The way one would break this stacking is by placing a block that is not able to be stacked to break up the flow.

```py
start();
move(3);
start();
move(4);
```

This would equate to two stacks that both are ran when the green flag is clicked. One stack with a move by 3 and another with a move by 4.

## Opcodes

A [Scratch Opcode](https://en.scratch-wiki.info/wiki/List_of_Block_Opcodes) is a specific identifier for a block. In scratch script you can create any scratch block by calling the opcode as a function.

```py
motion_movesteps(10);

looks_say("hi");

event_whenflagclicked();
```

A list of all opcodes used in Scratch Script can be found [here](https://github.com/vortech11/Comp-to-Scratch/blob/main/src/OpcodeMap.json)

## Aliases

An alias is a scratch opcode that has been renamed.

For example:
- `motion_movesteps()` has been renamed to `move`
- `looks_say()` to `say`
- `event_whenflagclicked()` to `start`

Both the alias and the original are allowed, but aliases are meant to be easier to remember.

A good example of this is `control_if` as it is renamed to `if` to make if statements work

```py
move(10);

say("hi");

start();

if(10 == 10){
    move(10);
}
```

A list of all aliases can be found [here](https://github.com/vortech11/Comp-to-Scratch/blob/main/src/opcodeAlias.py)

## Data

Currently there are three types of data within Scratch Script: the var data type, list data type, and static data type.

## Vars

The var data type is the built-in scratch variable data type. Vars are created on compile time, or in other words, cannot be created after it is compiled.

To create the var data type you can run the following:

```py
var varName;
```

This will initiate the variable (`varName`) with the value 0. To specify a different value the following can be ran:

```py
var varName = 10;
```

You can set the value of the variable by using the `=` keyword.

```py
varName = 10;
```

You can then apply operations with the variable by using the `+=` or `++` keyword.

```py
varName += 10;
varName++;
```

These operations change the value of the variable (varName) by a value (10 or 1).

To get the value of a var, you can use the name of the variable in an expression.

```py
var i = 3;
move(i);
move(i + 2);
```

In action this could look like:

```py
var i;
i = 10;
i += 2;
i++;
move(i);
```

## Lists

By using the list keyword, a Scratch list is created similarly to a variable. It is created on compile time and cannot be created or deleted while the Scratch Project is running.

To create a list, use the list keyword:

```py
list listName;
list listName = [];
```

Both of these scripts creates an empty list called listName that looks like this: []. I don't know which one is better so I will keep both. 

If you want to initiate values or set them, you can simply use commas to deliminate different values at indexes.

```py
list listName = [10, 4, 6, 7, 2];
listName = [3, 1];
```

To change a specific value at an index, you are able to do list indexing by doing the folloing:

```py
list listName = [10, 3];
listName[2] = 5;
```

!!! danger "Base Scratch is 1st indexed compared to most programming languages"
    In python:
    ```py
    listName = [10, 20]
    listName[0] = 30
    listName[1] = 40
    #listName [30, 40]
    ```

    In Scratch Script:
    ```py
    list listName = [10, 20];
    listName[1] = 30;
    listName[2] = 40;
    #listName [30, 40]
    ```

    Attempting to change or get the 0th item does nothing.

!!! warning "You are currently not able to change the value at an index by a value"
    
    This does not work:

    !!! failure ""
        ```py
        list listName = [10];
        listName[1] += 1;
        ```

To get the value at an index you can index through it as if you were to modify it, but within an expression.

```py
list listName = [10];
move(listName[1]);
```

## Static Vars

Similarly to the C programming language, static vars are accessable in all scopes (within the same sprite). The reference to "static variables" is a combination of static variables and pointers in c as static vars in Scratch Script can be deleted/freed.

Static vars are created at runtime and can be deleted, making them different from normal Scratch variables

!!! note "Static vars, behind the hood, use the `import`/`require` keyword to add to a Scratch Script project"
    To learn more about the `import` and `require` keywords, go to the [Importing](./importing.md) page.

To make a static var, use the static keyword.

```py
static varName;
static varName = 10;
```

You can modify and asign values.

```py
static varName;
varName = 10;
varName += 3;
varName++;
```

To get the value of a static var

```py
static varName = 3;
move(varName);
```

You can delete a static var by using the `del` keyword.

```py
static varName = 3;
move(varName);
del varName;
```

!!! danger "Deleting static variables is important"
    If you do not delete a static variable, errors can pop up in the console.

    !!! failure ""
        ```py
        start();
        loop(3){
            static distance = 10;
            move(distance);
        }

        # Variable `distance` already exists
        ```

## Functions

Functions are part of base scratch and can be implamented by using the `func` keyword.

```py
func funcName(){

}
```

A function can have inputs parameters.

Function parameters can be of type:

- text (numbers or strings)

- bool (boolean expressions)

Functions can have as many inputs as you want and are deliminated by commas.

```py
func funcName(input1: text, input2: bool){

}
```

`input1` is an input to funcName and is of type text.

`input2` is an input to funcName and is of type bool.

You can then place blocks within the function. Those blocks can also call inputs.

```py
func funcName(input1: text, input2: bool){
    if (input2){
        move(input1);
    }
}
```

Any static variables created in functions are deleted at the end of the function.

```py
func funcName(){
    static varName = 3;
    move(varName);
}

# Var `varName` no longer exist.
```

!!! example "Experimental: Function Returns"

    Functions in base scratch are not able to return values.

    However, by creating a static global variable, running the function, setting the value within the function, getting the value of the variable outside of the function, and deleting the static variable, it is possible to make function returns.

    This technology is still in production and does not work with bools or multiple return values and may be buggy.

    ```py
    func add(num1: text, num2: text){
        return (num1 + num2);
    }

    move(add(10, 4));
    ```