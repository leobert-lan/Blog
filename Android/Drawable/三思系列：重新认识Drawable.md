# 三思系列：重新认识Drawable

## 前言
[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

前一段时间看到宏洋公众号推送了一篇关于splash页面动效的文章，具体为：将一个英文单词拆分为多个字母，散落在屏幕中，然后按照一定的路径回归，最终展示一段流光效果，完成splash页面。

当时文章中提到的做法是自定义View的实现。当时脑海中灵光一闪，感觉还是用Drawable来干这个事情更加合适。

记忆中，我曾经整理过一篇Drawable基础内容的文章，可惜丢失了，在开始干这件事情之前，我们把这一块内容再完整的梳理一遍。

这篇文章会比较长，先给出导图

![guide.png](https://github.com/leobert-lan/Blog/blob/main/Android/Drawable/%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97%EF%BC%9A%E9%87%8D%E6%96%B0%E8%AE%A4%E8%AF%86Drawable/Drawable_guide.png)

## Drawable的设计意图