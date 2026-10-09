"""
pain_series_02_demo.py
痛苦系列 DSP-02：DTFT 与 DFT 频域切片工程实践验证

包含 10 组仿真验证实验：
  【第一幕：DTFT 的物理意义与性质】
  Demo 1: 单频信号的 DTFT（理解连续复指数基底投影与有限长截断谱线）
  Demo 2: 实序列频谱对称性（验证幅度偶对称与相位奇对称）
  Demo 3: 频域滤波模拟（频域正交解耦与低通滤波）
  Demo 4: 卷积定理验证（时域卷积 = 频域相乘）
  Demo 5: 矩形脉冲 DTFT 与时频不确定性（Dirichlet 核与主瓣宽度演变）

  【第二幕：走向计算机的 DFT 与工程幻象】
  Demo 6: DFT 是 DTFT 的等间隔频域采样（16 点矩形脉冲的频域采样与插值关系）
  Demo 7: 帕斯瓦尔定理能量守恒（时域总能量与频域能量归一化一致性验证）
  Demo 8: 栅栏效应与频谱泄漏（格点 vs 偏格点，窗函数旁瓣抑制）
  Demo 9: 补零（Zero-padding）的插值效果 vs 物理频率分辨率
  Demo 10: 循环卷积 vs 线性卷积（时域周期折叠混叠机理与补零法计算线性卷积）

运行方式（在项目根目录下）：
  python DSP/dsp02/pain_series_02_demo.py

依赖：
  pip install numpy matplotlib scipy
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams['font.sans-serif'] = [
    'PingFang SC', 'STHeiti', 'Heiti TC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 工具函数：手动计算 DTFT
# ============================================================
def compute_dtft(x, n, omega_range=None, num_points=512):
    """
    计算序列 x[n] 的 DTFT。
    DTFT 公式：X(e^jω) = Σ x[n] * e^(-jωn)

    参数:
        x: 序列的值数组
        n: 对应的时间索引数组（与 x 等长）
        omega_range: (omega_min, omega_max)，默认 (-π, π)
        num_points: 频率采样点数

    返回:
        omega: 频率轴
        X: 对应的 DTFT 值（复数数组）
    """
    if omega_range is None:
        omega_range = (-np.pi, np.pi)
    omega = np.linspace(omega_range[0], omega_range[1], num_points)
    # 利用广播：omega 是列向量，n 是行向量
    X = np.sum(x * np.exp(-1j * np.outer(omega, n)), axis=1)
    return omega, X


# ============================================================
# 演示 1：单频信号的 DTFT
# ============================================================
def demo1_single_frequency():
    """演示一个纯正弦序列的频谱，包含时域、幅度谱、相位谱和复平面轨迹。"""
    print("=== 演示 1：单频信号的 DTFT ===")
    fs = 100          # 采样率 100 Hz
    f0 = 10           # 信号频率 10 Hz
    omega0 = 2 * np.pi * f0 / fs   # 数字频率 = 2π × f/fs

    N = 64            # 序列长度
    n = np.arange(N)
    x = np.sin(omega0 * n)         # 正弦序列

    omega, X = compute_dtft(x, n)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('演示1：单频正弦信号 (f=10Hz, fs=100Hz) 的 DTFT', fontsize=14)

    # 时域
    axes[0, 0].stem(n[:32], x[:32], markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title('时域信号 x[n]（前32点）')
    axes[0, 0].set_xlabel('n（采样点）')
    axes[0, 0].set_ylabel('幅度')
    axes[0, 0].grid(True, alpha=0.3)

    # 幅度谱，标注数字频率与物理频率的对应
    axes[0, 1].plot(omega, np.abs(X))
    axes[0, 1].axvline(omega0, color='r', linestyle='--', label=f'ω₀={omega0:.2f} rad (f=10Hz)')
    axes[0, 1].axvline(-omega0, color='r', linestyle='--')
    axes[0, 1].set_title('幅度谱 |X(e^jω)|')
    axes[0, 1].set_xlabel('ω (弧度/采样)')
    axes[0, 1].set_ylabel('幅度')
    axes[0, 1].set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    axes[0, 1].set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 相位谱
    axes[1, 0].plot(omega, np.angle(X))
    axes[1, 0].set_title('相位谱 ∠X(e^jω)')
    axes[1, 0].set_xlabel('ω (弧度/采样)')
    axes[1, 0].set_ylabel('相位 (弧度)')
    axes[1, 0].set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    axes[1, 0].set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    axes[1, 0].grid(True, alpha=0.3)

    # 复平面轨迹
    axes[1, 1].plot(np.real(X), np.imag(X), 'C2-', alpha=0.6)
    axes[1, 1].set_title('X(e^jω) 复平面轨迹')
    axes[1, 1].set_xlabel('实部')
    axes[1, 1].set_ylabel('虚部')
    axes[1, 1].axhline(0, color='k', linewidth=0.5)
    axes[1, 1].axvline(0, color='k', linewidth=0.5)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_aspect('equal')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo1_single_freq.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print(f"  信号数字频率: ω₀ = 2π×{f0}/{fs} = {omega0:.4f} rad")
    print(f"  幅度谱峰值位置验证: {omega[np.argmax(np.abs(X))]:.4f} rad ≈ {omega0:.4f}")
    print()


# ============================================================
# 演示 2：实序列频谱对称性验证
# ============================================================
def demo2_symmetry():
    """验证实序列的频谱共轭对称性（幅度谱偶对称，相位谱奇对称）。"""
    print("=== 演示 2：实序列频谱对称性 ===")

    n = np.arange(64)
    # 两个频率的叠加：实序列
    x = 0.8 * np.cos(0.3 * np.pi * n) + 0.4 * np.cos(0.7 * np.pi * n)

    omega, X = compute_dtft(x, n)

    # 定量验证对称性
    half = len(omega) // 2
    amp_error = np.max(np.abs(np.abs(X[half:]) - np.abs(X[:half][::-1])))
    print(f"  幅度谱对称误差（应≈0）: {amp_error:.2e}")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('实序列频谱对称性验证', fontsize=13)

    axes[0].stem(n[:32], x[:32], markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0].set_title('实序列 x[n]（两频率叠加）')
    axes[0].set_xlabel('n')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(omega, np.abs(X))
    axes[1].set_title('幅度谱 |X(e^jω)|（偶对称）')
    axes[1].set_xlabel('ω (弧度/采样)')
    axes[1].set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    axes[1].set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    axes[1].axvline(0, color='r', linestyle='--', alpha=0.5, label='对称轴 ω=0')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(omega, np.angle(X))
    axes[2].set_title('相位谱 ∠X(e^jω)（奇对称）')
    axes[2].set_xlabel('ω (弧度/采样)')
    axes[2].set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    axes[2].set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    axes[2].axvline(0, color='r', linestyle='--', alpha=0.5)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo4_symmetry.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 3：频域滤波模拟
# ============================================================
def demo3_frequency_domain_filtering():
    """模拟频域相乘实现低通滤波，去除高频噪音。"""
    print("=== 演示 3：频域滤波模拟 ===")

    fs = 1000          # 采样率 1000 Hz
    N = fs             # 1 秒，共 1000 个采样点
    n = np.arange(N)

    # 信号 = 100 Hz 音乐 + 400 Hz 高频噪音
    f_music = 100
    f_noise = 400
    x = (np.sin(2 * np.pi * f_music / fs * n)
         + 0.6 * np.sin(2 * np.pi * f_noise / fs * n))

    print(f"  原始信号：{f_music} Hz 音乐 + {f_noise} Hz 噪音")

    # 用 FFT 进行频域处理
    X_fft = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, d=1.0/fs)

    # 理想低通滤波器：截止频率 200 Hz
    cutoff_freq = 200
    H_lpf = (freqs <= cutoff_freq).astype(float)

    # 频域相乘（卷积定理的直接应用）
    Y_fft = X_fft * H_lpf

    # 逆变换回时域
    y_filtered = np.fft.irfft(Y_fft, N)

    print(f"  低通滤波截止频率: {cutoff_freq} Hz")
    print(f"  滤波后 {f_noise} Hz 成分幅度: {np.max(np.abs(np.fft.rfft(y_filtered)[freqs == f_noise])):.4f}（应≈0）")

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.suptitle('频域滤波模拟：去除高频噪音（低通滤波器）', fontsize=13)

    show_samples = 200  # 显示前 200 点观察波形
    t = n / fs

    axes[0, 0].plot(t[:show_samples], x[:show_samples], 'C0-', alpha=0.8)
    axes[0, 0].set_title('原始信号（100Hz + 400Hz 混合）')
    axes[0, 0].set_xlabel('时间 (秒)')
    axes[0, 0].set_ylabel('幅度')
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(freqs, np.abs(X_fft) / N * 2, 'C0-')
    axes[0, 1].axvline(f_music, color='g', linestyle='--', label=f'{f_music}Hz 音乐', alpha=0.8)
    axes[0, 1].axvline(f_noise, color='r', linestyle='--', label=f'{f_noise}Hz 噪音', alpha=0.8)
    axes[0, 1].set_title('原始信号频谱（两个明显的峰）')
    axes[0, 1].set_xlabel('频率 (Hz)')
    axes[0, 1].set_ylabel('幅度')
    axes[0, 1].legend()
    axes[0, 1].set_xlim(0, 500)
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(t[:show_samples], y_filtered[:show_samples], 'C2-', alpha=0.8)
    axes[1, 0].set_title('滤波后信号（高频噪音已去除）')
    axes[1, 0].set_xlabel('时间 (秒)')
    axes[1, 0].set_ylabel('幅度')
    axes[1, 0].grid(True, alpha=0.3)

    Y_plot = np.fft.rfft(y_filtered)
    axes[1, 1].plot(freqs, np.abs(Y_plot) / N * 2, 'C2-')
    axes[1, 1].axvline(cutoff_freq, color='r', linestyle='--',
                       label=f'截止 {cutoff_freq}Hz', alpha=0.8)
    axes[1, 1].set_title('滤波后频谱（只剩 100Hz 分量）')
    axes[1, 1].set_xlabel('频率 (Hz)')
    axes[1, 1].set_ylabel('幅度')
    axes[1, 1].legend()
    axes[1, 1].set_xlim(0, 500)
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo5_filtering.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 4：卷积定理验证
# ============================================================
def demo4_convolution_theorem():
    """验证卷积定理：时域卷积 = 频域相乘。"""
    print("=== 演示 4：卷积定理验证 ===")

    x = np.array([1.0, 2.0, 3.0])
    h = np.array([1.0, 0.5])
    nx = np.arange(len(x))
    nh = np.arange(len(h))

    # 方法 1：时域直接卷积
    y_time = np.convolve(x, h)
    ny = np.arange(len(y_time))
    print(f"  方法1 - 时域卷积结果: {y_time}")

    # 方法 2：频域相乘（零填充到相同长度，等价于线性卷积）
    N_fft = len(y_time)
    X_fft = np.fft.fft(x, N_fft)
    H_fft = np.fft.fft(h, N_fft)
    Y_fft = X_fft * H_fft          # 频域逐点相乘
    y_freq = np.real(np.fft.ifft(Y_fft))
    print(f"  方法2 - 频域相乘结果: {np.round(y_freq, 6)}")
    print(f"  两种方法误差(应≈0): {np.max(np.abs(y_time - y_freq)):.2e}")

    # 连续 DTFT 可视化
    num_points = 1024
    omega = np.linspace(-np.pi, np.pi, num_points)
    X_freq = np.sum(x * np.exp(-1j * np.outer(omega, nx)), axis=1)
    H_freq = np.sum(h * np.exp(-1j * np.outer(omega, nh)), axis=1)
    Y_freq = X_freq * H_freq

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle('卷积定理验证：时域卷积 ↔ 频域相乘', fontsize=13)

    axes[0, 0].stem(nx, x, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title('输入 x[n] = [1, 2, 3]')
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].stem(nh, h, markerfmt='C1o', linefmt='C1-', basefmt='k-')
    axes[0, 1].set_title('系统 h[n] = [1, 0.5]')
    axes[0, 1].grid(True, alpha=0.3)

    axes[0, 2].stem(ny, y_time, markerfmt='C2o', linefmt='C2-', basefmt='k-')
    axes[0, 2].set_title(f'时域卷积输出 y[n] = {y_time}')
    axes[0, 2].grid(True, alpha=0.3)

    axes[1, 0].plot(omega, np.abs(X_freq))
    axes[1, 0].set_title('|X(e^jω)|')
    axes[1, 0].set_xticks([-np.pi, 0, np.pi])
    axes[1, 0].set_xticklabels(['-π', '0', 'π'])
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(omega, np.abs(H_freq), 'C1-')
    axes[1, 1].set_title('|H(e^jω)|（具有低通特性）')
    axes[1, 1].set_xticks([-np.pi, 0, np.pi])
    axes[1, 1].set_xticklabels(['-π', '0', 'π'])
    axes[1, 1].grid(True, alpha=0.3)

    axes[1, 2].plot(omega, np.abs(Y_freq), 'C2-')
    axes[1, 2].set_title('|Y(e^jω)| = |X||H|（频域相乘）')
    axes[1, 2].set_xticks([-np.pi, 0, np.pi])
    axes[1, 2].set_xticklabels(['-π', '0', 'π'])
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo3_dtft_convolution.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 5：矩形脉冲与时频不确定性
# ============================================================
def demo5_rect_pulse_uncertainty():
    """演示矩形脉冲的 DTFT 及 M 变化对频谱的影响（时频不确定性）。"""
    print("=== 演示 5：矩形脉冲的 DTFT（时频不确定性）===")

    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    fig.suptitle('矩形脉冲 DTFT：M 越大，时域越宽，频域主瓣越窄', fontsize=13)

    M_values = [2, 5, 10]
    for idx, M in enumerate(M_values):
        # 截断模拟
        n_full = np.arange(-50, 51)
        x_full = np.zeros(len(n_full))
        x_full[(n_full >= -M) & (n_full <= M)] = 1

        omega, X = compute_dtft(x_full, n_full)

        # 理论 Dirichlet 函数
        with np.errstate(divide='ignore', invalid='ignore'):
            X_theory = np.where(
                np.abs(np.sin(omega / 2)) < 1e-10,
                float(2 * M + 1),
                np.sin(omega * (M + 0.5)) / np.sin(omega / 2)
            )

        # 时域图
        n_show = np.arange(-M, M + 1)
        axes[idx, 0].stem(n_show, np.ones(len(n_show)),
                          markerfmt='C0o', linefmt='C0-', basefmt='k-')
        axes[idx, 0].set_title(f'时域：矩形脉冲 M={M}，宽度={2*M+1}')
        axes[idx, 0].set_xlabel('n')
        axes[idx, 0].set_xlim(-15, 15)
        axes[idx, 0].grid(True, alpha=0.3)

        # 频域图
        axes[idx, 1].plot(omega, np.abs(X), 'C0-', label='数值计算', linewidth=2)
        axes[idx, 1].plot(omega, np.abs(X_theory), 'r--', label='理论 Dirichlet 函数',
                          linewidth=1, alpha=0.7)
        main_lobe_width = 2 * np.pi / (M + 0.5)
        axes[idx, 1].set_title(f'幅度谱：M={M}（主瓣宽≈{main_lobe_width:.2f} rad）')
        axes[idx, 1].set_xlabel('ω (弧度/采样)')
        axes[idx, 1].set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
        axes[idx, 1].set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
        axes[idx, 1].legend()
        axes[idx, 1].grid(True, alpha=0.3)

        print(f"  M={M}: 时域宽度={2*M+1}, 理论主瓣宽≈{main_lobe_width:.3f} rad")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo2_rect_pulse.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 6：DFT 是 DTFT 的等间隔采样
# ============================================================
def demo6_dft_vs_dtft():
    """可视化 DFT 和 DTFT 的关系：DFT 是 DTFT 连续曲线在 ω=2πk/N 处的采样值。"""
    print("=== 演示 6：DFT 是 DTFT 的频域采样 ===")

    M = 3               # 矩形脉冲半宽
    N_dft = 16          # DFT 点数
    n_full = np.arange(-30, 31)
    x_full = (np.abs(n_full) <= M).astype(float)

    # 计算 DTFT（连续曲线）
    omega_cont, X_cont = compute_dtft(x_full, n_full, num_points=1024)

    # 计算 DFT（N 个离散点，平移到 [0, N-1]）
    x_dft = np.zeros(N_dft)
    for i, ni in enumerate(n_full):
        if 0 <= ni < N_dft:
            x_dft[ni] = x_full[i]
    X_dft = np.fft.fft(x_dft)
    k = np.arange(N_dft)
    omega_dft = 2 * np.pi * k / N_dft

    n_shifted = np.arange(N_dft)
    X_dtft_at_dft = np.sum(
        x_dft * np.exp(-1j * np.outer(omega_dft, n_shifted)), axis=1
    )
    error = np.max(np.abs(np.abs(X_dft) - np.abs(X_dtft_at_dft)))
    print(f"  DFT 与 DTFT 采样值误差（应≈0）: {error:.2e}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('演示1：DFT 是 DTFT 的等间隔频域采样', fontsize=13)

    axes[0].stem(np.arange(N_dft), x_dft, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0].set_title(f'时域序列（矩形脉冲，N={N_dft}点）')
    axes[0].set_xlabel('n')
    axes[0].grid(True, alpha=0.3)

    omega_pos = omega_cont.copy()
    X_pos = X_cont.copy()
    omega_pos[omega_cont < 0] += 2 * np.pi

    axes[1].plot(np.sort(omega_pos), np.abs(X_pos[np.argsort(omega_pos)]),
                 'C0-', linewidth=1.5, label='DTFT（连续）', alpha=0.7)
    axes[1].stem(omega_dft, np.abs(X_dft),
                 markerfmt='ro', linefmt='r-', basefmt='k-',
                 label=f'DFT（{N_dft}个采样点）')
    axes[1].set_title('幅度谱：DTFT 曲线 vs DFT 采样点')
    axes[1].set_xlabel('ω (弧度/采样)')
    axes[1].set_xticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    axes[1].set_xticklabels(['0', 'π/2', 'π', '3π/2', '2π'])
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo1_dft_vs_dtft.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 7：帕斯瓦尔定理——时频能量守恒
# ============================================================
def demo7_parseval_theorem():
    """验证帕斯瓦尔定理：时域能量 = 频域能量（差 1/N 的归一化）。"""
    print("=== 演示 7：帕斯瓦尔定理能量守恒 ===")

    fs = 1000
    N = 256
    n = np.arange(N)
    x = (np.sin(2*np.pi*100/fs*n) + 0.5*np.cos(2*np.pi*250/fs*n)
         + 0.3*np.sin(2*np.pi*400/fs*n))

    X = np.fft.fft(x)

    E_time = np.sum(np.abs(x)**2)
    E_freq = np.sum(np.abs(X)**2) / N
    error = abs(E_time - E_freq)

    print(f"  时域能量: {E_time:.6f}")
    print(f"  频域能量（÷N）: {E_freq:.6f}")
    print(f"  误差（应≈0）: {error:.2e}")

    freqs = np.fft.fftfreq(N, 1/fs)
    energy_per_bin = np.abs(X)**2 / N

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle(f'帕斯瓦尔定理验证：时域能量={E_time:.2f}，频域能量={E_freq:.2f}，误差={error:.2e}',
                 fontsize=12)

    axes[0].plot(n / fs, x, 'C0-', alpha=0.8)
    axes[0].set_title('时域信号 x[n]（三个频率叠加）')
    axes[0].set_xlabel('时间 (秒)')
    axes[0].set_ylabel('幅度')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(freqs[:N//2], np.abs(X[:N//2]) / N * 2)
    axes[1].set_title('幅度谱 |X[k]|/N')
    axes[1].set_xlabel('频率 (Hz)')
    axes[1].set_xlim(0, fs/2)
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(freqs[:N//2], energy_per_bin[:N//2])
    axes[2].set_title('频域能量分布 |X[k]|²/N\n（各频率分量的能量份额）')
    axes[2].set_xlabel('频率 (Hz)')
    axes[2].set_xlim(0, fs/2)
    axes[2].fill_between(freqs[:N//2], energy_per_bin[:N//2], alpha=0.3)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo4_parseval.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 8：栅栏效应与频谱泄漏
# ============================================================
def demo8_picket_fence():
    """演示栅栏效应与非格点频率泄漏，及窗函数的抑制效果。"""
    print("=== 演示 8：栅栏效应与频谱泄漏 ===")

    fs = 1000
    N = 64

    f_on = 5 * fs / N       # 格点频率
    f_off = 5.5 * fs / N    # 偏离半个格点

    n = np.arange(N)
    x_on = np.sin(2 * np.pi * f_on / fs * n)
    x_off = np.sin(2 * np.pi * f_off / fs * n)

    windows = {
        '矩形窗（无窗）': np.ones(N),
        '汉宁窗': np.hanning(N),
        '汉明窗': np.hamming(N),
        '布莱克曼窗': np.blackman(N),
    }

    freqs = np.fft.fftfreq(N, 1/fs)[:N//2]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('栅栏效应与窗函数改善：非格点频率的频谱泄漏', fontsize=13)

    axes[0, 0].stem(n, x_on, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title(f'信号（f={f_on:.1f}Hz，在格点）')
    axes[0, 0].set_xlabel('n')
    axes[0, 0].grid(True, alpha=0.3)

    for (name, win), color in zip(windows.items(), ['C0', 'C1', 'C2', 'C3']):
        X = np.fft.fft(x_on * win)
        amp = np.abs(X[:N//2]) / (np.sum(win) / 2)
        axes[0, 1].plot(freqs, 20*np.log10(amp + 1e-10), color=color,
                        alpha=0.8, label=name, linewidth=1.5)
    axes[0, 1].set_title('各窗函数频谱（频率在格点，矩形窗无旁瓣）')
    axes[0, 1].set_xlabel('频率 (Hz)')
    axes[0, 1].set_ylabel('幅度 (dB)')
    axes[0, 1].axvline(f_on, color='gray', linestyle='--', alpha=0.5, label='真实频率')
    axes[0, 1].set_xlim(0, fs/2)
    axes[0, 1].set_ylim(-80, 5)
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].stem(n, x_off, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[1, 0].set_title(f'信号（f={f_off:.1f}Hz，偏离格点半格）')
    axes[1, 0].set_xlabel('n')
    axes[1, 0].grid(True, alpha=0.3)

    for (name, win), color in zip(windows.items(), ['C0', 'C1', 'C2', 'C3']):
        X = np.fft.fft(x_off * win)
        amp = np.abs(X[:N//2]) / (np.sum(win) / 2)
        axes[1, 1].plot(freqs, 20*np.log10(amp + 1e-10), color=color,
                        alpha=0.8, label=name, linewidth=1.5)
    axes[1, 1].set_title('各窗函数频谱（偏格点，矩形窗旁瓣最大，非矩形窗改善泄漏）')
    axes[1, 1].set_xlabel('频率 (Hz)')
    axes[1, 1].set_ylabel('幅度 (dB)')
    axes[1, 1].axvline(f_off, color='gray', linestyle='--', alpha=0.5, label='真实频率')
    axes[1, 1].set_xlim(0, fs/2)
    axes[1, 1].set_ylim(-80, 5)
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    X_rect = np.fft.fft(x_off)
    peak_amp = np.max(np.abs(X_rect[:N//2])) / (N / 2)
    print(f"  真实幅度 = 1.0（正弦波），矩形窗测量峰值幅度 ≈ {peak_amp:.4f}")
    print(f"  栅栏效应导致幅度低估约 {(1.0 - peak_amp) / 1.0 * 100:.1f}%")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo5_picket_fence.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 9：补零的效果——插值 vs 分辨率
# ============================================================
def demo9_zero_padding():
    """演示补零对频谱的影响：插值加密采样 vs 物理分辨率不变。"""
    print("=== 演示 9：补零的插值效果 vs 频率分辨率 ===")

    fs = 1000           # 采样率
    N_orig = 32         # 原始信号长度

    f_on_grid = 2 * fs / N_orig                     # 62.5 Hz（格点）
    f_off_grid = f_on_grid + fs / (2 * N_orig)      # 78.125 Hz（偏格点）

    n = np.arange(N_orig)
    x_on = np.sin(2 * np.pi * f_on_grid / fs * n)
    x_off = np.sin(2 * np.pi * f_off_grid / fs * n)

    N_list = [N_orig, N_orig * 4, N_orig * 16]
    colors = ['C0', 'C1', 'C2']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('补零效果：插值让曲线平滑，但不能分辨更近的频率', fontsize=13)

    axes[0, 0].stem(n, x_on, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title(f'信号（频率={f_on_grid:.1f}Hz，恰好在格点）')
    axes[0, 0].set_xlabel('n')
    axes[0, 0].grid(True, alpha=0.3)

    for N_pad, color in zip(N_list, colors):
        X = np.fft.fft(x_on, N_pad)
        freqs = np.fft.fftfreq(N_pad, 1/fs)[:N_pad//2]
        amp = np.abs(X[:N_pad//2]) / N_orig
        axes[1, 0].plot(freqs, amp, color=color, alpha=0.8,
                        label=f'补零到 {N_pad} 点 (Δf={fs/N_pad:.1f}Hz显示)')
    axes[1, 0].axvline(f_on_grid, color='r', linestyle='--', alpha=0.6, label='真实频率')
    axes[1, 0].set_title('补零后频谱（频率在格点，峰值精准）')
    axes[1, 0].set_xlabel('频率 (Hz)')
    axes[1, 0].set_xlim(0, 200)
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, alpha=0.3)

    axes[0, 1].stem(n, x_off, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 1].set_title(f'信号（频率={f_off_grid:.1f}Hz，偏离格点）')
    axes[0, 1].set_xlabel('n')
    axes[0, 1].grid(True, alpha=0.3)

    for N_pad, color in zip(N_list, colors):
        X = np.fft.fft(x_off, N_pad)
        freqs = np.fft.fftfreq(N_pad, 1/fs)[:N_pad//2]
        amp = np.abs(X[:N_pad//2]) / N_orig
        axes[1, 1].plot(freqs, amp, color=color, alpha=0.8,
                        label=f'补零到 {N_pad} 点')
    axes[1, 1].axvline(f_off_grid, color='r', linestyle='--', alpha=0.6, label='真实频率')
    axes[1, 1].set_title('补零后频谱（频率偏格点，峰值偏低=栅栏效应）')
    axes[1, 1].set_xlabel('频率 (Hz)')
    axes[1, 1].set_xlim(0, 200)
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    peak_on = [np.max(np.abs(np.fft.fft(x_on, N))) / N_orig for N in N_list]
    peak_off = [np.max(np.abs(np.fft.fft(x_off, N))) / N_orig for N in N_list]
    print(f"  频率在格点 - 各补零长度峰值幅度: {[f'{p:.4f}' for p in peak_on]}")
    print(f"  频率偏格点 - 各补零长度峰值幅度: {[f'{p:.4f}' for p in peak_off]}")
    print(f"  （在格点时幅度稳定≈0.5，偏格点时幅度偏低=栅栏效应）")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo2_zero_padding.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 10：循环卷积 vs 线性卷积
# ============================================================
def demo10_circular_vs_linear_conv():
    """演示循环卷积与线性卷积的区别，以及如何用补零法用 DFT 计算线性卷积。"""
    print("=== 演示 10：循环卷积 vs 线性卷积 ===")

    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([1.0, 1.0, 1.0, 1.0])
    N = len(a)  # 4

    # 方法 1：直接线性卷积
    y_linear = np.convolve(a, b)
    print(f"  线性卷积结果（长度={len(y_linear)}）: {y_linear}")

    # 方法 2：4 点循环卷积（不补零，产生混叠）
    A = np.fft.fft(a, N)
    B = np.fft.fft(b, N)
    y_circular = np.real(np.fft.ifft(A * B))
    print(f"  4点循环卷积结果（长度={N}）:     {np.round(y_circular, 6)}")

    # 方法 3：补零法计算线性卷积
    L = len(a) + len(b) - 1    # 正确长度 7
    A_pad = np.fft.fft(a, L)
    B_pad = np.fft.fft(b, L)
    y_linear_fft = np.real(np.fft.ifft(A_pad * B_pad))
    print(f"  补零DFT法（补零到{L}点）结果:    {np.round(y_linear_fft, 6)}")
    print(f"  补零DFT法 vs 直接线性卷积误差: {np.max(np.abs(y_linear - y_linear_fft)):.2e}")

    # 验证循环卷积 = 线性卷积的时域折叠
    y_folded = y_linear.copy()
    while len(y_folded) > N:
        overflow = y_folded[N:]
        y_folded = y_folded[:N]
        y_folded[:len(overflow)] += overflow
    print(f"  线性卷积折叠后（验证）:         {y_folded}")

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('循环卷积 vs 线性卷积：补零法可用 DFT 计算线性卷积', fontsize=13)

    axes[0, 0].stem(np.arange(N), a, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title('a[n] = [1,2,3,4]')
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].stem(np.arange(N), b, markerfmt='C1o', linefmt='C1-', basefmt='k-')
    axes[0, 1].set_title('b[n] = [1,1,1,1]')
    axes[0, 1].grid(True, alpha=0.3)

    axes[0, 2].stem(np.arange(len(y_linear)), y_linear,
                    markerfmt='C2o', linefmt='C2-', basefmt='k-')
    axes[0, 2].set_title(f'线性卷积（长度{len(y_linear)}）: {y_linear}')
    axes[0, 2].grid(True, alpha=0.3)

    axes[1, 0].stem(np.arange(N), y_circular,
                    markerfmt='C3o', linefmt='C3-', basefmt='k-')
    axes[1, 0].set_title(f'4点循环卷积: {np.round(y_circular).astype(int)}\n（有时域混叠）')
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].stem(np.arange(L), y_linear_fft,
                    markerfmt='C4o', linefmt='C4-', basefmt='k-')
    axes[1, 1].set_title(f'补零到{L}点后DFT法: {np.round(y_linear_fft).astype(int)}\n（=线性卷积）')
    axes[1, 1].grid(True, alpha=0.3)

    axes[1, 2].stem(np.arange(len(y_linear)), y_linear,
                    markerfmt='C0o', linefmt='C0-', basefmt='k-', label='线性卷积')
    axes[1, 2].axvline(N - 0.5, color='r', linestyle='--', label=f'N={N} 折叠边界')
    axes[1, 2].set_title('线性卷积超出N的部分\n"折叠"回前N个点→循环卷积')
    axes[1, 2].legend(fontsize=9)
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo3_dft_convolution.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 主程序：依次执行 10 组仿真演示
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("痛苦系列 DSP-02：DTFT 与 DFT 频域切片工程实践验证（全套 10 组演示）")
    print("=" * 60)

    print("\n--- 第一部分：DTFT 物理意义与性质 ---")
    demo1_single_frequency()
    demo2_symmetry()
    demo3_frequency_domain_filtering()
    demo4_convolution_theorem()
    demo5_rect_pulse_uncertainty()

    print("\n--- 第二部分：DFT 与工程采样幻象 ---")
    demo6_dft_vs_dtft()
    demo7_parseval_theorem()
    demo8_picket_fence()
    demo9_zero_padding()
    demo10_circular_vs_linear_conv()

    print("=" * 60)
    print("所有 10 组演示完成！图片已完整保存至 output/ 目录。")
    print("=" * 60)
