# reqpin

Stdlib-only Python 3 CLI that lints `requirements.txt` files so builds stay reproducible.

## Why
Unpinned or duplicated dependencies and malformed lines cause surprise upgrades and broken installs.

## Install
No dependencies. Copy `reqpin.py` or run it in place (`python3 reqpin.py`).

## Usage
    python3 reqpin.py requirements.txt [more.txt ...]
    python3 reqpin.py --require-hashes requirements.txt
    python3 reqpin.py --json requirements.txt
    cat requirements.txt | python3 reqpin.py -

Checks: `unpinned` (no `==`), `duplicate` (same normalized name and marker),
`bad-line` (unparseable or invalid specifier), `missing-hash` (with `--require-hashes`).
Comments, `-r`/`-c` includes and other pip options are ignored; extras and env markers are
understood; VCS/URL lines (`git+https://...`, `name @ url`, `-e ...`) are not flagged.

Exit codes: 0 clean, 1 problems found, 2 unreadable file.

Example:

    $ python3 reqpin.py requirements.txt
    requirements.txt:2: unpinned: flask is not pinned with ==
    1 problem(s)

## Tests
    python3 -m unittest discover -s tests -v

## License
MIT
