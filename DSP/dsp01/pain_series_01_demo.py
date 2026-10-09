"""
痛苦系列 01 配套实验代码：采样定理、混叠效应与时域卷积和
"""
import os
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Songti SC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def demo1_sampling_and_aliasing():
    """演示奈奎斯特采样定理与混叠现象"""
    # 原始连续信号：包含 10Hz 与 40Hz 成分
    t_continuous = np.linspace(0, 0.2, 2000)
    f1, f2 = 10, 40
    x_continuous = np.sin(2 * np.pi * f1 * t_continuous) + 0.5 * np.sin(2 * np.pi * f2 * t_continuous)

    # 充足采样：Fs = 200 Hz (> 2 * 40 Hz)
    fs_high = 200
    t_high = np.arange(0, 0.2, 1 / fs_high)
    x_high = np.sin(2 * np.pi * f1 * t_high) + 0.5 * np.sin(2 * np.pi * f2 * t_high)

    # 欠采样混叠：Fs = 50 Hz (< 2 * 40 Hz, 40Hz 将混叠为 |40 - 50| = 10Hz)
    fs_low = 50
    t_low = np.arange(0, 0.2, 1 / fs_low)
    x_low = np.sin(2 * np.pi * f1 * t_low) + 0.5 * np.sin(2 * np.pi * f2 * t_low)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6))

    axes[0].plot(t_continuous, x_continuous, 'gray', alpha=0.6, label='原始连续信号 (10Hz + 40Hz)')
    axes[0].stem(t_high, x_high, linefmt='b-', markerfmt='bo', basefmt='k-', label='充足采样 (Fs = 200 Hz)')
    axes[0].set_title('充足采样：Fs = 200Hz > 2 * Fmax（保留原始波形形态）')
    axes[0].set_xlabel('时间 (s)')
    axes[0].set_ylabel('幅度')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].legend()

    axes[1].plot(t_continuous, x_continuous, 'gray', alpha=0.6, label='原始连续信号 (10Hz + 40Hz)')
    axes[1].stem(t_low, x_low, linefmt='r-', markerfmt='ro', basefmt='k-', label='欠采样混叠 (Fs = 50 Hz)')
    # 重构出的伪造低频波形
    axes[1].plot(t_continuous, 1.5 * np.sin(2 * np.pi * 10 * t_continuous), 'r--', alpha=0.8, label='混叠后的伪造信号 (40Hz 混叠为 10Hz)')
    axes[1].set_title('欠采样混叠：Fs = 50Hz < 2 * 40Hz（高频 40Hz 伪装成 10Hz 低频）')
    axes[1].set_xlabel('时间 (s)')
    axes[1].set_ylabel('幅度')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo1_sampling_aliasing.png'), dpi=150)
    plt.close()
    print("Demo 1: 采样与混叠图表已保存")

def demo2_impulse_and_echo_convolution():
    """演示单位脉冲响应与空谷回声卷积合成"""
    # 输入信号：在第 0, 2, 4 秒喊了三声号子
    x = np.array([1.0, 0.0, 1.5, 0.0, 0.8, 0.0, 0.0, 0.0])
    # 山谷脉冲响应：原声 + 1秒后一次回声(0.5) + 2秒后二次回声(0.25)
    h = np.array([1.0, 0.5, 0.25])

    # 卷积计算
    y = np.convolve(x, h)
    n_x = np.arange(len(x))
    n_h = np.arange(len(h))
    n_y = np.arange(len(y))

    fig, axes = plt.subplots(3, 1, figsize=(10, 7))

    axes[0].stem(n_x, x, linefmt='b-', markerfmt='bo', basefmt='k-')
    axes[0].set_title('输入序列 x[n]：喊号子信号')
    axes[0].set_ylabel('响度')
    axes[0].grid(True, linestyle='--', alpha=0.5)

    axes[1].stem(n_h, h, linefmt='g-', markerfmt='go', basefmt='k-')
    axes[1].set_title('系统单位脉冲响应 h[n]：山谷回声衰减特性')
    axes[1].set_ylabel('衰减系数')
    axes[1].grid(True, linestyle='--', alpha=0.5)

    axes[2].stem(n_y, y, linefmt='r-', markerfmt='ro', basefmt='k-')
    axes[2].set_title('卷积输出 y[n] = x[n] * h[n]：耳朵听到的原声与历史回声干涉叠加结果')
    axes[2].set_xlabel('离散时间点 n')
    axes[2].set_ylabel('总响度')
    axes[2].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'demo2_echo_convolution.png'), dpi=150)
    plt.close()
    print("Demo 2: 回声卷积图表已保存")

if __name__ == '__main__':
    demo1_sampling_and_aliasing()
    demo2_impulse_and_echo_convolution()
    print("痛苦系列 01 Demo 全部运行成功！")
