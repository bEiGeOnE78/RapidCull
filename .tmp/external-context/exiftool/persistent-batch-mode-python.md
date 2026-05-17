---
source: Context7 API + official docs
library: ExifTool
package: exiftool
topic: persistent batch mode metadata extraction in Python
fetched: 2026-03-14T00:00:00Z
official_docs: https://exiftool.org/exiftool_pod.html
---

## Relevant ExifTool documentation (filtered)

### 1) Persistent process: `-stay_open` + `-@`
- Start ExifTool as a long-running process:
  - `exiftool -stay_open True -@ -`
- `-stay_open` keeps ExifTool reading arguments after EOF when set to `True`/`1`; stop with `False`/`0`.
- `-@ ARGFILE` reads arguments from a file or stdin (`-`), one argument per line.
- Docs note a possible delay with disk argfiles; using a pipe (`-@ -`) avoids this.

### 2) Command framing: `-execute[NUM]`
- End each request with `-execute` (or `-execute123` etc).
- ExifTool processes all args up to that boundary and returns a ready marker.
- With `-stay_open`, completion marker is `{ready}` or `{readyNUM}`.
- Numbered execute/ready pairs are intended for response synchronization.

### 3) Output marker/delimiter behavior
- Ready marker appears on stdout unless output mode suppresses it.
- Docs explicitly note: `{ready}` message is not output when `-q` or `-T` is used.
- If a number is supplied in `-executeNUM`, `-q` does **not** suppress `{readyNUM}`.
- Practical implication: always use numbered `-executeN` and wait for `{readyN}`.

### 4) JSON output: `-j` (`-json`)
- Use `-j` for machine parsing.
- JSON output is UTF-8.
- `-a` is implied with `-json`, but duplicate JSON names are suppressed unless using unique group naming (eg. `-G4`).
- Array/list behavior: list tags are JSON arrays unless `-sep` is used.
- For strongly typed consumers, docs suggest `-api structformat=jsonq` to force numeric-looking values to remain quoted strings.

### 5) Safe argument passing patterns
- Because `-@` consumes one argument per line, do **not** shell-join request strings.
- Send each option/tag/path as a separate line to stdin of the persistent process.
- Treat user-provided strings as data lines, never as shell fragments.
- Prefer explicit terminators and strict request builders:
  - one arg per line
  - append `-executeN`
  - read until `{readyN}`

### 6) Lifecycle management notes from docs + operational guidance
- Shutdown sequence: send `-stay_open` then `False` then final `-executeN` (or terminate process if needed).
- ExifTool docs define protocol markers but not app-level timeout values.
- Application guidance:
  - enforce per-request timeout waiting for `{readyN}`
  - on timeout: kill process, restart cleanly, retry idempotent reads once
  - treat stderr warnings separately from transport/protocol failures

## Minimal robust request/response protocol (Python-oriented)

1. Spawn once:
   - argv: `['exiftool','-stay_open','True','-@','-','-j','-G4','-n','-api','structformat=jsonq']`
2. For each request id `N`:
   - write args (one per line), then `-executeN\n`
   - flush stdin
   - read stdout until line containing exactly `{readyN}`
   - parse preceding stdout chunk as JSON payload
   - capture/record stderr lines as warnings/errors
3. Timeout handling:
   - if `{readyN}` not received within timeout, kill/restart process and retry once
4. Close:
   - send `-stay_open\nFalse\n-executeN\n`, flush, wait briefly, then terminate if still alive

## Sources
- ExifTool app docs: https://exiftool.org/exiftool_pod.html
- ExifTool stay_open/execute details (Context7 source reference): https://github.com/exiftool/exiftool/blob/master/windows_exiftool.txt
