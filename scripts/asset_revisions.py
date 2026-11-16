"""Update content revisions after editing artwork, CSS, or the entry script."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['layer0.webp', 'time0.png', 'layer1.webp', 'time1.png',
         'layer2.webp', 'time2.png', 'finished.webp']


def update_revisions():
    path = ROOT / 'assets/manifest.json'
    manifest = json.loads(path.read_text())
    html_path = ROOT / 'index.html'
    html = html_path.read_text()
    for variant in ['desktop', 'mobile']:
        revisions = {name: hashlib.sha256((ROOT / 'assets' / variant / name).read_bytes()).hexdigest()[:20]
                     for name in FILES}
        manifest[variant]['revisions'] = revisions
        # Keep the no-JS / load-failure image on the same version as the renderer.
        html = re.sub(rf'assets/{variant}/finished\.webp(?:\?v=[a-f0-9]+)?',
                      f'assets/{variant}/finished.webp?v={revisions["finished.webp"]}', html)
    # Styling and initial state change independently of the artwork. Give
    # their entry URLs new cache keys too, including caches from old previews.
    for name in ['styles/site.css', 'src/main.js']:
        revision = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:20]
        html = re.sub(re.escape(name) + r'(?:\?v=[a-f0-9]+)?',
                      f'{name}?v={revision}', html)
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    html_path.write_text(html)


if __name__ == '__main__':
    update_revisions()
