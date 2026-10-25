# Project conventions

- Use XXBeadPattern as the application and project display name.
- Write code comments and docstrings in English. Support Chinese and English interface text through core/i18n.py. Preserve editing state when switching languages.
- Keep README.md bilingual: the complete English version first, followed by the complete Chinese version. Do not interleave languages by section.
- Use the selected Palette instance for automatic matching, manual edits, legends, and exports. Keep data/mard_221.csv unchanged as the default original palette.
- Bundle only traceable palette snapshots; record sources, pinned commits, exclusions, and licenses in data/palettes.json. Never invent unidentified color codes or claim complete market coverage.
- Run `.venv/bin/python -m unittest discover -s tests -v` after behavior changes.
- Preserve unrelated local changes when staging commits.
