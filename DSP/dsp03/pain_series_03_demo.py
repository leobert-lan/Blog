"""
pain_series_03_demo.py
DSP 痛苦系列 03 博客配套代码：Z变换与系统命运的零极点

运行方式（在项目根目录下）：
  python blog/code/pain_series_03_demo.py

依赖：
  pip install numpy matplotlib scipy
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import signal
import os

# ==========================================
# 字体设置（兼容 Windows, macOS, Linux）
# 避免中文在绘图时显示为方块
# ==========================================
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Heiti TC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 确保输出目录存在
output_dir = OUTPUT_DIR
os.makedirs(output_dir, exist_ok=True)


def demo1_divergent_signal():
    """
    Demo 1：拯救发散信号
    展示 DTFT 为什么无法处理发散信号，以及 Z变换中的衰减因子是如何将其强行压制的。
    """
    print("正在生成 Demo 1: 拯救发散信号...")
    n = np.arange(0, 30)
    
    # 创造一个正反馈爆炸信号，例如 x[n] = (1.2)^n
    x = 1.2**n
    
    plt.figure(figsize=(15, 5))
    
    # 1. 时域原信号
    plt.subplot(131)
    plt.stem(n, x, basefmt=" ")
    plt.title("原始信号 (指数爆炸)")
    plt.xlabel("n (时间步)")
    plt.ylabel("幅度")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # 2. 累加求和 (模拟未加衰减的求和发散)
    # DTFT 公式本质是求和，如果不收敛，数值会溢出
    plt.subplot(132)
    plt.plot(n, np.cumsum(x), color='red', marker='o')
    plt.title("直接级数求和 (DTFT 无法收敛)")
    plt.xlabel("n (时间步)")
    plt.ylabel("无穷大的累加值")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # 3. Z变换抢救 (乘上衰减因子 r^(-n), r=1.5)
    r = 1.5
    r_n = r**(-n)
    x_z = x * r_n
    plt.subplot(133)
    plt.stem(n, x_z, basefmt=" ")
    plt.title(f"乘以衰减因子 r={r} (被成功压制收敛)")
    plt.xlabel("n (时间步)")
    plt.ylabel("幅度 (被衰减)")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'demo1_divergent_signal.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")


def demo2_3d_zplane():
    """
    Demo 2：上帝视角的 3D 零极点曲面
    画出复平面上的幅度响应，直观看到极点(山峰)、零点(黑洞)以及单位圆上的截面(频率响应)。
    """
    print("正在生成 Demo 2: 上帝视角的 3D 零极点曲面...")
    
    # 设定一对共轭极点：半径 r=0.8，角度 ±pi/4
    r_pole = 0.8
    omega_pole = np.pi / 4
    p1 = r_pole * np.exp(1j * omega_pole)
    p2 = r_pole * np.exp(-1j * omega_pole)
    
    # 设定一对共轭零点：放在单位圆上，角度 ±pi/2 (阻断高频)
    z1 = np.exp(1j * np.pi / 2)
    z2 = np.exp(-1j * np.pi / 2)
    
    # 构造复平面网格
    x = np.linspace(-1.5, 1.5, 200)
    y = np.linspace(-1.5, 1.5, 200)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y
    
    # 计算传递函数 H(z) 的幅度 = |(z-z1)(z-z2)| / |(z-p1)(z-p2)|
    # 避免分母出现绝对的零导致报错，加个极小值
    epsilon = 1e-6
    num = np.abs((Z - z1) * (Z - z2))
    den = np.abs((Z - p1) * (Z - p2)) + epsilon
    Mag = num / den
    
    # 将极点处无限大的幅度截断，否则画出来的山峰会遮挡一切
    Mag = np.clip(Mag, 0, 8)
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制 3D 曲面
    surf = ax.plot_surface(X, Y, Mag, cmap='plasma', alpha=0.8, edgecolor='none')
    
    # 绘制 Z 平面上的单位圆 |z|=1 以及它对应的频率响应高度
    theta = np.linspace(0, 2*np.pi, 200)
    uc_x = np.cos(theta)
    uc_y = np.sin(theta)
    uc_z = uc_x + 1j * uc_y
    uc_mag = np.abs((uc_z - z1)*(uc_z - z2)) / (np.abs((uc_z - p1)*(uc_z - p2)) + epsilon)
    
    ax.plot(uc_x, uc_y, uc_mag, color='cyan', linewidth=4, label='单位圆截面 (频率响应 DTFT)')
    
    # 在底面画一个单位圆的阴影，辅助参考
    ax.plot(uc_x, uc_y, np.zeros_like(uc_mag), color='black', linestyle='--', linewidth=2, label='单位圆轨迹 |z|=1')
    
    ax.set_title("Z 平面：零点(黑洞)与极点(山峰)塑造的频率响应")
    ax.set_xlabel("实部 (Real)")
    ax.set_ylabel("虚部 (Imaginary)")
    ax.set_zlabel("幅度 |H(z)|")
    ax.legend(loc='upper right')
    
    # 调整视角让山峰和曲线更好看
    ax.view_init(elev=35, azim=-45)
    
    save_path = os.path.join(output_dir, 'demo2_3d_zplane.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")


def demo3_poles_movement():
    """
    Demo 3：极点的越狱与系统的毁灭
    展示当极点随着半径 r 变大，越过单位圆边界时，时域冲激响应的变化。
    """
    print("正在生成 Demo 3: 极点的越狱与系统毁灭...")
    n = np.arange(0, 80)
    # 输入为单位冲激信号 delta[n]
    delta = np.zeros_like(n)
    delta[0] = 1
    
    plt.figure(figsize=(15, 5))
    
    # 设置一个共轭极点，频率固定为 pi/8，只改变半径 r
    omega = np.pi / 8
    
    # 场景A：极点在圆内 (r=0.9) - 稳定
    r1 = 0.95
    # 分母多项式展开: (1 - p*z^-1)(1 - p^*z^-1) = 1 - 2r*cos(w)z^-1 + r^2*z^-2
    a1 = [1, -2*r1*np.cos(omega), r1**2]
    h1 = signal.lfilter([1], a1, delta)
    plt.subplot(131)
    plt.stem(n, h1, basefmt=" ")
    plt.title(f"圆内 (r={r1}): 能量衰减，系统稳定")
    plt.xlabel("n (时间)")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # 场景B：极点在圆上 (r=1.0) - 边缘震荡
    r2 = 1.0
    a2 = [1, -2*r2*np.cos(omega), r2**2]
    h2 = signal.lfilter([1], a2, delta)
    plt.subplot(132)
    plt.stem(n, h2, basefmt=" ")
    plt.title(f"圆上 (r={r2}): 永不衰减，边缘震荡")
    plt.xlabel("n (时间)")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # 场景C：极点在圆外 (r=1.05) - 系统毁灭
    r3 = 1.05
    a3 = [1, -2*r3*np.cos(omega), r3**2]
    h3 = signal.lfilter([1], a3, delta)
    plt.subplot(133)
    plt.stem(n, h3, basefmt=" ")
    plt.title(f"圆外 (r={r3}): 指数爆炸，系统毁灭")
    plt.xlabel("n (时间)")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'demo3_poles_movement.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")

def demo4_roc_visual():
    """
    Demo 4：收敛域（ROC）的可视化
    展示因果稳定、反果不稳定、双边信号的 ROC 区域与单位圆的关系。
    """
    print("正在生成 Demo 4: 收敛域(ROC)的可视化...")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 辅助画图函数
    def draw_zplane(ax, title, poles, roc_type, roc_radius):
        ax.set_title(title)
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.axhline(0, color='black', lw=1)
        ax.axvline(0, color='black', lw=1)
        ax.set_aspect('equal')
        
        # 画单位圆
        unit_circle = plt.Circle((0, 0), 1, color='blue', fill=False, linestyle='--', lw=2, label='单位圆 |z|=1')
        ax.add_patch(unit_circle)
        
        # 极点
        for p in poles:
            ax.plot(np.real(p), np.imag(p), 'rx', markersize=10, markeredgewidth=2, label='极点' if p==poles[0] else "")
            # 极点所在的圆
            r_circle = plt.Circle((0, 0), np.abs(p), color='red', fill=False, linestyle='-.', lw=1)
            ax.add_patch(r_circle)
            
        # 阴影区域 (ROC)
        if roc_type == 'outside':
            # 外域，画一个大圆减去小圆 (近似)
            roc_patch = plt.Circle((0, 0), 3, color='gray', alpha=0.3)
            ax.add_patch(roc_patch)
            white_patch = plt.Circle((0, 0), roc_radius[0], color='white')
            ax.add_patch(white_patch)
            ax.text(1.2, 1.2, 'ROC: |z| > r\n(包围单位圆=稳定)', color='gray')
        elif roc_type == 'inside':
            roc_patch = plt.Circle((0, 0), roc_radius[0], color='gray', alpha=0.3)
            ax.add_patch(roc_patch)
            ax.text(0.1, 0.1, 'ROC: |z| < r\n(错过单位圆=不稳定)', color='gray')
        elif roc_type == 'ring':
            roc_patch = plt.Circle((0, 0), roc_radius[1], color='gray', alpha=0.3)
            ax.add_patch(roc_patch)
            white_patch = plt.Circle((0, 0), roc_radius[0], color='white')
            ax.add_patch(white_patch)
            ax.text(0.8, 1.2, 'ROC: r1 < |z| < r2\n(双边信号)', color='gray')

        ax.legend(loc='lower right', fontsize=8)

    # 1. 因果稳定系统 (极点 r=0.8)
    draw_zplane(axes[0], "因果+稳定 (向外收敛)", [0.8 + 0j], 'outside', [0.8])
    
    # 2. 反果不稳定系统 (极点 r=0.8)
    draw_zplane(axes[1], "反因果+不稳定 (向内收敛)", [0.8 + 0j], 'inside', [0.8])
    
    # 3. 双边信号 (极点 r=0.5 和 r=1.2)
    draw_zplane(axes[2], "双边信号 (环状收敛)", [0.5, 1.2], 'ring', [0.5, 1.2])
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'demo4_roc_visual.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")


def demo5_notch_filter():
    """
    Demo 5：50Hz 工频陷波器实战
    展示如何通过在单位圆上放置零点来滤除特定频率的干扰。
    """
    print("正在生成 Demo 5: 50Hz陷波器除噪实战...")
    fs = 1000  # 采样率 1000Hz
    t = np.arange(0, 1, 1/fs)  # 1秒
    
    # 构造信号：5Hz有用波 + 50Hz干扰波
    signal_clean = np.sin(2 * np.pi * 5 * t)
    noise = 1.5 * np.sin(2 * np.pi * 50 * t)
    signal_noisy = signal_clean + noise
    
    # 设计陷波器：50Hz 对应的角频率 w = 2*pi*50/1000 = 0.1*pi
    w0 = 2 * np.pi * 50 / fs
    # 在单位圆上放置零点 (彻底消除 50Hz)
    z1 = np.exp(1j * w0)
    z2 = np.exp(-1j * w0)
    # 在稍微靠内的位置放置极点 (使得陷波器带宽变窄，不影响其他频率)
    r = 0.95
    p1 = r * np.exp(1j * w0)
    p2 = r * np.exp(-1j * w0)
    
    # 构造传递函数系数
    b = np.poly([z1, z2])
    a = np.poly([p1, p2])
    
    # 滤波
    signal_filtered = signal.lfilter(b, a, signal_noisy)
    
    fig = plt.figure(figsize=(15, 5))
    
    # 1. 零极点图
    ax1 = fig.add_subplot(131)
    ax1.set_title("上帝视角：零极点布局")
    unit_circle = plt.Circle((0,0), 1, color='blue', fill=False, linestyle='--')
    ax1.add_patch(unit_circle)
    ax1.plot(np.real([z1, z2]), np.imag([z1, z2]), 'bo', fillstyle='none', markersize=10, label='零点 (黑洞, 砸在50Hz)')
    ax1.plot(np.real([p1, p2]), np.imag([p1, p2]), 'rx', markersize=10, label='极点 (约束带宽)')
    ax1.set_xlim(-1.2, 1.2)
    ax1.set_ylim(-1.2, 1.2)
    ax1.set_aspect('equal')
    ax1.axhline(0, color='black', lw=0.5)
    ax1.axvline(0, color='black', lw=0.5)
    ax1.legend(loc='lower right', fontsize=8)
    
    # 2. 频率响应
    w, h = signal.freqz(b, a, worN=800)
    freq = w * fs / (2 * np.pi)
    ax2 = fig.add_subplot(132)
    ax2.plot(freq, 20 * np.log10(abs(h)), 'b')
    ax2.set_title("系统频响：50Hz 处的深坑")
    ax2.set_ylabel("幅度 (dB)")
    ax2.set_xlabel("频率 (Hz)")
    ax2.axvline(50, color='red', linestyle='--', alpha=0.5, label='50Hz')
    ax2.set_xlim(0, 100)
    ax2.grid(True)
    ax2.legend()
    
    # 3. 时域滤波效果对比
    ax3 = fig.add_subplot(133)
    ax3.plot(t[:200], signal_noisy[:200], color='gray', alpha=0.7, label='原始污染信号')
    ax3.plot(t[:200], signal_filtered[:200], color='red', linewidth=2, label='滤波后信号(恢复5Hz)')
    ax3.set_title("时域效果展示")
    ax3.set_xlabel("时间 (s)")
    ax3.legend()
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'demo5_notch_filter.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")


def demo6_pole_zero_interaction():
    """
    Demo 6：零极点相杀 (零点对极点的阻击)
    展示当零点靠近极点时，如何破坏极点产生的谐振峰。
    """
    print("正在生成 Demo 6: 零极点相杀...")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    w0 = np.pi / 4  # 45度
    
    # 系统 A：只有极点 (r=0.95)，会产生强烈的尖峰
    p_only = [0.95 * np.exp(1j * w0), 0.95 * np.exp(-1j * w0)]
    a_sys_a = np.poly(p_only)
    b_sys_a = [1]
    
    w_a, h_a = signal.freqz(b_sys_a, a_sys_a, worN=512)
    axes[0].plot(w_a / np.pi, np.abs(h_a), 'r', lw=2)
    axes[0].set_title("系统 A：纯极点引发巨大谐振")
    axes[0].set_ylabel("幅度")
    axes[0].set_xlabel("频率 (x π rad/sample)")
    axes[0].grid(True)
    axes[0].text(0.25, np.max(np.abs(h_a))*0.8, '极点山峰\n(接近单位圆)', color='red')

    # 系统 B：极点相同，但在同角度的单位圆上放置零点
    z_sys_b = [np.exp(1j * w0), np.exp(-1j * w0)]
    b_sys_b = np.poly(z_sys_b)
    
    w_b, h_b = signal.freqz(b_sys_b, a_sys_a, worN=512)
    axes[1].plot(w_b / np.pi, np.abs(h_b), 'b', lw=2)
    axes[1].set_title("系统 B：引入零点进行“阻击”")
    axes[1].set_ylabel("幅度")
    axes[1].set_xlabel("频率 (x π rad/sample)")
    axes[1].grid(True)
    axes[1].text(0.25, np.max(np.abs(h_b))*0.8, '山峰被零点黑洞吞噬\n降为绝对 0', color='blue')
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'demo6_pole_zero_interaction.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"-> 已保存: {save_path}")


if __name__ == '__main__':
    print("=== 开始运行 痛苦系列03 配套代码 ===")
    demo1_divergent_signal()
    demo2_3d_zplane()
    demo3_poles_movement()
    demo4_roc_visual()
    demo5_notch_filter()
    demo6_pole_zero_interaction()
    print("=== 所有 Demo 生成完毕！图片保存在 output/ 目录下 ===")
