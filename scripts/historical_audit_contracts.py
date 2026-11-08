"""Release-independent checks for historical, cumulative feature audits.

Historical feature versions are lower bounds, not simultaneous release pins.
Read the API's canonical version and verify its wiring, without importing it.
"""
import ast
from pathlib import Path
import re


def release_at_least(root: Path, component: str, minimum: str) -> bool:
    if component == 'api':
        tree = ast.parse((root / 'services/api/app/version.py').read_text(encoding='utf-8'))
        versions = [node.value.value for node in tree.body
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                    and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets)]
        main = (root / 'services/api/app/main.py').read_text(encoding='utf-8')
        if len(versions) != 1 or 'from app.version import __version__' not in main:
            return False
        if 'version=__version__' not in main or '"version": __version__' not in main:
            return False
        actual = versions[0]
    else:
        text = (root / f'apps/{component}/pubspec.yaml').read_text(encoding='utf-8')
        match = re.search(r'^version:\s*(\S+)\s*$', text, re.M)
        if not match:
            return False
        actual = match[1]
    pattern = r'(\d+)\.(\d+)\.(\d+)(?:\+(\d+))?'
    a, b = re.fullmatch(pattern, actual), re.fullmatch(pattern, minimum)
    if not a or not b:
        return False
    return tuple(int(n or 0) for n in a.groups()) >= tuple(int(n or 0) for n in b.groups())
