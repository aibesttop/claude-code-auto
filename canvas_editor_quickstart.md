# 画布式编辑器快速开始

## 🚀 5分钟快速搭建

### 1. 安装依赖

```bash
# 创建项目
npx create-next-app@latest canvas-editor --typescript --tailwind --app

cd canvas-editor

# 安装核心依赖
npm install fabric
npm install zustand
npm install lucide-react

# 安装 UI 组件（可选）
npx shadcn-ui@latest init
```

### 2. 基础画布组件

创建 `components/Canvas.tsx`:

```typescript
'use client';

import { useEffect, useRef } from 'react';
import { fabric } from 'fabric';

export default function Canvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvasRef = useRef<fabric.Canvas | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    // 初始化画布
    const canvas = new fabric.Canvas(canvasRef.current, {
      width: 1200,
      height: 800,
      backgroundColor: '#f5f5f5',
    });

    fabricCanvasRef.current = canvas;

    // 添加示例文本
    const text = new fabric.Text('Hello Canvas!', {
      left: 100,
      top: 100,
      fontSize: 40,
      fill: '#333',
    });
    canvas.add(text);

    return () => {
      canvas.dispose();
    };
  }, []);

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gray-100">
      <canvas ref={canvasRef} className="border border-gray-300 shadow-lg" />
    </div>
  );
}
```

### 3. 使用组件

在 `app/page.tsx`:

```typescript
import Canvas from '@/components/Canvas';

export default function Home() {
  return (
    <main>
      <Canvas />
    </main>
  );
}
```

### 4. 运行项目

```bash
npm run dev
```

访问 http://localhost:3000 即可看到画布！

## 📦 完整示例：带工具栏的画布

### 创建工具栏组件

`components/Toolbar.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { MousePointer2, Hand, Type, Image as ImageIcon } from 'lucide-react';

type Tool = 'select' | 'pan' | 'text' | 'image';

export default function Toolbar({ onToolChange }: { onToolChange: (tool: Tool) => void }) {
  const [activeTool, setActiveTool] = useState<Tool>('select');

  const tools: { id: Tool; icon: any; label: string }[] = [
    { id: 'select', icon: MousePointer2, label: '选择' },
    { id: 'pan', icon: Hand, label: '平移' },
    { id: 'text', icon: Type, label: '文本' },
    { id: 'image', icon: ImageIcon, label: '图片' },
  ];

  const handleToolClick = (tool: Tool) => {
    setActiveTool(tool);
    onToolChange(tool);
  };

  return (
    <div className="fixed left-4 top-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg p-2 flex flex-col gap-2">
      {tools.map((tool) => {
        const Icon = tool.icon;
        return (
          <button
            key={tool.id}
            onClick={() => handleToolClick(tool.id)}
            className={`p-3 rounded-lg transition-colors ${
              activeTool === tool.id
                ? 'bg-blue-500 text-white'
                : 'hover:bg-gray-100 text-gray-700'
            }`}
            title={tool.label}
          >
            <Icon size={20} />
          </button>
        );
      })}
    </div>
  );
}
```

### 创建 AI 生成器组件

`components/AIGenerator.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { Sparkles } from 'lucide-react';

export default function AIGenerator({ onGenerate }: { onGenerate: (prompt: string) => void }) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onGenerate(prompt);
      setPrompt('');
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What do you want to create?"
          className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Sparkles size={20} />
          Generate
        </button>
      </form>
    </div>
  );
}
```

### 更新 Canvas 组件

```typescript
'use client';

import { useEffect, useRef, useState } from 'react';
import { fabric } from 'fabric';
import Toolbar from './Toolbar';
import AIGenerator from './AIGenerator';

export default function Canvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvasRef = useRef<fabric.Canvas | null>(null);
  const [currentTool, setCurrentTool] = useState<'select' | 'pan' | 'text' | 'image'>('select');

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = new fabric.Canvas(canvasRef.current, {
      width: window.innerWidth,
      height: window.innerHeight,
      backgroundColor: '#f5f5f5',
    });

    fabricCanvasRef.current = canvas;

    // 根据工具切换模式
    if (currentTool === 'pan') {
      canvas.isDragging = true;
      canvas.selection = false;
    } else {
      canvas.isDragging = false;
      canvas.selection = true;
    }

    return () => {
      canvas.dispose();
    };
  }, [currentTool]);

  const handleGenerate = async (prompt: string) => {
    // 这里调用 AI API 生成图片
    // 示例：使用占位图片
    const imageUrl = `https://via.placeholder.com/400x300?text=${encodeURIComponent(prompt)}`;
    
    fabric.Image.fromURL(imageUrl, (img) => {
      img.set({
        left: Math.random() * 500,
        top: Math.random() * 500,
        scaleX: 0.5,
        scaleY: 0.5,
      });
      fabricCanvasRef.current?.add(img);
    });
  };

  return (
    <div className="relative w-full h-screen">
      <canvas ref={canvasRef} />
      <Toolbar onToolChange={setCurrentTool} />
      <AIGenerator onGenerate={handleGenerate} />
    </div>
  );
}
```

## 🎨 添加网格背景

```typescript
// 在 Canvas 组件中添加
useEffect(() => {
  if (!fabricCanvasRef.current) return;

  // 创建网格图案
  const gridSize = 20;
  const canvas = document.createElement('canvas');
  canvas.width = gridSize;
  canvas.height = gridSize;
  const ctx = canvas.getContext('2d');
  
  if (ctx) {
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, gridSize);
    ctx.lineTo(gridSize, gridSize);
    ctx.moveTo(gridSize, 0);
    ctx.lineTo(gridSize, gridSize);
    ctx.stroke();
  }

  fabricCanvasRef.current.setBackgroundColor({
    source: canvas.toDataURL(),
    repeat: 'repeat',
  }, () => {
    fabricCanvasRef.current?.renderAll();
  });
}, []);
```

## 🔧 添加元素操作菜单

`components/ContextMenu.tsx`:

```typescript
'use client';

import { useEffect, useRef } from 'react';
import { RefreshCw, Copy, Download, Trash2 } from 'lucide-react';

interface ContextMenuProps {
  x: number;
  y: number;
  onClose: () => void;
  onRegenerate?: () => void;
  onDuplicate?: () => void;
  onDownload?: () => void;
  onDelete?: () => void;
}

export default function ContextMenu({
  x,
  y,
  onClose,
  onRegenerate,
  onDuplicate,
  onDownload,
  onDelete,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const menuItems = [
    { icon: RefreshCw, label: '重新生成', onClick: onRegenerate },
    { icon: Copy, label: '复制', onClick: onDuplicate },
    { icon: Download, label: '下载', onClick: onDownload },
    { icon: Trash2, label: '删除', onClick: onDelete, danger: true },
  ].filter(item => item.onClick);

  return (
    <div
      ref={menuRef}
      className="fixed bg-white rounded-lg shadow-lg py-2 min-w-[150px] z-50"
      style={{ left: x, top: y }}
    >
      {menuItems.map((item, index) => {
        const Icon = item.icon;
        return (
          <button
            key={index}
            onClick={() => {
              item.onClick?.();
              onClose();
            }}
            className={`w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 ${
              item.danger ? 'text-red-600' : 'text-gray-700'
            }`}
          >
            <Icon size={16} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
```

## 📚 下一步

1. **集成真实的 AI API**（OpenAI、Stable Diffusion 等）
2. **添加文本编辑功能**（颜色、字体、大小）
3. **实现撤销/重做**
4. **添加画布序列化**（保存/加载）
5. **优化性能**（大量元素时）

查看完整开发指南：`canvas_editor_development_guide.md`

