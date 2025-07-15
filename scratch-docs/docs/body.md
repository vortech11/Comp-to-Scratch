# Structure of Scratch Script

Scratch Script is created to embody the functionality of base Scratch, so there must be some way to implement sprites.

## Sprites

This functionality is accomplished in Scratch Script by the use of the sprite keyword.

```ts linenums="1"
sprite Stage{}

sprite cat{}

sprite thing{}
```

The text that comes after `sprite` will be the name of the sprite.

For example the sprite created on line 3 would be called 'cat'.

!!! Warning "If the sprite name is `Stage`, the sprite is the stage and will have all of it's functionality (including it's lack of position)"

## Attributes of Sprites

Sprites have attributes such as their costumes or scripts.

```ts
sprite cat{
    script{}
    costumes{}
}
```

## Scripts

Inside of scripts, there are functions and commands that are created from top to bottom

```ts
sprite cat{
    script{
        start();
        move(10);
    }
}
```

For more information, go to [Scripts](./scripts.md)

## Costumes

Inside of the costumes attribute there is a list of file paths to images. The resulting name of the costume in the scratch website when imported is the filename without the extension.

```ts
sprite cat{
    costumes{
        "cat1.svg",
        "foldername/filename.svg"
    }
}
```

For example, the path "folder1/bestImage.svg" would result in a costume named "bestImage".

!!! danger "Currently the only file extension implemented is svg"