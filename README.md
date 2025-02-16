# i3-resurrect-menu

Menu for [i3-ressurect](https://github.com/JonnyHaystack/i3-resurrect).
Runs in [alacritty](https://github.com/alacritty/alacritty).

## Setup

In `i3/config`:

```
# i3-resurrect-menu
for_window [class="i3-resurrect-menu"] floating enable
bindsym $mod+p exec i3-resurrect-menu restore
bindsym $mod+Shift+p exec i3-resurrect-menu save
```

In `i3-resurrect/config.json` (`true` command is nop):

```
{
  "window_command_mappings": [
    {
      "class": "i3-resurrect-menu",
      "command": "true"
    }
  ]
} 
```
