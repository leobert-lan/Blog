# 好玩系列：优雅的处理ButterKnife和KAE被废弃

*最近反思了一下近期的工作，忽然就出现了一个想法，将平时干的好玩的事情，整理成一个系列，和大家分享一下，想来想去也没想好这个系列叫啥，索性就叫好玩系列得了。*

**文中涉及的代码均在 [此处](https://github.com/leobert-lan/UIBinding) 可以找到**

## 前言

如果你的项目中使用了ButterKnife或者Kotlin-Android-Extention（KAE）插件，近半年你一定关注过如下信息：
> Attention: This tool is now deprecated. Please switch to view binding. Existing versions will continue to work, obviously, but only critical bug fixes for integration with AGP will be considered. Feature development and general bug fixes have stopped. -- ButterKnife

> Resource IDs will be non-final in Android Gradle Plugin version 5.0, avoid using them in switch case statements
> Inspection info:Avoid the usage of resource IDs where constant expressions are required.  A future version of the Android Gradle Plugin will generate R classes with non-constant IDs in order to improve the performance of incremental compilation.
>
>Issue id: NonConstantResourceId -- lint

> The 'kotlin-android-extensions' Gradle plugin is deprecated. Please use this migration guide (https://goo.gle/kotlin-android-extensions-deprecation) to start working with View Binding (https://developer.android.com/topic/libraries/view-binding) and the 'kotlin-parcelize' plugin.

是的，这两个在Android中使用面很广的内容被标记为废弃了。

对于ButterKnife，被废弃的原因是：从AGP-5.0版本开始，R类生成的值不再是常量

对于KAE，问题如下：
* 类型安全：res下的任何id都可以被访问，有可能因访问了非当前Layout下的id而出错，难以利用lint等静态代码校验
* 空安全：运行时可能出现NPE
* 兼容性：只能在kotlin中使用，java不友好
* 局限性：不能跨module使用

按照官方或者社区的推荐，替代方案还是回归到findViewById or ViewBinding or DataBinding.

未来可能替代XML描述布局文件的技术：Compose还没有真正到来，而且一时半会也不可能把原先的内容全部迁移到Compose实现，所以我们还是要老老实实回归到上面的三个方案。

有些同学知识面广一点，立马想到了psi，通过分析代码文件的psi树，实现代码转换，直接搞一个插件来处理ButterKnife的迁移问题。


**当然，这篇文章并不准备去讲psi，虽然这是一个挺好玩的东西。下次有时间会专门写一个好玩的psi**

## 思考1：为什么要废弃ButterKnife

因为AGP生成的R类资源值不再是常量，无论是library还是application，那么要继续再思考一个问题：library的R类资源也不是常量，原先ButterKnife是怎么处理的？
我们知道，Butterknife有运行时反射用法，也有编译期使用apt预生成代码的用法。bk提供了gradle插件，用于copy原始R类内容,生成R2类，R2复刻了R的内容，但均为常量。因为注解中的内容，是需要在编译期确定，它被要求为常量，并且在编译时被优化。但我们知道，通过字节码技术，可以修改很多东西，无论是一个常量的值，还是索性连类都给换了。
一旦这个值被修改，注解中的信息便为谬误。但因为R2的存在，我们可以通过常量值反向获取到常量的名字，从而去使用R类。

## 思考2：是不是Butterknife所有的代码都没有意义了？

显然不是，因为findviewbyid还没用被革命性改变，bk中所有的核心代码还是有用的
如果你使用的apt方式，那么就有意思了，对于一个特定的target，bk生成的绑定代码完全是没有“废弃”风险的，我们完全可以拷贝其中的逻技，或者直接对生成类实行“拿来主义”
最终，我们只需要扔掉bk的gradle插件，注解和apt处理器，岁月静好。
如果你使用的是运行时反射方案，我不排斥运行时反射，虽然他会多耗一些时间，如果你不介意耗费更多的时间，完全可以改造bk的注解和逻辑，虽然它很好玩，但这并不是一个值得推荐的做法。

## 思考3：kae又是怎么帮助我们找到view的

没错，还是通过findviewbyid，它被废弃并不是犯了什么大错，只是不在适应潮流，且有各种各样的小毛病。
我们以Fragment为例子，看一下编译器为我们植入的代码：

```
public android.view.View _$_findCachedViewById(int var1) {
    if (this._$_findViewCache == null) {
       this._$_findViewCache = new HashMap();
    }

    android.view.View var2 = (android.view.View)this._$_findViewCache.get(var1);
    if (var2 == null) {
       android.view.View var10000 = this.getView();
       if (var10000 == null) {
          return null;
       }

       var2 = var10000.findViewById(var1);
       this._$_findViewCache.put(var1, var2);
    }

    return var2;
 }

 public void _$_clearFindViewByIdCache() {
    if (this._$_findViewCache != null) {
       this._$_findViewCache.clear();
    }

 }
```
以及：
```
// $FF: synthetic method
public void onDestroyView() {
  super.onDestroyView();
  this._$_clearFindViewByIdCache();
}
```

```
//源码
vMallAccountTitleBar.setTitle("我的钱包")

//反编译结果
((BarStyle4)this._$_findCachedViewById(id.vMallAccountTitleBar))
	.setTitle((CharSequence)"我的钱包");

```
可以很轻易的发现，具有多种场景下潜在的npe风险。本质上还是在使用findViewByID机制

## 思考4：是否可以最小程度重构实现从bk切换到databinding或者viewbinding
首先还是要粗略提一下databinding和viewbinding。记忆中databinding技术先于viewbinding，是Google提供的声明式UI解决方案，这里必须要岔开一句：什么是声明式UI？

这里我用SQL举个例子类比， select * from t where 't.id' = 1， 这就是声明式，声明一个符合规则的定则，让对应的系统执行，得到目标结果。相应的，对立面就是命令式，命令式需要准确的指出每一步操作的具体指令，以完成一个特定的算法。

肤浅的总结，声明式是底层实现了一类行为的抽象，其核心的算法或者控制段均被封装，只需要控制输入，即可得到输出。而命令式则完全需要自行实现。

理解了这一点，我们就会意识到，databinding本身不应该对外暴露这些view，只是这么干的话，项目迁移成本就会变大，所以还是选择了开放，这也就有了后来的viewbinding。

言归正传，原先用bk，我们需要一个根view作为起始点，以实现视图绑定，基本是找到Activity#setContentView(Int id)后activity的decorview，或者是viewholder#getRoot()，或者是开发者inflate得到的一个view等等。

不难判断，**如果彻底的修改代码，从基类出发应该是没什么方案。只能进行一件枯燥乏味的事情**

## 思考5：如果是kotlin语言下，利用属性代理是否可以简化代码修改

> 延伸：属性委托指的是一个类的某个属性值不是在类中直接进行定义，而是将其托付给一个代理类，从而实现对该类的属性统一管理。
> 属性委托语法格式：
>
>`val/var <属性名>: <类型> by <表达式>`


## 实践1：属性代理替代BK的注解

先定一个小目标,我们会将注解形式变成类似以下代码的形式：

```
val tvHello1 by bindView<TextView>(R.id.dialog)

val tvHello by bindView<TextView>(viewProvider, R.id.hello, lifecycle) {
    bindClick { changeText() }
}

val tvHellos by bindViews<TextView>(
    viewProvider,
    arrayListOf(R.id.hello1, R.id.hello2),
    lifecycle
) {
    this.forEach {
        it.bindClick { tv ->
            Toast.makeText(tv.context, it.text.toString(), Toast.LENGTH_SHORT).show()
        }
    }
}
```

那么我们需要先定义一个属性代理类，并实现操作符，以bindView为例，

我们先缓一缓，定义一个基类，接受属性持有者的生命周期，**以实现其生命周期走到特定节点时释放依赖**。

```
abstract class LifeCycledBindingDelegate<F,T>(lifecycle: Lifecycle): ReadOnlyProperty<F,T> {

    protected var property: T? = null

    init {
        lifecycle.onDestroyOnce { destroy() }
    }

    protected open fun destroy() {
        property = null
    }
}

internal class OnDestroyObserver(var lifecycle: Lifecycle?, val destroyed: () -> Unit) :
    LifecycleEventObserver {
    override fun onStateChanged(source: LifecycleOwner, event: Lifecycle.Event) {
        val lifecycleState = source.lifecycle.currentState
        if (lifecycleState == Lifecycle.State.DESTROYED) {
            destroyed()
            lifecycle?.apply {
                removeObserver(this@OnDestroyObserver)
                lifecycle = null
            }
        }
    }
}

fun Lifecycle.onDestroyOnce(destroyed: () -> Unit) {
    addObserver(OnDestroyObserver(this, destroyed))
}
```

这时候我们来处理findViewById的核心部分

```
class BindView<T:View>(
    private val targetClazz: Class<T>,
    private val rootViewProvider: ViewProvider,
    @IdRes val resId: Int,
    lifecycle: Lifecycle,
    private var onBind: (T.() -> Unit)?
):LifeCycledBindingDelegate<Any,T>(lifecycle) {


    override fun getValue(thisRef: Any, property: KProperty<*>): T {
        return this.property ?: let {

            val rootView = rootViewProvider.provide()
            val v = rootView.findViewById<T>(resId)
                ?: throw IllegalStateException(
                    "could not findViewById by id $resId," +
                            " given name: ${rootView.context.resources.getResourceEntryName(resId)}"
                )
            return v.apply {
                this@BindView.property = this
                onBind?.invoke(this)
                onBind = null
            }
        }
    }
}
```

我们需要几样东西以支持：
>`View#<T extends View> T findViewById(@IdRes int id)`

对应了**目标类**，**根View提供者**，**目标view的id**，**属性持有者的生命周期**和**初次属性初始化后的附加逻辑**

至于BindViews，我们如法炮制即可。

这时候会发现，这样使用太累了，对于Activity、Fragment、ViewHolder等常见的类而言，虽然他们提供根视图等内容的方式有所差别，但这种行为基本是可以抽象的。

以ComponentActivity为例，我们只需要定义扩展函数：

```
inline fun <reified T : View> ComponentActivity.bindView(@LayoutRes resId: Int) =
    BindView<T>(
        targetClazz = T::class.java,
        rootViewProvider = object : ViewProvider {
            override fun provide(): View {
                return this@bindView.window.decorView
            }
        },
        resId = resId,
        lifecycle = this.lifecycle,
        onBind = null
    )
```
就可以**比较方便的使用**，剩下来的Fragment、ViewHolder之类的东西，讲起来太啰嗦了，都是**如法炮制**。

再定义一个大而全的：
```
inline fun <reified T : View> Any.bindView(
    rootViewProvider: ViewProvider,
    @LayoutRes resId: Int,
    lifecycle: Lifecycle,
    noinline onBind: (T.() -> Unit)?
) =
    BindView<T>(
        targetClazz = T::class.java,
        rootViewProvider = rootViewProvider,
        resId = resId,
        lifecycle = lifecycle,
        onBind = onBind
    )
```

**实际项目中想怎么用完全看实际就行了。**

## 思考6：让DataBinding和ViewBinding拥有同样的特性是否有价值
当然是有价值的，一个大项目中，尤其是进行了模块化拆分，不同模块使用不同的技术是很正常的，DataBinding和ViewBinding并存的情况一定会发生，虽然我并没有真正遇到过同时使用的，**并且并不清楚同时使用会不会有bug**
## 实践2：支持DataBinding和ViewBinding
因为笔者项目中没有使用ViewBinding，我们就粗暴的只实现DataBinding了，其实都是获取Binding类实例而已，机制是一致的，**ViewBinding可以如法炮制**

得益于我们上面定义的基类，我们可以直接干一个处理DataBinding的子类了

```
class BindDataBinding<T : ViewDataBinding>(
    private val targetClazz: Class<T>,
    private val inflaterProvider: LayoutInflaterProvider,
    @LayoutRes val resId: Int,
    lifecycle: Lifecycle,
    private var onBind: (T.() -> Unit)?
) : LifeCycledBindingDelegate<Any, T>(lifecycle) {

    override fun getValue(thisRef: Any, property: KProperty<*>): T {

        return this.property ?: let {

            val layoutInflater = inflaterProvider.provide()
            val bind = DataBindingUtil.bind<T>(layoutInflater.inflate(resId, null))
                ?: throw IllegalStateException(
                    "could not create binding ${targetClazz.name} by id $resId," +
                            " given name: ${layoutInflater.context.resources.getResourceEntryName(resId)}"
                )
            return bind.apply {
                this@BindDataBinding.property = this
                onBind?.invoke(this)
                onBind = null
            }
        }

    }
}
```

依葫芦画瓢，我们直接搞定inflate方式获取Binding。

仔细一想，**这还不够**，本来我们将布局改为DataBinding模板，有多种方案设置视图，使用属性代理，有一个目的是：让**设置视图**和**得到Binding实例**之间减少限制。

再干一个：
```
class FindDataBinding<T : ViewDataBinding>(
    private val targetClazz: Class<T>,
    private val viewProvider: ViewProvider,
    lifecycle: Lifecycle,
    private var onBind: (T.() -> Unit)?
) : LifeCycledBindingDelegate<Any, T>(lifecycle) {

    override fun getValue(thisRef: Any, property: KProperty<*>): T {

        return this.property ?: let {
            val view = viewProvider.provide()
            val bind = DataBindingUtil.bind<T>(view)
                ?: throw IllegalStateException(
                    "could not find binding ${targetClazz.name}"
                )
            return bind.apply {
                this@FindDataBinding.property = this
                onBind?.invoke(this)
                onBind = null
            }
        }
    }
}
```

我们又可以通过bind的方式，从一个View发现其binding了。**寻找binding**和**设置视图**的先后，就可以灵活选择了。


加上一些扩展方法后，我们就可以开心的使用了：

```
class MainActivity2 : AppCompatActivity() ,ViewProvider{
    val binding by dataBinding<ActivityMainBinding>(this)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        binding.hello.text = "fragment"
        binding.hello.bindClick {

        }
    }

    override fun provide(): View {
        return window.decorView.findViewById(R.id.ll_root)
    }
}
```

## 总结
正如开篇提到的，好玩系列其出发点一定是好玩，它很可能是对一个问题展开的一次脑暴和尝试，不一定是一个真正成熟的特定问题通用解法。

这一篇，我们从Butterknife的废弃和KAE的废弃开始思考，回顾了两者的实现原理和被废弃的原因，再到寻找迁移方案，并进行了实践。抛开还未涉及到的PSI，基本可以画上一个阶段性句号了。

再次贴上代码链接：
**[UIBinding](https://github.com/leobert-lan/UIBinding)，如果本文中的内容对你有一丝丝的帮助，希望可以得到点赞支持。**

补充：2021-1-25
再补充一段内容重点。
* 对于Java编写的业务，不牵涉kae，只涉及bk，个人建议拷贝其生成类核心逻辑，再删除相关注解点。
* 对于kotlin编写的业务，bk内容可以和Java一样处理，kae相关内容考虑使用属性代理方式，增加全局变量。
* 这一波重构，并不适合在基类做手脚。
* 对于还没有迁移到databinding或者viewbinding的内容，配合属性代理迁移到databinding或者viewbinding也不麻烦。

