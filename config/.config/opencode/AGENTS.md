# Global Agent Guidelines

## Idioma
Responde siempre en español (es) salvo que el usuario indique lo contrario.

## Estilo
- **Código siempre en inglés**: identificadores, nombres de variables/funciones/clases/módulos, endpoints de API, rutas, campos JSON/YAML/TOML, mensajes de log, mensajes de commit, nombres de branches y tags, etc.
- **Documentación y comentarios en español neutro**: comentarios dentro del código, docstrings (JSDoc/Javadoc/PyDoc), README, comentarios inline, comentarios en configs (YAML/TOML/JSON), comentarios en `.http`/`.bru`, etc.
- **Strings visibles para el usuario final en español neutro**: mensajes de error, textos de UI, notificaciones, emails, etc.
- **Explicaciones y mensajes al usuario en español** (también neutro).
- Preferir respuestas concisas; expandir solo si se pide.

## Español neutro
- Sin voseo ni vosotros: usar **tú** (singular) y **ustedes** (plural).
- Sin regionalismos: evitar jerga local. Preferir vocabulario estándar internacional.
- Evitar argentinismos: "che", "boludo", "guita", "pibe", "quilombo", etc.
- Evitar mexicanismos: "güey", "órale", "neta", etc.
- Evitar chilenismos: "weón", "cachai", "pololo", etc.
- Evitar peninsularismos coloquiales: "vale", "tío", "mola", etc.
- Tono formal-informal estándar, como un README técnico internacional.
- Acentos y ortografía correctos: "español" con ñ, "está" con tilde, "más" vs "mas", etc.
- Esta regla aplica a archivos nuevos o nuevos comentarios. No migrar archivos existentes a menos que el usuario lo pida.

## Comandos del sistema
- Windows: usar PowerShell 7+ (`pwsh`). Evitar `cmd.exe` salvo que sea estrictamente necesario.
- Tras `windows.ps1`, el PATH del usuario ya incluye winget, node, npm, java.
- Maven no se instala automáticamente: descargar zip, definir `MAVEN_HOME` y añadir `%MAVEN_HOME%\bin` al PATH del sistema.

## Restricciones
- No ejecutar comandos destructivos (`Remove-Item -Recurse`, formateos) sin confirmación explícita.
- No commitear credenciales ni claves. Si aparecen en un diff, rotar y notificar.

## Operaciones de Git
- **NUNCA** ejecutar `git add`, `git commit`, `git push`, `git merge`, `git rebase`, `git reset --hard`, `git checkout` que descarte cambios, `git stash` ni `git branch -D` por iniciativa propia.
- Solo ejecutar estas operaciones cuando el usuario lo pida **explícitamente** en el mensaje actual.
- Incluso cuando el usuario lo pida, antes de ejecutar `git add` o `git commit`:
  1. Mostrar `git status` y `git diff --stat` (qué se va a stagear/commitar).
  2. Pedir validación explícita ("OK para commitear estos X archivos con mensaje Y?").
  3. Solo proceder tras confirmación.
- Si aparecen credenciales, tokens o claves en un diff, abortar y notificar (ya cubierto en Restricciones).

## Skills disponibles
- `synchronize-subtitles`: re-sincroniza un `.srt` local contra el vídeo de la misma carpeta usando `ffsubsync` y lo renombra a `<video>.es.srt`.
- `generate-api-requests`: genera ficheros `.requests.http` y colección Bruno desde las rutas de un proyecto.
- `customize-opencode`: skill **built-in** de opencode para editar o crear su propia configuración (opencode.json, AGENTS.md, skills, plugins, MCP, reglas de permisos). No requiere instalación, ya está disponible.

## Creación de nuevas skills
Cuando el usuario solicite **explícitamente** crear una nueva skill (p. ej. "crea una skill", "añade una nueva skill", "haz una SKILL.md para ..."), el agente debe:

1. Detectar el entorno de ejecución (Windows vs. WSL/Linux).
2. Si está en Windows: avisar de que las skills viven en el repo de dotfiles (`C:\Users\Roberto\Repos\dotfiles\.config\opencode\skills\` o, en WSL, `\\wsl.localhost\Ubuntu\home\roberto\.dotfiles\.config\opencode\skills\`) y se desarrollan con herramientas Unix (bash, python, shebangs `#!/usr/bin/env`). Recomendar abrir una sesión en WSL o Linux para crearlas allí, evitando problemas de CRLF, rutas UNC (`\\wsl.localhost\...`) y permisos.
3. Pedir confirmación antes de continuar con una de estas dos opciones:
   - (a) Crear la skill igualmente desde Windows, o
   - (b) Pausar y dejar que el usuario abra WSL.
4. Solo si el usuario confirma (a) o ya está en WSL/Linux, proceder siguiendo las convenciones de las skills existentes (`SKILL.md` + carpeta `scripts/` si lleva código).
