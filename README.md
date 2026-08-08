# dotfiles

Configuraciones personales para mi entorno de trabajo (Linux, WSL y Windows).

## Descripción

Dotfiles gestionados con [GNU Stow](https://www.gnu.org/software/stow/) mediante el modelo de **paquetes**: cada subdirectorio de primer nivel del repositorio es un paquete stow independiente. Los scripts de instalación (`wsl-ubuntu.sh` para Linux/WSL y `windows.ps1` para Windows, que viven en `~/.runs/`) automatizan el enlace de los paquetes y resuelven conflictos de forma idempotente.

## Estructura del repositorio

```
.
├── README.md
├── bash/                        # Paquete: configuración de Bash
│   ├── .bashrc                  # Portable + opencode TUI reset
│   └── .bash_aliases            # Aliases personales
├── git/                         # Paquete: configuración de Git
│   ├── .gitconfig
│   └── .gitattributes
└── config/                      # Paquete: todo bajo ~/.config/
    └── .config/
        ├── VSCodium/            # VSCodium (User/settings.json)
        ├── nvim/                # Neovim (init.lua + lua/)
        ├── opencode/            # opencode (AGENTS.md, skills)
        └── wezterm/             # Wezterm (terminal, detección de SO)
```

Los tres paquetes (`bash`, `git`, `config`) se enlazan al `$HOME` con `stow --restow`.

## Requisitos

- [Git](https://git-scm.com/)
- [GNU Stow](https://www.gnu.org/software/stow/) (solo Linux/WSL)
- [Wezterm](https://wezfurlong.org/wezterm/), [Neovim](https://neovim.io/), [VSCodium](https://vscodium.com/), [opencode](https://opencode.ai)
- [JetBrainsMono Nerd Font](https://www.nerdfonts.com/font-downloads) para tipografía monoespaciada

## Instalación

### Linux / WSL (Ubuntu)

El script `~/.runs/wsl-ubuntu.sh` automatiza todo: instala paquetes del sistema, clona o actualiza este repo y enlaza los paquetes stow con manejo de conflictos. Ejecutar:

```bash
bash ~/.runs/wsl-ubuntu.sh
```

El script itera sobre `bash`, `git` y `config` con `stow --restow`. Si un archivo en `$HOME` existe como archivo regular, se reemplaza por el symlink del repo (el repo es la fuente de verdad; no se hacen backups).

### Instalación manual con Stow

```bash
git clone https://github.com/roberfu/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
stow --target="$HOME" --restow bash
stow --target="$HOME" --restow git
stow --target="$HOME" --restow config
```

### Windows

En Windows no se usa Stow. El script `~/.runs/windows.ps1` crea los symlinks con una lista explícita y manejo de conflictos. Requiere PowerShell 7+ y permisos de administrador o [Developer Mode](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development) habilitado.

## Actualización

```bash
cd ~/.dotfiles
git pull
stow --target="$HOME" --restow bash git config
```

`--restow` re-aplica los symlinks; es idempotente y rápido.

## Añadir un nuevo dotfile

Para meter una nueva app o archivo al repo:

```bash
# 1. Crear el archivo en el paquete apropiado
mkdir -p ~/.dotfiles/config/.config/alacritty
# ... escribir la configuración ...

# 2. Re-ejecutar el script de install
bash ~/.runs/wsl-ubuntu.sh
```

El script detecta el nuevo archivo y crea el symlink automáticamente. **No hace falta tocar el script** para añadir dotfiles a un paquete existente. Para un paquete nuevo (`bin/`, `local/`, etc.), añadirlo al bucle `for pkg in ...` del `wsl-ubuntu.sh`.

## opencode (agente)

`config/.config/opencode/` contiene la configuración del agente opencode:

- `AGENTS.md`: reglas globales (idioma, estilo, español neutro, operaciones de Git).
- `opencode.jsonc`: configuración del agente y registro de skills.
- `skills/`: skills personalizados (`synchronize-subtitles`, `generate-api-requests`).

Este `AGENTS.md` se sincroniza vía stow a `~/.config/opencode/AGENTS.md` (Linux/WSL) y por el script de Windows a `C:\Users\Roberto\.config\opencode\AGENTS.md`.

## Convenciones

- **Código en inglés**: identificadores, endpoints, mensajes de log, mensajes de commit, nombres de branches y tags.
- **Documentación y comentarios en español neutro**: sin voseo ni regionalismos. Detalles en `config/.config/opencode/AGENTS.md`.
- **Operaciones de Git**: el agente NUNCA ejecuta `git add`/`commit`/`push` por iniciativa propia. Solo cuando se le pide explícitamente, y tras mostrar `git status` y `git diff --stat`.

## TODO

- [ ] Keybindings personalizados en Neovim
- [ ] Más plugins de LSP para lenguajes adicionales
- [ ] Configuración de tmux
- [ ] Documentar atajos y temas disponibles
- [ ] Replicar `wsl-ubuntu.sh` para Bazzite, CachyOS, Nobara, MX Linux (hay stubs vacíos en `~/.runs/`)
