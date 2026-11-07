#导入库
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle, Polygon
from pyproj import CRS, Transformer
from shapely.geometry import box as geo_box
import warnings

warnings.filterwarnings("ignore")

#配置路径
NPZ_PATH = 'work/figpaste/estFig4/methane_province_all.npz'
MAP_PATH = 'work/figpaste/estFig4/china_admin_2024/province.shp'
SEA_PATH = 'work/figpaste/estFig4/china_admin_2024/south_china_sea_lines.shp' 
FONT_PATH = 'work/figpaste/estFig4/Arial.ttf'

#配置字体
fm.fontManager.addfont(FONT_PATH)
font_prop = fm.FontProperties(fname=FONT_PATH)
font_bold = fm.FontProperties(fname=FONT_PATH, weight='bold')
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

#Albers 等面积投影地图
PROJECTION = CRS.from_proj4(
    '+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 '
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs'
)
PROJECT_POINT = Transformer.from_crs('EPSG:4326', PROJECTION, always_xy=True)

#读取npz1949-2022年CH4排放分省数据
data = np.load(NPZ_PATH)
years = np.arange(1949, 2023)
sl = slice(0, 74) 

categories = {
    'Rice cultivation': np.nan_to_num(data['methane_rice_cultivation'][:, sl]),
    'Livestock': np.nan_to_num(data['methane_livestock'][:, sl]),
    'Biomass and biofuel burning': np.nan_to_num(data['methane_biomass_biofuel_burning'][:, sl]),
    'Coal exploitation': np.nan_to_num(data['methane_coal'][:, sl]),
    'Oil and natural gas systems': np.nan_to_num(data['methane_oil_gas'][:, sl]),
    'Fossil fuel combustion': np.nan_to_num(data['methane_fossil_consumed'][:, sl]),
    'Landfills': np.nan_to_num(data['methane_landfills'][:, sl]),
    'Wastewater': np.nan_to_num(data['methane_wastewater'][:, sl])
}

colors = {
    'Rice cultivation': '#eaf6d8', 'Livestock': '#7dba53', 
    'Biomass and biofuel burning': '#1b804d', 'Coal exploitation': '#1b5b8e',        
    'Oil and natural gas systems': '#54b4b5', 'Fossil fuel combustion': '#8ec3e0',   
    'Landfills': '#dd6e6e', 'Wastewater': '#f7c6c7'                
}

province_names = [
    'Beijing', 'Tianjin', 'Hebei', 'Shanxi', 'InnerMongolia', 
    'Liaoning', 'Jilin', 'Heilongjiang', 'Shanghai', 'Jiangsu', 
    'Zhejiang', 'Anhui', 'Fujian', 'Jiangxi', 'Shandong', 
    'Henan', 'Hubei', 'Hunan', 'Guangdong', 'Guangxi', 
    'Hainan', 'Chongqing', 'Sichuan', 'Guizhou', 'Yunnan', 
    'Xizang', 'Shaanxi', 'Gansu', 'Qinghai', 'Ningxia', 'Xinjiang'
]
prov_idx_map = {name: i for i, name in enumerate(province_names)}

#分省小图尺寸
w_sq = 0.084
h_sq = 0.085

#分省小图位置
col_x = {
    0:   0.038,
    1:   0.155,
    1.5: 0.214,  # 新疆居中列
    2:   0.273,
    3:   0.392,
    4:   0.511,
    5:   0.630,
    6:   0.749,
    7:   0.866
}

row_y = {
    0: 0.791,
    1: 0.662,
    2: 0.533,
    3: 0.407,
    4: 0.280,
    5: 0.159,
    6: 0.025
}

prov_grid = {
    'Xinjiang': (1.5, 0),
    'Heilongjiang': (5, 0), 'Jilin': (6, 0), 'Liaoning': (7, 0),
    'Gansu': (1, 1), 'InnerMongolia': (2, 1), 'Beijing': (5, 1), 'Tianjin': (6, 1),
    'Xizang': (0, 2), 'Qinghai': (1, 2), 'Ningxia': (2, 2), 
    'Shaanxi': (3, 2), 'Shanxi': (4, 2), 'Hebei': (5, 2), 'Shandong': (6, 2),
    'Sichuan': (1, 3), 'Chongqing': (2, 3), 'Hubei': (3, 3), 
    'Henan': (4, 3), 'Anhui': (5, 3), 'Jiangsu': (6, 3), 'Shanghai': (7, 3),
    'Yunnan': (2, 4), 'Guizhou': (3, 4), 'Hunan': (4, 4), 'Jiangxi': (5, 4), 'Zhejiang': (6, 4),
    'Guangxi': (3, 5), 'Guangdong': (4, 5), 'Fujian': (5, 5),
    'Hainan': (4, 6)
}

layout_pos = {prov: (col_x[c], row_y[r]) for prov, (c, r) in prov_grid.items()}

#地图数据处理
china_map = gpd.read_file(MAP_PATH)
sea_map = gpd.read_file(SEA_PATH)

mainland_window = geo_box(72, 15, 136, 55)
def main_part(gdf):
    m = gdf.copy()
    m['geometry'] = m.geometry.intersection(mainland_window)
    return m.loc[~m.is_empty]

china_main = main_part(china_map).to_crs(PROJECTION)
china_main['geometry'] = china_main.geometry.make_valid()
bounds = china_main.total_bounds

china_full_proj = china_map.to_crs(PROJECTION)
sea_proj = sea_map.to_crs(PROJECTION)

#绘制主图底图与各省子图
fig = plt.figure(figsize=(16, 14), facecolor='white')

#主图底图
ax_map = fig.add_axes([0, 0, 1, 1], zorder=0)
ax_map.set_axis_off()
china_main.plot(ax=ax_map, color='white', edgecolor='black', linewidth=0.8)
sea_proj.plot(ax=ax_map, color='black', linewidth=0.8)

ax_map.set_xlim(bounds[0] - 100000, bounds[2] + 100000)
ax_map.set_ylim(bounds[1] - 100000, bounds[3] + 100000)
ax_map.set_aspect('equal')

#绘制各省子图及遮罩
for prov in province_names:
    idx = prov_idx_map[prov]
    left, bottom = layout_pos[prov]
    
    #白色遮罩层，遮挡底图省界线
    mask_rect = Rectangle((left - 0.026, bottom - 0.003), w_sq + 0.030, h_sq + 0.036, 
                          transform=fig.transFigure, facecolor='white', edgecolor='none', zorder=4)
    fig.add_artist(mask_rect)
    
    ax = fig.add_axes([left, bottom, w_sq, h_sq], facecolor='white', zorder=5)
    
    plot_data = [categories[k][idx] for k in colors.keys()]
    total_emis = np.sum(plot_data, axis=0)
    
    ax.stackplot(years, plot_data, colors=list(colors.values()), alpha=1.0, linewidth=0)
    ax.plot(years, total_emis, color='black', linewidth=1.1)
    
    for yr, color in zip([1980, 2000, 2010], ['#ff9999', 'black', '#4c72b0']):
        ax.axvline(x=yr, color=color, linestyle='--', linewidth=1.0, alpha=0.9)
    
    ax.set_xlim(1949, 2022)
    y_max = total_emis.max()
    ax.set_ylim(0, y_max * 1.05)
    ax.set_xticks([])
    ax.set_yticks([])
    
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_edgecolor('black')
        
    ax.text(-0.08, 0.85, f"{y_max:.1f}", transform=ax.transAxes, 
            fontproperties=font_prop, fontsize=13, ha='right', va='center', zorder=6)
    ax.set_title(prov, fontproperties=font_prop, fontsize=14, pad=4, zorder=6)

#上方时间虚线图例
ax_time = fig.add_axes([0.41, 0.805, 0.11, 0.07], zorder=10)
ax_time.set_axis_off()
ax_time.set_xlim(0, 1) 
ax_time.set_ylim(0, 1)

time_fontsize = 18
line_lw = 2.0

ax_time.plot([0.05, 0.35], [0.82, 0.82], color='#ff9999', linestyle='--', linewidth=line_lw)
ax_time.text(0.45, 0.82, '1980', va='center', ha='left', fontproperties=font_prop, fontsize=time_fontsize)

ax_time.plot([0.05, 0.35], [0.50, 0.50], color='black', linestyle='--', linewidth=line_lw)
ax_time.text(0.45, 0.50, '2000', va='center', ha='left', fontproperties=font_prop, fontsize=time_fontsize)

ax_time.plot([0.05, 0.35], [0.18, 0.18], color='#4c72b0', linestyle='--', linewidth=line_lw)
ax_time.text(0.45, 0.18, '2010', va='center', ha='left', fontproperties=font_prop, fontsize=time_fontsize)

#左下角排放源图例
legend_x, legend_y = 0.048, 0.255
box_size = 0.018 
font_size = 16 
row_spacing = 0.025 

for i, (label, color) in enumerate(colors.items()):
    rect = Rectangle((legend_x, legend_y - i*row_spacing), box_size, box_size * 0.75, 
                     transform=fig.transFigure, facecolor=color, edgecolor='none', zorder=10)
    fig.add_artist(rect)
    fig.text(legend_x + box_size + 0.010, legend_y - i*row_spacing + box_size*0.35, label, 
             fontproperties=font_prop, fontsize=font_size, va='center', zorder=10)

#指南针与比例尺
ax_comp = fig.add_axes([0.070, 0.915, 0.040, 0.065], zorder=10)
ax_comp.set_axis_off()
ax_comp.set_xlim(0, 1)
ax_comp.set_ylim(0, 1)

poly_left = Polygon([[0.5, 0.95], [0.15, 0.15], [0.5, 0.35]], closed=True, 
                    facecolor='#d8d8d8', edgecolor='black', linewidth=1.5)
poly_right = Polygon([[0.5, 0.95], [0.5, 0.35], [0.85, 0.15]], closed=True, 
                     facecolor='white', edgecolor='black', linewidth=1.5)
ax_comp.add_patch(poly_left)
ax_comp.add_patch(poly_right)

ax_sc = fig.add_axes([0.025, 0.865, 0.135, 0.035], zorder=10)
ax_sc.set_axis_off()
ax_sc.set_xlim(0, 1000)
ax_sc.set_ylim(0, 1)

ax_sc.text(0, 0.65, '0', ha='center', va='bottom', fontproperties=font_prop, fontsize=12)
ax_sc.text(500, 0.65, '500', ha='center', va='bottom', fontproperties=font_prop, fontsize=12)
ax_sc.text(1000, 0.65, '1000km', ha='center', va='bottom', fontproperties=font_prop, fontsize=12)

ax_sc.add_patch(Rectangle((0, 0.12), 500, 0.35, facecolor='black', edgecolor='black', linewidth=1.2))
ax_sc.add_patch(Rectangle((500, 0.12), 500, 0.35, facecolor='white', edgecolor='black', linewidth=1.2))

#右下角南海诸岛小图
ax_inset = fig.add_axes([0.82, 0.02, 0.10, 0.16], zorder=5)
ax_inset.set_facecolor('white') 

china_full_proj.plot(ax=ax_inset, facecolor='white', edgecolor='black', linewidth=0.5)
sea_proj.plot(ax=ax_inset, color='black', linewidth=0.8) 

corners = np.array([PROJECT_POINT.transform(lon, lat) for lon in [106, 123] for lat in [2, 23]])
limits = (corners[:,0].min(), corners[:,1].min(), corners[:,0].max(), corners[:,1].max())

ax_inset.set_xlim(limits[0], limits[2])
ax_inset.set_ylim(limits[1], limits[3])
ax_inset.set_aspect('equal') 

ax_inset.set_xticks([])
ax_inset.set_yticks([])
for spine in ax_inset.spines.values():
    spine.set_visible(True)
    spine.set_color('black')
    spine.set_linewidth(1.0)

plt.savefig('work/figpaste/estFig4/methane_map_with_inset.png', dpi=300, bbox_inches='tight')