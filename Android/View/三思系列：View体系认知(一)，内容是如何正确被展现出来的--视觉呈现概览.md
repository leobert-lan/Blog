# 三思系列：View体系认知(一)，内容是如何正确被展现出来的--视觉呈现概览

## 前言

> 这是View体系认知子系列的第一篇，这一篇会探知Android中，是通过`怎么的设计`
> 让视图正确呈现在屏幕上的。

[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

[关于View系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8EView%E7%B3%BB%E5%88%97.md)
极力建议读者了解一下 `为什么撰写这个系列`

考虑到博客不适合做大量的代码展现，我会以 WorkShop 的形式展现这些代码。[链接](https://github.com/leobert-lan/ViewWorkShop)

我们知道，在GUI编程中，必然存在一套试图体系内容，Android中也有一套，抛开掉底层内容，和Compose中的内容， 我们这一篇，一同探究下 `Framework中`，View体系 `如何做视觉呈现`。

---
补充：2021-02-22

感谢读者 `鲁班贼六`的建议，补充内容导图

这篇文章篇幅较长，在 View 的 measure 机制上花费了不少篇幅。本文尝试先抛开 `Android已有知识体系`，模拟 `从现实情况思考`，以建立认知体系的情况。

所以文章的内容编排和导图有一定出入。

![正确显示一个任意界面](./三思系列：View体系认知(一)/display_content.png)

> 注:本文中不涉及：
> * Canvas绘制基础
> * 屏幕渲染底层机制

我们会先思考，如何描述一个任意的界面，引出 View 继承体系，和 View-Tree 视图树。

再逆推一波：当界面被描述后，需要正确显示存在以下三步：
* 将 `正确内容` 绘制在 `正确位置`
  * 本文中，Widget的内容绘制略
* 依据布局规则，确定布局位置。 **注**：`显示大小` 也可以算作 `布局规则` 的范畴
* 测量显示大小

我们会先从现实情况出发，思考并设计一种可行的 `测量规则` ，并不断完善它，重点在于：
* `理解` 这种设计是如何 `演化` 得来的
* `明白` 测量本身就和 `布局规则` 有关，`布局规则` 会影响到测量过程

如果读者对 某些内容 已经打下 坚实的基础，建议 选择性泛读。

---

## 如何描述一个任意的界面

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

此时仔细思考一下，对于一个 `View-tree` 而言,`测量`每一个节点大小的`意义`是什么？

> `准确的完成布局` 并 `完成自身的绘制`

但是有很重要的一点： `屏幕的大小`，屏幕的大小是 `固定的` 、 `明确的`，这意味着，界面能够单次展示的最大 区域已经固定。

同理，对于一个有 Parent 的 View，原则上来说，它的展示区域也被限定在 Parent的区域中。

但是仔细一想，这并 `不合理` 啊，有一种革命式的交互： `滑动` ，可以用有限的窗口，展示无限的内容。

所以，我们先记住 <a id="issue_1">一个情况</a>：

> 不同类型的ViewGroup，对应着不同的布局特性，他们对待 子View 的态度也是不同的，可以表现为
> * 子View 可以 要求 比自身大 的展示大小，最终满不满足以及如何满足是之后的事情。
> * 子View 可以 要求 比自身大 的展示大小，但是要了也不给。

这时我们可以总结一个结论，展示和绘制一个内容时，有两组大小需要被考虑：

* 内容本身的大小
* 用于展示的区域大小

同样的，当一个 View 或者 ViewGroup，称之为A 被置于 ViewGroup B 中时。

A的大小就是内容本身的大小，B的大小就是用于展示的区域大小，递归思考之后，整个View-Tree都是这样。

显然，测量工作从树的 `根节点开始`，按照经验，可以使用 `深度优先` 完成整个测量工作。

我们希望得到的，是每个 View 所对应的 `展示区域大小`。按照刚才举的例子分析实际情况，我们可以用三种方式来指定View的展示大小：

* 一个明确值
* 相对值：刚好能够放下它的内容 -- `wrap_content`
* 相对值：撑满 Parent 的空间 -- `match_parent`

并在测量时，得到准确的结果。

我们再思考这几个取值场景：

对于Child而言，

* 设置了 展示大小为 `明确值`，毋庸置疑，测量时一定可以得到这个明确值
* 设置了 展示大小为 `match_parent`, 因为测量是从 Parent 到 Child， 所以，`对于Child` 而言,只要Parent的测量工作已经完成， 即 `Parent` 已经测算出自己的 `精确大小`，
  那么Child使用 `match_parent` 是可以得到明确值的。但如果Parent没有完成测算，我们先不思考这个问题
* 设置了 `wrap_content`，显然，要先测算出 `其内容` 的大小，才能得到 `显示区域` 的 `明确值`

> 注 上面这一段内容，非常重要，值得仔细思考。另：上述的内容中，我们先忽略掉 `可能存在` 的 `内边距`。

刚才我们还有一些没有考虑的内容：

> Parent 没有完成测算，Child 设置了 `match_parent`

那么，至少我们可以确定 Parent `不可能` 指定了 `显示大小` 的 `明确值`，至于其他的情况，需要用数学归纳法 `讨论嵌套`，我们换个角度思考。

`根节点` 的ViewGroup，我们可以得到 `显示大小` 的 `明确值`，按照刚才的讨论，其子View，使用 `match_parent` 或者 `明确值` 时，结合Parent 信息，可以得到 `明确值`；

只有当其为 `wrap_content` 时，需要继续测量其内容，再根据内容的大小，确定自身显示大小。

可以确定，当树中的一个节点为`wrap_content` 时，将`该节点`作为根节点，取出子树，当该子树的 `所有分支` 都能够找到满足 `条件R` 的节点时， 该根节点能够确定自身需要的显示大小。
> <a id="issue_1_rule">条件R</a>为：该View
> * 指定 显示大小为 `match_parent` 或者 `明确值`
> * 或者其 `布局要求` 能够让 parent 大小撑满至一个 `明确值`

**上面这一段内容有点长，适当消化一下**

此时，我们可以做出一点约定：

> Parent 多承担一点责任，结合自身情况，和Child情况，先确定一下，Child是否可以得到明确的显示大小，
> * 如果不可以，就将自身信息传递给Child，让它向下继续处理
> * 如果可以，那么 Parent 可以得出Child的显示大小, **注意** `不同类型的Parent`，应该有`不同的计算方式`。 这在[前面](#issue_1)提到过

### 确定测量规则

经过上面的思考，我们可以拟定测量规则了。

1. 测量必然从一个`明确自身展示大小` 的 ViewGroup 开始
2. 对于一个`子View` -- `A`，当其 `Parent` -- `P` 判断出 `A`
    * 可以得到 `明确的` 显示大小时，将 该信息： `可准确得到结果` + `结果值` 传递给 子View A； *注意，结果值是 Parent 按照自身规则计算的，和子View要求的可能不一致*
    * 否则，将 P 的 `自身大小` 和 `你还需要继续测量以得到结果` 的信息传递给 子View A。
3. 对于一个Parent，如果它是 `wrap_content`，则需要在子View 的显示大小都确定时，再计算自身大小。
4. 只要View-Tree中还 存在 `未确定` 自身 显示大小 的节点。就需要从根节点开始，继续遍历处理测量。

让表达更加准确一些，`可准确得到结果` 用 `EXACTLY` 代替。 `你还需要继续测量以得到结果` 用 `AT_MOST` 代替。

不言自明，`AT_MOST` 意味着会给定一个最大值。意味着：家族中的直系长辈 已经帮它 限定了人身自由。

> 方便准确表达，将他们称为 `测量模式`，简称 `mode` ：
>
> * `EXACTLY`：Parent 已经为 Child 决定了显示大小，按照规则，Child 应当使用 Parent 给定的值
> * `AT_MOST`：Parent 已经为 Child 决定了最大显示大小，按照规则，Child 自行决定使用 `最大不超过该值` 的显示大小

> 方便表达, 将 `显示大小` 简称为 `size`
>
> 显示和屏幕像素数量有关，显然，该数量是自然数范畴。size 在绝大多数情况下，可以用 Int值 准确表达，极少数情况下，大到越界，但极不合理。

若使用对象封装 `mode` 和 `size`，会出现大量的对象创建，这一点都不优雅，可以将 Int 分为 `高位区域` 和 `低位区域` 分别表达 `mode` 和 `size`
**这也是Android中采用的设计**

考虑到 `测量模式` 中，还可能存在 Parent 不约束 Child 的情况。

我们使用一个 `32位Int` 的 `高2位` 标识 `mode`，`低30位` 标识 `size`

### 进一步优化以减少遍历

规则的第4点中，是通过 `迭代` 的方式，完成整个树中所有节点的测量，按照实际分析，我们可以用 `递归`
来简化。

> 我们约定, 对于一个 设置了 `wrap_content` 的尾端节点，如果它没有实质的内容物，我们也认为它 `已经测量出了` 需要的展示大小

那么在一次递归中，我们就可以完成整个树的测量。

在 `递` 的过程中，仅有设置为 `wrap_content` 的 Parent角色 无法完成准确测量，而 `尾端节点` 必然完成了自身的测量。

开始 `归` 的过程，我们可以确定，每 `归` 到一个 Parent，

* 已经完成测量的继续 `归`，
* 没有完成测量的，它的 Children 都完成了测量，则按照 `wrap_content` 的定义，它必然可以完成测量，然后继续 `归`

最终整棵树完成测量。

### 完善规则，再添加一种mode

前面我们提到了 `滑动` 这一交互形式，可以利用 `有限的` 展示空间，显示 `无限的` 内容。

即，我们会遇到一些场景，Child 并不会收到 Parent 的制约。更加准确的说，是 `内容` 不受到 `呈现主体` 在显示空间上的制约。

而这个场景，超越了 `EXACTLY` 和 `AT_MOST` 两种测量模式的功能，我们还需要一种配套的测量模式：

`UNSPECIFIED`，即 Parent 不约束 Child，Child按照自身情况，自行测算。

> 注：对于 `UNSPECIFIED` ，`不要` 强行结合场景，尤其是 `不要` 利用 `warp_content`或者 `match_parent`的概念去理解。他们虽然有一些关联，
> 但并不是一个范畴的内容，也不可以相互推导。
>
> 因此，我单独将其拎了出来。

### 编码以验证

> 参考Android中FrameLayout的布局规则，它对于Child要求的大小为：
> 子View 可以 要求 比自身大 的展示大小，但是超过自身显示范围的不予显示。
> 所以，不 按照自身情况 调整 子View的 size

先给View添加一些必要的内容：

```kotlin
open class View {

    companion object {
        const val layout_width = "layout_width"
        const val layout_height = "layout_height"
        var debug = true
    }

    var tag: Any? = null

    var parent: View? = null

    val layoutParams: MutableMap<String, Int> = mutableMapOf()

    var measuredWidth: Int = WRAP_CONTENT

    var measuredHeight: Int = WRAP_CONTENT

    val heightMeasuredSize: Int
        get() = android.view.View.MeasureSpec.getSize(measuredHeight)

    val widthMeasuredSize: Int
        get() = android.view.View.MeasureSpec.getSize(measuredWidth)

    val heightMeasureMode: Int
        get() = android.view.View.MeasureSpec.getMode(measuredHeight)

    val widthMeasureMode: Int
        get() = android.view.View.MeasureSpec.getMode(measuredWidth)


    private var measured: Boolean = false

    fun isMeasured() = measured

    //绘制能力
    protected open fun onDraw(canvas: Canvas) {

    }

    //布局能力
    protected open fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {

    }

    fun measure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        if (!measured) {
            onMeasure(widthMeasureSpec, heightMeasureSpec)
        }
    }

    //测量能力
    protected open fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        setMeasuredDimensionRaw(widthMeasureSpec, heightMeasureSpec)
        debugMeasureInfo()
    }

    protected fun debugMeasureInfo() {
        if (debug) {
            Log.d(
                "view-debug",
                "$tag has measured: $measured, w mode:${getMode(widthMeasureMode)}, w size: $widthMeasuredSize " +
                        "h mode:${getMode(heightMeasureMode)}, h size: $heightMeasuredSize "
            )
        }
    }

    protected fun setMeasuredDimension(measuredWidth: Int, measuredHeight: Int) {
        setMeasuredDimensionRaw(measuredWidth, measuredHeight)
    }

    private fun setMeasuredDimensionRaw(measuredWidth: Int, measuredHeight: Int) {
        this.measuredWidth = measuredWidth
        this.measuredHeight = measuredHeight
        measured = true
        if (debug) {
            Log.d(
                "view-debug",
                "$tag mark has measured: $measured"
            )
        }
    }
}
```

添加一个FrameLayout：

```kotlin
class FrameLayout : ViewGroup() {
    override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        //handle horizon
        val widthMode = View.MeasureSpec.getMode(widthMeasureSpec)
        var widthSize = View.MeasureSpec.getSize(widthMeasureSpec)

        var wMeasured = false
        var hMeasured = false
        when (widthMode) {
            View.MeasureSpec.EXACTLY -> {
                // widthSize 即为Parent 为此决定的准确值，直接采用
                wMeasured = true
            }
            View.MeasureSpec.AT_MOST -> {
                // 需要再次测量，但可以保存该信息了
                measuredWidth = widthMeasureSpec
            }
            else -> {
                throw IllegalStateException("暂不支持测量模式：$widthMode")
            }
        }

        //同理处理 vertical方向

        val heightMode = View.MeasureSpec.getMode(heightMeasureSpec)
        var heightSize = View.MeasureSpec.getSize(heightMeasureSpec)

        when (heightMode) {
            View.MeasureSpec.EXACTLY -> {
                hMeasured = true
            }
            View.MeasureSpec.AT_MOST -> {
                measuredHeight = heightMeasureSpec
            }
            else -> {
                throw IllegalStateException("暂不支持测量模式：$widthMode")
            }
        }

        if (hMeasured && wMeasured) {
            setMeasuredDimension(widthMeasureSpec, heightMeasureSpec)
        }

        children.forEach {
            val childWidthMeasureSpec = makeMeasureSpec(widthMode, widthSize, it.layoutWidth)
            val childHeightMeasureSpec = makeMeasureSpec(heightMode, heightSize, it.layoutHeight)
            it.measure(childWidthMeasureSpec, childHeightMeasureSpec)
        }


        if (!hMeasured || !wMeasured) {
            var w = 0
            var h = 0
            children.forEach {
                if (!wMeasured)
                    w = maxOf(w, it.widthMeasuredSize)

                if (!hMeasured)
                    h = maxOf(h, it.heightMeasuredSize)
            }

            if (wMeasured)
                w = widthSize

            if (hMeasured)
                h = heightSize

            setMeasuredDimension(
                View.MeasureSpec.makeMeasureSpec(w, widthMode),
                View.MeasureSpec.makeMeasureSpec(h, heightMode),
            )
        }
        if (!allChildHasMeasured())
            throw IllegalStateException("child 未全部完成测量")

        debugMeasureInfo()
    }

    private fun makeMeasureSpec(mode: Int, size: Int, childSize: Int): Int {
        // 参考Android中FrameLayout的布局规则，它对于Child要求的大小为：
        // 子View 可以 要求 比自身大 的展示大小，但是超过自身显示范围的不予显示。
        // 所以，不 按照自身情况 调整 子View的 size
        val childMode = when (childSize) {
            WRAP_CONTENT -> View.MeasureSpec.AT_MOST
            else -> View.MeasureSpec.EXACTLY

        }

        val childSize2 = when (childSize) {
            WRAP_CONTENT -> size
            MATCH_PARENT -> size
            else -> childSize
        }
        return View.MeasureSpec.makeMeasureSpec(childSize2, childMode)
    }

    private fun allChildHasMeasured(): Boolean {
        val i = children.iterator()
        while (i.hasNext()) {
            if (!i.next().isMeasured())
                return false
        }

        return true
    }

}
```

以上代码 结合前面的规则 理解下即可

目前还没有到LayoutParam的阶段，我们将 必要的布局信息 声明在 map 中存储。

我们适当添加添加一些助手类，以建立View-tree

```kotlin
enum class Mode(val v: Int) {

    /**
     * Measure specification mode: The parent has not imposed any constraint
     * on the child. It can be whatever size it wants.
     */
    UNSPECIFIED(0 shl 30),

    /**
     * Measure specification mode: The parent has determined an exact size
     * for the child. The child is going to be given those bounds regardless
     * of how big it wants to be.
     */
    EXACTLY(1 shl 30),

    /**
     * Measure specification mode: The child can be as large as it wants up
     * to the specified size.
     */
    AT_MOST(2 shl 30)
}

class A {
    companion object {
        fun getMode(v: Int): Mode {
            Mode.values().forEach {
                if (it.v == v)
                    return it
            }
            throw IllegalStateException()
        }
    }
}
```

以上代码不言自明

```kotlin
typealias Decor<T> = (v: T) -> Unit

val MATCH_PARENT: Int = android.view.ViewGroup.LayoutParams.MATCH_PARENT
val WRAP_CONTENT = android.view.ViewGroup.LayoutParams.WRAP_CONTENT

var View.layoutWidth: Int
    get() {
        return layoutParams[View.layout_width] ?: WRAP_CONTENT
    }
    set(value) {
        layoutParams[View.layout_width] = value
    }

var View.layoutHeight: Int
    get() {
        return layoutParams[View.layout_height] ?: WRAP_CONTENT
    }
    set(value) {
        layoutParams[View.layout_height] = value
    }


fun root(): ViewGroup = FrameLayout().apply {
    this.layoutWidth = 1080
    this.layoutHeight = 1920
}

inline fun ViewGroup?.frameLayout(decor: Decor<FrameLayout>): ViewGroup {
    val child = FrameLayout()
    child.let(decor)
    return this?.apply { addView(child) } ?: child
}

inline fun ViewGroup.view(decor: Decor<View>): ViewGroup {
    val child = View()
    child.let(decor)
    return this.apply { addView(child) }
}
```

用以实现树结构描述的助手，不言自明

偷个懒，不设计单元测试了，构建一个结构：

```kotlin
class ViewTest {

    @Test
    fun testMeasure() {

        val tree = root().frameLayout { v1 ->

            v1.tag = "v1"
            v1.layoutWidth = MATCH_PARENT
            v1.layoutHeight = WRAP_CONTENT

            v1.frameLayout { frameLayout ->
                frameLayout.tag = "v2"
                frameLayout.layoutWidth = MATCH_PARENT
                frameLayout.layoutHeight = WRAP_CONTENT

                frameLayout.view {
                    it.tag = "v3"
                    it.layoutWidth = 200
                    it.layoutHeight = 300
                }

                frameLayout.frameLayout {
                    it.tag = "v4"
                    it.layoutWidth = WRAP_CONTENT
                    it.layoutHeight = WRAP_CONTENT
                }
            }
        }

        tree.tag = "root"


        tree.measure(
            View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.EXACTLY)
        )
        assert(tree is FrameLayout)
        assertEquals(true, (tree as FrameLayout).allChildHasMeasured())
    }
}
```

直接看一下日志输出的信息：

```shell
I/TestRunner: started: testMeasure(osp.leobert.blog.code.ViewTest)
D/view-debug: root mark has measured: true
D/view-debug: v3 mark has measured: true
D/view-debug: v3 has measured: true, w mode:EXACTLY, w size: 200 h mode:EXACTLY, h size: 300 
D/view-debug: v4 mark has measured: true
D/view-debug: v4 has measured: true, w mode:AT_MOST, w size: 0 h mode:AT_MOST, h size: 0 
D/view-debug: v2 mark has measured: true
D/view-debug: v2 has measured: true, w mode:EXACTLY, w size: 1080 h mode:AT_MOST, h size: 300 
D/view-debug: v1 mark has measured: true
D/view-debug: v1 has measured: true, w mode:EXACTLY, w size: 1080 h mode:AT_MOST, h size: 300 
D/view-debug: root has measured: true, w mode:EXACTLY, w size: 1080 h mode:EXACTLY, h size: 1920 
I/TestRunner: finished: testMeasure(osp.leobert.blog.code.ViewTest)
```

考虑到 一组 Parent 和 Child 有9种组合，我们全部验证一下。限于篇幅就不放代码和结果了

---

> 小结：上面通过很长一段篇幅，让我们在 `抛开Android的知识` 的前提下：
> > 1. 思考了如何设计一套系统，用以描述任意的界面
>
> 根据经验确定了使用 `视图树` 的方式，进行界面的描述，并意识到，应用 `不同的类` 来封装不同的功能，相互配合，完成界面描述工作。
> > 2. 思考了描述尺寸的 `两种方式` 、`三种取值类型`，并延伸出 `测量` `视图树` 每个节点的 `显示大小` 问题。
>
> 从现实角度出发，得出一种测量方式，并进行了优化，得出结论：
> * 测量过程从 Parent 到 Child。Parent 结合自身情况和 Child的情况，为 Child 决定测量的`模式` 即 `mode`， 以及 `EXACTLY` 模式下的精准值 和 `AT_MOST` 模式下的 `最大值` 参考值
>
>   * 从 Parent 到 Child 表现为：测量的入口为 `measure()`，其中封装了调用自身`onMeasure()` 的逻辑, 具体ViewGroup 类覆写 `onMeasure()` 并调用 Child的 `measure()` 方法,传递测量过程
>   * 显示大小的 `测量` 和 `布局规则` 有关
> 
> * 通过一次递归即可测量出视图树每个节点的显示大小
>
> 至此，我们对这套测量机制已经有了足够的认知，但是请注意，它还没有被完善。

## 确定布局位置

在前面，我们思考了一套可行的测量方案，其中我们提到：[一个情况](#issue_1)

并且，提出了[条件R](#issue_1_rule), 我们在其中提到了一个概念： `布局规则`

结合我们的经验，不同的GUI中，都会有布局规则体系。为了解决可能出现的布局需求，均抽象了不同的布局类，以实现不同的规则。

前面我们也提到了，不同的规则下，ViewGroup 对 子View 的测量是不同的。

这很合理，`测量的目的` 是为了 `正确布局`，不同的布局规则，具有特定的测量规则。

### 使用 LayoutParams 描述布局规则和信息

在前面，我们参考Android 建立了 FrameLayout 类，实现了 `帧布局` 的规则， 当然，这一种规则还不足以处理各种界面布局需求，还有更多的ViewGroup子类 等着我们实现。

> 换个说法：当 一个View 被 添加到 一个ViewGroup 中时，需要按照该ViewGroup的布局规则，阐述自身的布局信息.
> 必要信息不可缺省


显然，

* 按照面向对象思想，布局规则簇 应该被封装为类，称之为 `LayoutParams`。
* 按照单一职责原则，不同的布局规则，对应不同的ViewGroup子类，也对应不同的 `LayoutParams`类，显然这是一一对应的
* 按照依赖倒置原则，View 的 layoutParam 依赖于 抽象，而不是某个规则的具体类；
* 按照里氏代换原则，LayoutParams的继承关系，和ViewGroup的继承关系应当是对应的；

按照经验，我们会写出如下代码，一个 `必须指定宽高规则` 的 `ViewGroup.LayoutParams 基类`。

而视图 `可以` 存在 `内、外边距`，这可以被认为是 `基本规则`。

继续为FrameLayout 加上 `重力` 规则。

我们很快写出如下代码：

```kotlin
abstract class ViewGroup : View() {
    open class LayoutParams(var width: Int, var height: Int) {

    }

    open class MarginLayoutParams(width: Int, height: Int) : LayoutParams(width, height) {
        var leftMargin = 0

        var topMargin = 0

        var rightMargin = 0

        var bottomMargin = 0
    }
}

class FrameLayout : ViewGroup() {
    class LayoutParams(width: Int, height: Int) : ViewGroup.MarginLayoutParams(width, height) {
        val UNSPECIFIED_GRAVITY = -1

        var gravity = UNSPECIFIED_GRAVITY
    }

    override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
    }

    override fun checkLayoutParams(layoutParams: ViewGroup.LayoutParams): Boolean {
        return layoutParams is LayoutParams
    }

    override fun generateDefaultLayoutParams(): ViewGroup.LayoutParams {
        return LayoutParams(MATCH_PARENT, MATCH_PARENT)
    }
}
```

并对原先的Demo工程进行重构， *限于篇幅，略去相关代码*

> 注：按照里氏代换原则，我们定义的 LayoutParams 体系在使用中时，可能会遇到 `输入不符合期望` 的问题。此时我们需要了解一下：
> `契约式设计`：
> > 使用契约式设计，类中的方法需要声明前置条件和后置条件。前置条件为真，则方法才能被执行。而在方法调用完成之前，方法本身将确保后置条件也成立。
>
> 于是，在ViewGroup 体系中，设计了：
> * checkLayoutParams(layoutParams: ViewGroup.LayoutParams): Boolean
> * generateDefaultLayoutParams(): ViewGroup.LayoutParams
> 
> 我们可以采用两种契约：
> * 输入的LayoutParams 必须满足约束，否则抛出异常
> * 输入的LayoutParams 需要满足约束，否则使用默认规则

### 获得布局规则信息、按照ViewGroup 的布局规则进行布局

> 至此，我们已经理解了：
> * 使用视图树描述一个任意视图
> * 用不同的 ViewGroup 子类描述不同的布局，他们具有特定的布局规则；用不同的 Widget 展现不同的内容
> * 一种 测量`视图树各个节点` 的 `显示大小` 的测量方式
> * 不同的规则，决定了显示大小测算的细节有所不同
> * 使用LayoutParams 描述布局规则信息

在此基础上，我们需要接受设定：

> 存在一个机制，可以正确地解析 `视图树各个节点` 中申明的 `布局规则信息`，这些信息，会存储在正确的
> LayoutParams 对象中，被对应的节点所持有，以待使用。
>
> 这个机制，我们先忽略。

按照刚才获得的经验，布局和测量的过程类似，

我们定义 `layout()` 和 `onLayout()` 方法

```kotlin
open class View {
    open fun layout(l: Int, t: Int, r: Int, b: Int) {
        //todo
    }

    //布局能力
    protected open fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {

    }
}
```

对于参数，约定为：
* l Left position, relative to parent
* t Top position, relative to parent
* r Right position, relative to parent
* b Bottom position, relative to parent

在完成了 `大小测试` 和 `布局规则解析` 的前提下，这些相对值的计算并不复杂。

我们约定，实际的布局逻辑，在onLayout中完成，而layout方法，用于实现 `前置条件`，onLayout调用 和 `状态维护`

对于 ViewGroup 而言，需要遍历Children，为每个 Child，使用其显示大小信息&布局规则信息，确定其布局位置，即 l,t,r,b 四个参数值。
调用 Child 的 layout() 方法。

对于 Widget 而言，则是需要决定Content的展示区域，因为 Content 不再是 View，不再需要继续向下调用 layout 方法。

至此，所有的准备工作均已完成，接下来，就是绘制工作。

## 最后一步，绘制在正确位置

在此之前，我们已经得到了视图树每个节点的正确位置，此时，只需要将内容绘制在对应位置，即可通过屏幕呈现在用户眼前。

按照之前的经验，我们定义：

* draw(canvas:Canvas) 方法，封装整个绘制流程
* onDraw(canvas:Canvas) 方法，实现内容的绘制
* 如果在ViewGroup中覆写onDraw(canvas:Canvas) 同时 实现 `自身内容的绘制`，*例如背景* ，和 `分发 Child 的绘制`，这并不符合开闭原则
故而添加 dispatchDraw(canvas: Canvas) 用以实现 `分发 Child 的绘制`
  
其实到此为止，我们已经对 `正确展示内容` 有了比较完善的认知，绘制的内容，理解不复杂，但内容很庞杂，本篇就不再展开了。

## 展望

本身还计划再写如下内容的：

* 和Framework中的实现思路进行对比
* 编码验证布局规则 等

限于篇幅，这些内容被择掉了。不过我会将一些 `编码验证`的内容以 [WorkShop](https://github.com/leobert-lan/ViewWorkShop) 的形式展现。

下一篇，会对 `View`体系的 `交互` 功能进行探索。`点关注不迷路`。

> 注：关于WorkShop的内容，原定计划是配合博客中的知识体系，独立建立一套 `简单的`，`可视交互` 系统。用以验证和帮助理解 Android-View 体系的知识。
> 
> 希望今年的业务时间还能比较充裕。