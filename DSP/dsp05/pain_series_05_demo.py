"""
pain_series_05_demo.py
DSP 痛苦系列 05 博客配套仿真代码：反馈与共振——IIR 滤波器设计与定点量化

统一符号约定（与 DSP-04 保持一致）：
  L : FIR 滤波器抽头长度 (Number of taps)
  N : 滤波器阶数 (Filter order), FIR 满足 N = L - 1; IIR 对应分母多项式最高幂次
  fs: 采样率 (Hz), 采样周期 T = 1 / fs

运行方式（在仓库根目录下）：
  python DSP/dsp05/pain_series_05_demo.py

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


def quantize_pow2(x, bits=16):
    """
    模拟真实硬件的二进制有符号 Q 格式定点数截断（2 的整数次幂定标）：
      1 位符号位 + int_bits 位整数位 + frac_bits 位小数位 = bits
    返回 (量化后浮点近似数组, frac_bits)。
    """
    x = np.asarray(x, dtype=float)
    max_val = np.max(np.abs(x))
    if max_val == 0.0:
        return x.copy(), bits - 1
    int_bits = max(0, int(np.ceil(np.log2(max_val * (1.0 + 1e-12)))))
    frac_bits = (bits - 1) - int_bits
    scale = 2.0 ** frac_bits
    max_int = (2 ** (bits - 1)) - 1
    min_int = -(2 ** (bits - 1))
    q_int = np.clip(np.round(x * scale), min_int, max_int)
    return q_int / scale, frac_bits


def demo1_iir_vs_fir():
    """
    demo1 - 同指标严格对标：
      目标指标 (fs = 1000 Hz):
        通带 [0, 100 Hz] 波动 <= 1 dB (FIR 等波纹以 ±0.055 线性容差对标, 窗函数 >= -1 dB)
        阻带 [125, 500 Hz] 衰减 >= 50 dB
      对比达标所需的最低滤波器阶数、每样本乘加量与群延迟。
    """
    fs = 1000.0
    fp, fsb = 100.0, 125.0
    rp, rs = 1.0, 50.0

    # 1. 椭圆 IIR：由 ellipord 自动求解最低阶数
    n_iir, wn_iir = signal.ellipord(fp / (fs / 2.0), fsb / (fs / 2.0), rp, rs)
    sos_iir = signal.ellip(n_iir, rp, rs, wn_iir, btype='low', output='sos')

    # 2. Parks-McClellan (Remez) 等波纹 FIR：搜索最低奇数抽头数 L
    dp = 0.055  # 约 ±0.48 dB，峰峰值接近 1 dB
    ds = 10.0 ** (-rs / 20.0)
    L_remez = None
    b_remez = None
    for L_cand in range(21, 301, 2):
        br = signal.remez(L_cand, [0.0, fp, fsb, fs / 2.0], [1.0, 0.0], weight=[1.0, dp / ds], fs=fs)
        wr, hr = signal.freqz(br, [1.0], worN=8192)
        fr = wr * fs / (2.0 * np.pi)
        pb_err = np.max(np.abs(np.abs(hr[fr <= fp]) - 1.0))
        sb_db = np.max(20.0 * np.log10(np.maximum(np.abs(hr[fr >= fsb]), 1e-12)))
        if pb_err <= dp and sb_db <= -rs:
            L_remez = L_cand
            b_remez = br
            break

    # 3. 汉明窗 FIR：搜索最低奇数抽头数 L
    L_hamm = None
    b_hamm = None
    for L_cand in range(31, 401, 2):
        bh = signal.firwin(L_cand, (fp + fsb) / 2.0 / (fs / 2.0), window='hamming')
        wh, hh = signal.freqz(bh, [1.0], worN=8192)
        fh = wh * fs / (2.0 * np.pi)
        pb_min_db = np.min(20.0 * np.log10(np.maximum(np.abs(hh[fh <= fp]), 1e-12)))
        sb_max_db = np.max(20.0 * np.log10(np.maximum(np.abs(hh[fh >= fsb]), 1e-12)))
        if pb_min_db >= -rp and sb_max_db <= -rs:
            L_hamm = L_cand
            b_hamm = bh
            break

    w_iir, h_iir = signal.sosfreqz(sos_iir, worN=4096)
    w_rem, h_rem = signal.freqz(b_remez, [1.0], worN=4096)
    w_ham, h_ham = signal.freqz(b_hamm, [1.0], worN=4096)
    f = w_iir * fs / (2.0 * np.pi)

    n_sos_sections = sos_iir.shape[0]
    mac_iir = n_sos_sections * 5  # 每个二阶节 (a0=1): 3个b + 2个a = 5 次乘加
    mac_remez = L_remez           # 通用卷积 L 次乘加 (若利用偶对称可降乘法至 (L+1)//2)
    mac_hamm = L_hamm

    print(
        f"[Demo1] 同指标对标 (fp={fp}Hz, fsb={fsb}Hz, rp={rp}dB, rs={rs}dB):\n"
        f"  椭圆 IIR : 阶数 N={n_iir} ({n_sos_sections}个SOS), 乘加={mac_iir} MAC/样本\n"
        f"  Remez FIR: 抽头 L={L_remez} (阶数 N={L_remez-1}), 通用乘加={mac_remez} MAC/样本 (对称乘法 {(L_remez+1)//2}), 群延迟={(L_remez-1)/2:.1f} 样本\n"
        f"  汉明窗FIR: 抽头 L={L_hamm} (阶数 N={L_hamm-1}), 通用乘加={mac_hamm} MAC/样本 (对称乘法 {(L_hamm+1)//2}), 群延迟={(L_hamm-1)/2:.1f} 样本"
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：完全相同指标框下的幅频对比
    ax1.axvspan(0.0, fp, color='seagreen', alpha=0.08, label=f'目标通带 [0, {int(fp)} Hz]')
    ax1.axvspan(fsb, 300.0, color='indianred', alpha=0.08, label=f'目标阻带 [{int(fsb)}, 500 Hz]')
    ax1.axhline(-rs, color='gray', linestyle=':', linewidth=1.2, label=f'阻带指标 -{int(rs)} dB')

    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_ham), 1e-12)),
             label=f'汉明窗 FIR (L={L_hamm}, N={L_hamm-1})', color='darkorange', linewidth=1.5)
    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_rem), 1e-12)),
             label=f'Remez FIR (L={L_remez}, N={L_remez-1})', color='royalblue', linewidth=1.6)
    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_iir), 1e-12)),
             label=f'椭圆 IIR (N={n_iir}, {n_sos_sections}×SOS)', color='crimson', linewidth=1.8)

    ax1.set_title('同指标对标：三种达标滤波器的幅频响应')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_xlim([0.0, 260.0])
    ax1.set_ylim([-85, 5])
    ax1.legend(loc='upper right', fontsize=8.8)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：阶数与运行期乘加开销柱状对比
    labels = [f'椭圆 IIR\n(N={n_iir})', f'Remez FIR\n(L={L_remez}, N={L_remez-1})', f'汉明窗 FIR\n(L={L_hamm}, N={L_hamm-1})']
    orders = [n_iir, L_remez - 1, L_hamm - 1]
    macs = [mac_iir, mac_remez, mac_hamm]
    x_pos = np.arange(len(labels))
    width = 0.35

    bars1 = ax2.bar(x_pos - width / 2, orders, width, label='滤波器阶数 N', color='steelblue')
    bars2 = ax2.bar(x_pos + width / 2, macs, width, label='标准 MAC 运算/样本', color='coral')

    for bar in bars1:
        h_val = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h_val + 2.5, f'{int(h_val)}', ha='center', va='bottom', fontsize=9.5)
    for bar in bars2:
        h_val = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h_val + 2.5, f'{int(h_val)}', ha='center', va='bottom', fontsize=9.5)

    ax2.set_title('算力降维对比：同幅频指标下的阶数与每样本乘加数')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(labels, fontsize=9.5)
    ax2.set_ylabel('阶数 / 乘加次数 (MAC/sample)')
    ax2.set_ylim([0, max(macs) * 1.18])
    ax2.legend(loc='upper left', fontsize=9.5)
    ax2.grid(True, axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_01_vs_fir.png'), dpi=150)
    plt.close()


def demo2_analog_prototypes():
    """
    demo2 - 统一通带口径下的四大模拟原型对比 (N = 4, rp = 1 dB, rs = 40 dB)：
      将四个原型统一对齐至 Ω_p = 100 rad/s 处恰好达到 -1 dB 衰减，
      避免因 scipy 中 cheby2 默认以阻带作为 Wn 引起的口径错位。
    """
    N = 4
    rp = 1.0
    rs = 40.0
    Wp = 100.0

    # 将四个原型的 -1 dB 频点全部对齐至 Wp = 100 rad/s
    eps_rp = np.sqrt(10.0 ** (rp / 10.0) - 1.0)
    wn_butter = Wp / (eps_rp ** (1.0 / N))
    ratio_c2 = np.cosh(np.arccosh(np.sqrt(10.0 ** (rs / 10.0) - 1.0) / eps_rp) / N)
    wn_cheby2 = Wp * ratio_c2

    b_butt, a_butt = signal.butter(N, wn_butter, analog=True)
    b_cheb1, a_cheb1 = signal.cheby1(N, rp, Wp, analog=True)
    b_cheb2, a_cheb2 = signal.cheby2(N, rs, wn_cheby2, analog=True)
    b_ellip, a_ellip = signal.ellip(N, rp, rs, Wp, analog=True)

    w = np.logspace(1.0, 3.0, 4000)
    protos = [
        (b_butt, a_butt, '巴特沃斯 (通带/阻带单调平坦)', 'royalblue'),
        (b_cheb1, a_cheb1, '切比雪夫 I 型 (通带等波纹)', 'darkorange'),
        (b_cheb2, a_cheb2, '切比雪夫 II 型 (阻带等波纹)', 'seagreen'),
        (b_ellip, a_ellip, '椭圆滤波器 (双带等波纹，最陡峭)', 'crimson'),
    ]

    print(f"[Demo2] 四大模拟原型对齐到 -1 dB @ {Wp} rad/s (N={N}, rp={rp}dB, rs={rs}dB):")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    for b, a, name, color in protos:
        _, h = signal.freqs(b, a, worN=w)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        idx_40 = np.where(mag_db <= -rs)[0][0]
        idx_1 = np.argmin(np.abs(mag_db + rp))
        print(f"  {name}: -1dB={w[idx_1]:.2f} rad/s, 首次抵达 -40dB={w[idx_40]:.2f} rad/s")
        ax1.semilogx(w, mag_db, label=name, color=color, linewidth=1.8)
        ax2.plot(w, mag_db, label=name, color=color, linewidth=1.8)

    # 左图：全局对数幅频响应
    ax1.axvline(Wp, color='black', linestyle='--', alpha=0.6, label=f'统一通带边界 Ωp = {int(Wp)} rad/s (-1 dB)')
    ax1.axhline(-rs, color='gray', linestyle=':', alpha=0.8, label=f'参考阻带线 -{int(rs)} dB')
    ax1.set_title('四大模拟原型统一口径对比（同为 4 阶，-1 dB 通带边界对齐）')
    ax1.set_xlabel('模拟角频率 Ω (rad/s，对数坐标)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_xlim([10.0, 1000.0])
    ax1.set_ylim([-65, 5])
    ax1.legend(loc='lower left', fontsize=8.8)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)

    # 右图：通带局部放大，清晰展示等波纹 vs 单调平坦
    ax2.axvspan(10.0, Wp, color='seagreen', alpha=0.06)
    ax2.axhline(-rp, color='gray', linestyle=':', alpha=0.8, label=f'-{rp:.0f} dB 通带容差下限')
    ax2.axvline(Wp, color='black', linestyle='--', alpha=0.6)
    ax2.set_title('通带细节放大：单调平坦 vs 1 dB 等波纹起伏')
    ax2.set_xlabel('模拟角频率 Ω (rad/s)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_xlim([10.0, 135.0])
    ax2.set_ylim([-3.5, 0.5])
    ax2.legend(loc='lower left', fontsize=8.8)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_02_analog_prototypes.png'), dpi=150)
    plt.close()


def demo3_bilinear_warping():
    """
    demo3 - 双线性变换的频率畸变与预畸变校正实证：
      设定采样率 fs = 400 Hz (T = 2.5 ms)，目标 -3 dB 截止频率 fc = 100 Hz (ωc = 0.5π)。
    """
    fs = 400.0
    fc_target = 100.0
    fd = np.linspace(0.0, fs / 2.0 * 0.96, 1000)

    # 真实非线性映射与理想线性基准
    fa_warped = (fs / np.pi) * np.tan(np.pi * fd / fs)
    fa_linear = fd.copy()

    # 目标点预畸变频率与不预畸变时的偏移频率
    fa_pre = (fs / np.pi) * np.tan(np.pi * fc_target / fs)
    fc_drifted = (fs / np.pi) * np.arctan(np.pi * fc_target / fs)

    # 实际设计 4 阶巴特沃斯低通滤波器验证
    b_a_nw, a_a_nw = signal.butter(4, 2.0 * np.pi * fc_target, analog=True)
    b_d_nw, a_d_nw = signal.bilinear(b_a_nw, a_a_nw, fs=fs)

    b_a_pre, a_a_pre = signal.butter(4, 2.0 * np.pi * fa_pre, analog=True)
    b_d_pre, a_d_pre = signal.bilinear(b_a_pre, a_a_pre, fs=fs)

    w, h_nw = signal.freqz(b_d_nw, a_d_nw, worN=4096)
    _, h_pre = signal.freqz(b_d_pre, a_d_pre, worN=4096)
    f = w * fs / (2.0 * np.pi)
    mag_nw = 20.0 * np.log10(np.maximum(np.abs(h_nw), 1e-12))
    mag_pre = 20.0 * np.log10(np.maximum(np.abs(h_pre), 1e-12))

    fc_nw_meas = f[np.argmin(np.abs(mag_nw + 3.0103))]
    fc_pre_meas = f[np.argmin(np.abs(mag_pre + 3.0103))]
    print(
        f"[Demo3] 预畸变实证 (fs={fs}Hz, 目标 fc={fc_target}Hz):\n"
        f"  预畸变模拟频率 fa_pre={fa_pre:.2f}Hz\n"
        f"  未预畸变实际 -3dB={fc_nw_meas:.2f}Hz (理论 {fc_drifted:.2f}Hz)\n"
        f"  预畸变后实际 -3dB={fc_pre_meas:.2f}Hz"
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：频率映射曲线
    ax1.plot(fd, fa_linear, color='gray', linestyle='--', linewidth=1.4, label='理想线性映射 $f_a = f_d$')
    ax1.plot(fd, fa_warped, color='purple', linewidth=2.0, label=r'双线性映射 $f_a = \frac{f_s}{\pi}\tan(\frac{\pi f_d}{f_s})$')
    ax1.scatter([fc_target, fc_drifted], [fa_pre, fc_target], color=['royalblue', 'crimson'], zorder=6, s=55)
    ax1.annotate(
        f'预畸变校正点\n({fc_target:.0f} Hz → {fa_pre:.2f} Hz)',
        xy=(fc_target, fa_pre), xytext=(42, 230),
        arrowprops=dict(arrowstyle='->', color='royalblue', lw=1.3),
        color='royalblue', fontsize=9.2
    )
    ax1.annotate(
        f'未校正时偏移\n(100 Hz 模拟 → {fc_drifted:.2f} Hz 数字)',
        xy=(fc_drifted, fc_target), xytext=(105, 55),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.3),
        color='crimson', fontsize=9.2
    )
    ax1.set_title(f'频率畸变曲线 (采样率 fs={int(fs)} Hz, 奈奎斯特={int(fs/2)} Hz)')
    ax1.set_xlabel(r'数字频率 $f_d$ (Hz)')
    ax1.set_ylabel(r'模拟频率 $f_a$ (Hz)')
    ax1.set_xlim([0.0, 200.0])
    ax1.set_ylim([0.0, 500.0])
    ax1.legend(loc='upper left', fontsize=9.0)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：4 阶巴特沃斯低通频响验证
    ax2.axhline(-3.01, color='gray', linestyle=':', linewidth=1.2, label='-3 dB 截止基准线')
    ax2.axvline(fc_target, color='black', linestyle='--', alpha=0.5, label=f'目标截止频率 {int(fc_target)} Hz')
    ax2.plot(f, mag_nw, color='crimson', linestyle='--', linewidth=1.8,
             label=f'未做预畸变 (实际 -3 dB = {fc_nw_meas:.2f} Hz)')
    ax2.plot(f, mag_pre, color='royalblue', linewidth=2.0,
             label=f'预畸变校正 (实际 -3 dB = {fc_pre_meas:.2f} Hz)')
    ax2.scatter([fc_nw_meas, fc_pre_meas], [-3.01, -3.01], color=['crimson', 'royalblue'], zorder=6, s=45)
    ax2.set_title('4 阶巴特沃斯低通：预畸变校正前后幅频对比')
    ax2.set_xlabel('数字频率 (Hz)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_xlim([0.0, 200.0])
    ax2.set_ylim([-50.0, 3.0])
    ax2.legend(loc='lower left', fontsize=9.0)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_03_warping.png'), dpi=150)
    plt.close()


def _impulse_invariance_from_analog(b_a, a_a, fs):
    """
    通过留数/部分分式展开严格计算连续系统在采样周期 T=1/fs 下的脉冲响应不变离散化：
      H(z) = sum_i (T * r_i) / (1 - exp(p_i * T) * z^-1)
    仅适用于严格真分式模拟系统（阶数 M < N）。
    """
    T = 1.0 / fs
    r, p, k = signal.residue(b_a, a_a)
    if len(k) > 0:
        raise ValueError("双真分式/含直通项的系统（如高通/带阻）无法直接进行脉冲响应不变离散化。")
    den_total = np.poly1d([1.0])
    for pi in p:
        den_total *= np.poly1d([1.0, -np.exp(pi * T)])
    num_total = np.poly1d([0.0])
    for ri, pi in zip(r, p):
        other = np.polydiv(den_total, np.poly1d([1.0, -np.exp(pi * T)]))[0]
        num_total += (T * ri) * other
    return np.real(num_total.coeffs), np.real(den_total.coeffs)


def demo4_impulse_invariant_aliasing():
    """
    demo4 - 脉冲响应不变法的频域混叠 vs 双线性变换，以及为何高通/带阻不可用：
      左图：3 阶巴特沃斯低通 (fs=1000 Hz, fc=300 Hz)，展示脉冲响应不变法在阻带高频处上翘混叠；
      右图：4 阶巴特沃斯高通 (fs=1000 Hz, fc=200 Hz)，展示高通在 Ω->∞ 时不衰减导致无穷混叠失效，
            以及双线性变换对高通的完美映射。
    """
    fs = 1000.0
    fc_lp = 300.0
    b_a, a_a = signal.butter(3, 2.0 * np.pi * fc_lp, analog=True)
    b_imp, a_imp = _impulse_invariance_from_analog(b_a, a_a, fs)
    b_bil, a_bil = signal.butter(3, fc_lp / (fs / 2.0), btype='low')

    w_d, h_imp = signal.freqz(b_imp, a_imp, worN=2048)
    _, h_bil = signal.freqz(b_bil, a_bil, worN=2048)
    f_d = w_d * fs / (2.0 * np.pi)
    _, h_a = signal.freqs(b_a, a_a, worN=2.0 * np.pi * f_d)

    mag_a = 20.0 * np.log10(np.maximum(np.abs(h_a), 1e-12))
    mag_imp = 20.0 * np.log10(np.maximum(np.abs(h_imp), 1e-12))
    mag_bil = 20.0 * np.log10(np.maximum(np.abs(h_bil), 1e-12))

    print(
        f"[Demo4] 低通混叠 (Butter 3阶, fs={fs}Hz, fc={fc_lp}Hz):\n"
        f"  DC 增益: 模拟={mag_a[0]:.2f} dB, 脉冲不变={mag_imp[0]:.2f} dB\n"
        f"  Nyquist (500Hz): 模拟={mag_a[-1]:.2f} dB, 脉冲不变={mag_imp[-1]:.2f} dB (上翘 +{mag_imp[-1]-mag_a[-1]:.2f} dB), 双线性={mag_bil[-1]:.1f} dB"
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：低通混叠对比
    ax1.plot(f_d, mag_a, color='black', linestyle=':', linewidth=1.8, label='原始模拟低通 (超 500 Hz 尾部将折叠)')
    ax1.plot(f_d, mag_imp, color='crimson', linewidth=1.8, label='脉冲响应不变法 (高频折叠抬高阻带)')
    ax1.plot(f_d, mag_bil, color='royalblue', linewidth=1.8, label='预畸变双线性变换 (Nyquist 压至零点)')
    ax1.annotate(
        f'混叠上翘 ({mag_imp[-1]:.1f} dB\nvs 模拟 {mag_a[-1]:.1f} dB)',
        xy=(498.0, mag_imp[-1]), xytext=(190.0, -24.0),
        arrowprops=dict(arrowstyle='->', color='crimson', lw=1.3),
        color='crimson', fontsize=9.2
    )
    ax1.set_title(f'低通混叠对比：3 阶巴特沃斯 (fs={int(fs)} Hz, fc={int(fc_lp)} Hz)')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_xlim([0.0, 500.0])
    ax1.set_ylim([-50.0, 3.0])
    ax1.legend(loc='lower left', fontsize=8.8)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：为什么高通无法用脉冲响应不变法
    fc_hp = 200.0
    b_hp_a, a_hp_a = signal.butter(4, 2.0 * np.pi * fc_hp, btype='high', analog=True)
    f_ext = np.linspace(1.0, 2000.0, 2000)
    _, h_hp_a = signal.freqs(b_hp_a, a_hp_a, worN=2.0 * np.pi * f_ext)
    b_hp_bil, a_hp_bil = signal.butter(4, fc_hp / (fs / 2.0), btype='high')
    w_hp_d, h_hp_bil = signal.freqz(b_hp_bil, a_hp_bil, worN=1024)
    f_hp_d = w_hp_d * fs / (2.0 * np.pi)

    ax2.axvspan(500.0, 2000.0, color='crimson', alpha=0.09, label='Nyquist 之外的 0 dB 平坦高频区 (无穷混叠源)')
    ax2.axvline(500.0, color='crimson', linestyle='--', linewidth=1.2)
    ax2.plot(f_ext, 20.0 * np.log10(np.maximum(np.abs(h_hp_a), 1e-12)),
             color='black', linestyle=':', linewidth=1.8, label='模拟高通原型 (Ω→∞ 时增益恒趋近 0 dB)')
    ax2.plot(f_hp_d, 20.0 * np.log10(np.maximum(np.abs(h_hp_bil), 1e-12)),
             color='royalblue', linewidth=2.0, label='双线性变换数字高通 (s→∞ 压缩到 500 Hz)')
    ax2.set_title('高通失效机理：不满足带限条件，高通/带阻禁止直接采样')
    ax2.set_xlabel('频率 (Hz)')
    ax2.set_ylabel('幅度 (dB)')
    ax2.set_xlim([0.0, 1500.0])
    ax2.set_ylim([-50.0, 5.0])
    ax2.legend(loc='lower right', fontsize=8.8)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_04_aliasing.png'), dpi=150)
    plt.close()


def demo5_sos_quantization():
    """
    demo5 - 工程噩梦：高阶 IIR 直接型的 16-bit 二进制 Q 格式定点截断灾难 vs SOS 级联稳定性。
      三图实证：
        左图：复平面极点分布（直接型 4 个极点跃出单位圆）
        中图：时域冲激响应（直接型呈指数爆炸至溢出）
        右图：频响对比（直接型彻底畸变 vs SOS 与浮点完美贴合）
    """
    order = 8
    rp, rs = 1.0, 60.0
    fc_norm = 0.05

    b, a = signal.ellip(order, rp, rs, fc_norm, btype='low')
    sos = signal.ellip(order, rp, rs, fc_norm, btype='low', output='sos')

    # 直接型 16-bit Q 格式量化（保持硬件上归一化常数 a[0] = 1.0 不被量化）
    b_q, fb_b = quantize_pow2(b, bits=16)
    a_q = a.copy()
    a_q[1:], fb_a = quantize_pow2(a[1:], bits=16)
    a_q[0] = 1.0

    # SOS 16-bit Q 格式量化（保持每节 a_0k = 1.0）
    sos_q = np.copy(sos)
    fb_sos_a = []
    for i in range(sos.shape[0]):
        sos_q[i, 0:3], _ = quantize_pow2(sos[i, 0:3], bits=16)
        sos_q[i, 4:6], fb_sec = quantize_pow2(sos[i, 4:6], bits=16)
        sos_q[i, 3] = 1.0
        fb_sos_a.append(fb_sec)

    p_orig = np.roots(a)
    p_dir_q = np.roots(a_q)
    p_sos_q = np.concatenate([np.roots(row[3:6]) for row in sos_q])

    # 时域冲激响应检验
    n_len = 200
    imp = np.zeros(n_len)
    imp[0] = 1.0
    h_orig_t = signal.sosfilt(sos, imp)
    h_dir_q_t = signal.lfilter(b_q, a_q, imp)
    h_sos_q_t = signal.sosfilt(sos_q, imp)

    w_eval = np.linspace(1e-4, np.pi, 2048)
    w, h = signal.freqz(b, a, worN=w_eval)
    w_q, h_q = signal.freqz(b_q, a_q, worN=w_eval)
    w_sos_q, h_sos_q = signal.sosfreqz(sos_q, worN=w_eval)

    print(
        f"[Demo5] 8阶窄带椭圆 (fc=0.05π) 16-bit Q 格式定点量化:\n"
        f"  直接型分母 max|a|={np.max(np.abs(a)):.2f} -> 仅能用 Q{fb_a}; 量化后 {np.sum(np.abs(p_dir_q)>=1.0)} 个极点出圆/压线 (max|p|={np.max(np.abs(p_dir_q)):.4f})\n"
        f"  直接型时域冲激 |h[199]|={np.abs(h_dir_q_t[-1]):.2e} (指数发散溢出)\n"
        f"  SOS 型每节分母定标 Q{min(fb_sos_a)}~Q{max(fb_sos_a)}; max|p|={np.max(np.abs(p_sos_q)):.5f} (0个出圆), |h[199]|={np.abs(h_sos_q_t[-1]):.5f}"
    )

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.8, 5.2))

    # 左图：复平面单位圆边界附近的极点迁移
    theta = np.linspace(-0.75, 0.75, 400)
    ax1.plot(np.cos(theta), np.sin(theta), color='black', linestyle='--', linewidth=1.2, label='单位圆边界 |z|=1')
    ax1.scatter(np.real(p_orig), np.imag(p_orig), facecolors='none', edgecolors='gray', s=75, linewidths=1.8, label='64位浮点极点 (全在圆内)')
    ax1.scatter(np.real(p_dir_q), np.imag(p_dir_q), marker='x', color='crimson', s=65, linewidths=1.8,
                label=f'直接型 Q{fb_a} 极点 ({np.sum(np.abs(p_dir_q)>=1.0)}个出圆/压线)')
    ax1.scatter(np.real(p_sos_q), np.imag(p_sos_q), marker='+', color='royalblue', s=65, linewidths=1.6,
                label=f'SOS 型 Q{min(fb_sos_a)} 极点 (全部安全)')
    ax1.set_title('复平面极点迁移：直接型被截断误差推至圆外')
    ax1.set_xlabel('实部 Re(z)')
    ax1.set_ylabel('虚部 Im(z)')
    ax1.set_xlim([0.52, 1.56])
    ax1.set_ylim([-0.52, 0.52])
    ax1.set_aspect('equal', adjustable='box')
    ax1.legend(loc='upper left', fontsize=8.0)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 中图：时域冲激响应对数包络
    n_idx = np.arange(n_len)
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_orig_t), 1e-12)), color='gray', linewidth=3.5, alpha=0.45, label='浮点基准 (衰减收敛)')
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_dir_q_t), 1e-12)), color='crimson', linewidth=1.8, label='直接型 16-bit (指数发散至 10^29)')
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_sos_q_t), 1e-12)), color='royalblue', linewidth=1.5, linestyle='--', label='SOS 型 16-bit (收敛稳定)')
    ax2.set_title('时域冲激响应实证：直接型引发数值溢出')
    ax2.set_xlabel('采样点序号 n')
    ax2.set_ylabel(r'$\log_{10}|h[n]|$')
    ax2.set_xlim([0, 199])
    ax2.set_ylim([-5, 31])
    ax2.legend(loc='upper left', fontsize=8.3)
    ax2.grid(True, linestyle='--', alpha=0.6)

    # 右图：单位圆频响对比
    ax3.plot(w / np.pi, 20.0 * np.log10(np.maximum(np.abs(h), 1e-12)), label='64位浮点参考', color='gray', linewidth=4, alpha=0.45)
    ax3.plot(w_q / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_q), 1e-12)), label=f'直接型 Q{fb_a} (频响彻底崩溃)', color='crimson', linewidth=1.8)
    ax3.plot(w_sos_q / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_sos_q), 1e-12)), label='SOS 型 16-bit (高度吻合)', color='royalblue', linewidth=1.6)
    ax3.set_title('幅频响应对比：SOS 级联有效隔离系数敏度')
    ax3.set_xlabel('归一化角频率 ω/π (×π rad/sample)')
    ax3.set_ylabel('幅度 (dB)')
    ax3.set_xlim([0.0, 0.2])
    ax3.set_ylim([-80, 15])
    ax3.legend(loc='upper right', fontsize=8.3)
    ax3.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_05_sos.png'), dpi=150)
    plt.close()


def demo6_phase_and_group_delay():
    """
    demo6 - IIR 的隐形代价：非线性相位、通带边缘群延迟尖峰与复合脉冲色散畸变
    """
    fs = 1000.0
    fc = 100.0

    b_ell, a_ell = signal.ellip(4, 1.0, 40.0, fc / (fs / 2.0))
    b_ch1, a_ch1 = signal.cheby1(4, 1.0, fc / (fs / 2.0))
    b_but, a_but = signal.butter(4, fc / (fs / 2.0))
    b_bes, a_bes = signal.bessel(4, fc / (fs / 2.0), norm='mag')
    b_fir = signal.firwin(55, 125.0 / (fs / 2.0), window='hamming')

    w = np.linspace(0.001, np.pi * 0.40, 1500)
    f = w * fs / (2.0 * np.pi)

    filters = [
        (b_ell, a_ell, '椭圆 IIR (4阶)', 'crimson', '-'),
        (b_ch1, a_ch1, '切比雪夫I IIR (4阶)', 'darkorange', '-'),
        (b_but, a_but, '巴特沃斯 IIR (4阶)', 'seagreen', '-'),
        (b_bes, a_bes, '贝塞尔 IIR (4阶)', 'purple', '-.'),
        (b_fir, [1.0], '线性相位 FIR (L=55)', 'royalblue', '--'),
    ]

    print("[Demo6] 群延迟实测 (fs=1000 Hz, 通带 [0, 100 Hz]):")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    for b, a, name, color, ls in filters:
        _, gd = signal.group_delay((b, a), w=w)
        mask_pb = f <= 105.0
        print(f"  {name}: DC处={gd[0]:.2f} 样本, [0,105Hz]峰值={gd[mask_pb].max():.2f} 样本 @ {f[mask_pb][np.argmax(gd[mask_pb])]:.1f} Hz")
        ax1.plot(f, gd, label=name, color=color, linestyle=ls, linewidth=1.8)

    ax1.axvspan(0.0, 100.0, color='seagreen', alpha=0.06, label='通带区间 [0, 100 Hz]')
    ax1.set_title('群延迟对比：IIR 截止区剧烈尖峰 vs FIR 恒定直线')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('群延迟 (采样周期)')
    ax1.set_xlim([0.0, 150.0])
    ax1.set_ylim([0.0, 31.0])
    ax1.legend(loc='upper right', fontsize=8.5)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：通带复合脉冲波形通过滤波器的时域相位色散对比
    t = np.arange(0.0, 0.30, 1.0 / fs)
    env = np.exp(-((t - 0.10) / 0.022) ** 2)
    x = env * (0.6 + 0.5 * np.cos(2.0 * np.pi * 90.0 * (t - 0.10)))  # 均落在 100Hz 通带内

    y_ell = signal.lfilter(b_ell, a_ell, x)
    y_fir = signal.lfilter(b_fir, [1.0], x)
    # 剥离 FIR 固定的 27 个采样点纯延迟，仅对比波形保真度
    y_fir_aligned = np.roll(y_fir, -27)
    y_fir_aligned[-27:] = 0.0

    ax2.plot(t * 1000.0, x, color='gray', linewidth=3.2, alpha=0.45, label='原始通带复合脉冲 (含 90 Hz 调制)')
    ax2.plot(t * 1000.0, y_fir_aligned, color='royalblue', linestyle='--', linewidth=1.8, label='线性相位 FIR (左移27ms对齐后严格重合)')
    ax2.plot(t * 1000.0, y_ell, color='crimson', linewidth=1.6, label='4阶椭圆 IIR (高频分量滞后，产生不对称拖尾)')
    ax2.set_title('时域色散实证：通带复合脉冲经过滤波后的波形畸变')
    ax2.set_xlabel('时间 (ms)')
    ax2.set_ylabel('信号幅度')
    ax2.set_xlim([40.0, 220.0])
    ax2.set_ylim([-0.45, 1.25])
    ax2.legend(loc='upper right', fontsize=8.3)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_06_group_delay.png'), dpi=150)
    plt.close()


if __name__ == '__main__':
    print("Generating DSP-05 IIR Filter Design Figures...")
    demo1_iir_vs_fir()
    demo2_analog_prototypes()
    demo3_bilinear_warping()
    demo4_impulse_invariant_aliasing()
    demo5_sos_quantization()
    demo6_phase_and_group_delay()
    print("Done. Figures saved in:", OUTPUT_DIR)
