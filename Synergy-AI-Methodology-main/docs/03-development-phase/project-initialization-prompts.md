# 前后端项目初始化AI提示词模板

## 概述

本文档提供了基于不同项目类型的前后端项目初始化AI提示词模板，涵盖管理后台、C端应用和移动端三种常见场景。

## 技术栈选择AI

### 完整提示词
```
你是一位技术架构专家，基于项目需求推荐最适合的技术栈。

请分析以下项目信息：

**项目基本信息：**
- 项目名称：[项目名称]
- 项目类型：[管理后台/C端应用/移动端应用]
- 目标用户：[用户规模和特征]
- 业务复杂度：[简单/中等/复杂]

**技术要求：**
- 性能要求：[响应时间、并发量等]
- 安全要求：[数据安全、认证授权等]
- 开发周期：[开发时间限制]
- 维护要求：[运维复杂度]

**团队背景：**
- 技术偏好：[团队熟悉的技术]
- 人员配置：[前端x人，后端x人]
- 经验水平：[初级/中级/资深]

请提供以下内容：

1. **技术栈推荐**
   - 前端框架及理由
   - 后端框架及理由
   - 数据库选择及理由
   - 部署方案及理由

2. **项目结构设计**
   - 前端目录结构
   - 后端目录结构
   - 模块划分建议
   - 公共组件设计

3. **核心依赖**
   - 前端关键包列表
   - 后端关键依赖
   - 开发工具推荐
   - 测试框架选择

4. **实施建议**
   - 开发环境配置
   - 构建优化建议
   - 监控方案
   - 潜在风险提示
```

## 1. 管理后台项目初始化

### 1.1 前端项目初始化（React + Ant Design Pro）

#### 提示词模板
```
你是一位React前端架构专家，请基于以下信息初始化一个管理后台项目：

**项目信息：**
- 项目名称：[项目名称]
- 基础框架：React 18 + TypeScript
- UI框架：Ant Design Pro 6.x
- 状态管理：Redux Toolkit
- 路由：React Router 6
- 构建工具：Vite
- 代码规范：ESLint + Prettier
- 测试框架：Jest + React Testing Library

**UI描述JSON：**
[粘贴UI描述JSON内容]

**最终设计规范：**
[粘贴最终设计规范]

请执行以下任务：

1. **生成项目结构**
   ```
   project-name/
   ├── config/             # 配置文件
   │   ├── config.ts      # Umi配置
   │   ├── routes.ts      # 路由配置
   │   └── defaultSettings.ts
   ├── mock/              # Mock数据
   ├── public/            # 静态资源
   ├── src/
   │   ├── components/    # 公共组件
   │   │   ├── Common/    # 通用组件
   │   │   └── Chart/     # 图表组件
   │   ├── pages/         # 页面组件
   │   │   ├── Dashboard/  # 仪表板
   │   │   ├── User/       # 用户管理
   │   │   └── [其他模块]/
   │   ├── services/      # API服务
   │   ├── models/        # 数据模型（Redux）
   │   ├── utils/         # 工具函数
   │   ├── hooks/         # 自定义Hooks
   │   ├── locales/       # 国际化
   │   └── typings/       # TypeScript类型定义
   ├── tests/             # 测试文件
   ├── .eslintrc.js       # ESLint配置
   ├── .prettierrc.js     # Prettier配置
   ├── package.json       # 依赖配置
   └── README.md          # 项目说明
   ```

2. **生成package.json**
   ```json
   {
     "name": "project-name",
     "version": "1.0.0",
     "private": true,
     "dependencies": {
       "@ant-design/icons": "^5.0.0",
       "@ant-design/pro-components": "^2.4.0",
       "@reduxjs/toolkit": "^1.9.0",
       "@types/react": "^18.0.0",
       "@types/react-dom": "^18.0.0",
       "antd": "^5.0.0",
       "react": "^18.0.0",
       "react-dom": "^18.0.0",
       "react-redux": "^8.0.0",
       "react-router-dom": "^6.0.0",
       "umi": "^4.0.0",
       "@umijs/max": "^4.0.0"
     },
     "devDependencies": {
       "@testing-library/react": "^13.0.0",
       "@types/jest": "^29.0.0",
       "@typescript-eslint/eslint-plugin": "^5.0.0",
       "eslint": "^8.0.0",
       "jest": "^29.0.0",
       "prettier": "^2.0.0",
       "typescript": "^4.9.0",
       "vite": "^4.0.0"
     },
     "scripts": {
       "start": "umi dev",
       "build": "umi build",
       "test": "umi test",
       "lint": "eslint src --ext .ts,.tsx",
       "format": "prettier --write \"src/**/*.{ts,tsx}\""
     }
   }
   ```

3. **生成基础配置文件**
   - TypeScript配置 (tsconfig.json)
   - ESLint配置 (.eslintrc.js)
   - Prettier配置 (.prettierrc.js)
   - UmiJS配置 (config/config.ts)

4. **生成基础组件**
   - Layout组件（包含侧边栏、头部）
   - AuthRoute权限路由组件
   - PageContainer页面容器
   - ErrorBoundary错误边界

5. **生成Mock数据示例**
   - 用户相关Mock API
   - 登录认证Mock
   - 权限验证Mock

6. **生成示例页面**
   - Dashboard仪表板页面
   - User Management用户管理页面
   - Profile个人资料页面

请确保生成的代码：
- 使用TypeScript严格模式
- 遵循Ant Design Pro最佳实践
- 包含完整的类型定义
- 支持国际化
- 实现基本的权限控制
```

### 1.2 后端项目初始化（Spring Boot）

#### 提示词模板
```
你是一位Spring Boot后端架构专家，请基于以下信息初始化一个管理后台后端项目：

**项目信息：**
- 项目名称：[项目名称]
- JDK版本：17
- Spring Boot版本：3.1.x
- 数据库：MySQL 8.0
- 缓存：Redis
- 构建工具：Gradle

**数据库设计：**
[粘贴数据库ER图或表结构]

**API文档：**
[粘贴Swagger API文档]

请执行以下任务：

1. **生成项目结构**
   ```
   project-backend/
   ├── src/main/java/com/example/project/
   │   ├── config/              # 配置类
   │   │   ├── SecurityConfig.java    # 安全配置
   │   │   ├── RedisConfig.java       # Redis配置
   │   │   ├── MyBatisConfig.java      # MyBatis配置
   │   │   └── SwaggerConfig.java     # Swagger配置
   │   ├── controller/          # 控制器
   │   │   ├── BaseController.java
   │   │   ├── UserController.java
   │   │   └── [其他Controller].java
   │   ├── service/             # 服务层
   │   │   ├── UserService.java
   │   │   ├── UserServiceImpl.java
   │   │   └── [其他Service].java
   │   ├── repository/          # 数据访问层
   │   │   ├── UserMapper.java
   │   │   └── [其他Mapper].java
   │   ├── entity/              # 实体类
   │   │   ├── User.java
   │   │   ├── BaseEntity.java
   │   │   └── [其他Entity].java
   │   ├── dto/                 # 数据传输对象
   │   │   ├── UserDTO.java
   │   │   ├── UserQueryDTO.java
   │   │   └── [其他DTO].java
   │   ├── vo/                  # 视图对象
   │   │   ├── UserVO.java
   │   │   └── [其他VO].java
   │   ├── common/              # 公共类
   │   │   ├── exception/       # 异常处理
   │   │   ├── util/            # 工具类
   │   │   ├── constant/        # 常量
   │   │   └── annotation/      # 自定义注解
   │   └── ProjectApplication.java
   ├── src/main/resources/
   │   ├── mapper/             # MyBatis映射文件
   │   │   ├── UserMapper.xml
   │   │   └── [其他Mapper].xml
   │   ├── application.yml     # 应用配置
   │   ├── application-dev.yml # 开发环境配置
   │   └── application-prod.yml # 生产环境配置
   ├── src/test/java/          # 测试文件
   └── build.gradle            # 构建配置
   ```

2. **生成build.gradle配置**
   ```groovy
   plugins {
       id 'java'
       id 'org.springframework.boot' version '3.1.0'
       id 'io.spring.dependency-management' version '1.1.0'
   }

   group = 'com.example'
   version = '1.0.0'
   sourceCompatibility = '17'

   configurations {
       compileOnly {
           extendsFrom annotationProcessor
       }
   }

   repositories {
       mavenCentral()
   }

   dependencies {
       // Spring Boot Starters
       implementation 'org.springframework.boot:spring-boot-starter-web'
       implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
       implementation 'org.springframework.boot:spring-boot-starter-security'
       implementation 'org.springframework.boot:spring-boot-starter-data-redis'
       implementation 'org.springframework.boot:spring-boot-starter-validation'
       
       // Database
       runtimeOnly 'mysql:mysql-connector-java'
       implementation 'org.mybatis.spring.boot:mybatis-spring-boot-starter:3.0.0'
       
       // Documentation
       implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.1.0'
       
       // Utils
       implementation 'com.fasterxml.jackson.core:jackson-databind'
       implementation 'org.mapstruct:mapstruct:1.5.5.Final'
       annotationProcessor 'org.mapstruct:mapstruct-processor:1.5.5.Final'
       
       // Development tools
       developmentOnly 'org.springframework.boot:spring-boot-devtools'
       annotationProcessor 'org.springframework.boot:spring-boot-configuration-processor'
       
       // Test
       testImplementation 'org.springframework.boot:spring-boot-starter-test'
       testImplementation 'org.springframework.security:spring-security-test'
   }

   tasks.named('test') {
       useJUnitPlatform()
   }
   ```

3. **生成核心配置文件**
   - application.yml - 基础配置
   - SecurityConfig.java - Spring Security配置
   - SwaggerConfig.java - API文档配置
   - RedisConfig.java - 缓存配置
   - MyBatisConfig.java - 数据库配置

4. **生成基础实体类**
   - BaseEntity.java（包含id、createTime、updateTime）
   - User.java（用户实体）
   - Role.java（角色实体）
   - Permission.java（权限实体）

5. **生成通用响应类**
   - Result.java（统一响应格式）
   - PageResult.java（分页响应）
   - ErrorCode.java（错误码定义）

6. **生成异常处理**
   - GlobalExceptionHandler.java（全局异常处理）
   - BusinessException.java（业务异常）
   - ValidationException.java（验证异常）

7. **生成安全相关类**
   - JwtTokenUtil.java（JWT工具类）
   - UserDetailsServiceImpl.java（用户详情服务）
   - AuthenticationEntryPointImpl.java（认证入口点）

8. **生成工具类**
   - DateUtils.java（日期工具）
   - StringUtils.java（字符串工具）
   - BeanUtils.java（Bean拷贝工具）

请确保生成的代码：
- 遵循Spring Boot最佳实践
- 实现完整的认证授权机制
- 包含完整的API文档
- 支持分页和排序
- 实现参数验证
- 包含适当的日志记录
```

## 2. C端应用项目初始化

### 2.1 前端项目初始化（Next.js）

#### 提示词模板
```
你是一位Next.js前端架构专家，请基于以下信息初始化一个C端应用项目：

**项目信息：**
- 项目名称：[项目名称]
- 框架：Next.js 14
- 渲染模式：App Router
- 样式方案：Tailwind CSS
- 状态管理：Zustand
- 表单：React Hook Form + Zod
- 数据获取：TanStack Query
- 包管理：pnpm

**UI描述JSON：**
[粘贴UI描述JSON内容]

**设计规范：**
[粘贴设计规范]

请执行以下任务：

1. **生成项目结构**
   ```
   project-name/
   ├── app/                  # App Router
   │   ├── (auth)/          # 认证相关路由组
   │   │   ├── login/
   │   │   └── register/
   │   ├── (public)/        # 公开路由组
   │   │   ├── about/
   │   │   └── contact/
   │   ├── (user)/          # 用户路由组
   │   │   ├── dashboard/
   │   │   └── profile/
   │   ├── globals.css      # 全局样式
   │   ├── layout.tsx       # 根布局
   │   ├── layout.module.css # 布局样式
   │   └── page.tsx         # 首页
   ├── components/          # 组件
   │   ├── ui/             # 基础UI组件
   │   │   ├── button.tsx
   │   │   ├── input.tsx
   │   │   └── ...
   │   ├── forms/          # 表单组件
   │   ├── layout/         # 布局组件
   │   ├── modules/        # 业务模块组件
   │   └── common/         # 通用组件
   ├── lib/                # 工具库
   │   ├── utils/          # 工具函数
   │   ├── api/           # API客户端
   │   ├── validations/   # 验证规则
   │   └── constants/     # 常量
   ├── hooks/             # 自定义Hooks
   ├── store/             # 状态管理
   ├── types/             # TypeScript类型
   ├── public/            # 静态资源
   ├── styles/            # 样式文件
   ├── next.config.mjs    # Next.js配置
   ├── tailwind.config.ts # Tailwind配置
   ├── tsconfig.json      # TypeScript配置
   └── package.json       # 依赖配置
   ```

2. **生成核心配置文件**
   - next.config.mjs（Next.js配置）
   - tailwind.config.ts（Tailwind配置）
   - tsconfig.json（TypeScript配置）
   - .eslintrc.json（ESLint配置）

3. **生成UI组件库**
   基于设计规范生成基础组件：
   - Button组件（支持多种变体）
   - Input组件（包含验证）
   - Card组件
   - Modal组件
   - Loading组件
   - ErrorBoundary组件

4. **生成布局组件**
   - Header组件（导航栏）
   - Footer组件
   - Sidebar组件
   - Breadcrumb组件

5. **生成表单组件**
   ```tsx
   // components/forms/auth-form.tsx
   "use client";
   
   import { useForm } from "react-hook-form";
   import { zodResolver } from "@hookform/resolvers/zod";
   import { z } from "zod";
   import { Button } from "@/components/ui/button";
   import { Input } from "@/components/ui/input";
   
   const authSchema = z.object({
     email: z.string().email("请输入有效的邮箱"),
     password: z.string().min(6, "密码至少6位"),
   });
   
   type AuthFormData = z.infer<typeof authSchema>;
   
   export function AuthForm() {
     const {
       register,
       handleSubmit,
       formState: { errors },
     } = useForm<AuthFormData>({
       resolver: zodResolver(authSchema),
     });
     
     const onSubmit = (data: AuthFormData) => {
       console.log(data);
     };
     
     return (
       <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
         <div>
           <Input
             {...register("email")}
             type="email"
             placeholder="邮箱"
           />
           {errors.email && (
             <p className="text-red-500 text-sm">{errors.email.message}</p>
           )}
         </div>
         <div>
           <Input
             {...register("password")}
             type="password"
             placeholder="密码"
           />
           {errors.password && (
             <p className="text-red-500 text-sm">{errors.password.message}</p>
           )}
         </div>
         <Button type="submit" className="w-full">
           登录
         </Button>
       </form>
     );
   }
   ```

6. **生成API客户端**
   ```typescript
   // lib/api/client.ts
   import axios from 'axios';
   import { toast } from 'react-hot-toast';
   
   export const apiClient = axios.create({
     baseURL: process.env.NEXT_PUBLIC_API_URL,
     timeout: 10000,
   });
   
   // 请求拦截器
   apiClient.interceptors.request.use(
     (config) => {
       const token = localStorage.getItem('token');
       if (token) {
         config.headers.Authorization = `Bearer ${token}`;
       }
       return config;
     },
     (error) => {
       return Promise.reject(error);
     }
   );
   
   // 响应拦截器
   apiClient.interceptors.response.use(
     (response) => response.data,
     (error) => {
       const message = error.response?.data?.message || '请求失败';
       toast.error(message);
       
       // 401处理
       if (error.response?.status === 401) {
         window.location.href = '/login';
       }
       
       return Promise.reject(error);
     }
   );
   ```

7. **生成状态管理Store**
   ```typescript
   // store/auth-store.ts
   import { create } from 'zustand';
   import { persist } from 'zustand/middleware';
   
   interface AuthState {
     user: User | null;
     token: string | null;
     isAuthenticated: boolean;
     login: (email: string, password: string) => Promise<void>;
     logout: () => void;
   }
   
   export const useAuthStore = create<AuthState>()(
     persist(
       (set, get) => ({
         user: null,
         token: null,
         isAuthenticated: false,
         
         login: async (email: string, password: string) => {
           const response = await apiClient.post('/auth/login', {
             email,
             password,
           });
           
           set({
             user: response.data.user,
             token: response.data.token,
             isAuthenticated: true,
           });
         },
         
         logout: () => {
           set({
             user: null,
             token: null,
             isAuthenticated: false,
           });
           localStorage.removeItem('token');
         },
       }),
       {
         name: 'auth-storage',
       }
     )
   );
   ```

请确保生成的代码：
- 使用Next.js 14 App Router
- 遵循Tailwind CSS最佳实践
- 实现完整的类型安全
- 支持SSR和CSR
- 包含适当的SEO配置
- 实现响应式设计
```

## 3. 移动端项目初始化

### 3.1 UniApp (Vue3) 项目初始化

#### 提示词模板
```
你是一位UniApp移动端开发专家，请基于以下信息初始化一个跨平台移动应用：

**项目信息：**
- 项目名称：[项目名称]
- 框架：UniApp + Vue3
- UI库：uView Plus
- 状态管理：Pinia
- 网络请求：uni.request封装
- 构建工具：Vite
- 平台：iOS/Android/小程序/H5

**UI描述JSON：**
[粘贴UI描述JSON内容]

**设计规范：**
[粘贴设计规范]

请执行以下任务：

1. **生成项目结构**
   ```
   project-name/
   ├── src/
   │   ├── components/     # 公共组件
   │   │   ├── common/     # 通用组件
   │   │   └── business/   # 业务组件
   │   ├── pages/         # 页面
   │   │   ├── index/
   │   │   ├── user/
   │   │   └── [其他页面]/
   │   ├── static/        # 静态资源
   │   ├── store/         # 状态管理
   │   │   ├── modules/
   │   │   └── index.js
   │   ├── utils/         # 工具函数
   │   │   ├── request.js # 网络请求
   │   │   ├── auth.js    # 认证工具
   │   │   └── common.js  # 通用工具
   │   ├── api/           # API接口
   │   ├── config/        # 配置文件
   │   ├── styles/        # 样式文件
   │   │   ├── variables.scss # 变量
   │   │   └── common.scss   # 公共样式
   │   ├── App.vue        # 应用入口
   │   ├── main.js        # 主入口
   │   ├── pages.json     # 页面配置
   │   └── manifest.json  # 应用配置
   ├── vite.config.js     # Vite配置
   ├── .eslintrc.js       # ESLint配置
   └── package.json       # 依赖配置
   ```

2. **生成package.json**
   ```json
   {
     "name": "project-name",
     "version": "1.0.0",
     "description": "",
     "scripts": {
       "dev": "uni -p app",
       "dev:h5": "uni -p h5",
       "dev:mp-weixin": "uni -p mp-weixin",
       "build": "uni build",
       "build:app": "uni build -p app",
       "build:h5": "uni build -p h5",
       "type-check": "vue-tsc --noEmit"
     },
     "dependencies": {
       "@dcloudio/uni-app": "^3.0.0",
       "@dcloudio/uni-app-plus": "^3.0.0",
       "@dcloudio/uni-h5": "^3.0.0",
       "@dcloudio/uni-mp-weixin": "^3.0.0",
       "pinia": "^2.0.0",
       "uview-plus": "^3.1.0",
       "vue": "^3.2.0"
     },
     "devDependencies": {
       "@dcloudio/types": "^3.0.0",
       "@dcloudio/uni-cli-shared": "^3.0.0",
       "@dcloudio/vite-plugin-uni": "^3.0.0",
       "sass": "^1.0.0",
       "typescript": "^5.0.0",
       "vite": "^4.0.0",
       "vue-tsc": "^1.0.0"
     }
   }
   ```

3. **生成网络请求封装**
   ```javascript
   // utils/request.js
   import { useUserStore } from '@/store'

   const baseURL = process.env.VITE_API_BASE_URL

   const request = (options) => {
     return new Promise((resolve, reject) => {
       const userStore = useUserStore()
       
       // 请求拦截
       const token = userStore.token
       const header = {
         'content-type': 'application/json'
       }
       
       if (token) {
         header['Authorization'] = `Bearer ${token}`
       }
       
       uni.request({
         url: baseURL + options.url,
         method: options.method || 'GET',
         data: options.data || {},
         header,
         success: (res) => {
           if (res.statusCode === 200) {
             if (res.data.code === 0) {
               resolve(res.data)
             } else {
               uni.showToast({
                 title: res.data.message || '请求失败',
                 icon: 'none'
               })
               reject(res.data)
             }
           } else if (res.statusCode === 401) {
             // token失效处理
             userStore.logout()
             uni.navigateTo({
               url: '/pages/login/index'
             })
             reject(new Error('请重新登录'))
           } else {
             reject(new Error(`请求失败: ${res.statusCode}`))
           }
         },
         fail: (err) => {
           uni.showToast({
             title: '网络异常，请稍后重试',
             icon: 'none'
           })
           reject(err)
         }
       })
     })
   }

   export default request
   ```

4. **生成Store模块**
   ```javascript
   // store/modules/user.js
   import { defineStore } from 'pinia'

   export const useUserStore = defineStore('user', {
     state: () => ({
       token: uni.getStorageSync('token') || '',
       userInfo: uni.getStorageSync('userInfo') || {}
     }),
     
     getters: {
       isLoggedIn: (state) => !!state.token,
       userId: (state) => state.userInfo.id
     },
     
     actions: {
       // 登录
       async login(loginForm) {
         try {
           const res = await request({
             url: '/auth/login',
             method: 'POST',
             data: loginForm
           })
           
           this.token = res.data.token
           this.userInfo = res.data.userInfo
           
           // 持久化存储
           uni.setStorageSync('token', res.data.token)
           uni.setStorageSync('userInfo', res.data.userInfo)
           
           return res
         } catch (error) {
           throw error
         }
       },
       
       // 登出
       logout() {
         this.token = ''
         this.userInfo = {}
         uni.removeStorageSync('token')
         uni.removeStorageSync('userInfo')
       }
     }
   })
   ```

5. **生成通用组件示例**
   ```vue
   <!-- components/common/NavBar.vue -->
   <template>
     <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
       <view class="nav-bar-content">
         <view class="nav-bar-left" @tap="handleLeft">
           <slot name="left">
             <text class="iconfont icon-back" v-if="back"></text>
           </slot>
         </view>
         <view class="nav-bar-title">
           {{ title }}
         </view>
         <view class="nav-bar-right">
           <slot name="right"></slot>
         </view>
       </view>
     </view>
   </template>

   <script setup>
   import { computed } from 'vue'

   const props = defineProps({
     title: {
       type: String,
       default: ''
     },
     back: {
       type: Boolean,
       default: false
     },
     bgColor: {
       type: String,
       default: '#ffffff'
     }
   })

   const statusBarHeight = computed(() => {
     // 获取状态栏高度
     const systemInfo = uni.getSystemInfoSync()
     return systemInfo.statusBarHeight || 0
   })

   const handleLeft = () => {
     if (props.back) {
       uni.navigateBack()
     }
   }
   </script>

   <style lang="scss" scoped>
   .nav-bar {
     background-color: v-bind(bgColor);
     
     &-content {
       height: 44px;
       display: flex;
       align-items: center;
       justify-content: space-between;
       padding: 0 15px;
       
       &-left, &-right {
         width: 60px;
         display: flex;
         align-items: center;
       }
       
       &-title {
         flex: 1;
         text-align: center;
         font-size: 16px;
         font-weight: 500;
         color: #333;
       }
     }
   }
   </style>
   ```

请确保生成的代码：
- 遵循UniApp最佳实践
- 支持多端适配
- 实现完整的生命周期
- 包含错误处理
- 支持主题定制
```

## 4. 代码生成优化建议

### 4.1 增量生成策略
```
对于已有项目的增量更新：

1. **分析现有结构**
   - 检查当前项目结构
   - 识别新增模块
   - 确保兼容性

2. **差异化生成**
   - 只生成新增部分
   - 保留现有配置
   - 合并配置文件

3. **冲突解决**
   - 标记潜在冲突
   - 提供合并建议
   - 生成迁移脚本
```

### 4.2 质量保证
- 生成的代码必须包含类型定义
- 遵循各框架的最佳实践
- 包含适当的错误处理
- 实现必要的安全措施
- 支持国际化（如需要）

---

*模板版本：1.0*  
*最后更新：2025-09-22*