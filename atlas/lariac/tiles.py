"""Stitch LA County LARIAC7 (2023, 4 inch) web tiles over a bbox into one georeferenced image (Web Mercator)."""
import os, sys, math, json, urllib.request, concurrent.futures, io
from PIL import Image
UA = "mapgame (github.com/justinsovine/escape-from-catalina-island)"
T = "https://svc.pictometry.com/Image/BCC27E3E-766E-CE0B-7D11-AA4760AC43ED/wmts/PICT-LARIAC7--KCrSFBeqgG/default/GoogleMapsCompatible/{z}/{x}/{y}.png"
def tile(lon, lat, z):
    n = 2 ** z; x = (lon + 180) / 360 * n; y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y
def fetch(z, x, y, cache):
    p = os.path.join(cache, f"{z}_{x}_{y}.png")
    if os.path.exists(p): return p
    try:
        b = urllib.request.urlopen(urllib.request.Request(T.format(z=z, x=x, y=y), headers={"User-Agent": UA}), timeout=60).read()
        open(p, "wb").write(b); return p
    except Exception as e: return None
def stitch(name, bbox, z, out_dir):
    cache = os.path.join(out_dir, "cache"); os.makedirs(cache, exist_ok=True)
    x0, y1 = tile(bbox[0], bbox[1], z); x1, y0 = tile(bbox[2], bbox[3], z)
    X0, X1, Y0, Y1 = int(x0), int(x1), int(y0), int(y1)
    jobs = [(z, x, y) for x in range(X0, X1 + 1) for y in range(Y0, Y1 + 1)]
    with concurrent.futures.ThreadPoolExecutor(8) as ex: paths = list(ex.map(lambda j: fetch(*j, cache), jobs))
    W, H = (X1 - X0 + 1) * 256, (Y1 - Y0 + 1) * 256; im = Image.new("RGB", (W, H))
    ok = 0
    for (z_, x, y), p in zip(jobs, paths):
        if p:
            try: im.paste(Image.open(p).convert("RGB"), ((x - X0) * 256, (y - Y0) * 256)); ok += 1
            except Exception: pass
    im.save(os.path.join(out_dir, f"{name}_z{z}.png"))
    # georeference: Web Mercator bounds of the mosaic
    n = 2 ** z; world = 2 * math.pi * 6378137
    mx0 = -world / 2 + X0 / n * world; mx1 = -world / 2 + (X1 + 1) / n * world; my1 = world / 2 - Y0 / n * world; my0 = world / 2 - (Y1 + 1) / n * world
    json.dump(dict(name=name, z=z, tiles=len(jobs), ok=ok, size=[W, H], mercator_bounds=[mx0, my0, mx1, my1], res_m=world / n / 256 * math.cos(math.radians((bbox[1] + bbox[3]) / 2))), open(os.path.join(out_dir, f"{name}_z{z}.json"), "w"))
    print(name, z, "tiles", len(jobs), "ok", ok, "size", W, H, "res m", round(world / n / 256 * math.cos(math.radians((bbox[1] + bbox[3]) / 2)), 3))
if __name__ == "__main__":
    out = sys.argv[1]; name = sys.argv[2]; z = int(sys.argv[3]); bbox = tuple(map(float, sys.argv[4:8]))
    stitch(name, bbox, z, out)
