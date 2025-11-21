# 第一步：Interface扫描文档生成 - 伪代码

## 1. 主文档生成流程

```
FUNCTION generate_step1_documentation(scan_results):
    // 创建文档生成器
    doc_generator = NEW InterfaceScanDocGenerator()

    // 1. 生成总览文档
    overview = doc_generator.generate_overview(scan_results)
    doc_generator.save_doc("interface-overview.md", overview)

    // 2. 生成Interface清单表格
    interface_list = doc_generator.generate_interface_list(scan_results)
    doc_generator.save_doc("interface-list.md", interface_list)

    // 3. 生成分类文档
    categories = doc_generator.generate_category_docs(scan_results)
    FOR EACH category IN categories:
        doc_generator.save_doc(category.filename, category.content)
    END FOR

    // 4. 生成统计报告
    statistics = doc_generator.generate_statistics(scan_results)
    doc_generator.save_doc("interface-statistics.md", statistics)

    // 5. 生成继承关系图
    inheritance_diagram = doc_generator.generate_inheritance_diagram(scan_results)
    doc_generator.save_diagram("inheritance-diagram.svg", inheritance_diagram)

    // 6. 生成质量报告
    quality_report = doc_generator.generate_quality_report(scan_results)
    doc_generator.save_doc("scan-quality-report.md", quality_report)

    RETURN {
        "total_docs": 6,
        "overview": overview,
        "interface_count": scan_results.interfaces COUNT,
        "modules": extract_modules(scan_results)
    }
END FUNCTION
```

## 2. 总览文档生成

```
FUNCTION generate_overview(scan_results):
    overview = NEW Document()

    // 2.1 文档头部
    overview.add_header({
        "title": "Interface扫描总览",
        "scan_time": scan_results.scan_time,
        "project_path": scan_results.project_path,
        "total_interfaces": scan_results.interfaces COUNT,
        "scan_duration": scan_results.duration
    })

    // 2.2 执行摘要
    overview.add_section("执行摘要", generate_executive_summary(scan_results))

    // 2.3 关键指标
    overview.add_section("关键指标", generate_key_metrics(scan_results))

    // 2.4 Interface清单表格
    overview.add_section("Interface清单", generate_master_table(scan_results))

    // 2.5 模块分布
    overview.add_section("模块分布", generate_module_distribution(scan_results))

    // 2.6 扫描范围说明
    overview.add_section("扫描范围", generate_scan_scope(scan_results))

    RETURN overview
END FUNCTION

FUNCTION generate_executive_summary(scan_results):
    summary = {
        "project_overview": {
            "total_interfaces": scan_results.interfaces COUNT,
            "unique_packages": COUNT_UNIQUE(scan_results.interfaces.package_path),
            "total_methods": SUM_ALL(scan_results.interfaces.method_count),
            "avg_methods_per_interface": calculate_avg_methods(scan_results)
        },
        "scan_coverage": {
            "scanned_packages": scan_results.scanned_packages,
            "excluded_packages": scan_results.excluded_packages,
            "coverage_percentage": calculate_coverage(scan_results)
        },
        "findings": {
            "most_complex_interface": find_most_complex(scan_results),
            "most_used_interface": find_most_used(scan_results),
            "interfaces_without_implementations": find_orphan_interfaces(scan_results),
            "deep_inheritance_chains": find_deep_inheritance(scan_results)
        }
    }

    RETURN format_as_markdown(summary)
END FUNCTION

FUNCTION generate_master_table(scan_results):
    // 创建主表格
    table = NEW MarkdownTable()
    table.add_headers([
        "接口名称",
        "包路径",
        "所属模块",
        "方法数",
        "继承接口",
        "主要注解",
        "业务用途",
        "使用次数",
        "状态"
    ])

    // 填充数据
    FOR EACH interface IN scan_results.interfaces:
        table.add_row([
            create_internal_link(interface.name, interface.name + ".md"),
            interface.package_path,
            extract_module_name(interface.package_path),
            interface.methods COUNT,
            format_inherited_interfaces(interface.extended_interfaces),
            format_main_annotations(interface.annotations),
            interface.business_purpose OR ai_generate_purpose(interface),
            interface.usage_count,
            get_interface_status(interface)
        ])
    END FOR

    // 添加排序功能说明
    table.add_caption("点击列标题可排序，支持搜索过滤")

    RETURN table.to_markdown()
END FUNCTION
```

## 3. Interface清单表格生成

```
FUNCTION generate_interface_list(scan_results):
    doc = NEW Document()

    doc.add_header("Interface完整清单")

    // 添加筛选和排序说明
    doc.add_section("使用说明", generate_usage_instructions())

    // 按模块分组生成表格
    modules = group_interfaces_by_module(scan_results.interfaces)

    FOR EACH module IN modules:
        doc.add_section(f"模块：{module.name}", generate_module_table(module))
    END FOR

    // 添加索引
    doc.add_section("快速索引", generate_quick_index(modules))

    RETURN doc
END FUNCTION

FUNCTION generate_module_table(module):
    table = NEW MarkdownTable()
    table.add_headers([
        "接口名称",
        "方法详情",
        "继承关系",
        "实现类数",
        "最后修改",
        "复杂度"
    ])

    FOR EACH interface IN module.interfaces:
        // 方法详情展开
        method_details = format_method_details(interface.methods)

        // 继承关系图
        inheritance_diagram = create_mini_inheritance_diagram(interface)

        // 复杂度评级
        complexity_rating = evaluate_complexity(interface)

        table.add_row([
            interface.name,
            method_details,
            inheritance_diagram,
            interface.implementations COUNT,
            interface.last_modified,
            complexity_rating
        ])
    END FOR

    return table.to_markdown()
END FUNCTION

FUNCTION format_method_details(methods):
    IF methods COUNT <= 3:
        // 少量方法直接列出
        RETURN methods.map(m => `${m.name}()`).join(", ")
    ELSE:
        // 大量方法折叠显示
        RETURN f"<details><summary>{methods COUNT}个方法</summary><ul>" +
               methods.map(m => `<li>${m.name}(): ${m.return_type}</li>`).join("") +
               "</ul></details>"
    END IF
END FUNCTION
```

## 4. 分类文档生成

```
FUNCTION generate_category_docs(scan_results):
    categories = EMPTY_LIST

    // 4.1 按层级分类
    layer_categories = categorize_by_layer(scan_results.interfaces)
    FOR EACH layer IN layer_categories:
        doc = generate_layer_doc(layer)
        categories.add({
            "type": "layer",
            "name": layer.name,
            "filename": f"layer-{layer.name}.md",
            "content": doc
        })
    END FOR

    // 4.2 按功能分类
    functional_categories = categorize_by_function(scan_results.interfaces)
    FOR EACH category IN functional_categories:
        doc = generate_functional_doc(category)
        categories.add({
            "type": "functional",
            "name": category.name,
            "filename": f"func-{category.name}.md",
            "content": doc
        })
    END FOR

    // 4.3 按复杂度分类
    complexity_categories = categorize_by_complexity(scan_results.interfaces)
    FOR EACH level IN complexity_categories:
        doc = generate_complexity_doc(level)
        categories.add({
            "type": "complexity",
            "name": level.name,
            "filename": f"complexity-{level.name}.md",
            "content": doc
        })
    END FOR

    RETURN categories
END FUNCTION

FUNCTION categorize_by_layer(interfaces):
    layers = {
        "service": [],
        "repository": [],
        "controller": [],
        "component": [],
        "gateway": [],
        "other": []
    }

    FOR EACH interface IN interfaces:
        layer = determine_layer(interface)
        layers[layer].add(interface)
    END FOR

    // 转换为文档对象
    result = []
    FOR EACH layer_name, interfaces_list IN layers:
        IF interfaces_list NOT empty:
            result.add({
                "name": layer_name,
                "interfaces": interfaces_list,
                "count": interfaces_list COUNT
            })
        END IF
    END FOR

    RETURN result
END FUNCTION
```

## 5. 统计报告生成

```
FUNCTION generate_statistics(scan_results):
    stats = NEW Document()

    stats.add_header("Interface统计分析报告")

    // 5.1 基础统计
    stats.add_section("基础统计", generate_basic_statistics(scan_results))

    // 5.2 分布统计
    stats.add_section("分布统计", generate_distribution_statistics(scan_results))

    // 5.3 质量统计
    stats.add_section("质量统计", generate_quality_statistics(scan_results))

    // 5.4 趋势分析
    stats.add_section("趋势分析", generate_trend_analysis(scan_results))

    // 5.5 改进建议
    stats.add_section("改进建议", generate_improvement_suggestions(scan_results))

    RETURN stats
END FUNCTION

FUNCTION generate_basic_statistics(scan_results):
    stats_data = {
        "接口总数": scan_results.interfaces COUNT,
        "包数": COUNT_UNIQUE(scan_results.interfaces.package_path),
        "方法总数": SUM_ALL(scan_results.interfaces, i => i.methods COUNT),
        "平均方法数": calculate_average_methods(scan_results.interfaces),
        "最大方法数": MAX_ALL(scan_results.interfaces, i => i.methods COUNT),
        "最小方法数": MIN_ALL(scan_results.interfaces, i => i.methods COUNT),
        "无实现接口": COUNT(scan_results.interfaces, i => i.implementations is empty),
        "多实现接口": COUNT(scan_results.interfaces, i => i.implementations COUNT > 1)
    }

    RETURN format_as_statistics_table(stats_data)
END FUNCTION

FUNCTION generate_distribution_statistics(scan_results):
    distributions = NEW Section()

    // 按包路径分布
    package_dist = calculate_package_distribution(scan_results.interfaces)
    distributions.add_subsection("包路径分布", create_bar_chart(package_dist))

    // 按方法数分布
    method_dist = calculate_method_distribution(scan_results.interfaces)
    distributions.add_subsection("方法数分布", create_histogram(method_dist))

    // 按继承深度分布
    inheritance_dist = calculate_inheritance_distribution(scan_results.interfaces)
    distributions.add_subsection("继承深度分布", create_pie_chart(inheritance_dist))

    // 按使用频率分布
    usage_dist = calculate_usage_distribution(scan_results.interfaces)
    distributions.add_subsection("使用频率分布", create_heatmap(usage_dist))

    RETURN distributions.to_markdown()
END FUNCTION

FUNCTION generate_quality_statistics(scan_results):
    quality_metrics = {
        "文档完整性": calculate_documentation_completeness(scan_results),
        "命名规范性": evaluate_naming_conventions(scan_results),
        "设计合理性": assess_design_quality(scan_results),
        "耦合度分析": analyze_coupling(scan_results),
        "内聚度分析": analyze_cohesion(scan_results)
    }

    report = NEW QualityReport()
    FOR EACH metric_name, metric_value IN quality_metrics:
        report.add_metric(metric_name, metric_value)
    END FOR

    RETURN format_quality_report(report)
END FUNCTION
```

## 6. 继承关系图生成

```
FUNCTION generate_inheritance_diagram(scan_results):
    // 构建继承关系数据
    inheritance_data = build_inheritance_graph(scan_results.interfaces)

    // 生成Mermaid代码
    mermaid_code = "graph TD\n"

    // 添加节点样式定义
    mermaid_code += "    classDef interface fill:#lightblue,stroke:#333\n"
    mermaid_code += "    classDef abstract fill:#lightgreen,stroke:#333\n"
    mermaid_code += "    classDef root fill:#lightyellow,stroke:#333\n"

    // 添加节点和连线
    FOR EACH relationship IN inheritance_data.relationships:
        child_id = sanitize_id(relationship.child)
        parent_id = sanitize_id(relationship.parent)

        mermaid_code += f"    {child_id}[{relationship.child}]:::{relationship.type}\n"
        mermaid_code += f"    {parent_id}[{relationship.parent}]:::{relationship.type}\n"
        mermaid_code += f"    {child_id} --> {parent_id}\n"
    END FOR

    // 识别根接口
    root_interfaces = find_root_interfaces(inheritance_data)
    FOR EACH root IN root_interfaces:
        root_id = sanitize_id(root)
        mermaid_code += f"    class {root_id} root\n"
    END FOR

    RETURN {
        "type": "inheritance",
        "format": "mermaid",
        "code": mermaid_code,
        "svg_path": "diagrams/inheritance-hierarchy.svg",
        "interactive_path": "diagrams/inheritance-interactive.html"
    }
END FUNCTION

FUNCTION build_inheritance_graph(interfaces):
    graph = NEW InheritanceGraph()

    FOR EACH interface IN interfaces:
        graph.add_node(interface.name, interface)

        // 添加继承关系
        FOR EACH parent_interface IN interface.extended_interfaces:
            graph.add_edge(interface.name, parent_interface, "extends")
        END FOR
    END FOR

    // 计算传递闭包
    graph.compute_transitive_closure()

    // 识别继承链
    inheritance_chains = graph.find_chains()

    RETURN {
        "graph": graph,
        "relationships": graph.get_all_edges(),
        "chains": inheritance_chains,
        "cycles": graph.detect_cycles()
    }
END FUNCTION
```

## 7. 质量报告生成

```
FUNCTION generate_quality_report(scan_results):
    quality_report = NEW Document()
    quality_report.add_header("扫描质量报告")

    // 7.1 扫描完整性
    completeness = {
        "expected_interfaces": estimate_expected_interfaces(scan_results),
        "found_interfaces": scan_results.interfaces COUNT,
        "coverage_percentage": calculate_coverage_percentage(scan_results),
        "missing_items": identify_missing_items(scan_results)
    }
    quality_report.add_section("扫描完整性", format_completeness_report(completeness))

    // 7.2 数据准确性
    accuracy_checks = {
        "duplicate_interfaces": find_duplicates(scan_results),
        "invalid_references": validate_references(scan_results),
        "broken_inheritance": check_inheritance_integrity(scan_results),
        "annotation_consistency": verify_annotation_consistency(scan_results)
    }
    quality_report.add_section("数据准确性", format_accuracy_report(accuracy_checks))

    // 7.3 扫描性能
    performance_metrics = {
        "scan_duration": scan_results.duration,
        "memory_usage": scan_results.memory_usage,
        "files_scanned": scan_results.files_scanned,
        "scan_rate": calculate_scan_rate(scan_results)
    }
    quality_report.add_section("扫描性能", format_performance_report(performance_metrics))

    // 7.4 改进建议
    recommendations = generate_scan_recommendations(scan_results, accuracy_checks)
    quality_report.add_section("改进建议", format_recommendations(recommendations))

    RETURN quality_report
END FUNCTION

FUNCTION generate_scan_recommendations(scan_results, accuracy_checks):
    recommendations = []

    // 基于扫描结果的建议
    IF accuracy_checks.missing_items NOT empty:
        recommendations.add({
            "type": "coverage",
            "priority": "high",
            "description": "建议扩大扫描范围以包含所有包",
            "action": "更新扫描配置，添加遗漏的包路径"
        })
    END IF

    // 基于接口复杂度的建议
    complex_interfaces = find_complex_interfaces(scan_results)
    IF complex_interfaces NOT empty:
        recommendations.add({
            "type": "refactoring",
            "priority": "medium",
            "description": f"发现{complex_interfaces COUNT}个复杂接口，建议拆分",
            "examples": complex_interfaces.slice(0, 3)
        })
    END IF

    // 基于使用模式的建议
    unused_interfaces = find_unused_interfaces(scan_results)
    IF unused_interfaces NOT empty:
        recommendations.add({
            "type": "cleanup",
            "priority": "low",
            "description": f"发现{unused_interfaces COUNT}个未使用的接口",
            "action": "考虑删除或标记为废弃"
        })
    END IF

    RETURN recommendations
END FUNCTION
```

## 8. AI增强内容生成

```
FUNCTION ai_generate_purpose(interface):
    prompt = f"""
    分析以下Java接口的业务用途：

    接口名：{interface.name}
    包路径：{interface.package_path}
    方法列表：{format_method_list(interface.methods)}
    注解：{format_annotations(interface.annotations)}

    请用一句话概括这个接口的主要职责：
    """

    response = call_ai_service(prompt)
    RETURN extract_sentence(response)
END FUNCTION

FUNCTION ai_generate_interface_summary(interface_group):
    prompt = f"""
    为以下接口组生成总结：

    模块：{interface_group.name}
    接口数量：{interface_group.interfaces COUNT}
    主要功能：{extract_common_features(interface_group)}

    请生成：
    1. 模块职责描述
    2. 设计模式识别
    3. 潜在改进点
    """

    response = call_ai_service(prompt)
    RETURN parse_ai_summary(response)
END FUNCTION
```