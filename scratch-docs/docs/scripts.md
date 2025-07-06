# Sprite Scripts

The scripts of a sprite are the meat and potatoes of a project. Each function or command equates to one or more scratch blocks that gets created on compile. 

## Stacking

Scratch blocks are able to stack on top of one another. This happens in scratch script automatically when two functions gets called after one another. 

The way one would break this stacking is by placing a block that is not able to be stacked to break up the flow.

```ts
start();
move(3);
start();
move(4);
```

This would equate to two stacks that both are ran when the green flag is clicked. One stack with a move by 3 and another with a move by 4.

## Opcodes

A [Scratch Opcode](https://en.scratch-wiki.info/wiki/List_of_Block_Opcodes) is a specific identifier for a block. In scratch script you can create any scratch block by calling the opcode as a function.

```ts
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

```ts
move(10);

say("hi");

start();

if(10 == 10){
    move(10);
};
```

A list of all aliases can be found [here](https://github.com/vortech11/Comp-to-Scratch/blob/main/src/opcodeAlias.py)
