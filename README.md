# Compiling to scratch

Dragging and dropping is cool and all, but do you know what is faster? Typing. Therefore I set out to recreate the scratch experience with text: my own little programming language.

Turns out the scratch's sb3 file format is just a renamed zip file which contains images and a project.json file that contains all of the information for a project. Therefore, to make scratch programming language, you just need to do the steps in reverse!

# This Branch

Within this branch is a complete rewrite of the entire codebase following the systems I developed in my repo [Here](https://github.com/vortech11/Interpreted-Lang) 

The major difference between this version and the first one is the use of an Abstract Syntax Tree (AST). 

With the first version I did not know what I was doing and implamented a serious abomination of a data type. 

By using objects, it makes things so much easier.

# Features

Compared to the main branch, this rewrite is not yet feature complete.

### Things yet to implament:

* `Static` Variables (To be renamed to ptr or something of the like)
    * Function returns
* Sounds
* More asset stuff
* Documentation