# NCFig6：文件路径适配与注释版代码

## 1. 项目目录结构

将本项目放在你的本地目录，例如 `D:\\figpaste\\NCFig6\\`。推荐结构：

```text
NCFig6/
├── figure6_arial_refined_commented.py
├── Figure6_Arial_Commented.ipynb
├── Arial.ttf                         # 你本地已有的 Arial 常规字体
├── arialbd.ttf                       # 可选：Arial Bold
├── reference_style.json              # 版式参数；同时在 data/ 中保留一份
├── requirements.txt
├── data/
│   ├── reference_style.json
│   ├── fig6a.csv
│   ├── fig6b.csv
│   ├── fig6c.csv
│   ├── fig6d.csv
│   ├── fig6e.csv
│   ├── fig6f.csv
│   ├── fig6g.csv
│   ├── fig6h.csv
│   ├── source_supplementary.xlsx
│   └── china_admin_2024/
│       ├── city.shp / city.shx / city.dbf / city.prj
│       ├── province.shp / province.shx / province.dbf / province.prj
│       ├── county.shp / county.shx / county.dbf / county.prj
│       └── south_china_sea_lines.shp / .shx / .dbf / .prj
└── output/
```

**重要：** 你截图中的 `data/` 目录没有显示 `reference_style.json`。这个文件是绘图所需的版式坐标和省级小图几何参数，不是可以省略的文件。本项目已同时提供 `data/reference_style.json` 和项目根目录的 `reference_style.json`。至少保留其中一份。

Shapefile 不是单独的 `.shp` 文件；`.shp`、`.shx`、`.dbf`、`.prj` 等同名文件必须放在同一个文件夹。

## 2. 路径如何设置

### Python 脚本

脚本不再写死服务器路径，例如：

```python
/data/home/Capybara/work/figpaste/NCFig6/Arial.ttf
```

而是以脚本所在文件夹作为项目根目录：

```python
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
MAP_DIR = DATA_DIR / "china_admin_2024"
```

因此整个 `NCFig6` 文件夹移动到 D 盘、E 盘或服务器其他目录后，不需要修改 CSV 和地图的每条路径。

Arial 默认从 `NCFig6/Arial.ttf` 查找。如果字体不在项目根目录，可以运行时指定 `--font`。

### Jupyter Notebook

Notebook 使用：

```python
PROJECT_DIR = Path.cwd().resolve()
```

所以建议在 VS Code 中先打开 `NCFig6` 文件夹，再打开 Notebook。如果 Notebook 的当前工作目录不正确，只需将 `PROJECT_DIR` 改成：

```python
PROJECT_DIR = Path(r"D:\\figpaste\\NCFig6")
```

## 3. 安装依赖

在 VS Code 终端中切换到项目根目录：

```powershell
cd D:\\figpaste\\NCFig6
python -m pip install -r requirements.txt
```

## 4. 运行 Python

生成 a–h 独立子图和组合图：

```powershell
python figure6_arial_refined_commented.py --dpi 300
```

只生成组合图：

```powershell
python figure6_arial_refined_commented.py --only combined --dpi 300
```

只生成某一张图，例如地图 a：

```powershell
python figure6_arial_refined_commented.py --only a --dpi 300
```

指定 Arial 字体文件：

```powershell
python figure6_arial_refined_commented.py --font ".\\Arial.ttf" --dpi 300
```

如果有 Arial Bold：

```powershell
python figure6_arial_refined_commented.py --font ".\\Arial.ttf" --font-bold ".\\arialbd.ttf" --dpi 300
```

## 5. 运行 Notebook

打开 `Figure6_Arial_Commented.ipynb`，按顺序运行全部单元。Notebook 会：
1. 检查项目根目录；
2. 检查 a–h CSV、地图边界和 `reference_style.json`；
3. 检查 Arial 字体；
4. 调用同目录的 Python 脚本；
5. 输出 a–h 独立图和组合图；
6. 写出 `render_validation.json` 和城市代码匹配表。

## 6. 哪些数据被读取

- `fig6a.csv` 至 `fig6d.csv`：城市层面的综合负担、PM2.5、高温和绿地指标。
- `fig6h.csv`：城市优先治理类型。
- `fig6f.csv`：全国瀑布图分项。
- `fig6e.csv`：保留在项目数据目录中；区域表的绘制参数由当前脚本的版式配置提供。
- `fig6g.csv`：原始省级数据保留用于核查；省级小图默认使用 `reference_style.json` 中的相对柱形几何，以便保持原有绘图样式。这些相对几何不是省级科学估计。
- `china_admin_2024/`：市、省、县和南海附图矢量边界。

## 7. 本次修改范围

本次修改仅涉及：
- 将硬编码服务器绝对路径改为项目相对路径；
- 让脚本自动查找项目根目录中的 `Arial.ttf`；
- 支持从项目根目录或 `data/` 读取 `reference_style.json`；
- 增加模块、函数、输入数据、空间匹配、投影、绘图和导出步骤的解释性注释。

没有修改原始 CSV 数值、投影参数、版式数值、色阶、颜色、透明度和绘图函数的计算逻辑。
