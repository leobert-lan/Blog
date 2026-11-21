"""
pain_series_04_demo.py
DSP 痛苦系列 04 博客配套仿真代码：截断时空的“窗”——FIR 滤波器设计与线性相位

统一符号约定：
  L : 滤波器抽头长度 / 抽头数 (Number of taps)
  N : 滤波器阶数 (Filter order), N = L - 1
  tau : 对称中心 / 群延迟, tau = (L - 1) / 2 = N / 2

运行方式（在仓库根目录下）：
  python DSP/dsp04/pain_series_04_demo.py

依赖：
  pip install numpy matplotlib scipy
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.signal as signal

matplotlib.rcParams['font.sans-serif'] = [
    'PingFang SC', 'STHeiti', 'Heiti TC', 'Songti SC',
    'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def demo1_window_comparison():
    """demo1 - 四种对称窗函数的时域形态与频域主瓣/旁瓣特性对比（含关键点实测标注）"""
    L = 51  # 抽头长度 L=51，阶数 N=50
    w_rect = signal.windows.boxcar(L)
    w_hann = signal.windows.hann(L)
    w_hamm = signal.windows.hamming(L)
    w_black = signal.windows.blackman(L)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.0))

    # 左图：时域形态
    n = np.arange(L)
    ax1.plot(n, w_rect, label='矩形窗 (端点 = 1.00)', marker='.', markersize=4)
    ax1.plot(n, w_hann, label='汉宁窗 (端点 = 0.00)', marker='.', markersize=4)
    ax1.plot(n, w_hamm, label='汉明窗 (端点 = 0.08)', marker='.', markersize=4)
    ax1.plot(n, w_black, label='布莱克曼窗 (端点 = 0.00)', marker='.', markersize=4)
    ax1.scatter([0, L - 1], [0.08, 0.08], color='forestgreen', zorder=6, s=36)
    ax1.annotate(
        '汉明窗端点 = 0.08\n(非零端点台阶)',
        xy=(0, 0.08), xytext=(4.5, 0.17),
        arrowprops=dict(arrowstyle='->', color='forestgreen', lw=1.2),
        color='forestgreen', fontsize=9.0,
        bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='forestgreen', alpha=0.85)
    )
    ax1.set_title(f'窗函数的时域形态 (抽头长度 L={L}, 阶数 N={L-1})')
    ax1.set_xlabel('样本序号 n')
    ax1.set_ylabel('窗权重 w[n]')
    ax1.set_ylim([-0.05, 1.08])
    ax1.legend(loc='center right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：频域幅度谱（横轴严格对齐归一化角频率 ω/π ∈ [0, 1]）
    n_fft = 8192
    omega_over_pi = np.linspace(0.0, 1.0, n_fft // 2 + 1)
    spectra = {}
    for w, name in zip(
        [w_rect, w_hann, w_hamm, w_black],
        ['矩形窗', '汉宁窗', '汉明窗', '布莱克曼窗']
    ):
        W = np.fft.rfft(w, n_fft)
        W_dB = 20.0 * np.log10(np.maximum(np.abs(W) / np.max(np.abs(W)), 1e-12))
        spectra[name] = W_dB
        ax2.plot(omega_over_pi, W_dB, label=name, linewidth=1.7)

    # 背景分区提示：主瓣区 vs 旁瓣区
    ax2.axvspan(0.0, 0.0392, color='tab:blue', alpha=0.06)
    ax2.axvspan(0.080, 0.30, color='gray', alpha=0.05)
    ax2.text(
        0.006, -98, '主瓣区\n(越窄过渡带越陡)', fontsize=8.5, color='dimgray',
        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85)
    )
    ax2.text(
        0.200, -98, '旁瓣区 (越低阻带越干净)', fontsize=8.5, color='dimgray',
        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85)
    )

    # 计算并标注关键旁瓣峰值点
    mask = omega_over_pi <= 0.30
    freqs = omega_over_pi[mask]

    def get_peaks(db_arr):
        sub = db_arr[mask]
        idx = np.where((sub[1:-1] > sub[:-2]) & (sub[1:-1] >= sub[2:]))[0] + 1
        return [(float(freqs[i]), float(sub[i])) for i in idx]

    rect_p1 = get_peaks(spectra['矩形窗'])[0]
    hann_p1 = get_peaks(spectra['汉宁窗'])[0]
    hamm_peaks = get_peaks(spectra['汉明窗'])
    hamm_p1 = hamm_peaks[0]
    hamm_p3 = max(hamm_peaks, key=lambda item: item[1])  # 全频带最高旁瓣 (第 3 峰)
    black_psl = max(get_peaks(spectra['布莱克曼窗']), key=lambda item: item[1])

    annotations = [
        (rect_p1, f'矩形第1旁瓣\n{rect_p1[1]:.1f} dB', (0.070, -6.5), 'tab:blue'),
        (hann_p1, f'汉宁第1旁瓣\n{hann_p1[1]:.1f} dB', (0.106, -24.5), 'tab:orange'),
        (hamm_p1, f'汉明第1旁瓣(被压低)\n{hamm_p1[1]:.1f} dB', (0.042, -73.0), 'tab:green'),
        (hamm_p3, f'汉明最高旁瓣(第3峰)\n{hamm_p3[1]:.1f} dB', (0.178, -33.5), 'tab:green'),
        (black_psl, f'布莱克曼最高旁瓣\n{black_psl[1]:.1f} dB', (0.165, -83.0), 'tab:red'),
    ]
    for (px, py), text, text_xy, col in annotations:
        ax2.scatter([px], [py], color=col, zorder=6, s=36)
        ax2.annotate(
            text, xy=(px, py), xytext=text_xy,
            arrowprops=dict(arrowstyle='->', color=col, lw=1.15),
            color=col, fontsize=8.5,
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=col, alpha=0.96),
            zorder=7
        )

    ax2.set_title('窗函数的归一化幅度谱：主瓣宽度与峰值旁瓣电平的折中')
    ax2.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel('归一化幅度 (dB)')
    ax2.set_ylim([-102, 4])
    ax2.set_xlim([0.0, 0.30])
    ax2.legend(loc='upper right', fontsize=9.0)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_01_windows_raw.png'), dpi=150)
    plt.close()
    print(
        f"[demo1] rect_p1={rect_p1[1]:.2f} dB@{rect_p1[0]:.3f}pi, "
        f"hann_p1={hann_p1[1]:.2f} dB@{hann_p1[0]:.3f}pi, "
        f"hamm_p1={hamm_p1[1]:.2f} dB@{hamm_p1[0]:.3f}pi, "
        f"hamm_psl(p3)={hamm_p3[1]:.2f} dB@{hamm_p3[0]:.3f}pi, "
        f"black_psl={black_psl[1]:.2f} dB@{black_psl[0]:.3f}pi"
    )


def demo2_fir_window_design():
    """demo2 - 窗函数法设计低通 FIR，四种窗函数的频率响应对比（含阻带最差波纹标注）"""
    L = 51  # 抽头长度 L=51，阶数 N=50
    fc = 0.4  # 归一化截止频率 ω_c / π = 0.4

    windows_cfg = [
        ('boxcar', '矩形窗', 'tab:blue', (0.49, -11.5)),
        ('hann', '汉宁窗', 'tab:orange', (0.55, -34.0)),
        ('hamming', '汉明窗', 'tab:green', (0.58, -48.5)),
        ('blackman', '布莱克曼窗', 'tab:red', (0.64, -71.0)),
    ]

    plt.figure(figsize=(10.5, 6.0))
    summary = []
    for win_key, name, col, text_xy in windows_cfg:
        b = signal.firwin(L, fc, window=win_key)
        w, h = signal.freqz(b, worN=8192)
        fn = w / np.pi
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        plt.plot(fn, mag_db, label=name, color=col, linewidth=1.65)

        # 找到截止频率右侧第一个谷底之后的最高阻带旁瓣
        idx_sb = np.where(fn > fc)[0]
        sub_abs = np.abs(h[idx_sb])
        mins = np.where((sub_abs[1:-1] < sub_abs[:-2]) & (sub_abs[1:-1] <= sub_abs[2:]))[0] + 1
        sb_start = idx_sb[mins[0]]
        peak_idx = sb_start + int(np.argmax(mag_db[sb_start:]))
        px, py = float(fn[peak_idx]), float(mag_db[peak_idx])
        summary.append((name, px, py))
        plt.scatter([px], [py], color=col, zorder=6, s=34)
        plt.annotate(
            f'{name}阻带峰值\n{py:.1f} dB',
            xy=(px, py), xytext=text_xy,
            arrowprops=dict(arrowstyle='->', color=col, lw=1.15),
            color=col, fontsize=8.8,
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=col, alpha=0.90)
        )

    plt.axvline(fc, color='crimson', linestyle='--', alpha=0.65, label='理想截止频率 ωc = 0.4π')
    plt.title(f'不同窗函数设计的低通 FIR 幅频响应对比 (L={L}, 阶数 N={L-1})')
    plt.xlabel('归一化角频率 ω/π (×π rad/sample)')
    plt.ylabel('幅度 (dB)')
    plt.ylim([-120, 8])
    plt.xlim([0.0, 1.0])
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_02_filter_design.png'), dpi=150)
    plt.close()
    print("[demo2]", ", ".join(f"{n}: {y:.2f} dB@{x:.3f}pi" for n, x, y in summary))


def demo3_gibbs_effect():
    """demo3 - 矩形窗直接截断的吉布斯效应：抽头长度 L 增加时约 8.95% 过冲极限不消失"""
    fc = 0.4  # 对应 ω_c = 0.4π，阶跃高度 Δ = 1
    configs = [
        (21, 'L=21 (阶数 N=20)', 'tab:blue', (0.23, 1.128)),
        (101, 'L=101 (阶数 N=100)', 'tab:orange', (0.315, 1.132)),
        (501, 'L=501 (阶数 N=500)', 'tab:green', (0.43, 1.115)),
    ]

    plt.figure(figsize=(10.5, 6.0))
    peaks_log = []
    for L_val, label, col, text_xy in configs:
        # scale=False 严格对应理论公式 h[n] = h_d[n - τ] * w_rect[n]，不做额外直流重缩放
        b = signal.firwin(L_val, fc, window='boxcar', scale=False)
        w, h = signal.freqz(b, worN=16384)
        fn = w / np.pi
        mag = np.abs(h)
        plt.plot(fn, mag, label=label, color=col, linewidth=1.65)

        pk_i = int(np.argmax(mag))
        px, py = float(fn[pk_i]), float(mag[pk_i])
        peaks_log.append((L_val, px, py))
        plt.scatter([px], [py], color=col, zorder=6, s=36)
        plt.annotate(
            f'L={L_val} 峰值: {py:.3f}',
            xy=(px, py), xytext=text_xy,
            arrowprops=dict(arrowstyle='->', color=col, lw=1.15),
            color=col, fontsize=8.8,
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=col, alpha=0.90)
        )

    plt.axvline(fc, color='black', linestyle='--', linewidth=1.2, label='理想截止边界 ωc = 0.4π')
    plt.axhline(1.08949, color='gray', linestyle=':', linewidth=1.3, label='吉布斯过冲理论极限 ≈ 1.0895')
    plt.title('吉布斯效应：增加抽头长度 L 只能压缩过渡带，无法消除约 8.95% 的边缘过冲')
    plt.xlabel('归一化角频率 ω/π (×π rad/sample)')
    plt.ylabel(r'线性幅度 $|H(e^{j\omega})|$')
    plt.xlim([0.2, 0.6])
    plt.ylim([-0.03, 1.19])
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_03_gibbs.png'), dpi=150)
    plt.close()
    print("[demo3]", ", ".join(f"L={L_v}: {y:.4f}@{x:.4f}pi" for L_v, x, y in peaks_log))


def demo4_linear_phase_verify():
    """demo4 - 偶对称 Type I FIR 线性相位验证：通带严格直线、阻带过零 π 跳变与恒定群延迟 (L-1)/2"""
    L = 51  # 抽头长度 L=51，阶数 N=50，理论群延迟 τ = (L-1)/2 = 25
    tau = (L - 1) / 2.0
    fc = 0.4
    b = signal.firwin(L, fc, window='hamming')

    w, h = signal.freqz(b, worN=2048)
    phase = np.unwrap(np.angle(h))
    w_gd, gd = signal.group_delay((b, 1), w=1024)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：相位响应（标出通带与阻带，展示阻带内实幅度变号引发的 π 相位跳变）
    ax1.axvspan(0.0, 0.40, color='seagreen', alpha=0.08, label=r'通带区间 (严格直线 $-\omega\tau$)')
    ax1.axvspan(0.47, 1.00, color='indianred', alpha=0.08, label=r'阻带区间 (过零变号产生 $\pi$ 跳变)')
    ax1.plot(w / np.pi, phase, color='royalblue', linewidth=1.6, label=r'实际解缠相位 $\angle H(e^{j\omega})$')
    ax1.plot(w / np.pi, -w * tau, color='gray', linestyle='--', linewidth=1.2, alpha=0.8, label=r'连续线性基准 $-25\omega$')
    diffs = np.diff(phase)
    jump_i = int(np.argmax(np.abs(diffs)))
    ax1.annotate(
        r'实幅度过零变号' + '\n' + r'产生 $+\pi$ 跳变 (斜率不变)',
        xy=(float(w[jump_i + 1] / np.pi), float(phase[jump_i + 1])),
        xytext=(0.52, -20.0),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.2),
        color='crimson', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='crimson', alpha=0.90)
    )
    ax1.set_title(f'相位响应：通带严格线性，阻带过零伴随 π 跳变 (L={L})')
    ax1.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax1.set_ylabel('相位 (rad)')
    ax1.set_xlim([0.0, 1.0])
    ax1.legend(loc='lower left', fontsize=9.0)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：群延迟（除离散频响零点外恒定为 (L-1)/2 = 25）
    ax2.plot(w_gd / np.pi, gd, color='crimson', linewidth=1.8, label=rf'实测群延迟 $\tau_g = {tau:.1f}$ 采样点')
    ax2.set_title(f'群延迟：除频响零点外恒定为 (L-1)/2 = {tau:.1f}')
    ax2.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel('群延迟 (采样周期)')
    ax2.set_xlim([0.0, 1.0])
    ax2.set_ylim([0, 50])
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_04_linear_phase.png'), dpi=150)
    plt.close()


def demo4b_time_domain_intuition():
    """
    demo4b - 软件工程师时域直觉 2x2 对照：
      (a) 正确对称 FIR (L=51, fc=60Hz)：毛刺滤除且波形保真，切片左移 τ=25 格即可完全对齐
      (b) 错误单边截断 (从 n=0 截右半边 sinc 不平移)：对称性破坏导致单边过冲与拖尾
      (c) 非线性相位对比 (4 阶 Butterworth IIR, fc=60Hz)：相位色散使尖峰后拖出负向畸变
      (d) 幅度失真陷阱 (严格对称 FIR 但 fc=12Hz 过窄)：线性相位依然会把有效尖峰削平
    """
    fs = 500.0
    t = np.arange(0, 0.8, 1.0 / fs)
    t_ms = t * 1000.0
    clean = (
        0.15 * np.exp(-((t - 0.22) / 0.025) ** 2)
        - 0.18 * np.exp(-((t - 0.325) / 0.008) ** 2)
        + 1.20 * np.exp(-((t - 0.350) / 0.009) ** 2)
        - 0.28 * np.exp(-((t - 0.375) / 0.009) ** 2)
        + 0.32 * np.exp(-((t - 0.520) / 0.045) ** 2)
    )
    rng = np.random.default_rng(42)
    noisy = clean + 0.16 * np.sin(2.0 * np.pi * 135.0 * t) + 0.08 * rng.standard_normal(len(t))

    L = 51
    tau = (L - 1) // 2  # 25 个采样点 = 50 ms

    # 1. 对称 Type I FIR (fc = 60 Hz)
    b_sym = signal.firwin(L, 60.0, fs=fs, window='hamming')
    y_sym = signal.lfilter(b_sym, 1.0, noisy)
    y_sym_aligned = np.full_like(y_sym, np.nan)
    y_sym_aligned[:-tau] = y_sym[tau:]

    # 2. 错误单边截断：直接从 n=0..50 截未平移的理想低通 (破坏对称性)
    wc = 2.0 * np.pi * 60.0 / fs
    k = np.arange(L)
    k_safe = np.where(k == 0, 1, k)
    h_unshifted = np.where(k == 0, wc / np.pi, np.sin(wc * k_safe) / (np.pi * k_safe))
    h_unshifted /= np.sum(h_unshifted)
    y_unshifted = signal.lfilter(h_unshifted, 1.0, noisy)

    # 3. 4 阶 Butterworth IIR (fc = 60 Hz, 非线性相位)
    b_iir, a_iir = signal.butter(4, 60.0, fs=fs)
    y_iir = signal.lfilter(b_iir, a_iir, noisy)

    # 4. 严格线性相位但截止太窄 (fc = 12 Hz)
    b_narrow = signal.firwin(L, 12.0, fs=fs, window='hamming')
    y_narrow = signal.lfilter(b_narrow, 1.0, noisy)
    y_narrow_aligned = np.full_like(y_narrow, np.nan)
    y_narrow_aligned[:-tau] = y_narrow[tau:]

    fig, axes = plt.subplots(2, 2, figsize=(15, 9.2), sharex=True, sharey=True)
    xlim = (160, 620)
    ylim = (-0.52, 1.50)

    # (a) 正确对称 FIR + 对齐
    ax = axes[0, 0]
    ax.plot(t_ms, noisy, color='lightgray', linewidth=1.0, label='含噪输入 (含 135Hz 毛刺)')
    ax.plot(t_ms, clean, color='black', linestyle='--', linewidth=1.4, label='理想干净波形')
    ax.plot(t_ms, y_sym, color='royalblue', linewidth=1.5, alpha=0.85, label='FIR 直接输出 (整体延迟 50 ms)')
    ax.plot(t_ms, y_sym_aligned, color='seagreen', linewidth=1.8, label='切片 y[25:] 左移对齐后')
    ax.annotate(
        '', xy=(400, 1.15), xytext=(350, 1.15),
        arrowprops=dict(arrowstyle='<->', color='royalblue', lw=1.4)
    )
    ax.text(375, 1.21, 'τ=25点\n(50 ms)', ha='center', va='bottom', fontsize=8.5, color='royalblue')
    ax.set_title('(a) 正确对称 FIR (L=51, fc=60Hz)：波形保真，仅整体平移 τ=25 点')
    ax.set_ylabel('信号幅度')
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.legend(loc='upper left', fontsize=8.4)
    ax.grid(True, linestyle='--', alpha=0.6)

    # (b) 非对称单边截断
    ax = axes[0, 1]
    ax.plot(t_ms, clean, color='black', linestyle='--', linewidth=1.4, label='理想干净波形')
    ax.plot(t_ms, y_unshifted, color='crimson', linewidth=1.7, label='未平移：从 n=0 截断右半边 sinc')
    pk_u = int(np.argmax(y_unshifted))
    min_u = 160 + int(np.argmin(y_unshifted[160:230]))
    ax.scatter([t_ms[pk_u], t_ms[min_u]], [y_unshifted[pk_u], y_unshifted[min_u]], color='crimson', s=32, zorder=6)
    ax.annotate(
        f'非对称过冲 ({y_unshifted[pk_u]:.2f}) + 右侧拖尾',
        xy=(t_ms[min_u], y_unshifted[min_u]), xytext=(415, -0.36),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.15),
        color='crimson', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='crimson', alpha=0.90)
    )
    ax.set_title('(b) 非对称截断：从 n=0 直接截断引发单边歪斜')
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.legend(loc='upper left', fontsize=8.4)
    ax.grid(True, linestyle='--', alpha=0.6)

    # (c) 非线性相位 IIR vs 对称 FIR
    ax = axes[1, 0]
    ax.plot(t_ms, clean, color='black', linestyle='--', linewidth=1.4, label='理想干净波形')
    ax.plot(t_ms, y_sym_aligned, color='seagreen', linewidth=1.7, label='对称 FIR 对齐后 (形状对称吻合)')
    ax.plot(t_ms, y_iir, color='darkorange', linewidth=1.7, label='4 阶 Butterworth IIR (非线性相位)')
    min_iir = 160 + int(np.argmin(y_iir[160:230]))
    ax.scatter([t_ms[min_iir]], [y_iir[min_iir]], color='darkorange', s=32, zorder=6)
    ax.annotate(
        f'相位色散引发后沿振铃\n(S 谷深探至 {y_iir[min_iir]:.2f})',
        xy=(t_ms[min_iir], y_iir[min_iir]), xytext=(415, -0.38),
        arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.15),
        color='darkorange', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='darkorange', alpha=0.90)
    )
    ax.set_title('(c) 非线性相位代价：同为 60Hz 滤波，IIR 相位色散扭曲 QRS 后沿')
    ax.set_xlabel('时间 (ms)')
    ax.set_ylabel('信号幅度')
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.legend(loc='upper left', fontsize=8.4)
    ax.grid(True, linestyle='--', alpha=0.6)

    # (d) 幅度响应边界
    ax = axes[1, 1]
    ax.plot(t_ms, clean, color='black', linestyle='--', linewidth=1.4, label=f'理想干净波形 (峰值 {np.max(clean):.2f})')
    ax.plot(t_ms, y_narrow_aligned, color='purple', linewidth=1.8,
            label=f'严格线性相位 FIR 但 fc=12Hz (峰值跌至 {np.nanmax(y_narrow_aligned):.2f})')
    pk_n = int(np.nanargmax(y_narrow_aligned))
    ax.scatter([t_ms[pk_n]], [y_narrow_aligned[pk_n]], color='purple', s=34, zorder=6)
    ax.annotate(
        '线性相位 ≠ 绝对保真\n通带过窄一样削平尖峰',
        xy=(t_ms[pk_n], y_narrow_aligned[pk_n]), xytext=(405, 0.72),
        arrowprops=dict(arrowstyle='->', color='purple', lw=1.15),
        color='purple', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='purple', alpha=0.90)
    )
    ax.set_title('(d) 幅度响应影响：即使相位线性，通带过窄仍会削平尖峰')
    ax.set_xlabel('时间 (ms)')
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.legend(loc='upper left', fontsize=8.4)
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_04b_waveform_intuition.png'), dpi=150)
    plt.close()
    print(
        f"[demo4b] clean_pk={np.max(clean):.3f}, sym_pk={np.nanmax(y_sym_aligned):.3f}, "
        f"unshifted_pk={np.max(y_unshifted):.3f}/min={np.min(y_unshifted[160:230]):.3f}, "
        f"iir_min={np.min(y_iir[160:230]):.3f}, narrow_pk={np.nanmax(y_narrow_aligned):.3f}"
    )


def demo5_type2_highpass_fail():
    """
    demo5 - 三线同框频域对比：
      1. Type I  (L=51, 奇数偶对称): 通带直达 ω=π，且通带相移偏置 θ0 = 0°
      2. Type II (L=50, 偶数偶对称): 受结构零点约束，在 ω=π 处被强制拉回 0
      3. Type IV (L=50, 偶数奇对称, (-1)^n 调制): 幅频在 ω=π 处可达 1，但附带 +90° 希尔伯特相移
    """
    L1 = 51
    tau1 = (L1 - 1) / 2.0
    b_type1 = signal.firwin(L1, 0.5, pass_zero=False, window='hamming')

    L2 = 50
    tau2 = (L2 - 1) / 2.0  # 24.5
    m = np.arange(L2) - tau2
    h_hp_ideal = (np.sin(np.pi * m) - np.sin(0.5 * np.pi * m)) / (np.pi * m)
    b_type2 = h_hp_ideal * signal.windows.hamming(L2)

    b_lp_type2 = signal.firwin(L2, 0.5, window='hamming')
    b_type4 = b_lp_type2 * ((-1) ** np.arange(L2))

    w1, h1 = signal.freqz(b_type1, worN=2048)
    w2, h2 = signal.freqz(b_type2, worN=2048)
    w4, h4 = signal.freqz(b_type4, worN=2048)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    ax1.plot(w1 / np.pi, np.abs(h1), label='Type I (L=51, 奇数偶对称)：通带直达 π', color='royalblue', linewidth=2.0)
    ax1.plot(w2 / np.pi, np.abs(h2), label='Type II (L=50, 偶数偶对称)：ω=π 处强制归零', color='crimson', linestyle='--', linewidth=2.0)
    ax1.plot(w4 / np.pi, np.abs(h4), label='Type IV (L=50, 偶数奇对称)：幅频不归零', color='seagreen', linestyle='-.', linewidth=1.8)
    ax1.scatter([1.0], [0.0], color='crimson', zorder=5, s=45)
    ax1.annotate(
        '$H(e^{j\\pi}) = 0$\n(Type II 结构零点)',
        xy=(1.0, 0.02), xytext=(0.74, 0.22),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.3),
        color='crimson', fontsize=9.5
    )
    ax1.set_title('幅频响应对比：Type II 端点坍塌 vs Type IV 幅频保留')
    ax1.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax1.set_ylabel(r'线性幅度 $|H(e^{j\omega})|$')
    ax1.set_xlim([0.0, 1.02])
    ax1.set_ylim([-0.04, 1.12])
    ax1.legend(loc='upper left', fontsize=9.2)
    ax1.grid(True, linestyle='--', alpha=0.6)

    mask = (w1 / np.pi >= 0.58) & (w1 / np.pi <= 0.96)
    theta0_t1 = np.rad2deg(np.angle(h1[mask] * np.exp(1j * w1[mask] * tau1)))
    theta0_t2 = np.rad2deg(np.angle(h2[mask] * np.exp(1j * w2[mask] * tau2)))
    theta0_t4 = np.rad2deg(np.angle(h4[mask] * np.exp(1j * w4[mask] * tau2)))

    ax2.axvspan(0.58, 0.96, color='seagreen', alpha=0.07, label='观测通带区间 [0.58π, 0.96π]')
    ax2.plot(w1[mask] / np.pi, theta0_t1, label=r'Type I (偶对称)：$\theta_0 = 0^\circ$ (纯延迟无相移)', color='royalblue', linewidth=2.2)
    ax2.plot(w2[mask] / np.pi, theta0_t2, label=r'Type II (偶对称)：$\theta_0 = 0^\circ$ (归零前无附加相移)', color='crimson', linestyle='--', linewidth=1.8)
    ax2.plot(w4[mask] / np.pi, theta0_t4, label=r'Type IV (奇对称)：$\theta_0 = +90^\circ$ (希尔伯特相移)', color='seagreen', linestyle='-.', linewidth=2.0)
    ax2.set_title(r'通带残余相移 $\theta_0$：为什么 firwin 仍拒绝偶数抽头高通？')
    ax2.set_xlabel('通带归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel(r'去线性延迟后的常数相移 $\theta_0$ (度)')
    ax2.set_xlim([0.55, 1.0])
    ax2.set_ylim([-25, 115])
    ax2.set_yticks([0, 45, 90])
    ax2.legend(loc='center left', fontsize=9.2)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_05_type2_fail.png'), dpi=150)
    plt.close()


def demo5b_type4_waveform():
    """
    demo5b - Type IV (+90° 希尔伯特相移) 在时域到底把信号拧成什么样：
      左图：对称窄脉冲经过 Type I (偶对称保形) vs Type IV (拧成正负反对称双峰)
      右图：高通通带内的余弦调幅波包穿过 Type I (中心保持波峰) vs Type IV (内部载波被拧转 90° 变过零)
    """
    b_hp1 = signal.firwin(51, 0.5, pass_zero=False, window='hamming')
    b_hp4 = signal.firwin(50, 0.5, window='hamming') * ((-1) ** np.arange(50))

    n = np.arange(200)
    # 1. 对称窄脉冲 (sigma = 1.0 样本，中心在 n=60)
    x_pulse = np.exp(-((n - 60.0) / 1.0) ** 2)
    y1_p = np.roll(signal.lfilter(b_hp1, 1.0, x_pulse), -25)
    y4_p_raw = signal.lfilter(b_hp4, 1.0, x_pulse)
    rel_t1 = np.arange(-15, 16)
    y1_p_centered = y1_p[45:76]
    rel_t4 = np.arange(70, 100) - 84.5
    y4_p_centered = y4_p_raw[70:100]

    # 2. 通带高频脉冲包络 (中心频率 0.75π 位于高通通带平坦区, 中心在 n=80)
    x_burst = np.cos(0.75 * np.pi * (n - 80.0)) * np.exp(-((n - 80.0) / 8.0) ** 2)
    y1_b = np.roll(signal.lfilter(b_hp1, 1.0, x_burst), -25)
    y4_b_raw = signal.lfilter(b_hp4, 1.0, x_burst)
    rel_b1 = np.arange(-12, 13)
    y1_b_centered = y1_b[68:93]
    rel_b4 = np.arange(92, 117) - 104.5
    y4_b_centered = y4_b_raw[92:117]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.8))

    ax1.plot(rel_t1, x_pulse[45:76] * 0.25, color='gray', linestyle=':', linewidth=1.4, label='对称输入脉冲 (缩放 0.25× 示意)')
    ax1.plot(rel_t1, y1_p_centered, color='royalblue', marker='.', markersize=4.5, linewidth=1.8,
             label='Type I 高通输出：保持左右偶对称 (单正峰)')
    ax1.plot(rel_t4, y4_p_centered, color='seagreen', marker='.', markersize=4.5, linestyle='-.', linewidth=1.8,
             label='Type IV 高通输出：+90° 相移转为反对称双极性波')
    ax1.axvline(0.0, color='black', linestyle='--', alpha=0.4)
    ax1.axhline(0.0, color='black', linewidth=0.8, alpha=0.4)
    ax1.annotate(
        '中心处变成过零反转\n(对称形态改变)',
        xy=(0.5, float(np.min(y4_p_centered))), xytext=(3.0, -0.24),
        arrowprops=dict(arrowstyle='->', color='seagreen', lw=1.2),
        color='seagreen', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='seagreen', alpha=0.92)
    )
    ax1.set_title('时域直觉 1：对称窄脉冲穿过 Type I vs Type IV 高通')
    ax1.set_xlabel('相对中心样本偏移 (n - n_center)')
    ax1.set_ylabel('输出幅度')
    ax1.set_xlim([-10, 12])
    ax1.set_ylim([-0.30, 0.44])
    ax1.legend(loc='upper right', fontsize=8.5)
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2.plot(rel_b1, x_burst[68:93], color='gray', linestyle=':', linewidth=1.5, label='原始输入波包 (0.75π, 中心为波峰 +1.0)')
    ax2.plot(rel_b1, y1_b_centered, color='royalblue', marker='.', markersize=4.5, linewidth=1.8,
             label='Type I 高通输出：中心与原输入完全重合')
    ax2.plot(rel_b4, y4_b_centered, color='seagreen', marker='.', markersize=4.5, linestyle='-.', linewidth=1.8,
             label='Type IV 高通输出：包络一致，相位偏置 +90° (cos → -sin)')
    ax2.axvline(0.0, color='black', linestyle='--', alpha=0.4)
    ax2.axhline(0.0, color='black', linewidth=0.8, alpha=0.4)
    ax2.annotate(
        '外包络幅频一致 (|H|=1)\n中心波峰转为过零点',
        xy=(0.0, 0.0), xytext=(1.6, -1.18),
        arrowprops=dict(arrowstyle='->', color='seagreen', lw=1.25),
        color='seagreen', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='seagreen', alpha=0.95),
        zorder=7
    )
    ax2.set_title('时域直觉 2：同在通带内 (0.75π)，+90° 相移改变波包内部形态')
    ax2.set_xlabel('相对中心样本偏移 (n - n_center)')
    ax2.set_ylabel('输出幅度')
    ax2.set_xlim([-10, 11])
    ax2.set_ylim([-1.32, 1.58])
    ax2.legend(loc='upper right', fontsize=8.5)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_05b_type4_waveform.png'), dpi=150)
    plt.close()
    print(
        f"[demo5b] Type I pulse max={np.max(y1_p_centered):.3f}, "
        f"Type IV pulse max/min={np.max(y4_p_centered):.3f}/{np.min(y4_p_centered):.3f}; "
        f"burst TypeI@0={y1_b_centered[12]:.3f}, TypeIV@-0.5/+0.5={y4_b_centered[12]:.3f}/{y4_b_centered[13]:.3f}"
    )


def demo6_parks_mcclellan():
    """
    demo6 - Parks-McClellan 等波纹逼近 vs 窗函数法双维度对比（含关键实测数值标注）：
      左图：相同抽头数 (L=51, N=50) 下的过渡带与误差预算分布对比
      右图：相同设计指标 (通带 [0, 0.3π] 误差 ≤ 0.01, 阻带 [0.4π, π] 衰减 ≥ 50 dB) 下的最小抽头数实测对比
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.0))

    # --- 左图：固定抽头数 L=51 (阶数 N=50) ---
    L_fixed = 51
    bands = [0.0, 0.3, 0.4, 1.0]
    desired = [1, 0]
    b_remez_51 = signal.remez(L_fixed, bands, desired, weight=[1.0, 1.0], fs=2.0)
    b_hamm_51 = signal.firwin(L_fixed, 0.35, window='hamming')

    w_r51, h_r51 = signal.freqz(b_remez_51, worN=4096)
    w_h51, h_h51 = signal.freqz(b_hamm_51, worN=4096)
    fn = w_h51 / np.pi
    db_h51 = 20.0 * np.log10(np.maximum(np.abs(h_h51), 1e-12))
    db_r51 = 20.0 * np.log10(np.maximum(np.abs(h_r51), 1e-12))

    idx_04 = int(np.argmin(np.abs(fn - 0.4)))
    val_h_04 = float(db_h51[idx_04])
    idx_far_pk = int(np.where(fn > 0.9)[0][np.argmax(db_h51[fn > 0.9])])
    val_h_far = float(db_h51[idx_far_pk])
    idx_r_pk = int(np.where(fn >= 0.4)[0][np.argmax(db_r51[fn >= 0.4])])
    val_r_ceil = float(db_r51[idx_r_pk])

    ax1.axvspan(0.0, 0.3, color='seagreen', alpha=0.08, label='目标通带 [0, 0.3π]')
    ax1.axvspan(0.4, 1.0, color='indianred', alpha=0.08, label='目标阻带 [0.4π, π]')
    ax1.plot(fn, db_h51, label='汉明窗法 (L=51, N=50)', color='darkorange', linewidth=1.65)
    ax1.plot(fn, db_r51, label='等权重 Remez (L=51, W=[1, 1])', color='royalblue', linewidth=1.65)

    ax1.scatter([0.4, float(fn[idx_far_pk]), float(fn[idx_r_pk])], [val_h_04, val_h_far, val_r_ceil],
                color=['darkorange', 'darkorange', 'royalblue'], zorder=6, s=36)
    ax1.annotate(
        f'0.4π 处仅 {val_h_04:.1f} dB\n(滚降未完成)',
        xy=(0.4, val_h_04), xytext=(0.46, -21.0),
        arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.15),
        color='darkorange', fontsize=8.6,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='darkorange', alpha=0.90)
    )
    ax1.annotate(
        f'远端峰值 {val_h_far:.1f} dB\n(误差预算冗余)',
        xy=(float(fn[idx_far_pk]), val_h_far), xytext=(0.60, -93.0),
        arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.15),
        color='darkorange', fontsize=8.6,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='darkorange', alpha=0.90)
    )
    ax1.annotate(
        f'Remez 等高波纹上限: {val_r_ceil:.1f} dB',
        xy=(float(fn[idx_r_pk]), val_r_ceil), xytext=(0.48, -36.0),
        arrowprops=dict(arrowstyle='->', color='royalblue', lw=1.15),
        color='royalblue', fontsize=8.6,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='royalblue', alpha=0.90)
    )

    ax1.set_title('固定抽头数 (L=51)：误差预算分配与过渡带陡度对比')
    ax1.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_ylim([-102, 8])
    ax1.set_xlim([0.0, 1.0])
    ax1.legend(loc='upper right', fontsize=8.8)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- 右图：固定指标 (δp ≤ 0.01, 阻带 ≤ -50 dB) 实测最小奇数抽头数 ---
    delta_p = 0.01
    delta_s = 10.0 ** (-50.0 / 20.0)
    weights = [1.0, delta_p / delta_s]

    L_hamm_min = None
    for L_cand in range(31, 101, 2):
        bh = signal.firwin(L_cand, 0.35, window='hamming')
        w, hh = signal.freqz(bh, worN=8192)
        fn_c = w / np.pi
        if np.max(np.abs(np.abs(hh[fn_c <= 0.3]) - 1.0)) <= delta_p and np.max(np.abs(hh[fn_c >= 0.4])) <= delta_s:
            L_hamm_min = L_cand
            b_hamm_spec = bh
            break

    L_remez_min = None
    for L_cand in range(21, 101, 2):
        br = signal.remez(L_cand, bands, desired, weight=weights, fs=2.0)
        w, hr = signal.freqz(br, worN=8192)
        fn_c = w / np.pi
        if np.max(np.abs(np.abs(hr[fn_c <= 0.3]) - 1.0)) <= delta_p and np.max(np.abs(hr[fn_c >= 0.4])) <= delta_s:
            L_remez_min = L_cand
            b_remez_spec = br
            break

    w_hs, h_hs = signal.freqz(b_hamm_spec, worN=4096)
    w_rs, h_rs = signal.freqz(b_remez_spec, worN=4096)

    ax2.axvspan(0.0, 0.3, color='seagreen', alpha=0.08)
    ax2.axvspan(0.4, 1.0, color='indianred', alpha=0.08)
    ax2.axhline(-50.0, color='crimson', linestyle=':', linewidth=1.3, label='阻带指标线 -50.0 dB')
    ax2.plot(w_hs / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_hs), 1e-12)),
             label=f'汉明窗达标最小长度：L={L_hamm_min} (阶数 N={L_hamm_min-1})',
             color='darkorange', linewidth=1.65)
    ax2.plot(w_rs / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_rs), 1e-12)),
             label=f'加权 Remez 达标最小长度：L={L_remez_min} (阶数 N={L_remez_min-1}, W=[1, 3.16])',
             color='royalblue', linewidth=1.65)
    ax2.annotate(
        f'同指标节省 {L_hamm_min - L_remez_min} 个抽头\n(L={L_hamm_min} → L={L_remez_min})',
        xy=(0.55, -50.0), xytext=(0.48, -32.0),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.2),
        color='crimson', fontsize=8.8,
        bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='crimson', alpha=0.90)
    )
    ax2.set_title('固定指标 (δp≤0.01, 阻带≤-50dB)：达标所需最小抽头数实测')
    ax2.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_ylim([-102, 8])
    ax2.set_xlim([0.0, 1.0])
    ax2.legend(loc='upper right', fontsize=8.8)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_06_remez.png'), dpi=150)
    plt.close()
    print(
        f"[demo6] hamm_0.4pi={val_h_04:.2f} dB, hamm_far_pk={val_h_far:.2f} dB, "
        f"remez_ceil={val_r_ceil:.2f} dB, L_hamm_min={L_hamm_min}, L_remez_min={L_remez_min}"
    )


if __name__ == '__main__':
    print("Generating DSP-04 FIR Filter Design Figures...")
    demo1_window_comparison()
    demo2_fir_window_design()
    demo3_gibbs_effect()
    demo4_linear_phase_verify()
    demo4b_time_domain_intuition()
    demo5_type2_highpass_fail()
    demo5b_type4_waveform()
    demo6_parks_mcclellan()
    print("Done. Figures saved in:", OUTPUT_DIR)
