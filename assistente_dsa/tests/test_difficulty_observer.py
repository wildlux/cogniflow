"""Test dell'osservatore dei momenti di difficoltà (core.difficulty_observer).

Verifica: spento non cattura nulla; acceso cattura solo dopo una smorfia
tenuta abbastanza a lungo; rispetta il cooldown; salva screenshot + registro;
applica la ritenzione. Il "punteggio di difficoltà" derivato dai blendshape
è testato a parte con blendshape sintetici.
"""

import json
import os
import sys
import time
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.difficulty_observer import DifficultyObserver


class FakePixmap:
    """Finto QPixmap: 'salva' scrivendo un file, per non dipendere da Qt."""

    def __init__(self, null=False):
        self._null = null

    def isNull(self):
        return self._null

    def save(self, path, fmt="PNG"):
        if self._null:
            return False
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n")  # firma PNG, contenuto simbolico
        return True


def make_observer(tmp, **kw):
    return DifficultyObserver(
        output_dir=tmp,
        screenshot_provider=lambda: FakePixmap(),
        enabled=kw.pop("enabled", True),
        sustain_s=kw.pop("sustain_s", 0.2),
        cooldown_s=kw.pop("cooldown_s", 0.5),
        threshold=kw.pop("threshold", 0.5),
        **kw,
    )


def _pngs(tmp):
    if not os.path.isdir(tmp):
        return []
    return [n for n in os.listdir(tmp) if n.endswith(".png")]


def test_spento_non_cattura(tmp="/tmp/obs_off"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    obs = make_observer(tmp, enabled=False)
    for _ in range(10):
        obs.on_difficulty(0.9)
        time.sleep(0.05)
    assert not os.path.isdir(tmp) or not _pngs(tmp)


def test_cattura_dopo_smorfia_sostenuta(tmp="/tmp/obs_on"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    obs = make_observer(tmp, sustain_s=0.3)
    obs.on_difficulty(0.8)  # inizia l'episodio
    time.sleep(0.1)
    obs.on_difficulty(0.8)  # non ancora abbastanza a lungo
    assert not _pngs(tmp)
    time.sleep(0.3)
    obs.on_difficulty(0.8)  # ora supera sustain_s -> cattura
    imgs = _pngs(tmp)
    assert len(imgs) == 1
    # registro coerente
    with open(os.path.join(tmp, "eventi.jsonl"), encoding="utf-8") as f:
        rec = json.loads(f.readline())
    assert rec["immagine"] == imgs[0]
    assert rec["indice_difficolta"] >= 0.5


def test_sotto_soglia_azzera(tmp="/tmp/obs_reset"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    obs = make_observer(tmp, sustain_s=0.3)
    obs.on_difficulty(0.8)
    time.sleep(0.2)
    obs.on_difficulty(0.1)  # rilassa il viso: l'episodio si azzera
    time.sleep(0.2)
    obs.on_difficulty(0.8)  # riparte da capo, non abbastanza per catturare
    assert not _pngs(tmp)


def test_cooldown(tmp="/tmp/obs_cool"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    obs = make_observer(tmp, sustain_s=0.1, cooldown_s=1.0)

    def episodio():
        obs.on_difficulty(0.9)
        time.sleep(0.15)
        obs.on_difficulty(0.9)

    episodio()
    assert len(_pngs(tmp)) == 1
    episodio()  # subito dopo: bloccato dal cooldown
    assert len(_pngs(tmp)) == 1


def test_pixmap_nullo_non_salva(tmp="/tmp/obs_null"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    obs = DifficultyObserver(
        output_dir=tmp,
        screenshot_provider=lambda: FakePixmap(null=True),
        enabled=True,
        sustain_s=0.1,
    )
    obs.on_difficulty(0.9)
    time.sleep(0.15)
    obs.on_difficulty(0.9)
    assert not os.path.isdir(tmp) or not _pngs(tmp)


def test_ritenzione(tmp="/tmp/obs_ret"):
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    vecchio = os.path.join(tmp, "difficolta_20000101_000000.png")
    with open(vecchio, "wb") as f:
        f.write(b"x")
    old_time = time.time() - 40 * 86400  # 40 giorni fa
    os.utime(vecchio, (old_time, old_time))
    obs = make_observer(tmp, retention_days=30)
    obs.purge_old()
    assert not os.path.exists(vecchio)


def test_punteggio_da_blendshape():
    from Artificial_Intelligence.Video.visual_background import VideoThread

    BS = namedtuple("BS", "category_name score")

    def score(**kw):
        return VideoThread._difficulty_from_blendshapes(
            [BS(k, v) for k, v in kw.items()]
        )

    neutro = score(browDownLeft=0.0, mouthFrownLeft=0.0)
    smorfia = score(
        browDownLeft=0.9,
        browDownRight=0.9,
        mouthFrownLeft=0.7,
        mouthFrownRight=0.7,
        eyeSquintLeft=0.6,
        eyeSquintRight=0.6,
    )
    sorriso = score(mouthSmileLeft=0.9, mouthSmileRight=0.9)
    assert smorfia > 0.5
    assert neutro < 0.2
    assert sorriso < 0.2  # un sorriso non è difficoltà


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  OK   {name}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {name}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERR  {name}: {e}")
    sys.exit(1 if failed else 0)
