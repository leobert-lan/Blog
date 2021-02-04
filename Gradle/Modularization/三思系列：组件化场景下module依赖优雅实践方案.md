# 三思系列：组件化场景下module依赖优雅实践方案

## 前言

[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

> 背景：
> 如果没有记错，15年那会Android项目逐步转向使用Gradle构建，时至今日，组件化已经不再是一个新颖的话题。
> 
> 虽然我将这篇文章放在了`Gradle分类`中，但是我们知道，使用gradle构建的后端项目，
> 热点聚焦在：实现`微服务化`，项目是拆开的，决定了依赖库已经是静态jar包，和我们
> 要讨论的场景是不一致的。所以我们还是在`Android`领域中讨论这个问题.
> 
> 在各种方案的组件化实施中，一定会将`部分功能模块拆分`，进行`library下沉`。
> 于是，就有了`处理依赖`的场景。
> 
> 相信大家思考过这样一个问题：如果下沉的`library`也提前编译好`静态aar包`，我们的项目编译时间会缩短。 
> 毋庸置疑，这样做会直接从`源头解决` `编译时间长的问题`，就是`减少编译内容`。
> 
> `但是`，项目合并在一起，难免就想在开发下层library时，直接用上层业务集成进行冒烟。 *ps:这个做法并不好，应当为library配置好冒烟测试环境，虽然会耗费掉一定的时间*
> 
> 理想归理想，最终还是会败给现实，这个问题就变成了`鱼和熊掌想要兼得`的问题

我们下面会进行一定的展开，来体悟这个问题。

## 为什么使用远程仓库中的依赖包比使用本地静态aar要方便

我们知道，对于一个module，我们对其进行编译生成静态aar包，只会处理它自身的内容。那么他的依赖是如何传递的？

`通过pom文件`

举个例子：

我们新建一个module，看一下依赖：

```groovy
dependencies {

    implementation "org.jetbrains.kotlin:kotlin-stdlib:$kotlin_version"
    implementation 'androidx.core:core-ktx:1.3.2'
    implementation 'androidx.appcompat:appcompat:1.2.0'
    implementation 'com.google.android.material:material:1.2.1'
    testImplementation 'junit:junit:4.+'
    androidTestImplementation 'androidx.test.ext:junit:1.1.2'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.3.0'
}
```

利用maven plugin 进行发布，会有任务生成pom文件，如下：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>leobert</groupId>
  <artifactId>B</artifactId>
  <version>1.0.0</version>
  <packaging>aar</packaging>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>1.4.21</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>androidx.core</groupId>
      <artifactId>core-ktx</artifactId>
      <version>1.3.2</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>androidx.appcompat</groupId>
      <artifactId>appcompat</artifactId>
      <version>1.2.0</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>com.google.android.material</groupId>
      <artifactId>material</artifactId>
      <version>1.2.1</version>
      <scope>compile</scope>
    </dependency>
  </dependencies>
</project>

```

我们发现，关于测试相关的依赖并`没有`被收录到pom文件中。这很合理，测试代码是针对该module的，并不需要提供给使用方，其依赖自然也不需要传递。

我们知道，AGP中现在有4种声明依赖的方式（除去testXXX这种变种）

* api
* implementation
* compileOnly
* runtimeOnly

runtimeOnly对应以前的apk方式声明依赖，我们直接忽略掉，测试一下生成的pom文件。

```groovy
dependencies {

    api "org.jetbrains.kotlin:kotlin-stdlib:$kotlin_version"
    implementation 'androidx.core:core-ktx:1.3.2'
    compileOnly 'androidx.appcompat:appcompat:1.2.0'
    compileOnly 'com.google.android.material:material:1.2.1'


    testImplementation 'junit:junit:4.+'
    androidTestImplementation 'androidx.test.ext:junit:1.1.2'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.3.0'
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>leobert</groupId>
  <artifactId>B</artifactId>
  <version>1.0.0</version>
  <packaging>aar</packaging>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>1.4.21</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>androidx.core</groupId>
      <artifactId>core-ktx</artifactId>
      <version>1.3.2</version>
      <scope>compile</scope>
    </dependency>
  </dependencies>
</project>

```

使用compileOnly方式的并没有被收录到pom文件中，而api和implementation 方式，在pom文件中，都表现为
采用compile的方案应用依赖。
> *ps:api和implementation在编码期的不同，不是我们讨论的重点，略。*

**回到我们开始的问题**，将library发布时，按照约定，会将library本身的依赖收录到pom文件中。相应的，使用方使用
仓库中的依赖项时，gradle会拉取其对应的pom文件，并添加依赖。

所以，如果我们直接使用一个编译好的静态包，而丢弃了他对应的pom文件时，有很大的概率会丢失依赖，出现打包失败或者运行异常。
这意味着我们需要人为维护依赖传递

**我们记住这些内容，并先放到一边**。

## 下沉后，library会有多个层级

> 例如：APP => A => B， 即APP依赖A，A依赖B，而A和B都是library

我们知道，对于B，并不会有什么说法，只会出现在A和APP

如果不使用静态包，那么A会声明：

```groovy
api project(':B')
//或者
implementation project(':B')
```
我们先看一下，这样生成的library-A的pom文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>leobert</groupId>
  <artifactId>A</artifactId>
  <version>1.0.0</version>
  <packaging>aar</packaging>
  <dependencies>
    <dependency>
      <groupId>Demo</groupId>
      <artifactId>B</artifactId>
      <version>unspecified</version>
      <scope>compile</scope>
    </dependency>
  </dependencies>
</project>

```
会得到groupID是项目名，artifactId是module名，version是未知的一个依赖项。

假如我将A编译为静态包并发布到仓库，并运用了pom中的依赖描述，一定会得到无法找到:`Demo-B-unspecified.pom` 的问题。
当然，这个问题可以通过`在APP中重新声明 B的依赖` 来解决。

> 这意味着，我们需要时刻保持警惕，维护上层module的依赖。

