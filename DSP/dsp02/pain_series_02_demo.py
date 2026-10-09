"""
lesson4_dft_demo.py
第四课 DFT 工程实践演示

演示内容：
  1. DFT 是 DTFT 的频域采样（可视化两者关系）
  2. 补零的插值效果 vs 真实频率分辨率的区别
  3. 循环卷积 vs 线性卷积，补零得到线性卷积
  4. 帕斯瓦尔定理能量守恒验证
  5. 栅栏效应：频率在格点 vs 不在格点

运行方式（在项目根目录下）：
  python note/code/lesson4_dft_demo.py

依赖：
  pip install numpy matplotlib scipy
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os

matplotlib.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Heiti TC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 工具函数：手动计算 DTFT（从第三课复用）
# ============================================================
def compute_dtft(x, n, num_points=512):
    """计算序列 x[n] 的 DTFT，返回 (omega, X)。"""
    omega = np.linspace(-np.pi, np.pi, num_points)
    X = np.sum(x * np.exp(-1j * np.outer(omega, n)), axis=1)
    return omega, X


# ============================================================
# 演示 1：DFT 是 DTFT 的等间隔采样
# ============================================================
def demo1_dft_vs_dtft():
    """
    可视化 DFT 和 DTFT 的关系：
    DFT 的 N 个点就是 DTFT 连续曲线在 ω=2πk/N 处的采样值。
    """
    print("=== 演示 1：DFT 是 DTFT 的频域采样 ===")

    # 用矩形脉冲作为例子（DTFT 有解析表达式，便于对比）
    M = 3               # 矩形脉冲半宽
    N_dft = 16          # DFT 点数
    n_full = np.arange(-30, 31)
    x_full = (np.abs(n_full) <= M).astype(float)

    # 计算 DTFT（连续曲线）
    omega_cont, X_cont = compute_dtft(x_full, n_full, num_points=1024)

    # 计算 DFT（N 个离散点）
    # DFT 只能处理从 n=0 开始的序列，把矩形脉冲平移到 [0, N-1]
    x_dft = np.zeros(N_dft)
    for i, ni in enumerate(n_full):
        if 0 <= ni < N_dft:
            x_dft[ni] = x_full[i]
    X_dft = np.fft.fft(x_dft)           # NumPy 的 FFT 就是 DFT
    k = np.arange(N_dft)
    omega_dft = 2 * np.pi * k / N_dft   # DFT 频率点

    # 理论：DTFT 在这些点上的值（用平移后序列计算）
    n_shifted = np.arange(N_dft)
    X_dtft_at_dft = np.sum(
        x_dft * np.exp(-1j * np.outer(omega_dft, n_shifted)), axis=1
    )
    error = np.max(np.abs(np.abs(X_dft) - np.abs(X_dtft_at_dft)))
    print(f"  DFT 与 DTFT 采样值误差（应≈0）: {error:.2e}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('演示1：DFT 是 DTFT 的等间隔频域采样', fontsize=13)

    # 时域
    axes[0].stem(np.arange(N_dft), x_dft, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0].set_title(f'时域序列（矩形脉冲，N={N_dft}点）')
    axes[0].set_xlabel('n')
    axes[0].grid(True, alpha=0.3)

    # 频域对比
    # 把 DTFT 的频率轴映射到 [0, 2π]
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
    plt.savefig(os.path.join(OUTPUT_DIR, r'demo1_dft_vs_dtft.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 2：补零的效果——插值 vs 分辨率
# ============================================================
def demo2_zero_padding():
    """
    演示补零对频谱的影响：
    - 补零让频域采样更密（插值效果，曲线更平滑）
    - 但无法分辨两个相近频率（真实分辨率不变）
    """
    print("=== 演示 2：补零的插值效果 vs 频率分辨率 ===")

    fs = 1000           # 采样率
    N_orig = 32         # 原始信号长度

    # 场景 A：信号频率恰好在 DFT 格点上（100 Hz，Δf=31.25Hz时格点在96.875...不对）
    # 用 N=32，fs=1000，格点在 k*31.25 Hz
    # 让频率 = 2 * 31.25 = 62.5 Hz（在格点上）
    f_on_grid = 2 * fs / N_orig      # 恰好在格点上
    f_off_grid = f_on_grid + fs / (2 * N_orig)  # 偏移半个格点间距

    n = np.arange(N_orig)
    x_on = np.sin(2 * np.pi * f_on_grid / fs * n)
    x_off = np.sin(2 * np.pi * f_off_grid / fs * n)

    # 不同补零长度
    N_list = [N_orig, N_orig * 4, N_orig * 16]
    colors = ['C0', 'C1', 'C2']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('补零效果：插值让曲线平滑，但不能分辨更近的频率', fontsize=13)

    # 左列：频率在格点上
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

    # 右列：频率不在格点上（栅栏效应）
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

    # 定量：峰值幅度随补零量的变化（频率在格点时应为常数）
    peak_on = [np.max(np.abs(np.fft.fft(x_on, N))) / N_orig for N in N_list]
    peak_off = [np.max(np.abs(np.fft.fft(x_off, N))) / N_orig for N in N_list]
    print(f"  频率在格点 - 各补零长度峰值幅度: {[f'{p:.4f}' for p in peak_on]}")
    print(f"  频率偏格点 - 各补零长度峰值幅度: {[f'{p:.4f}' for p in peak_off]}")
    print(f"  （在格点时幅度应稳定≈0.5，偏格点时幅度偏低=栅栏效应）")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, r'demo2_zero_padding.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 3：循环卷积 vs 线性卷积
# ============================================================
def demo3_circular_vs_linear_conv():
    """
    演示循环卷积和线性卷积的区别，以及如何用补零法用 DFT 计算线性卷积。
    对应课文练习 3 的数值例子。
    """
    print("=== 演示 3：循环卷积 vs 线性卷积 ===")

    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([1.0, 1.0, 1.0, 1.0])
    N = len(a)  # 4

    # 方法 1：线性卷积（直接法）
    y_linear = np.convolve(a, b)
    print(f"  线性卷积结果（长度={len(y_linear)}）: {y_linear}")

    # 方法 2：4 点循环卷积（DFT 相乘，不补零）
    A = np.fft.fft(a, N)
    B = np.fft.fft(b, N)
    y_circular = np.real(np.fft.ifft(A * B))
    print(f"  4点循环卷积结果（长度={N}）:     {np.round(y_circular, 6)}")

    # 方法 3：补零法用 DFT 计算线性卷积
    L = len(a) + len(b) - 1    # 线性卷积的正确长度
    A_pad = np.fft.fft(a, L)
    B_pad = np.fft.fft(b, L)
    y_linear_fft = np.real(np.fft.ifft(A_pad * B_pad))
    print(f"  补零DFT法（补零到{L}点）结果:    {np.round(y_linear_fft, 6)}")
    print(f"  补零DFT法 vs 直接线性卷积误差: {np.max(np.abs(y_linear - y_linear_fft)):.2e}")

    # 解释循环卷积 = 线性卷积的时域折叠
    y_folded = y_linear.copy()
    while len(y_folded) > N:
        # 把超出 N 的部分折叠回来（时域混叠）
        overflow = y_folded[N:]
        y_folded = y_folded[:N]
        y_folded[:len(overflow)] += overflow
    print(f"  线性卷积折叠后（验证）:         {y_folded}")

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('循环卷积 vs 线性卷积：补零法可用 DFT 计算线性卷积', fontsize=13)

    # 时域信号
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

    # 循环卷积结果
    axes[1, 0].stem(np.arange(N), y_circular,
                    markerfmt='C3o', linefmt='C3-', basefmt='k-')
    axes[1, 0].set_title(f'4点循环卷积: {np.round(y_circular).astype(int)}\n（有时域混叠）')
    axes[1, 0].grid(True, alpha=0.3)

    # 补零后的 DFT 卷积
    axes[1, 1].stem(np.arange(L), y_linear_fft,
                    markerfmt='C4o', linefmt='C4-', basefmt='k-')
    axes[1, 1].set_title(f'补零到{L}点后DFT法: {np.round(y_linear_fft).astype(int)}\n（=线性卷积 ✓）')
    axes[1, 1].grid(True, alpha=0.3)

    # 示意图：循环卷积 = 线性卷积折叠
    axes[1, 2].stem(np.arange(len(y_linear)), y_linear,
                    markerfmt='C0o', linefmt='C0-', basefmt='k-', label='线性卷积')
    axes[1, 2].axvline(N - 0.5, color='r', linestyle='--', label=f'N={N} 折叠边界')
    axes[1, 2].set_title('线性卷积超出N的部分\n"折叠"回前N个点→循环卷积')
    axes[1, 2].legend(fontsize=9)
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, r'demo3_dft_convolution.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 4：帕斯瓦尔定理——时频能量守恒
# ============================================================
def demo4_parseval_theorem():
    """验证帕斯瓦尔定理：时域能量 = 频域能量（差1/N的归一化）。"""
    print("=== 演示 4：帕斯瓦尔定理能量守恒 ===")

    fs = 1000
    N = 256
    n = np.arange(N)
    # 多频率信号
    x = (np.sin(2*np.pi*100/fs*n) + 0.5*np.cos(2*np.pi*250/fs*n)
         + 0.3*np.sin(2*np.pi*400/fs*n))

    X = np.fft.fft(x)

    # 时域能量
    E_time = np.sum(np.abs(x)**2)
    # 频域能量（帕斯瓦尔定理：除以 N）
    E_freq = np.sum(np.abs(X)**2) / N
    error = abs(E_time - E_freq)

    print(f"  时域能量: {E_time:.6f}")
    print(f"  频域能量（÷N）: {E_freq:.6f}")
    print(f"  误差（应≈0）: {error:.2e}")

    # 频域能量分布
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
    plt.savefig(os.path.join(OUTPUT_DIR, r'demo4_parseval.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 演示 5：栅栏效应——频率在格点 vs 不在格点
# ============================================================
def demo5_picket_fence():
    """
    演示栅栏效应：
    - 频率恰好在 DFT 格点时：幅度准确，旁瓣为零
    - 频率偏离格点时：幅度被低估，出现旁瓣（能量泄漏）
    并展示如何用不同窗函数改善泄漏。
    """
    print("=== 演示 5：栅栏效应与频谱泄漏 ===")

    fs = 1000
    N = 64

    # 格点频率（恰好是 fs/N 的整数倍）
    f_on = 5 * fs / N       # 第 5 个格点
    # 非格点频率（偏移半个格点）
    f_off = 5.5 * fs / N

    n = np.arange(N)
    x_on = np.sin(2 * np.pi * f_on / fs * n)
    x_off = np.sin(2 * np.pi * f_off / fs * n)

    # 不同窗函数
    windows = {
        '矩形窗（无窗）': np.ones(N),
        '汉宁窗': np.hanning(N),
        '汉明窗': np.hamming(N),
        '布莱克曼窗': np.blackman(N),
    }

    freqs = np.fft.fftfreq(N, 1/fs)[:N//2]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('栅栏效应与窗函数改善：非格点频率的频谱泄漏', fontsize=13)

    # 上行：频率在格点
    axes[0, 0].stem(n, x_on, markerfmt='C0o', linefmt='C0-', basefmt='k-')
    axes[0, 0].set_title(f'信号（f={f_on:.1f}Hz，在格点）')
    axes[0, 0].set_xlabel('n')
    axes[0, 0].grid(True, alpha=0.3)

    for (name, win), color in zip(windows.items(), ['C0', 'C1', 'C2', 'C3']):
        X = np.fft.fft(x_on * win)
        # 归一化：除以窗函数之和（使幅度可比）
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

    # 下行：频率偏格点
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

    # 定量：偏格点时矩形窗的最大幅度误差
    X_rect = np.fft.fft(x_off)
    peak_amp = np.max(np.abs(X_rect[:N//2])) / (N / 2)
    print(f"  真实幅度 = 1.0（正弦波），矩形窗测量峰值幅度 ≈ {peak_amp:.4f}")
    print(f"  栅栏效应导致幅度低估约 {(1.0 - peak_amp) / 1.0 * 100:.1f}%")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, r'demo5_picket_fence.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print()


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    # os.makedirs handled above

    print("=" * 55)
    print("第四课 DFT 工程实践演示")
    print("=" * 55)
    demo1_dft_vs_dtft()
    demo2_zero_padding()
    demo3_circular_vs_linear_conv()
    demo4_parseval_theorem()
    demo5_picket_fence()
    print("=" * 55)
    print("所有演示完成！图片已保存到 output/ 目录。")

