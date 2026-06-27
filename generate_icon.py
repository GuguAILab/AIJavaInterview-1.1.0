"""
Generate app_icon.ico matching the screenshot:
  - Dark navy background
  - Bold red square mug with slightly rounded corners
  - White wavy line on mug body
  - 3 short red steam dashes above mug
  - Dark red C-handle on right
  - Multi-size ICO (16,32,48,64,128,256)
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image, ImageDraw, ImageFont

import os

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")

def draw_icon(size=256):
    img = Image.new("RGBA", (size, size), (18, 24, 45, 255))  # dark navy #12182d
    d   = ImageDraw.Draw(img)

    def sc(v): return max(1, int(v * size / 256))

    # ── Colours ──
    RED        = (210, 35,  25,  255)   # bright red mug
    RED_DARK   = (155, 15,  10,  255)   # darker red for handle/shadow
    RED_SHADE  = (175, 28,  18,  255)   # slightly darker for mug right side
    WHITE      = (255, 255, 255, 230)   # wavy line
    STEAM      = (210, 35,  25,  200)   # steam dashes

    # ── 3 Steam dashes above mug ──
    steam_xs = [sc(80), sc(103), sc(126)]
    for sx in steam_xs:
        # Each dash = 2 short lines with gap (dashed look)
        d.line([(sx, sc(28)), (sx, sc(44))], fill=STEAM, width=sc(4))
        d.line([(sx, sc(50)), (sx, sc(60))], fill=STEAM, width=sc(4))

    # ── Mug body (bold red rounded square) ──
    MX1, MY1 = sc(48),  sc(68)
    MX2, MY2 = sc(178), sc(196)
    radius   = sc(14)
    d.rounded_rectangle([MX1, MY1, MX2, MY2], radius=radius, fill=RED)

    # Right-side shade to give slight 3D feel
    d.rounded_rectangle([MX1 + sc(65), MY1, MX2, MY2],
                        radius=radius, fill=RED_SHADE)

    # ── White wavy line (~) in centre of mug ──
    # Draw as a sine-wave using short arc segments
    wave_y  = (MY1 + MY2) // 2 - sc(4)
    wave_x0 = MX1 + sc(14)
    seg_w   = sc(22)
    amp     = sc(10)
    for i in range(5):
        x0 = wave_x0 + i * seg_w
        x1 = x0 + seg_w
        if i % 2 == 0:
            d.arc([x0, wave_y,       x1, wave_y + amp*2],
                  start=180, end=0, fill=WHITE, width=sc(4))
        else:
            d.arc([x0, wave_y,       x1, wave_y + amp*2],
                  start=0,   end=180, fill=WHITE, width=sc(4))

    # ── Handle (C-shape on right) ──
    hx1 = MX2 - sc(8)
    hy1 = MY1 + sc(24)
    hx2 = MX2 + sc(38)
    hy2 = MY1 + sc(84)
    d.arc([hx1, hy1, hx2, hy2], start=-90, end=90,
          fill=RED_DARK, width=sc(13))

    # ── Mug base / bottom shadow line ──
    d.rectangle([MX1 + sc(6), MY2 - sc(8), MX2 - sc(6), MY2],
                fill=RED_DARK)

    return img


# Build multi-size ICO
sizes  = [16, 32, 48, 64, 128, 256]
images = [draw_icon(s) for s in sizes]
images[0].save(
    OUTPUT,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=images[1:]
)
print(f"✅ Icon saved: {OUTPUT}")
