# Structure of Scratch Script

Scratch Script is created to embody the functionality of base Scratch, so there must be some way to implement sprites.

## Sprites

You can create sprites by using the `sprite` keyword, similar to `class` in other languages.

```ts linenums="1"
sprite Stage{}

sprite cat{}

sprite thing{}
```

The text that comes after `sprite` will be the name of the sprite.

For example the sprite created on line 3 would be called 'cat'.

!!! Warning "If the sprite name is `Stage`, the sprite is the stage and will have all of it's functionality. The stage does not have position, and variables created in them are accessable from other sprites."

## Contents of sprites

Inside a sprite, you can start creating blocks and functions.

```rust
sprite cat{
    move(10);

    func doSomething(){
        move(10);
    }

    func main(){
        doSomething();
    }
}
```

For more information, go to [Scripts](./scripts.md)

## Costumes

Inside of the contents of a sprite, you can define a costume of a sprite by using the `costume` keyword.

The statement takes in two manditory parameters, and two optional ones.

The two manditory parameters are:

* The name of the costume to be created
* The relative path to the costume

The two optional parameters that come after the manditory ones, seperated by a comma:

* The x offset of the image
* The y offset of the image

Offsets are optional and the compiler will attempt to auto center the images if you do not specify an offset.

```ts
sprite cat{
    costume myCostumeName "foldername/filename.svg";

    costume myCostumeName2 "../myFile.png" 10, 3;
}
```

The first costume declaration creates a costume named myCostumeName with the file being at "foldername/filename.svg".

The second costume declaration creates a costume named myCostumeName2 with the file being at "../myFile.png" with a visual offset of 10, 3.

!!! Warning "Notice: raster images are destructive and anything outside of the bounds of the screen will be clipped when importing."

!!! danger "Currently the only file extensions implamented are svg, png, jpg."