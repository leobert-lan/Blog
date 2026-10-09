import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import time
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Songti SC', 'Arial Unicode MS', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def direct_dft(x):
    """暴力计算 DFT (O(N^2))"""
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    W = np.exp(-2j * np.pi * k * n / N)
    return np.dot(W, x)

def cooley_tukey_dit_fft(x):
    """教学用：从零实现的基2时域抽取 (DIT) FFT"""
    N = len(x)
    if N <= 1:
        return x
    even = cooley_tukey_dit_fft(x[0::2])
    odd = cooley_tukey_dit_fft(x[1::2])
    W = np.exp(-2j * np.pi * np.arange(N // 2) / N)
    return np.concatenate([even + W * odd, even - W * odd])

def bit_reverse_order(x):
    """倒位序重排"""
    N = len(x)
    num_bits = int(np.log2(N))
    reversed_idx = np.zeros(N, dtype=int)
    for i in range(N):
        # 将整数 i 转为二进制反转后再转回十进制
        b = bin(i)[2:].zfill(num_bits)
        reversed_idx[i] = int(b[::-1], 2)
    return x[reversed_idx], reversed_idx

def demo1_dft_vs_fft_benchmark():
    """demo1 - 复杂度悬崖：O(N^2) 暴力计算 vs O(N log N) 快速傅里叶变换"""
    sizes = [16, 32, 64, 128, 256, 512, 1024, 2048]
    dft_times = []
    fft_times = []
    
    print("--- 正在进行 DFT vs FFT 耗时基准测试 ---")
    for N in sizes:
        x = np.random.randn(N) + 1j * np.random.randn(N)
        
        # 测量直接 DFT
        t0 = time.perf_counter()
        _ = direct_dft(x)
        t_dft = time.perf_counter() - t0
        dft_times.append(t_dft * 1000) # ms
        
        # 测量 FFT (手写基2)
        t0 = time.perf_counter()
        _ = cooley_tukey_dit_fft(x)
        t_fft = time.perf_counter() - t0
        fft_times.append(t_fft * 1000) # ms
        
        print(f"N={N:4d} | Direct DFT: {t_dft*1000:8.3f} ms | Cooley-Tukey FFT: {t_fft*1000:8.3f} ms | Speedup: {t_dft/t_fft:6.1f}x")

    plt.figure(figsize=(12, 5))
    
    # 线性坐标系对比
    plt.subplot(1, 2, 1)
    plt.plot(sizes, dft_times, 'o-', color='crimson', label='直接计算 DFT ($O(N^2)$)')
    plt.plot(sizes, fft_times, 's-', color='dodgerblue', label='分治 FFT ($O(N \\log N)$)')
    plt.title('计算耗时对比 (线性坐标)')
    plt.xlabel('序列长度 N')
    plt.ylabel('耗时 (毫秒 ms)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 对数坐标系对比
    plt.subplot(1, 2, 2)
    plt.loglog(sizes, dft_times, 'o-', color='crimson', label='直接计算 DFT ($O(N^2)$)')
    plt.loglog(sizes, fft_times, 's-', color='dodgerblue', label='分治 FFT ($O(N \\log N)$)')
    plt.title('计算耗时对比 (双对数坐标 log-log)')
    plt.xlabel('序列长度 N (对数)')
    plt.ylabel('耗时 (毫秒 ms, 对数)')
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fft_01_complexity_benchmark.png'), dpi=150)
    plt.close()
    print("Demo 1 图片已生成: fft_01_complexity_benchmark.png")

def demo2_butterfly_and_accuracy():
    """demo2 - 验证手写基2 FFT 与 NumPy FFT 的数值绝对一致性 & 蝶形拆解"""
    N = 8
    np.random.seed(42)
    x = np.array([1.0, 2.0, 3.5, 4.0, 2.5, 1.0, -0.5, -2.0])
    
    # 1. 验证倒位序
    x_rev, rev_idx = bit_reverse_order(x)
    print(f"\n--- N=8 倒位序重排演示 ---")
    for i in range(N):
        b_orig = bin(i)[2:].zfill(3)
        b_rev = bin(rev_idx[i])[2:].zfill(3)
        print(f"原始索引 {i} ({b_orig}) -> 倒位序位置 {rev_idx[i]} ({b_rev}) | x[{rev_idx[i]}] = {x_rev[i]}")
        
    # 2. 验证基2分治结果
    X_custom = cooley_tukey_dit_fft(x)
    X_numpy = np.fft.fft(x)
    max_err = np.max(np.abs(X_custom - X_numpy))
    print(f"\n手写 Cooley-Tukey FFT 与 np.fft.fft 最大绝对误差: {max_err:.2e} (完全等价!)")
    
    # 可视化频谱对比
    plt.figure(figsize=(10, 5))
    k = np.arange(N)
    plt.stem(k - 0.08, np.abs(X_numpy), linefmt='dodgerblue', markerfmt='bo', basefmt=' ', label='NumPy FFT 幅度')
    plt.stem(k + 0.08, np.abs(X_custom), linefmt='crimson', markerfmt='rx', basefmt=' ', label='手写蝶形 DIT-FFT 幅度')
    plt.title(f'N=8 蝶形 FFT 与标准 DFT 结果完全吻合 (误差 < {max_err:.1e})')
    plt.xlabel('频率序号 k')
    plt.ylabel('幅度 |X[k]|')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fft_02_butterfly_verification.png'), dpi=150)
    plt.close()
    print("Demo 2 图片已生成: fft_02_butterfly_verification.png")

def demo3_fast_convolution():
    """demo3 - 工程实战：快速卷积 (Fast Convolution) 对比直接卷积"""
    signal_len = 100000  # 10万点信号 (例如 10秒 10kHz 音频/脑电)
    x = np.random.randn(signal_len)
    
    filter_lens = [32, 64, 128, 256, 512, 1024, 2048]
    direct_times = []
    fft_times = []
    
    print("\n--- 正在进行时域卷积 vs FFT 快速卷积性能对比 ---")
    for M in filter_lens:
        h = np.random.randn(M)
        
        # 时域直接卷积 (scipy.signal.convolve(..., method='direct'))
        t0 = time.perf_counter()
        _ = signal.convolve(x, h, mode='same', method='direct')
        t_direct = time.perf_counter() - t0
        direct_times.append(t_direct * 1000)
        
        # FFT 快速卷积 (scipy.signal.fftconvolve)
        t0 = time.perf_counter()
        _ = signal.fftconvolve(x, h, mode='same')
        t_fft = time.perf_counter() - t0
        fft_times.append(t_fft * 1000)
        
        print(f"Filter M={M:4d} | Direct Conv: {t_direct*1000:8.2f} ms | FFT Conv: {t_fft*1000:8.2f} ms | Speedup: {t_direct/t_fft:6.1f}x")
        
    plt.figure(figsize=(10, 6))
    plt.plot(filter_lens, direct_times, 'o-', color='crimson', label='时域直接卷积 ($O(N \\cdot M)$)')
    plt.plot(filter_lens, fft_times, 's-', color='forestgreen', label='FFT 频域乘积 ($O((N+M) \\log (N+M))$)')
    plt.title('FIR 滤波器实战：时域直接卷积 vs FFT 快速卷积耗时对比 (N=10万点)')
    plt.xlabel('FIR 滤波器阶数 (抽头数 M)')
    plt.ylabel('耗时 (毫秒 ms)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fft_03_fast_convolution.png'), dpi=150)
    plt.close()
    print("Demo 3 图片已生成: fft_03_fast_convolution.png")

def demo4_zeropadding_myth():
    """demo4 - 避坑辨析：补零 (Zero-Padding) 究竟能不能提高频率分辨率？"""
    fs = 1000 # 1000 Hz 采样率
    # 构造两个频率非常接近的正弦波: 100 Hz 和 105 Hz (相差 5 Hz)
    f1, f2 = 100.0, 105.0
    
    # 场景 A: 观测时间只有 0.1 秒 (N=100 点)，物理分辨率 Δf = 1/0.1 = 10 Hz > 5 Hz (理论上分不开)
    t_short = np.arange(0, 0.1, 1/fs)
    x_short = np.sin(2 * np.pi * f1 * t_short) + np.sin(2 * np.pi * f2 * t_short)
    
    # 场景 A-1: 对这 100 点直接做 100 点 FFT
    X_short_raw = np.fft.rfft(x_short)
    freqs_short_raw = np.fft.rfftfreq(len(x_short), 1/fs)
    
    # 场景 A-2: 对这 100 点补零到 1024 点 (很多人误以为补零后分辨率变成了 1000/1024 ≈ 0.97Hz，就能看清两个峰)
    X_short_padded = np.fft.rfft(x_short, n=1024)
    freqs_short_padded = np.fft.rfftfreq(1024, 1/fs)
    
    # 场景 B: 真正延长观测时间到 1.0 秒 (N=1000 点)，物理分辨率 Δf = 1/1.0 = 1 Hz < 5 Hz (能分开)
    t_long = np.arange(0, 1.0, 1/fs)
    x_long = np.sin(2 * np.pi * f1 * t_long) + np.sin(2 * np.pi * f2 * t_long)
    X_long = np.fft.rfft(x_long, n=1024)
    freqs_long = np.fft.rfftfreq(1024, 1/fs)
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(freqs_short_padded, np.abs(X_short_padded) / len(x_short), color='crimson', linestyle='--', label='短信号补零 (T=0.1s, 补零至 1024点) -> 光滑的假象，依然只有1个鼓包')
    plt.plot(freqs_short_raw, np.abs(X_short_raw) / len(x_short), 'ro', markersize=6, label='短信号原始DFT (T=0.1s, 100点) -> 稀疏采样')
    plt.plot(freqs_long, np.abs(X_long) / len(x_long), color='dodgerblue', linewidth=2, label='长信号 (T=1.0s, 1000点采样) -> 真正清晰分辨出 100Hz 与 105Hz 双峰')
    
    plt.axvline(f1, color='gray', linestyle=':', alpha=0.7, label='真实信号频率 (100Hz & 105Hz)')
    plt.axvline(f2, color='gray', linestyle=':', alpha=0.7)
    
    plt.title('认知纠偏：补零只是频域 Sinc 插值（画出光滑曲线），绝不能提升物理频率分辨率！')
    plt.xlabel('频率 (Hz)')
    plt.ylabel('归一化幅度')
    plt.xlim([80, 125])
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fft_04_zeropadding_myth.png'), dpi=150)
    plt.close()
    print("Demo 4 图片已生成: fft_04_zeropadding_myth.png")

if __name__ == '__main__':
    demo1_dft_vs_fft_benchmark()
    demo2_butterfly_and_accuracy()
    demo3_fast_convolution()
    demo4_zeropadding_myth()
    print("\n所有 FFT 演示生成完毕！")
