# -*- coding: utf-8 -*-
"""
BitwiseAI - 硬件调试和日志分析的 AI 工具

专注于硬件指令验证、日志解析和智能分析
支持 Agent 循环、多会话管理、Skill 系统等高级功能
"""

import os
import json
from typing import Any, Iterator, List, Optional, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .llm import LLM
from .embedding import Embedding
from .utils import DocumentLoader, TextSplitter
from .core import (
    SkillManager,
    RAGEngine,
    ChatEngine,
    SkillIndexer,
    LLMConfig,
    LLMProvider,
    AgentConfig,
    LoopConfig,
)
from .core.document_manager import DocumentManager
from .interfaces import TaskInterface, AnalysisResult


class BitwiseAI:
    """
    BitwiseAI 核心类

    整合所有功能：
    - 硬件指令验证和调试日志分析
    - Agent 循环（对话→执行→反馈）
    - 多会话管理
    - Skill 系统
    - RAG 检索
    - 记忆系统（双层次：短期/长期）

    设计原则（第一性原理）：
    1. 单一职责：每个初始化方法只负责一个组件
    2. 依赖清晰：组件初始化顺序明确
    3. 防御性编程：每个步骤都有错误处理
    4. 优雅降级：增强功能失败时自动降级
    """

    def __init__(
        self,
        config_path: str = "~/.bitwiseai/config.json",
        use_enhanced: bool = True,
    ):
        """
        初始化 BitwiseAI

        Args:
            config_path: 配置文件路径
            use_enhanced: 是否使用增强版引擎（支持 Agent、会话等）
        """
        self.config_path = os.path.expanduser(config_path)
        self.use_enhanced = use_enhanced

        # 加载配置（第一步：配置管理）
        self.config = self._load_config()

        # 验证配置（第二步：配置验证）
        self._validate_config()

        # 初始化核心组件（第三步：组件初始化）
        self._init_components()

        # 任务管理
        self.tasks: List[TaskInterface] = []
        self.task_results: Dict[str, List[AnalysisResult]] = {}
        self.log_file_path: Optional[str] = None

        # 打印启动信息
        self._print_startup_info()

    def _load_config(self) -> dict:
        """
        加载配置文件

        从 ~/.bitwiseai/config.json 加载配置
        用户运行 'bitwiseai config --force' 生成配置文件后，
        应该直接编辑该文件来配置 API 密钥和其他参数
        """
        default_path = os.path.expanduser("~/.bitwiseai/config.json")

        # 从默认配置开始
        config = {}

        # 加载默认配置文件
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  配置文件读取失败: {e}")
                print(f"   请运行: bitwiseai config --force")
        else:
            print(f"⚠️  配置文件不存在: {default_path}")
            print(f"   请运行: bitwiseai config --force")

        # 加载指定配置（覆盖默认配置）
        if self.config_path != default_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    specified_config = json.load(f)
                    config.update(specified_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  指定配置文件读取失败: {e}")

        # 不再从环境变量加载配置
        # 所有配置应通过编辑 ~/.bitwiseai/config.json 完成
        return config

    def _validate_config(self):
        """验证配置完整性"""
        errors = []

        # 验证 LLM 配置
        llm_config = self.config.get("llm", {})
        if not llm_config.get("api_key"):
            errors.append("LLM_API_KEY 未设置")
        if not llm_config.get("base_url"):
            errors.append("LLM_BASE_URL 未设置")

        # 验证 Embedding 配置（仅在需要时）
        try:
            from .core import RAGEngine
            embedding_config = self.config.get("embedding", {})
            if not embedding_config.get("api_key"):
                errors.append("EMBEDDING_API_KEY 未设置")
            if not embedding_config.get("base_url"):
                errors.append("EMBEDDING_BASE_URL 未设置")
        except ImportError:
            # RAGEngine 不可用，跳过验证
            pass

        if errors:
            raise ValueError(
                "配置不完整，请设置以下环境变量或配置文件:\n" +
                "\n".join(f"  - {e}" for e in errors) +
                "\n\n或运行: bitwiseai config --force"
            )

    def _init_components(self):
        """
        初始化所有组件

        初始化顺序（依赖链）：
        1. LLM（最底层，无依赖）
        2. Embedding（无依赖）
        3. MemoryManager（依赖 Embedding）
        4. DocumentManager（依赖 MemoryManager）
        5. RAGEngine（依赖 MemoryManager, DocumentManager）
        6. SkillManager（依赖 MemoryManager）
        7. ChatEngine（依赖上述所有）
        """
        # 1. 初始化 LLM
        self._init_llm()

        # 2. 初始化 Embedding
        self._init_embedding()

        # 3. 初始化记忆系统（替代 VectorDB）
        self._init_memory_system()

        # 4. 初始化文档管理器
        self._init_document_manager()

        # 5. 初始化 RAG 引擎
        self._init_rag_engine()

        # 6. 初始化 Skill 系统
        self._init_skills()

        # 7. 初始化聊天引擎（最后，依赖最多）
        self._init_chat_engine()

    def _init_llm(self):
        """初始化 LLM"""
        llm_config = self.config.get("llm", {})

        self.llm = LLM(
            model=llm_config.get("model", "gpt-4o-mini"),
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=llm_config.get("temperature", 0.7)
        )

    def _init_embedding(self):
        """初始化 Embedding"""
        embedding_config = self.config.get("embedding", {})

        self.embedding = Embedding(
            model=embedding_config.get("model", "text-embedding-3-small"),
            api_key=embedding_config["api_key"],
            base_url=embedding_config["base_url"]
        )

    def _init_memory_system(self):
        """初始化记忆系统（替代 MilvusDB）"""
        from .core.memory import MemoryManager, MemoryConfig, OpenAIEmbeddingProvider

        memory_config = self.config.get("memory", {})
        embedding_config = self.config.get("embedding", {})

        # 创建 Embedding Provider
        embedding_provider = OpenAIEmbeddingProvider(
            api_key=embedding_config["api_key"],
            base_url=embedding_config.get("base_url"),
            model=embedding_config.get("model", "text-embedding-3-small")
        )

        # 创建 MemoryManager
        config = MemoryConfig.from_dict(memory_config)
        self.memory_manager = MemoryManager(
            workspace_dir=memory_config.get("workspace_dir", "~/.bitwiseai"),
            db_path=memory_config.get("db_path"),
            embedding_provider=embedding_provider,
            config=config
        )

        # 初始化记忆系统
        self.memory_manager.initialize()
        print("✓ 记忆系统初始化完成")

    def _init_document_manager(self):
        """初始化文档管理器"""
        rag_config = self.config.get("rag", {})

        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter()

        doc_config = {
            "similarity_threshold": rag_config.get("similarity_threshold", 0.85),
            "save_chunks": rag_config.get("save_chunks", False),
            "chunks_dir": os.path.expanduser(rag_config.get("chunks_dir", "~/.bitwiseai/chunks"))
        }

        self.document_manager = DocumentManager(
            memory_manager=self.memory_manager,
            document_loader=self.document_loader,
            text_splitter=self.text_splitter,
            config=doc_config
        )

    def _init_rag_engine(self):
        """初始化 RAG 引擎"""
        rag_config = self.config.get("rag", {})

        rag_engine_config = {
            "similarity_threshold": rag_config.get("similarity_threshold", 0.85),
            "save_chunks": rag_config.get("save_chunks", False),
            "chunks_dir": os.path.expanduser(rag_config.get("chunks_dir", "~/.bitwiseai/chunks")),
            "enable_document_name_matching": rag_config.get("enable_document_name_matching", True),
            "document_name_match_threshold": rag_config.get("document_name_match_threshold", 0.3)
        }

        self.rag_engine = RAGEngine(
            memory_manager=self.memory_manager,
            document_manager=self.document_manager,
            config=rag_engine_config
        )

    def _init_skills(self):
        """初始化 Skill 系统"""
        skill_config = self.config.get("skills", {})

        # 初始化技能索引器
        skill_indexer = None
        if skill_config.get("index_to_memory", True):
            try:
                skill_indexer = SkillIndexer(
                    memory_manager=self.memory_manager
                )
            except Exception as e:
                print(f"⚠️  初始化技能索引器失败: {e}")

        # 初始化 Skill 管理器
        self.skill_manager = SkillManager(skill_indexer=skill_indexer)

        # 添加外部技能目录
        external_dirs = skill_config.get("external_directories", ["~/.bitwiseai/skills"])
        for ext_dir in external_dirs:
            self.skill_manager.add_skills_directory(ext_dir)

        # 扫描技能
        self.skill_manager.scan_skills()

        # 自动加载技能（包括内置默认技能和用户配置）
        default_auto_load = ['memory-archiver']  # 默认自动加载的技能
        auto_load = skill_config.get("auto_load", [])
        auto_load = list(dict.fromkeys(default_auto_load + auto_load))  # 去重保持顺序

        for skill_name in auto_load:
            if skill_name in self.skill_manager.list_available_skills():
                self.skill_manager.load_skill(skill_name)

    def _init_chat_engine(self):
        """
        初始化聊天引擎

        尝试使用增强版引擎，失败时降级到普通引擎
        """
        self.system_prompt = self.config.get(
            "system_prompt",
            "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        )

        # 普通引擎（降级选项）
        def create_standard_engine():
            return ChatEngine(
                llm=self.llm,
                rag_engine=self.rag_engine,
                skill_manager=self.skill_manager,
                system_prompt=self.system_prompt
            )

        # 如果不需要增强版，直接使用普通引擎
        if not self.use_enhanced:
            self.enhanced_engine = None
            self.chat_engine = create_standard_engine()
            return

        # 暂时禁用增强版引擎，使用标准引擎
        self.enhanced_engine = None
        self.chat_engine = create_standard_engine()
        print("使用标准版引擎")

    def _create_enhanced_engine(self):
        """
        创建增强版引擎

        Returns:
            EnhancedChatEngine 实例

        Raises:
            ImportError: 如果增强版依赖缺失
            Exception: 如果初始化失败
        """
        # 动态导入，避免普通模式下的依赖问题
        try:
            from .core import EnhancedChatEngine
        except ImportError as e:
            raise ImportError(f"EnhancedChatEngine 不可用: {e}")

        llm_config_data = self.config.get("llm", {})
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=llm_config_data.get("model", "gpt-4o-mini"),
            api_key=llm_config_data.get("api_key", ""),
            base_url=llm_config_data.get("base_url", ""),
            temperature=llm_config_data.get("temperature", 0.7),
        )

        return EnhancedChatEngine(
            llm_config=llm_config,
            rag_engine=self.rag_engine,
            skill_manager=self.skill_manager,
            system_prompt=self.system_prompt,
            auto_save=True,
        )

    def _print_startup_info(self):
        """打印启动信息"""
        llm_config = self.config.get("llm", {})
        embedding_config = self.config.get("embedding", {})
        memory_status = self.memory_manager.status()

        print("=" * 50)
        print("BitwiseAI 初始化完成")
        print(f"  模式: {'增强版' if self.enhanced_engine else '标准版'}")
        print(f"  LLM: {llm_config.get('model', 'N/A')}")
        print(f"  Embedding: {embedding_config.get('model', 'N/A')}")
        print(f"  记忆系统: {'已启用' if memory_status.initialized else '未初始化'}")
        print(f"  记忆文件数: {memory_status.files}")
        print(f"  记忆块数: {memory_status.chunks}")
        print(f"  Skills: {len(self.skill_manager.list_available_skills())} 个")
        print(f"  已加载: {len(self.skill_manager.list_loaded_skills())} 个")
        print("=" * 50)

    # ========== 对话 API ==========

    def chat(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        history: Optional[List[dict]] = None,
        skill_context: Optional[str] = None
    ) -> str:
        """
        对话方法（非流式）

        自动处理同步和异步引擎
        """
        import asyncio
        import inspect

        # 调用 chat 引擎的方法
        result = self.chat_engine.chat(
            query=query,
            use_rag=use_rag,
            use_tools=use_tools,
            history=history,
            skill_context=skill_context
        )

        # 如果结果是协程，运行它
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, result)
                        return future.result()
                else:
                    return asyncio.run(result)
            except RuntimeError:
                return asyncio.run(result)

        return result

    def chat_stream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        history: Optional[List[dict]] = None
    ) -> Iterator[str]:
        """
        流式对话方法

        自动处理同步和异步引擎
        """
        yield from self.chat_engine.chat_stream(
            query=query,
            use_rag=use_rag,
            use_tools=use_tools,
            history=history
        )

    # ========== Agent 循环 API ==========

    async def chat_with_agent(
        self,
        query: str,
        agent_config: Optional[AgentConfig] = None,
        loop_config: Optional[LoopConfig] = None,
    ) -> str:
        """使用 Agent 循环进行对话"""
        if not self.enhanced_engine:
            raise RuntimeError(
                "Agent 模式需要增强版引擎。"
                "请初始化时设置 use_enhanced=True，"
                "或检查是否缺少相关依赖。"
            )

        return await self.enhanced_engine.chat_with_agent(
            query=query,
            agent_config=agent_config,
            loop_config=loop_config,
        )

    async def chat_with_agent_stream(
        self,
        query: str,
        agent_config: Optional[AgentConfig] = None,
    ) -> Iterator[str]:
        """使用 Agent 循环进行对话（流式）"""
        if not self.enhanced_engine:
            raise RuntimeError("Agent 模式需要增强版引擎")

        async for token in self.enhanced_engine.chat_with_agent_stream(
            query=query,
            agent_config=agent_config,
        ):
            yield token

    # ========== 会话管理 API ==========

    async def new_session(self, name: str):
        """创建新会话"""
        if not self.enhanced_engine:
            raise RuntimeError("会话管理需要增强版引擎")
        return await self.enhanced_engine.new_session(name)

    async def switch_session(self, session_id: str):
        """切换会话"""
        if not self.enhanced_engine:
            raise RuntimeError("会话管理需要增强版引擎")
        return await self.enhanced_engine.switch_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if not self.enhanced_engine:
            raise RuntimeError("会话管理需要增强版引擎")
        return await self.enhanced_engine.delete_session(session_id)

    def list_sessions(self) -> list:
        """列出所有会话"""
        if not self.enhanced_engine:
            return []
        return self.enhanced_engine.list_sessions()

    # ========== 记忆系统 API（新增）==========

    def append_to_memory(self, content: str, to_long_term: bool = False) -> None:
        """
        追加内容到记忆系统

        Args:
            content: 要记录的内容
            to_long_term: 是否直接写入长期记忆
        """
        if to_long_term:
            self.memory_manager.promote_to_long_term(content)
        else:
            self.memory_manager.append_to_short_term(content)

    def search_memory(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索记忆系统

        Args:
            query: 查询文本
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        results = self.memory_manager.search_sync(query, max_results=max_results)
        return [
            {
                "text": r.text,
                "path": r.path,
                "score": r.score,
                "start_line": r.start_line,
                "end_line": r.end_line,
            }
            for r in results
        ]

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = self.memory_manager.stats()
        status = self.memory_manager.status()
        return {
            "total_files": stats.total_files,
            "total_chunks": stats.total_chunks,
            "total_vectors": stats.total_vectors,
            "cache_entries": stats.cache_entries,
            "db_size_bytes": stats.db_size_bytes,
            "initialized": status.initialized,
            "watching": status.watching,
        }

    def compact_memory(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """
        压缩短期记忆

        Args:
            days_to_keep: 保留天数

        Returns:
            压缩结果统计
        """
        result = self.memory_manager.compact_short_term(days_to_keep=days_to_keep)
        return {
            "files_compacted": result.files_compacted,
            "files_archived": result.files_archived,
            "summaries_generated": result.summaries_generated,
        }

    # ========== 文档管理 API ==========

    def load_documents(self, folder_path: str, skip_duplicates: bool = True) -> Dict[str, Any]:
        """加载文件夹中的所有文档"""
        return self.rag_engine.load_documents(folder_path, skip_duplicates=skip_duplicates)

    def add_text(self, text: str, source: Optional[str] = None) -> int:
        """添加单个文本到知识库

        Args:
            text: 要添加的文本内容
            source: 文本来源标识（如文件名）

        Returns:
            添加的文档数量
        """
        return self.rag_engine.add_text(text, source=source)

    def clear_memory_db(self):
        """清空记忆系统数据库"""
        self.rag_engine.clear()
        print("✓ 记忆系统数据库已清空")

    # ========== Skill 管理 API ==========

    def load_skill(self, name: str) -> bool:
        """加载 skill"""
        return self.skill_manager.load_skill(name)

    def unload_skill(self, name: str) -> bool:
        """卸载 skill"""
        return self.skill_manager.unload_skill(name)

    def list_skills(self, loaded_only: bool = False) -> List[str]:
        """列出所有 skills"""
        if loaded_only:
            return self.skill_manager.list_loaded_skills()
        else:
            return self.skill_manager.list_available_skills()

    def search_skills(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相关技能"""
        return self.skill_manager.search_skills(query, top_k)

    def add_skills_directory(self, path: str) -> bool:
        """添加外部技能目录"""
        return self.skill_manager.add_skills_directory(path)

    # ========== 检查点 API ==========

    def create_checkpoint(self, description: str = "") -> int:
        """创建检查点"""
        if not self.enhanced_engine:
            raise RuntimeError("检查点功能需要增强版引擎")
        return self.enhanced_engine.create_checkpoint(description)

    def rollback_to_checkpoint(self, checkpoint_id: int) -> bool:
        """回滚到检查点"""
        if not self.enhanced_engine:
            raise RuntimeError("检查点功能需要增强版引擎")
        return self.enhanced_engine.rollback_to_checkpoint(checkpoint_id)

    def list_checkpoints(self) -> list:
        """列出所有检查点"""
        if not self.enhanced_engine:
            return []
        return self.enhanced_engine.list_checkpoints()

    # ========== 向后兼容 API ==========

    def invoke_tool(self, name: str, *args, **kwargs) -> Any:
        """调用工具（向后兼容）"""
        for skill_name in self.skill_manager.list_loaded_skills():
            skill = self.skill_manager.get_skill(skill_name)
            if skill and skill.loaded and name in skill.tools:
                func = skill.tools[name]["function"]
                return func(*args, **kwargs)
        raise ValueError(f"工具不存在: {name}")

    def load_log_file(self, file_path: str):
        """加载日志文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"日志文件不存在: {file_path}")
        self.log_file_path = file_path
        print(f"✓ 已加载日志文件: {file_path}")

    def load_specification(self, spec_path: str):
        """加载规范文档到知识库"""
        if os.path.isdir(spec_path):
            self.load_documents(spec_path)
        elif os.path.isfile(spec_path):
            with open(spec_path, 'r', encoding='utf-8') as f:
                self.add_text(f.read())
        print("✓ 规范文档已加载到知识库")

    def query_specification(self, query: str, top_k: int = 5) -> str:
        """查询规范文档"""
        return self.rag_engine.search(query, top_k=top_k)

    def ask_about_log(self, question: str) -> str:
        """询问关于日志的问题"""
        if self.log_file_path:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read(10000)
            prompt = f"基于以下日志内容回答问题：\n\n```\n{log_content}\n```\n\n问题：{question}"
            return self.llm.invoke(prompt)
        return self.chat(question, use_rag=True)

    # ========== 清理 API ==========

    def close(self):
        """关闭 BitwiseAI，释放资源"""
        if hasattr(self, 'memory_manager'):
            self.memory_manager.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


__all__ = ["BitwiseAI"]
