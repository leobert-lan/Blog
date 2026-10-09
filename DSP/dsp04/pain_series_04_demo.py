import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Songti SC', 'Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def demo1_window_comparison():
    """demo1 - 四种窗函数时域形状 + 频谱对比（主瓣/旁瓣）"""
    M = 51
    w_rect = signal.windows.boxcar(M)
    w_hann = signal.windows.hann(M)
    w_hamm = signal.windows.hamming(M)
    w_black = signal.windows.blackman(M)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 时域
    n = np.arange(M)
    ax1.plot(n, w_rect, label='矩形窗', marker='.')
    ax1.plot(n, w_hann, label='汉宁窗', marker='.')
    ax1.plot(n, w_hamm, label='汉明窗', marker='.')
    ax1.plot(n, w_black, label='布莱克曼窗', marker='.')
    ax1.set_title('窗函数的时域形态：如何温柔地截断')
    ax1.set_xlabel('样本点 n')
    ax1.legend(); ax1.grid(True)
    
    # 频域 (加窗相当于频域卷积，看窗本身的频谱)
    for w, name in zip([w_rect, w_hann, w_hamm, w_black], ['矩形窗', '汉宁窗', '汉明窗', '布莱克曼窗']):
        W = np.fft.fft(w, 2048)
        freqs = np.fft.fftfreq(2048)
        W = np.fft.fftshift(W)
        freqs = np.fft.fftshift(freqs)
        # 归一化并转dB
        W_dB = 20 * np.log10(np.abs(W) / np.max(np.abs(W)))
        # 仅显示一半正频率部分
        ax2.plot(freqs[1024:], W_dB[1024:], label=name)
        
    ax2.set_title('窗函数的频谱：主瓣宽度与旁瓣衰减的博弈')
    ax2.set_xlabel('归一化频率 (xπ rad/sample)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_ylim([-100, 0]); ax2.set_xlim([0, 0.15])
    ax2.legend(); ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_01_windows_raw.png'))
    plt.close()

def demo2_fir_window_design():
    """demo2 - 窗函数法设计低通 FIR，四种窗的频率响应叠加"""
    M = 51; fc = 0.4 # 归一化截止频率
    
    b_rect = signal.firwin(M, fc, window='boxcar')
    b_hann = signal.firwin(M, fc, window='hann')
    b_hamm = signal.firwin(M, fc, window='hamming')
    b_black = signal.firwin(M, fc, window='blackman')
    
    plt.figure(figsize=(10, 6))
    for b, name in zip([b_rect, b_hann, b_hamm, b_black], ['矩形窗', '汉宁窗', '汉明窗', '布莱克曼窗']):
        w, h = signal.freqz(b, worN=1024)
        plt.plot(w / np.pi, 20 * np.log10(np.abs(h)), label=name)
        
    plt.title('用不同窗函数设计低通FIR滤波器的频响对比')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('幅度 (dB)')
    plt.axvline(fc, color='red', linestyle='--', alpha=0.5, label='理想截止点')
    plt.ylim([-120, 10]); plt.xlim([0, 1])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_02_filter_design.png'))
    plt.close()

def demo3_gibbs_effect():
    """demo3 - 矩形窗的吉布斯效应：M 增大时过冲不消失"""
    fc = 0.4
    b_21 = signal.firwin(21, fc, window='boxcar')
    b_101 = signal.firwin(101, fc, window='boxcar')
    b_501 = signal.firwin(501, fc, window='boxcar')
    
    plt.figure(figsize=(10, 6))
    for b, label in zip([b_21, b_101, b_501], ['M=21', 'M=101', 'M=501 (力大砖飞)']):
        w, h = signal.freqz(b, worN=2048)
        plt.plot(w / np.pi, np.abs(h), label=label)
        
    plt.axvline(fc, color='black', linestyle='--', label='理想砖墙边界')
    plt.title('吉布斯魔咒：阶数增加只能收窄过渡带，抹不平约 9% 的边缘震荡')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('线性幅度')
    plt.xlim([0.2, 0.6])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_03_gibbs.png'))
    plt.close()

def demo4_linear_phase_verify():
    """demo4 - 线性相位验证：对称系数 → 群延迟恒为 M/2"""
    M = 51 # 阶数为 50，长度 51
    b = signal.firwin(M, 0.4, window='hamming')
    
    w, h = signal.freqz(b, worN=1024)
    phase = np.unwrap(np.angle(h))
    
    # 计算群延迟: -d(phase)/dw
    # 也可以使用 scipy.signal.group_delay
    w_gd, gd = signal.group_delay((b, 1), w=1024)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    ax1.plot(w / np.pi, phase, color='blue')
    ax1.set_title('相位响应：一条完美的直线 (线性相位)')
    ax1.set_xlabel('归一化频率 (xπ rad/sample)')
    ax1.set_ylabel('相位 (弧度)')
    ax1.grid(True)
    
    ax2.plot(w_gd / np.pi, gd, color='red')
    ax2.set_title(f'群延迟：恒定为 (M-1)/2 = {(M-1)/2}')
    ax2.set_xlabel('归一化频率 (xπ rad/sample)')
    ax2.set_ylabel('群延迟 (采样点)')
    ax2.set_ylim([0, 50])
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_04_linear_phase.png'))
    plt.close()

def demo5_type2_highpass_fail():
    """demo5 - 类型 II 不能做高通的数值验证"""
    # Type 1: 奇数长度 (M=51) -> 对称中心落在采样点上
    b_type1 = signal.firwin(51, 0.5, pass_zero=False) 
    
    # Type 2: 偶数长度 (M=50) -> 对称中心落在两个点中间
    # scipy 默认禁止偶数长度做高通，会抛错。为了展示，我们强行设计低通后反转频谱
    b_type2_low = signal.firwin(50, 0.5) 
    b_type2_high = b_type2_low * ((-1)**np.arange(50))
    
    w1, h1 = signal.freqz(b_type1, worN=1024)
    w2, h2 = signal.freqz(b_type2_high, worN=1024)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w1 / np.pi, np.abs(h1), label='Type 1 (奇数长度51)：成功的高通', color='blue')
    plt.plot(w2 / np.pi, np.abs(h2), label='Type 2 (偶数长度50)：Nyquist 处被强制拉回 0', color='red', linestyle='--')
    
    plt.title('结构决定宿命：为什么 Type 2 FIR 做不出高通滤波器？')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('线性幅度')
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_05_type2_fail.png'))
    plt.close()

def demo6_parks_mcclellan():
    """demo6 - Parks-McClellan 等波纹设计 vs 窗函数法对比"""
    M = 51
    bands = [0, 0.3, 0.4, 1.0]
    desired = [1, 0]
    
    # Parks-McClellan (Remez)
    b_remez = signal.remez(M, bands, desired, fs=2)
    # Hamming window for rough equivalence
    b_hamm = signal.firwin(M, 0.35)
    
    w_remez, h_remez = signal.freqz(b_remez, worN=2048)
    w_hamm, h_hamm = signal.freqz(b_hamm, worN=2048)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w_hamm / np.pi, 20 * np.log10(np.abs(h_hamm)), label='窗函数法 (Hamming)', color='orange')
    plt.plot(w_remez / np.pi, 20 * np.log10(np.abs(h_remez)), label='等波纹设计 (Parks-McClellan)', color='blue')
    
    plt.title('Parks-McClellan 等波纹设计 vs 窗函数法')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('幅度 (dB)')
    plt.ylim([-100, 10]); plt.xlim([0, 1])
    plt.axvspan(0, 0.3, color='green', alpha=0.1, label='要求通带')
    plt.axvspan(0.4, 1.0, color='red', alpha=0.1, label='要求阻带')
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fir_06_remez.png'))
    plt.close()

if __name__ == '__main__':
    print("Generating Pain Series 04 Full FIR Demo Figures...")
    demo1_window_comparison()
    demo2_fir_window_design()
    demo3_gibbs_effect()
    demo4_linear_phase_verify()
    demo5_type2_highpass_fail()
    demo6_parks_mcclellan()
    print("Done. Output in", OUTPUT_DIR)
