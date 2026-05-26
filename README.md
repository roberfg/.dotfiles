# dotfiles

Archivos de configuración personal para mi entorno de trabajo.

## Descripción

Configuraciones para terminal, editor de texto y herramientas de desarrollo.

## Requisitos

- [Alacritty](https://alacritty.org/) - Emulador de terminal
- [Ghostty](https://ghostty.org/) - Emulador de terminal
- [Neovim](https://neovim.io/) - Editor de texto
- [VSCodium](https://vscodium.com/) - Editor de código
- [Hack Nerd Font](https://www.nerdfonts.com/font-downloads) - Tipografía

## Instalación

### Linux

```bash
git clone git@github.com:roberfu/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
stow .
```

### Windows

Ejecutar el script [windows.ps1](https://github.com/roberfu/runs/blob/main/windows.ps1) que crea los symlinks automáticamente.

## TODO

- [ ] Configurar keybindings personalizados en Neovim
- [ ] Agregar más plugins de LSP para lenguajes adicionales
- [ ] Agregar configuración de tmux
- [ ] Agregar configuración de bash

