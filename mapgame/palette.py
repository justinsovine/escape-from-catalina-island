"""Palettes. The rule in every one: terrain and features are desaturated, the route is the only saturated
thing, so it stands out by saturation and luminance, not just hue. Day colors are a bright triad tuned to the
background (dark palettes get light, luminous hues; the paper palette gets printed-ink hues).

Tokens: bg/plate/slab_* (iso), card/body/rim/contour_* (wire), paper/cink/water/croute (crt), route/days/glow (all)."""

PALETTES = {
    "mono": dict(
        bg="#0c0c0c", plate="#131313", plate_side="#0f0f0f", plate_edge="#5c5c5c",
        slab_lo=(0.13, 0.13, 0.13), slab_hi=(0.29, 0.29, 0.29), slab_edge="#707070", side_edge="#5c5c5c",
        stream="#56707c", road="#8a8a8a", trail="#8a8a8a", pier="#dcdcdc", building=("#e0e0e0", "#8f8f8f", "#b8b8b8"),
        tree=("#c8c8c8", "#e2e2e2"), label="#f4f4f4", label_bg="#0c0c0c", peak="#ffffff", muted="#7a7a7a", title="#e6e6e6",
        route="#ffffff", days={"mon": "#ffffff", "tue": "#ffffff", "wed": "#ffffff"}, glow=False, casing="#0c0c0c", dashed=True,
        card_bg="#1e2124", card="#141618", body="#17191c", rim="#7fa6b4", ink="#eef1f2", wmuted="#8b9499", tick="#5f6b70", stem="#cfd6d9",
        contour_lo=(0.50, 0.56, 0.62), contour_hi=(0.95, 0.96, 0.97), pin_camp="#e05a3a", pin_peak="#8fd3e8", pin_flag="#f5c400", pin_end="#eef1f2",
        paper=(255, 255, 255), cink=(0, 0, 0), water=(0, 0, 0), croute=(0, 0, 0), cdays={"mon": (0, 0, 0), "tue": (0, 0, 0), "wed": (0, 0, 0)},
        crt_streams=False, bezel=(0, 0, 0), caption=(120, 120, 120)),

    # dark and cool: navy sea, blue-grey slabs, luminous warm route
    "night": dict(
        bg="#0a1118", plate="#0d1b2a", plate_side="#0a1520", plate_edge="#3f5a6e",
        slab_lo=(0.11, 0.16, 0.21), slab_hi=(0.30, 0.38, 0.45), slab_edge="#5b7386", side_edge="#3f5566",
        stream="#3d7a9a", road="#7c8a94", trail="#7c8a94", pier="#d6e2ea", building=("#dfe6ea", "#8c98a0", "#b7c1c7"),
        tree=("#b9c7cf", "#d7e2e8"), label="#f1f5f7", label_bg="#0a1118", peak="#ffffff", muted="#6f8290", title="#e8eef2",
        route="#ffb000", days={"mon": "#ff6b5c", "tue": "#49c9ff", "wed": "#ffd23f"}, glow=True, casing="#0a1118", dashed=False,
        card_bg="#121a22", card="#0e151c", body="#101a24", rim="#5f93ab", ink="#eef3f6", wmuted="#7f94a3", tick="#4f6675", stem="#c7d4dc",
        contour_lo=(0.36, 0.48, 0.58), contour_hi=(0.86, 0.93, 0.98), pin_camp="#ff6b5c", pin_peak="#49c9ff", pin_flag="#ffd23f", pin_end="#eef3f6",
        paper=(14, 20, 27), cink=(140, 164, 180), water=(28, 52, 76), croute=(255, 176, 0), cdays={"mon": (255, 107, 92), "tue": (73, 201, 255), "wed": (255, 210, 63)},
        crt_streams=True, bezel=(0, 0, 0), caption=(110, 130, 145)),

    # printed map: cream paper, tan slabs, pale blue water, ink-colored route
    "paper": dict(
        bg="#efe7d3", plate="#cfe0e6", plate_side="#b9cdd4", plate_edge="#6f8591",
        slab_lo=(0.91, 0.86, 0.74), slab_hi=(0.70, 0.63, 0.50), slab_edge="#6e5f46", side_edge="#8c7d62",
        stream="#4f86ad", road="#6d655a", trail="#6d655a", pier="#3b332a", building=("#3b332a", "#6d655a", "#55493c"),
        tree=("#4f6b45", "#5f7f52"), label="#1c1a17", label_bg="#efe7d3", peak="#1c1a17", muted="#7a6f5e", title="#1c1a17",
        route="#d7261e", days={"mon": "#d7261e", "tue": "#1d57c9", "wed": "#c99700"}, glow=False, casing="#efe7d3", dashed=False,
        card_bg="#e6ddc6", card="#f3eee2", body="#ebe4d2", rim="#6f8a99", ink="#1c1a17", wmuted="#7a6f5e", tick="#9a8f7c", stem="#5a5146",
        contour_lo=(0.62, 0.55, 0.42), contour_hi=(0.22, 0.18, 0.12), pin_camp="#d7261e", pin_peak="#1d57c9", pin_flag="#c99700", pin_end="#1c1a17",
        paper=(241, 234, 214), cink=(27, 27, 27), water=(58, 111, 168), croute=(215, 38, 30), cdays={"mon": (215, 38, 30), "tue": (29, 87, 201), "wed": (201, 151, 0)},
        crt_streams=True, bezel=(20, 18, 16), caption=(140, 130, 110)),
}

# CRT-only looks: a two-ink print on a screen, and a green phosphor terminal
PALETTES["ink"] = dict(PALETTES["paper"], paper=(241, 234, 214), cink=(27, 27, 27), water=(58, 111, 168), croute=(215, 38, 30), bezel=(0, 0, 0))
PALETTES["phosphor"] = dict(PALETTES["night"], paper=(5, 18, 11), cink=(57, 211, 83), water=(16, 66, 42), croute=(247, 255, 138),
                            cdays={"mon": (255, 170, 120), "tue": (120, 255, 230), "wed": (247, 255, 138)}, bezel=(0, 0, 0), caption=(40, 120, 60))


def get(name="mono"):
    if name not in PALETTES: raise SystemExit(f"unknown palette {name}; known: {', '.join(PALETTES)}")
    return PALETTES[name]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
