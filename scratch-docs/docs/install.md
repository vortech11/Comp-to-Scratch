# The Installation of Scratch script

For ease of use, there are install scripts.

!!! warning "If I am being honest, these shell and bash scripts were made by AI. The should work, but you should always read the install scripts. You can find the source code [here for windows](https://github.com/vortech11/Comp-to-Scratch/blob/main/install.ps1), and [here for linux](https://github.com/vortech11/Comp-to-Scratch/blob/main/install.sh)"

### Windows

```shell
irm https://raw.githubusercontent.com/vortech11/Comp-to-Scratch/main/install.ps1 | iex
```

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

Check that you have python installed (around version 3.13 idk)

```shell
python --version
```

You can now compile `.scratch` files by running:

```shell
python "Comp-to-Scratch-path/main.py" "fileName"
```

This should result in an build folder being created in the directory of the .scratch file

### Compiling yourself

If you want, you can even compile the program yourself. You can achieve this by using the `nuitka` python compiler.

You can read up on how to install Nuitka yourself [here](https://nuitka.net/doc/download.html)

To use Nuitka, you can run the following:

```shell
python -m nuitka main.py
```

Make sure you are running this while your current working directory is the same one containing `main.py`

!!! note "Ability to run with a button"
    You can use vscode extensions such as "Code Runner" to add a button to .scratch files and make them run the command