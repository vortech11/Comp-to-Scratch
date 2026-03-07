# Welcome to Scratch Script

Scratch script is a domain specific language that is made to compile to a scratch .sb3 file which can be imported into the scratch website. 

Scratch script's syntax looks similar to the `java` programming language, however many of thier concepts are derived from the `C` programming language.

## Example

The following is an example `.scratch` file that makes the cat step through the items in a list:

```js linenums="0"
sprite Stage{}

sprite cat{
    costume catCostume "cat.svg";
    func main(){
        list myList = [10, 20, 30];
        for (ptr i = 0; i < myList.length; i += 1){
            move(myList[i]);
            sleep(1);
        }
    }
}
```