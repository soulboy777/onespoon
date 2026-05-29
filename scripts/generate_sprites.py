"""像素画角色生成器 — 5 个状态 (byte array 手绘)"""

import os
from pathlib import Path

# 128×128 RGBA canvas, 8×8 grid (16px per cell, 2px brush)
# 实际用 64×64 绘制再 2x 放大，保证像素感
SZ = 64
F = 2  # 2x scale

PINK = (0xF8, 0xBB, 0xD0, 0xFF)       # 粉色睡衣
DARK = (0x2D, 0x2D, 0x2D, 0xFF)        # 深色头发
SKIN = (0xFF, 0xE0, 0xC8, 0xFF)        # 肤色
WHITE = (0xFF, 0xFF, 0xFF, 0xFF)       # 白色
RED = (0xFF, 0x6B, 0x6B, 0xFF)         # 红色强调
BLANKET = (0xE8, 0xA8, 0xC0, 0xFF)     # 被子粉色
TRANSPARENT = (0, 0, 0, 0)


def new_canvas():
    return [[TRANSPARENT for _ in range(SZ)] for _ in range(SZ)]


def fill_rect(canvas, x, y, w, h, color):
    for iy in range(max(0, y), min(SZ, y + h)):
        for ix in range(max(0, x), min(SZ, x + w)):
            canvas[iy][ix] = color


def fill_circle(canvas, cx, cy, r, color):
    for iy in range(max(0, cy - r), min(SZ, cy + r + 1)):
        for ix in range(max(0, cx - r), min(SZ, cx + r + 1)):
            if (ix - cx) ** 2 + (iy - cy) ** 2 <= r**2:
                canvas[iy][ix] = color


def line(canvas, x1, y1, x2, y2, color, w=2):
    dx = abs(x2 - x1); dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1; sy = 1 if y1 < y2 else -1
    err = dx + dy
    while True:
        fill_rect(canvas, x1 - w // 2, y1 - w // 2, w, w, color)
        if x1 == x2 and y1 == y2: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x1 += sx
        if e2 <= dx: err += dx; y1 += sy


def draw_head(canvas, cx, cy, r=8):
    """头 + 头发"""
    fill_circle(canvas, cx, cy, r, SKIN)           # 脸
    fill_circle(canvas, cx, cy - r // 2, r + 1, DARK)  # 头发（覆盖上半）
    fill_rect(canvas, cx - r, cy - r, r * 2, r, DARK)  # 顶部补齐
    # 粉色挑染
    fill_rect(canvas, cx + r - 2, cy - r - 1, 3, 3, PINK)
    fill_rect(canvas, cx - r - 1, cy - r, 3, 3, PINK)


def draw_eyes(canvas, cx, cy, state="open"):
    """眼睛: open / half / closed / x_x"""
    if state == "open":
        fill_rect(canvas, cx - 4, cy - 1, 3, 3, DARK)   # 左
        fill_rect(canvas, cx + 1, cy - 1, 3, 3, DARK)   # 右
        fill_rect(canvas, cx - 3, cy, 1, 1, WHITE)      # 高光
        fill_rect(canvas, cx + 2, cy, 1, 1, WHITE)
    elif state == "half":
        fill_rect(canvas, cx - 4, cy - 1, 3, 2, DARK)
        fill_rect(canvas, cx + 1, cy - 1, 3, 2, DARK)
    elif state == "closed":
        fill_rect(canvas, cx - 4, cy - 1, 3, 1, DARK)
        fill_rect(canvas, cx + 1, cy - 1, 3, 1, DARK)
    elif state == "happy":
        fill_rect(canvas, cx - 3, cy - 1, 2, 2, DARK)
        fill_rect(canvas, cx + 1, cy - 1, 2, 2, DARK)
        # 脸红
        fill_rect(canvas, cx - 6, cy - 1, 2, 3, RED)
        fill_rect(canvas, cx + 4, cy - 1, 2, 3, RED)
    elif state == "x_x":
        line(canvas, cx - 5, cy - 2, cx - 3, cy, DARK, 2)  # 左 X
        line(canvas, cx - 3, cy - 2, cx - 5, cy, DARK, 2)
        line(canvas, cx + 1, cy - 2, cx + 3, cy, DARK, 2)  # 右 X
        line(canvas, cx + 3, cy - 2, cx + 1, cy, DARK, 2)
    elif state == "none":
        pass


def draw_mouth(canvas, cx, cy, style="normal"):
    if style == "normal":
        fill_rect(canvas, cx - 2, cy, 5, 1, DARK)
    elif style == "smile":
        fill_rect(canvas, cx - 2, cy, 5, 1, DARK)
        fill_rect(canvas, cx - 3, cy - 1, 1, 1, DARK)
        fill_rect(canvas, cx + 2, cy - 1, 1, 1, DARK)
    elif style == "open":
        fill_rect(canvas, cx - 2, cy, 5, 2, DARK)
    elif style == "zZz":
        fill_rect(canvas, cx - 2, cy, 3, 3, DARK)


def draw_body(canvas, cx, cy, w=10, h=12, color=PINK):
    """身体 + 睡衣"""
    fill_rect(canvas, cx - w // 2, cy, w, h, color)
    # 蝴蝶结在领口
    fill_rect(canvas, cx - 2, cy, 4, 3, RED)


def draw_legs(canvas, cx, cy, length=10, w=3):
    fill_rect(canvas, cx - w - 1, cy, w, length, SKIN)
    fill_rect(canvas, cx + 1, cy, w, length, SKIN)
    # 睡裤
    fill_rect(canvas, cx - w - 1, cy, w, 4, PINK)
    fill_rect(canvas, cx + 1, cy, w, 4, PINK)


def export_png(canvas, filepath):
    from PIL import Image
    img = Image.new("RGBA", (SZ, SZ))
    pixels = img.load()
    for y in range(SZ):
        for x in range(SZ):
            pixels[x, y] = canvas[y][x]
    # 2x 放大
    img = img.resize((SZ * F, SZ * F), Image.NEAREST)

    # 嵌入到 300×500 画布中
    big = Image.new("RGBA", (300, 500))
    big.paste(img, (150 - SZ, 200 - SZ))

    os.makedirs(Path(filepath).parent, exist_ok=True)
    big.save(filepath)
    print(f"  OK {filepath}")


# ══════════════════════════
#  5 角色状态生成
# ══════════════════════════

def gen_idle():
    c = new_canvas()
    draw_head(c, 32, 14)
    draw_eyes(c, 32, 16, "half")
    draw_mouth(c, 32, 18, "normal")
    draw_body(c, 32, 24)
    line(c, 20, 26, 10, 34, SKIN)   # 左臂
    line(c, 44, 26, 54, 34, SKIN)   # 右臂
    draw_legs(c, 32, 36)
    return c


def gen_sleeping():
    """正躺，被子半盖，露 2 手 1 脚"""
    c = new_canvas()
    # 头 (右侧，枕在枕头上)
    draw_head(c, 34, 12)
    draw_eyes(c, 34, 14, "closed")
    draw_mouth(c, 34, 17, "zZz")
    # 枕头
    fill_rect(c, 20, 8, 20, 10, WHITE)
    # 身体(水平躺)
    fill_rect(c, 10, 22, 30, 10, PINK)  # 睡衣身体
    # 被子 (只盖下半身)
    fill_rect(c, 8, 30, 34, 24, BLANKET)
    # 被子纹理
    fill_rect(c, 10, 34, 30, 1, PINK)
    fill_rect(c, 10, 40, 30, 1, PINK)
    # 露出的手 (2只)
    fill_rect(c, 4, 22, 5, 3, SKIN)   # 左手伸出
    fill_rect(c, 38, 24, 5, 3, SKIN)  # 右手伸出
    # 露出的脚 (1只)
    fill_rect(c, 15, 54, 6, 6, SKIN)  # 左脚伸出被子
    # zZz
    fill_rect(c, 48, 6, 4, 3, WHITE)
    fill_rect(c, 50, 2, 5, 3, WHITE)
    return c


def gen_thinking():
    """趴着，头朝下"""
    c = new_canvas()
    # 头 (朝下，趴在手臂上)
    draw_head(c, 32, 8)
    draw_eyes(c, 32, 10, "half")
    draw_mouth(c, 32, 13, "normal")
    # 手臂枕着
    fill_rect(c, 20, 18, 24, 4, SKIN)
    # 身体平趴
    fill_rect(c, 18, 22, 28, 8, PINK)
    # 腿翘起
    fill_rect(c, 20, 30, 6, 14, PINK)
    fill_rect(c, 38, 30, 6, 14, PINK)
    # 脚
    fill_rect(c, 18, 44, 7, 4, SKIN)
    fill_rect(c, 36, 44, 10, 4, SKIN)   # 一只脚翘高
    # 手指点在嘴边
    fill_rect(c, 28, 14, 2, 2, SKIN)
    return c


def gen_happy():
    """举手跳起"""
    c = new_canvas()
    draw_head(c, 32, 8)
    draw_eyes(c, 32, 10, "happy")
    draw_mouth(c, 32, 13, "smile")
    # 身体微侧
    fill_rect(c, 26, 20, 12, 10, PINK)
    # 跳起姿态 (脚离地)
    fill_rect(c, 24, 30, 6, 4, PINK)
    fill_rect(c, 34, 30, 6, 4, PINK)
    # 脚离地
    fill_rect(c, 22, 34, 6, 4, SKIN)
    fill_rect(c, 36, 34, 6, 4, SKIN)
    # 高举双手
    line(c, 22, 22, 8, 8, SKIN)
    line(c, 42, 22, 56, 8, SKIN)
    fill_rect(c, 6, 4, 5, 5, SKIN)     # 左手 (拳头)
    fill_rect(c, 54, 4, 5, 5, SKIN)    # 右手 (拳头)
    # 星星 (庆祝)
    fill_rect(c, 50, 2, 2, 2, RED)
    fill_rect(c, 10, 0, 2, 2, RED)
    return c


def gen_busy():
    """慌张挥手"""
    c = new_canvas()
    draw_head(c, 32, 12)
    draw_eyes(c, 32, 14, "x_x")
    draw_mouth(c, 32, 17, "open")
    # 冒汗
    fill_rect(c, 36, 4, 3, 5, WHITE)
    fill_rect(c, 40, 2, 3, 5, WHITE)
    # 身体
    fill_rect(c, 26, 24, 12, 10, PINK)
    # 慌乱挥手
    line(c, 22, 26, 6, 14, SKIN)
    line(c, 42, 26, 58, 14, SKIN)
    line(c, 6, 14, 14, 10, SKIN)       # 左手第二动作
    line(c, 58, 14, 54, 10, SKIN)
    # 腿 (紧张小碎步)
    fill_rect(c, 24, 34, 5, 8, PINK)
    fill_rect(c, 35, 34, 5, 8, PINK)
    fill_rect(c, 22, 42, 5, 4, SKIN)
    fill_rect(c, 37, 42, 5, 4, SKIN)
    # 汗滴
    fill_rect(c, 38, 6, 3, 4, WHITE)
    return c


# ══════════════════════════
#  生成 & 保存
# ══════════════════════════

def main():
    out_dir = Path(__file__).resolve().parent.parent / "src" / "ui" / "resources" / "characters"
    print(f"Generating sprites -> {out_dir}")

    export_png(gen_idle(), str(out_dir / "idle.png"))
    export_png(gen_sleeping(), str(out_dir / "sleeping.png"))
    export_png(gen_thinking(), str(out_dir / "thinking.png"))
    export_png(gen_happy(), str(out_dir / "happy.png"))
    export_png(gen_busy(), str(out_dir / "busy.png"))

    print("All done!")


if __name__ == "__main__":
    main()
