# dotfiles

Archivos de configuración personal para mi entorno de trabajo.

## Descripción

Configuraciones para terminal, editor de texto y herramientas de desarrollo, gestionadas con [GNU Stow](https://www.gnu.org/software/stow/) para crear symlinks desde este repositorio al directorio home (`~` o `%USERPROFILE%` en Windows).

### Estructura del repositorio

```
.
├── .alacritty.toml          # Configuración de Alacritty (raíz)
├── .config/
│   ├── alacritty/            # Temas y configuración adicional de Alacritty
│   ├── ghostty/              # Configuración de Ghostty
│   ├── nvim/                 # Configuración de Neovim (init.lua + lua/)
│   ├── opencode/             # Configuración de opencode (AGENTS.md, skills, etc.)
│   ├── VSCodium/             # Configuración de VSCodium
│   └── zed/                  # Configuración de Zed
├── .gitconfig                # Configuración global de Git
├── .gitattributes            # Atributos de Git
├── .gitignore                # Ficheros ignorados
└── .stow-local-ignore        # Ficheros que Stow no debe enlazar
```

## Requisitos

- [Alacritty](https://alacritty.org/) - Emulador de terminal (configurado en raíz con `.alacritty.toml`)
- [Ghostty](https://ghostty.org/) - Emulador de terminal
- [Neovim](https://neovim.io/) - Editor de texto (gestionado con [lazy.nvim](https://github.com/folke/lazy.nvim))
- [VSCodium](https://vscodium.com/) - Editor de código
- [Zed](https://zed.dev/) - Editor de código
- [opencode](https://opencode.ai) - Asistente de IA en terminal
- [JetBrainsMono Nerd Font](https://www.nerdfonts.com/font-downloads) - Tipografía monoespaciada
- [Git](https://git-scm.com/) - Control de versiones
- [GNU Stow](https://www.gnu.org/software/stow/) - Gestión de symlinks (solo Linux/macOS)

## Instalación

### Linux / macOS

Clonar el repositorio y usar Stow para crear los symlinks:

```bash
git clone git@github.com:roberfu/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
stow .
```

Stow enlazará automáticamente los ficheros de la raíz (`.*`) al home y el contenido de `.config/` a `~/.config/`. El fichero `.stow-local-ignore` evita que se enlacen `.git`, el propio `README.md` y `.alacritty.toml` (este último porque Alacritty espera encontrarlo en la raíz del home).

Si solo quieres desplegar un paquete concreto (por ejemplo, solo Neovim):

```bash
stow nvim
```

Para eliminar los symlinks:

```bash
stow -D .
```

### Windows

En Windows no se utiliza Stow. Ejecutar el script [windows.ps1](https://github.com/roberfu/runs/blob/main/windows.ps1) que crea los symlinks automáticamente (requiere PowerShell 7+ y permisos de administrador o [Developer Mode](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development) habilitado).

## Actualización

Para mantener los dotfiles al día:

```bash
cd ~/.dotfiles
git pull
# Si hay nuevos paquetes, ejecutar de nuevo:
stow .
```

## TODO

- [ ] Configurar keybindings personalizados en Neovim
- [ ] Agregar más plugins de LSP para lenguajes adicionales
- [ ] Agregar configuración de tmux
- [ ] Agregar configuración de bash
- [ ] Documentar atajos y temas disponibles
- [ ] Añadir script de instalación multiplataforma unificado
