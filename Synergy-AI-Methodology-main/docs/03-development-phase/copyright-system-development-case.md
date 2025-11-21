# 软著生成系统 - 开发案例演示

## 概述

本案例展示如何使用AI协同开发框架，基于第二阶段生成的规格文档，开发软著生成系统。案例涵盖设计风格评测、项目初始化、代码生成和集成部署的完整流程。

## 项目背景

基于第二阶段的规格文档，我们将开发一个软著生成系统，包括：
- 管理后台（React + Ant Design Pro）
- 用户端（Next.js）
- 后端API（Spring Boot）

## 第一阶段：设计风格评测与确认

### 1.1 生成可交互原型

**设计评测AI工作流程：**

```bash
# 输入：三套设计风格文档
design-evaluation-ai --input design-styles.md --output prototypes

# 生成内容：
# - Figma原型（简约专业风）
# - Figma原型（友好活力风）
# - Figma原型（极简科技风）
```

### 1.2 用户评测执行

**评测方案：**
- 目标用户：15位独立开发者
- 评测方式：在线A/B测试
- 评测时长：30分钟/人

**评测结果：**
```
选择结果统计：
- 简约专业风：45% （专业、可信赖）
- 友好活力风：35% （友好、现代）
- 极简科技风：20% （过于冷淡）

关键反馈：
1. 开发者更喜欢专业的外观
2. 界面清晰度最重要
3. 操作效率是关键
```

### 1.3 最终设计规范

**整合后的设计规范：**
```markdown
# 软著宝设计系统

## 核心原则
- 专业性：体现工具的专业性
- 高效：简化操作流程
- 清晰：信息层次分明

## 色彩系统
- 主色：#2E7DFF（专业蓝）
- 辅助色：#00C896（成功绿）
- 强调色：#FFA940（警告橙）
- 中性色：#86909C（文字灰）

## 字体系统
- 中文：PingFang SC
- 英文：SF Pro Text
- 代码：JetBrains Mono
```

## 第二阶段：项目初始化

### 2.1 技术栈选择

**技术栈AI分析结果：**
```
项目分析：
- 管理后台：需要丰富组件库，快速开发
- 用户端：需要SEO优化，快速加载
- 移动端：跨平台，考虑成本

推荐技术栈：
1. 管理后台：React + Ant Design Pro
2. 用户端：Next.js + Tailwind CSS
3. 后端：Spring Boot 3.x + MySQL
4. 移动端：先做Web响应式，后期考虑UniApp
```

### 2.2 项目结构生成

**使用项目初始化AI生成标准项目结构：**

#### 后端项目结构
```bash
copyright-backend/
├── src/main/java/com/copyright/
│   ├── config/              # 配置类
│   ├── controller/          # 控制器
│   ├── service/             # 服务层
│   ├── repository/          # 数据访问
│   ├── entity/              # 实体类
│   ├── dto/                 # 数据传输对象
│   └── common/              # 公共类
└── src/main/resources/
    ├── mapper/              # MyBatis映射
    ├── application.yml       # 配置文件
    └── db/migration/        # 数据库迁移
```

#### 前端管理后台结构
```bash
copyright-admin/
├── config/
├── mock/
├── public/
└── src/
    ├── components/          # 组件库
    ├── pages/              # 页面
    ├── services/           # API服务
    ├── models/            # 数据模型
    └── utils/             # 工具函数
```

### 2.3 核心依赖配置

**package.json（管理后台）：**
```json
{
  "dependencies": {
    "@ant-design/pro-components": "^2.4.0",
    "antd": "^5.0.0",
    "react": "^18.0.0",
    "@reduxjs/toolkit": "^1.9.0",
    "umi": "^4.0.0"
  }
}
```

**build.gradle（后端）：**
```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.mybatis.spring.boot:mybatis-spring-boot-starter:3.0.0'
    implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.1.0'
}
```

## 第三阶段：代码生成

### 3.1 后端代码生成

基于数据库设计和API文档，使用代码生成AI生成后端代码。

#### 实体类生成示例
```java
// src/main/java/com/copyright/entity/Project.java
@Entity
@Table(name = "projects")
@Data
@Schema(description = "项目实体")
public class Project {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @NotBlank
    @Column(nullable = false)
    private String softwareName;
    
    @NotBlank
    @Column(nullable = false)
    private String softwareVersion;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SoftwareType softwareType;
    
    @Column(unique = true)
    private String codeRepoUrl;
    
    @Lob
    private String softwareDescription;
    
    @Column(name = "tech_stack")
    private String techStack;
    
    @Enumerated(EnumType.STRING)
    private ProjectStatus status;
    
    @CreationTimestamp
    private LocalDateTime createdAt;
}
```

#### Controller生成示例
```java
// src/main/java/com/copyright/controller/ProjectController.java
@RestController
@RequestMapping("/api/v1/projects")
@Tag(name = "项目管理")
@RequiredArgsConstructor
public class ProjectController {
    
    private final ProjectService projectService;
    
    @Operation(summary = "创建项目")
    @PostMapping
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ProjectVO> createProject(
            @Valid @RequestBody ProjectCreateDTO createDTO) {
        return ResponseEntity.ok(projectService.createProject(createDTO));
    }
    
    @Operation(summary = "提取源代码")
    @PostMapping("/{id}/extract")
    public ResponseEntity<Void> extractCode(
            @PathVariable Long id,
            @RequestBody CodeExtractRequest request) {
        projectService.extractCode(id, request);
        return ResponseEntity.accepted().build();
    }
}
```

### 3.2 前端代码生成

基于UI描述JSON和设计规范，生成前端组件。

#### 页面组件生成示例
```tsx
// src/pages/project/ProjectList.tsx
import React, { useState } from 'react';
import { Card, Table, Button, Tag, Space, Modal } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons';
import { useRequest } from 'ahooks';
import { ProjectService } from '@/services/project.service';
import ProjectCreateModal from './ProjectCreateModal';

const ProjectList: React.FC = () => {
  const [createModalVisible, setCreateModalVisible] = useState(false);
  
  const { data, loading, refresh } = useRequest(ProjectService.getProjects);
  
  const columns = [
    {
      title: '软件名称',
      dataIndex: 'softwareName',
      key: 'softwareName',
    },
    {
      title: '版本',
      dataIndex: 'softwareVersion',
      key: 'softwareVersion',
    },
    {
      title: '类型',
      dataIndex: 'softwareType',
      key: 'softwareType',
      render: (type) => (
        <Tag color={type === '应用软件' ? 'blue' : 'green'}>
          {type}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={
          status === 'completed' ? 'green' :
          status === 'generating' ? 'orange' : 'default'
        }>
          {status}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button icon={<EyeOutlined />}>查看</Button>
          <Button icon={<EditOutlined />}>编辑</Button>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          创建项目
        </Button>
      </div>
      
      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={loading}
        pagination={{
          total: data?.total,
          showSizeChanger: true,
          showQuickJumper: true,
        }}
      />
      
      <ProjectCreateModal
        visible={createModalVisible}
        onSuccess={() => {
          setCreateModalVisible(false);
          refresh();
        }}
        onCancel={() => setCreateModalVisible(false)}
      />
    </Card>
  );
};

export default ProjectList;
```

### 3.3 API服务生成

```typescript
// src/services/project.service.ts
import { request } from '@/utils/request';

export class ProjectService {
  static getProjects(params?: {
    page?: number;
    size?: number;
    status?: string;
  }) {
    return request.get<{
      total: number;
      items: ProjectItem[];
    }>('/projects', { params });
  }

  static createProject(data: {
    softwareName: string;
    softwareVersion: string;
    softwareType: string;
    codeRepoUrl?: string;
    softwareDescription?: string;
    techStack?: string[];
  }) {
    return request.post<ProjectItem>('/projects', data);
  }

  static extractCode(projectId: number, data: {
    repoUrl: string;
    branch?: string;
  }) {
    return request.post(`/projects/${projectId}/extract`, data);
  }
}
```

## 第四阶段：集成与测试

### 4.1 API集成测试

```typescript
// tests/services/project.test.ts
import { ProjectService } from '@/services/project.service';
import { renderHook } from '@testing-library/react';

jest.mock('@/utils/request');

describe('ProjectService', () => {
  test('should get projects list', async () => {
    const mockData = {
      total: 1,
      items: [
        {
          id: 1,
          softwareName: '测试软件',
          status: 'draft',
        },
      ],
    };

    (request.get as jest.Mock).mockResolvedValue(mockData);

    const result = await ProjectService.getProjects();
    expect(result).toEqual(mockData);
    expect(request.get).toHaveBeenCalledWith('/projects');
  });
});
```

### 4.2 E2E测试

```typescript
// tests/e2e/project.spec.ts
describe('Project Management', () => {
  beforeEach(() => {
    cy.login();
    cy.visit('/projects');
  });

  it('should create project successfully', () => {
    cy.get('[data-testid="create-project-btn"]').click();
    
    cy.get('[name="softwareName"]').type('软著宝测试版');
    cy.get('[name="softwareVersion"]').type('V1.0');
    cy.get('[name="softwareType"]').select('应用软件');
    
    cy.get('[data-testid="submit-btn"]').click();
    
    cy.contains('创建成功').should('be.visible');
    cy.contains('软著宝测试版').should('be.visible');
  });
});
```

## 第五阶段：部署配置

### 5.1 Docker化配置

**后端Dockerfile：**
```dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app
COPY build/libs/*.jar app.jar

EXPOSE 8080

ENV JAVA_OPTS="-Xmx512m -Xms256m"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

**前端Dockerfile：**
```dockerfile
FROM node:16-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
```

### 5.2 Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./copyright-backend
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      - mysql
      - redis

  frontend:
    build: ./copyright-admin
    ports:
      - "80:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: copyright
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

## 开发效率对比

| 环节 | 传统开发 | AI协同开发 | 效率提升 |
|------|----------|------------|----------|
| 项目初始化 | 2天 | 2小时 | 24倍 |
| 代码生成 | 2周 | 2天 | 7倍 |
| 测试编写 | 3天 | 4小时 | 18倍 |
| 部署配置 | 1天 | 2小时 | 12倍 |

**总计：从3周缩短到3天，效率提升约7倍**

## 关键成功因素

### 1. 规格文档质量
- 第二阶段生成的规格文档必须完整准确
- UI描述JSON要详细
- API文档要规范

### 2. AI角色协作
- 各个AI角色职责明确
- 生成代码风格一致
- 及时解决冲突

### 3. 人工审核把关
- 关键业务逻辑需要人工审核
- 安全性检查必不可少
- 性能优化需要人工调优

## 经验总结

1. **增量生成比全量生成更实用**
   - 保留现有业务逻辑
   - 只生成新增部分

2. **代码模板需要持续优化**
   - 积累最佳实践
   - 适应业务变化

3. **质量控制很重要**
   - 自动化测试
   - 代码审查
   - 性能监控

---

*案例版本：1.0*  
*最后更新：2025-09-22*