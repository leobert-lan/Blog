# 三思系列：重新认识Drawable

## 前言

[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

前一段时间看到宏洋公众号推送了一篇关于splash页面动效的文章，具体为：将一个英文单词拆分为多个字母，散落在屏幕中，然后按照一定的路径回归，最终展示一段流光效果，完成splash页面。

当时文章中提到的做法是自定义View的实现。当时脑海中灵光一闪，感觉还是用Drawable来干这个事情更加合适。

记忆中，我曾经整理过一篇Drawable基础内容的文章，可惜丢失了，在开始干这件事情之前，我们把这一块内容再完整的梳理一遍。

这篇文章会比较长，先给出导图

![guide.png](https://github.com/leobert-lan/Blog/blob/main/Android/Drawable/%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97%EF%BC%9A%E9%87%8D%E6%96%B0%E8%AE%A4%E8%AF%86Drawable/Drawable_guide.png)

## Drawable的设计意图

> A Drawable is a general abstraction for "something that can be drawn."  Most often you will deal with Drawable as the type of resource retrieved for drawing things to the screen; the Drawable class provides a generic API for dealing with an underlying visual resource that may take a variety of forms. Unlike a View, a Drawable does not have any facility to receive events or otherwise interact with the user.

这是SDK文档中的内容，大致含义呢：drawable是对于"**可以被绘制的内容**"的**抽象**。 多数情况下，我们将获取的资源作为Drawable绘制在屏幕上，
Drawable类提供了一个通用API，用于处理可能采用多种类型的底层可视资源。 不像View，Drawable**没有**任何接收事件或以其他方式与用户交互的功能。

为了简化绘制，Drawable中为使用者提供了一定的机制操作绘制：

> * The {@link #setBounds} method <var>must</var> be called to tell the
    > Drawable where it is drawn and how large it should be. All Drawables
    > should respect the requested size, often simply by scaling their
    > imagery. A client can find the preferred size for some Drawables with
    > the {@link #getIntrinsicHeight} and {@link #getIntrinsicWidth} methods.
>
> * The {@link #getPadding} method can return from some Drawables
    > information about how to frame content that is placed inside of them.
    > For example, a Drawable that is intended to be the frame for a button
    > widget would need to return padding that correctly places the label
    > inside of itself.
>
> * The {@link #setState} method allows the client to tell the Drawable
    > in which state it is to be drawn, such as "focused", "selected", etc.
    > Some drawables may modify their imagery based on the selected state.
>
> * The {@link #setLevel} method allows the client to supply a single
    > continuous controller that can modify the Drawable is displayed, such as
    > a battery level or progress level. Some drawables may modify their
    > imagery based on the current level.
>
> * A Drawable can perform animations by calling back to its client
    > through the {@link Callback} interface. All clients should support this
    > interface (via {@link #setCallback}) so that animations will work. A
    > simple way to do this is through the system facilities such as
    > {@link android.view.View#setBackground(Drawable)} and
    > {@link android.widget.ImageView}.


继续简要翻译一下重要内容

* setBounds 方法必须被调用，它告知了Drawable应该被绘制的位置和大小
* getPadding 方法可以获知一些Drawable绘制时的内边距信息
* setState 方法允许使用者告知Drawable应当在哪些状态时绘制，例如获取了焦点，被选中等
* setLevel 方法允许调用者提供一个连续的控制器，可以修改显示的可绘制内容， 例如电池电量或进度。一些Drawable可能会根据当前的level改变其图像
* Drawable可以展现动画，通过设置Callback接口回调给他的使用者，所有的使用者，需要通过 setCallback方法提供回调函数支持以让动画工作。一个简便方式是通过一些系统设施例如：View#setBackground 和
  ImageView

> 注：Drawable展现动画部分，这里翻译的比较晦涩，具体细节见：Drawable Api概览

小结：Android SDK中抽象了Drawable体系，不同于View体系，它仅负责描述可绘制的内容，不可进行用户交互，其子类将描述各类可绘制内容的特性。

## SDK中的Drawable子类概览

> 注：经过多次思考，我最终把这一段的草稿删除了，这部分体系实在是太大，浅写无异于copy官方文档，深挖就会影响文章关注的重点。
> 如果对系统中提供的Drawable子类感兴趣的，建议深入源码看一下。

## Drawable Api概览

在开头的设计意图探索中，我们已经阅读了几个关键API：`setBound`，`getPadding`，`setState`，`setLevel`，`setCallback`的信息

还有`getBound`，`copyBound`等获取边界信息的API，RippleDrawable和一些自定义的Drawable还覆写了`getDirtyBounds`，用以获取它可能涉及到的范围边界

横向的方向相关：`setLayoutDirection`，`getLayoutDirection`，`onLayoutDirectionChanged`

透明度相关：`setAlpha`，`getAlpha`

着色和颜色filter相关：`setColorFilter`，`getColorFilter`，`clearColorFilter`，
`setTint`，`setTintList`，`setTintMode`，`setTintBlendMode`

尺寸测量：`getIntrinsicWidth`，`getIntrinsicHeight`，`getMinimumWidth`，`getMinimumHeight`
当作为背景使用时，getMinimumXXX用于告知View建议使用的最小宽高。getIntrinsicXXX是获取一个Drawable的内在的、固有的宽高，这个值和设备屏幕密度是有关系的。

自我独立：`mutate`，和缓存机制有关，调用得到一个新的Drawable，这样自己的状态就不会影响到其他使用处。

重绘相关：`setCallback(@Nullable Callback cb)`，`getCallback()`，`invalidateSelf()`，
`scheduleSelf(@NonNull Runnable what, long when)`，`unscheduleSelf(@NonNull Runnable what)`

上面我们提到这一组API会详细说一下。以AnimationDrawable为例，这是一个动画Drawable，

```java
class AnimationDrawable {
    private void setFrame(int frame, boolean unschedule, boolean animate) {
        if (frame >= mAnimationState.getChildCount()) {
            return;
        }
        mAnimating = animate;
        mCurFrame = frame;
        selectDrawable(frame);
        if (unschedule || animate) {
            unscheduleSelf(this);
        }
        if (animate) {
            // Unscheduling may have clobbered these values; restore them
            mCurFrame = frame;
            mRunning = true;
            scheduleSelf(this, SystemClock.uptimeMillis() + mAnimationState.mDurations[frame]);
        }
    }
}
```

设置某一帧之后，如果是使用动画，则会调用scheduleSelf，时间戳是下一帧应该出现的时间戳。

```java
class Drawable {
    public void scheduleSelf(@NonNull Runnable what, long when) {
        final Callback callback = getCallback();
        if (callback != null) {
            callback.scheduleDrawable(this, what, when);
        }
    }
}
```

如果存在Callback，则调用Callback#scheduleDrawable。

以View的代码为例

```java
class View {
    public void scheduleDrawable(@NonNull Drawable who, @NonNull Runnable what, long when) {
        if (verifyDrawable(who) && what != null) {
            final long delay = when - SystemClock.uptimeMillis();
            if (mAttachInfo != null) {
                mAttachInfo.mViewRootImpl.mChoreographer.postCallbackDelayed(
                        Choreographer.CALLBACK_ANIMATION, what, who,
                        Choreographer.subtractFrameDelay(delay));
            } else {
                // Postpone the runnable until we know
                // on which thread it needs to run.
                getRunQueue().postDelayed(what, delay);
            }
        }
    }
}
```

很简单，验证合法性之后定时执行Runnable，Runnable的内容：

```java
class AnimationDrawable {
    public void run() {
        nextFrame(false);
    }

    private void nextFrame(boolean unschedule) {
        int nextFrame = mCurFrame + 1;
        final int numFrames = mAnimationState.getChildCount();
        final boolean isLastFrame = mAnimationState.mOneShot && nextFrame >= (numFrames - 1);

        // Loop if necessary. One-shot animations should never hit this case.
        if (!mAnimationState.mOneShot && nextFrame >= numFrames) {
            nextFrame = 0;
        }

        setFrame(nextFrame, unschedule, !isLastFrame);
    }
}
```
显示下一帧，逻辑非常清晰，不再进行解析。

> 小结: 这一段我们对Drawable的API进行了简单的梳理，略去了大量关于创建的API以及和开发不太紧密的API，完成了一次概览。
> 更完善的认知需要再仔细研读源码内容，限于篇幅不再展开。

## DrawableInflater
顾名思义，这是一个Drawable加载器，和LayoutInflater类似，从一种满足特定语法的语法式中解析出实例对象，显然，在Android中它用来处理xml语法的drawable资源文件。

看一下文档：

```java
/**
 * Instantiates a drawable XML file into its corresponding
 * {@link android.graphics.drawable.Drawable} objects.
 * <p>
 * For performance reasons, inflation relies heavily on pre-processing of
 * XML files that is done at build time. Therefore, it is not currently possible
 * to use this inflater with an XmlPullParser over a plain XML file at runtime;
 * it only works with an XmlPullParser returned from a compiled resource (R.
 * <em>something</em> file.)
 *
 * @hide Pending API finalization.
 */
```

需要注意，从性能角度上，这种创建严重依赖于构建时的预处理，因此，目前不可能利用它和 **XmlPullParser** 一起 **在运行时解析一个xml文件** 并创建对象实例
只适用于那些已经在资源编译阶段返回的XmlPullParser

我们知道，一个受检的xml document，会被解析为语法树，得到树中的标签节点和属性信息。

我们阅读DrawableInflater的代码，有两段关于创建Drawable具体实例的内容，这是根据tag创建实例的代码

```java
class DrawableInflater {
    private Drawable inflateFromTag(@NonNull String name) {
        switch (name) {
            case "selector":
                return new StateListDrawable();
            case "animated-selector":
                return new AnimatedStateListDrawable();
            case "level-list":
                return new LevelListDrawable();
            case "layer-list":
                return new LayerDrawable();
            case "transition":
                return new TransitionDrawable();
            case "ripple":
                return new RippleDrawable();
            case "adaptive-icon":
                return new AdaptiveIconDrawable();
            case "color":
                return new ColorDrawable();
            case "shape":
                return new GradientDrawable();
            case "vector":
                return new VectorDrawable();
            case "animated-vector":
                return new AnimatedVectorDrawable();
            case "scale":
                return new ScaleDrawable();
            case "clip":
                return new ClipDrawable();
            case "rotate":
                return new RotateDrawable();
            case "animated-rotate":
                return new AnimatedRotateDrawable();
            case "animation-list":
                return new AnimationDrawable();
            case "inset":
                return new InsetDrawable();
            case "bitmap":
                return new BitmapDrawable();
            case "nine-patch":
                return new NinePatchDrawable();
            case "animated-image":
                return new AnimatedImageDrawable();
            default:
                return null;
        }
    }
}
```

如果您已经在第二小节自行对Drawable的子类进行了概览，应该对这些内容不陌生了。

