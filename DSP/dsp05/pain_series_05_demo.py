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

def demo1_iir_vs_fir():
    """demo1 - 终极杠杆：IIR (极小阶数) vs FIR (力大砖飞)"""
    fs = 1000; fc = 100
    
    # IIR: 4阶椭圆滤波器就能达到极高的陡峭度
    b_iir, a_iir = signal.ellip(4, 1, 40, fc/(fs/2), 'low')
    # FIR: 需要 100 多阶才能勉强抗衡
    b_fir = signal.firwin(121, fc/(fs/2), window='hamming')
    
    w_iir, h_iir = signal.freqz(b_iir, a_iir, worN=2048)
    w_fir, h_fir = signal.freqz(b_fir, [1.0], worN=2048)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w_fir * fs / (2 * np.pi), 20 * np.log10(np.abs(h_fir)), label='FIR (121 阶, 纯零点堆叠)', color='orange')
    plt.plot(w_iir * fs / (2 * np.pi), 20 * np.log10(np.abs(h_iir)), label='IIR (仅 4 阶, 极点共振借力)', color='red')
    
    plt.title('计算量降维打击：IIR 用 4 阶撬动了 FIR 121 阶的陡峭度')
    plt.xlabel('频率 (Hz)'); plt.ylabel('幅度 (dB)')
    plt.axvline(fc, color='black', linestyle='--', alpha=0.5)
    plt.ylim([-80, 10]); plt.xlim([0, 300])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_01_vs_fir.png'))
    plt.close()

def demo2_analog_prototypes():
    """demo2 - 抄袭模拟时代的四大天王原型"""
    N = 4 # 同为 4 阶
    rp = 1; rs = 40; Wn = 100 # 截止频率
    
    b_butt, a_butt = signal.butter(N, Wn, analog=True)
    b_cheb1, a_cheb1 = signal.cheby1(N, rp, Wn, analog=True)
    b_cheb2, a_cheb2 = signal.cheby2(N, rs, Wn, analog=True)
    b_ellip, a_ellip = signal.ellip(N, rp, rs, Wn, analog=True)
    
    plt.figure(figsize=(10, 6))
    for b, a, name in zip([b_butt, b_cheb1, b_cheb2, b_ellip], 
                          [a_butt, a_cheb1, a_cheb2, a_ellip],
                          ['巴特沃斯 (最平坦)', '切比雪夫I (通带波纹)', '切比雪夫II (阻带波纹)', '椭圆 (最陡峭)']):
        w, h = signal.freqs(b, a, worN=np.logspace(1, 3, 1000))
        plt.semilogx(w, 20 * np.log10(np.abs(h)), label=name)
        
    plt.title('模拟时代老前辈的作业：同等阶数下的权衡艺术')
    plt.xlabel('角频率 (rad/s) - 对数坐标'); plt.ylabel('幅度 (dB)')
    plt.axvline(Wn, color='black', linestyle='--', alpha=0.5)
    plt.ylim([-60, 5]); plt.xlim([10, 1000])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_02_analog_prototypes.png'))
    plt.close()

def demo3_bilinear_warping():
    """demo3 - 双线性变换的非线性频率挤压 (Warping)"""
    # Z 平面频率 w: 0 ~ pi
    w = np.linspace(0, np.pi, 1000)
    # 对应的 S 平面频率 Omega
    T = 2.0 # 标准化
    Omega = (2/T) * np.tan(w / 2)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w / np.pi, Omega, color='purple', linewidth=2)
    plt.title('双线性变换的“空间折叠”：将无穷大的 S 虚轴塞进 Z 的单位圆')
    plt.xlabel('数字频率 ω (xπ rad/sample)')
    plt.ylabel('模拟频率 Ω (rad/s)')
    plt.grid(True)
    
    # 标示预畸变效应
    plt.axvline(0.5, color='gray', linestyle='--')
    plt.axhline(np.tan(np.pi/4), color='gray', linestyle='--')
    plt.scatter([0.5], [np.tan(np.pi/4)], color='red', zorder=5)
    plt.annotate('高频被极度挤压', xy=(0.8, 5), xytext=(0.6, 10),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.ylim([0, 15]); plt.xlim([0, 1])
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_03_warping.png'))
    plt.close()

def demo4_impulse_invariant_aliasing():
    """demo4 - 脉冲响应不变法的致命伤：频率混叠"""
    # 模拟低通滤波器的极点离虚轴太近，衰减慢，导致采样混叠
    # 这里用一个简单的 2 阶切比雪夫来放大混叠现象
    b_a, a_a = signal.cheby1(2, 3, 0.8 * np.pi, analog=True)
    
    # 脉冲响应不变法 (scipy 用 cont2discrete, method='impulse')
    sys_imp = signal.cont2discrete((b_a, a_a), dt=1.0, method='impulse')
    b_imp, a_imp = sys_imp[0].flatten(), sys_imp[1]
    
    # 双线性变换
    sys_bil = signal.cont2discrete((b_a, a_a), dt=1.0, method='bilinear')
    b_bil, a_bil = sys_bil[0].flatten(), sys_bil[1]
    
    w, h_a = signal.freqs(b_a, a_a, worN=np.linspace(0, np.pi, 1000))
    w_d, h_imp = signal.freqz(b_imp, a_imp, worN=1000)
    w_d, h_bil = signal.freqz(b_bil, a_bil, worN=1000)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w / np.pi, 20 * np.log10(np.abs(h_a)), label='原始模拟原型 (超出 π 的部分会被折叠)', color='black', linestyle=':')
    plt.plot(w_d / np.pi, 20 * np.log10(np.abs(h_imp)), label='脉冲响应不变法 (高频翘起，发生混叠！)', color='red')
    plt.plot(w_d / np.pi, 20 * np.log10(np.abs(h_bil)), label='双线性变换法 (高频强制归零，无混叠)', color='blue')
    
    plt.title('为什么大家更爱双线性变换？脉冲响应不变法的混叠灾难')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('幅度 (dB)')
    plt.ylim([-50, 10]); plt.xlim([0, 1])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_04_aliasing.png'))
    plt.close()

def demo5_sos_quantization():
    """demo5 - 工程噩梦：高阶 IIR 的直接型系数截断灾难与 SOS 救赎"""
    # 极端的 8阶 窄带椭圆滤波器，极点极其靠近单位圆
    order = 8; rp = 1; rs = 60; fc = 0.05
    
    # 获取直接型 (Direct form)
    b, a = signal.ellip(order, rp, rs, fc, 'low')
    # 获取二阶级联型 (SOS)
    sos = signal.ellip(order, rp, rs, fc, 'low', output='sos')
    
    # 模拟 16-bit 定点数的量化函数
    def quantize(x, bits=16):
        max_val = np.max(np.abs(x))
        if max_val == 0: return x
        scale = (2**(bits-1) - 1) / max_val
        return np.round(x * scale) / scale
    
    # 量化直接型
    b_q = quantize(b); a_q = quantize(a)
    # 量化 SOS 型 (每个 b,a 独立量化)
    sos_q = np.copy(sos)
    for i in range(sos.shape[0]):
        sos_q[i, 0:3] = quantize(sos[i, 0:3])
        # 对 a_1, a_2 量化，保持 a_0 = 1.0
        sos_q[i, 4:6] = quantize(sos[i, 4:6])
        sos_q[i, 3] = 1.0
        
    w, h = signal.freqz(b, a, worN=1024)
    w_q, h_q = signal.freqz(b_q, a_q, worN=1024)
    w_sos_q, h_sos_q = signal.sosfreqz(sos_q, worN=1024)
    
    plt.figure(figsize=(10, 6))
    plt.plot(w / np.pi, 20 * np.log10(np.abs(h)), label='理想浮点精度 (理论完美)', color='gray', linewidth=4, alpha=0.5)
    plt.plot(w_q / np.pi, 20 * np.log10(np.abs(h_q)), label='直接型 16-bit 量化 (完全崩溃，发生畸变/发散)', color='red')
    plt.plot(w_sos_q / np.pi, 20 * np.log10(np.abs(h_sos_q)), label='SOS型 16-bit 量化 (成功保命)', color='blue')
    
    plt.title('落地 MCU 的定点灾难：为什么 IIR 必须拆成 SOS 二阶级联？')
    plt.xlabel('归一化频率 (xπ rad/sample)')
    plt.ylabel('幅度 (dB)')
    plt.ylim([-80, 20]); plt.xlim([0, 0.2])
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_05_sos.png'))
    plt.close()

if __name__ == '__main__':
    print("Generating Pain Series 05 (IIR) Demo Figures...")
    demo1_iir_vs_fir()
    demo2_analog_prototypes()
    demo3_bilinear_warping()
    demo4_impulse_invariant_aliasing()
    demo5_sos_quantization()
    print("Done. Output in", OUTPUT_DIR)
