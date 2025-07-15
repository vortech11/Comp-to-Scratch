# Importing Scripts

Similarly to the `#include` keyword in C, the `import` keyword in Scratch Script "runs" the file specified ""linking"" the files together. In actuality, this process is achieved by different means in both cases.

## Import

The import keyword can be used in two contexts:

1. Within a `script`

2. Not within a `script`

### Importing within a script

If the `import` keyword is used within the script of a sprite, the import will look for the `export` keyword within the .scratch file.

Once it has found the `export` keyword, it will run all of the commands within it.

To assign stacks, the original stack will "jump" over the import and will continue on without it.

```py title="main.scratch"
sprite cat {
    script {
        start();
        import "otherfile.scratch";
        move(3);
    }
}
```

```py title="otherfile.scratch"
export {
    move(7);
}
```

The resulting stacks would be:

start(); move(3);

and...

move(7);

### Importing outside of a script

If the `import` keyword is used outside of the script of a sprite, the import will look for all `sprites` within the .scratch file.

```py title="main.scratch"
import "otherfile.scratch";

sprite cat {
    script {
        start();
        move(3);
    }
}
```

```py title="otherfile.scratch"
sprite cat2 {
    script{
        move(7);
    }
}
```

The resulting Scratch project would contain both `cat` and `cat2`.

This achieves the same thing as if you put the sprite in the base project.

## Require

The require keyword is a one time import.

If the .scratch file has not been imported yet, it imports it.

If the .scratch file has been imported before, it does not import the file.

```py title="main.scratch"
sprite cat{
    script {
        require "otherfile.scratch";
    }
}
```

## File Path

The file in quotes for the `require` and `import` command is a relative file path, meaning you are able to put the file you want to import into a subdirectory.

For example a directory like this:

```
.
└─ project/
    ├─ main.scratch
    └─ subforlder/
        └─ example.scratch
```

Could have a import like this:

```py title="main.scratch"
import "subfolder/example.scratch";
```

## Standard Packages

Standard Packages are files that are part of compiler and are used for base functionality such as static variables.

Importing standard packages are the exact same as importing regular .scratch files.

```py
import "static.scratch";
```

For most cases however, this is done automatically.