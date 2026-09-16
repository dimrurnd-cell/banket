"""Prepare supplied corporate event photos, preserving originals."""
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / 'assets/img/opt'
SOURCES = {
    '5440828660811239245': '5440828660811239245',
    **{name: name for name in ('072A9084', '072A9086', '072A3626', '072A3530', '072A3532',
       '072A3568', '072A3628', '072A3549', '072A3614', '072A3604', '072A3537')},
    **{f'ny2020-{n}': f'НГ2020 ({n}) копия' for n in (1, 2, 3)},
    **{f'img-{n}': f'IMG_{n} копия' for n in (2156, 2167, 2164)},
}

if __name__ == '__main__':
    manifest_path = ROOT / '_src/images.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    before = after = 0
    for slug, name in SOURCES.items():
        source = FOLDER / (name + '.jpg')
        before += source.stat().st_size
        with Image.open(source) as original:
            photo = ImageOps.exif_transpose(original).convert('RGB')
            w, h = photo.size
            widths = sorted(set(min(w, size) for size in (400, 800, 1280, 1920)))
            rows = []
            for width in widths:
                target = FOLDER / f'event-{slug}-{width}.webp'
                if not target.exists() or target.stat().st_mtime < source.stat().st_mtime:
                    photo.resize((width, round(h * width / w)), Image.Resampling.LANCZOS).save(
                        target, 'WEBP', quality=85, method=6)
                rows.append([width, target.stat().st_size, '/assets/img/opt/' + target.name])
            after += rows[-1][1]
            url = rows[-1][2]
            manifest['images'][url] = {'src': url, 'slug': 'event-' + slug,
                'w': w, 'h': h, 'alpha': False,
                'files': {'webp': {'ext': 'webp', 'widths': rows}}}
        print(slug, rows[-1][1])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(SOURCES)} photos: {before / 1024**2:.1f} MB originals -> {after / 1024**2:.1f} MB largest WebP variants')
