# Global Agent Guidelines

## Idioma
Responde siempre en español (es) salvo que el usuario indique lo contrario.

## Estilo
- Código en inglés (identificadores, mensajes de commit, comentarios técnicos).
- Explicaciones y mensajes al usuario en español.
- Preferir respuestas concisas; expandir solo si se pide.

## Comandos del sistema
- Windows: usar PowerShell 7+ (`pwsh`). Evitar `cmd.exe` salvo que sea estrictamente necesario.
- Tras `windows.ps1`, el PATH del usuario ya incluye winget, node, npm, java, mvn.

## Restricciones
- No ejecutar comandos destructivos (`Remove-Item -Recurse`, formateos) sin confirmación explícita.
- No commitear credenciales ni claves. Si aparecen en un diff, rotar y notificar.

## Skills disponibles
- `search-subtitles`: descarga subs en español para una carpeta de vídeos.
- `generate-api-requests`: genera ficheros `.requests.http` y colección Bruno desde las rutas de un proyecto.
