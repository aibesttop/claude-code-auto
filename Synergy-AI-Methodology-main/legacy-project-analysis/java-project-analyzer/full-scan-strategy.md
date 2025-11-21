# Java Interface全量扫描策略 - 无遗漏分析

## 扫描原则
1. **全量扫描**：所有项目自定义Interface，不论层级、不论用途
2. **框架过滤**：只排除Spring、JPA等框架自带的Interface
3. **深度分析**：每个Interface都要分析到方法级别
4. **完整性验证**：通过静态分析确保扫描完整性

## 第一步：全量Interface扫描器实现

### 1.1 核心扫描逻辑

```java
@Component
public class FullInterfaceScanner {

    // 框架包名黑名单
    private static final Set<String> FRAMEWORK_PACKAGES = Set.of(
        "org.springframework",
        "javax.persistence",
        "jakarta.persistence",
        "org.hibernate",
        "org.mybatis",
        "org.apache.ibatis",
        "org.junit",
        "junit",
        "org.mockito",
        "org.easymock",
        "org.powermock",
        "org.slf4j",
        "org.apache.commons",
        "com.google",
        "org.junit.jupiter"
    );

    // 项目基础包（从配置读取）
    @Value("${analyzer.base-package}")
    private String basePackage;

    public List<InterfaceInfo> scanAllInterfaces(String projectPath) {
        List<InterfaceInfo> allInterfaces = new ArrayList<>();

        // 1. 使用JavaParser扫描所有Java文件
        Collection<CompilationUnit> compilationUnits = JavaParser.parseAllFiles(
            Paths.get(projectPath),
            new JavaParserAdapter()
        );

        // 2. 遍历所有CompilationUnit
        for (CompilationUnit cu : compilationUnits) {
            // 提取所有Interface声明
            cu.findAll(InterfaceDeclaration.class).forEach(interfaceDecl -> {
                InterfaceInfo info = analyzeInterface(interfaceDecl, cu);
                if (info != null) {
                    allInterfaces.add(info);
                }
            });
        }

        // 3. 验证扫描完整性
        validateScanCompleteness(allInterfaces);

        // 4. 排序和分类
        sortAndClassify(allInterfaces);

        return allInterfaces;
    }

    private InterfaceInfo analyzeInterface(InterfaceDeclaration interfaceDecl,
                                         CompilationUnit cu) {
        String fullName = getFullName(interfaceDecl, cu);

        // 过滤框架Interface
        if (isFrameworkInterface(fullName)) {
            return null;
        }

        // 只扫描项目内的Interface
        if (!fullName.startsWith(basePackage)) {
            return null;
        }

        InterfaceInfo info = new InterfaceInfo();
        info.setFullName(fullName);
        info.setSimpleName(interfaceDecl.getNameAsString());
        info.setPackagePath(extractPackagePath(cu));

        // 解析继承关系
        interfaceDecl.getExtendedTypes().forEach(extType -> {
            info.addExtendedInterface(extType.toString());
        });

        // 解析所有方法
        interfaceDecl.getMethods().forEach(method -> {
            MethodInfo methodInfo = analyzeMethod(method);
            info.addMethod(methodInfo);
        });

        // 解析注解
        interfaceDecl.getAnnotations().forEach(annotation -> {
            info.addAnnotation(annotation.getNameAsString());
        });

        // 解析泛型参数
        interfaceDecl.getTypeParameters().forEach(typeParam -> {
            info.addTypeParameter(typeParam.getNameAsString());
        });

        return info;
    }

    private boolean isFrameworkInterface(String fullName) {
        return FRAMEWORK_PACKAGES.stream()
            .anyMatch(framework -> fullName.startsWith(framework));
    }

    /**
     * 验证扫描完整性
     */
    private void validateScanCompleteness(List<InterfaceInfo> interfaces) {
        // 1. 检查是否有循环依赖
        detectCircularDependencies(interfaces);

        // 2. 检查继承链完整性
        validateInheritanceChain(interfaces);

        // 3. 生成扫描报告
        generateScanReport(interfaces);
    }

    /**
     * 生成扫描统计报告
     */
    private void generateScanReport(List<InterfaceInfo> interfaces) {
        ScanReport report = new ScanReport();

        report.setTotalInterfaces(interfaces.size());

        // 按包路径统计
        Map<String, Long> packageStats = interfaces.stream()
            .collect(Collectors.groupingBy(
                InterfaceInfo::getPackagePath,
                Collectors.counting()
            ));
        report.setPackageDistribution(packageStats);

        // 方法数量统计
        IntSummaryStatistics methodStats = interfaces.stream()
            .mapToInt(i -> i.getMethods().size())
            .summaryStatistics();
        report.setMethodStatistics(methodStats);

        // 继承深度统计
        Map<Integer, Long> inheritanceStats = interfaces.stream()
            .collect(Collectors.groupingBy(
                i -> calculateInheritanceDepth(i, interfaces),
                Collectors.counting()
            ));
        report.setInheritanceDepthDistribution(inheritanceStats);

        // 保存报告
        reportService.saveReport(report);
    }
}
```

### 1.2 Interface信息模型

```java
@Data
@Builder
public class InterfaceInfo {
    private String fullName;           // com.company.service.UserService
    private String simpleName;          // UserService
    private String packagePath;         // com.company.service
    private String moduleName;          // 推断的模块名
    private String businessPurpose;     // AI推断的业务用途

    // 结构信息
    private List<String> extendedInterfaces;  // 继承的接口
    private List<String> typeParameters;      // 泛型参数
    private List<String> annotations;         // 注解
    private List<MethodInfo> methods;         // 方法列表

    // 统计信息
    private int methodCount;
    private int inheritanceDepth;
    private boolean isRootInterface;
    private boolean isLeafInterface;

    // 使用情况
    private List<String> implementationClasses;  // 实现类
    private List<String> usageLocations;         // 使用位置
    private int usageCount;                       // 使用次数
}

@Data
@Builder
public class MethodInfo {
    private String name;               // 方法名
    private String returnType;         // 返回类型
    private List<ParameterInfo> parameters;  // 参数列表
    private List<String> exceptions;   // 声明的异常
    private List<String> annotations;  // 方法注解
    private String javaDoc;           // JavaDoc注释
    private boolean isDefault;        // 是否default方法
    private boolean isStatic;         // 是否static方法
    private String accessModifier;    // 访问修饰符
}
```

### 1.3 静态分析验证工具

```java
@Component
public class StaticAnalysisValidator {

    /**
     * 使用ASM验证扫描结果
     */
    public void validateWithASM(List<InterfaceInfo> scannedInterfaces,
                               String classpath) throws IOException {
        Set<String> asmFoundInterfaces = new HashSet<>();

        // ASM扫描所有class文件中的接口
        ClassReader cr = new ClassReader(classpath);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9) {
            @Override
            public void visit(int version, int access, String name,
                             String signature, String superName, String[] interfaces) {
                if ((access & Opcodes.ACC_INTERFACE) != 0) {
                    asmFoundInterfaces.add(name.replace('/', '.'));
                }
            }
        };
        cr.accept(cv, 0);

        // 对比结果
        Set<String> scannedNames = scannedInterfaces.stream()
            .map(InterfaceInfo::getFullName)
            .collect(Collectors.toSet());

        // 找出遗漏的接口
        Set<String> missed = new HashSet<>(asmFoundInterfaces);
        missed.removeAll(scannedNames);

        if (!missed.isEmpty()) {
            throw new ScanIncompleteException(
                "扫描遗漏的接口: " + missed
            );
        }
    }

    /**
     * 使用反射验证
     */
    public void validateWithReflection(List<InterfaceInfo> scannedInterfaces,
                                     ClassLoader classLoader) {
        Set<String> reflectionFound = new HashSet<>();

        // 反射获取所有接口
        Reflections reflections = new Reflections(
            new ConfigurationBuilder()
                .setUrls(ClasspathHelper.forPackage(basePackage))
                .setScanners(new SubTypesScanner(false))
                .addClassLoaders(classLoader)
        );

        Set<Class<?>> allInterfaces = reflections.getSubTypesOf(Object.class)
            .stream()
            .filter(Class::isInterface)
            .filter(c -> c.getName().startsWith(basePackage))
            .collect(Collectors.toSet());

        allInterfaces.forEach(clazz -> {
            reflectionFound.add(clazz.getName());
        });

        // 验证完整性
        validateCompleteness(scannedInterfaces, reflectionFound);
    }
}
```

### 1.4 增量扫描支持

```java
@Component
public class IncrementalScanner {

    private final ObjectMapper mapper = new ObjectMapper();
    private final Path scanStatePath = Paths.get(".scan-state.json");

    /**
     * 检查是否有变更
     */
    public boolean hasChanges(String projectPath) throws IOException {
        if (!Files.exists(scanStatePath)) {
            return true;
        }

        ScanState lastState = mapper.readValue(
            Files.readAllBytes(scanStatePath),
            ScanState.class
        );

        // 检查文件修改时间
        return Files.walk(Paths.get(projectPath))
            .filter(p -> p.toString().endsWith(".java"))
            .anyMatch(p -> {
                try {
                    return Files.getLastModifiedTime(p)
                        .compareTo(lastState.getLastScanTime()) > 0;
                } catch (IOException e) {
                    return true;
                }
            });
    }

    /**
     * 增量扫描
     */
    public List<InterfaceInfo> incrementalScan(String projectPath)
            throws IOException {
        ScanState lastState = null;
        if (Files.exists(scanStatePath)) {
            lastState = mapper.readValue(
                Files.readAllBytes(scanStatePath),
                ScanState.class
            );
        }

        // 找出修改的文件
        Set<Path> modifiedFiles = findModifiedJavaFiles(
            projectPath,
            lastState
        );

        // 扫描修改的文件中的接口
        List<InterfaceInfo> updatedInterfaces = new ArrayList<>();
        for (Path file : modifiedFiles) {
            CompilationUnit cu = JavaParser.parse(file);
            cu.findAll(InterfaceDeclaration.class).forEach(decl -> {
                InterfaceInfo info = analyzeInterface(decl, cu);
                if (info != null) {
                    updatedInterfaces.add(info);
                }
            });
        }

        // 更新扫描状态
        ScanState newState = new ScanState();
        newState.setLastScanTime(Instant.now());
        newState.setScannedFiles(modifiedFiles);
        mapper.writeValue(scanStatePath.toFile(), newState);

        return updatedInterfaces;
    }
}
```

### 1.5 扫描执行器

```java
@Service
public class InterfaceScanExecutor {

    @Autowired
    private FullInterfaceScanner scanner;

    @Autowired
    private StaticAnalysisValidator validator;

    @Autowired
    private IncrementalScanner incrementalScanner;

    @Autowired
    private DocumentGenerator docGenerator;

    public void executeScan(String projectPath, boolean forceFullScan) {
        try {
            log.info("开始扫描项目Interface: {}", projectPath);

            List<InterfaceInfo> interfaces;

            // 决定是否增量扫描
            if (!forceFullScan && incrementalScanner.hasChanges(projectPath)) {
                log.info("执行增量扫描");
                interfaces = incrementalScanner.incrementalScan(projectPath);
            } else {
                log.info("执行全量扫描");
                interfaces = scanner.scanAllInterfaces(projectPath);

                // 静态分析验证
                validator.validateWithASM(interfaces, projectPath);
                validator.validateWithReflection(interfaces,
                    this.getClass().getClassLoader());
            }

            // 生成文档
            generateAllDocuments(interfaces);

            log.info("扫描完成，共发现 {} 个Interface", interfaces.size());

        } catch (Exception e) {
            log.error("扫描失败", e);
            throw new ScanException("Interface扫描失败", e);
        }
    }

    private void generateAllDocuments(List<InterfaceInfo> interfaces) {
        // 1. 生成Interface总览表
        docGenerator.generateOverviewTable(interfaces);

        // 2. 生成每个Interface的详细文档
        interfaces.forEach(interfaceInfo -> {
            docGenerator.generateInterfaceDetail(interfaceInfo);
        });

        // 3. 生成继承关系图
        docGenerator.generateInheritanceDiagram(interfaces);

        // 4. 生成使用统计报告
        docGenerator.generateUsageStatistics(interfaces);
    }
}
```

### 1.6 命令行工具

```java
@SpringBootApplication
public class InterfaceAnalyzerApplication implements CommandLineRunner {

    @Autowired
    private InterfaceScanExecutor scanExecutor;

    public static void main(String[] args) {
        SpringApplication.run(InterfaceAnalyzerApplication.class, args);
    }

    @Override
    public void run(String... args) throws Exception {
        Options options = new Options();
        options.addOption("p", "project", true, "项目路径");
        options.addOption("o", "output", true, "输出目录");
        options.addOption("f", "force", false, "强制全量扫描");
        options.addOption("v", "verbose", false, "详细输出");

        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);

        String projectPath = cmd.getOptionValue("p", ".");
        String outputDir = cmd.getOptionValue("o", "./interface-docs");
        boolean forceFullScan = cmd.hasOption("f");

        // 执行扫描
        scanExecutor.executeScan(projectPath, forceFullScan);

        System.out.println("\n扫描完成！文档已生成到: " + outputDir);
    }
}
```

## 使用方法

```bash
# 全量扫描
java -jar interface-analyzer.jar -p /path/to/project -o ./docs

# 增量扫描
java -jar interface-analyzer.jar -p /path/to/project

# 强制全量扫描
java -jar interface-analyzer.jar -p /path/to/project -f

# 详细输出
java -jar interface-analyzer.jar -p /path/to/project -v
```

## 扫描输出示例

```
=== Interface扫描报告 ===
项目路径: /workspace/my-project
扫描时间: 2024-01-20 10:30:00
扫描模式: 全量扫描

总Interface数: 156
├── service层: 45
├── repository层: 23
├── mapper层: 18
├── component层: 31
├── strategy层: 12
└── 其他: 27

方法统计:
├── 平均方法数: 6.8
├── 最大方法数: 28 (ReportService)
├── 最小方法数: 1 (CacheKeyGenerator)

继承深度:
├── 0层（根接口）: 89
├── 1层继承: 45
├── 2层继承: 18
├── 3层以上: 4

验证结果:
✓ ASM验证通过
✓ 反射验证通过
✓ 无循环依赖
✓ 无继承链断裂

文档生成:
✓ Interface总览表
✓ 详细Interface文档 (156个)
✓ 继承关系图
✓ 使用统计报告
```

这个方案确保了：
1. **全量扫描**：不遗漏任何自定义Interface
2. **框架过滤**：自动排除Spring、JPA等框架Interface
3. **完整性验证**：通过ASM和反射双重验证
4. **增量支持**：支持增量扫描，提高效率
5. **详细报告**：生成完整的扫描报告和统计信息

接下来我们可以讨论第二步：实现类对比分析的具体实现细节。