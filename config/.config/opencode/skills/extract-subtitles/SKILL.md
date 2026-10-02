---
name: extract-subtitles
description: Usar SOLO cuando el usuario quiera extraer UNA pista de subtítulos española incrustada en un vídeo y dejarla como archivo .srt UTF-8 con BOM al lado del vídeo, con prioridad español latino > español neutro > español. Si no hay una pista española subrip elegible, no extrae nada. Se activa con frases como "extrae los subtítulos", "extrae el subtítulo del vídeo", "saca los subtítulos del mkv", "extract subtitles", "extract the embedded subtitle", "dump the subs". Auto-detecta un único vídeo (.mkv/.mp4/.avi/.mov/.m4v) y aborta con un error claro si hay cero o más de uno. Solo extrae pistas subrip mediante copia directa con ffmpeg; descarta inglés, PGS, ASS/SSA, WebVTT y cualquier otro formato. La salida siempre se nombra <video>.es.srt. Sobrescribe un destino existente sin preguntar.
---

# Extract Subtitles

Flujo para que el agente extraiga **una** pista `subrip` en español incrustada en el vídeo de una carpeta, la convierta a UTF-8 con BOM y la deje como `<video>.es.srt`, eligiendo por prioridad: **español latino > español neutro > español**. Si no hay ninguna pista española `subrip` elegible, no extrae nada y avisa.

El usuario ejecuta el script incluido. **Sin flags, sin opciones de configuración.** El script auto-detecta el vídeo en la carpeta actual (o en la carpeta pasada como único argumento), lista las pistas con `ffprobe`, elige una y la vuelca con `ffmpeg` en copia directa.

## Cuándo usar esta skill

- El usuario tiene un vídeo con subtítulos `subrip` incrustados y quiere un archivo `.srt` al lado.
- Quiere específicamente subtítulos en español (latino, neutro o genérico).

NO usar esta skill cuando:

- El usuario quiere **descargar** subtítulos de internet (usar `search-subtitles`).
- El usuario quiere **re-sincronizar** un `.srt` ya existente (usar `synchronize-subtitles`).
- El usuario quiere **convertir** entre formatos (`.ass` → `.srt`, etc.).
- El vídeo solo tiene subtítulos en un formato distinto de `subrip` (por ejemplo PGS, ASS/SSA o WebVTT).
- La carpeta contiene más de un vídeo (elección ambigua; el script aborta con un mensaje claro).

## Prioridad de selección

Se extrae **una sola pista**, la primera que cumpla este orden:

1. **Español latino**: `language=spa` y el título de la pista contiene "latin" o "latino" (case-insensitive; p. ej. "Spanish (Latin American)").
2. **Español neutro**: `language=spa` y el título contiene "neutral" o "neutro".
3. **Español**: cualquier otra pista `spa` (la primera si hay varias).
4. **Ninguna**: no se extrae nada y se avisa: *"No se puede extraer ningún subtítulo .srt: no existe ninguna pista subrip en español."* (exit code 4).

## Convención de nombrado

La salida siempre es `<video>.es.srt`, sin excepciones por el nombre del vídeo. Solo se aceptan pistas españolas con códec `subrip`, cuya salida se normaliza a UTF-8 con BOM. Cualquier otro idioma o códec se descarta. Si el destino ya existe, se sobrescribe sin preguntar.

## Workflow

### 1. Localizar la carpeta objetivo
- Si el cwd ya contiene el vídeo, usarlo.
- Si no, tomar la ruta de carpeta que dé el usuario (absoluta o relativa al cwd).
- Glob para las extensiones configuradas: `*.mkv`, `*.mp4`, `*.avi`, `*.mov`, `*.m4v`.

### 2. Resolver el vídeo
- Se requiere exactamente **un** vídeo en la carpeta.
- Si no hay ninguno: abortar con error claro (exit code 1).
- Si hay más de uno: abortar con un error que pida dejar solo uno (exit code 2).

### 3. Confirmar el entorno (en silencio)
- Comprobar que `ffprobe` y `ffmpeg` están en el PATH (`shutil.which`). Si falta alguno, abortar (exit code 3); no hay fallback.

### 4. Ejecutar el script incluido
```
python scripts/extract_subs.py [carpeta]
```

El script lo hace todo de extremo a extremo:

- **Detección** automática; sin flags. Si el usuario pasa una carpeta, debe ser el único argumento posicional.
- **Listado** de pistas con `ffprobe` (índice absoluto, códec, idioma, título) impreso en stdout.
- **Selección** de una pista según la prioridad de arriba; el motivo elegido se imprime ("español latino", "español neutro" o "español").
- **Extracción** con `ffmpeg -map 0:N -c:s copy` (copia directa, instantánea, sin pérdida). Coste: segundos.
- **Codificación** del resultado como UTF-8 con BOM.
- **Nombrado** según la convención anterior. Sobrescribe sin preguntar.

### 5. Verificar e informar
- Tras terminar, listar la carpeta y confirmar la presencia del archivo destino.
- Mostrar la línea de resumen del propio script:
  - `OK -> <archivo>` — éxito, con el tamaño en bytes.
  - `ERROR: <razón>` — aborto, con la razón.
  - Si el resultado es exit code 4, explicar al usuario que el vídeo no tiene pistas `.srt` (`subrip`) en español y que no se extrajo nada; las opciones son descargar el subtítulo (`search-subtitles`) o usar otra herramienta para convertir formatos.

## Known pitfalls

- Solo se extraen pistas `subrip`. Los subtítulos PGS, ASS/SSA, WebVTT y cualquier otro códec se ignoran; esta skill no convierte formatos ni hace OCR.
- El índice usado en `ffmpeg -map 0:N` es el **índice absoluto de stream** que reporta ffprobe (campo `index`), no el ordinal entre subtítulos. No "corregir" ese número.
- Se extrae **una sola** pista por diseño. Si el usuario quiere varias, que lo pida explícitamente y se extraen a mano con ffmpeg.
- El script no maneja varios vídeos en la carpeta. Es intencional: elegir uno en silencio sería peor que pedir al usuario que limpie la carpeta.
- En consolas Windows, el script fuerza UTF-8 en stdout (`sys.stdout.reconfigure(encoding="utf-8")`) para que `á`, `é`, `í`, etc. se impriman bien.

## Reusable script reference

| Script | Propósito |
| --- | --- |
| `scripts/extract_subs.py` | Extractor. Auto-detecta el vídeo, elige UNA pista española `subrip` por prioridad (español latino > español neutro > español), la vuelca a `<video>.es.srt` y la normaliza a UTF-8 con BOM. Sin flags; acepta una carpeta opcional como único argumento. |

Exit codes:
- `0` — éxito (pista extraída).
- `1` — no hay vídeo en la carpeta.
- `2` — error de uso (demasiados argumentos, carpeta inválida, varios vídeos).
- `3` — `ffmpeg`/`ffprobe` no disponible o falló al listar pistas.
- `4` — no hay pista `subrip` elegible en español; no se extrajo nada.
- `5` — la extracción falló.
