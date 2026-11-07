#导入库
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from pyproj import CRS, Transformer
from shapely.geometry import box as geo_box
from PIL import Image

#设置地图投影
PROJ = CRS.from_proj4('+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs')
TRANS = Transformer.from_crs('EPSG:4326', PROJ, always_xy=True)

KEYS5 = ['pm', 'pmheat', 'heat', 'green', 'pmgreen']
MAPS = {
    'a': {'col': 'AMDs Burden', 'title': 'Environmental exposures', 'lim': (-4800, 28000), 'cmap': 'viridis',
          'box': (42, 53, 166, 148), 'sea': (147.51, 124.49, 162.82, 147.42), 'xb': 45.0, 'tx': 45.0},
    'b': {'col': 'AMDs-PM-mean', 'title': r'Attributable to PM$_{2.5}$', 'lim': (0, 12000), 'cmap': 'Purples',
          'box': (173, 53, 297, 148), 'sea': (278.52, 124.70, 293.80, 147.40), 'xb': 177.5, 'tx': 176.3},
    'c': {'col': 'AMDs-EHDs-mean', 'title': 'Attributable to heatwave days', 'lim': (0, 26000), 'cmap': 'Oranges',
          'box': (303.5, 53, 427.5, 148), 'sea': (409.04, 124.79, 424.59, 147.44), 'xb': 306.0, 'tx': 306.6},
    'd': {'col': 'AMDs-GSA-mean', 'title': 'Attributable to greenness', 'lim': (-18000, 0), 'cmap': 'Greens_r',
          'box': (434, 53, 558, 148), 'sea': (539.47, 124.73, 554.89, 147.48), 'xb': 437.0, 'tx': 436.8},
}

ANNOTATIONS = {
    'a': [('北京城区', 'Beijing', 116.4, 39.9, 101.0, 69.5, 'center'), ('南阳市', 'Nanyang', 112.52, 32.99, 46.0, 109.5, 'left'),
          ('广州市', 'Guangzhou', 113.26, 23.14, 47.0, 120.0, 'left'), ('东莞市', 'Dongguan', 113.75, 23.04, 166.0, 109.0, 'right'),
          ('佛山市', 'Foshan', 113.12, 23.02, 145.5, 135.3, 'right')],
    'b': [('北京城区', 'Beijing', 116.4, 39.9, 230.2, 69.0, 'center'), ('南阳市', 'Nanyang', 112.52, 32.99, 177.3, 108.5, 'left'),
          ('广州市', 'Guangzhou', 113.26, 23.14, 177.3, 120.0, 'left'), ('保定市', 'Baoding', 115.46, 38.88, 294.0, 86.3, 'right'),
          ('周口市', 'Zhoukou', 114.65, 33.63, 294.0, 100.0, 'right')],
    'c': [('南阳市', 'Nanyang', 112.52, 32.99, 307.0, 108.5, 'left'), ('广州市', 'Guangzhou', 113.26, 23.14, 307.0, 120.0, 'left'),
          ('周口市', 'Zhoukou', 114.65, 33.63, 425.0, 99.7, 'right'), ('东莞市', 'Dongguan', 113.75, 23.04, 426.0, 112.5, 'right'),
          ('佛山市', 'Foshan', 113.12, 23.02, 356.0, 128.2, 'left')],
    'd': [('商丘市', 'Shangqiu', 115.65, 34.41, 454.3, 54.5, 'left'), ('驻马店市', 'Zhumadian', 114.02, 32.98, 437.0, 83.5, 'left'),
          ('南阳市', 'Nanyang', 112.52, 32.99, 437.0, 101.8, 'left'), ('阜阳市', 'Fuyang', 115.81, 32.89, 437.0, 115.1, 'left'),
          ('周口市', 'Zhoukou', 114.65, 33.63, 555.2, 100.0, 'right')]
}


def fmt(v):
    return f'{int(np.rint(v)):,}'

#排版
class Canvas:
    def __init__(self, fig, bounds, f_reg, f_bold, fig_w=12.16):
        self.fig = fig
        self.x0, self.y0, self.x1, self.y1 = bounds
        self.w, self.h = self.x1 - self.x0, self.y1 - self.y0
        self.scale = fig_w * 72.0 / self.w
        self.f_reg, self.f_bold = f_reg, f_bold

    def fprop(self, size, bold=False):
        return fm.FontProperties(fname=self.f_bold if bold else self.f_reg, size=size * self.scale)

    def pt(self, x, y):
        return (x - self.x0) / self.w, (self.y1 - y) / self.h

    def rect(self, b):
        return [(b[0] - self.x0) / self.w, (self.y1 - b[3]) / self.h, (b[2] - b[0]) / self.w, (b[3] - b[1]) / self.h]

    def axes(self, b, z=3):
        ax = self.fig.add_axes(self.rect(b), zorder=z)
        ax.patch.set_alpha(0)
        ax.axis('off')
        return ax

    def text(self, x, y, s, size=5.5, bold=False, **kw):
        kw.setdefault('ha', 'left')
        kw.setdefault('va', 'top')
        kw.setdefault('zorder', 20)
        kw.setdefault('linespacing', 1.05)
        return self.fig.text(*self.pt(x, y), s, fontproperties=self.fprop(size, bold), **kw)

    def rectangle(self, b, fc='none', ec='none', alpha=None, lw=0.0, z=3):
        r = self.rect(b)
        patch = Rectangle((r[0], r[1]), r[2], r[3], transform=self.fig.transFigure,
                          facecolor=fc, edgecolor=ec, alpha=alpha, linewidth=lw * self.scale, zorder=z)
        self.fig.add_artist(patch)
        return patch

    def border(self, b, lw=0.30, z=30):
        return self.rectangle(b, ec='#424242', lw=lw, z=z)

#数据加载
def load_all(root: Path):
    #字体加载
    f_reg = str(root / 'Arial.ttf' if (root / 'Arial.ttf').is_file() else 'C:/Windows/Fonts/arial.ttf')
    f_bold = str(root / 'arialbd.ttf' if (root / 'arialbd.ttf').is_file() else 'C:/Windows/Fonts/arialbd.ttf')
    fm.fontManager.addfont(f_reg)
    fm.fontManager.addfont(f_bold)
    mpl.rcParams.update({'font.family': 'Arial', 'axes.unicode_minus': False, 'pdf.fonttype': 42})

    spec = json.loads((root / 'data/reference_style.json').read_text(encoding='utf-8'))

    #数据表
    data = {}
    for k in 'abcdgh':
        df = pd.read_csv(root / f'data/fig6{k}.csv', encoding='utf-8-sig', dtype=str)
        if k in 'abcdh':
            df['adcode6'] = df['Postal Code'].str.split('.').str[0].str.zfill(6)
        data[k] = df
    f_df = pd.read_csv(root / 'data/fig6f.csv', header=None, names=['effect', 'val'], encoding='utf-8-sig')
    data['f'] = dict(zip(f_df.effect, f_df.val.astype(float)))

    #边界读取与投影
    m_dir = root / 'data/china_admin_2024'
    city = gpd.read_file(m_dir / 'city.shp').to_crs('EPSG:4326')
    prov = gpd.read_file(m_dir / 'province.shp').to_crs('EPSG:4326')
    sea = gpd.read_file(m_dir / 'south_china_sea_lines.shp').to_crs('EPSG:4326')
    county = gpd.read_file(m_dir / 'county.shp').to_crs('EPSG:4326')

    #重庆拆分与编码对齐
    city['adcode6'] = city['市代码'].astype(str).str.zfill(6)
    city = city[city.adcode6 != '500000']
    cq = county[county['省'] == '重庆市'].copy()
    cq['adcode6'] = cq['县代码'].astype(str).str[:4].map({'5001': '500100', '5002': '500200'})
    city = pd.concat([city, cq.dissolve(by='adcode6', as_index=False)], ignore_index=True)
    city['adcode6'] = city.adcode6.replace({'110000': '110100', '120000': '120100', '310000': '310100'})
    city = city.dissolve(by='adcode6', as_index=False)

    #裁剪大陆主体
    win = geo_box(72, 17.8, 136, 55)
    city_m = city.copy()
    city_m['geometry'] = city_m.geometry.intersection(win)
    prov_m = prov.copy()
    prov_m['geometry'] = prov_m.geometry.intersection(win)

    #投影变换
    proj = lambda g: g.to_crs(PROJ).assign(geometry=lambda x: x.geometry.simplify(1000.0, preserve_topology=True))
    city, prov, sea, city_m, prov_m = map(proj, [city, prov, sea, city_m, prov_m])
    union_m = prov_m.geometry.union_all() if hasattr(prov_m.geometry, "union_all") else prov_m.geometry.unary_union

    return {'root': root, 'spec': spec, 'data': data, 'f_reg': f_reg, 'f_bold': f_bold,
            'city': city, 'prov': prov, 'sea': sea, 'city_m': city_m, 'prov_m': prov_m, 'union_m': union_m}

# 绘图
def fit_bounds(ax, b, pad=0.008, anchor='center'):
    x0, y0, x1, y1 = b
    w, h = (x1 - x0) * (1 + 2 * pad), (y1 - y0) * (1 + 2 * pad)
    pos = ax.get_position(original=True)
    fw, fh = ax.figure.get_size_inches()
    target = (pos.width * fw) / (pos.height * fh)
    if w / h > target:
        extra = w / target - h
        y0, y1 = (y0 - extra, y1) if anchor == 'north' else (y0 - extra / 2, y1 + extra / 2)
    else:
        extra = h * target - w
        x0 -= extra / 2; x1 += extra / 2
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect('equal', adjustable='box')


def draw_sea(cvs, ctx, box):
    ax = cvs.axes(box, z=8)
    ctx['prov'].plot(ax=ax, facecolor='#f8f8f8', edgecolor='#969696', lw=0.12 * cvs.scale)
    ctx['sea'].plot(ax=ax, color='#707070', lw=0.24 * cvs.scale)
    c = np.array([TRANS.transform(lon, lat) for lon in np.linspace(105, 124.5, 25) for lat in [3, 22.5]])
    fit_bounds(ax, (c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max()), 0, anchor='north')
    cvs.border(box, lw=0.46)


def draw_map_cont(cvs, ctx, k):
    cfg = MAPS[k]
    g = ctx['city_m'].merge(ctx['data'][k], on='adcode6')
    g[cfg['col']] = g[cfg['col']].astype(float)

    ax = cvs.axes(cfg['box'], z=5)
    cmap = mpl.colormaps[cfg['cmap']]
    norm = Normalize(*cfg['lim'], clip=True)
    g.plot(ax=ax, column=cfg['col'], cmap=cmap, norm=norm, edgecolor='#9e9e9e', lw=0.10 * cvs.scale,
           missing_kwds={'color': '#ececec', 'edgecolor': '#b0b0b0'})
    ctx['prov_m'].boundary.plot(ax=ax, color='#989898', lw=0.20 * cvs.scale)
    fit_bounds(ax, ctx['prov_m'].total_bounds)

    #色条
    xb = cfg['xb']
    cax = cvs.axes((xb, 137.0, xb + 42, 139.5), z=10)
    cax.axis('on')
    cb = cvs.fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal')
    cb.set_ticks([]); cb.outline.set_visible(False)
    if k == 'd': cax.invert_xaxis()

    l, r = (cfg['lim'][1], cfg['lim'][0]) if k == 'd' else cfg['lim']
    cvs.text(xb, 135.2, fmt(l), size=3.6, va='bottom', ha='center')
    cvs.text(xb + 42, 135.2, fmt(r), size=3.6, va='bottom', ha='center')
    cvs.text(xb, 141.7, cfg['title'], size=4.5)

    draw_sea(cvs, ctx, cfg['sea'])
    cvs.text(cfg['tx'], 53.3, k, size=9.3, bold=True)

    #标注点引线
    srs = ctx['data'][k].set_index('City')[cfg['col']]
    for key, name, lon, lat, tx, ty, align in ANNOTATIONS[k]:
        val = np.rint(float(srs.loc[key]) / 100) * 100
        ax.annotate(f'{name}\n{fmt(abs(val) if k == "d" else val)}', xy=TRANS.transform(lon, lat),
                    xycoords='data', xytext=cvs.pt(tx, ty), textcoords=cvs.fig.transFigure,
                    ha=align, va='top', linespacing=1.0, fontproperties=cvs.fprop(4.5),
                    arrowprops={'arrowstyle': '-', 'color': '#333333', 'lw': 0.30 * cvs.scale,
                                'connectionstyle': 'arc3,rad=0', 'shrinkA': 1.5, 'shrinkB': 0.8}, zorder=20)


def draw_panel_e(cvs, ctx):
    cvs.border(ctx['spec']['frames']['e'])
    cvs.text(53.2, 165.0, 'e', size=9.3, bold=True)
    cvs.text(65.0, 168.0, 'Estimates across seven geographical regions', size=5.4)
    bgs = ['#e1f4fc', '#f2f1fc', '#e8eff1', '#fdf6e3', '#f7f9eb', '#fbf0f1', '#e4f3e6']
    for i, (name, mean, lo, hi) in enumerate(ctx['spec']['regional']):
        y = 176.6 + i * 12.65
        cvs.rectangle((50.7, y, 183.5, y + 12.65), fc=bgs[i], alpha=0.87, z=5)
        cvs.text(54.5, y + 3.3, name)
        cvs.text(182.1, y + 3.3, f'{fmt(mean)} ({fmt(lo)}–{fmt(hi)})', ha='right', size=5.35)


def draw_waterfall(ax, cvs, vals, cols, total, width=0.6, labels=False, total_color='#636363'):
    vals = np.asarray(vals, float)
    cum = np.cumsum(np.r_[0.0, vals])
    for i, v in enumerate(vals):
        ax.add_patch(Rectangle((i - width / 2, min(cum[i], cum[i + 1])), width, abs(v), facecolor=cols[i], ec='none', zorder=4))
        if i < len(vals) - 1:
            ax.plot([i + width / 2, i + 1 - width / 2], [cum[i + 1]] * 2, color='#a4a4a4', lw=0.22 * cvs.scale, zorder=3)
        if labels:
            yy = (max(cum[i], cum[i + 1]) + 18000) if v >= 0 else (min(cum[i], cum[i + 1]) - 18000)
            ax.text(i, yy, fmt(abs(v)), ha='center', va='bottom' if v >= 0 else 'top', fontproperties=cvs.fprop(5.5))
    ax.add_patch(Rectangle((len(vals) - width / 2, min(0, total)), width, abs(total), facecolor=total_color, ec='none', zorder=4))
    if labels:
        ax.text(len(vals), max(total, 0) + 18000, fmt(total), ha='center', va='bottom', fontproperties=cvs.fprop(5.5))
    ax.set_xlim(-0.65, len(vals) + 0.65)
    ax.set_ylim(min(0, cum.min()) * 1.03, max(cum.max(), total) * 1.09)


def draw_panel_f(cvs, ctx):
    f_data = ctx['data']['f']
    ax = cvs.axes(ctx['spec']['frames']['f'], z=5)
    keys = ['PM2.5 direct', 'PM2.5 synergy', 'PM2.5 compromise', 'EHDs direct', 'EHDs synergy', 'GSA direct', 'GSA synergy']
    cols = [ctx['spec']['colors'][k] for k in ['pm', 'pmheat', 'pmgreen', 'heat', 'heatpm', 'green', 'pmgreen']]
    draw_waterfall(ax, cvs, [f_data[k] for k in keys], cols, f_data['Overall'], labels=True, total_color=ctx['spec']['colors']['total'])
    ax.set_ylim(0, 1720000); ax.set_xlim(-0.65, 7.65)

    pos = [(0, 750000, r'Direct effect by PM$_{2.5}$'), (1, 920000, 'PM$_{2.5}$ effect\naggravated by EHDs'),
           (2, 915000, 'PM$_{2.5}$ effect compromised\nby greenness'), (3, 35000, 'Direct effect by EHDs'),
           (4, 620000, 'EHDs effect aggravated by PM$_{2.5}$'), (5, 245000, 'Direct effect by greenness'),
           (6, 1110000, 'Greenness effect\nbuffered by PM$_{2.5}$'), (7, 935000, 'Total effects')]
    for x, y, s in pos:
        ax.text(x, y, s, rotation=90, ha='center', va='bottom', linespacing=1.08, fontproperties=cvs.fprop(5.5))

    cvs.text(299.4, 309.4, 'In total: 817,100\n95% UI: 701,000–929,500', size=5.5)
    cvs.border(ctx['spec']['frames']['f'])
    cvs.text(198.8, 165.0, 'f', size=9.3, bold=True)


def draw_panel_g(cvs, ctx, bg=False, border=False):
    if bg:
        ax = cvs.axes((45.5, 161.0, 551.0, 594.0), z=0)
        gpd.GeoSeries([ctx['union_m']], crs=PROJ).plot(ax=ax, color='#9dc8df', alpha=0.27, ec='none', lw=0)
        fit_bounds(ax, ctx['prov_m'].total_bounds, pad=0)

    for name, st in ctx['spec']['tile_styles'].items():
        r = st['box']
        cvs.rectangle(r, fc=st['fill'], alpha=st['alpha'], z=3)
        ax = cvs.axes(r, z=5); ax.set_xlim(0, 1); ax.set_ylim(0, 1)

        for b in st['bars']:
            xx, yy, ww, hh = b['rect']
            cx = xx + ww / 2
            if hh > 0.00001:
                ax.add_patch(Rectangle((cx - ww / 2, 1 - yy - hh), ww, hh, facecolor=ctx['spec']['colors'][b['effect']], ec='none', zorder=4))
            else:
                ax.plot([cx - ww / 2, cx + ww / 2], [1 - yy] * 2, color=ctx['spec']['colors'][b['effect']], lw=0.18 * cvs.scale)

        bs = st['bars']
        for left, right in zip(bs[:-2], bs[1:-1]):
            x, y, bw, bh = left['rect']; rx, ry, rw, rh = right['rect']
            yy = min(((abs(a - b), a) for a in [y, y + bh] for b in [ry, ry + rh]), key=lambda p: p[0])[1]
            ax.plot([x + bw, rx], [1 - yy] * 2, color='#a8a8a8', lw=0.16 * cvs.scale, zorder=2)

        ui = st['reported_ui']
        title = st['name'] if name != '香港特别行政区' else 'Hong Kong SAR\nMacao SAR'
        ax.text(0.51, 0.925, title, ha='center', va='top', linespacing=1.08, fontproperties=cvs.fprop(5.5))
        if ui is None:
            ax.text(0.50, 0.47, 'NA', ha='center', va='center', fontproperties=cvs.fprop(5.5))
        elif all(np.isfinite(ui)):
            iv = f'{fmt(ui[1])} to {fmt(ui[2])}' if (ui[1] < 0 or (ui[0] == 200 and ui[1] == 0)) else f'{fmt(ui[1])}–{fmt(ui[2])}'
            ax.text(0.050, 0.035, f'{fmt(ui[0])}\n{iv}', rotation=90, ha='left', va='bottom', linespacing=1.03, fontproperties=cvs.fprop(5.5))
        cvs.border(r)

    cvs.text(50.35, 435.0, 'g', size=9.3, bold=True)
    items = [('pm', r'Direct effect by PM$_{2.5}$'), ('pmheat', r'Interactions between PM$_{2.5}$ and EHDs'),
             ('heat', 'Direct effect by EHDs'), ('green', 'Direct effect by greenness'),
             ('pmgreen', r'Interactions between PM$_{2.5}$ and greenness'), ('total', 'Total effects')]
    for i, (k, lbl) in enumerate(items):
        y = 546.3 + i * 8.2
        cvs.rectangle((192.1, y, 200.6, y + 5.2), fc=ctx['spec']['colors'][k], ec='#343434', lw=0.22, z=9)
        cvs.text(204.1, y + 0.1, lbl, size=5.45)
    draw_sea(cvs, ctx, ctx['spec']['frames']['large_inset'])
    if border: cvs.border(ctx['spec']['frames']['lower'], lw=0.30)


def draw_panel_h(cvs, ctx):
    ax = cvs.axes((48.0, 490.0, 184.5, 591.7), z=5)
    g = ctx['city_m'].merge(ctx['data']['h'][['adcode6', 'Priority']], on='adcode6', how='left')
    g['Priority'] = pd.to_numeric(g['Priority'])
    palette = {0: '#ececec', 1: '#9acbe5', 2: '#ffcd47', 3: '#aabd69'}
    for k, c in palette.items():
        g[g.Priority == k].plot(ax=ax, color=c, edgecolor='#555555', lw=0.15 * cvs.scale)
    g[g.Priority.isna()].plot(ax=ax, color='#ececec', edgecolor='#888888', lw=0.14 * cvs.scale)
    ctx['prov_m'].boundary.plot(ax=ax, color='#3d3d3d', lw=0.25 * cvs.scale)
    fit_bounds(ax, ctx['prov_m'].total_bounds, pad=0)

    cvs.text(50.35, 493.0, 'h', size=9.3, bold=True)
    for i, (k, lbl) in enumerate([(0, 'Low-risk areas'), (1, r'PM$_{2.5}$ pollution'), (2, 'Extreme heat'), (3, 'Urban greening')]):
        y = 567.0 + i * 6.0
        cvs.rectangle((49.8, y, 56.7, y + 4.4), fc=palette[k], z=10)
        cvs.text(60.9, y - 0.1, lbl, size=4.4)
    draw_sea(cvs, ctx, (166.84, 564.77, 184.54, 591.32))

#生成图
def create_cvs(ctx, bounds):
    x0, y0, x1, y1 = bounds
    scale = 12.16 * 72.0 / (x1 - x0)
    fig = plt.figure(figsize=((x1 - x0) * scale / 72.0, (y1 - y0) * scale / 72.0), facecolor='none')
    fig.patch.set_alpha(0)
    return Canvas(fig, bounds, ctx['f_reg'], ctx['f_bold'])


def save_cvs(cvs, out, stem, dpi=300):
    p = out / f'{stem}.png'
    cvs.fig.savefig(p, dpi=dpi, transparent=True, facecolor='none', edgecolor='none', pad_inches=0)
    im = Image.open(p).convert('RGBA')
    w = Image.new('RGBA', im.size, (255, 255, 255, 255))
    w.alpha_composite(im)
    w.convert('RGB').save(out / f'{stem}_white_preview.png')
    plt.close(cvs.fig)
    print(f'[Saved] {p}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-dir', default=str(Path(__file__).resolve().parent))
    parser.add_argument('--dpi', type=int, default=300)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()

    root = Path(args.project_dir)
    out = Path(args.out) if args.out else root / 'output'
    out.mkdir(parents=True, exist_ok=True)
    ctx = load_all(root)

    #绘制整张组合图
    cvs = create_cvs(ctx, tuple(ctx['spec']['canvas']))
    ax_bg = cvs.axes((45.5, 161.0, 551.0, 594.0), z=0)
    gpd.GeoSeries([ctx['union_m']], crs=PROJ).plot(ax=ax_bg, color='#9dc8df', alpha=0.27, ec='none', lw=0)
    fit_bounds(ax_bg, ctx['prov_m'].total_bounds, pad=0)

    for k in 'abcd': draw_map_cont(cvs, ctx, k)
    draw_panel_e(cvs, ctx)
    draw_panel_f(cvs, ctx)
    draw_panel_g(cvs, ctx)
    draw_panel_h(cvs, ctx)
    cvs.border(ctx['spec']['frames']['lower'], lw=0.30, z=40)

    save_cvs(cvs, out, 'Fig6_combined', args.dpi)


if __name__ == '__main__':
    main()