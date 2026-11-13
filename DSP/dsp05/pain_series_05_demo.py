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
from scipy.optimize import brentq

matplotlib.rcParams['font.sans-serif'] = [
    'PingFang SC', 'STHeiti', 'Heiti TC', 'Songti SC',
    'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def quantize_pow2(x, bits=16):
    """
    模拟二进制有符号 Q 格式定点数舍入量化（2 的整数次幂定标）：
      1 位符号位 + int_bits 位整数位 + frac_bits 位小数位 = bits
    返回 (舍入量化后的浮点近似数组, frac_bits)。
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


def _design_matched_spec_filters(fs=1000.0, fp=100.0, fsb=125.0, rp=1.0, rs=50.0):
    """
    统一按完全相同的幅频容差箱进行设计与验收：
      通带 [0, fp]    : 幅度严格落在 [10^(-rp/20), 1.0]，即 [-rp dB, 0.0 dB]
      阻带 [fsb, fs/2]: 幅度 <= 10^(-rs/20)，即 <= -rs dB
    在 8192 点频域网格与奇数抽头 (Type I，保证整数样本群延迟) 范围内搜索最小 FIR 抽头数，
    同时返回放开偶数抽头时的最小抽头数以便对照说明。
    """
    n_iir, wn_iir = signal.ellipord(fp / (fs / 2.0), fsb / (fs / 2.0), rp, rs)
    sos_iir = signal.ellip(n_iir, rp, rs, wn_iir, btype='low', output='sos')

    pb_min_lin = 10.0 ** (-rp / 20.0)
    pb_max_lin = 1.0
    center = 0.5 * (pb_max_lin + pb_min_lin)
    dp_half = 0.5 * (pb_max_lin - pb_min_lin)
    ds = 10.0 ** (-rs / 20.0)

    def _find_min_remez(step, start):
        for L_cand in range(start, 301, step):
            br = signal.remez(L_cand, [0.0, fp, fsb, fs / 2.0], [center, 0.0], weight=[1.0, dp_half / ds], fs=fs)
            wr, hr = signal.freqz(br, [1.0], worN=8192)
            fr = wr * fs / (2.0 * np.pi)
            mag = np.abs(hr)
            if np.max(mag[fr <= fp]) <= pb_max_lin and np.min(mag[fr <= fp]) >= pb_min_lin and np.max(mag[fr >= fsb]) <= ds:
                return L_cand, br
        return None, None

    def _find_min_hamming(step, start):
        for L_cand in range(start, 401, step):
            bh = signal.firwin(L_cand, (fp + fsb) / 2.0 / (fs / 2.0), window='hamming')
            wh, hh = signal.freqz(bh, [1.0], worN=8192)
            fh = wh * fs / (2.0 * np.pi)
            # 若存在微小 Gibbs 过冲 (+0.007 dB)，统一归一化使通带峰值严格 <= 0 dB
            peak = np.max(np.abs(hh[fh <= fp]))
            if peak > pb_max_lin:
                bh = bh / peak
                _, hh = signal.freqz(bh, [1.0], worN=8192)
            mag = np.abs(hh)
            if np.max(mag[fh <= fp]) <= pb_max_lin and np.min(mag[fh <= fp]) >= pb_min_lin and np.max(mag[fh >= fsb]) <= ds:
                return L_cand, bh
        return None, None

    L_remez_odd, b_remez = _find_min_remez(step=2, start=21)
    L_remez_all, _ = _find_min_remez(step=1, start=20)
    L_hamm_odd, b_hamm = _find_min_hamming(step=2, start=31)
    L_hamm_all, _ = _find_min_hamming(step=1, start=30)

    return {
        'fs': fs, 'fp': fp, 'fsb': fsb, 'rp': rp, 'rs': rs,
        'n_iir': n_iir, 'sos_iir': sos_iir,
        'L_remez': L_remez_odd, 'L_remez_all': L_remez_all, 'b_remez': b_remez,
        'L_hamm': L_hamm_odd, 'L_hamm_all': L_hamm_all, 'b_hamm': b_hamm,
    }


def demo1_iir_vs_fir():
    """
    demo1 - 统一容差箱下的同指标对标：
      对比椭圆 IIR、Remez FIR 与汉明窗 FIR 的最低阶数、普通卷积乘加量与对称折叠乘法优化。
    """
    spec = _design_matched_spec_filters()
    fs, fp, fsb, rp, rs = spec['fs'], spec['fp'], spec['fsb'], spec['rp'], spec['rs']
    n_iir, sos_iir = spec['n_iir'], spec['sos_iir']
    L_remez, b_remez = spec['L_remez'], spec['b_remez']
    L_hamm, b_hamm = spec['L_hamm'], spec['b_hamm']

    w_iir, h_iir = signal.sosfreqz(sos_iir, worN=4096)
    _, h_rem = signal.freqz(b_remez, [1.0], worN=4096)
    _, h_ham = signal.freqz(b_hamm, [1.0], worN=4096)
    f = w_iir * fs / (2.0 * np.pi)

    n_sos = sos_iir.shape[0]
    mult_iir = n_sos * 5            # 每个二阶节 (a0=1): 3个b + 2个a = 5 次乘法
    add_iir = n_sos * 4             # 每个二阶节 4 次加法
    mult_rem_std = L_remez
    mult_rem_sym = (L_remez + 1) // 2  # 奇数偶对称折叠：(L-1)/2 次预加法后共享乘法系数
    add_rem = L_remez - 1
    mult_ham_std = L_hamm
    mult_ham_sym = (L_hamm + 1) // 2
    add_ham = L_hamm - 1

    print(
        f"[Demo1] 统一容差箱对标 (fs={fs}Hz, 通带[0,{fp}Hz]∈[-{rp},0]dB, 阻带[{fsb},500Hz]<=-{rs}dB, 8192点网格):\n"
        f"  椭圆 IIR : 阶数 N={n_iir} ({n_sos}×SOS), 乘法={mult_iir}/样本, 加法={add_iir}/样本\n"
        f"  Remez FIR: 奇数最小抽头 L={L_remez} (全整数最小={spec['L_remez_all']}, N={L_remez-1}), "
        f"普通乘法={mult_rem_std}, 对称折叠乘法={mult_rem_sym}, 加法={add_rem}, 群延迟={(L_remez-1)/2:.1f}样本\n"
        f"  汉明窗FIR: 奇数最小抽头 L={L_hamm} (全整数最小={spec['L_hamm_all']}, N={L_hamm-1}), "
        f"普通乘法={mult_ham_std}, 对称折叠乘法={mult_ham_sym}, 加法={add_ham}, 群延迟={(L_hamm-1)/2:.1f}样本"
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    # 左图：统一容差箱下的幅频响应
    ax1.axvspan(0.0, fp, color='seagreen', alpha=0.08, label=f'目标通带 [0, {int(fp)} Hz] ([-1, 0] dB)')
    ax1.axvspan(fsb, 300.0, color='indianred', alpha=0.08, label=f'目标阻带 [{int(fsb)}, 500 Hz] (<=-{int(rs)} dB)')
    ax1.axhline(-rs, color='gray', linestyle=':', linewidth=1.2, label=f'阻带指标 -{int(rs)} dB')

    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_ham), 1e-12)),
             label=f'汉明窗 FIR (L={L_hamm}, N={L_hamm-1})', color='darkorange', linewidth=1.5)
    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_rem), 1e-12)),
             label=f'Remez FIR (L={L_remez}, N={L_remez-1})', color='royalblue', linewidth=1.6)
    ax1.plot(f, 20.0 * np.log10(np.maximum(np.abs(h_iir), 1e-12)),
             label=f'椭圆 IIR (N={n_iir}, {n_sos}×SOS)', color='crimson', linewidth=1.8)

    ax1.set_title('同指标对标：三种达标滤波器的幅频响应')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_xlim([0.0, 260.0])
    ax1.set_ylim([-85, 5])
    ax1.legend(loc='upper right', fontsize=8.5)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：普通乘法、对称折叠乘法与加法次数分开统计
    labels = [f'椭圆 IIR\n(N={n_iir})', f'Remez FIR\n(L={L_remez}, N={L_remez-1})', f'汉明窗 FIR\n(L={L_hamm}, N={L_hamm-1})']
    mults_std = [mult_iir, mult_rem_std, mult_ham_std]
    mults_sym = [mult_iir, mult_rem_sym, mult_ham_sym]
    adds = [add_iir, add_rem, add_ham]
    x_pos = np.arange(len(labels))
    width = 0.25

    b1 = ax2.bar(x_pos - width, mults_std, width, label='乘法/样本 (普通卷积/SOS)', color='steelblue')
    b2 = ax2.bar(x_pos, mults_sym, width, label='乘法/样本 (利用FIR对称折叠)', color='teal')
    b3 = ax2.bar(x_pos + width, adds, width, label='加法/样本 (含对称预加法)', color='coral')

    for bars in (b1, b2, b3):
        for bar in bars:
            h_val = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h_val + 2.0, f'{int(h_val)}', ha='center', va='bottom', fontsize=8.8)

    ax2.set_title('运算复杂度拆解：普通乘法、对称折叠乘法与加法次数')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(labels, fontsize=9.2)
    ax2.set_ylabel('每样本运算次数 (Ops/sample)')
    ax2.set_ylim([0, max(mults_std) * 1.18])
    ax2.legend(loc='upper left', fontsize=8.8)
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
        _, h_wp = signal.freqs(b, a, worN=[Wp])
        print(f"  {name}: @{Wp}rad/s={20*np.log10(np.abs(h_wp[0])):.3f} dB, 首次抵达 -40dB={w[idx_40]:.2f} rad/s")
        ax1.semilogx(w, mag_db, label=name, color=color, linewidth=1.8)
        ax2.plot(w, mag_db, label=name, color=color, linewidth=1.8)

    ax1.axvline(Wp, color='black', linestyle='--', alpha=0.6, label=f'统一通带边界 Ωp = {int(Wp)} rad/s (-1 dB)')
    ax1.axhline(-rs, color='gray', linestyle=':', alpha=0.8, label=f'参考阻带线 -{int(rs)} dB')
    ax1.set_title('四大模拟原型统一口径对比（同为 4 阶，-1 dB 通带边界对齐）')
    ax1.set_xlabel('模拟角频率 Ω (rad/s，对数坐标)')
    ax1.set_ylabel('幅度 (dB)')
    ax1.set_xlim([10.0, 1000.0])
    ax1.set_ylim([-65, 5])
    ax1.legend(loc='lower left', fontsize=8.8)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)

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

    fa_warped = (fs / np.pi) * np.tan(np.pi * fd / fs)
    fa_linear = fd.copy()

    fa_pre = (fs / np.pi) * np.tan(np.pi * fc_target / fs)
    fc_drifted = (fs / np.pi) * np.arctan(np.pi * fc_target / fs)

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
    通过留数/部分分式展开计算严格真分式模拟系统 (M < N) 在周期 T=1/fs 下的标准脉冲响应不变离散化：
      H(z) = sum_i (T * r_i) / (1 - exp(p_i * T) * z^-1)
    """
    T = 1.0 / fs
    r, p, k = signal.residue(b_a, a_a)
    if len(k) > 0:
        raise ValueError("含非零直通项的系统不能直接套用严格真分式的脉冲响应不变采样公式。")
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
    demo4 - 标准脉冲响应不变法的频域混叠 vs 双线性变换，以及为何高通/带阻通常不适用：
      左图：3 阶巴特沃斯低通 (fs=1000 Hz, fc=300 Hz)，展示脉冲响应不变法在阻带高频处上翘混叠；
      右图：4 阶巴特沃斯高通 (fs=1000 Hz, fc=200 Hz)，展示高通含直通项且在 Ω->∞ 不带限引起的严重混叠。
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

    fc_hp = 200.0
    b_hp_a, a_hp_a = signal.butter(4, 2.0 * np.pi * fc_hp, btype='high', analog=True)
    f_ext = np.linspace(1.0, 2000.0, 2000)
    _, h_hp_a = signal.freqs(b_hp_a, a_hp_a, worN=2.0 * np.pi * f_ext)
    b_hp_bil, a_hp_bil = signal.butter(4, fc_hp / (fs / 2.0), btype='high')
    w_hp_d, h_hp_bil = signal.freqz(b_hp_bil, a_hp_bil, worN=1024)
    f_hp_d = w_hp_d * fs / (2.0 * np.pi)

    ax2.axvspan(500.0, 2000.0, color='crimson', alpha=0.09, label='Nyquist 之外的 0 dB 平坦高频区 (严重混叠源)')
    ax2.axvline(500.0, color='crimson', linestyle='--', linewidth=1.2)
    ax2.plot(f_ext, 20.0 * np.log10(np.maximum(np.abs(h_hp_a), 1e-12)),
             color='black', linestyle=':', linewidth=1.8, label='模拟高通原型 (含直通项且 Ω→∞ 趋近 0 dB)')
    ax2.plot(f_hp_d, 20.0 * np.log10(np.maximum(np.abs(h_hp_bil), 1e-12)),
             color='royalblue', linewidth=2.0, label='双线性变换数字高通 (s→∞ 映射至 500 Hz)')
    ax2.set_title('高通/带阻为何少用脉冲不变法：含直通项且高频不带限')
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
    demo5 - 16 位系数量化引起的高阶 IIR 极点迁移：直接型与 SOS 结构对比
      注：本实验将滤波器系数按 16-bit 二进制 Q 格式进行舍入量化，随后使用 64 位浮点递推 (lfilter/sosfilt)
      单独隔离检验“系数量化引起的极点迁移与结构稳定性”，与状态变量定点运算效应区分开来。
    """
    order = 8
    rp, rs = 1.0, 60.0
    fc_norm = 0.05

    b, a = signal.ellip(order, rp, rs, fc_norm, btype='low')
    sos = signal.ellip(order, rp, rs, fc_norm, btype='low', output='sos')

    # 直接型 16-bit Q 格式舍入量化（保持硬件上归一化首项 a[0] = 1.0 不变）
    b_q, _ = quantize_pow2(b, bits=16)
    a_q = a.copy()
    a_q[1:], fb_a = quantize_pow2(a[1:], bits=16)
    a_q[0] = 1.0

    # SOS 16-bit Q 格式舍入量化（保持每节 a_0k = 1.0）
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

    # 浮点递推检验量化后系数构成的极点稳定性
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
        f"[Demo5] 8阶窄带椭圆 (fc=0.05π) 16-bit 系数舍入量化:\n"
        f"  直接型分母 max|a|={np.max(np.abs(a)):.2f} -> 仅能用 Q{fb_a}; 量化后 {np.sum(np.abs(p_dir_q)>=1.0)} 个极点出圆/压线 (max|p|={np.max(np.abs(p_dir_q)):.4f})\n"
        f"  直接型量化系数浮点递推冲激 |h[199]|={np.abs(h_dir_q_t[-1]):.2e} (极点出圆导致递推发散)\n"
        f"  SOS 型每节分母定标 Q{min(fb_sos_a)}~Q{max(fb_sos_a)}; max|p|={np.max(np.abs(p_sos_q)):.5f} (0个出圆), |h[199]|={np.abs(h_sos_q_t[-1]):.5f}"
    )

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.8, 5.2))

    theta = np.linspace(-0.75, 0.75, 400)
    ax1.plot(np.cos(theta), np.sin(theta), color='black', linestyle='--', linewidth=1.2, label='单位圆边界 |z|=1')
    ax1.scatter(np.real(p_orig), np.imag(p_orig), facecolors='none', edgecolors='gray', s=75, linewidths=1.8, label='64位浮点极点 (全在圆内)')
    ax1.scatter(np.real(p_dir_q), np.imag(p_dir_q), marker='x', color='crimson', s=65, linewidths=1.8,
                label=f'直接型 Q{fb_a} 极点 ({np.sum(np.abs(p_dir_q)>=1.0)}个出圆/压线)')
    ax1.scatter(np.real(p_sos_q), np.imag(p_sos_q), marker='+', color='royalblue', s=65, linewidths=1.6,
                label=f'SOS 型 Q{min(fb_sos_a)} 极点 (全部安全)')
    ax1.set_title('16位系数量化极点迁移：直接型被舍入误差推至圆外')
    ax1.set_xlabel('实部 Re(z)')
    ax1.set_ylabel('虚部 Im(z)')
    ax1.set_xlim([0.52, 1.56])
    ax1.set_ylim([-0.52, 0.52])
    ax1.set_aspect('equal', adjustable='box')
    ax1.legend(loc='upper left', fontsize=8.0)
    ax1.grid(True, linestyle='--', alpha=0.6)

    n_idx = np.arange(n_len)
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_orig_t), 1e-12)), color='gray', linewidth=3.5, alpha=0.45, label='原浮点基准 (衰减收敛)')
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_dir_q_t), 1e-12)), color='crimson', linewidth=1.8, label='直接型 Q8 系数浮点递推 (指数发散至 10^29)')
    ax2.plot(n_idx, np.log10(np.maximum(np.abs(h_sos_q_t), 1e-12)), color='royalblue', linewidth=1.5, linestyle='--', label='SOS Q14 系数浮点递推 (收敛稳定)')
    ax2.set_title('量化后系统的冲激响应稳定性验证 (浮点递推)')
    ax2.set_xlabel('采样点序号 n')
    ax2.set_ylabel(r'$\log_{10}|h[n]|$')
    ax2.set_xlim([0, 199])
    ax2.set_ylim([-5, 31])
    ax2.legend(loc='upper left', fontsize=8.0)
    ax2.grid(True, linestyle='--', alpha=0.6)

    ax3.plot(w / np.pi, 20.0 * np.log10(np.maximum(np.abs(h), 1e-12)), label='64位浮点参考', color='gray', linewidth=4, alpha=0.45)
    ax3.plot(w_q / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_q), 1e-12)), label=f'直接型 Q{fb_a} 系数 (频响垮塌)', color='crimson', linewidth=1.8)
    ax3.plot(w_sos_q / np.pi, 20.0 * np.log10(np.maximum(np.abs(h_sos_q), 1e-12)), label='SOS Q14 系数 (高度吻合)', color='royalblue', linewidth=1.6)
    ax3.set_title('单位圆频响对比：SOS 级联有效隔离系数敏感度')
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
    demo6 - 统一同指标与通带口径下的非线性相位与群延迟对比：
      直接复用 Demo1 相同指标 (通带 [0, 100 Hz] ∈ [-1, 0] dB，阻带 >= 125 Hz <= -50 dB) 的
      6 阶椭圆 IIR 与 73 抽头 Remez FIR；同时将 6 阶切比雪夫 I 型、巴特沃斯与贝塞尔的 -1 dB 边缘
      统一校准至 100 Hz，确保对比过程中不混入截止频率口径或幅度响应偏差。
    """
    spec = _design_matched_spec_filters()
    fs, fp, rp, rs = spec['fs'], spec['fp'], spec['rp'], spec['rs']
    b_ell, a_ell = signal.ellip(spec['n_iir'], rp, rs, fp / (fs / 2.0))
    b_rem = spec['b_remez']
    tau_rem = (spec['L_remez'] - 1) // 2

    # 统一将 6 阶切比雪夫 I、巴特沃斯、贝塞尔的 -1 dB 通带边缘对齐至 fp = 100 Hz
    b_ch1, a_ch1 = signal.cheby1(6, rp, fp / (fs / 2.0))

    eps_rp = np.sqrt(10.0 ** (rp / 10.0) - 1.0)
    wp_analog = 2.0 * fs * np.tan(np.pi * fp / fs)
    b_but_a, a_but_a = signal.butter(6, wp_analog / (eps_rp ** (1.0 / 6.0)), analog=True)
    b_but, a_but = signal.bilinear(b_but_a, a_but_a, fs=fs)

    def _bessel_1db_err(wc_hz):
        ba, aa = signal.bessel(6, 2.0 * np.pi * wc_hz, analog=True, norm='mag')
        bd, ad = signal.bilinear(ba, aa, fs=fs)
        _, h_val = signal.freqz(bd, ad, worN=[2.0 * np.pi * fp / fs])
        return 20.0 * np.log10(np.abs(h_val[0])) + rp

    wc_bes = brentq(_bessel_1db_err, 50.0, 300.0)
    b_bes_a, a_bes_a = signal.bessel(6, 2.0 * np.pi * wc_bes, analog=True, norm='mag')
    b_bes, a_bes = signal.bilinear(b_bes_a, a_bes_a, fs=fs)

    w = np.linspace(0.001, np.pi * 0.36, 1500)
    f = w * fs / (2.0 * np.pi)

    filters = [
        (b_ell, a_ell, '椭圆 IIR (6阶, 同指标)', 'crimson', '-'),
        (b_ch1, a_ch1, '切比雪夫I IIR (6阶, -1dB@100Hz)', 'darkorange', '-'),
        (b_but, a_but, '巴特沃斯 IIR (6阶, -1dB@100Hz)', 'seagreen', '-'),
        (b_bes, a_bes, '贝塞尔 IIR (6阶, -1dB@100Hz)', 'purple', '-.'),
        (b_rem, [1.0], f'Remez FIR (L={spec["L_remez"]}, 同指标)', 'royalblue', '--'),
    ]

    print(f"[Demo6] 统一 -1dB@100Hz 口径与同指标对比 (fs={fs}Hz):")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8))

    for b, a, name, color, ls in filters:
        _, h_chk = signal.freqz(b, a, worN=[2.0 * np.pi * fp / fs])
        _, gd = signal.group_delay((b, a), w=w)
        mask_pb = f <= 102.0
        print(
            f"  {name}: @100Hz={20*np.log10(np.abs(h_chk[0])):.2f}dB, "
            f"DC处={gd[0]:.2f}样本, [0,102Hz]峰值={gd[mask_pb].max():.2f}样本 @ {f[mask_pb][np.argmax(gd[mask_pb])]:.1f} Hz"
        )
        ax1.plot(f, gd, label=name, color=color, linestyle=ls, linewidth=1.8)

    ax1.axvspan(0.0, 100.0, color='seagreen', alpha=0.06, label='通带区间 [0, 100 Hz]')
    ax1.set_title('群延迟对比：6 阶同指标椭圆峰谷跨越逾 10 倍')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('群延迟 (采样周期)')
    ax1.set_xlim([0.0, 140.0])
    ax1.set_ylim([0.0, 65.0])
    ax1.legend(loc='upper left', fontsize=8.3)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 右图：统一复用 Demo1 同指标下的 6 阶椭圆 IIR vs 73 抽头 Remez FIR
    t = np.arange(0.0, 0.35, 1.0 / fs)
    env = np.exp(-((t - 0.10) / 0.022) ** 2)
    x = env * (0.6 + 0.5 * np.cos(2.0 * np.pi * 90.0 * (t - 0.10)))  # 完全处于 [0, 100 Hz] 通带内部

    y_ell = signal.lfilter(b_ell, a_ell, x)
    y_rem = signal.lfilter(b_rem, [1.0], x)
    y_rem_aligned = np.roll(y_rem, -tau_rem)
    y_rem_aligned[-tau_rem:] = 0.0

    tail_ell = np.max(np.abs(y_ell[160:260]))
    tail_rem = np.max(np.abs(y_rem_aligned[160:260]))
    print(f"  时域色散尾部幅度 (160~260ms): 6阶椭圆={tail_ell:.4f}, 73抽头Remez={tail_rem:.4f}")

    ax2.plot(t * 1000.0, x, color='gray', linewidth=3.2, alpha=0.45, label='原始通带复合脉冲 (含 90 Hz 调制)')
    ax2.plot(t * 1000.0, y_rem_aligned, color='royalblue', linestyle='--', linewidth=1.8,
             label=f'Remez FIR (L={spec["L_remez"]}, 补偿 {tau_rem}ms 纯延迟后重合)')
    ax2.plot(t * 1000.0, y_ell, color='crimson', linewidth=1.6,
             label='6 阶椭圆 IIR (同指标下高频滞后，产生长拖尾色散)')
    ax2.set_title('同指标实证：相位色散导致的时域波形畸变')
    ax2.set_xlabel('时间 (ms)')
    ax2.set_ylabel('信号幅度')
    ax2.set_xlim([40.0, 240.0])
    ax2.set_ylim([-0.45, 1.25])
    ax2.legend(loc='upper right', fontsize=8.2)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_06_group_delay.png'), dpi=150)
    plt.close()


def demo7_fixed_point_limit_cycle():
    """
    demo7 - 真实的 16 位定点状态变量与反馈累加器仿真（与仅量化系数的 Demo5 独立区分）：
      构造极点完全位于单位圆内 (r=0.95) 的单节二阶 IIR (Q14 系数, Q15 状态, 整数反馈舍入)：
        左图：零输入量化极限环（输入清零后，舍入反馈被锁在 [-2, +2] LSB 持续振荡）；
        右图：溢出处治对比（整数回绕引发 ±19000 幅度的溢出极限环 vs 饱和运算平稳收敛）。
    """
    r = 0.95
    theta = 0.2 * np.pi
    a1_f = -2.0 * r * np.cos(theta)
    a2_f = r ** 2
    Q_c = 14
    a1_q = int(np.round(a1_f * (1 << Q_c)))
    a2_q = int(np.round(a2_f * (1 << Q_c)))
    b0_q = int(np.round(0.1 * (1 << Q_c)))

    # 1. 零输入量化极限环仿真
    n_lc = 250
    x_imp = np.zeros(n_lc, dtype=np.int64)
    x_imp[0] = 1 << 14  # Q15 中的 0.5
    y_fp = np.zeros(n_lc, dtype=np.int64)
    y_flt = np.zeros(n_lc, dtype=float)

    for n in range(n_lc):
        yn1 = y_fp[n - 1] if n >= 1 else 0
        yn2 = y_fp[n - 2] if n >= 2 else 0
        acc = b0_q * x_imp[n] - a1_q * yn1 - a2_q * yn2
        y_fp[n] = int(np.round(acc / (1 << Q_c)))

        yf1 = y_flt[n - 1] if n >= 1 else 0.0
        yf2 = y_flt[n - 2] if n >= 2 else 0.0
        y_flt[n] = (b0_q * x_imp[n] - a1_q * yf1 - a2_q * yf2) / (1 << Q_c)

    # 2. 溢出回绕 vs 饱和截幅仿真（脉冲激励撤除后观测自激）
    b0_ov = int(np.round((1.0 + a1_f + a2_f) * (1 << Q_c)))
    n_ov = 160
    t_ov = np.arange(n_ov)
    x_burst = np.zeros(n_ov, dtype=np.int64)
    x_burst[:40] = np.round(0.45 * 32767.0 * np.sin(2.0 * np.pi * 0.1 * t_ov[:40])).astype(np.int64)

    y_wrap = np.zeros(n_ov, dtype=np.int64)
    y_sat = np.zeros(n_ov, dtype=np.int64)
    for n in range(n_ov):
        yw1 = y_wrap[n - 1] if n >= 1 else 0
        yw2 = y_wrap[n - 2] if n >= 2 else 0
        acc_w = b0_ov * x_burst[n] - a1_q * yw1 - a2_q * yw2
        val_w = int(np.round(acc_w / (1 << Q_c)))
        y_wrap[n] = ((val_w + 32768) & 0xFFFF) - 32768

        ys1 = y_sat[n - 1] if n >= 1 else 0
        ys2 = y_sat[n - 2] if n >= 2 else 0
        acc_s = b0_ov * x_burst[n] - a1_q * ys1 - a2_q * ys2
        val_s = int(np.round(acc_s / (1 << Q_c)))
        y_sat[n] = max(-32768, min(32767, val_s))

    print(
        f"[Demo7] 16位定点状态运算与极限环实证 (r=0.95, 稳定极点):\n"
        f"  零输入尾部 [220:250]: 定点整数态范围 [{y_fp[220:].min()}, {y_fp[220:].max()}] LSB (量化极限环), "
        f"同系数浮点参考最大={np.max(np.abs(y_flt[220:])):.4f} LSB\n"
        f"  激励撤除后尾部 [120:160]: 整数回绕振幅={np.max(np.abs(y_wrap[120:]))} LSB, 饱和运算振幅={np.max(np.abs(y_sat[120:]))} LSB"
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.6))

    n_tail = np.arange(150, n_lc)
    ax1.plot(n_tail, y_flt[150:], color='gray', linewidth=2.5, alpha=0.65, label='同Q14系数浮点运算 (平滑衰减趋近0)')
    ax1.step(n_tail, y_fp[150:], where='mid', color='crimson', linewidth=1.6, label='16位定点舍入反馈 (锁死在 [-2, +2] LSB)')
    ax1.axhline(0, color='black', linestyle=':', linewidth=1.0)
    ax1.set_title('零输入量化极限环：极点安全但状态舍入导致持续底噪')
    ax1.set_xlabel('采样点序号 n (激励已于 n=0 后清零)')
    ax1.set_ylabel('输出幅度 (LSB 整数刻度)')
    ax1.set_ylim([-5.5, 5.5])
    ax1.legend(loc='upper right', fontsize=8.8)
    ax1.grid(True, linestyle='--', alpha=0.6)

    n_all = np.arange(n_ov)
    ax2.axvspan(40, n_ov - 1, color='gray', alpha=0.08, label='输入彻底归零区间 (n >= 40)')
    ax2.plot(n_all, y_wrap, color='crimson', linewidth=1.4, label='补码回绕 (Wrap-around：激发 ±19000 溢出极限环)')
    ax2.plot(n_all, y_sat, color='royalblue', linewidth=1.8, label='饱和截幅 (Saturation：撤除激励后平滑衰减)')
    ax2.set_title('溢出极限环 vs 饱和算术：回绕引发的大幅度自激振荡')
    ax2.set_xlabel('采样点序号 n')
    ax2.set_ylabel('16位有符号输出 (int16)')
    ax2.set_xlim([0, n_ov - 1])
    ax2.set_ylim([-36000, 36000])
    ax2.legend(loc='upper right', fontsize=8.5)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'iir_07_limit_cycle.png'), dpi=150)
    plt.close()


if __name__ == '__main__':
    print("Generating DSP-05 IIR Filter Design Figures...")
    demo1_iir_vs_fir()
    demo2_analog_prototypes()
    demo3_bilinear_warping()
    demo4_impulse_invariant_aliasing()
    demo5_sos_quantization()
    demo6_phase_and_group_delay()
    demo7_fixed_point_limit_cycle()
    print("Done. Figures saved in:", OUTPUT_DIR)
