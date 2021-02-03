# 三思系列：组件化场景下module依赖优雅实践方案

## 前言

[关于三思系列](https://github.com/leobert-lan/Blog/blob/main/info/%E5%85%B3%E4%BA%8E%E4%B8%89%E6%80%9D%E7%B3%BB%E5%88%97.md)

> 背景：时至今日，组件化已经不再是一个新颖的话题，虽然我将这篇文章放在了`Gradle分类`中，
> 
> 但是我们知道，后端项目呢是实现`微服务化`，通过`RPC机制`实现多个子系统通信的，基本`不会`出现我们将要讨论的问题
> 
> 所以我们还是在`Android`领域中讨论这个问题.
> 
> 如果没有记错，15年那会Android项目逐步转向使用Gradle构建，我在17年参与了DDComponentForAndroid，*后续迁移到JIMU* 
> 的组件化生态维护。包括其他的主流方案，在实现组件化的核心思路上，都是`动态切换plugin`，
> 
> 当然，这不是我们今天要讨论的重点，再各种方案的组件化实施中，我们一定会需要将部分功能模块拆分后，
> 进行`library下沉`。于是，就有了`处理依赖`的场景。


相信大家思考过这样一个问题：如果下沉的library也提前编译好静态aar包，我们的项目编译时间会缩短

毋庸置疑，这样做会直接从源头解决`编译时间长的问题`，就是`减少编译内容`。

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

