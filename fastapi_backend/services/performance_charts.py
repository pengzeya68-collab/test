"""
性能测试报告 - 图表生成服务

基于真实压测数据生成6张实用图表：
  图1: 各接口TPS对比
  图2: 各接口响应时间多指标对比 (Avg/P50/P90/P95/P99)
  图3: 响应时间区间分布直方图
  图4: TPS吞吐量趋势折线图
  图5: 状态码分布饼图
  图6: 错误类型分布饼图
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import io
from typing import List, Dict, Any

def _find_chinese_font():
    for f in fm.fontManager.ttflist:
        if 'SimHei' in f.name or 'Microsoft YaHei' in f.name or 'Noto Sans CJK' in f.name:
            return f.name
    return 'SimHei'

_CHINESE_FONT = _find_chinese_font()
plt.rcParams['font.sans-serif'] = [_CHINESE_FONT, 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ========== 统一配色 ==========
CLR_AVG = '#FCD34D'
CLR_P50 = '#93C5FD'
CLR_P90 = '#FDBA74'
CLR_P95 = '#FCA5A5'
CLR_P99 = '#C084FC'
CLR_STDDEV = '#86EFAC'
CLR_TPS = '#6EE7B7'
CLR_TREND = '#3B82F6'
CLR_EDGE = '#374151'
CLR_PASS = '#10B981'
CLR_WARN = '#F59E0B'
CLR_FAIL = '#EF4444'

PIE_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#F97316', '#6366F1']

CHART_STYLE = {
    'figsize': (10, 5),
    'dpi': 120,
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'annotate_size': 8,
}

def _apply_style(ax, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, fontsize=CHART_STYLE['title_size'], fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, fontsize=CHART_STYLE['label_size'])
    ax.set_ylabel(ylabel, fontsize=CHART_STYLE['label_size'])
    ax.tick_params(labelsize=CHART_STYLE['tick_size'])
    ax.grid(axis='y', alpha=0.25, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def _short_name(name: str, max_len: int = 15) -> str:
    if not name:
        return '未知'
    return name[:max_len] + '...' if len(name) > max_len else name


# ========== 图1: 各接口TPS对比 ==========
def generate_tps_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    sorted_data = sorted(scenarios_data, key=lambda d: d.get("actual_qps", 0), reverse=True)
    names = [_short_name(d.get("name", "")) for d in sorted_data]
    tps_values = [d.get("actual_qps", 0) or 0 for d in sorted_data]

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    colors = [CLR_TPS] * len(names)
    bars = ax.bar(range(len(names)), tps_values, color=colors, edgecolor=CLR_EDGE, linewidth=0.8)

    _apply_style(ax, '图1: 各接口TPS吞吐量对比', '', 'TPS (事务/秒)')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=25, ha='right')

    max_tps = max(tps_values) if tps_values else 1
    for bar, val in zip(bars, tps_values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + max_tps*0.02,
                    f'{val:.1f}', ha='center', fontsize=CHART_STYLE['annotate_size'])

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图2: 响应时间多指标对比 (Avg/P50/P90/P95/P99) ==========
def generate_response_time_multimetric_chart(scenarios_data: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()
    names = [_short_name(d.get("name", "")) for d in scenarios_data]
    n = len(names)

    avg_ms = [d.get("avg_ms", 0) or 0 for d in scenarios_data]
    p50_ms = [d.get("p50_ms", 0) or 0 for d in scenarios_data]
    p90_ms = [d.get("p90_ms", 0) or 0 for d in scenarios_data]
    p95_ms = [d.get("p95_ms", 0) or 0 for d in scenarios_data]
    p99_ms = [d.get("p99_ms", 0) or 0 for d in scenarios_data]

    x = np.arange(n)
    width = 0.15

    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.bar(x - width*2, avg_ms, width, label='平均', color=CLR_AVG, edgecolor=CLR_EDGE, linewidth=0.5)
    ax.bar(x - width, p50_ms, width, label='P50', color=CLR_P50, edgecolor=CLR_EDGE, linewidth=0.5)
    ax.bar(x, p90_ms, width, label='P90', color=CLR_P90, edgecolor=CLR_EDGE, linewidth=0.5)
    ax.bar(x + width, p95_ms, width, label='P95', color=CLR_P95, edgecolor=CLR_EDGE, linewidth=0.5)
    ax.bar(x + width*2, p99_ms, width, label='P99', color=CLR_P99, edgecolor=CLR_EDGE, linewidth=0.5)

    _apply_style(ax, '图2: 各接口响应时间多指标对比 (Avg/P50/P90/P95/P99)', '', '响应时间 (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha='right')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9, ncol=5)

    all_vals = avg_ms + p50_ms + p90_ms + p95_ms + p99_ms
    max_val = max(all_vals) if all_vals and max(all_vals) > 0 else 1
    for bar in ax.patches:
        h = bar.get_height()
        if h > 0 and h > max_val * 0.05:
            ax.text(bar.get_x() + bar.get_width()/2, h + max_val*0.015,
                    f'{int(h)}', ha='center', fontsize=6, rotation=90)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图3: 响应时间区间分布直方图 ==========
def generate_rt_distribution_chart(rt_distribution: Dict[str, int]) -> io.BytesIO:
    buf = io.BytesIO()

    bucket_order = ['<10ms', '10-50ms', '50-100ms', '100-200ms', '200-500ms', '500-1000ms', '>1000ms']
    labels = []
    values = []
    for b in bucket_order:
        if b in rt_distribution:
            labels.append(b)
            values.append(rt_distribution[b])

    if not labels or sum(values) == 0:
        fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
        ax.text(0.5, 0.5, '无响应时间分布数据', ha='center', va='center', fontsize=16, color='#94A3B8')
        ax.set_title('图3: 响应时间区间分布', fontsize=CHART_STYLE['title_size'], fontweight='bold')
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    gradient_colors = ['#10B981', '#6EE7B7', '#93C5FD', '#FCD34D', '#FDBA74', '#FCA5A5', '#EF4444']

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    bars = ax.bar(range(len(labels)), values, color=gradient_colors[:len(labels)],
                  edgecolor=CLR_EDGE, linewidth=0.8)

    _apply_style(ax, '图3: 响应时间区间分布', '响应时间区间', '请求数')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0, ha='center')

    total = sum(values)
    for bar, val in zip(bars, values):
        if val > 0:
            pct = val / total * 100
            ax.text(bar.get_x() + bar.get_width()/2, val + max(values)*0.02,
                    f'{val}\n({pct:.1f}%)', ha='center', fontsize=CHART_STYLE['annotate_size'])

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图4: TPS吞吐量趋势折线图 ==========
def generate_throughput_trend_chart(throughput_trend: List[Dict]) -> io.BytesIO:
    buf = io.BytesIO()

    if not throughput_trend or len(throughput_trend) < 2:
        fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
        ax.text(0.5, 0.5, '无吞吐量趋势数据', ha='center', va='center', fontsize=16, color='#94A3B8')
        ax.set_title('图4: TPS吞吐量趋势', fontsize=CHART_STYLE['title_size'], fontweight='bold')
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    times = [d.get("t", 0) for d in throughput_trend]
    tps_vals = [d.get("tps", 0) for d in throughput_trend]

    fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
    ax.fill_between(times, tps_vals, alpha=0.15, color=CLR_TREND)
    ax.plot(times, tps_vals, '-', color=CLR_TREND, linewidth=2, label='TPS')

    avg_tps = sum(tps_vals) / len(tps_vals) if tps_vals else 0
    ax.axhline(y=avg_tps, color=CLR_WARN, linestyle='--', linewidth=1.5,
               label=f'平均 TPS: {avg_tps:.1f}')

    _apply_style(ax, '图4: TPS吞吐量趋势', '时间 (秒)', 'TPS (事务/秒)')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图5: 状态码分布饼图 ==========
def generate_status_distribution_chart(status_distribution: Dict[str, int]) -> io.BytesIO:
    buf = io.BytesIO()

    if not status_distribution or sum(status_distribution.values()) == 0:
        fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
        ax.text(0.5, 0.5, '无状态码数据', ha='center', va='center', fontsize=16, color='#94A3B8')
        ax.set_title('图5: HTTP状态码分布', fontsize=CHART_STYLE['title_size'], fontweight='bold')
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    labels = list(status_distribution.keys())
    sizes = list(status_distribution.values())

    status_colors = {
        '200': '#10B981', '201': '#6EE7B7', '204': '#93C5FD',
        '301': '#3B82F6', '302': '#60A5FA',
        '400': '#F59E0B', '401': '#FBBF24', '403': '#F97316', '404': '#FB923C',
        '500': '#EF4444', '502': '#DC2626', '503': '#B91C1C',
    }
    colors = [status_colors.get(l, '#8B5CF6') for l in labels]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors, startangle=90, pctdistance=0.75,
        textprops={'fontsize': 10}
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')

    ax.set_title('图5: HTTP状态码分布', fontsize=CHART_STYLE['title_size'], fontweight='bold', pad=15)

    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ========== 图6: 错误类型分布饼图 ==========
def generate_error_type_pie_chart(error_types: Dict[str, int]) -> io.BytesIO:
    buf = io.BytesIO()

    if not error_types or sum(error_types.values()) == 0:
        fig, ax = plt.subplots(figsize=CHART_STYLE['figsize'])
        ax.text(0.5, 0.5, '无错误', ha='center', va='center', fontsize=16, color=CLR_PASS)
        ax.set_title('图6: 错误类型分布', fontsize=CHART_STYLE['title_size'], fontweight='bold')
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    sorted_errs = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_errs) > 8:
        top = sorted_errs[:7]
        other_count = sum(v for _, v in sorted_errs[7:])
        top.append(('其他', other_count))
        labels = [k for k, v in top]
        sizes = [v for k, v in top]
    else:
        labels = [k for k, v in sorted_errs]
        sizes = [v for k, v in sorted_errs]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=PIE_COLORS[:len(labels)],
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


# ========== 聚合生成所有图表 ==========

def generate_all_charts(
    scenarios: List[Dict],
    rt_distribution: Dict[str, int] = None,
    throughput_trend: List[Dict] = None,
    status_distribution: Dict[str, int] = None,
    error_types: Dict[str, int] = None,
) -> Dict[str, io.BytesIO]:
    """
    生成全套性能测试图表 (6张)

    Args:
        scenarios: [{name, actual_qps, avg_ms, p50_ms, p90_ms, p95_ms, p99_ms,
                     stddev_ms, max_ms, min_ms, error_rate, total_requests, failed_requests}, ...]
        rt_distribution: {"<10ms": 100, "10-50ms": 500, ...}
        throughput_trend: [{"t": 0, "tps": 50.2}, {"t": 5, "tps": 48.7}, ...]
        status_distribution: {"200": 950, "500": 50}
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
    _safe("rt_distribution", generate_rt_distribution_chart, rt_distribution or {})
    _safe("throughput_trend", generate_throughput_trend_chart, throughput_trend or [])
    _safe("status_distribution", generate_status_distribution_chart, status_distribution or {})
    _safe("error_type_pie", generate_error_type_pie_chart, error_types or {})

    return charts
