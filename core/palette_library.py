"""Discover bundled palettes and persist user-imported CSV palettes independently."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .palette import Palette


@dataclass(frozen=True)
class PaletteSpec:
    id: str
    path: Path
    name_en: str
    name_zh: str
    count: int
    source: str = ''
    reference: str = 'community'

    def load(self) -> Palette:
        return Palette(str(self.path), palette_id=self.id, name=self.name_en, name_zh=self.name_zh,
                       source=self.source, reference=self.reference)

    def label(self, language: str) -> str:
        return self.name_en if language == 'en' else self.name_zh


class PaletteLibrary:
    def __init__(self, data_dir: Path, user_dir: Path):
        self.data_dir = data_dir
        self.user_dir = user_dir
        self.specs: dict[str, PaletteSpec] = {}
        self.reload()

    @staticmethod
    def _spec(record: dict, root: Path) -> PaletteSpec:
        path = (root/record['file']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Palette paths must stay inside their data directory.')
        return PaletteSpec(record['id'], path, record['name_en'], record['name_zh'], record['count'],
                           record.get('source', ''), record.get('reference', 'custom'))

    def reload(self) -> None:
        records = json.loads((self.data_dir/'palettes.json').read_text(encoding='utf-8'))
        self.specs = {record['id']: self._spec(record, self.data_dir) for record in records}
        if self.user_dir.exists():
            for path in sorted(self.user_dir.glob('*.json')):
                try:
                    spec = self._spec(json.loads(path.read_text(encoding='utf-8')), self.user_dir)
                    if spec.id.startswith('custom-') and spec.path.is_file():
                        self.specs[spec.id] = spec
                except (ValueError, KeyError, OSError, TypeError):
                    # A damaged optional import must not prevent loading bundled palettes.
                    continue

    def import_csv(self, path: Path) -> PaletteSpec:
        raw = path.read_bytes()
        if len(raw) > 2_000_000:
            raise ValueError('色卡文件不能超过 2 MB。')
        palette = Palette(str(path))
        digest = hashlib.sha256(raw).hexdigest()[:20]
        palette_id = 'custom-'+digest
        if palette_id in self.specs:
            return self.specs[palette_id]
        self.user_dir.mkdir(parents=True, exist_ok=True)
        target = self.user_dir/(digest+'.csv')
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes(raw)
        temporary.replace(target)
        record = {'id': palette_id, 'file': target.name, 'name_en': path.stem, 'name_zh': path.stem,
                  'count': len(palette), 'source': 'Imported CSV', 'reference': 'custom'}
        metadata = target.with_suffix('.json')
        temporary = metadata.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(metadata)
        self.reload()
        return self.specs[palette_id]
