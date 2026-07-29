"""Pydantic models for the teaching animation agent."""
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class MathTopic(str, Enum):
    GEOMETRY = "geometry"
    ALGEBRA = "algebra"
    ARITHMETIC = "arithmetic"
    FUNCTION = "function"
    STATISTICS = "statistics"
    OTHER = "other"


class AnalysisResult(BaseModel):
    """Step 1 output: 题目分析"""
    topic: MathTopic
    knowledge_points: list[str]
    difficulty: int  # 1-5
    question_type: str  # e.g. "证明题", "计算题"
    summary: str  # 一句话概括题目


class AnimationPlan(BaseModel):
    """Step 2 output: 动画方案"""
    title: str
    description: str
    steps: list[dict]  # [{title, text, bubble, svg_hint}]
    visual_style: str  # e.g. "几何图形", "函数曲线", "数字运算"
    interaction_type: str  # e.g. "step-by-step", "drag", "input"


class ReviewResult(BaseModel):
    """Step 4 output: 代码审查"""
    passed: bool
    issues: list[str]  # 发现的问题
    suggestions: list[str]  # 改进建议
    score: int  # 0-100


class TaskCreate(BaseModel):
    prompt: str


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = 0
    title: Optional[str] = None
    message: Optional[str] = None
