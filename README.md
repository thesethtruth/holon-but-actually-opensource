# holon-but-actually-opensource

> *wat voor snarky comments kan je nog meer bedenken?*  - Gillis Hommen


## Installation

```bash
conda create -n agentpy
conda activate agentpy
conda install pip
pip install -r requirements.txt
```

## Running
```
python main.py
```


## Protip:

By installing `requirements.txt` you get `ipykernel` which is **supoah** nice for development. 

Use by pressing `CTRL + SHIFT + P` > `keybindings.json` and adding:
```json
[
    {
        "key": "shift+enter",
        "command": "-python.execSelectionInTerminal",
        "when": "editorTextFocus && !findInputFocussed && !jupyter.ownsSelection && !notebookEditorFocused && !replaceInputFocussed && editorLangId == 'python'"
    },
    {
        "key": "shift+enter",
        "command": "jupyter.runFileInteractive"
    }
]
```

Now press `shift+enter` when focused on the `main.py`. Now an interactive window will open in VSCode. 