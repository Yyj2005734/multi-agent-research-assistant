"""
FastAPI 后端服务（Web 模式入口）

提供 REST API 接口，供前端 Web 页面调用：
  - POST /api/start-analysis   启动 Agent 分析任务
  - POST /api/stop-analysis    停止分析任务
  - GET  /api/task-status      获取任务状态
  - GET  /api/agent-status     获取 Agent 状态（task-status 别名）
  - GET  /api/logs             获取日志
  - GET  /api/result/{type}    获取单个 Agent 结果
  - GET  /api/all-results      获取所有结果
  - POST /api/test             测试 API 连接
  - POST /api/test-pipeline    快速测试（不消耗 token）
  - GET  /api/config           获取配置信息

启动方式：
  python server.py
  访问 http://127.0.0.1:8000
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict

# 将项目根目录加入 sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 确保从项目目录加载 .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

from utils.api_client import LLMClient
from pipeline import Pipeline

# ─── 日志配置 ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("server")

# ─── FastAPI 应用 ──────────────────────────────────────────

app = FastAPI(title="多 Agent 协作研究助手", version="2.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        logger.info(f"→ {request.method} {request.url.path}")
        response = await call_next(request)
        elapsed = round((time.time() - start) * 1000)
        logger.info(f"← {request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
        return response


app.add_middleware(RequestLoggingMiddleware)

# 静态文件服务
app.mount("/static", StaticFiles(directory=os.path.join(project_root, "static")), name="static")

# ─── 全局状态 ──────────────────────────────────────────────


class LogCollector:
    """收集 Pipeline 运行日志（结构化存储）"""

    # 类型映射：内部 level → 前端 type
    LEVEL_MAP = {
        "info": "info",
        "success": "success",
        "warning": "warn",
        "error": "error",
        "agent": "agent",
        "coord": "coord",
    }

    def __init__(self):
        self._records: List[Dict] = []  # [{id, time, type, message}, ...]
        self._next_id = 1
        self._lock = threading.Lock()

    def add(self, message: str, level: str = "info"):
        log_type = self.LEVEL_MAP.get(level, "info")
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            entry = {
                "id": self._next_id,
                "time": timestamp,
                "type": log_type,
                "message": message,
            }
            self._records.append(entry)
            self._next_id += 1
        logger.info(f"[LOG] {message}")

    def get_since(self, since_id: int = 0) -> List[Dict]:
        """获取 id > since_id 的日志"""
        with self._lock:
            return [r for r in self._records if r["id"] > since_id]

    def get_all(self) -> List[Dict]:
        with self._lock:
            return list(self._records)

    def get_last_id(self) -> int:
        with self._lock:
            return self._records[-1]["id"] if self._records else 0

    def clear(self):
        with self._lock:
            self._records.clear()


log_collector = LogCollector()


# ─── 任务管理器 ────────────────────────────────────────────

# Agent 执行顺序
AGENT_STEPS = ["coordinator", "analyzer", "reviewer", "synthesizer", "advisor"]


class TaskManager:
    """管理分析任务的生命周期"""

    def __init__(self):
        self.task_status = "idle"  # idle | running | done | error | stopped
        self.progress = 0
        self.agent_states: Dict[str, str] = {a: "idle" for a in AGENT_STEPS}
        self.results: Dict[str, str] = {}
        self.error_message: Optional[str] = None
        self.thread: Optional[threading.Thread] = None
        self.elapsed = 0.0
        self._start_time = 0.0
        self._stop_flag = False
        self._lock = threading.Lock()

    def start(self, content: str, api_key: str = None, api_base: str = None, model: str = None):
        """启动分析任务"""
        if self.task_status == "running":
            raise RuntimeError("任务正在运行中")

        self.task_status = "running"
        self.progress = 0
        self.agent_states = {a: "idle" for a in AGENT_STEPS}
        self.results = {}
        self.error_message = None
        self.elapsed = 0.0
        self._stop_flag = False
        self._start_time = time.time()

        log_collector.clear()
        log_collector.add("分析任务启动")

        self.thread = threading.Thread(
            target=self._run_pipeline,
            args=(content, api_key, api_base, model),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """停止分析任务"""
        if self.task_status == "running":
            self._stop_flag = True
            self.task_status = "stopped"
            log_collector.add("任务已手动停止", "warning")

    def get_status(self) -> dict:
        """获取任务状态（匹配前端期望的字段名）"""
        with self._lock:
            # 实时计算运行时长
            if self.task_status == "running" and self._start_time > 0:
                elapsed = time.time() - self._start_time
            else:
                elapsed = self.elapsed
            return {
                "task_status": self.task_status,
                "agent_states": dict(self.agent_states),
                "elapsed": round(elapsed, 1),
                "progress": self.progress,
                "error_message": self.error_message,
            }

    def get_results(self) -> dict:
        with self._lock:
            return dict(self.results)

    def _set_agent_state(self, agent: str, state: str):
        with self._lock:
            self.agent_states[agent] = state

    def _run_pipeline(self, content: str, api_key: str = None, api_base: str = None, model: str = None):
        """在后台线程中执行 Pipeline"""
        try:
            log_collector.add("正在初始化 LLM 客户端...")
            client = LLMClient(api_key=api_key, base_url=api_base, model=model)
            pipeline = Pipeline(client)

            agent_names = {
                "coordinator": "🎯 协调者",
                "analyzer": "🔍 分析专员",
                "reviewer": "📝 评审专员",
                "synthesizer": "🔗 综合专员",
                "advisor": "💡 研究顾问",
            }

            # 并行模式：用完成计数算进度
            done_count = [0]  # 用列表以便在闭包中修改

            def on_step(agent_name, step_status, result):
                if self._stop_flag:
                    return

                name = agent_names.get(agent_name, agent_name)

                if step_status == "start":
                    self._set_agent_state(agent_name, "working")
                    log_collector.add(f"{name} 开始分析...")

                elif step_status == "done":
                    self._set_agent_state(agent_name, "done")
                    done_count[0] += 1
                    with self._lock:
                        self.progress = int(done_count[0] / len(AGENT_STEPS) * 100)
                    log_collector.add(f"{name} 分析完成 ({done_count[0]}/5)")

                elif step_status == "error":
                    self._set_agent_state(agent_name, "error")
                    done_count[0] += 1
                    with self._lock:
                        self.progress = int(done_count[0] / len(AGENT_STEPS) * 100)
                    log_collector.add(f"{name} 分析失败: {result}", "error")

            log_collector.add("开始并行执行 5 个 Agent...")

            # 并行执行管线（5 个 Agent 同时并发）
            result = pipeline.run_parallel(content, on_step=on_step)

            if self._stop_flag:
                return

            # Pipeline 返回 result 名（plan/analysis/review/synthesis/advice）
            # 前端期望 agent 名（coordinator/analyzer/reviewer/synthesizer/advisor）
            RESULT_TO_AGENT = {
                "plan": "coordinator",
                "analysis": "analyzer",
                "review": "reviewer",
                "synthesis": "synthesizer",
                "advice": "advisor",
            }

            with self._lock:
                for key, value in result.items():
                    if key in RESULT_TO_AGENT:
                        self.results[RESULT_TO_AGENT[key]] = value
                self.results["steps"] = result.get("steps", {})
                self.elapsed = result.get("elapsed", time.time() - self._start_time)
                self.progress = 100
                self.task_status = "done"

            log_collector.add(f"分析完成！总耗时 {self.elapsed:.1f}s")

        except Exception as e:
            with self._lock:
                self.error_message = str(e)
                self.task_status = "error"
            log_collector.add(f"分析失败: {e}", "error")
            logger.exception("Pipeline 执行异常")


task_manager = TaskManager()

# ─── 结果类型映射 ──────────────────────────────────────────

RESULT_TYPE_MAP = {
    "content_analysis": "analyzer",
    "review_report": "reviewer",
    "synthesis_report": "synthesizer",
    "advice": "advisor",
    "plan": "coordinator",
    "analysis": "analyzer",
    "review": "reviewer",
    "synthesis": "synthesizer",
}

# ─── 请求模型 ──────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    content: str
    mode: str = "full"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None


class TestApiRequest(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None


# ─── API 路由 ──────────────────────────────────────────────


@app.get("/")
async def root():
    """返回前端页面"""
    html_path = os.path.join(project_root, "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/start-analysis")
async def start_analysis(request: AnalyzeRequest):
    """启动分析任务"""
    logger.info(f"收到分析请求，内容长度: {len(request.content)}")
    try:
        task_manager.start(
            request.content,
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
        )
        return {"code": 200, "msg": "分析任务已启动", "data": None}
    except RuntimeError as e:
        logger.warning(f"启动失败: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"启动异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop-analysis")
async def stop_analysis():
    """停止分析任务"""
    task_manager.stop()
    return {"code": 200, "msg": "分析任务已停止", "data": None}


@app.get("/api/task-status")
async def get_task_status():
    """获取任务状态（前端期望: task_status, agent_states, elapsed, error_message）"""
    return task_manager.get_status()


@app.get("/api/agent-status")
async def get_agent_status():
    """获取 Agent 状态（task-status 的别名）"""
    return task_manager.get_status()


@app.get("/api/logs")
async def get_logs(since_id: int = 0):
    """获取日志（支持 since_id 增量拉取）"""
    logs = log_collector.get_since(since_id)
    return {
        "logs": logs,
        "last_id": log_collector.get_last_id(),
    }


@app.get("/api/result/{result_type}")
async def get_result(result_type: str):
    """获取单个 Agent 的分析结果"""
    results = task_manager.get_results()

    # 直接匹配
    if result_type in results:
        return {"type": result_type, "content": results[result_type]}

    # 映射匹配
    mapped_type = RESULT_TYPE_MAP.get(result_type)
    if mapped_type and mapped_type in results:
        return {"type": result_type, "content": results[mapped_type]}

    if task_manager.task_status == "done":
        raise HTTPException(status_code=404, detail=f"结果类型 '{result_type}' 不存在")

    return {"type": result_type, "content": ""}


@app.get("/api/all-results")
async def get_all_results():
    """获取所有分析结果"""
    results = task_manager.get_results()
    return {"results": results, "task_status": task_manager.task_status}


@app.post("/api/test")
async def test_connection(request: TestApiRequest):
    """测试 API 连接（接收前端传入的 api_key/api_base/model）"""
    logger.info(f"测试 API 连接: model={request.model}, base={request.api_base}")
    try:
        client = LLMClient(
            api_key=request.api_key,
            base_url=request.api_base,
            model=request.model,
        )
        result = client.test_connection()
        return result
    except ValueError as e:
        # LLMClient 初始化失败（如 api_key 为空）
        logger.error(f"API 配置错误: {e}")
        return {"success": False, "message": f"配置错误: {e}"}
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return {"success": False, "message": f"连接失败: {e}"}


@app.post("/api/test-pipeline")
async def test_pipeline():
    """快速测试管线（不消耗 token）"""
    logger.info("快速测试管线")

    mock_results = {
        "coordinator": "## 📋 分析计划\n\n"
                       "1. **内容概览**：快速浏览论文结构和主要章节\n"
                       "2. **深度分析**：分析研究方法、实验设计和数据\n"
                       "3. **批判性评审**：评估论文的优缺点\n"
                       "4. **综合整合**：整合各维度分析结果\n"
                       "5. **研究建议**：提供后续研究方向建议\n\n"
                       "> ⚡ 这是快速测试模式的模拟结果，不消耗 token。",
        "analyzer": "## 🔍 内容分析报告\n\n"
                    "### 论文结构\n"
                    "- 摘要清晰地概括了研究目标和主要发现\n"
                    "- 引言部分文献综述较为全面\n"
                    "- 方法论描述详细，实验设计合理\n\n"
                    "### 关键发现\n"
                    "1. 提出了创新的模型架构\n"
                    "2. 实验结果优于现有基线方法\n"
                    "3. 消融实验验证了各组件的有效性\n\n"
                    "> ⚡ 这是快速测试模式的模拟结果。",
        "reviewer": "## 📝 评审报告\n\n"
                    "### 优点\n"
                    "- ✅ 研究问题明确，具有实际应用价值\n"
                    "- ✅ 实验设计合理，对比实验充分\n"
                    "- ✅ 写作清晰，图表展示规范\n\n"
                    "### 不足\n"
                    "- ⚠️ 缺乏大规模数据集验证\n"
                    "- ⚠️ 计算复杂度分析不够深入\n"
                    "- ⚠️ 可复现性细节可以更详细\n\n"
                    "> ⚡ 这是快速测试模式的模拟结果。",
        "synthesizer": "## 🔗 综合报告\n\n"
                       "### 核心贡献\n"
                       "该论文在研究领域做出了有意义的贡献，提出了创新的方法并进行了充分的实验验证。\n\n"
                       "### 研究价值\n"
                       "- 理论价值：提供了新的研究视角\n"
                       "- 实践价值：方法可应用于实际场景\n\n"
                       "### 整体评价\n"
                       "论文质量良好，具有一定的创新性和实用价值。\n\n"
                       "> ⚡ 这是快速测试模式的模拟结果。",
        "advisor": "## 💡 研究建议\n\n"
                   "### 后续研究方向\n"
                   "1. **扩展实验**：在更多数据集上验证方法的有效性\n"
                   "2. **效率优化**：探索模型压缩和加速方法\n"
                   "3. **跨领域应用**：将方法应用到其他研究领域\n\n"
                   "### 改进建议\n"
                   "- 增加更多对比基线\n"
                   "- 提供更详细的超参数选择依据\n"
                   "- 开源代码和预训练模型\n\n"
                   "> ⚡ 这是快速测试模式的模拟结果。",
    }

    # 模拟分步完成（通过轮询驱动，先设 running 再逐步推进）
    log_collector.clear()

    with task_manager._lock:
        task_manager.task_status = "running"
        task_manager.progress = 0
        task_manager.agent_states = {a: "idle" for a in AGENT_STEPS}
        task_manager.results = {}
        task_manager.error_message = None
        task_manager.elapsed = 0.0

    log_collector.add("⚡ 快速测试模式启动")

    # 模拟每个 Agent 逐步完成
    for agent in AGENT_STEPS:
        with task_manager._lock:
            task_manager.agent_states[agent] = "working"
            task_manager.progress = int(AGENT_STEPS.index(agent) / len(AGENT_STEPS) * 100)
        time.sleep(0.3)
        with task_manager._lock:
            task_manager.agent_states[agent] = "done"
            task_manager.results[agent] = mock_results[agent]
        log_collector.add(f"✅ {agent} 分析完成")

    with task_manager._lock:
        task_manager.progress = 100
        task_manager.elapsed = 1.6
        task_manager.task_status = "done"

    log_collector.add("⚡ 快速测试完成！总耗时 1.6s")

    return {"code": 200, "message": "快速测试完成", "data": {"elapsed": 1.6}}


@app.get("/api/config")
async def get_config():
    """获取配置信息（脱敏）"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    has_key = bool(api_key and api_key != "your_api_key")
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"

    return {
        "has_api_key": has_key,
        "masked_key": masked_key if has_key else "未配置",
        "model": os.getenv("OPENAI_MODEL", "未配置"),
        "base_url": os.getenv("OPENAI_API_BASE", "未配置"),
        "host": os.getenv("SERVER_HOST", "127.0.0.1"),
        "port": int(os.getenv("SERVER_PORT", "8000")),
    }


# ─── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8000"))

    logger.info(f"启动服务: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/docs")

    uvicorn.run(app, host=host, port=port, log_level="info")
