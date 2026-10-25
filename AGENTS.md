# Project conventions

- Use XXBeadPattern as the application and project display name.
- Write code comments and docstrings in English. Support Chinese and English interface text through core/i18n.py. Preserve editing state when switching languages.
- Keep README.md bilingual: the complete English version first, followed by the complete Chinese version. Do not interleave languages by section.
- Use data/mard_221.csv as the shared palette for automatic matching and manual color edits.
- Run `.venv/bin/python -m unittest discover -s tests -v` after behavior changes.
- Preserve unrelated local changes when staging commits.
