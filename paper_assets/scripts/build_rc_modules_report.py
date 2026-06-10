#!/usr/bin/env python3
"""Build a Chinese RC modules report deck from existing paper assets.

This script intentionally uses only existing markdown/CSV/PNG assets. It does
not launch training, rerun evaluation, or modify original experiment results.
The PPTX is written directly as PresentationML so it does not require
python-pptx in the environment.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper_assets" / "slides"
PPTX_PATH = OUT_DIR / "RC_Modules_Report.pptx"
PDF_PATH = OUT_DIR / "RC_Modules_Report.pdf"
OUTLINE_PATH = OUT_DIR / "RC_Modules_Report_outline.md"

SLIDE_W = 12192000
SLIDE_H = 6858000
EMU_PER_INCH = 914400

FONT_CN = "Microsoft YaHei"
FONT_EN = "Aptos"
COLOR_TEXT = "1F2937"
COLOR_MUTED = "64748B"
COLOR_LIGHT = "F8FAFC"
COLOR_LINE = "CBD5E1"
COLOR_BLUE = "2563EB"
COLOR_BLUE_DARK = "1E3A8A"
COLOR_GREEN = "059669"
COLOR_RED = "DC2626"
COLOR_AMBER = "D97706"
COLOR_PURPLE = "7C3AED"

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def inch(v: float) -> int:
    return int(round(v * EMU_PER_INCH))


def safe_text(text: str) -> str:
    return escape(str(text), {"\n": "&#10;"})


def para_xml(
    text: str,
    size: int = 18,
    color: str = COLOR_TEXT,
    bold: bool = False,
    align: str = "l",
    font: str = FONT_CN,
) -> str:
    return (
        f'<a:p><a:pPr algn="{align}"/>'
        f'<a:r><a:rPr lang="zh-CN" sz="{size * 100}" b="{1 if bold else 0}">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="{FONT_EN}"/><a:ea typeface="{font}"/><a:cs typeface="{font}"/>'
        f"</a:rPr><a:t>{safe_text(text)}</a:t></a:r></a:p>"
    )


def text_shape(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    w: int,
    h: int,
    paragraphs: Iterable[str],
    size: int = 18,
    color: str = COLOR_TEXT,
    bold: bool = False,
    align: str = "l",
    fill: str | None = None,
    line: str | None = None,
    radius: bool = False,
) -> str:
    prst = "roundRect" if radius else "rect"
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    )
    line_xml = (
        f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        if line
        else "<a:ln><a:noFill/></a:ln>"
    )
    body = "".join(
        para_xml(p, size=size, color=color, bold=bold, align=align) for p in paragraphs
    )
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="{safe_text(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
    <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>
  <p:txBody><a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720"/><a:lstStyle/>{body}</p:txBody>
</p:sp>"""


def rect_shape(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    w: int,
    h: int,
    fill: str = COLOR_LIGHT,
    line: str = COLOR_LINE,
    radius: bool = False,
) -> str:
    prst = "roundRect" if radius else "rect"
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="{safe_text(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
    <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
    <a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>
  </p:spPr>
</p:sp>"""


def line_shape(
    shape_id: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: str = COLOR_BLUE,
    width: int = 19050,
) -> str:
    return f"""
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="line {shape_id}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr><a:xfrm><a:off x="{min(x1, x2)}" y="{min(y1, y2)}"/><a:ext cx="{abs(x2-x1)}" cy="{abs(y2-y1)}"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
      <a:tailEnd type="triangle" w="sm" len="sm"/></a:ln>
  </p:spPr>
</p:cxnSp>"""


def image_shape(
    shape_id: int,
    rel_id: str,
    name: str,
    x: int,
    y: int,
    w: int,
    h: int,
) -> str:
    return f"""
<p:pic>
  <p:nvPicPr><p:cNvPr id="{shape_id}" name="{safe_text(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>"""


def fit_image(path: Path, x: float, y: float, max_w: float, max_h: float) -> tuple[int, int, int, int]:
    im = Image.open(path)
    aspect = im.width / im.height
    box_aspect = max_w / max_h
    if aspect > box_aspect:
        w = max_w
        h = w / aspect
    else:
        h = max_h
        w = h * aspect
    return inch(x + (max_w - w) / 2), inch(y + (max_h - h) / 2), inch(w), inch(h)


@dataclass
class Picture:
    path: Path
    x: int
    y: int
    w: int
    h: int


@dataclass
class Slide:
    title: str
    shapes: list[str]
    pictures: list[Picture]
    source: str
    takeaway: str


def add_title(slide: Slide, title: str, subtitle: str | None = None) -> None:
    slide.shapes.append(text_shape(2, "title", inch(0.55), inch(0.25), inch(12.2), inch(0.55), [title], 25, COLOR_BLUE_DARK, True))
    if subtitle:
        slide.shapes.append(text_shape(3, "subtitle", inch(0.58), inch(0.82), inch(12.0), inch(0.34), [subtitle], 12, COLOR_MUTED))
    slide.shapes.append(rect_shape(4, "rule", inch(0.55), inch(1.12), inch(12.25), inch(0.015), COLOR_BLUE, COLOR_BLUE))


def add_footer(slide: Slide, idx: int, scope: str = "Scope: FD-P2-lite / non-Shiny-Real / completed runs") -> None:
    slide.shapes.append(text_shape(900 + idx, "scope", inch(0.55), inch(7.02), inch(9.6), inch(0.22), [scope], 8, COLOR_MUTED))
    slide.shapes.append(text_shape(950 + idx, "page", inch(12.15), inch(7.02), inch(0.7), inch(0.22), [f"{idx:02d}"], 8, COLOR_MUTED, align="r"))


def label_box(slide: Slide, sid: int, x: float, y: float, w: float, h: float, header: str, body: str, color: str = COLOR_BLUE) -> None:
    slide.shapes.append(rect_shape(sid, header, inch(x), inch(y), inch(w), inch(h), "FFFFFF", COLOR_LINE, True))
    slide.shapes.append(text_shape(sid + 100, header + " head", inch(x + 0.08), inch(y + 0.06), inch(w - 0.16), inch(0.25), [header], 12, color, True))
    wrapped = textwrap.wrap(body, width=26)
    slide.shapes.append(text_shape(sid + 200, header + " body", inch(x + 0.08), inch(y + 0.38), inch(w - 0.16), inch(h - 0.42), wrapped, 10, COLOR_TEXT))


def read_required_texts() -> None:
    required = [
        "paper_draft/rc_modules_intro_method_zh.md",
        "paper_assets/rc_results_summary_zh.md",
        "paper_assets/experiment_data_audit.md",
        "paper_assets/experiment_claim_boundary.md",
        "paper_assets/diagnostics/refl_metrics_degradation_analysis_zh.md",
        "paper_assets/diagnostics/diagnostic_missing_fields.md",
    ]
    for rel in required:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(f"Required source missing: {rel}")
        path.read_text(encoding="utf-8")


def metric_value(df: pd.DataFrame, dataset: str, split: str, method: str, metric: str) -> float | None:
    rows = df[
        (df["dataset"] == dataset)
        & (df["split"] == split)
        & (df["method"] == method)
        & (df["metric"] == metric)
    ]
    if rows.empty:
        return None
    return float(rows.iloc[0]["mean_value"])


def fmt_metric(metric: str, value: float | None) -> str:
    if value is None:
        return "--"
    if metric == "mean_reflection_consistency":
        return f"{value:.4f}"
    if "ssim" in metric or "lpips" in metric:
        return f"{value:.3f}"
    return f"{value:.2f}"


def build_avg_table_shapes(slide: Slide, df: pd.DataFrame) -> None:
    datasets = ["glossy_synthetic", "shiny_blender_synthetic"]
    splits = ["train", "test"]
    metrics = [
        ("mean_reflection_consistency", "RC↓"),
        ("full_psnr", "PSNR↑"),
        ("full_ssim", "SSIM↑"),
        ("full_lpips", "LPIPS↓"),
    ]
    x0, y0 = 0.65, 1.45
    col_ws = [2.2, 0.9] + [1.0] * 8
    row_h = 0.36
    headers = ["Dataset", "Split"] + [f"{name}\nBase" if i % 2 == 0 else f"{name}\nRC" for name in [m[1] for m in metrics] for i in range(2)]
    xs = [x0]
    for w in col_ws[:-1]:
        xs.append(xs[-1] + w)
    total_w = sum(col_ws)
    slide.shapes.append(rect_shape(20, "table bg", inch(x0), inch(y0), inch(total_w), inch(row_h * 6), "FFFFFF", COLOR_LINE))
    for j, h in enumerate(headers):
        slide.shapes.append(rect_shape(30 + j, f"th {j}", inch(xs[j]), inch(y0), inch(col_ws[j]), inch(row_h), "EAF2FF", COLOR_LINE))
        slide.shapes.append(text_shape(60 + j, f"th text {j}", inch(xs[j]), inch(y0 + 0.02), inch(col_ws[j]), inch(row_h - 0.02), h.split("\n"), 8, COLOR_BLUE_DARK, True, "c"))
    row = 1
    for dataset in datasets:
        for split in splits:
            vals = [dataset.replace("_", "\n"), split]
            for metric, _ in metrics:
                vals.append(fmt_metric(metric, metric_value(df, dataset, split, "base", metric)))
                vals.append(fmt_metric(metric, metric_value(df, dataset, split, "rc", metric)))
            for j, val in enumerate(vals):
                fill = "FFFFFF" if row % 2 else "F8FAFC"
                slide.shapes.append(rect_shape(100 + row * 20 + j, f"td {row}-{j}", inch(xs[j]), inch(y0 + row * row_h), inch(col_ws[j]), inch(row_h), fill, COLOR_LINE))
                color = COLOR_TEXT
                bold = False
                if j >= 2:
                    metric_idx = (j - 2) // 2
                    is_rc_col = (j - 2) % 2 == 1
                    metric = metrics[metric_idx][0]
                    base = metric_value(df, dataset, split, "base", metric)
                    rc = metric_value(df, dataset, split, "rc", metric)
                    if base is not None and rc is not None:
                        rc_better = rc < base if metric in {"mean_reflection_consistency", "full_lpips"} else rc > base
                        if is_rc_col and rc_better:
                            color, bold = COLOR_GREEN, True
                        if (not is_rc_col) and (not rc_better):
                            color, bold = COLOR_AMBER, True
                slide.shapes.append(text_shape(300 + row * 20 + j, f"td text {row}-{j}", inch(xs[j]), inch(y0 + row * row_h + 0.03), inch(col_ws[j]), inch(row_h - 0.05), [val], 8, color, bold, "c"))
            row += 1
    slide.shapes.append(text_shape(850, "table note", inch(0.75), inch(3.78), inch(11.6), inch(0.36), ["Avg. 在同一 dataset + split 内计算；缺失值不参与平均。绿色仅标记该行方向下更优。"], 9, COLOR_MUTED))


def build_deck() -> list[Slide]:
    read_required_texts()
    main_avg = pd.read_csv(ROOT / "paper_assets/data/main_full_metrics_by_dataset_avg.csv")

    slides: list[Slide] = []

    # 1 Title
    s = Slide("Title", [], [], "整理自论文草稿、实验表格与诊断报告", "RC 更适合作为反射一致性正则与诊断模块。")
    s.shapes.append(text_shape(2, "cover title", inch(0.72), inch(1.15), inch(11.8), inch(1.15), ["RC 模块组：跨视角反射一致性优化的", "阶段性结果与问题诊断"], 31, COLOR_BLUE_DARK, True))
    s.shapes.append(text_shape(3, "cover subtitle", inch(0.76), inch(2.55), inch(10.8), inch(0.45), ["From Reflection Consistency to Geometry-aware Reconstruction"], 18, COLOR_MUTED))
    s.shapes.append(rect_shape(4, "cover line", inch(0.76), inch(3.23), inch(5.6), inch(0.04), COLOR_BLUE, COLOR_BLUE))
    s.shapes.append(text_shape(5, "cover scope", inch(0.78), inch(5.63), inch(10.4), inch(0.62), ["数据范围：FD-P2-lite / non-Shiny-Real / completed runs", "汇报定位：研究进展、实验结果、问题诊断与下一步方向"], 13, COLOR_TEXT))
    s.shapes.append(text_shape(6, "cover date", inch(0.78), inch(6.5), inch(4.0), inch(0.25), ["2026-06-05"], 10, COLOR_MUTED))
    slides.append(s)

    # 2 Motivation
    s = Slide("Motivation", [], [], "论文 Introduction", "普通 RGB loss 容易把高光当成单视角颜色拟合。")
    add_title(s, "高反射场景的核心难点不是“亮”，而是 view-dependent ambiguity")
    bullets = [
        "镜面反射、折射与近场照明导致外观随视角强烈变化",
        "多视角 RGB loss 可以拟合像素，但不自动约束反射几何对应",
        "高光可能被吸收到颜色、方向查询、alpha 或局部特征中",
        "目标：让反射预测在几何一致区域中更稳定，而非追求单一指标最优",
    ]
    s.shapes.append(text_shape(10, "mot bullets", inch(0.78), inch(1.45), inch(6.05), inch(2.45), [f"• {b}" for b in bullets], 15, COLOR_TEXT))
    label_box(s, 20, 7.15, 1.4, 2.25, 1.15, "传统拟合路径", "view-dependent color query 解释单视角高光", COLOR_AMBER)
    label_box(s, 30, 9.85, 1.4, 2.35, 1.15, "本文关注路径", "跨视角几何对应约束 specular stability", COLOR_BLUE)
    s.shapes.append(line_shape(80, inch(9.42), inch(1.98), inch(9.78), inch(1.98), COLOR_MUTED))
    s.shapes.append(text_shape(90, "bottom", inch(0.8), inch(5.45), inch(11.7), inch(0.55), ["关键判断：reflection consistency 是反射结构的内部约束，不等价于 full RGB 或 mesh quality。"], 16, COLOR_BLUE_DARK, True, "c", fill="EEF6FF", line="BFDBFE", radius=True))
    add_footer(s, 2)
    slides.append(s)

    # 3 Core idea
    s = Slide("Core idea", [], [], "论文 Method: Renderer-Buffer Interface", "RC 只依赖 renderer intermediate buffers，而不是特定 Gaussian 参数化。")
    add_title(s, "RC 模块组把反射约束下沉到 renderer-buffer 层")
    label_box(s, 10, 0.75, 1.55, 3.35, 1.45, "1. Renderer buffers", "RGB / specular / confidence / alpha / depth / normal", COLOR_BLUE)
    label_box(s, 20, 4.95, 1.55, 3.35, 1.45, "2. Cross-view correspondence", "source depth 反投影 → target 投影 → 可微采样", COLOR_PURPLE)
    label_box(s, 30, 9.15, 1.55, 3.15, 1.45, "3. Weighted RC loss", "alpha、depth、normal、confidence 共同调制", COLOR_GREEN)
    s.shapes.append(line_shape(80, inch(4.18), inch(2.25), inch(4.82), inch(2.25)))
    s.shapes.append(line_shape(81, inch(8.38), inch(2.25), inch(9.02), inch(2.25)))
    s.shapes.append(text_shape(90, "claim", inch(0.95), inch(4.2), inch(11.1), inch(0.92), ["核心贡献不是 Ref-GS 的实现细节，而是可插拔反射一致性优化框架。", "原则上，只要 renderer 提供语义等价 buffers，就可以接入 RC 模块组。"], 17, COLOR_BLUE_DARK, True, "c"))
    add_footer(s, 3)
    slides.append(s)

    # 4 Method overview
    s = Slide("Method overview", [], [], "论文 Method: Cross-view Reflective Correspondence", "RC 的流程是 render buffers、几何投影、可微采样和加权 specular consistency。")
    add_title(s, "Method overview：从 source depth 到 target specular consistency")
    steps = [
        ("Source render", "得到 S_s, A_s, D_s, N_s, C_s"),
        ("Back-project", "D_s(u)K_s^{-1}\\bar{u}"),
        ("Target project", "v(u)=π(K_tT_t x_s)"),
        ("Sample target", "双线性采样 S_t, A_t, D_t, N_t"),
        ("Weighted loss", "w(u)||sg(S_s)-S_t(v)||_1"),
    ]
    x = 0.55
    for i, (head, body) in enumerate(steps):
        label_box(s, 20 + i * 10, x + i * 2.55, 2.05 if i % 2 == 0 else 3.2, 2.05, 1.05, head, body, [COLOR_BLUE, COLOR_PURPLE, COLOR_BLUE, COLOR_PURPLE, COLOR_GREEN][i])
        if i < len(steps) - 1:
            s.shapes.append(line_shape(150 + i, inch(x + i * 2.55 + 2.12), inch(2.62 if i % 2 == 0 else 3.75), inch(x + (i + 1) * 2.55 - 0.1), inch(2.62 if i % 2 == 0 else 3.75), COLOR_MUTED))
    s.shapes.append(text_shape(210, "caution", inch(0.8), inch(5.25), inch(11.6), inch(0.7), ["注意：这里约束的是“可见、几何一致、置信度高的相邻视角对应区域”的反射预测稳定性，", "不是假设真实 specular radiance 跨视角严格相等。"], 14, COLOR_TEXT, False, "c", fill="FFF7ED", line="FED7AA", radius=True))
    add_footer(s, 4)
    slides.append(s)

    # 5 Buffer interface
    s = Slide("Buffer interface", [], [], "论文 Method: Renderer-Buffer Interface", "可迁移性来自最小 buffer contract。")
    add_title(s, "Buffer Interface：可迁移性来自最小 contract")
    buffers = [
        ("RGB", "最终渲染颜色，用于常规重建项"),
        ("specular", "view-dependent reflection 分量"),
        ("confidence", "反射/材质置信度，不强制解释为物理粗糙度"),
        ("alpha", "可见性与投影有效性过滤"),
        ("depth", "source 反投影与 target depth consistency"),
        ("normal_render / normal_depth", "法线一致性权重"),
    ]
    y = 1.35
    for i, (name, desc) in enumerate(buffers):
        fill = "F8FAFC" if i % 2 == 0 else "FFFFFF"
        s.shapes.append(rect_shape(20 + i, f"buf row {i}", inch(0.8), inch(y + i * 0.63), inch(11.7), inch(0.52), fill, COLOR_LINE))
        s.shapes.append(text_shape(60 + i, f"buf name {i}", inch(1.0), inch(y + i * 0.63 + 0.08), inch(2.4), inch(0.28), [name], 12, COLOR_BLUE_DARK, True))
        s.shapes.append(text_shape(90 + i, f"buf desc {i}", inch(3.65), inch(y + i * 0.63 + 0.08), inch(8.5), inch(0.28), [desc], 12, COLOR_TEXT))
    s.shapes.append(text_shape(200, "migration", inch(0.85), inch(5.55), inch(11.4), inch(0.65), ["原则上可接入：3DGS / 2DGS / GaussianShader / 3DGS-DR / NeRF-like reflective reconstruction。", "必要条件是提供语义等价的 image-space buffers，而非采用特定 Sph-Mip、light MLP 或 PBR 分支。"], 12, COLOR_MUTED, False, "c"))
    add_footer(s, 5)
    slides.append(s)

    # 6 Main finding
    s = Slide("Main finding", [], [], "paper_assets/figures/fig1_rc_win_count_by_metric.png", "RC 的最稳定收益集中在 reflection consistency。")
    add_title(s, "主实验发现：RC 的稳定收益集中在 reflection consistency")
    img = ROOT / "paper_assets/figures/fig1_rc_win_count_by_metric.png"
    s.pictures.append(Picture(img, *fit_image(img, 0.55, 1.25, 8.45, 5.25)))
    label_box(s, 20, 9.25, 1.35, 3.35, 1.05, "Consistency", "train 14/14 wins; test 13/14 wins", COLOR_GREEN)
    label_box(s, 30, 9.25, 2.75, 3.35, 1.15, "RGB metrics", "full-image 与 reflective-region 指标呈 mixed behavior", COLOR_AMBER)
    label_box(s, 40, 9.25, 4.25, 3.35, 1.05, "安全结论", "RC 是 consistency regularizer，不是通用质量提升插件", COLOR_BLUE)
    add_footer(s, 6)
    slides.append(s)

    # 7 Full metrics compact table
    s = Slide("Full metrics", [], [], "paper_assets/data/main_full_metrics_by_dataset_avg.csv", "per-dataset full metric table 支持逐指标讨论，而非整体胜利叙事。")
    add_title(s, "Full metric table：平均值支持“逐指标报告”")
    build_avg_table_shapes(s, main_avg)
    s.shapes.append(text_shape(875, "interpretation", inch(0.85), inch(4.55), inch(11.4), inch(0.85), ["观察：RC↓ 在两个 dataset 的 train/test Avg. 均下降；PSNR/SSIM/LPIPS 的变化幅度和方向更依赖数据集与 split。", "因此主表应作为 per-dataset / per-scene 数值对照，而不是“全面优于 baseline”的证据。"], 13, COLOR_TEXT, False, "c", fill="F8FAFC", line="E2E8F0", radius=True))
    add_footer(s, 7)
    slides.append(s)

    # 8 Reflective-region problem
    s = Slide("Reflective-region problem", [], [], "paper_assets/diagnostics/figD1_refl_metric_improvements_by_scene.png", "Refl. PSNR/SSIM/LPIPS 没有稳定提升。")
    add_title(s, "Reflective-region quality problem：Refl. metrics 有正有负")
    img = ROOT / "paper_assets/diagnostics/figD1_refl_metric_improvements_by_scene.png"
    s.pictures.append(Picture(img, *fit_image(img, 0.45, 1.2, 9.0, 5.7)))
    s.shapes.append(text_shape(20, "stats", inch(9.7), inch(1.45), inch(3.0), inch(2.15), ["Refl. PSNR：16 win / 12 loss", "Refl. SSIM：14 win / 14 loss", "Refl. LPIPS：10 win / 18 loss", "正值表示 RC 更好"], 14, COLOR_TEXT, False, "l", fill="FFFFFF", line=COLOR_LINE, radius=True))
    s.shapes.append(text_shape(21, "take", inch(9.7), inch(4.05), inch(3.0), inch(1.15), ["结论：反射区域 RGB 指标并未随 consistency 稳定提升。"], 15, COLOR_AMBER, True, "c", fill="FFF7ED", line="FED7AA", radius=True))
    add_footer(s, 8)
    slides.append(s)

    # 9 Trade-off
    s = Slide("Trade-off", [], [], "paper_assets/diagnostics/figD2_consistency_vs_refl_quality_tradeoff.png", "Consistency improvement 不能推出 Refl. image-quality improvement。")
    add_title(s, "Trade-off：consistency improvement 与 Refl. quality 基本解耦")
    img = ROOT / "paper_assets/diagnostics/figD2_consistency_vs_refl_quality_tradeoff.png"
    s.pictures.append(Picture(img, *fit_image(img, 0.45, 1.18, 12.2, 4.0)))
    s.shapes.append(text_shape(20, "corr", inch(0.8), inch(5.45), inch(11.6), inch(0.72), ["Pearson r：Refl. PSNR 0.01，Refl. SSIM 0.04，Refl. LPIPS 0.10；Spearman 同样接近 0。", "存在多行 “consistency 改善，但 reflective image quality 下降” 的 trade-off。"], 13, COLOR_TEXT, False, "c", fill="F8FAFC", line="E2E8F0", radius=True))
    add_footer(s, 9)
    slides.append(s)

    # 10 Ablation
    s = Slide("Ablation", [], [], "paper_assets/diagnostics/figD3_ablation_refl_metrics_heatmap.png", "消融显示 confidence 和 RC loss 的作用边界。")
    add_title(s, "消融诊断：RC consistency 最强，但 Refl. metrics 不是最优")
    img = ROOT / "paper_assets/diagnostics/figD3_ablation_refl_metrics_heatmap.png"
    s.pictures.append(Picture(img, *fit_image(img, 0.55, 1.25, 8.8, 4.35)))
    bullets = [
        "wo_ref 牺牲 consistency，但若干 Refl. metrics 可持平或更好",
        "wo_conf 削弱 consistency，说明 confidence 有贡献但非充分条件",
        "rough_only 不能复现 RC 的 reflection consistency 行为",
        "消融支持模块边界，不支持“所有指标全面提升”",
    ]
    s.shapes.append(text_shape(30, "abl bullets", inch(9.65), inch(1.35), inch(2.9), inch(3.1), [f"• {b}" for b in bullets], 11, COLOR_TEXT, False, "l", fill="FFFFFF", line=COLOR_LINE, radius=True))
    add_footer(s, 10)
    slides.append(s)

    # 11 Why worse
    s = Slide("Why worse", [], [], "paper_assets/diagnostics/refl_metrics_degradation_analysis_zh.md", "Refl. metrics 下降更像 objective trade-off，而不是已证实的单点 bug。")
    add_title(s, "为什么 Refl. PSNR/SSIM/LPIPS 反而更差？")
    label_box(s, 20, 0.75, 1.35, 3.8, 1.25, "有代码与指标共同支持", "objective mismatch：specular stability 正则 vs masked final-RGB 指标", COLOR_GREEN)
    label_box(s, 30, 4.8, 1.35, 3.8, 1.25, "部分支持", "L1 specular consistency 可能抑制 view-specific 高频高光", COLOR_AMBER)
    label_box(s, 40, 8.85, 1.35, 3.55, 1.25, "机制支持但未量化", "RC mask 与 Refl. metric mask 不完全一致", COLOR_PURPLE)
    label_box(s, 50, 0.75, 3.25, 3.8, 1.25, "仍待验证", "错误 correspondence：depth / normal / alpha 不稳定", COLOR_MUTED)
    label_box(s, 60, 4.8, 3.25, 3.8, 1.25, "仍待验证", "小反射 mask 导致 PSNR/SSIM/LPIPS 高方差", COLOR_MUTED)
    label_box(s, 70, 8.85, 3.25, 3.55, 1.25, "结论边界", "这是 trade-off 信号，不是 RC 一定失败或实现一定有 bug", COLOR_BLUE)
    s.shapes.append(text_shape(90, "safe wording", inch(0.9), inch(5.55), inch(11.2), inch(0.45), ["论文讨论应写：RC 更适合作为 reflection consistency regularizer，而非保证 reflective RGB 全面提升的插件。"], 14, COLOR_BLUE_DARK, True, "c"))
    add_footer(s, 11)
    slides.append(s)

    # 12 Mesh limitation
    s = Slide("Mesh limitation", [], [], "paper_assets/experiment_claim_boundary.md", "缺少独立几何指标，因此不能主张 mesh quality 改善。")
    add_title(s, "Hard limitation：reflection consistency 不是 mesh quality 证据")
    s.shapes.append(text_shape(20, "big", inch(0.9), inch(1.55), inch(11.4), inch(1.1), ["如果最终目标是 mesh / surface quality，", "仅提升 reflection consistency 还不够。"], 27, COLOR_BLUE_DARK, True, "c"))
    bullets = [
        "当前结果包没有 Chamfer / F-score / normal MAE 等独立几何指标",
        "confidence-aware geometry filtering 只能作为工程增强模块讨论",
        "reflection consistency 更像内部诊断指标，而不是最终表面质量指标",
        "下一步必须证明 RC inconsistency 与 mesh artifact 有空间对应关系",
    ]
    s.shapes.append(text_shape(30, "mesh bullets", inch(1.35), inch(3.25), inch(10.6), inch(1.75), [f"• {b}" for b in bullets], 15, COLOR_TEXT, False, "l", fill="FFFFFF", line=COLOR_LINE, radius=True))
    s.shapes.append(text_shape(40, "warning", inch(1.1), inch(5.55), inch(11.0), inch(0.6), ["Unsafe claim：RC 必然提升 mesh quality。Safe claim：mesh quality 需要独立评估。"], 15, COLOR_RED, True, "c", fill="FEF2F2", line="FECACA", radius=True))
    add_footer(s, 12)
    slides.append(s)

    # 13 Future direction
    s = Slide("Future direction", [], [], "诊断报告后续改进建议", "下一阶段应从 consistency-only 转向 geometry-aware / mesh-aware RC。")
    add_title(s, "Future direction：从 consistency-only 到 geometry-aware RC")
    label_box(s, 20, 0.85, 1.55, 3.55, 2.1, "A. RC as diagnostic regularizer", "保留 reflection consistency 指标，作为高反射区域稳定性诊断与轻量正则。", COLOR_BLUE)
    label_box(s, 30, 4.85, 1.55, 3.55, 2.1, "B. Geometry-aware RC", "联合约束 specular、depth、normal、alpha，并引入 view-angle-aware weighting。", COLOR_GREEN)
    label_box(s, 40, 8.85, 1.55, 3.55, 2.1, "C. Mesh-aware RC filtering", "将 RC inconsistency 转化为 TSDF / mesh fusion confidence，而不是直接声称质量提升。", COLOR_PURPLE)
    s.shapes.append(text_shape(50, "future bottom", inch(0.95), inch(5.25), inch(11.0), inch(0.7), ["策略转向：让 RC 解释并筛除反射导致的几何不可靠区域，而不是单独优化反射 RGB 指标。"], 16, COLOR_BLUE_DARK, True, "c"))
    add_footer(s, 13)
    slides.append(s)

    # 14 Next experiments
    s = Slide("Next experiments", [], [], "paper_assets/diagnostics/diagnostic_missing_fields.md", "下一步需要补轻量诊断与几何指标。")
    add_title(s, "Next experiments：补齐从 RC 到 geometry 的证据链")
    left = [
        "Chamfer / F-score / normal MAE",
        "RC mask 与 mesh artifact overlap",
        "valid correspondence ratio",
        "depth pass rate / normal agreement",
        "pair angle distribution",
    ]
    right = [
        "mean RC weight / weight sum",
        "specular confidence distribution",
        "reflective mask area ratio",
        "specular variance / highlight sharpness",
        "lambda_RC / schedule sweep",
    ]
    s.shapes.append(text_shape(20, "left", inch(0.95), inch(1.55), inch(5.6), inch(3.1), [f"• {b}" for b in left], 15, COLOR_TEXT, False, "l", fill="FFFFFF", line=COLOR_LINE, radius=True))
    s.shapes.append(text_shape(30, "right", inch(6.85), inch(1.55), inch(5.45), inch(3.1), [f"• {b}" for b in right], 15, COLOR_TEXT, False, "l", fill="FFFFFF", line=COLOR_LINE, radius=True))
    s.shapes.append(text_shape(40, "next claim", inch(1.05), inch(5.35), inch(11.0), inch(0.7), ["这些诊断可以回答：RC 改善的是反射稳定性，还是确实减少了几何伪影？"], 17, COLOR_BLUE_DARK, True, "c", fill="EEF6FF", line="BFDBFE", radius=True))
    add_footer(s, 14)
    slides.append(s)

    # 15 Conclusion
    s = Slide("Conclusion", [], [], "汇总自结果摘要、claim boundary 与诊断报告", "论文主张应降级为反射一致性正则，并转向几何感知验证。")
    add_title(s, "Conclusion：RC 有价值，但主张必须降级并转向几何验证")
    conclusions = [
        ("已支持", "RC 在完成范围内稳定改善 cross-view reflection consistency", COLOR_GREEN),
        ("未支持", "Refl. PSNR / SSIM / LPIPS 和 mesh quality 的稳定提升", COLOR_RED),
        ("当前定位", "reflection consistency regularizer / diagnostic module", COLOR_BLUE),
        ("下一阶段", "geometry-aware RC 与 mesh-aware RC filtering", COLOR_PURPLE),
    ]
    for i, (head, body, color) in enumerate(conclusions):
        label_box(s, 20 + i * 10, 1.0, 1.35 + i * 1.05, 11.2, 0.78, head, body, color)
    s.shapes.append(text_shape(90, "end", inch(1.05), inch(6.25), inch(11.1), inch(0.42), ["一句话总结：RC 证明了反射一致性可以被显式优化，但还没有证明它能稳定转化为 RGB 或 mesh 质量。"], 15, COLOR_BLUE_DARK, True, "c"))
    add_footer(s, 15)
    slides.append(s)

    return slides


def slide_xml(slide: Slide, slide_idx: int, rels: list[tuple[str, str]]) -> str:
    pic_xml = []
    for pic_idx, pic in enumerate(slide.pictures, start=1):
        rel_id = f"rId{pic_idx + 1}"
        rels.append((rel_id, f"../media/{pic.path.name}"))
        pic_xml.append(image_shape(1000 + pic_idx, rel_id, pic.path.name, pic.x, pic.y, pic.w, pic.h))
    sp_tree = "\n".join(slide.shapes + pic_xml)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm></p:grpSpPr>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="9998" name="background"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>
      </p:sp>
      {sp_tree}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def rels_xml(items: Iterable[tuple[str, str, str]]) -> str:
    rels = "\n".join(
        f'<Relationship Id="{rid}" Type="{rtype}" Target="{target}"/>'
        for rid, rtype, target in items
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}
</Relationships>"""


def content_types_xml(slide_count: int) -> str:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
    ]
    for i in range(1, slide_count + 1):
        overrides.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  {''.join(overrides)}
</Types>"""


def presentation_xml(slide_count: int) -> str:
    sld_ids = "\n".join(f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>' for i in range(1, slide_count + 1))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}" saveSubsetFonts="1">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{sld_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle><a:defPPr><a:defRPr lang="zh-CN"/></a:defPPr></p:defaultTextStyle>
</p:presentation>"""


def presentation_rels(slide_count: int) -> str:
    items = [("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml")]
    for i in range(1, slide_count + 1):
        items.append((f"rId{i+1}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", f"slides/slide{i}.xml"))
    items.append((f"rId{slide_count+2}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "theme/theme1.xml"))
    return rels_xml(items)


def slide_master_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def slide_layout_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def theme_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{NS['a']}" name="RCModules">
  <a:themeElements>
    <a:clrScheme name="RCModules"><a:dk1><a:srgbClr val="111827"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="{COLOR_BLUE}"/></a:accent1><a:accent2><a:srgbClr val="{COLOR_GREEN}"/></a:accent2><a:accent3><a:srgbClr val="{COLOR_AMBER}"/></a:accent3><a:accent4><a:srgbClr val="{COLOR_PURPLE}"/></a:accent4><a:accent5><a:srgbClr val="{COLOR_RED}"/></a:accent5><a:accent6><a:srgbClr val="{COLOR_MUTED}"/></a:accent6><a:hlink><a:srgbClr val="{COLOR_BLUE}"/></a:hlink><a:folHlink><a:srgbClr val="{COLOR_PURPLE}"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="RCFonts"><a:majorFont><a:latin typeface="{FONT_EN}"/><a:ea typeface="{FONT_CN}"/><a:cs typeface="{FONT_CN}"/></a:majorFont><a:minorFont><a:latin typeface="{FONT_EN}"/><a:ea typeface="{FONT_CN}"/><a:cs typeface="{FONT_CN}"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="RCFmt"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>"""


def write_pptx(slides: list[Slide]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if PPTX_PATH.exists():
        PPTX_PATH.unlink()
    media_paths: dict[str, Path] = {}
    with zipfile.ZipFile(PPTX_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(slides)))
        zf.writestr("_rels/.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml")]))
        zf.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        zf.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        zf.writestr("ppt/theme/theme1.xml", theme_xml())
        zf.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml")]))
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml")]))
        for idx, slide in enumerate(slides, start=1):
            rels: list[tuple[str, str]] = []
            zf.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(slide, idx, rels))
            slide_rels = [("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml")]
            slide_rels += [(rid, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", target) for rid, target in rels]
            zf.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", rels_xml(slide_rels))
            for _, target in rels:
                fname = Path(target).name
                # Retrieve by file name from slide pictures.
                for pic in slide.pictures:
                    if pic.path.name == fname:
                        media_paths[fname] = pic.path
        for fname, path in media_paths.items():
            zf.write(path, f"ppt/media/{fname}")


def write_outline(slides: list[Slide]) -> None:
    lines = [
        "# RC Modules Report Outline",
        "",
        "Deck: `paper_assets/slides/RC_Modules_Report.pptx`",
        "",
        "Scope: FD-P2-lite / non-Shiny-Real / completed runs. No training or new evaluation is performed.",
        "",
    ]
    for idx, slide in enumerate(slides, start=1):
        lines.extend(
            [
                f"## Slide {idx}: {slide.title}",
                f"- Takeaway: {slide.takeaway}",
                f"- Source: {slide.source}",
                "",
            ]
        )
    lines.extend(
        [
            "## Evidence Boundary",
            "- Supported: RC mainly improves cross-view reflection consistency within the completed FD-P2-lite / non-Shiny-Real scope.",
            "- Mixed: full-image and reflective-region PSNR/SSIM/LPIPS.",
            "- Unsupported: universal quality improvement, full reflective dataset validation, or mesh-quality improvement.",
            "- Missing diagnostics: mask coverage, RC valid correspondence ratio, depth/normal pass rate, pair-angle distribution, highlight sharpness, and mesh metrics.",
            "",
        ]
    )
    OUTLINE_PATH.write_text("\n".join(lines), encoding="utf-8")


def convert_pdf() -> bool:
    exe = shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:
        write_pdf_preview(build_deck(), "LibreOffice unavailable; generated a static PDF preview from slide geometry.")
        return PDF_PATH.exists()
    cmd = [exe, "--headless", "--convert-to", "pdf", "--outdir", str(OUT_DIR), str(PPTX_PATH)]
    result = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (OUT_DIR / "RC_Modules_Report_pdf_export.log").write_text(result.stdout, encoding="utf-8")
    if result.returncode == 0 and PDF_PATH.exists():
        return True
    write_pdf_preview(build_deck(), "LibreOffice export failed; generated a static PDF preview from slide geometry.\n" + result.stdout)
    return PDF_PATH.exists()


def _emu_to_in(v: int) -> float:
    return v / EMU_PER_INCH


def _find_text_font() -> str | None:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def _parse_shape_xml(shape_xml: str):
    root = ET.fromstring(
        f'<root xmlns:a="{NS["a"]}" xmlns:r="{NS["r"]}" xmlns:p="{NS["p"]}">{shape_xml}</root>'
    )
    sp = root.find("p:sp", NS)
    if sp is None:
        return None
    off = sp.find(".//a:off", NS)
    ext = sp.find(".//a:ext", NS)
    if off is None or ext is None:
        return None
    x = _emu_to_in(int(off.attrib.get("x", 0)))
    y = _emu_to_in(int(off.attrib.get("y", 0)))
    w = _emu_to_in(int(ext.attrib.get("cx", 0)))
    h = _emu_to_in(int(ext.attrib.get("cy", 0)))
    fills = sp.findall(".//a:solidFill/a:srgbClr", NS)
    fill = fills[0].attrib["val"] if fills else None
    line = fills[1].attrib["val"] if len(fills) > 1 else None
    paras = []
    tx = sp.find("p:txBody", NS)
    if tx is not None:
        for p in tx.findall("a:p", NS):
            text = "".join(t.text or "" for t in p.findall(".//a:t", NS))
            if text:
                ppr = p.find("a:pPr", NS)
                align = ppr.attrib.get("algn", "l") if ppr is not None else "l"
                rpr = p.find(".//a:rPr", NS)
                size = int(rpr.attrib.get("sz", "1200")) / 100 if rpr is not None else 12
                bold = rpr.attrib.get("b") == "1" if rpr is not None else False
                color_node = p.find(".//a:rPr/a:solidFill/a:srgbClr", NS)
                color = color_node.attrib["val"] if color_node is not None else COLOR_TEXT
                paras.append((text, align, size, bold, color))
    return {"x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "paras": paras}


def write_pdf_preview(slides: list[Slide], note: str) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(OUT_DIR / ".mplconfig"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle

    font_path = _find_text_font()
    fp = FontProperties(fname=font_path) if font_path else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF_PATH) as pdf:
        for slide in slides:
            fig = plt.figure(figsize=(13.333, 7.5), dpi=160)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_xlim(0, 13.333)
            ax.set_ylim(7.5, 0)
            ax.axis("off")
            ax.add_patch(Rectangle((0, 0), 13.333, 7.5, facecolor="white", edgecolor="none"))
            for shape_xml_str in slide.shapes:
                try:
                    shape = _parse_shape_xml(shape_xml_str)
                except ET.ParseError:
                    shape = None
                if not shape:
                    continue
                fill = shape["fill"]
                line = shape["line"]
                # Text-only noFill shapes should not draw a background rectangle.
                if fill and fill != "FFFFFF" or line:
                    ax.add_patch(
                        Rectangle(
                            (shape["x"], shape["y"]),
                            shape["w"],
                            shape["h"],
                            facecolor=f"#{fill}" if fill else "none",
                            edgecolor=f"#{line}" if line else "none",
                            linewidth=0.7,
                        )
                    )
                if shape["paras"]:
                    yy = shape["y"] + 0.12
                    for text, align, size, bold, color in shape["paras"]:
                        ha = {"c": "center", "r": "right"}.get(align, "left")
                        tx = shape["x"] + (shape["w"] / 2 if ha == "center" else shape["w"] - 0.08 if ha == "right" else 0.08)
                        # Existing line breaks are already encoded as separate paragraphs.
                        ax.text(
                            tx,
                            yy,
                            text,
                            ha=ha,
                            va="top",
                            fontsize=max(size * 0.7, 5),
                            fontproperties=fp,
                            fontweight="bold" if bold else "normal",
                            color=f"#{color}",
                            wrap=True,
                        )
                        yy += max(0.18, size * 0.030)
            for pic in slide.pictures:
                im = Image.open(pic.path).convert("RGBA")
                x, y, w, h = map(_emu_to_in, [pic.x, pic.y, pic.w, pic.h])
                ax.imshow(im, extent=[x, x + w, y + h, y])
            pdf.savefig(fig, bbox_inches="tight", pad_inches=0)
            plt.close(fig)
    (OUT_DIR / "RC_Modules_Report_pdf_export.log").write_text(note, encoding="utf-8")


def main() -> None:
    slides = build_deck()
    write_pptx(slides)
    write_outline(slides)
    pdf_ok = convert_pdf()
    status = {
        "pptx": PPTX_PATH.exists(),
        "pdf": pdf_ok,
        "outline": OUTLINE_PATH.exists(),
        "slide_count": len(slides),
    }
    with (OUT_DIR / "RC_Modules_Report_build_status.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        for k, v in status.items():
            writer.writerow([k, v])
    if not pdf_ok:
        raise RuntimeError(f"PDF export failed; see {OUT_DIR / 'RC_Modules_Report_pdf_export.log'}")


if __name__ == "__main__":
    main()
