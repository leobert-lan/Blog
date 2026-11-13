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
    """demo1 - 四种对称窗函数的时域形态与频域主瓣/旁瓣特性对比"""
    L = 51  # 抽头长度 L=51，阶数 N=50
    w_rect = signal.windows.boxcar(L)
    w_hann = signal.windows.hann(L)
    w_hamm = signal.windows.hamming(L)
    w_black = signal.windows.blackman(L)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8))

    # 左图：时域形态
    n = np.arange(L)
    ax1.plot(n, w_rect, label='矩形窗 (端点 = 1.00)', marker='.', markersize=4)
    ax1.plot(n, w_hann, label='汉宁窗 (端点 = 0.00)', marker='.', markersize=4)
    ax1.plot(n, w_hamm, label='汉明窗 (端点 = 0.08)', marker='.', markersize=4)
    ax1.plot(n, w_black, label='布莱克曼窗 (端点 = 0.00)', marker='.', markersize=4)
    ax1.set_title(f'窗函数的时域形态 (抽头长度 L={L}, 阶数 N={L-1})')
    ax1.set_xlabel('样本序号 n')
    ax1.set_ylabel('窗权重 w[n]')
    ax1.set_ylim([-0.05, 1.08])
    ax1.legend(loc='center right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：频域幅度谱（横轴严格对齐归一化角频率 ω/π ∈ [0, 1]）
    n_fft = 8192
    omega_over_pi = np.linspace(0.0, 1.0, n_fft // 2 + 1)
    for w, name in zip(
        [w_rect, w_hann, w_hamm, w_black],
        ['矩形窗', '汉宁窗', '汉明窗', '布莱克曼窗']
    ):
        W = np.fft.rfft(w, n_fft)
        W_dB = 20.0 * np.log10(np.maximum(np.abs(W) / np.max(np.abs(W)), 1e-12))
        ax2.plot(omega_over_pi, W_dB, label=name, linewidth=1.6)

    ax2.set_title('窗函数的归一化幅度谱：主瓣宽度与峰值旁瓣电平的折中')
    ax2.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel('归一化幅度 (dB)')
    ax2.set_ylim([-100, 2])
    ax2.set_xlim([0.0, 0.30])
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_01_windows_raw.png'), dpi=150)
    plt.close()


def demo2_fir_window_design():
    """demo2 - 窗函数法设计低通 FIR，四种窗函数的频率响应对比"""
    L = 51  # 抽头长度 L=51，阶数 N=50
    fc = 0.4  # 归一化截止频率 ω_c / π = 0.4

    b_rect = signal.firwin(L, fc, window='boxcar')
    b_hann = signal.firwin(L, fc, window='hann')
    b_hamm = signal.firwin(L, fc, window='hamming')
    b_black = signal.firwin(L, fc, window='blackman')

    plt.figure(figsize=(10, 5.8))
    for b, name in zip(
        [b_rect, b_hann, b_hamm, b_black],
        ['矩形窗', '汉宁窗', '汉明窗', '布莱克曼窗']
    ):
        w, h = signal.freqz(b, worN=4096)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        plt.plot(w / np.pi, mag_db, label=name, linewidth=1.6)

    plt.axvline(fc, color='crimson', linestyle='--', alpha=0.6, label='理想截止频率 ωc = 0.4π')
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


def demo3_gibbs_effect():
    """demo3 - 矩形窗直接截断的吉布斯效应：抽头长度 L 增加时约 8.95% 过冲极限不消失"""
    fc = 0.4  # 对应 ω_c = 0.4π，阶跃高度 Δ = 1
    # scale=False 严格对应理论公式 h[n] = h_d[n - τ] * w_rect[n]，不做额外直流重缩放
    b_21 = signal.firwin(21, fc, window='boxcar', scale=False)
    b_101 = signal.firwin(101, fc, window='boxcar', scale=False)
    b_501 = signal.firwin(501, fc, window='boxcar', scale=False)

    plt.figure(figsize=(10, 5.8))
    for b, label in zip(
        [b_21, b_101, b_501],
        ['L=21 (阶数 N=20)', 'L=101 (阶数 N=100)', 'L=501 (阶数 N=500)']
    ):
        w, h = signal.freqz(b, worN=8192)
        plt.plot(w / np.pi, np.abs(h), label=label, linewidth=1.6)

    plt.axvline(fc, color='black', linestyle='--', linewidth=1.2, label='理想截止边界 ωc = 0.4π')
    plt.axhline(1.08949, color='gray', linestyle=':', linewidth=1.2, label='吉布斯过冲理论极限 ≈ 1.0895')
    plt.title('吉布斯效应：增加抽头长度 L 只能压缩过渡带，无法消除约 8.95% 的边缘过冲')
    plt.xlabel('归一化角频率 ω/π (×π rad/sample)')
    plt.ylabel(r'线性幅度 $|H(e^{j\omega})|$')
    plt.xlim([0.2, 0.6])
    plt.ylim([-0.03, 1.16])
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_03_gibbs.png'), dpi=150)
    plt.close()


def demo4_linear_phase_verify():
    """demo4 - 偶对称 Type I FIR 线性相位验证：通带严格直线、阻带过零 π 跳变与恒定群延迟 (L-1)/2"""
    L = 51  # 抽头长度 L=51，阶数 N=50，理论群延迟 τ = (L-1)/2 = 25
    tau = (L - 1) / 2.0
    fc = 0.4
    b = signal.firwin(L, fc, window='hamming')

    w, h = signal.freqz(b, worN=2048)
    phase = np.unwrap(np.angle(h))
    w_gd, gd = signal.group_delay((b, 1), w=1024)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8))

    # 左图：相位响应（标出通带与阻带，展示阻带内实幅度变号引发的 π 相位跳变）
    ax1.axvspan(0.0, 0.40, color='seagreen', alpha=0.08, label=r'通带区间 (严格直线 $-\omega\tau$)')
    ax1.axvspan(0.47, 1.00, color='indianred', alpha=0.08, label=r'阻带区间 (过零变号产生 $\pi$ 跳变)')
    ax1.plot(w / np.pi, phase, color='royalblue', linewidth=1.6, label=r'实际解缠相位 $\angle H(e^{j\omega})$')
    ax1.plot(w / np.pi, -w * tau, color='gray', linestyle='--', linewidth=1.2, alpha=0.8, label=r'连续线性基准 $-25\omega$')
    ax1.set_title(f'相位响应：通带严格线性，阻带过零伴随 π 跳变 (L={L})')
    ax1.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax1.set_ylabel('相位 (rad)')
    ax1.set_xlim([0.0, 1.0])
    ax1.legend(loc='upper right', fontsize=9.5)
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


def demo5_type2_highpass_fail():
    """
    demo5 - 三线同框对比：
      1. Type I  (L=51, 奇数偶对称): 通带直达 ω=π，且通带相移偏置 θ0 = 0°
      2. Type II (L=50, 偶数偶对称): 受结构零点约束，在 ω=π 处被强制拉回 0
      3. Type IV (L=50, 偶数奇对称, (-1)^n 调制): 幅频在 ω=π 处可达 1，但附带 +90° 希尔伯特相移
    """
    # 1. Type I: L=51 (奇数抽头, 偶对称)
    L1 = 51
    tau1 = (L1 - 1) / 2.0
    b_type1 = signal.firwin(L1, 0.5, pass_zero=False, window='hamming')

    # 2. 真正的 Type II 高通候选序列: L=50 (偶数抽头, 偶对称)
    # 将截止频率 ωc = 0.5π 的理想高通冲激响应中心平移至 τ2 = 24.5 后乘对称汉明窗
    L2 = 50
    tau2 = (L2 - 1) / 2.0  # 24.5
    m = np.arange(L2) - tau2
    h_hp_ideal = (np.sin(np.pi * m) - np.sin(0.5 * np.pi * m)) / (np.pi * m)
    b_type2 = h_hp_ideal * signal.windows.hamming(L2)

    # 3. Type IV 序列: L=50 (偶数抽头, 奇对称) —— 对 Type II 低通乘以 (-1)^n 频谱搬移得到
    b_lp_type2 = signal.firwin(L2, 0.5, window='hamming')
    b_type4 = b_lp_type2 * ((-1) ** np.arange(L2))

    w1, h1 = signal.freqz(b_type1, worN=2048)
    w2, h2 = signal.freqz(b_type2, worN=2048)
    w4, h4 = signal.freqz(b_type4, worN=2048)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：幅频响应三线同框
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

    # 右图：通带区间 [0.58π, 0.96π] 剥离线性延迟 e^{-jωτ} 后的常数相位偏置 θ0（度）
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


def demo6_parks_mcclellan():
    """
    demo6 - Parks-McClellan 等波纹逼近 vs 窗函数法双维度对比：
      左图：相同抽头数 (L=51, N=50) 下的过渡带与误差预算分布对比
      右图：相同设计指标 (通带 [0, 0.3π] 误差 ≤ 0.01, 阻带 [0.4π, π] 衰减 ≥ 50 dB) 下的最小抽头数实测对比
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # --- 左图：固定抽头数 L=51 (阶数 N=50) ---
    L_fixed = 51
    bands = [0.0, 0.3, 0.4, 1.0]
    desired = [1, 0]
    b_remez_51 = signal.remez(L_fixed, bands, desired, weight=[1.0, 1.0], fs=2.0)
    b_hamm_51 = signal.firwin(L_fixed, 0.35, window='hamming')

    w_r51, h_r51 = signal.freqz(b_remez_51, worN=4096)
    w_h51, h_h51 = signal.freqz(b_hamm_51, worN=4096)

    ax1.axvspan(0.0, 0.3, color='seagreen', alpha=0.08, label='目标通带 [0, 0.3π]')
    ax1.axvspan(0.4, 1.0, color='indianred', alpha=0.08, label='目标阻带 [0.4π, π]')
    ax1.plot(w_h51 / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_h51), 1e-12)),
             label='汉明窗法 (L=51, N=50)', color='darkorange', linewidth=1.6)
    ax1.plot(w_r51 / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_r51), 1e-12)),
             label='等权重 Remez (L=51, W=[1, 1])', color='royalblue', linewidth=1.6)
    ax1.set_title('固定抽头数 (L=51)：误差预算分配与过渡带陡度对比')
    ax1.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_ylim([-100, 8])
    ax1.set_xlim([0.0, 1.0])
    ax1.legend(loc='upper right', fontsize=9.2)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- 右图：固定指标 (δp ≤ 0.01, 阻带 ≤ -50 dB) 实测最小奇数抽头数 ---
    delta_p = 0.01
    delta_s = 10.0 ** (-50.0 / 20.0)  # ≈ 0.003162
    weights = [1.0, delta_p / delta_s]  # ≈ [1.0, 3.162]

    # 搜索达标的最小奇数抽头数
    L_hamm_min = None
    for L_cand in range(31, 101, 2):
        bh = signal.firwin(L_cand, 0.35, window='hamming')
        w, hh = signal.freqz(bh, worN=8192)
        fn = w / np.pi
        if np.max(np.abs(np.abs(hh[fn <= 0.3]) - 1.0)) <= delta_p and np.max(np.abs(hh[fn >= 0.4])) <= delta_s:
            L_hamm_min = L_cand
            b_hamm_spec = bh
            break

    L_remez_min = None
    for L_cand in range(21, 101, 2):
        br = signal.remez(L_cand, bands, desired, weight=weights, fs=2.0)
        w, hr = signal.freqz(br, worN=8192)
        fn = w / np.pi
        if np.max(np.abs(np.abs(hr[fn <= 0.3]) - 1.0)) <= delta_p and np.max(np.abs(hr[fn >= 0.4])) <= delta_s:
            L_remez_min = L_cand
            b_remez_spec = br
            break

    w_hs, h_hs = signal.freqz(b_hamm_spec, worN=4096)
    w_rs, h_rs = signal.freqz(b_remez_spec, worN=4096)

    ax2.axvspan(0.0, 0.3, color='seagreen', alpha=0.08)
    ax2.axvspan(0.4, 1.0, color='indianred', alpha=0.08)
    ax2.axhline(-50.0, color='crimson', linestyle=':', linewidth=1.2, label='阻带指标线 -50 dB')
    ax2.plot(w_hs / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_hs), 1e-12)),
             label=f'汉明窗达标最小长度：L={L_hamm_min} (阶数 N={L_hamm_min-1})',
             color='darkorange', linewidth=1.6)
    ax2.plot(w_rs / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_rs), 1e-12)),
             label=f'加权 Remez 达标最小长度：L={L_remez_min} (阶数 N={L_remez_min-1}, W=[1, 3.16])',
             color='royalblue', linewidth=1.6)
    ax2.set_title('固定指标 (δp≤0.01, 阻带≤-50dB)：达标所需最小抽头数实测')
    ax2.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_ylim([-100, 8])
    ax2.set_xlim([0.0, 1.0])
    ax2.legend(loc='upper right', fontsize=9.0)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_06_remez.png'), dpi=150)
    plt.close()


if __name__ == '__main__':
    print("Generating DSP-04 FIR Filter Design Figures...")
    demo1_window_comparison()
    demo2_fir_window_design()
    demo3_gibbs_effect()
    demo4_linear_phase_verify()
    demo5_type2_highpass_fail()
    demo6_parks_mcclellan()
    print("Done. Figures saved in:", OUTPUT_DIR)
