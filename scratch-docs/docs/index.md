# Welcome to Scratch Script

Scratch script is a domain specific language that is made to compile to a scratch .sb3 file which can be imported into the scratch website.

## Example

The following is an example .scratch file that makes the cat step through the items in a list:

```js linenums="1"
sprite Stage{};

sprite cat{
    script[
        start();
        setxy(0, 0);
        list distances = [10, 23, 56, 11];

        for(var i = 0; i < len(distances); i++){
            if(i != 1){
                move(distances[i]);
            };
            sleep(".5");
        };
    ];
    costumes[
        "pics/cat.svg"
    ];
};
```