"""
性能测试报告 - 图表生成服务

生成专业性能测试报告所需的各类图表（统一格式，参照京通报告）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import io
import os
from typing import List, Dict, Any, Optional

def _find_chinese_font():
    for f in fm.fontManager.ttflist:
        if 'SimHei' in f.name or 'Microsoft YaHei' in f.name or 'Noto Sans CJK' in f.name:
            return f.name
    return 'SimHei'

_CHINESE_FONT = _find_chinese_font()
plt.rcParams['font.sans-serif'] = [_CHINESE_FONT, 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ========== 统一配色 ==========
CLR_TARGET = '#93C5FD'      # 目标值 浅蓝
CLR_ACTUAL = '#6EE7B7'      # 实际值 浅绿
CLR_AVG = '#FCD34D'          # 平均 浅黄
CLR_P50 = '#93C5FD'          # P50 浅蓝
CLR_P90 = '#FDBA74'          # P90 浅橙
CLR_P95 = '#FCA5A5'          # P95 浅红
CLR_P99 = '#C084FC'          # P99 浅紫
CLR_STDDEV = '#86EFAC'       # 标准差 薄荷绿
CLR_LINE_AVG = '#F59E0B'     # 平均线 橙
CLR_LINE_P95 = '#EF4444'     # P95线 红
CLR_EDGE_TARGET = '#3B82F6'
CLR_EDGE_ACTUAL = '#10B981'
CLR_EDGE_DEFAULT = '#374151'
CLR_PASS = '#10B981'
CLR_WARN = '#F59E0B'
CLR_FAIL = '#EF4444'

# ========== 统一图表风格 ==========
CHART_STYLE = {
    'figsize': (10, 5),
    'dpi': 120,
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'annotate_size': 8,
}

def _apply_style(ax, title: str, xlabel: str, ylabel: str):
    """统一应用图表样式"""
    ax.set_title(title, fontsize=CHART_STYLE['title_size'], fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, fontsize=CHART_STYLE['label_size'])
    ax.set_ylabel(ylabel, fontsize=CHART_STYLE['label_size'])
    ax.tick_params(labelsize=CHART_STYLE['tick_size'])
    ax.grid(axis='y', alpha=0.25, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ========== 图1: 吞吐量对比 ==========
def generate_tps_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [d["name"][:15] for d in scenarios_data]
    target = [d.get("target_qps", 0) for d in scenarios_data]
    actual = [d.get("actual_qps", 0) for d in scenarios_data]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    bars1 = ax.bar(x - width/2, target, width, label='目标 TPS', color=CLR_TARGET, edgecolor=CLR_EDGE_TARGET, linewidth=0.8)
    bars2 = ax.bar(x + width/2, actual, width, label='实际 TPS', color=CLR_ACTUAL, edgecolor=CLR_EDGE_ACTUAL, linewidth=0.8)

    _apply_style(ax, '图1: 接口吞吐量对比 (目标 vs 实际)', '', 'TPS (事务/秒)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    for bar in bars1:
        h = bar.get_height()
        if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + max(target)*0.02, str(int(h)), ha='center', fontsize=CHART_STYLE['annotate_size'])
    for bar in bars2:
        h = bar.get_height()
        if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + max(actual)*0.02, str(int(h)), ha='center', fontsize=CHART_STYLE['annotate_size'])

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图2: 响应时间多指标对比 (Avg+P50+P90+P95+P99) ==========
def generate_response_time_multimetric_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [d["name"][:15] for d in scenarios_data]
    n = len(names)

    avg_ms = [d.get("avg_ms", 0) for d in scenarios_data]
    p50_ms = [d.get("p50_ms", 0) or 0 for d in scenarios_data]
    p90_ms = [d.get("p90_ms", 0) or 0 for d in scenarios_data]
    p95_ms = [d.get("p95_ms", 0) for d in scenarios_data]
    p99_ms = [d.get("p99_ms", 0) or 0 for d in scenarios_data]
    stddev_ms = [d.get("stddev_ms", 0) or 0 for d in scenarios_data]

    x = np.arange(n)
    width = 0.15

    fig, ax = plt.subplots(figsize=(12, 5.5))
    bars_avg = ax.bar(x - width*2, avg_ms, width, label='平均', color=CLR_AVG, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.5)
    bars_p50 = ax.bar(x - width, p50_ms, width, label='P50', color=CLR_P50, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.5)
    bars_p90 = ax.bar(x, p90_ms, width, label='P90', color=CLR_P90, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.5)
    bars_p95 = ax.bar(x + width, p95_ms, width, label='P95', color=CLR_P95, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.5)
    bars_p99 = ax.bar(x + width*2, p99_ms, width, label='P99', color=CLR_P99, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.5)

    _apply_style(ax, '图2: 接口响应时间多指标对比 (Avg/P50/P90/P95/P99)', '', '响应时间 (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9, ncol=3)

    all_vals = avg_ms + p50_ms + p90_ms + p95_ms + p99_ms
    max_val = max(all_vals) if all_vals else 1
    for bar in ax.patches:
        h = bar.get_height()
        if h > 0 and h > max_val * 0.05:
            ax.text(bar.get_x() + bar.get_width()/2, h + max_val*0.015, f'{int(h)}', ha='center', fontsize=6, rotation=90)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图3: 响应时间标准差对比 ==========
def generate_stddev_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [d["name"][:15] for d in scenarios_data]
    stddev_ms = [d.get("stddev_ms", 0) or 0 for d in scenarios_data]
    avg_ms = [d.get("avg_ms", 0) for d in scenarios_data]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    bars = ax.bar(x, stddev_ms, width, color=CLR_STDDEV, edgecolor='#22C55E', linewidth=0.8)
    ax.plot(x, avg_ms, 'D-', color=CLR_LINE_AVG, linewidth=2, markersize=8, label='平均响应时间', zorder=5)

    _apply_style(ax, '图3: 接口响应时间标准差与波动分析', '', '标准差 (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    for i, (bar, std, avg) in enumerate(zip(bars, stddev_ms, avg_ms)):
        h = bar.get_height()
        if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + max(stddev_ms)*0.03, f'σ={int(std)}', ha='center', fontsize=CHART_STYLE['annotate_size'])
        if avg > 0: ax.annotate(f'avg={int(avg)}', (i, avg), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=7, color=CLR_LINE_AVG)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图4: P95/P99 瓶颈分析 (散点+连线) ==========
def generate_bottleneck_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    sorted_data = sorted(scenarios_data, key=lambda d: d.get("p95_ms", 0))
    names = [d["name"][:15] for d in sorted_data]
    p50 = [d.get("p50_ms", 0) or 0 for d in sorted_data]
    p90 = [d.get("p90_ms", 0) or 0 for d in sorted_data]
    p95 = [d.get("p95_ms", 0) for d in sorted_data]
    p99 = [d.get("p99_ms", 0) or 0 for d in sorted_data]

    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    ax.plot(x, p50, 'o-', color=CLR_P50, linewidth=2, markersize=8, label='P50', zorder=5)
    ax.plot(x, p90, 's-', color=CLR_P90, linewidth=2, markersize=8, label='P90', zorder=4)
    ax.plot(x, p95, 'D-', color=CLR_LINE_P95, linewidth=2.5, markersize=9, label='P95', zorder=3)
    ax.plot(x, p99, '^-', color=CLR_P99, linewidth=2, markersize=8, label='P99', zorder=2)

    _apply_style(ax, '图4: 接口响应时间瓶颈分析 (P50→P90→P95→P99)', '', '响应时间 (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图5: 错误率对比 ==========
def generate_error_rate_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [d["name"][:15] for d in scenarios_data]
    error_rates = [d.get("error_rate", 0) for d in scenarios_data]

    colors = [CLR_PASS if e <= 1.0 else CLR_WARN if e <= 3.0 else CLR_FAIL for e in error_rates]

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    bars = ax.bar(range(len(names)), error_rates, color=colors, edgecolor=CLR_EDGE_DEFAULT, linewidth=0.8)
    ax.axhline(y=1.0, color=CLR_WARN, linestyle='--', linewidth=1.5, label='错误率标准 (1%)')

    _apply_style(ax, '图5: 接口错误率对比', '', '错误率 (%)')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    for bar, rate in zip(bars, error_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(error_rates)*0.03, f'{rate:.2f}%', ha='center', fontsize=CHART_STYLE['annotate_size'])

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图6: 错误类型分布饼图 ==========
def generate_error_type_pie_chart(error_types: Dict[str, int]) -> io.BytesIO:
    buf = io.BytesIO()
    if not error_types:
        fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
        ax.text(0.5, 0.5, '无错误', ha='center', va='center', fontsize=16, color=CLR_PASS)
        ax.set_title('图6: 错误类型分布', fontsize=CHART_STYLE['title_size'], fontweight='bold')
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    labels = list(error_types.keys())
    sizes = list(error_types.values())
    colors_pie = ['#EF4444', '#F59E0B', '#F97316', '#EC4899', '#8B5CF6', '#6366F1', '#3B82F6', '#10B981']

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors_pie[:len(labels)],
        startangle=90, pctdistance=0.75,
        textprops={'fontsize': 9}
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')

    ax.set_title('图6: 错误类型分布', fontsize=CHART_STYLE['title_size'], fontweight='bold', pad=15)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图7: 各场景错误数统计 ==========
def generate_error_count_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [d["name"][:15] for d in scenarios_data]
    failed = [d.get("failed_requests", 0) for d in scenarios_data]
    total = [d.get("total_requests", 0) for d in scenarios_data]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    bars_total = ax.bar(x - width/2, total, width, label='总请求数', color='#E2E8F0', edgecolor='#94A3B8', linewidth=0.8)
    bars_fail = ax.bar(x + width/2, failed, width, label='失败数', color=CLR_FAIL, edgecolor='#DC2626', linewidth=0.8)

    _apply_style(ax, '图7: 各场景请求数 vs 失败数统计', '', '请求数')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    for bar in bars_total:
        h = bar.get_height()
        if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + max(total)*0.02, str(int(h)), ha='center', fontsize=CHART_STYLE['annotate_size'])
    for bar in bars_fail:
        h = bar.get_height()
        if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + max(failed)*0.04 if max(failed) > 0 else 0.5, str(int(h)), ha='center', fontsize=CHART_STYLE['annotate_size'], color=CLR_FAIL, fontweight='bold')

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 聚合生成所有图表 ==========

def generate_all_charts(
    scenarios: List[Dict],
    error_types: Dict[str, int] = None,
) -> Dict[str, io.BytesIO]:
    """
    生成全套性能测试图表 (7张)

    Args:
        scenarios: [{name, target_qps, actual_qps, avg_ms, p50_ms, p90_ms, p95_ms, p99_ms, 
                     stddev_ms, max_ms, min_ms, concurrency, threads, loops, duration,
                     error_rate, total_requests, failed_requests, status}, ...]
        error_types: {"连接超时": 5, "HTTP 500": 3, ...}

    Returns:
        {chart_name: BytesIO}
    """
    charts = {}

    def _safe(chart_name: str, fn, *args):
        try:
            charts[chart_name] = fn(*args)
        except Exception as e:
            print(f"[Chart] {chart_name} 生成失败: {e}")

    _safe("tps_compare", generate_tps_chart, scenarios)
    _safe("response_time_multimetric", generate_response_time_multimetric_chart, scenarios)
    _safe("stddev", generate_stddev_chart, scenarios)
    _safe("bottleneck", generate_bottleneck_chart, scenarios)
    _safe("error_rate", generate_error_rate_chart, scenarios)
    _safe("error_type_pie", generate_error_type_pie_chart, error_types or {})
    _safe("error_count", generate_error_count_chart, scenarios)

    return charts