# Sprite Scripts

The scripts of a sprite are the meat and potatoes of a project. Each statement roughly equates to one scratch blocks that gets created on compile. 

## Stacking

Scratch blocks stack on top of one another. In Scratch Script, this happens automatically when there are two or more statments. 

```py
move(3);
move(4);
```

This would equate to two stacks that both are ran when the green flag is clicked. One stack with a move by 3 and another with a move by 4.

## Opcodes

A [Scratch Opcode](https://en.scratch-wiki.info/wiki/List_of_Block_Opcodes) is a specific identifier for a block. In scratch script, you can create any scratch block by calling the opcode as a function.

```py
motion_movesteps(10);

looks_say("hi");

event_whenflagclicked();
```

A list of all opcodes used in Scratch Script can be found [here](https://github.com/vortech11/Comp-to-Scratch/blob/main/src/OpcodeMap.json)

While this does work as the backend for most blocks, this is not the intended way of interacting with Scratch Script

## Macros

Built into Scratch Script is a set of macros that maps opcodes to more common place names

For example:

- `motion_movesteps` has been renamed to `move`

- `looks_say` to `say`

- `operator_round` to `round`

Both the alias and the original are allowed, but macros are meant to be easier to remember.

```py
move(10);

say("hi");

if(10 == 10){
    move(10);
}
```

A list of all aliases can be found [here](https://github.com/vortech11/Comp-to-Scratch/blob/main/src/opcodeAlias.py)

## Entry Points

While stacking blocks on empty space is fun, placing them on something is better.

There are two types of entry points,

* User defined functions

* Scratch defined 'cap blocks'

Both types of entry points use the `func` keyword.

The difference is the name of the function declared.

``` rust
def main(){
    move(3);
}

def doThing(){

}
```

The `main` function declared is a scratch defined entry point that aliases to the "when flag clicked" block.

!!! Notice "You can have multiple `main` functions. They will all run asyncranicely. Good luck getting async to work tho."

User defined function names can be anything else that is not is a scratch defined entry point.

## Data

Currently there are three types of data within Scratch Script: the var data type, list data type, and pointer data type.

## Vars

The var data type is the built-in scratch variable data type. Vars are created on compile time, or in other words, cannot be created after it is compiled.

To create the var data type you can run the following:

```py
var varName;
```

This will initiate the variable (`varName`) with the value "": an empty string. To specify a different value the following can be ran:

```py
var varName = 10;
```

You can set the value of the variable by using the `=` keyword.

```py
varName = 10;
```

You can then apply operations with the variable by using the `+=` keyword.

```py
varName += 10;
```

These operations change the value of the variable (varName) by a value (10).

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

Both of these lines create 'delete all of list' and 'add item to list' blocks, which means that they do not update the default state of the list. 

The difference between the two is that the first one creates a list to be used.

To change a specific value at an index, you are able to do list indexing by doing the folloing:

```py
list listName = [10, 3];
listName[2] = 5;
```

!!! danger "Base Scratch is 0st indexed compared to base scratch"
    In Scratch Script:
    ```js
    listName = [10, 20]
    listName[0] = 30
    listName[1] = 40
    //listName [30, 40]
    ```

    In normal Scratch:
    ```js
    list listName = [10, 20];
    listName[1] = 30;
    listName[2] = 40;
    //listName [30, 40]
    ```

    Attempting to change or get the 0th item does nothing.

To get the value at an index you can index through it as if you were to modify it, but within an expression.

```py
list listName = [10];
move(listName[1]);
```

## Pointers

Similarly to the C programming language, pointers are variables that point to positions in memory. In scratch this "memory" is a set of lists.

There are two types of pointers in Scratch Script:
* Smart pointers (garbage collected)
* Dumb pointers (not garbage collected)

The major difference between normal Scratch variables and pointers, is that pointers are created at runtime and can be deleted. 

!!! note "To use pointers, there must be a `require "std.scratch";` line before the use of pointers"
    To learn more about the `import` and `require` keywords, go to the [Importing](./importing.md) page.

To make a smart pointer, use the `ptr` keyword.

```py
ptr varName;
ptr varName3 = 10;
```

You can modify and asign values.

```py
ptr varName;
varName = 10;
varName += 3;
```

To get the value of a static var

```py
ptr varName = 3;
move(varName);
```

To make a dumb pointer, use the `dptr` keyword.

Everything a smart pointer can do, a dumb pointer can do.

Unlike smart pointers, you also have to manualy garbage collect them.

You can delete a dumb pointer by using the `del` keyword.

```py
dptr varName = 3;
move(varName);
del varName;
```

This automatically happens with a smart pointer.

!!! danger "Deleting dumb pointers is important"
    If you do not delete a dumb pointer, errors can pop up in the console.

    !!! failure ""
        ```py
        loop(3){
            dptr distance = 10;
            move(distance);
        }

        // Variable `distance` already exists
        ```

## Functions

Functions are part of base scratch and can be implamented by using the `func` keyword.

```py
func funcName(){

}
```

A function can have inputs parameters.

Functions can have as many inputs as you want and are deliminated by commas.

```rust
func funcName(input1, input2){

}
```

You can then place statements within the function. Statements inside of a function can use inputs.

```rust
func funcName(input1, input2){
    if (input2){
        move(input1);
    }
}
```

Any smart pointers created in functions are deleted at the end of the function.

```js
func funcName(){
    static varName = 3;
    move(varName);
}

// Var `varName` no longer exist.
```

## Function Returns

Functions in base scratch are not able to return values.

However, by the use of pointers, it is possible to pas in a reference to a pointer for it to be set inside of the function for it to be used outside of the function.

To use function returns, a function must return something.

To set a pointer to the function return, the `<<` keyword is used.

```rust
func add(num1, num2){
    return num1 + num2;
}

ptr result << add(1, 2);
say(result);

```

You can create a pointer for the function return assignment, or you can use a pre-existing pointer.

The portion on the right side of the `<<` must be a singular function call with nothing more.