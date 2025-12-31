# 画布式编辑器开发指南

基于 Google Mixboard 的设计，专注于画布式 AI 编辑器的开发。

## 🎯 核心需求分析

### 画布式 vs 节点式

**画布式编辑器特点：**
- ✅ 自由布局，类似 Figma/Miro
- ✅ 元素可自由拖拽、缩放、旋转
- ✅ 上下文菜单操作（hover 显示）
- ✅ 工具栏模式切换（选择、平移、添加元素）
- ✅ 无限画布，支持缩放和平移
- ✅ AI 生成内容直接添加到画布

**适用场景：**
- 创意设计工具
- AI 图像/视频生成平台
- 内容创作工具
- 可视化白板

## 🛠️ 核心技术栈推荐

### 方案一：Fabric.js（推荐）⭐

**为什么选择 Fabric.js：**
- ✅ 专门为画布编辑器设计
- ✅ 完整的对象模型（Object Model）
- ✅ 内置事件处理
- ✅ 序列化/反序列化支持
- ✅ 丰富的图形类型
- ✅ 活跃的社区

**GitHub**: https://github.com/fabricjs/fabric.js
**Stars**: 9k+
**文档**: http://fabricjs.com/

**核心功能：**
```javascript
// 创建画布
const canvas = new fabric.Canvas('canvas');

// 添加图片
fabric.Image.fromURL('image.jpg', (img) => {
  canvas.add(img);
});

// 添加文本
const text = new fabric.Text('Hello', {
  left: 100,
  top: 100,
  fontSize: 20
});
canvas.add(text);

// 序列化
const json = JSON.stringify(canvas.toJSON());
```

**适用场景：**
- 需要复杂图形操作
- 需要对象序列化
- 需要丰富的交互功能

### 方案二：Konva.js

**GitHub**: https://github.com/konvajs/konva
**Stars**: 10k+
**文档**: https://konvajs.org/

**特点：**
- ✅ 高性能 2D 画布库
- ✅ 支持复杂图形和动画
- ✅ React 集成（react-konva）
- ✅ 事件处理完善

**适用场景：**
- 需要高性能渲染
- 需要动画效果
- React 项目

### 方案三：React Flow（画布模式）

**GitHub**: https://github.com/xyflow/xyflow
**Stars**: 20k+

**特点：**
- ✅ 虽然主要用于节点编辑器，但也可以做画布
- ✅ React 原生支持
- ✅ TypeScript 支持
- ✅ 丰富的交互功能

**适用场景：**
- 需要 React 生态
- 未来可能扩展节点功能
- 需要 TypeScript 支持

### 方案四：Paper.js（矢量图形）

**GitHub**: https://github.com/paperjs/paper.js
**Stars**: 14k+

**特点：**
- ✅ 矢量图形处理
- ✅ 路径操作强大
- ✅ 适合复杂图形编辑

**适用场景：**
- 需要矢量图形
- 需要路径编辑
- 需要复杂图形操作

## 📦 完整技术栈

### 前端框架
```json
{
  "框架": "React 18+ / Vue 3 / Next.js",
  "语言": "TypeScript",
  "状态管理": "Zustand / Jotai (轻量级)",
  "样式": "Tailwind CSS + CSS Modules",
  "画布库": "Fabric.js (推荐) / Konva.js"
}
```

### UI 组件库
- **shadcn/ui** - 现代化组件（推荐）
- **Radix UI** - 无样式组件基础
- **Headless UI** - 无样式组件

### 工具库
- **react-draggable** - 拖拽功能
- **react-resizable** - 调整大小
- **react-hotkeys-hook** - 快捷键
- **zustand** - 状态管理（轻量）
- **react-query** - 数据获取和缓存

### 后端
```json
{
  "运行时": "Node.js / Python",
  "框架": "Express / FastAPI",
  "AI 服务": "OpenAI API / Stable Diffusion API",
  "数据库": "PostgreSQL (画布数据) + Redis (缓存)",
  "文件存储": "AWS S3 / Cloudflare R2 / 本地存储"
}
```

## 🏗️ 架构设计

### 核心模块

```
src/
├── components/
│   ├── Canvas/              # 画布组件
│   │   ├── Canvas.tsx       # 主画布
│   │   ├── CanvasToolbar.tsx # 工具栏
│   │   └── CanvasGrid.tsx   # 网格背景
│   ├── Elements/            # 画布元素
│   │   ├── ImageElement.tsx # 图片元素
│   │   ├── TextElement.tsx  # 文本元素
│   │   └── ShapeElement.tsx # 形状元素
│   ├── ContextMenu/         # 上下文菜单
│   ├── PropertyPanel/       # 属性面板
│   └── AIGenerator/         # AI 生成器
├── stores/
│   ├── canvasStore.ts       # 画布状态
│   ├── elementStore.ts      # 元素状态
│   └── aiStore.ts           # AI 状态
├── hooks/
│   ├── useCanvas.ts         # 画布操作
│   ├── useElement.ts        # 元素操作
│   └── useAI.ts             # AI 操作
├── services/
│   ├── canvasService.ts     # 画布服务
│   └── aiService.ts         # AI 服务
└── utils/
    ├── fabricUtils.ts       # Fabric.js 工具
    └── serialization.ts     # 序列化工具
```

## 💻 实现示例

### 1. 基础画布设置（Fabric.js + React）

```typescript
// components/Canvas/Canvas.tsx
import { useEffect, useRef } from 'react';
import { fabric } from 'fabric';
import { useCanvasStore } from '@/stores/canvasStore';

export const Canvas = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvasRef = useRef<fabric.Canvas | null>(null);
  const { elements, addElement, selectElement } = useCanvasStore();

  useEffect(() => {
    if (!canvasRef.current) return;

    // 初始化 Fabric.js 画布
    const canvas = new fabric.Canvas(canvasRef.current, {
      width: window.innerWidth,
      height: window.innerHeight,
      backgroundColor: '#f5f5f5',
    });

    fabricCanvasRef.current = canvas;

    // 网格背景
    const gridPattern = createGridPattern();
    canvas.setBackgroundColor({
      source: gridPattern,
      repeat: 'repeat',
    }, () => canvas.renderAll());

    // 选择事件
    canvas.on('selection:created', (e) => {
      selectElement(e.selected?.[0]?.id);
    });

    // 对象添加事件
    canvas.on('object:added', (e) => {
      const obj = e.target;
      if (obj) {
        addElement({
          id: obj.id || generateId(),
          type: obj.type,
          data: obj.toJSON(),
        });
      }
    });

    return () => {
      canvas.dispose();
    };
  }, []);

  return (
    <div className="canvas-container">
      <canvas ref={canvasRef} />
    </div>
  );
};
```

### 2. 工具栏组件

```typescript
// components/Canvas/CanvasToolbar.tsx
import { useState } from 'react';
import { Select, Pan, Text, Image } from 'lucide-react';

type Tool = 'select' | 'pan' | 'text' | 'image';

export const CanvasToolbar = () => {
  const [activeTool, setActiveTool] = useState<Tool>('select');
  const { setTool } = useCanvasStore();

  const tools = [
    { id: 'select', icon: Select, label: '选择' },
    { id: 'pan', icon: Pan, label: '平移' },
    { id: 'text', icon: Text, label: '添加文本' },
    { id: 'image', icon: Image, label: '添加图片' },
  ] as const;

  return (
    <div className="toolbar">
      {tools.map((tool) => {
        const Icon = tool.icon;
        return (
          <button
            key={tool.id}
            onClick={() => {
              setActiveTool(tool.id);
              setTool(tool.id);
            }}
            className={activeTool === tool.id ? 'active' : ''}
          >
            <Icon />
            <span>{tool.label}</span>
          </button>
        );
      })}
    </div>
  );
};
```

### 3. AI 生成器组件

```typescript
// components/AIGenerator/AIGenerator.tsx
import { useState } from 'react';
import { useAIStore } from '@/stores/aiStore';

export const AIGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const { generateImage, isGenerating } = useAIStore();

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    const image = await generateImage(prompt);
    // 将生成的图片添加到画布
    addImageToCanvas(image);
  };

  return (
    <div className="ai-generator">
      <input
        type="text"
        placeholder="What do you want to create?"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
      />
      <button onClick={handleGenerate} disabled={isGenerating}>
        {isGenerating ? 'Generating...' : 'Generate'}
      </button>
    </div>
  );
};
```

### 4. 上下文菜单

```typescript
// components/ContextMenu/ContextMenu.tsx
import { useEffect, useRef } from 'react';
import { useElementStore } from '@/stores/elementStore';

export const ContextMenu = ({ elementId, position }: Props) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const { 
    regenerateImage, 
    generateSimilar, 
    duplicate, 
    download, 
    deleteElement 
  } = useElementStore();

  const menuItems = [
    { label: '重新生成', onClick: () => regenerateImage(elementId) },
    { label: '生成类似', onClick: () => generateSimilar(elementId) },
    { label: '复制', onClick: () => duplicate(elementId) },
    { label: '下载', onClick: () => download(elementId) },
    { label: '删除', onClick: () => deleteElement(elementId), danger: true },
  ];

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{ left: position.x, top: position.y }}
    >
      {menuItems.map((item) => (
        <button
          key={item.label}
          onClick={item.onClick}
          className={item.danger ? 'danger' : ''}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
};
```

## 🎨 UI/UX 设计参考

### Google Mixboard 设计要点

1. **简洁的工具栏**
   - 左侧垂直工具栏
   - 图标 + 文字标签
   - 激活状态明显

2. **上下文菜单**
   - Hover 显示操作菜单
   - 图标 + 文字
   - 危险操作（删除）用红色

3. **AI 输入框**
   - 底部固定位置
   - 清晰的提示文字
   - 生成按钮明显

4. **缩放控制**
   - 底部右侧
   - 百分比显示
   - 缩放按钮

5. **网格背景**
   - 浅色网格
   - 辅助对齐
   - 不干扰内容

## 📚 学习资源

### 官方文档
- [Fabric.js 文档](http://fabricjs.com/docs/)
- [Konva.js 文档](https://konvajs.org/docs/)
- [React Flow 文档](https://reactflow.dev/)

### 教程
- [Building a Canvas Editor with Fabric.js](https://www.youtube.com/watch?v=...)
- [React + Fabric.js Tutorial](https://...)

### 示例项目
- [Fabric.js Examples](http://fabricjs.com/examples/)
- [Konva.js Examples](https://konvajs.org/docs/sandbox/)

## 🚀 开发路线图

### Phase 1: 基础画布（1-2周）
- [ ] 设置 Fabric.js 画布
- [ ] 实现基础工具栏
- [ ] 添加/删除元素
- [ ] 选择和多选
- [ ] 拖拽和移动

### Phase 2: 元素操作（2-3周）
- [ ] 图片元素（上传、显示）
- [ ] 文本元素（编辑、格式化）
- [ ] 上下文菜单
- [ ] 属性面板
- [ ] 缩放、旋转

### Phase 3: AI 集成（2-3周）
- [ ] AI 生成 API 集成
- [ ] 生成图片添加到画布
- [ ] 重新生成功能
- [ ] 生成类似功能
- [ ] 加载状态

### Phase 4: 高级功能（3-4周）
- [ ] 画布序列化/反序列化
- [ ] 撤销/重做
- [ ] 图层管理
- [ ] 导出功能
- [ ] 分享功能

### Phase 5: 优化（持续）
- [ ] 性能优化
- [ ] 响应式设计
- [ ] 快捷键支持
- [ ] 协作功能（可选）

## 🔗 相关项目参考

### 开源项目
1. **Fabric.js** - 核心画布库
2. **Google Mixboard** - 设计参考
3. **Figma** - 交互设计参考
4. **Miro** - 白板设计参考

### GitHub 示例
- [fabricjs/fabric.js](https://github.com/fabricjs/fabric.js)
- [konvajs/konva](https://github.com/konvajs/konva)
- [react-konva/react-konva](https://github.com/konvajs/react-konva)

### 完整实现参考 ⭐
- **[popawan/google-mixboard-app](https://github.com/popawan/google-mixboard-app)** - Google Mixboard 的开源实现
  - 可直接查看完整代码
  - TypeScript + Vite
  - 集成 Gemini API
  - 画布编辑器实现示例

---

**推荐技术栈：**
- **画布库**: Fabric.js
- **前端框架**: React + TypeScript
- **状态管理**: Zustand
- **样式**: Tailwind CSS
- **UI 组件**: shadcn/ui

**预计开发时间**: 8-12 周（MVP）

