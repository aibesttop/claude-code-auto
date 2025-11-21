# 第二步：实现类对比分析 - 伪代码 V2

## 主流程：两种扫描策略

```
FUNCTION analyze_all_implementations(project_info):
    // 获取第一步的所有interface
    interfaces = project_info.interfaces

    // 情况1：有Interface的类
    FOR EACH interface IN interfaces:
        implementations = find_interface_implementations(interface)
        interface.implementations = implementations
        analyze_and_compare(implementations)
    END FOR

    // 情况2：独立的业务类（无Interface）
    standalone_classes = find_standalone_business_classes(project_info)
    FOR EACH class IN standalone_classes:
        similar_classes = find_similar_classes(class, standalone_classes)
        IF similar_classes NOT empty:
            class.alternatives = similar_classes
            analyze_and_compare([class] + similar_classes)
        END IF
    END FOR

    // AI推理所有实现类的使用场景
    FOR EACH analyzed_group IN all_analyzed_groups:
        usage_scenarios = ai_infer_usage_scenarios(analyzed_group)
        analyzed_group.usage_scenarios = usage_scenarios
    END FOR
END FUNCTION
```

## 1. Interface实现类搜索

```
FUNCTION find_interface_implementations(interface_info):
    implementations = EMPTY_LIST

    // 1.1 直接实现搜索
    direct_impls = search_direct_implementations(interface_info.full_name)
    ADD_ALL direct_impls TO implementations

    // 1.2 间接实现搜索（继承链）
    indirect_impls = search_indirect_implementations(interface_info.full_name)
    ADD_ALL indirect_impls TO implementations

    // 1.3 配置文件中的Bean定义
    config_impls = search_config_beans(interface_info.full_name)
    ADD_ALL config_impls TO implementations

    // 1.4 去重
    implementations = remove_duplicates(implementations)

    RETURN implementations
END FUNCTION

FUNCTION search_direct_implementations(interface_name):
    // 扫描字节码
    FOR EACH class_file IN project_class_files:
        IF class_file.interfaces CONTAINS interface_name:
            implementation = {
                "name": class_file.name,
                "type": "direct",
                "package": class_file.package,
                "source": "bytecode"
            }
            ADD implementation TO results
        END IF
    END FOR

    RETURN results
END FUNCTION

FUNCTION search_indirect_implementations(interface_name):
    // 获取接口继承链
    interface_hierarchy = build_interface_hierarchy(interface_name)

    // 搜索实现继承链中任何接口的类
    FOR EACH parent_interface IN interface_hierarchy:
        parent_impls = search_direct_implementations(parent_interface.name)
        MARK parent_impls.type = "indirect"
        ADD_ALL parent_impls TO results
    END FOR

    RETURN results
END FUNCTION
```

## 2. 独立业务类搜索

```
FUNCTION find_standalone_business_classes(project_info):
    business_classes = EMPTY_LIST

    // 扫描所有类
    FOR EACH class_file IN project_class_files:
        // 排除条件
        IF class_file.is_interface OR
           class_file.is_enum OR
           class_file.is_exception OR
           is_framework_class(class_file):
            CONTINUE
        END IF

        // 识别业务类特征
        IF is_business_class(class_file):
            business_class = {
                "name": class_file.name,
                "package": class_file.package,
                "methods": extract_business_methods(class_file),
                "annotations": class_file.annotations,
                "dependencies": analyze_dependencies(class_file)
            }
            ADD business_class TO business_classes
        END IF
    END FOR

    RETURN business_classes
END FUNCTION

FUNCTION is_business_class(class_file):
    // 业务类判断规则
    rules = [
        HAS_ANNOTATION("@Service") OR
        HAS_ANNOTATION("@Component") OR
        package_contains(".service.") OR
        package_contains(".business.") OR
        has_business_methods(class_file)
    ]

    RETURN ANY rules ARE TRUE
END FUNCTION

FUNCTION find_similar_classes(target_class, all_classes):
    similar_classes = EMPTY_LIST

    FOR EACH other_class IN all_classes:
        IF other_class == target_class:
            CONTINUE
        END IF

        similarity = calculate_class_similarity(target_class, other_class)
        IF similarity > SIMILARITY_THRESHOLD:
            similar_classes.add({
                "class": other_class,
                "similarity": similarity,
                "differences": find_class_differences(target_class, other_class)
            })
        END IF
    END FOR

    SORT similar_classes BY similarity DESCENDING
    RETURN similar_classes
END FUNCTION

FUNCTION calculate_class_similarity(class1, class2):
    // 相似度计算维度
    factors = {
        "method_similarity": compare_method_signatures(class1, class2),
        "name_similarity": compare_class_names(class1, class2),
        "package_similarity": compare_packages(class1, class2),
        "dependency_similarity": compare_dependencies(class1, class2)
    }

    // 加权计算总分
    similarity = (
        factors.method_similarity * 0.4 +
        factors.name_similarity * 0.3 +
        factors.package_similarity * 0.2 +
        factors.dependency_similarity * 0.1
    )

    RETURN similarity
END FUNCTION
```

## 3. 对比分析核心逻辑

```
FUNCTION analyze_and_compare(classes):
    comparison_result = {
        "classes": classes,
        "comparison_matrix": create_comparison_matrix(classes),
        "key_differences": find_key_differences(classes),
        "usage_patterns": analyze_usage_patterns(classes)
    }

    RETURN comparison_result
END FUNCTION

FUNCTION create_comparison_matrix(classes):
    matrix = EMPTY_MATRIX

    // 对比维度定义
    dimensions = [
        "method_count",
        "has_transaction",
        "has_cache",
        "has_async",
        "complexity_score",
        "dependency_count",
        "package_type"
    ]

    // 填充矩阵
    FOR EACH dimension IN dimensions:
        FOR EACH class IN classes:
            value = extract_dimension_value(class, dimension)
            matrix[dimension][class.name] = value
        END FOR
    END FOR

    RETURN matrix
END FUNCTION

FUNCTION find_key_differences(classes):
    differences = EMPTY_LIST

    // 方法实现差异
    method_diffs = compare_method_implementations(classes)
    ADD method_diffs TO differences

    // 注解差异
    annotation_diffs = compare_annotations(classes)
    ADD annotation_diffs TO differences

    // 性能特征差异
    performance_diffs = infer_performance_differences(classes)
    ADD performance_diffs TO differences

    RETURN differences
END FUNCTION
```

## 4. AI推理使用场景

```
FUNCTION ai_infer_usage_scenarios(comparison_result):
    prompt = build_ai_prompt(comparison_result)
    ai_response = call_ai_service(prompt)

    scenarios = parse_ai_response(ai_response)

    RETURN scenarios
END FUNCTION

FUNCTION build_ai_prompt(comparison_result):
    prompt = """
    角色：资深Java架构师

    任务：分析以下实现类的使用场景差异

    接口/类信息：
    {interface_or_class_name}

    实现类列表：
    {implementations_list}

    对比信息：
    {comparison_matrix}

    关键差异：
    {key_differences}

    请分析：
    1. 每个实现类的主要特征
    2. 在什么场景下使用哪个实现类
    3. 选择实现类的判断条件
    4. 潜在的使用风险

    输出格式：
    {
      "implementations": [
        {
          "name": "实现类名",
          "characteristics": ["特征1", "特征2"],
          "use_cases": ["使用场景1", "使用场景2"],
          "selection_criteria": "选择条件",
          "risks": ["风险1", "风险2"]
        }
      ],
      "decision_logic": "选择逻辑描述",
      "recommendations": ["建议1", "建议2"]
    }
    """

    RETURN substitute_placeholders(prompt, comparison_result)
END FUNCTION

FUNCTION parse_ai_response(ai_response):
    // 解析AI返回的JSON
    scenarios = PARSE_JSON(ai_response)

    // 验证和补充
    FOR EACH impl IN scenarios.implementations:
        // 添加推理依据
        impl.reasoning_basis = extract_reasoning_basis(impl)

        // 添加置信度
        impl.confidence = calculate_confidence(impl)
    END FOR

    RETURN scenarios
END FUNCTION
```

## 5. 使用模式分析

```
FUNCTION analyze_usage_patterns(classes):
    patterns = EMPTY_LIST

    // 搜索代码中的使用模式
    FOR EACH class IN classes:
        usages = find_class_usages(class)

        FOR EACH usage IN usages:
            context = extract_usage_context(usage)
            pattern = infer_usage_pattern(context)
            ADD pattern TO patterns
        END FOR
    END FOR

    // 聚类相似的使用模式
    clustered_patterns = cluster_patterns(patterns)

    RETURN clustered_patterns
END FUNCTION

FUNCTION extract_usage_context(usage_location):
    context = {
        "calling_class": usage_location.calling_class,
        "calling_method": usage_location.calling_method,
        "parameters": usage_location.parameters,
        "environment_tags": extract_environment_tags(usage_location),
        "business_context": infer_business_context(usage_location)
    }

    RETURN context
END FUNCTION

FUNCTION infer_usage_pattern(context):
    // 规则引擎推理
    IF context.environment_tags CONTAINS "test":
        RETURN "测试环境使用"
    END IF

    IF context.calling_method CONTAINS "batch":
        RETURN "批量处理场景"
    END IF

    IF context.parameters CONTAINS "high_concurrency":
        RETURN "高并发场景"
    END IF

    // 如果规则不明确，使用AI推理
    RETURN ai_infer_pattern(context)
END FUNCTION
```

## 6. 文档生成

```
FUNCTION generate_comparison_docs(interface_groups, class_groups):
    FOR EACH group IN interface_groups + class_groups:
        // 生成对比表格
        comparison_table = generate_comparison_table(group)

        // 生成AI推理结果
        ai_analysis = group.usage_scenarios

        // 生成选择决策树
        decision_tree = generate_decision_tree(ai_analysis)

        // 组装文档
        doc = {
            "title": f"{group.name} 实现类对比分析",
            "overview": generate_overview(group),
            "comparison_table": comparison_table,
            "ai_analysis": ai_analysis,
            "decision_tree": decision_tree,
            "usage_examples": generate_usage_examples(group),
            "recommendations": generate_recommendations(group)
        }

        // 保存文档
        save_document(doc, f"{group.name}_comparison.md")
    END FOR
END FUNCTION

FUNCTION generate_decision_tree(ai_analysis):
    tree = {
        "root": "选择" + ai_analysis.interface_name,
        "branches": []
    }

    FOR EACH impl IN ai_analysis.implementations:
        branch = {
            "condition": impl.selection_criteria,
            "implementation": impl.name,
            "description": impl.use_cases.join("、"),
            "examples": impl.usage_examples
        }
        ADD branch TO tree.branches
    END FOR

    RETURN tree
END FUNCTION
```

## 7. 质量保证

```
FUNCTION validate_comparison_results(results):
    issues = EMPTY_LIST

    // 验证实现类完整性
    FOR EACH result IN results:
        IF result.implementations COUNT < 1:
            issues.add({
                "type": "warning",
                "message": f"{result.name} 没有找到实现类"
            })
        END IF

        // 验证AI推理结果
        validation = validate_ai_inference(result.usage_scenarios)
        IF validation.has_issues:
            ADD validation.issues TO issues
        END IF
    END FOR

    // 生成验证报告
    report = {
        "total_analyzed": results COUNT,
        "issues_found": issues COUNT,
        "issues": issues,
        "recommendations": generate_fix_recommendations(issues)
    }

    RETURN report
END FUNCTION
```