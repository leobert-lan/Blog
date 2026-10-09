import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Heiti TC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def demo1_nonstationary_fft_failure():
    """demo1 - 传统全局 FFT 的盲区：时间信息的彻底丢失"""
    fs = 1000 # 采样率 1000 Hz
    t = np.arange(0, 2.0, 1/fs)
    
    # 信号 A：前 1 秒 10 Hz，后 1 秒 50 Hz
    x_a = np.zeros_like(t)
    x_a[t < 1.0] = np.sin(2 * np.pi * 10 * t[t < 1.0])
    x_a[t >= 1.0] = np.sin(2 * np.pi * 50 * t[t >= 1.0])
    
    # 信号 B：前 1 秒 50 Hz，后 1 秒 10 Hz (时间顺序完全颠倒)
    x_b = np.zeros_like(t)
    x_b[t < 1.0] = np.sin(2 * np.pi * 50 * t[t < 1.0])
    x_b[t >= 1.0] = np.sin(2 * np.pi * 10 * t[t >= 1.0])
    
    # 计算全局标准 FFT
    freqs = np.fft.rfftfreq(len(t), 1/fs)
    X_a = np.abs(np.fft.rfft(x_a))
    X_b = np.abs(np.fft.rfft(x_b))
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 6))
    
    # 信号 A 时域与频域
    axes[0, 0].plot(t, x_a, color='navy')
    axes[0, 0].set_title('信号 A 时域波形 (先 10Hz 后 50Hz)')
    axes[0, 0].set_xlabel('时间 (s)'); axes[0, 0].set_ylabel('幅度')
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].plot(freqs, X_a, color='crimson')
    axes[0, 1].set_title('信号 A 的全局 FFT 幅度谱')
    axes[0, 1].set_xlabel('频率 (Hz)'); axes[0, 1].set_ylabel('幅度')
    axes[0, 1].set_xlim([0, 80]); axes[0, 1].grid(True, alpha=0.3)
    
    # 信号 B 时域与频域
    axes[1, 0].plot(t, x_b, color='darkgreen')
    axes[1, 0].set_title('信号 B 时域波形 (先 50Hz 后 10Hz - 顺序颠倒)')
    axes[1, 0].set_xlabel('时间 (s)'); axes[1, 0].set_ylabel('幅度')
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].plot(freqs, X_b, color='crimson', linestyle='--')
    axes[1, 1].set_title('信号 B 的全局 FFT 幅度谱 (与信号 A 几乎完全重合)')
    axes[1, 1].set_xlabel('频率 (Hz)'); axes[1, 1].set_ylabel('幅度')
    axes[1, 1].set_xlim([0, 80]); axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wild_01_fft_temporal_loss.png'), dpi=150)
    plt.close()
    print("Demo 1 图片已生成: wild_01_fft_temporal_loss.png")

def demo2_stft_uncertainty_tradeoff():
    """demo2 - 时频测不准原理：窗长与时频分辨率的零和博弈"""
    fs = 1000
    t = np.arange(0, 2.0, 1/fs)
    
    # 构造信号：线性扫频信号 (10Hz -> 100Hz) + 在 t=1.0s 处的短暂瞬态脉冲 (高斯脉冲)
    x = signal.chirp(t, f0=10, t1=2.0, f1=100, method='linear')
    pulse = np.exp(-((t - 1.0) / 0.02)**2) * 2.0 # 20ms 脉冲
    x += pulse
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    
    # 1. 窄窗 (Nwin=32, ~32ms): 时间分辨率极高，频率分辨率模糊
    f1, t1, Zxx1 = signal.stft(x, fs, window='hann', nperseg=32, noverlap=28)
    axes[0].pcolormesh(t1, f1, np.abs(Zxx1), shading='gouraud', cmap='viridis')
    axes[0].set_title('窄窗 (N=32, 32ms)\n时间分辨率高 (脉冲清晰)，频率弥散')
    axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('频率 (Hz)')
    axes[0].set_ylim([0, 120])
    
    # 2. 宽窗 (Nwin=256, ~256ms): 频率分辨率极高，时间分辨率模糊
    f2, t2, Zxx2 = signal.stft(x, fs, window='hann', nperseg=256, noverlap=240)
    axes[1].pcolormesh(t2, f2, np.abs(Zxx2), shading='gouraud', cmap='viridis')
    axes[1].set_title('宽窗 (N=256, 256ms)\n频率分辨率高 (扫频清晰)，时间被抹平')
    axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('频率 (Hz)')
    axes[1].set_ylim([0, 120])
    
    # 3. 适中窗 (Nwin=96, ~96ms): 折中平衡
    f3, t3, Zxx3 = signal.stft(x, fs, window='hann', nperseg=96, noverlap=80)
    axes[2].pcolormesh(t3, f3, np.abs(Zxx3), shading='gouraud', cmap='viridis')
    axes[2].set_title('折中窗 (N=96, 96ms)\n工程平衡点：兼顾扫频轨迹与脉冲定位')
    axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('频率 (Hz)')
    axes[2].set_ylim([0, 120])
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wild_02_stft_uncertainty.png'), dpi=150)
    plt.close()
    print("Demo 2 图片已生成: wild_02_stft_uncertainty.png")

def demo3_realworld_eeg_erd_ers():
    """demo3 - 真实荒野应用：运动想象脑电 (EEG) 的事件相关去同步 (ERD/ERS) 时频图"""
    fs = 250 # 脑电常用采样率 250 Hz
    t = np.arange(0, 4.0, 1/fs)
    np.random.seed(42)
    
    # 模拟脑电 C3 通道信号 (右手运动想象任务)
    # 0~1s: 静息基线 (存在 10Hz Mu 节律)
    # 1~3s: 右手运动想象触发 -> 对侧感觉运动区 (C3) 产生 ERD (10Hz Mu 节律能量显著衰减)
    # 3~4s: 任务结束 -> 产生 ERS (20Hz Beta 节律能量反弹)
    eeg = np.zeros_like(t)
    # 背景白噪声与 1/f 低频漂移
    eeg += np.random.randn(len(t)) * 0.8
    
    # 10Hz Mu 节律 (0~1s 强, 1~3s 衰减到 0.15, 3~4s 缓慢恢复)
    mu_envelope = np.ones_like(t)
    mu_envelope[(t >= 1.0) & (t < 3.0)] = 0.15
    mu_envelope[t >= 3.0] = 0.6
    eeg += mu_envelope * 2.0 * np.sin(2 * np.pi * 10 * t)
    
    # 20Hz Beta 节律反弹 (3.0~4.0s 爆发)
    beta_envelope = np.zeros_like(t)
    beta_envelope[t >= 3.0] = np.exp(-(t[t >= 3.0] - 3.4)**2 / 0.05) * 2.5
    eeg += beta_envelope * np.sin(2 * np.pi * 20 * t)
    
    # 叠加 50Hz 工频干扰
    eeg += 1.5 * np.sin(2 * np.pi * 50 * t)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    
    # 1. 时域脑电原始波形 (几乎看不出规律，被噪声淹没)
    ax1.plot(t, eeg, color='slategray', lw=1)
    ax1.axvspan(1.0, 3.0, color='crimson', alpha=0.1, label='右手运动想象阶段 (1.0~3.0s)')
    ax1.set_title('原始脑电 C3 通道时域信号 (受 50Hz 工频与随机噪声污染)')
    ax1.set_ylabel('电压 (μV)')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # 2. 时频谱 (STFT 语谱图)
    f, t_stft, Zxx = signal.stft(eeg, fs, window='hann', nperseg=64, noverlap=56)
    im = ax2.pcolormesh(t_stft, f, np.abs(Zxx), shading='gouraud', cmap='inferno')
    ax2.axvspan(1.0, 3.0, color='white', alpha=0.15)
    ax2.set_title('时频分析 (STFT Spectrogram)：清晰捕捉到 10Hz Mu 衰减 (ERD) 与 20Hz Beta 反弹 (ERS)')
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('频率 (Hz)')
    ax2.set_ylim([0, 60])
    fig.colorbar(im, ax=ax2, label='幅度谱密度')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wild_03_eeg_erd_spectrogram.png'), dpi=150)
    plt.close()
    print("Demo 3 图片已生成: wild_03_eeg_erd_spectrogram.png")

def demo4_end_to_end_dsp_pipeline():
    """demo4 - 全链路工程实战：从被污染的非平稳信号到纯净特征提取"""
    fs = 1000
    t = np.arange(0, 3.0, 1/fs)
    np.random.seed(100)
    
    # 目标真实事件：在 1.2s~2.0s 出现的一段微弱 12Hz 振荡 (幅度 1.0)
    target = np.zeros_like(t)
    mask = (t >= 1.2) & (t <= 2.0)
    target[mask] = 1.0 * np.sin(2 * np.pi * 12 * t[mask])
    
    # 现实污染荒野：
    # 1. 0.5Hz 呼吸基线漂移 (低频大干扰)
    drift = 2.5 * np.sin(2 * np.pi * 0.5 * t)
    # 2. 50Hz 工频市电辐射 (强干扰)
    hum = 3.0 * np.sin(2 * np.pi * 50 * t)
    # 3. 随机宽带高斯白噪声
    noise = np.random.randn(len(t)) * 0.8
    
    raw = target + drift + hum + noise
    
    # --- 阶段 1: 50Hz IIR 陷波器 (痛苦系列 03/05) ---
    b_notch, a_notch = signal.iirnotch(50.0, 30.0, fs)
    step1_notched = signal.lfilter(b_notch, a_notch, raw)
    
    # --- 阶段 2: 8~20Hz 线性相位 FIR 带通滤波 (痛苦系列 04) ---
    # 消除基线漂移与高频噪声
    b_fir = signal.firwin(101, [8.0, 20.0], pass_zero=False, fs=fs, window='hamming')
    # 使用 filtfilt 实现零相位或直接卷积
    step2_bandpassed = signal.filtfilt(b_fir, [1.0], step1_notched)
    
    # --- 阶段 3: 时频能量包络检测 (希尔伯特变换 / 瞬时功率) ---
    analytic_signal = signal.hilbert(step2_bandpassed)
    amplitude_envelope = np.abs(analytic_signal)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    
    # 1. 原始输入
    axes[0].plot(t, raw, color='gray', lw=1)
    axes[0].set_title('1. 原始采集信号 (12Hz 微弱目标被基线漂移、50Hz工频及白噪声彻底淹没)')
    axes[0].set_ylabel('输入幅度'); axes[0].grid(True, alpha=0.3)
    
    # 2. 50Hz 陷波后
    axes[1].plot(t, step1_notched, color='navy', lw=1)
    axes[1].set_title('2. 经过 50Hz IIR 陷波器后 (切除市电工频，基线漂移仍存)')
    axes[1].set_ylabel('陷波后幅度'); axes[1].grid(True, alpha=0.3)
    
    # 3. 带通滤波后
    axes[2].plot(t, step2_bandpassed, color='darkgreen', lw=1.2)
    axes[2].set_title('3. 经过 8~20Hz 线性相位 FIR 带通滤波后 (基线与高频噪声切净，12Hz 波形显现)')
    axes[2].set_ylabel('带通后幅度'); axes[2].grid(True, alpha=0.3)
    
    # 4. 提取出的能量包络与真实目标区间对照
    axes[3].plot(t, amplitude_envelope, color='crimson', lw=2, label='提取的瞬时能量包络')
    axes[3].axvspan(1.2, 2.0, color='gold', alpha=0.25, label='真实 12Hz 目标活跃区间 (1.2~2.0s)')
    axes[3].set_title('4. 特征提取与事件判决 (能量包络与真实活跃区间精确对齐)')
    axes[3].set_xlabel('时间 (s)'); axes[3].set_ylabel('能量包络')
    axes[3].legend(loc='upper right'); axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wild_04_end_to_end_pipeline.png'), dpi=150)
    plt.close()
    print("Demo 4 图片已生成: wild_04_end_to_end_pipeline.png")

if __name__ == '__main__':
    print("=== 开始运行 痛苦系列 07 配套实验代码 ===")
    demo1_nonstationary_fft_failure()
    demo2_stft_uncertainty_tradeoff()
    demo3_realworld_eeg_erd_ers()
    demo4_end_to_end_dsp_pipeline()
    print("=== 所有 Demo 生成完毕！图片保存在 output/ 目录下 ===")
