# 数字信号处理（DSP）痛苦系列代码仓库

本目录包含《痛苦系列》数字信号处理专栏全部篇章的可运行 Python 仿真验证脚本。

## 目录索引

| 篇章 | 对应 Issue | 目录与脚本 | 说明 |
|---|---|---|---|
| **DSP-01** | [Issue 70](https://github.com/leobert-lan/Blog/issues/70) | [`dsp01/pain_series_01_demo.py`](./dsp01/pain_series_01_demo.py) | 采样定理、混叠效应、脉冲响应与空谷回声卷积合成 |
| **DSP-02** | [Issue 71](https://github.com/leobert-lan/Blog/issues/71) | [`dsp02/pain_series_02_demo.py`](./dsp02/pain_series_02_demo.py) | DTFT 与 DFT 频域切片、卷积定理、栅栏效应与循环卷积 |
| **DSP-03** | [Issue 72](https://github.com/leobert-lan/Blog/issues/72) | [`dsp03/pain_series_03_demo.py`](./dsp03/pain_series_03_demo.py) | Z 变换收敛域（ROC）、3D 零极点曲面、极点越狱与 50Hz 陷波器仿真 |
| **DSP-04** | [Issue 73](https://github.com/leobert-lan/Blog/issues/73) | [`dsp04/pain_series_04_demo.py`](./dsp04/pain_series_04_demo.py) | FIR 线性相位、矩形窗频域卷积与吉布斯过冲、经典窗函数与 Type 2 代数约束 |
| **DSP-05** | [Issue 74](https://github.com/leobert-lan/Blog/issues/74) | [`dsp05/pain_series_05_demo.py`](./dsp05/pain_series_05_demo.py) | IIR 极点反馈共振、双线性变换与预畸变、16位定点量化 Wilkinson 效应与 SOS 级联 |
| **DSP-06** | [Issue 75](https://github.com/leobert-lan/Blog/issues/75) | [`dsp06/pain_series_06_demo.py`](./dsp06/pain_series_06_demo.py) | FFT 基2时域抽取（DIT）蝶形演进、位反转寻址、快速卷积与补零分辨率辨析 |
| **DSP-07** | [Issue 76](https://github.com/leobert-lan/Blog/issues/76) | [`dsp07/pain_series_07_demo.py`](./dsp07/pain_series_07_demo.py) | 全局 FFT 时序丢失、STFT 时频测不准 Gabor 极限、脑电节律变化与级联流水线 |

## 环境依赖

```bash
pip install numpy matplotlib scipy
```

## 运行方式

在 `BlogCode` 根目录下执行对应脚本即可：

```bash
python DSP/dsp01/pain_series_01_demo.py
python DSP/dsp02/pain_series_02_demo.py
python DSP/dsp03/pain_series_03_demo.py
python DSP/dsp04/pain_series_04_demo.py
python DSP/dsp05/pain_series_05_demo.py
python DSP/dsp06/pain_series_06_demo.py
python DSP/dsp07/pain_series_07_demo.py
```
