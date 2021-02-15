# 三思系列：View体系认知(一)，内容是如何正确被展现出来的--视觉呈现概览

## 前言

> 这是View体系认知子系列的第一篇，这一篇会探知Android中，是通过`怎么的设计`
> 让视图正确呈现在屏幕上的。

[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

[关于View系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8EView%E7%B3%BB%E5%88%97.md)
极力建议读者了解一下 `为什么撰写这个系列`

我们知道，在GUI编程中，必然存在一套试图体系内容，Android中也有一套，抛开掉底层内容，和Compose中的内容， 我们这一篇，一同探究下 `Framework中`，View体系 `如何做视觉呈现`。

## 描述一棵树

假如我们现在对Android的内容一无所知，如何`描述` 一个 `任意的界面`。

* 无论我们要达成什么效果，必然存在`一个虚拟窗体`，和物理屏幕相对应
* 系统层面抽象的绘制呈现过程，一定需要通过 这个 `虚拟窗体`，而我们描述的界面内容，会被放在窗体中
* 按照 `面向对象思想` 和 `单一职责原则`，描述 `这个窗体` 的类，假定被称为 `Window`，一定和描述视图的类 `不是同一个`。假定视图类被称为 `View`
* Window可以获知内部View的信息

在此基础上，

方案1：构建一个上帝类，它全知全能，能够 `记录` 和 `表达` 任意的"文字"、"图片"、"区块"等信息。

方案2：构建一个简单类 `View`，它有方式知道自己多大，并抽象了视图内容绘制，可以在内部放置子 `View`，并有方式确定如何放置；

显然，方案1不可取。我们`细化方案2`.

此时，我们做出了一个假设：`View`拥有3个能力

* 测算自身大小
* 可以放置`子View`；并知道其所在位置，即拥有 `布局能力`
* 准确的知道如何绘制自身所代表的内容

在此基础上，我们就可以将 `任意界面` 拆分结构，这个结构可以用 `树` 来表达。

<a id="id_tree_rule">目前我们约定：</a>

* 每个 `View` 只能有 `一个` 双亲
* 作为双亲的 `View`，仅用来描述 `布局信息`
* 实际 `可视` 、 `可交互` 的 `View`， 描述其代表的内容信息

于是 `描述任意界面` 的问题，就可以用 `描述一棵树` 来解决。

> 注：目前这个约定还很粗糙，但是不影响我们进行问题认知

> 树的存储方法有3种：
> * 双亲表示法
> * 孩子表示法
> * 孩子兄弟表示法
>
> 以及基于以上方法的改进版本

为了更加方便地向上和向下检索，我们使用 `双亲孩子表示法` 这一改进版本。

### 细化方案2，ViewGroup和Widget，各司其职

按照我们上面对[树的约定](#id_tree_rule)

我们按职责细分：

* 一部分View 专注于对子View的布局能力，而不再表达 "文字"、"图片"等内容信息，我们将其抽象为子类 `ViewGroup`。因为没有具体表达
  `如何放置子View`的 `规则`，所以它是`抽象类`。

* 将 `非包含子View` 的，表达"文字"、"图片"等特定信息的View，归纳为Widget。

> 小结：在上面的阶段性成果中，我们已经细化了方案，用树的形式，描述了界面的结构和内容。
> 存在一个预设的ViewGroup，作为树的根节点。

下面我们先给出一些伪代码。

```kotlin
open class View {
    var parent: View? = null

    //绘制能力
    protected open fun onDraw(canvas: Canvas) {

    }

    //布局能力
    protected open fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {

    }

    //测量能力
    protected open fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {

    }
}

abstract class ViewGroup : View() {
    protected val children = arrayListOf<View>()

    abstract override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int)

    fun addView(view: View) {
        if (view.parent != null) {
            throw IllegalArgumentException("view has a parent")
        }
        children.add(view)
        view.parent = this
    }

}

```

## 测量大小

接下来我们设计测量大小的能力，

假定有一个显示文字的View，他可以测算自身的大小，但这有3种可能：

* 恰好装下文字内容
* 被指定了大小，但和第一种大小不一致，这又分两个情况：
  * 人为指定的明确值
  * 被限定的区域，比如无法超过屏幕大小


再假定一个ViewGroup，仔细一想，巧了，它也有这3种可能。

此时仔细思考一下，对于


## 确定布局位置


