"""LangGraph Agent: analyze → plan → generate_steps → assemble → output"""
import os
import json
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# ── State ──────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    task_id: str
    prompt: str
    analysis: str        # 题目分析 JSON
    plan: str            # 动画方案 JSON (含 steps 数组)
    step_htmls: list     # 每个步骤生成的 HTML 片段
    final_html: str      # 组装后的完整 HTML


# ── LLM Configuration ──────────────────────────────────────────────────
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# Image generation API (optional)
IMAGE_API_BASE = os.environ.get("IMAGE_API_BASE", "")  # e.g. https://api.openai.com/v1
IMAGE_API_KEY = os.environ.get("IMAGE_API_KEY", "")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")


def get_llm(temperature=0.7, max_tokens=4000):
    return ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ── Helper ─────────────────────────────────────────────────────────────
def extract_json(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def safe_parse_json(text: str) -> dict:
    """Parse JSON with fallback for common LLM output issues (e.g. unescaped LaTeX backslashes)."""
    extracted = extract_json(text)
    # Try direct parse first
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass
    # Fix unescaped backslashes in string values (LaTeX like \frac, \sqrt, etc.)
    # Replace backslashes that are NOT followed by valid JSON escape chars
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', extracted)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    # Last resort: try to fix truncated/incomplete JSON by closing open brackets
    # Track bracket depth and find the longest valid prefix
    depth = 0
    in_string = False
    escape = False
    last_complete = 0
    openers = []
    for i, c in enumerate(extracted):
        if escape:
            escape = False
            continue
        if c == '\\' and in_string:
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c in '{[':
            depth += 1
            openers.append(c)
        elif c == '}' and openers and openers[-1] == '{':
            depth -= 1
            openers.pop()
            if depth == 0:
                last_complete = i + 1
        elif c == ']' and openers and openers[-1] == '[':
            depth -= 1
            openers.pop()
            if depth == 0:
                last_complete = i + 1
    # If we found a complete top-level structure, try truncating to it
    if last_complete > 0:
        try:
            return json.loads(extracted[:last_complete])
        except json.JSONDecodeError:
            pass
    # If JSON is truncated mid-way, try closing all open brackets
    if openers:
        closers = ''.join('}' if o == '{' else ']' for o in reversed(openers))
        # Strip trailing incomplete content (e.g. partial key/value after last complete item)
        trimmed = extracted.rstrip()
        # Remove trailing partial object in array: find last complete }, and cut after it
        last_brace = trimmed.rfind('},')
        if last_brace > 0:
            trimmed = trimmed[:last_brace + 1]
        # Remove trailing comma
        trimmed = re.sub(r',\s*$', '', trimmed)
        attempt = trimmed + closers
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("Failed to parse JSON", extracted, 0)


def extract_svg_fragment(text: str) -> str:
    """提取 SVG + HTML 片段（不需要完整 HTML）"""
    # 提取 ```html ... ``` 块
    match = re.search(r"```html\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 提取 ```svg ... ``` 块
    match = re.search(r"```svg\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 如果包含 <svg 或 <div 标签，直接返回
    if "<svg" in text or "<div" in text:
        return text.strip()
    return text.strip()


# ── Node 1: Analyze ────────────────────────────────────────────────────
ANALYZE_PROMPT = """分析数学题目，输出JSON。

题目：{prompt}

输出：
{{"topic":"geometry/algebra/arithmetic/function","knowledge_points":["知识点"],"difficulty":1-5,"summary":"一句话概括"}}"""


def analyze_node(state: AgentState) -> dict:
    print(f"--- Node: Analyze (Prompt: {state['prompt'][:20]}...) ---")

    llm = get_llm(temperature=0.3, max_tokens=32000)
    resp = llm.invoke([
        SystemMessage(content="只输出JSON。"),
        HumanMessage(content=ANALYZE_PROMPT.format(prompt=state["prompt"])),
    ])
    # MiMo reasoning model may return empty content; retry once with explicit instruction
    content = resp.content.strip()
    if not content:
        resp = llm.invoke([
            SystemMessage(content="直接输出JSON结果，不要思考过程。"),
            HumanMessage(content=ANALYZE_PROMPT.format(prompt=state["prompt"])),
        ])
        content = resp.content.strip()

    print(f"   Analysis result: {resp.content[:50]}...")
    return {"analysis": content}


# ── Node 2: Plan ───────────────────────────────────────────────────────
PLAN_PROMPT = """设计教学动画方案，输出JSON。

题目：{prompt}
分析：{analysis}

要求：按照难度生成2-5个步骤，每步描述如何用SVG展示。

输出：
{{
  "title": "动画标题",
  "main_tag": "从以下选一个：模型意识/数据意识/空间观念/几何直观/符号意识/量感/数感/推理意识/运算能力",
  "sub_tags": ["从上面选2个"],
  "steps": [
    {{
      "title": "步骤标题",
      "text": "数学解释（可用$包裹LaTeX）",
      "bubble": "口语化解释",
      "visual": "这一步SVG画什么"
    }}
  ]
}}"""


def plan_node(state: AgentState) -> dict:
    print(f"--- Node: Plan ---")

    llm = get_llm(temperature=0.5, max_tokens=32000)
    resp = llm.invoke([
        SystemMessage(content="只输出JSON。"),
        HumanMessage(content=PLAN_PROMPT.format(
            prompt=state["prompt"],
            analysis=state["analysis"],
        )),
    ])
    print(f"   plan result: {resp.content}...")
    return {"plan": resp.content}


# ── Node 3: Generate Steps (逐个生成) ──────────────────────────────────
STEP_PROMPT = """为教学动画的第{step_index}步生成HTML片段。

题目：{prompt}
步骤信息：
- 标题：{step_title}
- 数学内容：{step_text}
- 气泡文字：{step_bubble}
- 图形要求：{step_visual}

要求：
- 只输出这一步的HTML片段（不需要完整HTML页面）
- 用 <div x-show="currentStep === {step_index}"> 包裹
- SVG图形简洁（rect/circle/polygon/path/text），坐标在viewBox="0 0 600 400"范围内
- 数学公式用 <span x-html="katex.renderToString('公式', {{throwOnError:false}})"> 展示
- 右侧气泡框用 <div class="bubble"> 展示口语化解释
- 代码精简，不要多余装饰

输出格式：
```html
<div x-show="currentStep === {step_index}" class="step-panel">
  <div class="step-svg">
    <svg viewBox="0 0 600 400">...</svg>
  </div>
  <div class="step-info">
    <h3>{step_title}</h3>
    <div class="step-text">数学内容</div>
    <div class="bubble">气泡文字</div>
  </div>
</div>
```"""


def generate_steps_node(state: AgentState) -> dict:
    """逐个步骤调用LLM生成HTML片段"""
    print(f"--- Node: Generate Steps ---")

    llm = get_llm(temperature=0.7, max_tokens=32000)
    try:
        plan_data = safe_parse_json(state["plan"])
        steps = plan_data.get("steps", [])
    except (json.JSONDecodeError, KeyError):
        steps = []
    
    if not steps:
        print("  [WARNING] No steps found in plan! Check plan LLM output.", flush=True)
        return {"step_htmls": []}
    print(f"  Found {len(steps)} steps in plan. Start generating HTML...", flush=True)
    step_htmls = []
    for i, step in enumerate(steps):
        resp = llm.invoke([
            SystemMessage(content="你是前端开发专家。只输出HTML片段代码，不要其他内容。"),
            HumanMessage(content=STEP_PROMPT.format(
                prompt=state["prompt"],
                step_index=i,
                step_title=step.get("title", f"步骤{i+1}"),
                step_text=step.get("text", ""),
                step_bubble=step.get("bubble", ""),
                step_visual=step.get("visual", "展示数学图形"),
            )),
        ])
        if not resp.content:
            print("该步骤生成的content为空")
        print(f"  [generate]  step content {i}: {resp.content}...")
        fragment = extract_svg_fragment(resp.content)
        step_htmls.append(fragment)
        print(f"  [generate] Step {i+1}/{len(steps)} done ({len(fragment)} chars)")

    print(f"   Generated {len(step_htmls)} steps.", flush=True)
    return {"step_htmls": step_htmls}


# ── Node 4: Assemble (模板组装) ────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
<style>
body {{ font-family: 'Songti SC','SimSun',serif; background:#fdfbf7; margin:0; }}
.step-panel {{ display:flex; gap:24px; padding:20px; min-height:400px; }}
.step-svg {{ flex:1; }}
.step-svg svg {{ width:100%; height:100%; max-height:400px; }}
.step-info {{ width:320px; display:flex; flex-direction:column; gap:12px; }}
.step-info h3 {{ font-size:1.2rem; font-weight:700; color:#2B2B2B; margin:0; }}
.step-text {{ font-size:0.95rem; color:#5A6A76; line-height:1.6; }}
.bubble {{ background:rgba(255,255,255,0.85); border:1px solid #E0DCD3; border-radius:12px;
           padding:14px; font-size:0.9rem; color:#5A6A76; line-height:1.6;
           position:relative; }}
.bubble::before {{ content:''; position:absolute; left:16px; top:-8px;
                   border-left:8px solid transparent; border-right:8px solid transparent;
                   border-bottom:8px solid rgba(255,255,255,0.85); }}
.nav {{ display:flex; justify-content:center; gap:12px; padding:16px; }}
.nav button {{ padding:8px 24px; border:1px solid #E0DCD3; border-radius:8px; background:#fff;
               cursor:pointer; font-size:0.9rem; color:#2B2B2B; transition:all 0.2s; }}
.nav button:hover {{ background:#3E5C76; color:#fff; border-color:#3E5C76; }}
.nav button:disabled {{ opacity:0.4; cursor:not-allowed; }}
.nav button:disabled:hover {{ background:#fff; color:#2B2B2B; border-color:#E0DCD3; }}
.dots {{ display:flex; gap:8px; align-items:center; }}
.dot {{ width:10px; height:10px; border-radius:50%; background:#E0DCD3; cursor:pointer; transition:all 0.2s; }}
.dot.active {{ background:#3E5C76; transform:scale(1.2); }}
header {{ text-align:center; padding:20px; border-bottom:1px solid #E0DCD3; }}
header h1 {{ font-size:1.5rem; color:#2B2B2B; margin:0; }}
</style>
</head>
<body x-data="mathApp()">

<header>
  <h1>{title}</h1>
</header>

<div style="max-width:1000px;margin:0 auto;position:relative;min-height:400px;">
{step_htmls}
</div>

<div class="nav">
  <button @click="prevStep()" :disabled="currentStep===0">‹ 上一步</button>
  <div class="dots">
    <template x-for="(s,i) in steps" :key="i">
      <div class="dot" :class="currentStep===i && 'active'" @click="currentStep=i"></div>
    </template>
  </div>
  <button @click="nextStep()" :disabled="currentStep===steps.length-1">下一步 ›</button>
</div>

<script>
function mathApp() {{
  return {{
    currentStep: 0,
    steps: {steps_json},
    nextStep() {{ if(this.currentStep<this.steps.length-1) this.currentStep++ }},
    prevStep() {{ if(this.currentStep>0) this.currentStep-- }}
  }};
}}
</script>
</body>
</html>"""


def assemble_node(state: AgentState) -> dict:
    """将各个步骤片段组装成完整HTML"""
    try:
        plan_data = safe_parse_json(state["plan"])
        title = plan_data.get("title", state["prompt"])
        steps = plan_data.get("steps", [])
    except (json.JSONDecodeError, KeyError):
        title = state["prompt"]
        steps = []
    
    step_htmls = state.get("step_htmls", [])
    
    # 合并所有步骤 HTML
    combined_steps = "\n".join(step_htmls)
    
    # 构建 steps JSON（供 Alpine.js 使用）
    steps_data = []
    for i, step in enumerate(steps):
        steps_data.append({
            "title": step.get("title", f"步骤{i+1}"),
            "text": step.get("text", ""),
            "bubble": step.get("bubble", ""),
        })
    
    final_html = HTML_TEMPLATE.format(
        title=title,
        step_htmls=combined_steps,
        steps_json=json.dumps(steps_data, ensure_ascii=False),
    )
    print(f"   Assembled final HTML with {len(step_htmls)} step panels. Total length: {len(final_html)}", flush=True)
    return {"final_html": final_html}


# ── Node 5: Generate Preview ───────────────────────────────────────────
def generate_preview_node(state: AgentState) -> dict:
    """生成封面：优先用图像生成API，否则让LLM生成SVG"""
    prompt = state["prompt"]
    task_id = state["task_id"]

    try:
        plan_data = safe_parse_json(state["plan"])
        title = plan_data.get("title", prompt)
    except (json.JSONDecodeError, KeyError):
        title = prompt

    preview_content = ""
    preview_type = "svg"

    # 方案 A：图像生成 API
    if IMAGE_API_BASE and IMAGE_API_KEY:
        try:
            preview_content = generate_image_preview(title, prompt)
            preview_type = "webp"
            print(f"  [preview] Generated image via API ({len(preview_content)} bytes)")
        except Exception as e:
            print(f"  [preview] Image API failed: {e}, falling back to SVG")
            preview_content = ""

    # 方案 B：LLM 生成 SVG
    if not preview_content:
        preview_content = generate_svg_preview(title, prompt, state)
        preview_type = "svg"
        print(f"  [preview] Generated SVG via LLM ({len(preview_content)} chars)")

    # 保存预览文件
    from backend.storage import storage
    storage.save_preview(task_id, preview_content, preview_type)

    return {}


def generate_image_preview(title: str, prompt: str) -> bytes:
    """调用图像生成 API，返回图片二进制"""
    import requests as req
    import base64

    img_prompt = (
        f"中国传统水墨画风格，数学教学封面。"
        f"主题：{title}。"
        f"画面包含：水墨山水背景、数学公式或几何图形、"
        f"梅花/竹子/算盘等传统元素点缀。"
        f"风格：古雅、简洁、适合教育场景。"
    )

    resp = req.post(
        f"{IMAGE_API_BASE}/images/generations",
        headers={"Authorization": f"Bearer {IMAGE_API_KEY}"},
        json={
            "model": IMAGE_MODEL,
            "prompt": img_prompt,
            "n": 1,
            "size": "512x512",
            "response_format": "b64_json",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    img_b64 = data["data"][0]["b64_json"]
    return base64.b64decode(img_b64)


def generate_svg_preview(title: str, prompt: str, state: AgentState) -> str:
    """让 LLM 生成一个简洁的封面 SVG"""
    try:
        llm = get_llm(temperature=0.7, max_tokens=32000)

        svg_prompt = f"""为数学教学动画生成一个简洁的封面SVG。

题目：{title}
原始问题：{prompt}

要求：
- viewBox="0 0 400 300"
- 古风水墨色调：背景#F7F5F0，主色#3E5C76（黛蓝），点缀#B83B43（朱砂）
- 包含与题目相关的简洁数学图形（如三角形、函数曲线、算式等）
- 可加少量装饰元素（山水轮廓、梅花枝等）
- 代码精简，SVG元素不超过20个
- 只输出<svg>...</svg>，不要其他内容"""

        resp = llm.invoke([
            SystemMessage(content="只输出SVG代码。"),
            HumanMessage(content=svg_prompt),
        ])

        content = resp.content.strip()
        if not content:
            print("  [preview] LLM returned empty content, using fallback", flush=True)
            return _fallback_svg(title)

        # 提取 SVG
        match = re.search(r"(<svg[^>]*>.*?</svg>)", content, re.DOTALL)
        if match:
            return match.group(1)
        return content
    except Exception as e:
        print(f"  [preview] LLM error: {e}, using fallback", flush=True)
        return _fallback_svg(title)


def _fallback_svg(title: str) -> str:
    """默认封面 SVG"""
    safe_title = title[:20].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
  <rect width="400" height="300" fill="#F7F5F0" rx="8"/>
  <circle cx="200" cy="120" r="60" fill="none" stroke="#3E5C76" stroke-width="2" opacity="0.3"/>
  <line x1="160" y1="120" x2="240" y2="120" stroke="#3E5C76" stroke-width="1.5" opacity="0.5"/>
  <line x1="200" y1="80" x2="200" y2="160" stroke="#3E5C76" stroke-width="1.5" opacity="0.5"/>
  <text x="200" y="200" text-anchor="middle" fill="#3E5C76" font-size="16" font-family="serif">{safe_title}</text>
  <text x="200" y="230" text-anchor="middle" fill="#B83B43" font-size="12" font-family="serif">象数演易</text>
</svg>'''


# ── Node 6: Output ─────────────────────────────────────────────────────
def output_node(state: AgentState) -> dict:
    html = state.get("final_html", "")
    if not html or "</html>" not in html:
        html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>生成失败</title>
<style>body{{display:flex;align-items:center;justify-content:center;height:100vh;background:#fdfbf7;}}
.box{{text-align:center;padding:40px;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);}}
h1{{color:#B83B43;}}</style></head>
<body><div class="box"><h1>⚠️ 生成失败</h1><p>{state.get("prompt","")}</p></div></body></html>"""
    return {"final_html": html}


# ── Build Graph ────────────────────────────────────────────────────────
def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("analyze", analyze_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("generate_steps", generate_steps_node)
    workflow.add_node("assemble", assemble_node)
    workflow.add_node("generate_preview", generate_preview_node)
    workflow.add_node("output", output_node)

    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", "generate_steps")
    workflow.add_edge("generate_steps", "assemble")
    workflow.add_edge("assemble", "generate_preview")
    workflow.add_edge("generate_preview", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


# ── Run Agent ──────────────────────────────────────────────────────────
async def run_agent(task_id: str, prompt: str, callback=None):
    agent = build_agent()

    initial_state: AgentState = {
        "task_id": task_id,
        "prompt": prompt,
        "analysis": "",
        "plan": "",
        "step_htmls": [],
        "final_html": "",
    }

    result = None
    async for event in agent.astream(initial_state):
        for node_name, output in event.items():
            if callback:
                callback(node_name)
            if output and isinstance(output, dict):
                result = {**(result or {}), **output}

    # 从 plan 中提取标题和标签
    title = prompt[:30]
    tags = {"main_tag": "运算能力", "sub_tags": ["推理意识"]}
    try:
        plan_data = json.loads(extract_json(result.get("plan", "")))
        title = plan_data.get("title", title)
        tags = {
            "main_tag": plan_data.get("main_tag", "运算能力"),
            "sub_tags": plan_data.get("sub_tags", ["推理意识"]),
        }
    except (json.JSONDecodeError, KeyError):
        pass

    return {
        "html": result.get("final_html", ""),
        "title": title,
        "tags": tags,
    }

