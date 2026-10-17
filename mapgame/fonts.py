"""Press Start 2P (OFL) for the CRT look, fetched from Google Fonts on first use."""
import os, re, urllib.request
from . import DATA


def press_start(size=8):
    from PIL import ImageFont
    cache = os.path.join(DATA, "fonts"); os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, "PressStart2P.ttf")
    if not os.path.exists(path):
        try:   # an old user agent makes Google Fonts hand back plain TTF urls
            req = urllib.request.Request("https://fonts.googleapis.com/css2?family=Press+Start+2P", headers={"User-Agent": "Mozilla/4.0"})
            css = urllib.request.urlopen(req, timeout=30).read().decode()
            url = re.search(r"https://fonts\.gstatic\.com[^)]+", css).group(0)
            open(path, "wb").write(urllib.request.urlopen(url, timeout=30).read())
        except Exception:
            return ImageFont.load_default()
    return ImageFont.truetype(path, size)
