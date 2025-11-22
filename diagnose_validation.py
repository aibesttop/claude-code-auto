"""
Validation Diagnostic Tool

帮助诊断为什么验证失败
"""

import re
from pathlib import Path


def diagnose_file(file_path: str, required_sections: list):
    """诊断文件验证问题"""
    
    print("=" * 70)
    print(f"🔍 诊断文件: {file_path}")
    print("=" * 70)
    
    path = Path(file_path)
    
    # 1. 检查文件是否存在
    if not path.exists():
        print(f"\n❌ 文件不存在: {file_path}")
        print(f"   当前工作目录: {Path.cwd()}")
        print(f"   绝对路径: {path.absolute()}")
        
        # 尝试查找文件
        parent = path.parent
        if parent.exists():
            print(f"\n📁 父目录存在，内容:")
            for item in parent.iterdir():
                print(f"   - {item.name}")
        return
    
    print(f"✅ 文件存在\n")
    
    # 2. 读取文件内容
    try:
        content = path.read_text(encoding='utf-8')
        print(f"📊 文件大小: {len(content)} 字符")
        print(f"📊 文件行数: {len(content.splitlines())} 行\n")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 3. 提取所有headers
    all_headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    
    print(f"📝 找到 {len(all_headers)} 个headers:\n")
    for level, title in all_headers[:20]:  # 最多显示20个
        print(f"   {level} {title}")
    
    if len(all_headers) > 20:
        print(f"   ... (还有 {len(all_headers) - 20} 个)")
    
    print("\n" + "-" * 70)
    
    # 4. 检查每个required section
    print(f"\n🎯 验证Required Sections:\n")
    
    for required in required_sections:
        print(f"Required: '{required}'")
        
        # Method 1: 精确匹配
        if required in content:
            print(f"   ✅ Method 1 (精确匹配): Found")
            continue
        
        # Method 2: 灵活空格
        pattern = re.escape(required)
        pattern = pattern.replace(r'\ ', r'\s*')
        
        if re.search(pattern, content, re.MULTILINE):
            print(f"   ✅ Method 2 (灵活空格): Found with pattern {pattern}")
            continue
        
        # Method 3: 归一化
        normalized_required = ' '.join(required.split())
        normalized_content = ' '.join(content.split())
        
        if normalized_required in normalized_content:
            print(f"   ✅ Method 3 (归一化): Found")
            continue
        
        # 未找到 - 提供建议
        print(f"   ❌ NOT FOUND")
        
        # 查找相似的headers
        print(f"   💡 相似的headers:")
        for level, title in all_headers:
            if required.lower().replace('#', '').strip() in title.lower():
                print(f"      - {level} {title}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 配置
    work_dir = "demo_act"
    file_name = "market-research.md"
    file_path = f"{work_dir}/{file_name}"
    
    required_sections = [
        "## Executive Summary",
        "## Target Users",
        "## Competitor Analysis",
        "## Market Size",
        "## User Pain Points",
        "## Opportunities"
    ]
    
    diagnose_file(file_path, required_sections)
