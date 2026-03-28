# The Installation of Scratch script

For ease of use, there are install scripts.

!!! warning "If I am being honest, these shell and bash scripts were made by AI. The should work, but you should always read the install scripts. You can find the source code [here for windows](https://github.com/vortech11/Comp-to-Scratch/blob/main/install.ps1), and [here for linux](https://github.com/vortech11/Comp-to-Scratch/blob/main/install.sh)"

!!! warning "The windows build binarys currently do not work."
    
    Because I am using Nuitka to compile a python project into a standalone file, the code gets obfuscated and Windows throws a tantrum; assuming whatever I am doing is malicious. Until I get zip projects to work with github workflows, if you use windows, you will just have to use python to run the compiler.

    Cheers, The Scratch Script Development Team.

<!--
### Windows

```shell
irm https://raw.githubusercontent.com/vortech11/Comp-to-Scratch/main/install.ps1 | iex
```
-->

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/vortech11/Comp-to-Scratch/main/install.sh | bash
```

### Running the compiler

After using the install script, you can use the following command:

```shell
scratch myProject.scratch
```

And obviously replace the "myProject.scratch" with the file you want to compile

## Using python

The compiler is able to be used using only python. By installing the repo, you are able to use the compiler without the binary.

```shell
git clone https://github.com/vortech11/Comp-to-Scratch.git
```

Check that you have python installed (around version 3.13, idk)

```shell
python --version
```

You can now compile `.scratch` files by running:

```shell
python "Comp-to-Scratch-path/main.py" "fileName"
```

This should result in an build folder being created in the directory of the .scratch file

For any future use of the compiler, you can always use

```shell
python "Comp-to-Scratch-path/main.py"
```

in place of

```shell
scratch
```

### Compiling yourself

If you want, you can even compile the program yourself. You can achieve this by using the `nuitka` python compiler.

You can read up on how to install Nuitka yourself [here](https://nuitka.net/doc/download.html)

To use Nuitka, you can run the following:

```shell
python -m nuitka main.py
```

Make sure you are running this while your current working directory is the same one containing `main.py`

## Using the compiler

For a list of flags and commands you can use the compiler with, run:

```shell
scratch --help
```

To compile a `.scratch` file, run

```shell
scratch "myPath/myFile.scratch"
```

!!! note "Ability to run with a button"
    If you use vscode, you can use vscode extensions such as "Code Runner" to add a button to .scratch files and make them run the command