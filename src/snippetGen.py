import json

opcodeMap = json.load(open("src/OpcodeMap.json"))

snippetOutput = {
    "Create a sprite": {
		"scope": "scratch",
		"prefix": "create",
		"body": [
			"create"
		],
		"description": "Create a sprite"
	},
	"Scripts of a sprite": {
		"scope": "scratch",
		"prefix": "script",
		"body": [
			"script[", "\t$0", "]"
		],
		"description": "Define the scripts of a sprite"
	},
	"Costumes of a sprite": {
		"scope": "scratch",
		"prefix": "costumes",
		"body": [
			"costumes[", "\t$0", "]"
		],
		"description": "Define the costumes of a sprite"
	},
	"Sounds of a sprite": {
		"scope": "scratch",
		"prefix": "sounds",
		"body": [
			"sounds[", "\t$0", "]"
		],
		"description": "Define the sounds of a sprite"
	}
}

for key, value in opcodeMap.items():
    snippet = {
        key: {
	    	"scope": "scratch",
	    	"prefix": key,
	    	"body": [],
	    	"description": value["description"]
	    }
    }
    if(len(value["inputs"]) == 0):
        snippet[key]["body"] = [key+"();$0"]
    else:
        snippet[key]["body"] = [key+"($0);"]
    snippetOutput.update(snippet)

snippetOutput = json.dumps(snippetOutput)

with open("src/temp/Scratch snippets.code-snippets", "w") as file:
    file.write(snippetOutput)