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


## Protips:


### Interactive mode
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

### Code formatting

By installing `requirements.txt` you've also installed `black` which is the nicest formatter out there for Python (this is _not_ an opinion).

To make sure you always use it, add the following lines to your `settings.json` (`CTRL + SHIFT + P` > `open settings (json)`). 

```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "editor.codeActionsOnSave": {
    "source.fixAll": false,
    "source.sortImports": true
  },
}
```

### Recommended terminal

Use `bash` as default profile:
`CTRL + SHIFT + P` > `Terminal: Select Default Profile` > `git bash`.

Now all terminals opened in VSCode will be directly openend with bash. 

### Add the correct Python interpreter

Use the `agentpy` conda environment in VSCode by pressing:
`CTRL + SHIFT + P` > `Python: Select Interperter` > `python 3.10.6 ('agentpy')`.
