# holon-but-actually-opensource

![img](img/100python.png)
> *wat voor snarky comments kan je nog meer bedenken?*  - Gillis Hommen


## Setting up your development environment in VSCode:

### Recommended terminal

Use `bash` as default profile:
`CTRL + SHIFT + P` > `Terminal: Select Default Profile` > `git bash`.

Now all terminals opened in VSCode will be directly openend with bash. 

> For this to work you might with `conda` need to register the `bash` terminal. To this end, open the `anaconda prompt` and type `conda init bash`. 

### Add the correct Python interpreter

Use the `agentpy` conda environment in VSCode by pressing:
`CTRL + SHIFT + P` > `Python: Select Interperter` > `python 3.10.6 ('agentpy')`.

### Install the Python modules

```bash
conda create -n agentpy
conda activate agentpy
conda install pip
pip install -r requirements.txt
``` 


### Interactive mode
By installing `requirements.txt` you get `ipykernel` which is **supoah** nice for development. 

Use by pressing `CTRL + SHIFT + P` > `Preferences: Open Keyboard Shortcuts (JSON)` and adding:
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

To make sure you always use it, add the following lines to your `settings.json` (`CTRL + SHIFT + P` > `Preferences: Open User Settings (JSON)`). 

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

## Running
```
python main.py
```



