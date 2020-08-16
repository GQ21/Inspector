# Inspector

![Inspector](https://i.imgur.com/dezy9QL.jpg)

## Idea behind it:
The main idea was to create ultimate sanity checker which would be production friendly, durable and could be very flexible.
This sanity checker can easily update with new commands, have different command options and have possibility to save all settings into a preset. In that way, user can use same sanity checker for different projects, their own personal project, or studio work. Switching between projects is just a matter of few buttons clicks. 

For studios it can save time by instead of remaking new script for every single project they rather can use this code as a framework and update it every time they need some changes which in the end can create useful library that can be transferred on every project and different workflows.

## How to install:
Put folder "Inspector" in your default Maya script directory.

`Windows: ~\Users\<username>\Documents\Maya\<Maya version>\scripts`

`Mac OS X ~<username>/Library/Preferences/Autodesk/Maya/<Maya version>/scripts`
  
`Linux (64-bit) ~<username>/Maya/<Maya version>/scripts`

Create shell button by typing this code in the script editor (python tab) and drag into shelf from where it will be accessed:

```python
import Inspector.UI.inspector_UI
from Inspector.UI.inspector_UI  import Inspector

Inspector.show_dialog()
```

## How to use it:

There are three main sections:

First is object selection window. Where user can add or remove objects which he wants to check.

Second is command section where user can choose which commands he wants to use. It's possible to run all checked commands or run every command separately by clicking “run” button on particular command. Button “select all” is by default deactivated. Although whenever user runs command with error, this button activates and allows to select all occurred problematic objects or nodes. Few commands can have an additional “opt” button which will rise option window. Lastly, all commands have info buttons who gives pop up windows with a small explanation of what command does (still uncomplete).

![inspector_category_menu](https://i.imgur.com/F36mnqR.jpg)

All categories have small option button on the left where user can take out commands or add them and do simple tasks like check all commands related to category or uncheck them.    
Third is log section where all processed commands log is displayed. If error occurs proceeding command on one of the chosen objects error message will be displayed and “select” button will rise. It allows select object or error nodes related to appeared error.

![inspector_main_menu](https://i.imgur.com/hzFoK5G.jpg)

Finally, in the main menu, there are two submenus. Preset menu gives functions to open, save, reload preset file. Another menu is help menu which simply directs to this website.

## Commands:
### Geometry:
#### triangle_count
Checks if objects don't exceed set maximum triangle count. Returns objects that exceeds limit and shows their triangle count

![inspector_triangle_count_options](https://i.imgur.com/tm5nHT9.jpg)

Maximum triangle count can be set in triangle_count options.

#### lamina_faces
Checks if objects don't have lamina faces. Returns laminas faces and object that has it.

### Uvs:
#### Missing_uvs
Checks if objects have uvs. Return objects which miss uvs.

### Naming:
#### Naming_convention
Checks if objects are named with set prefixes. Returns objects that don't fit naming convention and shows which prefixes they are missing. 

![inspector_naming_convention_options](https://i.imgur.com/pdpXnek.jpg)

Prefixes can be set in naming_convention options. If prefix line is empty it will be considered as no prefix.

### Other:
#### History
Checks if objects have history. Returns objects with history.

## How it functions:
When this checker runs it first checks current_preset.txt file which should be located in default Maya script directory where all script files were placed. Current_preset.txt file contains preset name and its location. If file won't load script will automatically load default script. Preset file contains nested list with dictionaries, like this one:

`[['geometry', [['triangle_count', [0, 1], {'options': [{'max': ['QLineEdit', 5000]}]}], ['lamina_faces', [0, 1]]]], ['uvs', [['missing_UVS', [0, 1]]]], ['naming', [['naming_convention', [0, 1], {'options': [{'first_prefix_': ['QLineEdit', 'mdl_']}, {'second_prefix': ['QLineEdit', 'char_']}]}]]], ['other', [['history', [0, 1]]]]]`

First member in the list is containing category name and all belonging commands. 

`['geometry', [['triangle_count', [0, 1], {'options': [{'max': ['QLineEdit', 5000]}]}],['lamina_faces', [0, 1]]]`

In this example first command is “triangle_count”. It corresponds to the same name function in module "in_commands". Second member in command list is checkbox status and visibility status. In this case, 0 indicates that checkbox should be unchecked and 1 indicates that command should be visible in category group box. It has an additional options dictionary which depending on the command can be included. Here key element “options” has list item which contains dictionary with key name “max” and its item list ['QLineEdit', 5000]. First element in this item is name of QWidget which will be displayed in option dialog box and second element is a parameter which will define dictionary key value “max”. As you can see in “naming_convention” command options key can have multiple items.

When making all tweaks, like hiding commands or editing commands options main list will update automatically. So when user will want to save preset, main list will be stored in specified directory and current_preset.txt will be changed. 

![inspector_main_label](https://i.imgur.com/LisQigC.jpg)

Be aware of giving preset file name, because it will appear in script UI and will show which preset is currently being used. To make preset name with spaces user should use underscore. For example, if user will save file with name “custom_preset” in Inspector main label underscore will be treated as space and this name will be shown as “custom preset”.
