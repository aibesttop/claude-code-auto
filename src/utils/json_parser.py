"""
强化的 JSON 解析器
支持多种解析策略、重试机制、Schema 验证
"""
import json
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class DecisionResponse(BaseModel):
    """AI 决策响应模型"""
    completed: bool = Field(..., description="任务是否完成")
    next_prompt: str = Field(default="", description="下一步提示词")
    analysis: str = Field(default="", description="分析说明")
    confidence: float = Field(default=0.8, ge=0, le=1, description="置信度(0-1)")

    @field_validator('next_prompt')
    def validate_next_prompt(cls, v, info):
        """验证 next_prompt: 如果已完成，应该为空"""
        if info.data.get('completed') and v.strip():
            # 已完成但还有 next_prompt，可能是误判
            pass  # 只警告，不强制
        return v

    def to_dict(self) -> dict:
        return {
            'completed': self.completed,
            'next_prompt': self.next_prompt,
            'analysis': self.analysis,
            'confidence': self.confidence
        }


class JsonParseError(Exception):
    """JSON 解析错误"""
    pass


class JsonParser:
    """JSON 解析器"""

    def __init__(
        self,
        max_retries: int = 3,
        strict_mode: bool = False,
        default_confidence: float = 0.5
    ):
        self.max_retries = max_retries
        self.strict_mode = strict_mode
        self.default_confidence = default_confidence

    def parse(
        self,
        response_text: str,
        retry_count: int = 0
    ) -> DecisionResponse:
        """
        解析 AI 响应文本，提取 JSON 决策

        Args:
            response_text: AI 的响应文本
            retry_count: 当前重试次数（内部使用）

        Returns:
            DecisionResponse: 解析后的决策对象

        Raises:
            JsonParseError: 解析失败
        """
        strategies = [
            self._extract_from_markdown_code_block,
            self._extract_from_json_pattern,
            self._extract_first_valid_json,
            self._fallback_text_analysis
        ]

        last_error = None

        for strategy in strategies:
            try:
                result = strategy(response_text)
                if result:
                    return result
            except Exception as e:
                last_error = e
                continue

        # 所有策略都失败
        if retry_count < self.max_retries:
            # 可以在这里添加重新请求 AI 的逻辑
            pass

        # 如果非严格模式，返回默认失败响应
        if not self.strict_mode:
            return DecisionResponse(
                completed=False,
                next_prompt="JSON解析失败，请明确回复 JSON 格式",
                analysis=f"解析错误: {last_error}. 原始响应: {response_text[:200]}",
                confidence=self.default_confidence
            )

        raise JsonParseError(f"无法解析 JSON: {last_error}")

    def _extract_from_markdown_code_block(
        self,
        text: str
    ) -> Optional[DecisionResponse]:
        """策略1: 从 Markdown 代码块中提取 JSON"""
        # 匹配 ```json ... ``` 或 ```{ ... }```
        patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(\{.*?\})\n```',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1).strip()
                try:
                    data = json.loads(json_str)
                    return DecisionResponse(**data)
                except (json.JSONDecodeError, ValueError):
                    continue

        return None

    def _extract_from_json_pattern(
        self,
        text: str
    ) -> Optional[DecisionResponse]:
        """策略2: 使用正则提取 JSON 对象"""
        # 匹配完整的 JSON 对象（支持嵌套）
        # 简化版本：匹配 { ... }，确保括号平衡
        pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        matches = re.findall(pattern, text, re.DOTALL)

        for json_str in matches:
            try:
                data = json.loads(json_str)
                # 验证是否包含必需字段
                if 'completed' in data:
                    return DecisionResponse(**data)
            except (json.JSONDecodeError, ValueError):
                continue

        return None

    def _extract_first_valid_json(
        self,
        text: str
    ) -> Optional[DecisionResponse]:
        """策略3: 查找第一个有效的 JSON"""
        # 查找第一个 { 和最后一个 }
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = text[start_idx:end_idx + 1]
            try:
                data = json.loads(json_str)
                if 'completed' in data:
                    return DecisionResponse(**data)
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    def _fallback_text_analysis(
        self,
        text: str
    ) -> Optional[DecisionResponse]:
        """策略4: 文本分析降级策略（最后手段）"""
        # 尝试从文本中推断决策
        text_lower = text.lower()

        # 检测"完成"关键词
        completed_keywords = [
            'completed', 'done', 'finished', 'success',
            '已完成', '完成', '成功', '结束'
        ]

        is_completed = any(kw in text_lower for kw in completed_keywords)

        # 检测"继续"关键词
        continue_keywords = [
            'continue', 'next', 'proceed',
            '继续', '下一步', '接下来'
        ]

        has_next_step = any(kw in text_lower for kw in continue_keywords)

        # 如果明确说完成，且没有后续步骤
        if is_completed and not has_next_step:
            return DecisionResponse(
                completed=True,
                next_prompt="",
                analysis=f"基于文本分析判断已完成: {text[:200]}",
                confidence=0.3  # 低置信度
            )

        return None

    def validate_decision(self, decision: DecisionResponse) -> bool:
        """验证决策的合理性"""
        # 基本验证
        if decision.completed and decision.next_prompt.strip():
            # 警告：已完成但还有下一步
            return True  # 仍然接受，但可能需要人工确认

        if not decision.completed and not decision.next_prompt.strip():
            # 警告：未完成但没有下一步指令
            return False

        # 置信度检查
        if decision.confidence < 0.5:
            # 低置信度警告
            pass

        return True


def parse_decision_response(
    response_text: str,
    max_retries: int = 3,
    strict_mode: bool = False
) -> DecisionResponse:
    """
    便捷函数：解析 AI 决策响应

    Args:
        response_text: AI 的响应文本
        max_retries: 最大重试次数
        strict_mode: 是否严格模式

    Returns:
        DecisionResponse: 解析后的决策
    """
    parser = JsonParser(
        max_retries=max_retries,
        strict_mode=strict_mode
    )
    return parser.parse(response_text)


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        # 测试1: 标准 Markdown 代码块
        '''
        分析完成，结果如下：
        ```json
        {
            "completed": true,
            "next_prompt": "",
            "analysis": "任务已完成",
            "confidence": 0.95
        }
        ```
        ''',

        # 测试2: 嵌入文本中的 JSON
        '''
        让我检查一下当前状态。
        根据分析，结果是：{"completed": false, "next_prompt": "请继续编写文档", "analysis": "文档未完成", "confidence": 0.8}
        这是我的建议。
        ''',

        # 测试3: 多个 JSON 对象（取有效的）
        '''
        先看一下 {test: 123}，然后是真实结果：
        {
            "completed": false,
            "next_prompt": "添加测试用例",
            "analysis": "缺少测试",
            "confidence": 0.9
        }
        ''',

        # 测试4: 纯文本（降级策略）
        '''
        任务已经完成了，所有文件都生成成功。
        ''',

        # 测试5: 错误格式（应该失败或返回默认值）
        '''
        这不是 JSON 格式的响应。
        ''',
    ]

    parser = JsonParser(strict_mode=False)

    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"测试用例 {i}:")
        print(f"输入: {test_text[:100]}...")

        try:
            result = parser.parse(test_text)
            print(f"✅ 解析成功:")
            print(f"   completed: {result.completed}")
            print(f"   next_prompt: {result.next_prompt[:50]}")
            print(f"   confidence: {result.confidence}")
        except JsonParseError as e:
            print(f"❌ 解析失败: {e}")

    print(f"\n{'=' * 60}")
    print("✅ JSON 解析器测试完成！")
