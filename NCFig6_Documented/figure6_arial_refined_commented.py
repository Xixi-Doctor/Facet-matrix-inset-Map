#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fig. 6 绘图学习版：本地 Arial、Albers、透明底、单层中国底图。

运行示例（Windows）:
    python figure6_arial_refined.py --font "C:/Windows/Fonts/arial.ttf" \
        --font-bold "C:/Windows/Fonts/arialbd.ttf" --dpi 300

本文件包含全部函数，不需要旧版 fig6_core.py。
所需输入全部在同级 data/；程序不联网、不覆盖输入数据。
省级柱形默认按原图矢量相对几何复绘，不把几何坐标当成统计估计。
替换为自己的研究数据时，可用 --province-values 指定可加总的分项表。
"""
# %% 01 — 导入与可修改参数
# 本节只导入绘图和空间数据处理所需的库，并集中设置字体、尺寸、颜色、投影。
# 后续修改版式时，优先修改 Settings 和下面的常量，不要直接改数据处理流程。
from __future__ import annotations
import argparse
import json
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import Normalize, to_rgba
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import box as geo_box
from PIL import Image

# 项目根目录：默认认为本 .py 文件与 data/ 文件夹处于同一层。
PROJECT_ROOT = Path(__file__).resolve().parent
# 按你的文件夹截图，Arial.ttf 放在项目根目录；粗体文件为可选项。
ARIAL_REGULAR = None  # 默认自动查找项目根目录/Arial.ttf；也可通过 --font 显式指定
ARIAL_BOLD = None  # 有 arialbd.ttf 时可改为 str(PROJECT_ROOT / "arialbd.ttf")

@dataclass
class Settings:
    """排版参数集中在这里；坐标使用原图版式参考点，不是经纬度。"""
    figure_width_in: float = 12.16
    dpi: int = 300
    map_simplify_m: float = 1000.0  # 仅显示用简化；不修改原始 SHP
    font_regular: Optional[str] = None
    font_bold: Optional[str] = None
    allow_font_fallback: bool = False  # 仅预览测试使用；正式作图保持 False
    font_scale: float = 1.0
    body_font: float = 5.5
    annotation_font: float = 4.5
    map_legend_font: float = 4.4
    panel_letter_font: float = 9.3
    border_width: float = 0.30
    outer_border_width: float = 0.30
    inset_border_width: float = 0.46
    city_border_width: float = 0.10
    province_border_width: float = 0.20
    legend_key_width: float = 8.5
    legend_key_height: float = 5.2
    legend_row_spacing: float = 8.2
    national_bar_width: float = 0.60
    provincial_bar_width_scale: float = 1.0
    panel_tint_scale: float = 1.0
    background_color: str = '#9dc8df'
    background_alpha: float = 0.27
    # 只有这一层底图：无平移副本、无投影阴影、无重复边界。
    background_box: tuple = (45.5, 161.0, 551.0, 594.0)
    formats: tuple = ('png', 'pdf', 'svg')
    province_values: Optional[str] = None

PROJECTION = CRS.from_proj4(
    '+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 '
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs'
)
# 上面的中央经线、标准纬线来自用户的《中国地图投影》；
# lat_0=0、米制与 WGS84 为代码的显式设置，输入边界 .prj 声明 WGS84。
PROJECT_POINT = Transformer.from_crs('EPSG:4326', PROJECTION, always_xy=True)
FIELDS = {'a': 'AMDs Burden', 'b': 'AMDs-PM-mean',
          'c': 'AMDs-EHDs-mean', 'd': 'AMDs-GSA-mean'}
MAP_NAMES = {'a': 'Environmental exposures', 'b': r'Attributable to PM$_{2.5}$',
             'c': 'Attributable to heatwave days', 'd': 'Attributable to greenness'}
LIMITS = {'a': (-4800, 28000), 'b': (0, 12000), 'c': (0, 26000), 'd': (-18000, 0)}
CMAPS = {'a': 'viridis', 'b': 'Purples', 'c': 'Oranges', 'd': 'Greens_r'}
MAP_BOXES = {'a': (42, 53, 166, 148), 'b': (173, 53, 297, 148),
             'c': (303.5, 53, 427.5, 148), 'd': (434, 53, 558, 148),
             'h': (48, 490, 184.5, 591.7)}
SEA_BOXES = {'a': (147.51,124.49,162.82,147.42), 'b': (278.52,124.70,293.80,147.40),
             'c': (409.04,124.79,424.59,147.44), 'd': (539.47,124.73,554.89,147.48),
             'h': (166.84,564.77,184.54,591.32)}
# (城市中文名, 英文名, 经度, 纬度, 版面文字 x, 版面文字 y, 对齐)
# 注释放置是版面坐标，与实际投影点通过引线连接，不改地理位置。
ANNOTATIONS = {
 'a': [('北京城区','Beijing',116.40,39.90,101.0,69.5,'center'),
       ('南阳市','Nanyang',112.52,32.99,46.0,109.5,'left'),
       ('广州市','Guangzhou',113.26,23.14,47.0,120.0,'left'),
       ('东莞市','Dongguan',113.75,23.04,166.0,109.0,'right'),
       ('佛山市','Foshan',113.12,23.02,145.5,135.3,'right')],
 'b': [('北京城区','Beijing',116.40,39.90,230.2,69.0,'center'),
       ('南阳市','Nanyang',112.52,32.99,177.3,108.5,'left'),
       ('广州市','Guangzhou',113.26,23.14,177.3,120.0,'left'),
       ('保定市','Baoding',115.46,38.88,294.0,86.3,'right'),
       ('周口市','Zhoukou',114.65,33.63,294.0,100.0,'right')],
 'c': [('南阳市','Nanyang',112.52,32.99,307.0,108.5,'left'),
       ('广州市','Guangzhou',113.26,23.14,307.0,120.0,'left'),
       ('周口市','Zhoukou',114.65,33.63,425.0,99.7,'right'),
       ('东莞市','Dongguan',113.75,23.04,426.0,112.5,'right'),
       ('佛山市','Foshan',113.12,23.02,356.0,128.2,'left')],
 'd': [('商丘市','Shangqiu',115.65,34.41,454.3,54.5,'left'),
       ('驻马店市','Zhumadian',114.02,32.98,437.0,83.5,'left'),
       ('南阳市','Nanyang',112.52,32.99,437.0,101.8,'left'),
       ('阜阳市','Fuyang',115.81,32.89,437.0,115.1,'left'),
       ('周口市','Zhoukou',114.65,33.63,555.2,100.0,'right')]
}
KEYS5 = ['pm', 'pmheat', 'heat', 'green', 'pmgreen']

# %% 02 — Arial 字体文件：严格检查，不静默回退
# 字体必须从本地文件注册，避免不同电脑的字体替代导致文字宽度和排版变化。
# load_fonts() 同时检查字体内部名称；文件名叫 Arial.ttf 并不自动证明字体就是 Arial。
@dataclass
class FontSet:
    regular: Path
    bold: Path
    family: str
    is_fallback: bool = False

    def prop(self, size: float, bold: bool = False):
        """prop：执行本函数对应的数据处理或绘图步骤。"""
        return fm.FontProperties(fname=str(self.bold if bold else self.regular), size=size)


def load_fonts(cfg: Settings, root: Path) -> FontSet:
    """直接加载本地 ttf/otf/ttc，正式模式必须为 Arial。字体不复制到输出。"""
    def inspect(path):
        """inspect：执行本函数对应的数据处理或绘图步骤。"""
        path = Path(path).expanduser()
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise FileNotFoundError(f'字体文件不存在：{path}')
        fm.fontManager.addfont(str(path))
        family = fm.FontProperties(fname=str(path)).get_name()
        if 'arial' not in family.lower():
            raise ValueError(f'需要 Arial，所选文件实际字体为 {family}: {path}')
        return path.resolve(), family

    requested = cfg.font_regular or os.environ.get('FIG6_ARIAL_REGULAR')
    if requested:
        regular, family = inspect(requested)
    else:
        candidates = [root/'Arial.ttf', root/'fonts/arial.ttf', Path('C:/Windows/Fonts/arial.ttf'),
                      Path('/Library/Fonts/Arial.ttf'), Path('/System/Library/Fonts/Supplemental/Arial.ttf')]
        found = next((p for p in candidates if p.is_file()), None)
        if found is None:
            try:
                p = Path(fm.findfont(fm.FontProperties(family='Arial'), fallback_to_default=False))
                found = p if 'arial' in fm.FontProperties(fname=str(p)).get_name().lower() else None
            except ValueError:
                found = None
        if found is not None:
            regular, family = inspect(found)
        elif cfg.allow_font_fallback:
            regular = Path(fm.findfont('Liberation Sans', fallback_to_default=False))
            bold = Path(fm.findfont(fm.FontProperties(family='Liberation Sans', weight='bold'), fallback_to_default=False))
            warnings.warn('预览使用 Liberation Sans，不是 Arial。正式运行请指定本地 Arial 文件。')
            return FontSet(regular, bold, 'Liberation Sans', True)
        else:
            raise FileNotFoundError('没有找到 Arial。请通过 --font 指定 arial.ttf，'
                                    '并通过 --font-bold 指定 arialbd.ttf；或把文件放入 fonts/。')
    requested_bold = cfg.font_bold or os.environ.get('FIG6_ARIAL_BOLD')
    if requested_bold:
        bold, _ = inspect(requested_bold)
    else:
        bold = None
        for name in ['arialbd.ttf', 'Arial Bold.ttf', 'Arial-Bold.ttf', 'Arial-BoldMT.ttf']:
            p = regular.parent/name
            if p.is_file():
                bold, _ = inspect(p)
                break
        if bold is None:
            try:
                p = Path(fm.findfont(fm.FontProperties(family=family, weight='bold'), fallback_to_default=False))
                if p != regular and 'arial' in fm.FontProperties(fname=str(p)).get_name().lower():
                    bold, _ = inspect(p)
            except ValueError:
                pass
        if bold is None:
            warnings.warn('未提供 Arial Bold：暂用同一 Arial 常规字体。提供 --font-bold 可恢复加粗子图字母。')
            bold = regular
    return FontSet(regular, bold, family)


def configure_matplotlib(fonts: FontSet):
    """configure_matplotlib：设置全局字体、数学下标字体、透明背景和矢量 PDF/SVG 字体输出。"""
    for p in {fonts.regular, fonts.bold}:
        fm.fontManager.addfont(str(p))
    mpl.rcParams.update({
        'font.family': fonts.family, 'font.sans-serif': [fonts.family],
        'mathtext.fontset': 'custom', 'mathtext.rm': fonts.family,
        'mathtext.it': fonts.family, 'mathtext.bf': f'{fonts.family}:bold',
        'mathtext.sf': fonts.family, 'mathtext.fallback': None,
        'axes.unicode_minus': False, 'pdf.fonttype': 42, 'ps.fonttype': 42,
        'svg.fonttype': 'none', 'svg.hashsalt': 'fig6-Arial-refined',
        'figure.facecolor': 'none', 'axes.facecolor': 'none',
        'savefig.facecolor': 'none', 'savefig.transparent': True,
    })

# %% 03 — 读取数据和投影（不改动原始科学估计）
# 数据读取顺序：城市 CSV → 全国分解 CSV → 行政区划 SHP → 代码匹配 → 几何修复 → 投影。
# 原始 CSV 不会被覆盖；城市空间连接使用六位行政区划代码，不依赖中文名称模糊匹配。
def normalize_code(value):
    """normalize_code：将行政区划代码统一为六位字符串，防止 Excel/CSV 将代码读成数字后丢失前导零。"""
    if pd.isna(value):
        return None
    text = str(value).strip().split('.')[0]
    if not text.isdigit():
        raise ValueError(f'无效行政代码：{value}')
    return text.zfill(6)


def fix_geometries(gdf):
    """fix_geometries：检查并修复行政区划多边形的无效几何；没有 CRS 时停止，避免盲目投影。"""
    if gdf.crs is None:
        raise ValueError('边界文件缺少坐标系，不能猜测 CRS。请保留 .prj 文件。')
    gdf = gdf.copy()
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        gdf.loc[invalid, 'geometry'] = gdf.loc[invalid, 'geometry'].map(make_valid)
    return gdf


@dataclass
class Context:
    root: Path
    cfg: Settings
    fonts: FontSet
    spec: dict
    data: dict
    city: gpd.GeoDataFrame
    province: gpd.GeoDataFrame
    sea: gpd.GeoDataFrame
    city_main: gpd.GeoDataFrame
    province_main: gpd.GeoDataFrame
    mainland_union: object
    user_values: object = None

    @property
    def scale(self):
        """scale：执行本函数对应的数据处理或绘图步骤。"""
        a, _, b, _ = self.spec['canvas']
        return self.cfg.figure_width_in*72/(b-a)

    def fontsize(self, size):
        """fontsize：执行本函数对应的数据处理或绘图步骤。"""
        return size*self.scale*self.cfg.font_scale

    def linewidth(self, width):
        """linewidth：执行本函数对应的数据处理或绘图步骤。"""
        return width*self.scale


def resolve_root(value=None):
    """确定项目根目录。项目根目录下必须有 data/，其中放 CSV 和地图边界。"""
    if value is not None:
        root = Path(value).expanduser().resolve()
    else:
        # .py 运行时以脚本所在目录为准，避免依赖 PowerShell 当前目录。
        root = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()

    # 兼容两种放置方式：data/reference_style.json 或项目根目录/reference_style.json。
    style_candidates = [root/'data/reference_style.json', root/'reference_style.json']
    if not any(p.is_file() for p in style_candidates):
        raise FileNotFoundError(
            f'在 {root} 下没有找到 reference_style.json。\n'
            '请将本项目附带的 reference_style.json 放入 data/ 文件夹，'
            '并确认 data/fig6a.csv 等文件及 data/china_admin_2024/ 地图目录存在。'
        )
    if not (root/'data').is_dir():
        raise FileNotFoundError(f'项目根目录 {root} 下缺少 data/ 文件夹。')
    return root


def load_context(root=None, cfg=None):
    """load_context：读取统计 CSV、地图 Shapefile 和版式 JSON，完成行政代码匹配、重庆拆分及 Albers 投影。"""
    root = resolve_root(root)
    cfg = cfg or Settings(font_regular=ARIAL_REGULAR, font_bold=ARIAL_BOLD)
    fonts = load_fonts(cfg, root)
    configure_matplotlib(fonts)
    style_path = root/'data/reference_style.json'
    if not style_path.is_file():
        style_path = root/'reference_style.json'
    spec = json.loads(style_path.read_text(encoding='utf-8'))
    data = {}
    for k in 'abcdgh':
        df = pd.read_csv(root/f'data/fig6{k}.csv', encoding='utf-8-sig', dtype={'Postal Code': str})
        if k in 'abcdh':
            df['adcode6'] = df['Postal Code'].map(normalize_code)
            if not df['adcode6'].is_unique:
                raise ValueError(f'fig6{k}.csv 的行政代码有重复。')
        data[k] = df
    f = pd.read_csv(root/'data/fig6f.csv', header=None, names=['effect','value'], encoding='utf-8-sig')
    data['f'] = dict(zip(f.effect, f.value.astype(float)))
    maps = root/'data/china_admin_2024'
    def read_map(stem):
        """read_map：执行本函数对应的数据处理或绘图步骤。"""
        p = maps/f'{stem}.shp'
        if not p.is_file():
            raise FileNotFoundError(f'缺少边界文件 {p}')
        return fix_geometries(gpd.read_file(p)).to_crs('EPSG:4326')
    city, prov, counties, sea = [read_map(x) for x in ('city','province','county','south_china_sea_lines')]
    city['adcode6'] = city['市代码'].map(normalize_code)
    # 使用县界恢复原表中的重庆城区/郊县两个单元，不重分配统计值。
    city = city.loc[city.adcode6!='500000'].copy()
    cq = counties.loc[counties['省']=='重庆市'].copy()
    cq['adcode6'] = cq['县代码'].map(normalize_code).str[:4].map({'5001':'500100','5002':'500200'})
    cq = cq.loc[cq.adcode6.notna()].dissolve(by='adcode6', as_index=False)
    city = gpd.GeoDataFrame(pd.concat([city, cq], ignore_index=True), geometry='geometry', crs='EPSG:4326')
    city['adcode6'] = city.adcode6.replace({'110000':'110100','120000':'120100','310000':'310100'})
    if not city.adcode6.is_unique:
        city = city.dissolve(by='adcode6', as_index=False)
    missing = set(data['a'].adcode6)-set(city.adcode6)
    if missing:
        raise ValueError(f'地图未匹配到以下代码：{sorted(missing)}')
    # 南海诸岛保留在附图中；主图视窗不把远海算入主大陆 extent。
    mainland_window = geo_box(72, 17.8, 136, 55)
    def main_part(g):
        """main_part：执行本函数对应的数据处理或绘图步骤。"""
        m = g.copy()
        m['geometry'] = m.geometry.intersection(mainland_window)
        return m.loc[~m.is_empty].copy()
    city_main, prov_main = main_part(city), main_part(prov)
    projected = []
    for g in (city, prov, sea, city_main, prov_main):
        q = g.to_crs(PROJECTION)
        q['geometry'] = q.geometry.simplify(cfg.map_simplify_m, preserve_topology=True)
        projected.append(q)
    city, prov, sea, city_main, prov_main = projected
    union = prov_main.geometry.union_all()
    user_values = None
    if cfg.province_values:
        p = Path(cfg.province_values)
        if not p.is_absolute(): p = root/p
        user_values = pd.read_csv(p).set_index('Province')
        required = KEYS5+['total']
        if not set(required).issubset(user_values.columns):
            raise ValueError(f'省级用户数据需要列：Province,{",".join(required)}')
        arr = user_values[required].to_numpy(dtype=float)
        if not np.isfinite(arr).all() or not np.allclose(arr[:,:5].sum(axis=1), arr[:,5], rtol=1e-6, atol=1e-8):
            raise ValueError('用户数据缺失，或五个增量不等于 total；请先核对，程序不会自动调平。')
    return Context(root, cfg, fonts, spec, data, city, prov, sea, city_main, prov_main, union, user_values)

# %% 04 — 通用布局、文字、框线与导出
# Layout 将参考图的画布坐标映射为 Matplotlib 的 0–1 归一化坐标。
# 所有子图、文字和框线共用同一套坐标映射，因此更改画布尺寸时能保持相对位置。
@dataclass
class Layout:
    ctx: Context
    fig: object
    view: tuple

    def rect(self, b):
        """rect：执行本函数对应的数据处理或绘图步骤。"""
        x0,y0,x1,y1 = b; vx,vy,vxx,vyy = self.view
        return [(x0-vx)/(vxx-vx), (vyy-y1)/(vyy-vy), (x1-x0)/(vxx-vx), (y1-y0)/(vyy-vy)]

    def point(self, x, y):
        """point：执行本函数对应的数据处理或绘图步骤。"""
        vx,vy,vxx,vyy = self.view
        return (x-vx)/(vxx-vx), (vyy-y)/(vyy-vy)

    def axes(self, bounds, zorder=3):
        """axes：执行本函数对应的数据处理或绘图步骤。"""
        ax = self.fig.add_axes(self.rect(bounds), zorder=zorder)
        ax.patch.set_alpha(0)
        ax.set_axis_off()
        return ax

    def text(self, x,y,s,size=None,bold=False,**kwargs):
        """text：执行本函数对应的数据处理或绘图步骤。"""
        c=self.ctx
        kwargs.setdefault('ha','left'); kwargs.setdefault('va','top')
        kwargs.setdefault('zorder',20); kwargs.setdefault('linespacing',1.05)
        return self.fig.text(*self.point(x,y), s,
            fontproperties=c.fonts.prop(c.fontsize(size or c.cfg.body_font),bold), **kwargs)

    def rectangle(self, bounds, facecolor='none', alpha=None, edgecolor='none', width=0, zorder=3):
        """rectangle：执行本函数对应的数据处理或绘图步骤。"""
        r=self.rect(bounds)
        patch=Rectangle((r[0],r[1]),r[2],r[3],transform=self.fig.transFigure,
                        facecolor=facecolor,edgecolor=edgecolor,alpha=alpha,
                        linewidth=self.ctx.linewidth(width),zorder=zorder,clip_on=False)
        self.fig.add_artist(patch)
        return patch

    def border(self, bounds, width=None, zorder=30):
        """border：执行本函数对应的数据处理或绘图步骤。"""
        return self.rectangle(bounds,edgecolor='#424242',width=width or self.ctx.cfg.border_width,zorder=zorder)


def new_layout(ctx, view=None):
    """new_layout：执行本函数对应的数据处理或绘图步骤。"""
    view=tuple(view or ctx.spec['canvas'])
    scale=ctx.scale
    fig=plt.figure(figsize=((view[2]-view[0])*scale/72,(view[3]-view[1])*scale/72),facecolor='none')
    fig.patch.set_alpha(0)
    return Layout(ctx,fig,view)


def axtext(ax,ctx,x,y,s,size=None,bold=False,**kwargs):
    """axtext：执行本函数对应的数据处理或绘图步骤。"""
    return ax.text(x,y,s,fontproperties=ctx.fonts.prop(ctx.fontsize(size or ctx.cfg.body_font),bold),**kwargs)


def fmt(value):
    """fmt：执行本函数对应的数据处理或绘图步骤。"""
    return f'{int(np.rint(value)):,}'


def source_ui(mean, lower, upper):
    """source_ui：执行本函数对应的数据处理或绘图步骤。"""
    if lower < 0 or (mean==200 and lower==0):
        interval=f'{fmt(lower)} to {fmt(upper)}'
    else:
        interval=f'{fmt(lower)}–{fmt(upper)}'
    return f'{fmt(mean)}\n{interval}'


def enforce_font(fig,ctx):
    """包括图例、色条、隐藏刻度在内的 Text 都绑定本地字体文件。"""
    for text in fig.findobj(Text):
        prop=text.get_fontproperties()
        is_bold=(str(prop.get_weight()).lower() in ('bold','heavy','black','700','800','900')
                 or prop.get_file()==str(ctx.fonts.bold))
        text.set_fontproperties(ctx.fonts.prop(prop.get_size_in_points(),is_bold))


def export_layout(layout, out, stem, preview=False, formats=None):
    """export_layout：执行本函数对应的数据处理或绘图步骤。"""
    ctx=layout.ctx;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    enforce_font(layout.fig,ctx)
    formats=formats or ctx.cfg.formats
    paths={}
    for ext in formats:
        p=out/f'{stem}.{ext}'
        layout.fig.savefig(p,dpi=ctx.cfg.dpi,transparent=True,facecolor='none',
                           edgecolor='none',bbox_inches=None,pad_inches=0)
        paths[ext]=str(p)
    if preview and 'png' in paths:
        # 白底只用于阅读预览；正式 PNG 保留 alpha 通道。
        im=Image.open(paths['png']).convert('RGBA')
        white=Image.new('RGBA',im.size,(255,255,255,255))
        white.alpha_composite(im)
        white.convert('RGB').save(out/f'{stem}_white_preview.png')
    plt.close(layout.fig)
    print('[Saved]',stem)
    return paths

# %% 05 — 地图基础函数：主图、南海附图、注释、单层背景
# 本节负责地图几何显示，不重新计算环境负担：城市多边形只与对应城市指标表连接。
# 主图与南海附图分别设置范围；底部阴影使用 dissolve/union 后的单一几何，避免透明重影。

def fit_bounds(ax, bounds, pad=0.008, anchor='center'):
    """先按实际子图宽高比扩展视窗，再固定等比例投影；不触发缩放警告。"""
    x0,y0,x1,y1=bounds;w=x1-x0;h=y1-y0
    x0-=w*pad;x1+=w*pad;y0-=h*pad;y1+=h*pad
    position=ax.get_position(original=True)
    fw,fh=ax.figure.get_size_inches()
    target=(position.width*fw)/(position.height*fh)
    w=x1-x0;h=y1-y0
    if w/h>target:
        extra=w/target-h
        if anchor=='north': y0-=extra
        else: y0-=extra/2;y1+=extra/2
    else:
        extra=h*target-w;x0-=extra/2;x1+=extra/2
    ax.set_xlim(x0,x1);ax.set_ylim(y0,y1)
    ax.set_aspect('equal',adjustable='box')
    ax.set_anchor('C')


def draw_shadow_map(layout):
    """draw_shadow_map：执行本函数对应的数据处理或绘图步骤。"""
    ctx=layout.ctx
    ax=layout.axes(ctx.cfg.background_box,zorder=0)
    # 只画一次 union，避免相邻多边形透明层累积、错位副本和重影。
    gpd.GeoSeries([ctx.mainland_union],crs=PROJECTION).plot(
        ax=ax,color=ctx.cfg.background_color,alpha=ctx.cfg.background_alpha,
        edgecolor='none',linewidth=0)
    fit_bounds(ax,ctx.province_main.total_bounds,pad=0)
    ax.set_axis_off()


def draw_sea_inset(layout,bounds):
    """draw_sea_inset：执行本函数对应的数据处理或绘图步骤。"""
    ctx=layout.ctx;ax=layout.axes(bounds,zorder=8)
    ctx.province.plot(ax=ax,facecolor='#f8f8f8',edgecolor='#969696',linewidth=ctx.linewidth(.12))
    ctx.sea.plot(ax=ax,color='#707070',linewidth=ctx.linewidth(.24))
    # 用投影后的完整四角范围，不错误地仅用一对对角点裁切。
    corners=np.array([PROJECT_POINT.transform(lon,lat) for lon in np.linspace(105,124.5,25)
                      for lat in [3,22.5]])
    limits=(corners[:,0].min(),corners[:,1].min(),corners[:,0].max(),corners[:,1].max())
    fit_bounds(ax,limits,0,anchor='north')
    ax.set_axis_off()
    layout.border(bounds,ctx.cfg.inset_border_width)
    return ax


def draw_city_annotations(layout,ax,k):
    """draw_city_annotations：执行本函数对应的数据处理或绘图步骤。"""
    ctx=layout.ctx;series=ctx.data[k].set_index('City')[FIELDS[k]]
    for key,name,lon,lat,tx,ty,align in ANNOTATIONS[k]:
        if key not in series.index:continue
        value=float(series.loc[key]);value=np.rint(value/100)*100
        if k=='d':value=abs(value)
        # 无不透明白色大框；文字与真实地理点用细折线连接。
        target=PROJECT_POINT.transform(lon,lat)
        point=layout.point(tx,ty)
        ann=ax.annotate(f'{name}\n{fmt(value)}',xy=target,xycoords='data',
                        xytext=point,textcoords=layout.fig.transFigure,
                        ha=align,va='top',linespacing=1.0,
                        fontproperties=ctx.fonts.prop(ctx.fontsize(ctx.cfg.annotation_font)),
                        arrowprops={'arrowstyle':'-','color':'#333333','lw':ctx.linewidth(.30),
                                    'connectionstyle':'arc3,rad=0',
                                    'shrinkA':1.5,'shrinkB':0.8},
                        zorder=20,annotation_clip=False)
        ann.set_clip_on(False)


def draw_continuous_map(layout,k):
    """draw_continuous_map：绘制 a–d 城市级连续变量地图、色带、南海附图和城市注释。"""
    ctx=layout.ctx;field=FIELDS[k]
    g=ctx.city_main.merge(ctx.data[k][['adcode6',field]],on='adcode6',how='left',validate='one_to_one')
    ax=layout.axes(MAP_BOXES[k],zorder=5)
    cmap=mpl.colormaps[CMAPS[k]];norm=Normalize(*LIMITS[k],clip=True)
    g.plot(ax=ax,column=field,cmap=cmap,norm=norm,edgecolor='#9e9e9e',
           linewidth=ctx.linewidth(ctx.cfg.city_border_width),
           missing_kwds={'color':'#ececec','edgecolor':'#b0b0b0'})
    ctx.province_main.boundary.plot(ax=ax,color='#989898',linewidth=ctx.linewidth(ctx.cfg.province_border_width))
    fit_bounds(ax,ctx.province_main.total_bounds)
    ax.set_axis_off()
    xbase={'a':45.0,'b':177.5,'c':306.0,'d':437.0}[k]
    cax=layout.axes((xbase,137.0,xbase+42,139.5),zorder=10)
    cax.set_axis_on()
    cb=layout.fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal')
    cb.set_ticks([]);cb.outline.set_visible(False)
    if k=='d':cax.invert_xaxis()
    left,right=(LIMITS[k][1],LIMITS[k][0]) if k=='d' else LIMITS[k]
    layout.text(xbase,135.2,fmt(left),size=3.6,va='bottom',ha='center')
    layout.text(xbase+42,135.2,fmt(right),size=3.6,va='bottom',ha='center')
    layout.text(xbase,141.7,MAP_NAMES[k],size=4.5)
    draw_sea_inset(layout,SEA_BOXES[k])
    layout.text({'a':45.0,'b':176.3,'c':306.6,'d':436.8}[k],53.3,k,
                size=ctx.cfg.panel_letter_font,bold=True)
    draw_city_annotations(layout,ax,k)
    return ax

# %% 06 — 子图 a（各子图有独立函数，可单独运行）
# a 显示综合环境暴露对应的城市负担；色阶范围来自当前绘图参数 LIMITS。
def draw_panel_a(layout):
    """draw_panel_a：绘制综合环境暴露归因负担地图。"""
    return draw_continuous_map(layout,'a')

# %% 07 — 子图 b
# b 显示 PM2.5 归因负担，使用独立色阶，不与 a/c/d 共用数值范围。

def draw_panel_b(layout):
    """draw_panel_b：绘制 PM2.5 归因负担地图。"""
    return draw_continuous_map(layout,'b')

# %% 08 — 子图 c
# c 显示极端高温日（EHDs）归因负担，地图范围与标注使用统一投影。

def draw_panel_c(layout):
    """draw_panel_c：绘制极端高温日归因负担地图。"""
    return draw_continuous_map(layout,'c')

# %% 09 — 子图 d
# d 显示绿地相关的预防负担；原始值为负值时，显示标注按图件约定取绝对值。

def draw_panel_d(layout):
    """draw_panel_d：绘制绿地相关预防负担地图。"""
    return draw_continuous_map(layout,'d')

# %% 10 — 子图 e：连续对齐表格，字体与省级图一致
# e 的区域估计值和区间来自参考图及补充材料；每一行采用独立浅色底纹以区分区域。

def draw_panel_e(layout):
    """draw_panel_e：绘制七大地理区域统计表。"""
    ctx=layout.ctx;r=ctx.spec['frames']['e'];layout.border(r)
    layout.text(53.2,165.0,'e',size=ctx.cfg.panel_letter_font,bold=True)
    layout.text(65.0,168.0,'Estimates across seven geographical regions',size=5.4)
    bgs=['#e1f4fc','#f2f1fc','#e8eff1','#fdf6e3','#f7f9eb','#fbf0f1','#e4f3e6']
    for i,(name,mean,lo,hi) in enumerate(ctx.spec['regional']):
        y0=176.6+i*12.65
        layout.rectangle((50.7,y0,183.5,y0+12.65),facecolor=bgs[i],alpha=.87,zorder=5)
        layout.text(54.5,y0+3.3,name)
        layout.text(182.1,y0+3.3,f'{fmt(mean)} ({fmt(lo)}–{fmt(hi)})',ha='right',size=5.35)

# %% 11 — 子图 f：七个有符号增量 + 总量，柱宽与细线统一
# 瀑布图先计算累计值，再用矩形表示每个正/负增量；若分项与总量不一致则报错，绝不自动调平。

def draw_waterfall(ax,ctx,values,colors,total=None,width=.60,labels=False):
    """draw_waterfall：按正负增量计算累计高度并绘制瀑布图；分项不等于总量时不自动修正。"""
    vals=np.asarray(values,dtype=float)
    if not np.isfinite(vals).all():raise ValueError('瀑布图数据必须全部为有限数。')
    total=float(vals.sum()) if total is None else float(total)
    if not np.isclose(vals.sum(),total,rtol=1e-6,atol=1e-5):
        raise ValueError(f'瀑布图分项之和 {vals.sum()} 与总量 {total} 不一致，未自动调平。')
    cumulative=np.cumsum(np.r_[0.,vals])
    for i,v in enumerate(vals):
        ax.add_patch(Rectangle((i-width/2,min(cumulative[i],cumulative[i+1])),width,abs(v),
                               facecolor=colors[i],edgecolor='none',zorder=4))
        if i<len(vals)-1:
            ax.plot([i+width/2,i+1-width/2],[cumulative[i+1]]*2,
                    color='#a4a4a4',lw=ctx.linewidth(.22),zorder=3)
        if labels:
            upper=max(cumulative[i],cumulative[i+1]);lower=min(cumulative[i],cumulative[i+1])
            yy=upper+18000 if v>=0 else lower-18000
            axtext(ax,ctx,i,yy,fmt(abs(v)),ha='center',va='bottom' if v>=0 else 'top')
    ax.add_patch(Rectangle((len(vals)-width/2,min(0,total)),width,abs(total),
                           facecolor=ctx.spec['colors']['total'],edgecolor='none',zorder=4))
    if labels:axtext(ax,ctx,len(vals),max(total,0)+18000,fmt(total),ha='center',va='bottom')
    ax.set_xlim(-.65,len(vals)+.65);ax.set_ylim(min(0,cumulative.min())*1.03,max(cumulative.max(),total)*1.09)
    ax.set_axis_off()
    return cumulative


def draw_panel_f(layout):
    """draw_panel_f：绘制全国层面的效应组成瀑布图。"""
    ctx=layout.ctx;f=ctx.data['f'];r=ctx.spec['frames']['f']
    ax=layout.axes(r,zorder=5)
    keys=['PM2.5 direct','PM2.5 synergy','PM2.5 compromise','EHDs direct','EHDs synergy','GSA direct','GSA synergy']
    cols=[ctx.spec['colors'][k] for k in ['pm','pmheat','pmgreen','heat','heatpm','green','pmgreen']]
    draw_waterfall(ax,ctx,[f[k] for k in keys],cols,f['Overall'],width=ctx.cfg.national_bar_width,labels=True)
    ax.set_ylim(0,1720000);ax.set_xlim(-.65,7.65)
    # 每个标签放在它的空白柱段，不再把所有旋转标签堆在基线。
    positions=[(0,750000,r'Direct effect by PM$_{2.5}$','bottom'),
               (1,920000,'PM$_{2.5}$ effect\naggravated by EHDs','bottom'),
               (2,915000,'PM$_{2.5}$ effect compromised\nby greenness','bottom'),
               (3,35000,'Direct effect by EHDs','bottom'),
               (4,620000,'EHDs effect aggravated by PM$_{2.5}$','bottom'),
               (5,245000,'Direct effect by greenness','bottom'),
               (6,1110000,'Greenness effect\nbuffered by PM$_{2.5}$','bottom'),
               (7,935000,'Total effects','bottom')]
    for x,y,s,va in positions:
        axtext(ax,ctx,x,y,s,rotation=90,ha='center',va=va,linespacing=1.08)
    layout.text(299.4,309.4,'In total: 817,100\n95% UI: 701,000–929,500',size=5.5)
    layout.border(r)
    layout.text(198.8,165.0,'f',size=ctx.cfg.panel_letter_font,bold=True)

# %% 12 — 子图 g：原图相对柱形几何 / 用户自己的可加总数据
# 默认省级柱形是从参考图中提取的相对绘图几何，仅用于学习柱宽、顺序、配色和版式。
# 若提供自己的 province_values.csv，则使用真实分项重新绘制，并检查分项之和是否等于 total。

def draw_province_tile(layout,name,style):
    """draw_province_tile：绘制单个省级小面板，包括底色、柱形、区间数字和边框。"""
    ctx=layout.ctx;r=style['box'];x0,y0,x1,y1=r;w=x1-x0;h=y1-y0
    # 必须用显式 Rectangle：transparent=True 不会删除这里的淡彩填充。
    layout.rectangle(r,facecolor=style['fill'],alpha=min(1,style['alpha']*ctx.cfg.panel_tint_scale),zorder=3)
    ax=layout.axes(r,zorder=5);ax.set_xlim(0,1);ax.set_ylim(0,1)
    if ctx.user_values is None:
        for b in style['bars']:
            xx,yy,ww,hh=b['rect'];center=xx+ww/2;ww*=ctx.cfg.provincial_bar_width_scale
            if hh>0.00001:
                ax.add_patch(Rectangle((center-ww/2,1-yy-hh),ww,hh,
                    facecolor=ctx.spec['colors'][b['effect']],edgecolor='none',zorder=4))
            else:
                ax.plot([center-ww/2,center+ww/2],[1-yy]*2,
                        color=ctx.spec['colors'][b['effect']],lw=ctx.linewidth(.18))
        # 连接线只在相邻柱空隙内绘制，绝不覆盖数字。
        bs=style['bars']
        for left,right in zip(bs[:-2],bs[1:-1]):
            x,y,bw,bh=left['rect'];rx,ry,rw,rh=right['rect']
            e1=[y,y+bh];e2=[ry,ry+rh]
            yy=min(((abs(a-b),a) for a in e1 for b in e2),key=lambda p:p[0])[1]
            ax.plot([x+bw,rx],[1-yy]*2,color='#a8a8a8',lw=ctx.linewidth(.16),zorder=2)
        ui=style['reported_ui']
    elif name in ctx.user_values.index:
        row=ctx.user_values.loc[name]
        sub=ax.inset_axes([.28,0,.69,.72]);sub.patch.set_alpha(0)
        draw_waterfall(sub,ctx,row[KEYS5].values,[ctx.spec['colors'][k] for k in KEYS5],row['total'],width=.60)
        ui=[row['total'],row.get('lower',np.nan),row.get('upper',np.nan)]
    else:
        ui=None
    title=style['name'] if name!='香港特别行政区' else 'Hong Kong SAR\nMacao SAR'
    axtext(ax,ctx,.51,.925,title,ha='center',va='top',linespacing=1.08)
    if ui is None:
        axtext(ax,ctx,.50,.47,'NA',ha='center',va='center')
    elif all(np.isfinite(ui)):
        axtext(ax,ctx,.050,.035,source_ui(*ui),rotation=90,ha='left',va='bottom',linespacing=1.03)
    else:
        axtext(ax,ctx,.065,.04,fmt(ui[0]),rotation=90,ha='left',va='bottom')
    layout.border(r)


def draw_effect_legend(layout):
    """draw_effect_legend：执行本函数对应的数据处理或绘图步骤。"""
    ctx=layout.ctx;cfg=ctx.cfg
    items=[('pm',r'Direct effect by PM$_{2.5}$'),
           ('pmheat',r'Interactions between PM$_{2.5}$ and EHDs'),
           ('heat','Direct effect by EHDs'),('green','Direct effect by greenness'),
           ('pmgreen',r'Interactions between PM$_{2.5}$ and greenness'),('total','Total effects')]
    for i,(key,label) in enumerate(items):
        y=546.3+i*cfg.legend_row_spacing
        layout.rectangle((192.1,y,192.1+cfg.legend_key_width,y+cfg.legend_key_height),
                         facecolor=ctx.spec['colors'][key],edgecolor='#343434',width=.22,zorder=9)
        layout.text(204.1,y+.1,label,size=5.45)


def draw_panel_g(layout,background=False,outer_border=False):
    """draw_panel_g：绘制省级小图阵列、底部中国地图背景、图例及南海插图。"""
    ctx=layout.ctx
    if background:draw_shadow_map(layout)
    for name,style in ctx.spec['tile_styles'].items():
        draw_province_tile(layout,name,style)
    layout.text(50.35,435.0,'g',size=ctx.cfg.panel_letter_font,bold=True)
    draw_effect_legend(layout)
    draw_sea_inset(layout,ctx.spec['frames']['large_inset'])
    if outer_border:layout.border(ctx.spec['frames']['lower'],ctx.cfg.outer_border_width)

# %% 13 — 子图 h：无外框，只有南海插图带框
# h 将每个地级市按 Priority 分类着色；缺失类别保持浅灰，不擅自推断其风险类型。

def draw_panel_h(layout):
    """draw_panel_h：绘制各地级市优先治理类别地图及图例。"""
    ctx=layout.ctx;ax=layout.axes(MAP_BOXES['h'],zorder=5)
    g=ctx.city_main.merge(ctx.data['h'][['adcode6','Priority']],on='adcode6',how='left')
    palette={0:'#ececec',1:'#9acbe5',2:'#ffcd47',3:'#aabd69'}
    for key,color in palette.items():
        q=g.loc[g.Priority.eq(key)]
        if len(q):q.plot(ax=ax,color=color,edgecolor='#555555',linewidth=ctx.linewidth(.15))
    missing=g.loc[g.Priority.isna()]
    if len(missing):missing.plot(ax=ax,color='#ececec',edgecolor='#888888',linewidth=ctx.linewidth(.14))
    ctx.province_main.boundary.plot(ax=ax,color='#3d3d3d',linewidth=ctx.linewidth(.25))
    fit_bounds(ax,ctx.province_main.total_bounds,pad=0)
    ax.set_axis_off()
    layout.text(50.35,493.0,'h',size=ctx.cfg.panel_letter_font,bold=True)
    for i,(key,label) in enumerate([(0,'Low-risk areas'),(1,r'PM$_{2.5}$ pollution'),(2,'Extreme heat'),(3,'Urban greening')]):
        y=567+i*6.0
        layout.rectangle((49.8,y,56.7,y+4.4),facecolor=palette[key],zorder=10)
        layout.text(60.9,y-.1,label,size=ctx.cfg.map_legend_font)
    draw_sea_inset(layout,SEA_BOXES['h'])

# %% 14 — 单图导出、整图组合与运行检查
# 最后一节提供单独输出 a–h、生成组合图、写出匹配与透明度检查报告的入口。
PANEL_FUNCTIONS={'a':draw_panel_a,'b':draw_panel_b,'c':draw_panel_c,'d':draw_panel_d,
                 'e':draw_panel_e,'f':draw_panel_f,'g':draw_panel_g,'h':draw_panel_h}


def panel_view(ctx,letter):
    """panel_view：执行本函数对应的数据处理或绘图步骤。"""
    if letter in 'abcd':
        x=MAP_BOXES[letter][0]
        return (x-4,52,x+125,151)
    if letter in 'ef':
        x,y,xx,yy=ctx.spec['frames'][letter]
        return (x-2,y-2,xx+2,yy+2)
    if letter=='g':return (39,155,558,601)
    if letter=='h':return (47,488,186,594)
    raise ValueError('子图只能是 a–h')


def make_panel(ctx,letter,out=None):
    """make_panel：单独生成 a–h 中指定的一张子图，便于局部检查和调整。"""
    layout=new_layout(ctx,panel_view(ctx,letter))
    if letter=='g':draw_panel_g(layout,background=True,outer_border=True)
    else:PANEL_FUNCTIONS[letter](layout)
    return export_layout(layout,out or ctx.root/'output',f'Fig6_{letter}')


def make_combined(ctx,out=None):
    """make_combined：将 a–h 子图按版式坐标组合，输出透明 PNG、PDF 和 SVG。"""
    layout=new_layout(ctx)
    draw_shadow_map(layout)
    for key in 'abcdef':PANEL_FUNCTIONS[key](layout)
    draw_panel_g(layout)
    draw_panel_h(layout)
    # 原图下半部只有一个总框；a–d、h 主地图没有多余外框。
    layout.border(ctx.spec['frames']['lower'],ctx.cfg.outer_border_width,zorder=40)
    return export_layout(layout,out or ctx.root/'output','Fig6_combined',preview=True)


def write_validation(ctx,out):
    """write_validation：输出字体、城市代码匹配、投影、透明度和绘图模式的检查记录。"""
    out=Path(out);out.mkdir(exist_ok=True,parents=True)
    matching=ctx.data['a'][['Province','City','adcode6']].copy()
    matching['matched']=matching.adcode6.isin(ctx.city.adcode6)
    matching.to_csv(out/'city_matching.csv',index=False,encoding='utf-8-sig')
    info={'font_family':ctx.fonts.family,'font_is_fallback':ctx.fonts.is_fallback,
          'font_regular':str(ctx.fonts.regular),'font_bold':str(ctx.fonts.bold),
          'projection':PROJECTION.to_string(),'city_matching':f'{matching.matched.sum()}/{len(matching)}',
          'background_layer_count':1,'province_mode':'user_values' if ctx.user_values is not None else 'source_relative_geometry',
          'province_geometry_note':'Normalized rectangles from the supplied figure, not scientific estimates.',
          'panel_frame_rule':'lower composite + e + f + 33 province tiles + six sea insets; no outer a-d/h frames',
          'source':ctx.spec['source'],'settings':{k:str(v) if isinstance(v,Path) else v for k,v in vars(ctx.cfg).items()}}
    p=out/'Fig6_combined.png'
    if p.is_file():
        im=Image.open(p).convert('RGBA');a=np.asarray(im)[:,:,3]
        info['png_size']=list(im.size);info['png_mode']=im.mode
        info['fully_transparent_pixel_fraction']=float(np.mean(a==0))
        info['partly_transparent_pixel_fraction']=float(np.mean((a>0)&(a<255)))
    (out/'render_validation.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    return info


def main(argv=None):
    """main：解析命令行参数并执行单图或整图绘制流程。"""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-dir',default=None)
    parser.add_argument('--font',default=ARIAL_REGULAR,help='本机 Arial 常规字体完整路径')
    parser.add_argument('--font-bold',default=ARIAL_BOLD,help='本机 Arial Bold 字体完整路径')
    parser.add_argument('--dpi',type=int,default=300)
    parser.add_argument('--out',default=None)
    parser.add_argument('--only',default='all',choices=['all','combined']+list('abcdefgh'))
    parser.add_argument('--formats',default='png,pdf,svg')
    parser.add_argument('--province-values',default=None,help='自己的分项表；不填则复绘原图相对柱形')
    parser.add_argument('--allow-font-fallback',action='store_true',help='仅用于无 Arial 环境的预览；会明确警告')
    args=parser.parse_args(argv)
    formats=tuple(x.strip() for x in args.formats.split(','))
    if not set(formats).issubset({'png','pdf','svg'}):parser.error('formats 仅支持 png,pdf,svg')
    cfg=Settings(font_regular=args.font,font_bold=args.font_bold,dpi=args.dpi,formats=formats,
                 allow_font_fallback=args.allow_font_fallback,province_values=args.province_values)
    ctx=load_context(args.project_dir,cfg)
    out=Path(args.out) if args.out else ctx.root/'output'
    if args.only=='all':
        for k in 'abcdefgh':make_panel(ctx,k,out)
        make_combined(ctx,out)
    elif args.only=='combined':make_combined(ctx,out)
    else:make_panel(ctx,args.only,out)
    info=write_validation(ctx,out)
    print(f"Font: {info['font_family']}; matched cities: {info['city_matching']}")


if __name__=='__main__':
    main()
