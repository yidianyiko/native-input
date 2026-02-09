"""
Pydantic模型定义
用于Agno的结构化输出（可选功能）
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class TranslationResult(BaseModel):
    """翻译结果模型"""
    translated_text: str = Field(description="翻译结果")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1, default=0.9)
    detected_language: str = Field(description="检测到的源语言", default="auto")
    alternatives: List[str] = Field(description="备选翻译", default=[])


class PolishResult(BaseModel):
    """润色结果模型"""
    polished_text: str = Field(description="润色后的文本")
    improvements: List[str] = Field(description="改进点", default=[])
    confidence: float = Field(description="改进质量评分", ge=0, le=1, default=0.9)


class CorrectionResult(BaseModel):
    """纠错结果模型"""
    corrected_text: str = Field(description="纠错后的文本")
    errors_found: List[dict] = Field(description="发现的错误", default=[])
    confidence: float = Field(description="纠错准确度", ge=0, le=1, default=0.9)


class AgentResponse(BaseModel):
    """通用Agent响应模型"""
    content: str = Field(description="处理后的内容")
    agent_name: str = Field(description="处理的Agent名称")
    processing_time: float = Field(description="处理时间（秒）", default=0.0)
    success: bool = Field(description="处理是否成功", default=True)
    error_message: Optional[str] = Field(description="错误信息", default=None)