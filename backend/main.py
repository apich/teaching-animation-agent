"""FastAPI application - Teaching Animation Generator"""
import sys
import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 确保项目根目录在 sys.path 中（支持直接运行 main.py）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load .env
load_dotenv(os.path.join(project_root, ".env"))

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.storage import storage
from backend.models import TaskStatus
from backend.agent import run_agent
from backend.auth import router as auth_router


# ── Task Runner (background) ───────────────────────────────────────────
async def process_task(task_id: str, prompt: str):
    """Background task: run the LangGraph agent"""
    print(f"\n[STEP 1] Background task started for ID: {task_id}", flush=True)
    try:
        print(f"[STEP 2] Updating storage to 'analyzing'...", flush=True)
        storage.update_task(task_id, status="analyzing", progress=10)

        print(f"[STEP 3] Entering run_agent...", flush=True)

        def on_node_sync(node_name):
            progress_map = {
                "analyze": 10, "plan": 20, "generate_steps": 55,
                "assemble": 70, "generate_preview": 90, "output": 100,
            }
            status_map = {
                "analyze": "analyzing", "plan": "planning",
                "generate_steps": "generating", "assemble": "assembling",
                "generate_preview": "generating_preview", "output": "completed",
            }
            storage.update_task(
                task_id,
                status=status_map.get(node_name, "generating"),
                progress=progress_map.get(node_name, 50),
            )
            print(f"  [progress] {node_name} -> {progress_map.get(node_name, 50)}%", flush=True)

        result = await run_agent(task_id, prompt, callback=on_node_sync)

        final_html = result.get("html", "")
        title = result.get("title", prompt[:30])
        tags = result.get("tags", {"main_tag": "运算能力", "sub_tags": ["推理意识"]})

        print(f"[STEP 4] run_agent finished. HTML length: {len(final_html) if final_html else 0}", flush=True)

        if final_html:
            storage.save_html(task_id, final_html)
            storage.update_task(
                task_id,
                status="completed",
                progress=100,
                title=title,
                tags=tags,
            )
        else:
            print(f"❌ Task {task_id} failed: run_agent returned an empty string.", flush=True)
            storage.update_task(task_id, status="failed", progress=0)

    except Exception as e:
        import traceback
        print(f"[ERROR] Task {task_id} failed: {e}", flush=True)
        traceback.print_exc()
        storage.update_task(task_id, status="failed", progress=0)


# ── App ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Teaching Animation Agent started")
    yield
    print("👋 Shutting down")


app = FastAPI(title="Teaching Animation Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router
app.include_router(auth_router)

# Serve frontend
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# ── API Endpoints ──────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve frontend"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Teaching Animation Agent API</h1>")


@app.get("/video.html", response_class=HTMLResponse)
async def video_page():
    """Serve video page"""
    video_path = os.path.join(frontend_dir, "video.html")
    if os.path.exists(video_path):
        with open(video_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    raise HTTPException(404, "video.html not found")


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """解析上传文件，提取文字内容（支持文档和图片）"""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content = await file.read()

    try:
        # 图片类型 → 用 LLM 识别
        if ext in ("jpg", "jpeg", "png", "bmp", "webp", "gif"):
            import base64
            img_b64 = base64.b64encode(content).decode("utf-8")
            mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
            text = _ocr_image_with_llm(img_b64, mime)
            if not text:
                raise HTTPException(400, "无法识别图片中的内容")
            return JSONResponse({"filename": filename, "text": text, "length": len(text)})

        # 文档类型
        if ext == "txt":
            text = content.decode("utf-8", errors="ignore")
        elif ext == "docx":
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == "pdf":
            import fitz
            import io
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        elif ext == "doc":
            raise HTTPException(400, "暂不支持 .doc 格式，请转为 .docx 后重试")
        else:
            raise HTTPException(400, f"不支持的文件格式: .{ext}")

        text = text.strip()
        if not text:
            raise HTTPException(400, "文件内容为空")

        if len(text) > 3000:
            text = text[:3000] + "...(已截断)"

        return JSONResponse({"filename": filename, "text": text, "length": len(text)})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"文件解析失败: {str(e)}")


def _ocr_image_with_llm(img_b64: str, mime: str) -> str:
    """用 LLM 视觉能力识别图片中的数学内容"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from backend.agent import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

    try:
        llm = ChatOpenAI(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            temperature=0,
            max_tokens=1000,
        )
        msg = HumanMessage(content=[
            {"type": "text", "text": "请识别这张图片中的数学题目内容，只输出题目文字，不要解答。"},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
        ])
        resp = llm.invoke([msg])
        return resp.content.strip()
    except Exception as e:
        print(f"[ocr] LLM vision failed: {e}", flush=True)
        return ""


@app.post("/api/tasks")
async def create_task(prompt: str = Form(...)):
    """创建生成任务"""
    task_id = str(uuid.uuid4())
    storage.create_task(task_id, prompt)

    # 启动后台任务
    asyncio.create_task(process_task(task_id, prompt))

    return JSONResponse({
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "任务已创建，正在处理中",
    })


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """查询任务状态"""
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.get("/api/tasks/{task_id}/html")
async def get_task_html(task_id: str):
    """获取生成的 HTML"""
    html = storage.get_html(task_id)
    if not html:
        raise HTTPException(404, "HTML not found or still generating")
    return HTMLResponse(html)


@app.get("/api/tasks/{task_id}/preview")
async def get_task_preview(task_id: str):
    """获取封面预览图（仅读文件，不按需生成）"""
    preview = storage.get_preview(task_id)
    if not preview:
        raise HTTPException(404, "Preview not found")
    content, content_type = preview
    from fastapi.responses import Response
    return Response(content=content, media_type=content_type)


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    return storage.list_tasks()


# ── Run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8081, reload=False)
