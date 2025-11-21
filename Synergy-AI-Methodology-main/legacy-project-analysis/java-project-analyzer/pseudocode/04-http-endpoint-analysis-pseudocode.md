# 第四步：HTTP端点调用链分析 - 伪代码

## 1. 主分析流程

```
FUNCTION analyze_all_http_endpoints(project_info):
    // 初始化分析器
    analyzer = NEW HTTPEndpointAnalyzer()

    // 1. 扫描所有HTTP端点
    endpoints = analyzer.scan_all_endpoints(project_info)

    // 2. 分析每个端点
    FOR EACH endpoint IN endpoints:
        endpoint_analysis = analyzer.analyze_endpoint(endpoint)
        endpoint.analyses = endpoint_analysis
    END FOR

    // 3. 生成所有端点文档
    FOR EACH endpoint IN endpoints:
        doc = generate_endpoint_document(endpoint)
        save_endpoint_doc(doc)
    END FOR

    // 4. 生成汇总报告
    summary = generate_endpoint_summary(endpoints)

    RETURN {
        "total_endpoints": endpoints COUNT,
        "endpoints": endpoints,
        "summary": summary
    }
END FUNCTION
```

## 2. HTTP端点扫描

```
FUNCTION scan_all_endpoints(project_info):
    endpoints = EMPTY_LIST

    // 2.1 扫描Controller类
    controllers = scan_controllers(project_info)

    FOR EACH controller IN controllers:
        // 获取类级别映射
        class_mapping = extract_class_mapping(controller)

        // 扫描所有端点方法
        endpoint_methods = scan_endpoint_methods(controller)

        FOR EACH method IN endpoint_methods:
            endpoint = {
                "controller": controller.name,
                "method": method.name,
                "http_method": extract_http_method(method),
                "path": combine_paths(class_mapping, extract_method_path(method)),
                "parameters": extract_parameters(method),
                "return_type": method.return_type,
                "annotations": method.annotations,
                "class_location": controller.file_path,
                "line_number": method.line_number
            }

            ADD endpoint TO endpoints
        END FOR
    END FOR

    // 2.2 扫描配置文件中的路由
    config_endpoints = scan_config_routes(project_info)
    ADD_ALL config_endpoints TO endpoints

    // 2.3 去重和排序
    endpoints = deduplicate_endpoints(endpoints)
    SORT endpoints BY path

    RETURN endpoints
END FUNCTION

FUNCTION scan_controllers(project_info):
    controllers = EMPTY_LIST

    // 扫描所有类文件
    FOR EACH class_file IN project_info.class_files:
        class_info = parse_class_file(class_file)

        // 检查是否是Controller
        IF is_controller_class(class_info):
            controller = {
                "name": class_info.name,
                "package": class_info.package,
                "base_path": extract_base_path(class_info),
                "methods": class_info.methods,
                "dependencies": analyze_dependencies(class_info),
                "file_path": class_file.path
            }

            ADD controller TO controllers
        END IF
    END FOR

    RETURN controllers
END FUNCTION

FUNCTION is_controller_class(class_info):
    // 检查Controller注解
    controller_annotations = [
        "@RestController",
        "@Controller",
        "@RequestMapping"
    ]

    FOR EACH annotation IN class_info.annotations:
        IF annotation IN controller_annotations:
            RETURN TRUE
        END IF
    END FOR

    // 检查类命名规范
    IF class_info.name ENDS_WITH "Controller":
        RETURN TRUE
    END IF

    RETURN FALSE
END FUNCTION

FUNCTION extract_parameters(method):
    parameters = EMPTY_LIST

    FOR EACH param IN method.parameters:
        param_info = {
            "name": param.name,
            "type": param.type,
            "annotation": extract_main_annotation(param),
            "required": is_required(param),
            "default_value": get_default_value(param)
        }

        ADD param_info TO parameters
    END FOR

    RETURN parameters
END FUNCTION
```

## 3. 调用链路分析

```
FUNCTION analyze_endpoint(endpoint):
    analysis = NEW EndpointAnalysis()

    // 3.1 构建调用图
    call_graph = build_call_graph(endpoint)
    analysis.call_graph = call_graph

    // 3.2 追踪调用链路
    call_chain = trace_call_chain(endpoint, call_graph)
    analysis.call_chain = call_chain

    // 3.3 识别注入的依赖
    dependencies = analyze_injected_dependencies(endpoint.controller)
    analysis.dependencies = dependencies

    // 3.4 推理实现类
    FOR EACH dependency IN dependencies:
        IF dependency.is_interface:
            impl_inference = infer_implementation(dependency, endpoint)
            dependency.inferred_implementation = impl_inference
        END IF
    END FOR

    // 3.5 分析数据流
    data_flow = analyze_data_flow(call_chain)
    analysis.data_flow = data_flow

    // 3.6 生成数据流图
    data_flow_diagram = generate_data_flow_diagram(data_flow)
    analysis.data_flow_diagram = data_flow_diagram

    RETURN analysis
END FUNCTION

FUNCTION build_call_graph(endpoint):
    graph = NEW CallGraph()

    // 获取Controller方法代码
    controller_method = get_method_code(endpoint.controller, endpoint.method)

    // 分析方法体
    method_body = parse_method_body(controller_method)

    // 递归分析所有调用
    FOR EACH call IN method_body.method_calls:
        analyze_method_call(call, graph, 0)
    END FOR

    RETURN graph
END FUNCTION

FUNCTION analyze_method_call(call, graph, depth):
    // 避免过深递归
    IF depth > MAX_DEPTH:
        RETURN
    END IF

    // 添加调用节点
    graph.add_node(call.target_class, call.target_method)

    // 分析目标方法
    target_method = find_method_definition(call.target_class, call.target_method)
    IF target_method EXISTS:
        // 添加调用关系
        graph.add_edge(call.caller_class, call.target_class, call.method)

        // 递归分析
        target_body = parse_method_body(target_method)
        FOR EACH sub_call IN target_body.method_calls:
            analyze_method_call(sub_call, graph, depth + 1)
        END FOR
    END IF
END FUNCTION

FUNCTION trace_call_chain(endpoint, call_graph):
    chain = NEW CallChain()

    // 从Controller开始
    current_node = endpoint.controller
    chain.add_node(current_node, "Controller")

    // 使用BFS追踪主要调用路径
    visited = NEW Set()
    queue = NEW Queue([current_node])

    WHILE queue NOT empty:
        node = queue.dequeue()
        IF visited.contains(node):
            CONTINUE
        END IF

        visited.add(node)

        // 获取直接调用
        direct_calls = call_graph.get_direct_calls(node)
        FOR EACH call IN direct_calls:
            // 判断是否是主要调用路径
            IF is_main_call_path(call):
                chain.add_node(call.target, determine_layer(call.target))
                chain.add_edge(node, call.target, call.method)
                queue.enqueue(call.target)
            END IF
        END FOR
    END WHILE

    RETURN chain
END FUNCTION

FUNCTION analyze_injected_dependencies(controller_class):
    dependencies = EMPTY_LIST

    // 分析字段注入
    FOR EACH field IN controller_class.fields:
        IF has_annotation(field, "@Autowired") OR
           has_annotation(field, "@Resource") OR
           has_annotation(field, "@Inject"):

            dependency = {
                "name": field.name,
                "type": field.type,
                "injection_type": "field",
                "is_interface": is_interface_type(field.type),
                "annotations": field.annotations
            }

            ADD dependency TO dependencies
        END IF
    END FOR

    // 分析构造器注入
    constructor = find_main_constructor(controller_class)
    IF constructor EXISTS:
        FOR EACH param IN constructor.parameters:
            dependency = {
                "name": param.name,
                "type": param.type,
                "injection_type": "constructor",
                "is_interface": is_interface_type(param.type),
                "annotations": param.annotations
            }

            ADD dependency TO dependencies
        END FOR
    END IF

    // 分析Setter注入
    FOR EACH method IN controller_class.methods:
        IF is_setter_method(method) AND has_dependency_annotation(method):
            dependency = extract_dependency_from_setter(method)
            ADD dependency TO dependencies
        END IF
    END FOR

    RETURN dependencies
END FUNCTION
```

## 4. AI推理实现类

```
FUNCTION infer_implementation(dependency, endpoint):
    // 获取接口的所有实现类
    implementations = get_interface_implementations(dependency.type)

    IF implementations is empty:
        RETURN null
    END IF

    // 构建推理上下文
    context = build_inference_context(dependency, endpoint)

    // 生成推理提示
    prompt = build_inference_prompt(dependency, implementations, context)

    // 调用AI推理
    ai_response = call_ai_service(prompt)

    // 解析推理结果
    inference_result = parse_ai_inference(ai_response)

    // 添加置信度评估
    inference_result.confidence = calculate_confidence(inference_result, context)

    RETURN inference_result
END FUNCTION

FUNCTION build_inference_context(dependency, endpoint):
    context = {
        "endpoint_info": {
            "path": endpoint.path,
            "method": endpoint.http_method,
            "controller": endpoint.controller
        },
        "dependency_info": {
            "type": dependency.type,
            "name": dependency.name,
            "injection_type": dependency.injection_type
        },
        "caller_context": {
            "package": endpoint.controller.package,
            "annotations": endpoint.controller.annotations,
            "similar_endpoints": find_similar_endpoints(endpoint)
        },
        "runtime_hints": {
            "config_properties": get_relevant_config(dependency.type),
            "environment_variables": get_relevant_env_vars(dependency.type),
            "feature_flags": get_feature_flags(dependency.type)
        }
    }

    RETURN context
END FUNCTION

FUNCTION build_inference_prompt(dependency, implementations, context):
    prompt = f"""
    角色：Java架构师

    任务：推理在HTTP端点中使用的具体实现类

    上下文信息：
    - HTTP端点：{context.endpoint_info.method} {context.endpoint_info.path}
    - Controller类：{context.endpoint_info.controller}
    - 依赖接口：{dependency.type}
    - 注入名称：{dependency.name}

    可选实现类：
    {format_implementations(implementations)}

    推理线索：
    - Controller包路径：{context.caller_context.package}
    - 相关配置：{context.runtime_hints.config_properties}
    - 类似端点：{analyze_similar_usage(context.caller_context.similar_endpoints)}

    请分析：
    1. 基于端点的HTTP方法推断可能的业务场景
    2. 分析每个实现类的命名特征和包路径规律
    3. 考虑性能要求（GET查询、POST创建、PUT更新）
    4. 评估配置和环境因素
    5. 给出最可能的实现类及推理过程

    输出格式：
    {{
        "selected_implementation": "实现类全名",
        "confidence": 0.95,
        "reasoning": "详细推理过程",
        "alternative_implementations": ["备选1", "备选2"],
        "selection_criteria": ["条件1", "条件2"],
        "runtime_conditions": "运行时条件描述"
    }}
    """

    RETURN prompt
END FUNCTION

FUNCTION calculate_confidence(inference_result, context):
    confidence_factors = {
        "naming_match": check_naming_pattern(inference_result.selected_implementation, context),
        "package_match": check_package_consistency(inference_result.selected_implementation, context),
        "annotation_match": check_annotation_patterns(inference_result.selected_implementation, context),
        "config_match": check_configuration_alignment(inference_result, context),
        "usage_pattern": check_usage_pattern_consistency(inference_result.selected_implementation, context)
    }

    // 加权计算置信度
    confidence = (
        confidence_factors.naming_match * 0.3 +
        confidence_factors.package_match * 0.25 +
        confidence_factors.annotation_match * 0.2 +
        confidence_factors.config_match * 0.15 +
        confidence_factors.usage_pattern * 0.1
    )

    RETURN confidence
END FUNCTION
```

## 5. 数据流分析

```
FUNCTION analyze_data_flow(call_chain):
    data_flow = NEW DataFlow()

    // 5.1 识别数据结构
    data_structures = identify_data_structures(call_chain)
    data_flow.data_structures = data_structures

    // 5.2 追踪数据变换
    transformations = track_data_transformations(call_chain)
    data_flow.transformations = transformations

    // 5.3 分析数据持久化
    persistence = analyze_data_persistence(call_chain)
    data_flow.persistence = persistence

    // 5.4 识别缓存操作
    cache_operations = identify_cache_operations(call_chain)
    data_flow.cache_operations = cache_operations

    // 5.5 外部服务调用
    external_calls = identify_external_calls(call_chain)
    data_flow.external_calls = external_calls

    RETURN data_flow
END FUNCTION

FUNCTION identify_data_structures(call_chain):
    structures = EMPTY_LIST

    FOR EACH node IN call_chain.nodes:
        method_signatures = get_method_signatures(node.class_name)

        FOR EACH signature IN method_signatures:
            // 识别输入参数类型
            FOR EACH param IN signature.parameters:
                IF is_data_transfer_object(param.type):
                    dto_info = analyze_dto_structure(param.type)
                    ADD dto_info TO structures
                END IF
            END FOR

            // 识别返回值类型
            IF is_data_transfer_object(signature.return_type):
                dto_info = analyze_dto_structure(signature.return_type)
                ADD dto_info TO structures
            END IF
        END FOR
    END FOR

    RETURN remove_duplicates(structures)
END FUNCTION

FUNCTION track_data_transformations(call_chain):
    transformations = EMPTY_LIST

    FOR EACH edge IN call_chain.edges:
        // 分析方法调用前后的数据变化
        from_method = edge.from_method
        to_method = edge.to_method

        transformation = {
            "from_class": edge.from_class,
            "to_class": edge.to_class,
            "method": edge.method,
            "input_type": to_method.input_type,
            "output_type": to_method.return_type,
            "transformation_type": classify_transformation(to_method),
            "mapping_details": analyze_field_mapping(to_method)
        }

        ADD transformation TO transformations
    END FOR

    RETURN transformations
END FUNCTION

FUNCTION generate_data_flow_diagram(data_flow):
    mermaid_code = "graph TD\n"

    // 定义节点样式
    mermaid_code += "    classDef controller fill:#ff9999\n"
    mermaid_code += "    classDef service fill:#99ccff\n"
    mermaid_code += "    classDef repository fill:#99ff99\n"
    mermaid_code += "    classDef external fill:#ffcc99\n"
    mermaid_code += "    classDef cache fill:#cc99ff\n"

    // 添加数据结构节点
    FOR EACH structure IN data_flow.data_structures:
        node_id = sanitize_id(structure.name)
        mermaid_code += f"    {node_id}[{structure.name}]\n"
    END FOR

    // 添加变换节点
    FOR EACH transform IN data_flow.transformations:
        from_node = sanitize_id(transform.input_type)
        to_node = sanitize_id(transform.output_type)
        method_node = f"{sanitize_id(transform.to_class)}.{transform.method}"

        mermaid_code += f"    {method_node}(({transform.method}))\n"
        mermaid_code += f"    {from_node} --> {method_node}\n"
        mermaid_code += f"    {method_node} --> {to_node}\n"
    END FOR

    // 添加持久化节点
    FOR EACH persist IN data_flow.persistence:
        db_node = f"{persist.table}_db[(Database)]"
        entity_node = sanitize_id(persist.entity)

        mermaid_code += f"    {entity_node} --> {db_node}\n"
    END FOR

    RETURN {
        "mermaid_code": mermaid_code,
        "type": "data_flow",
        "format": "mermaid"
    }
END FUNCTION
```

## 6. 端点文档生成

```
FUNCTION generate_endpoint_document(endpoint):
    doc = NEW Document()

    // 6.1 基本信息
    doc.add_header(f"{endpoint.http_method} {endpoint.path}")
    doc.add_section("基本信息", generate_basic_info(endpoint))

    // 6.2 请求说明
    doc.add_section("请求参数", generate_request_params(endpoint))

    // 6.3 响应说明
    doc.add_section("响应格式", generate_response_format(endpoint))

    // 6.4 调用链路
    doc.add_section("调用链路", generate_call_chain_doc(endpoint))

    // 6.5 实现类分析
    doc.add_section("实现类分析", generate_impl_analysis(endpoint))

    // 6.6 数据流图
    doc.add_section("数据流图", endpoint.analyses.data_flow_diagram)

    // 6.7 关联Interface
    doc.add_section("关联Interface", generate_interface_mapping(endpoint))

    // 6.8 使用示例
    doc.add_section("使用示例", generate_usage_examples(endpoint))

    RETURN doc
END FUNCTION

FUNCTION generate_call_chain_doc(endpoint):
    chain = endpoint.analyses.call_chain
    doc = NEW Section()

    // 生成调用路径
    path_string = " → ".join(chain.node_names)
    doc.add_content(f"**调用路径：** {path_string}")

    // 生成详细表格
    table = NEW MarkdownTable()
    table.add_headers(["层级", "类名", "方法", "说明", "实现类"])

    FOR EACH node IN chain.nodes:
        impl_class = ""
        IF node.has_injected_interface:
            impl = node.inferred_implementation
            impl_class = f"{impl.class_name} (置信度: {impl.confidence:.0%})"
        END IF

        table.add_row([
            node.layer,
            node.class_name,
            node.method,
            node.description,
            impl_class
        ])
    END FOR

    doc.add_content(table.to_markdown())

    // 添加性能关键点
    performance_notes = identify_performance_points(chain)
    IF performance_notes NOT empty:
        doc.add_subsection("性能注意点", format_performance_notes(performance_notes))
    END IF

    RETURN doc
END FUNCTION

FUNCTION generate_impl_analysis(endpoint):
    impl_section = NEW Section()

    FOR EACH dependency IN endpoint.analyses.dependencies:
        IF dependency.inferred_implementation:
            impl_doc = {
                "interface": dependency.type,
                "selected_implementation": dependency.inferred_implementation.selected_implementation,
                "confidence": dependency.inferred_implementation.confidence,
                "reasoning": dependency.inferred_implementation.reasoning,
                "alternatives": dependency.inferred_implementation.alternative_implementations,
                "selection_conditions": dependency.inferred_implementation.selection_criteria
            }

            impl_section.add_subsection(dependency.name, format_impl_doc(impl_doc))
        END IF
    END FOR

    RETURN impl_section
END FUNCTION

FUNCTION generate_interface_mapping(endpoint):
    mapping_section = NEW Section()

    // 收集所有关联的Interface
    interfaces = collect_related_interfaces(endpoint)

    FOR EACH interface IN interfaces:
        mapping_info = {
            "interface_name": interface.name,
            "used_methods": interface.used_methods,
            "implementation": interface.actual_implementation,
            "call_pattern": interface.call_pattern
        }

        mapping_section.add_subsection(interface.name, format_mapping_info(mapping_info))
    END FOR

    RETURN mapping_section
END FUNCTION
```

## 7. 批量处理和质量保证

```
FUNCTION process_all_endpoints_batch(endpoints):
    // 创建并行处理池
    pool = NEW ThreadPool()

    // 分批处理
    batches = split_into_batches(endpoints, BATCH_SIZE)

    FOR EACH batch IN batches:
        futures = EMPTY_LIST

        FOR EACH endpoint IN batch:
            future = pool.submit(analyze_endpoint, endpoint)
            ADD future TO futures
        END FOR

        // 等待批次完成
        FOR EACH future IN futures:
            analysis = future.get()
            validate_analysis_result(analysis)
        END FOR
    END FOR

    pool.shutdown()
END FUNCTION

FUNCTION validate_analysis_result(analysis):
    issues = EMPTY_LIST

    // 验证调用链完整性
    IF analysis.call_chain.has_breaks():
        issues.add("调用链存在断点")
    END IF

    // 验证推理结果
    FOR EACH impl_inference IN analysis.implementations:
        IF impl_inference.confidence < CONFIDENCE_THRESHOLD:
            issues.add(f"{impl_inference.interface} 推理置信度过低")
        END IF
    END FOR

    // 验证数据流
    IF analysis.data_flow.has_missing_transformations():
        issues.add("数据流变换不完整")
    END IF

    IF issues NOT empty:
        log_validation_issues(analysis, issues)
    END IF

    RETURN issues
END FUNCTION
```