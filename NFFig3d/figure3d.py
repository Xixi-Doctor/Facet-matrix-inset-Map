import os
import warnings
import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pyproj
from matplotlib.lines import Line2D
from pyproj import CRS, Transformer
from shapely.geometry import box as geo_box

warnings.filterwarnings("ignore")
os.environ.setdefault("PROJ_LIB", pyproj.datadir.get_data_dir())

# 路径与字体
CSV_PATH = "/data/home/Capybara/work/figpaste/NFFig3d/fig3_data.csv"
FIG3E_PATH = "/data/home/Capybara/work/figpaste/NFFig3d/fig3e.csv"
MAP_PATH = "/data/home/Capybara/work/figpaste/estFig4/china_admin_2024/province.shp"
SEA_PATH = "/data/home/Capybara/work/figpaste/estFig4/china_admin_2024/south_china_sea_lines.shp"
FONT_PATH = "/data/home/Capybara/work/figpaste/estFig4/Arial.ttf"

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    font_prop = fm.FontProperties(fname=FONT_PATH)
    font_bold = fm.FontProperties(fname=FONT_PATH, weight="bold")
    plt.rcParams["font.family"] = font_prop.get_name()
else:
    font_prop = fm.FontProperties(family="sans-serif")
    font_bold = fm.FontProperties(family="sans-serif", weight="bold")

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "custom"
plt.rcParams["mathtext.rm"] = "Arial"
plt.rcParams["mathtext.it"] = "Arial:italic"
plt.rcParams["mathtext.bf"] = "Arial:bold"
plt.rcParams["xtick.direction"] = "out"
plt.rcParams["ytick.direction"] = "out"

PROJECTION = CRS.from_proj4(
    "+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
PROJECT_POINT = Transformer.from_crs("EPSG:4326", PROJECTION, always_xy=True)

# 省级网格与配色
# 省名: 行、列、显示名、底色
GRID_LAYOUT = {
    # r=0
    "Heilongjiang": (0, 6, "Heilongjiang", "#cecad4"),
    # r=1
    "Inner Mongolia": (1, 5, "Inner Mongolia", "#b4bfcd"), "Jilin": (1, 6, "Jilin", "#cecad4"),
    # r=2
    "Beijing": (2, 4, "Beijing", "#b4bfcd"), "Tianjin": (2, 5, "Tianjin", "#b4bfcd"), "Liaoning": (2, 6, "Liaoning", "#cecad4"),
    # r=3
    "Xinjiang": (3, 0, "Xinjiang", "#d9c9b9"), "Gansu": (3, 1, "Gansu", "#d9c9b9"),
    "Hebei": (4, 4, "Hebei", "#b4bfcd"), "Shandong": (4, 5, "Shandong", "#c1cdcf"),
    # r=4
    "Qinghai": (4, 0, "Qinghai", "#d9c9b9"), "Ningxia": (4, 1, "Ningxia", "#d9c9b9"), 
    "Shaanxi": (4, 2, "Shaanxi", "#d9c9b9"), "Shanxi": (4, 3, "Shanxi", "#b4bfcd"),
    # r=5
    "Xizang": (5, 0, "Tibet", "#e1cdce"), "Sichuan": (5, 1, "Sichuan", "#e1cdce"), "Chongqing": (5, 2, "Chongqing", "#e1cdce"),
    "Hubei": (5, 3, "Hubei", "#e1d8be"), "Henan": (5, 4, "Henan", "#e1d8be"), "Jiangsu": (5, 5, "Jiangsu", "#c1cdcf"), "Shanghai": (5, 6, "Shanghai", "#c1cdcf"),
    # r=6
    "Yunnan": (6, 1, "Yunnan", "#e1cdce"), "Guizhou": (6, 2, "Guizhou", "#e1cdce"),
    "Hunan": (6, 3, "Hunan", "#e1d8be"), "Anhui": (6, 4, "Anhui", "#c1cdcf"), "Zhejiang": (6, 5, "Zhejiang", "#c1cdcf"), "Taiwan": (6, 6, "Taiwan", "#e4e4e4"),
    # r=7
    "Guangxi": (7, 2, "Guangxi", "#cce4c9"), "Guangdong": (7, 3, "Guangdong", "#b6cdb3"), "Jiangxi": (7, 4, "Jiangxi", "#c1cdcf"), "Fujian": (7, 5, "Fujian", "#c1cdcf"),
    # r=8
    "Hainan": (8, 3, "Hainan", "#cce4c9"), "Macau": (8, 4, "Macau", "#e4e4e4"), "Hong Kong": (8, 5, "Hong Kong", "#e4e4e4"),
}

# 颜色
COLOR_PDI_AQUA = "#91bd8c"
COLOR_PDI_FISH = "#8ea1be"
COLOR_SAFE_RATE = "#4e696c"
COLOR_SAFE_SHADE = "#b9cbcd"
COLOR_IQ = "#945416"
COLOR_IQ_SHADE = "#f8e5d3"
COLOR_URBAN_INTAKE = "#6ca466"
COLOR_RURAL_INTAKE = "#bf9366"
COLOR_MALE = "#5b769e"
COLOR_FEMALE = "#d08c90"
COLOR_WEDGE_MALE = "#9dadc5"
COLOR_WEDGE_FEMALE = "#deaeb1"
COLOR_LINE_3E = "#679992"
COLOR_BAND_3E = "#eef2f2" 
COLOR_MARKER_3E = "#ffffff" 
COLOR_BG_MAP = "#e2e2e2"

# 数据加载
def load_fig3e_data():
    data = {
        "Residence": ["Urban", "Suburban", "Town", "Rural"],
        "Male_Res": [85.05, 69.17, 39.00, 33.33],
        "Female_Res": [87.07, 77.86, 40.05, 27.80],
        "Age_X": [2, 3, 4, 5, 6, 9, 12, 15, 18, 25, 30, 35, 40, 45, 55, 65, 75, 80],
        "Age_Y": [104.96, 97.05, 79.12, 70.46, 68.54, 59.97, 62.59, 54.39, 46.23, 51.07, 54.34, 51.06, 51.00, 46.33, 51.75, 38.71, 34.05, 27.24],
    }
    csv_path = FIG3E_PATH
    if os.path.exists(csv_path):
        try:
            import pandas as pd
            df = pd.read_csv(csv_path, header=None).fillna("")
            for _, row in df.iterrows():
                row_vals = [str(x).strip() for x in row.values]
                if "Male" in row_vals:
                    idx = row_vals.index("Male")
                    data["Male_Res"] = [float(x) for x in row_vals[idx+1:idx+5]]
                    try:
                        ages = [float(x) for x in row_vals[idx+5:] if x != ""]
                        if len(ages) > 10: data["Age_Y"] = ages
                    except: pass
                if "Female" in row_vals:
                    idx = row_vals.index("Female")
                    data["Female_Res"] = [float(x) for x in row_vals[idx+1:idx+5]]
        except Exception: pass
    return data

def load_clean_data(csv_path):
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    idx_3d, idx_3e = -1, len(raw_lines)
    for i, line in enumerate(raw_lines):
        if "Figure 3d" in line: idx_3d = i
        elif "Figure 3e" in line: idx_3e = i

    years = list(range(1980, 2023))
    data_3d, curr_prov, curr_metric = {}, None, None

    for line in raw_lines[idx_3d + 1 : idx_3e]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4 or (parts[0] == "Province" and "1980" in parts): continue

        val_probe = parts[3]
        is_num = False
        if val_probe != "":
            try:
                float(val_probe)
                is_num = True
            except ValueError:
                if val_probe.lower() == "no data": is_num = True

        if not is_num:
            if parts[0] != "":
                curr_prov = parts[0]
                if curr_prov not in data_3d: data_3d[curr_prov] = {}
            if len(parts) > 1 and parts[1] != "":
                curr_metric = parts[1]
                if curr_metric not in data_3d[curr_prov]: data_3d[curr_prov][curr_metric] = {}
        else:
            sub_key = parts[1]
            vals = []
            for v in parts[3 : 3 + len(years)]:
                try: vals.append(float(v))
                except: vals.append(np.nan)
            if curr_prov and curr_metric:
                data_3d[curr_prov][curr_metric][sub_key] = np.array(vals)

    data_3e = load_fig3e_data()
    return data_3d, years, data_3e

# 单省小图
def draw_province_tile(ax, prov_key, display_name, bg_color, prov_data, years):
    ax.set_facecolor(bg_color)
    ax.patch.set_alpha(0.55)

    for spine in ax.spines.values():
        spine.set_visible(False)

    def add_title_layer():
        box = ax.get_position()
        title_ax = ax.figure.add_axes([box.x0, box.y0, box.width, box.height], zorder=9)
        title_ax.set_facecolor("none")
        title_ax.patch.set_alpha(0.0)
        title_ax.axis("off")
        title_ax.text(0.5, 0.92, display_name, transform=title_ax.transAxes,
                      ha="center", va="top", fontsize=12.5,
                      color="#222222", fontproperties=font_bold)

    has_valid = False
    if prov_data:
        for m in prov_data.values():
            for arr in m.values():
                if len(arr) > 0 and np.nanmax(arr) > 0:
                    has_valid = True
                    break

    if not has_valid:
        add_title_layer()
        ax.set_xticks([]); ax.set_yticks([])
        return

    pdi_aqua = prov_data.get("MeHg PDI decrease (ng kg-1 day-1)", {}).get("From aquaculture", np.zeros(len(years)))
    pdi_fish = prov_data.get("MeHg PDI decrease (ng kg-1 day-1)", {}).get("From fisheries capture", np.zeros(len(years)))

    safe_d = prov_data.get("Increment rate of MeHg-safe population (%)", {})
    safe_avg = safe_d.get("Average", np.zeros(len(years))) / 100.0
    safe_low = safe_d.get("Lower bound", np.zeros(len(years))) / 100.0
    safe_up = safe_d.get("Upper bound", np.zeros(len(years))) / 100.0

    iq_d = prov_data.get("IQ increment (point per fetus)", {})
    iq_avg = iq_d.get("Average", np.zeros(len(years)))
    iq_low = iq_d.get("Lower bound", np.zeros(len(years)))
    iq_up = iq_d.get("Upper bound", np.zeros(len(years)))

    intake_d = prov_data.get("Daily seafood intake (g day-1)", {})
    intake_urb = intake_d.get("Urban", np.zeros(len(years)))
    intake_rur = intake_d.get("Rural", np.zeros(len(years)))

    deaths_d = prov_data.get("Aviod deaths", {})
    male_d = deaths_d.get("Male", np.zeros(len(years)))
    fem_d = deaths_d.get("Female", np.zeros(len(years)))

    ax.set_xlim(1980, 2022)
    ax.set_ylim(0, 0.3)

    ax.fill_between(years, 0, pdi_aqua, color=COLOR_PDI_AQUA, alpha=0.6, linewidth=0, zorder=2)
    ax.fill_between(years, pdi_aqua, pdi_aqua + pdi_fish, color=COLOR_PDI_FISH, alpha=0.6, linewidth=0, zorder=2)
    ax.fill_between(years, safe_low, safe_up, color=COLOR_SAFE_SHADE, alpha=0.75, linewidth=0, zorder=3)
    ax.plot(years, safe_avg, color=COLOR_SAFE_RATE, lw=0.9, zorder=3)
    ax.fill_between(years, iq_low, iq_up, color=COLOR_IQ_SHADE, alpha=0.4, zorder=4)
    ax.plot(years, iq_avg, color=COLOR_IQ, lw=1.15, zorder=4)

    ax_sec = ax.twinx()
    ax_sec.set_ylim(0, 150)
    ax_sec.plot(years, intake_urb, color=COLOR_URBAN_INTAKE, linestyle="--", lw=0.85, alpha=0.85, zorder=5)
    ax_sec.plot(years, intake_rur, color=COLOR_RURAL_INTAKE, linestyle="--", lw=0.85, alpha=0.85, zorder=5)
    ax_sec.set_yticks([])
    for spine in ax_sec.spines.values(): spine.set_visible(False)

    tot_m = np.nansum(male_d)
    tot_f = np.nansum(fem_d)
    tot_deaths = tot_m + tot_f
    if tot_deaths > 10:
        max_r = 0.62
        log_val = np.log10(np.clip(tot_deaths, 50, 50000))
        r = (log_val - np.log10(50)) / (np.log10(50000) - np.log10(50)) * max_r

        box = ax.get_position()
        overlay_size = box.width * max_r
        overlay = ax.figure.add_axes(
            [box.x0 - 0.008, box.y1 - overlay_size, overlay_size, overlay_size], zorder=8
        )
        overlay.set_facecolor("none")
        overlay.patch.set_alpha(0.0)
        overlay.set_xlim(0, 1)
        overlay.set_ylim(0, 1)
        overlay.set_aspect("equal")
        overlay.axis("off")
        r_norm = r / max_r
        overlay.add_patch(patches.Wedge((0, 1), r_norm, 270, 315,
                                        facecolor=COLOR_WEDGE_FEMALE,
                                        alpha=0.95, edgecolor="none"))
        overlay.add_patch(patches.Wedge((0, 1), r_norm, 315, 360,
                                        facecolor=COLOR_WEDGE_MALE,
                                        alpha=0.95, edgecolor="none"))

    ax.set_xticks([]); ax.set_yticks([])
    add_title_layer()

# e 面板
def draw_inset_3e(ax, data_3e):
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#333333")
        spine.set_linewidth(0.8)

    # 柱形
    w = 0.24
    x = np.arange(len(data_3e["Residence"]))

    # 年龄曲线
    ax.bar(x - w / 2, data_3e["Male_Res"], w, label="Male", color=COLOR_MALE, alpha=1.0, edgecolor="none", zorder=3)
    ax.bar(x + w / 2, data_3e["Female_Res"], w, label="Female", color=COLOR_FEMALE, alpha=1.0, edgecolor="none", zorder=3)

    ax.set_ylabel("MeHg PDI decrease (ng kg$^{-1}$ d$^{-1}$)", fontsize=12, fontproperties=font_prop)
    ax.set_xticks(x)
    ax.set_xticklabels(data_3e["Residence"], fontsize=11.5, fontproperties=font_prop)
    ax.tick_params(axis="both", labelsize=11)
    ax.set_ylim(0, 120)
    ax.set_xlim(-0.5, 3.5)

    ax_top = ax.twiny()
    ax_top.set_facecolor("none")
    ax_top.set_zorder(ax.get_zorder() + 2)
    ax_top.patch.set_alpha(0.0)

    age_x = data_3e["Age_X"]
    age_y = data_3e["Age_Y"]

    ax_top.plot(age_x, age_y, color=COLOR_LINE_3E, marker="o", markersize=5.0, lw=1.5,
                markerfacecolor=COLOR_MARKER_3E, markeredgecolor=COLOR_LINE_3E, markeredgewidth=1.0, zorder=5)
    ax_top.fill_between(age_x, np.array(age_y) - 8, np.array(age_y) + 12,
                        color=COLOR_BAND_3E, alpha=0.8, linewidth=0, zorder=4)
    ax_top.set_xlabel("Age", fontsize=12, fontproperties=font_prop)
    ax_top.set_xlim(0, 80)
    ax_top.set_ylim(0, 120)
    ax_top.tick_params(axis="x", labelsize=11)
    ax_top.spines["top"].set_color("#333333")
    ax_top.spines["top"].set_linewidth(0.8)
    for side in ["left", "right", "bottom"]:
        ax_top.spines[side].set_visible(False)

    ax.legend(loc="upper right", frameon=False, prop={'family': font_prop.get_name(), 'size': 10.5}, bbox_to_anchor=(0.98, 0.98))

# 图例
def draw_legends_clean(fig, col_x, row_y, w_tile, h_tile):
    # 指北针
    ax_n = fig.add_axes([0.040, 0.895, 0.050, 0.075], zorder=15)
    ax_n.axis("off"); ax_n.set_xlim(0, 1); ax_n.set_ylim(0, 1)
    ax_n.text(0.5, 0.92, "N", ha="center", va="center", fontsize=12, fontproperties=font_bold)
    ax_n.add_patch(patches.Polygon([[0.5, 0.78], [0.35, 0.14], [0.5, 0.35]], closed=True, facecolor="black", edgecolor="black", linewidth=0.8))
    ax_n.add_patch(patches.Polygon([[0.5, 0.78], [0.5, 0.35], [0.65, 0.14]], closed=True, facecolor="white", edgecolor="black", linewidth=0.8))

    f_size, t_size = 12.5, 13.5
    x0 = col_x[0]

    def fig_label(x, y, text, size=t_size, bold=False, **kwargs):
        fig.text(x, y, text, fontsize=size, fontproperties=font_bold if bold else font_prop,
                 color="#111111", **kwargs)

    def fig_sample(y, color, label, dashed=False, width=0.014, height=0.018):
        x1, x2 = x0 + 0.016, x0 + 0.016 + width
        if dashed:
            fig.add_artist(Line2D([x1, x2], [y, y], transform=fig.transFigure,
                                  color=color, lw=1.6, linestyle="--", zorder=20))
        else:
            fig.add_artist(patches.Rectangle((x1, y - height / 2), width, height,
                                             transform=fig.transFigure, facecolor=color,
                                             edgecolor="none", zorder=20))
        fig_label(x0 + 0.042, y, label, size=f_size, va="center")

    fig_label(x0, 0.384, "IQ increase\n(points per fetus)", bold=True, va="top")
    fig_sample(0.329, COLOR_IQ_SHADE, "In fetuses", width=0.018)
    fig.add_artist(Line2D([x0 + 0.016, x0 + 0.034], [0.329, 0.329], transform=fig.transFigure,
                          color=COLOR_IQ, lw=1.5, zorder=21))

    fig_label(x0, 0.295, "Increase rate of", bold=True, va="top")
    fig_sample(0.258, COLOR_SAFE_SHADE, "MeHg-safe population", width=0.018)
    fig.add_artist(Line2D([x0 + 0.016, x0 + 0.034], [0.258, 0.258], transform=fig.transFigure,
                          color=COLOR_SAFE_RATE, lw=1.5, zorder=21))

    fig_label(x0, 0.222, "MeHg PDI decrease (ng kg$^{-1}$ d$^{-1}$)", bold=True, va="top")
    fig_sample(0.183, COLOR_PDI_FISH, "From fishery capture", width=0.020, height=0.025)
    fig_sample(0.151, COLOR_PDI_AQUA, "From aquaculture", width=0.020, height=0.025)

    fig_label(x0, 0.118, "Daily seafood intake\n(g d$^{-1}$)", bold=True, va="top")
    fig_sample(0.069, COLOR_URBAN_INTAKE, "Urban", dashed=True, width=0.020)
    fig_sample(0.032, COLOR_RURAL_INTAKE, "Rural", dashed=True, width=0.020)

    # 避免死亡
    ax_w = fig.add_axes([0.185, 0.020, 0.14, 0.18], zorder=15)
    ax_w.axis("off"); ax_w.set_xlim(0, 1); ax_w.set_ylim(0, 1)
    ax_w.set_aspect("equal")
    cx, cy, r_max = 0.30, 0.64, 0.30
    r_vals = [0.075, 0.15, 0.225, 0.30]
    labels = ["0", "500", "5,000", "50,000"]

    ax_w.add_patch(patches.Wedge((cx, cy), r_max, 270, 315,
                                 facecolor=COLOR_WEDGE_FEMALE, alpha=0.9,
                                 edgecolor="none", zorder=1))
    ax_w.add_patch(patches.Wedge((cx, cy), r_max, 315, 360,
                                 facecolor=COLOR_WEDGE_MALE, alpha=0.9,
                                 edgecolor="none", zorder=1))
    for rv in r_vals[1:]:
        ax_w.add_patch(patches.Arc((cx, cy), 2*rv, 2*rv, angle=0,
                                   theta1=270, theta2=360, color="white",
                                   linestyle=(0, (3, 2)), linewidth=1.2,
                                   zorder=3))
    axis_x = cx
    tick_y = [cy, cy - r_max / 3, cy - 2 * r_max / 3, cy - r_max]
    ax_w.plot([axis_x, axis_x], [cy - r_max, cy], color="black", lw=1.4)
    for yy in tick_y:
        ax_w.plot([axis_x - 0.025, axis_x], [yy, yy], color="black", lw=1.0)

    ax_w.text(0.05, 0.79, "Avoided deaths", ha="left", va="bottom", fontsize=13.5, fontproperties=font_bold)
    ax_w.text(0.57, 0.58, "Male", fontsize=12.5, va="center", fontproperties=font_prop)
    ax_w.text(0.36, 0.31, "Female", fontsize=12.5, va="center", fontproperties=font_prop)
    for yy, txt in zip(tick_y, labels):
        ax_w.text(axis_x - 0.035, yy, txt, ha="right", va="center", fontsize=11.5, fontproperties=font_prop)

    # 比例尺
    ax_sc = fig.add_axes([0.330, 0.012, 0.095, 0.15], zorder=15)
    ax_sc.axis("off"); ax_sc.set_xlim(0, 1); ax_sc.set_ylim(0, 1)
    ax_sc.add_patch(patches.Rectangle((0.35, 0.30), 0.09, 0.65, facecolor=COLOR_URBAN_INTAKE, edgecolor="none", alpha=0.85))
    ax_sc.add_patch(patches.Rectangle((0.35, 0.30), 0.09, 0.20, facecolor=COLOR_PDI_FISH, edgecolor="none", alpha=0.9))
    ax_sc.plot([0.58, 0.58], [0.30, 0.95], color="black", lw=2.8)
    ax_sc.plot([0.54, 0.62], [0.95, 0.95], color="black", lw=2.8)
    ax_sc.plot([0.54, 0.62], [0.30, 0.30], color="black", lw=2.8)
    ax_sc.text(0.68, 0.63, "Ratio\nor\npoint", va="center", fontsize=12.5, color="#111111", fontproperties=font_prop)
    ax_sc.text(0.25, 0.95, "150", ha="right", va="center", fontsize=12.5, fontproperties=font_prop)
    ax_sc.text(0.25, 0.30, "0", ha="right", va="center", fontsize=12.5, fontproperties=font_prop)
    ax_sc.text(0.64, 0.95, "0.3", ha="left", va="center", fontsize=12.5, fontproperties=font_prop)
    ax_sc.text(0.64, 0.30, "0", ha="left", va="center", fontsize=12.5, fontproperties=font_prop)
    ax_sc.text(0.20, 0.63, "Daily\nintake", va="center", ha="right", fontsize=12.5, color="#111111", fontproperties=font_prop)



# 生成图
def main():
    print("[1/3] 正在加载地理底图与投影...")
    china_map = gpd.read_file(MAP_PATH)
    sea_map = gpd.read_file(SEA_PATH)

    mainland_window = geo_box(72, 15, 136, 55)
    def main_part(gdf):
        m = gdf.copy()
        m["geometry"] = m.geometry.intersection(mainland_window)
        return m.loc[~m.is_empty]

    china_main = main_part(china_map).to_crs(PROJECTION)
    bounds = china_main.total_bounds
    china_full_proj = china_map.to_crs(PROJECTION)
    sea_proj = sea_map.to_crs(PROJECTION)

    print("[2/3] 正在解析数据...")
    data_3d, years, data_3e = load_clean_data(CSV_PATH)
    print(f"[*] 成功获取 {len(data_3d)} 个行政区的时间序列数据！")
    
    fig = plt.figure(figsize=(16, 12.37), facecolor="white", dpi=300)

    # 底图
    ax_map = fig.add_axes([0.02, 0.02, 0.96, 0.96], zorder=0)
    ax_map.set_axis_off()
    china_main.plot(ax=ax_map, color=COLOR_BG_MAP, edgecolor="#ffffff", linewidth=1.0)
    china_main.boundary.plot(ax=ax_map, color="#ffffff", alpha=1.0, linewidth=1.0, zorder=1)
    ax_map.set_xlim(bounds[0] - 120000, bounds[2] + 120000)
    ax_map.set_ylim(bounds[1] - 80000, bounds[3] + 180000)
    ax_map.set_aspect("equal")

    # 省图网格
    w_tile = 0.1175
    h_tile = 0.110
    gap_x = 0.0125
    x_start = 0.0425

    col_x = [x_start + i * (w_tile + gap_x) for i in range(7)]
    row_y = [0.868, 0.757, 0.640, 0.640, 0.524, 0.407, 0.290, 0.173, 0.056]

    for prov_key, (r, c, display_name, bg_color) in GRID_LAYOUT.items():
        x0 = col_x[c]
        y0 = row_y[r]
        ax = fig.add_axes([x0, y0, w_tile, h_tile], zorder=6)
        prov_data = data_3d.get(prov_key, {})
        draw_province_tile(ax, prov_key, display_name, bg_color, prov_data, years)

    # e 面板
    inset_x = col_x[2] + 0.034
    inset_y = 0.686
    inset_w = 0.212
    inset_h = 0.248
    ax_inset = fig.add_axes([inset_x, inset_y, inset_w, inset_h], zorder=10)
    draw_inset_3e(ax_inset, data_3e)

    # 图例
    draw_legends_clean(fig, col_x, row_y, w_tile, h_tile)

    # 南海插图
    scs_x0 = col_x[6] + 0.025
    scs_y0 = 0.094
    ax_scs = fig.add_axes([scs_x0, scs_y0, 0.080, 0.124], zorder=8)
    ax_scs.set_facecolor("white")
    china_full_proj.plot(ax=ax_scs, facecolor="#edf0f3", edgecolor="#444444", linewidth=0.5)
    sea_proj.plot(ax=ax_scs, color="#222222", linewidth=0.8)

    corners = np.array([PROJECT_POINT.transform(lon, lat) for lon in [106, 123] for lat in [2, 23]])
    limits = (corners[:, 0].min(), corners[:, 1].min(), corners[:, 0].max(), corners[:, 1].max())
    ax_scs.set_xlim(limits[0], limits[2])
    ax_scs.set_ylim(limits[1], limits[3])
    ax_scs.set_aspect("equal")
    ax_scs.set_xticks([]); ax_scs.set_yticks([])
    for spine in ax_scs.spines.values():
        spine.set_color("#666666"); spine.set_linewidth(0.8)

    fig.text(col_x[3] + 0.005, 0.040, "1980", fontsize=10, fontproperties=font_prop, ha="left", va="bottom")
    fig.text(col_x[3] + w_tile / 2, 0.028, "Year", fontsize=10, fontproperties=font_prop, ha="center", va="bottom")
    fig.text(col_x[3] + w_tile - 0.005, 0.040, "2022", fontsize=10, fontproperties=font_prop, ha="right", va="bottom")

    out_png = "/data/home/Capybara/work/figpaste/NFFig3d/Figure_3d_final.png"
    plt.savefig(out_png, dpi=300)
    print(f"[3/3] 图像成功生成并保存至: {out_png}")
    plt.close(fig)

if __name__ == "__main__":
    main()
