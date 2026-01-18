# -*- coding: utf-8 -*-
"""
BitwiseAI - 硬件调试和日志分析的 AI 工具

专注于硬件指令验证、日志解析和智能分析
基于 LangChain，支持本地 Milvus 向量数据库
"""
import os
import json
from typing import List, Optional, Dict, Any, Union, Callable
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from typing import Iterator
from .llm import LLM
from .embedding import Embedding
from .vector_database import MilvusDB
from .utils import DocumentLoader, TextSplitter
from .core import SkillManager, RAGEngine, ChatEngine
from .core.document_manager import DocumentManager
from .interfaces import TaskInterface, AnalysisResult
from .reporter import Reporter


class BitwiseAI:
    """
    BitwiseAI 核心类

    特性：
    - 硬件指令验证和调试日志分析
    - 基于 LangChain 的 ChatOpenAI 和 OpenAIEmbeddings
    - 本地 Milvus 向量数据库
    - 支持 RAG 模式和纯 LLM 模式
    - 自定义系统提示词和工具扩展
    """

    def __init__(
        self,
        config_path: str = "~/.bitwiseai/config.json"
    ):
        """
        初始化 BitwiseAI

        Args:
            config_path: 配置文件路径
        """
        # 展开路径
        self.config_path = os.path.expanduser(config_path)
        self.working_dir = os.path.dirname(self.config_path)

        # 加载配置
        self.config = self._load_config()

        # 获取 LLM API 配置（优先从配置文件，其次从环境变量）
        llm_config = self.config.get("llm", {})
        llm_api_key = llm_config.get("api_key") or os.getenv("LLM_API_KEY")
        llm_base_url = llm_config.get("base_url") or os.getenv("LLM_BASE_URL")

        if not llm_api_key:
            raise ValueError("请在配置文件或 .env 文件中设置 LLM API Key")
        if not llm_base_url:
            raise ValueError("请在配置文件或 .env 文件中设置 LLM Base URL")

        # 获取 Embedding API 配置（优先从配置文件，其次从环境变量）
        embedding_config = self.config.get("embedding", {})
        embedding_api_key = embedding_config.get("api_key") or os.getenv("EMBEDDING_API_KEY")
        embedding_base_url = embedding_config.get("base_url") or os.getenv("EMBEDDING_BASE_URL")

        if not embedding_api_key:
            raise ValueError("请在配置文件或 .env 文件中设置 Embedding API Key")
        if not embedding_base_url:
            raise ValueError("请在配置文件或 .env 文件中设置 Embedding Base URL")

        # 初始化 LLM
        self.llm = LLM(
            model=llm_config.get("model", "MiniMax-M2.1"),
            api_key=llm_api_key,
            base_url=llm_base_url,
            temperature=llm_config.get("temperature", 0.7)
        )

        # 初始化 Embedding
        self.embedding = Embedding(
            model=embedding_config.get("model", "Qwen/Qwen3-Embedding-8B"),
            api_key=embedding_api_key,
            base_url=embedding_base_url
        )

        # 初始化向量数据库
        vector_config = self.config.get("vector_db", {})
        db_file = os.path.expanduser(vector_config.get("db_file", "~/.bitwiseai/milvus_data.db"))
        collection_name = vector_config.get("collection_name", "bitwiseai")
        embedding_dim = vector_config.get("embedding_dim", 4096)

        self.vector_db = MilvusDB(
            db_file=db_file,
            embedding_model=self.embedding,
            collection_name=collection_name,
            embedding_dim=embedding_dim
        )

        # 系统提示词
        self.system_prompt = self.config.get("system_prompt", "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。")

        # 文档加载器和切分器
        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter()
        
        # 创建文档管理器配置
        doc_manager_config = {
            "similarity_threshold": vector_config.get("similarity_threshold", 0.85),
            "save_chunks": vector_config.get("save_chunks", False),
            "chunks_dir": os.path.expanduser(vector_config.get("chunks_dir", "~/.bitwiseai/chunks"))
        }
        
        # 初始化文档管理器
        self.document_manager = DocumentManager(
            vector_db=self.vector_db,
            document_loader=self.document_loader,
            text_splitter=self.text_splitter,
            config=doc_manager_config
        )
        
        # 初始化 RAG 引擎（使用DocumentManager）
        self.rag_engine = RAGEngine(
            vector_db=self.vector_db,
            document_manager=self.document_manager
        )
        
        # 初始化 Skill 管理器
        self.skill_manager = SkillManager()
        self.skill_manager.scan_skills()
        
        # 自动加载内置 skills
        builtin_skills = ["hex_converter", "asm_parser"]
        for skill_name in builtin_skills:
            if skill_name in self.skill_manager.list_available_skills():
                self.skill_manager.load_skill(skill_name)
        
        # 初始化聊天引擎
        self.chat_engine = ChatEngine(
            llm=self.llm,
            rag_engine=self.rag_engine,
            skill_manager=self.skill_manager,
            system_prompt=self.system_prompt
        )
        
        # 任务管理
        self.tasks: List[TaskInterface] = []
        self.task_results: Dict[str, List[AnalysisResult]] = {}
        
        # 报告生成器
        self.reporter = Reporter()
        
        # 当前日志文件路径（用于任务执行）
        self.log_file_path: Optional[str] = None

        print("=" * 50)
        print("BitwiseAI 初始化完成")
        print(f"  LLM 模型: {llm_config.get('model')}")
        print(f"  Embedding 模型: {embedding_config.get('model')}")
        print(f"  向量库: {db_file}")
        print(f"  集合: {collection_name}")
        print(f"  可用 Skills: {len(self.skill_manager.list_available_skills())}")
        print(f"  已加载 Skills: {len(self.skill_manager.list_loaded_skills())}")
        print("=" * 50)

    def _load_config(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def set_system_prompt(self, prompt: str):
        """
        设置系统提示词

        Args:
            prompt: 系统提示词内容
        """
        self.system_prompt = prompt
        print(f"系统提示词已更新: {prompt[:50]}...")

    def load_documents(self, folder_path: str, skip_duplicates: bool = True) -> Dict[str, Any]:
        """
        加载文件夹中的所有文档

        Args:
            folder_path: 文件夹路径
            skip_duplicates: 是否跳过重复文档

        Returns:
            包含统计信息的字典：
                - total: 总文档片段数
                - inserted: 实际插入的片段数
                - skipped: 跳过的重复片段数
        """
        return self.rag_engine.load_documents(folder_path, skip_duplicates=skip_duplicates)

    def add_text(self, text: str) -> int:
        """
        添加单个文本到向量数据库

        Args:
            text: 文本内容

        Returns:
            插入的片段数量
        """
        return self.rag_engine.add_text(text)

    def chat(self, query: str, use_rag: bool = True, use_tools: bool = True) -> str:
        """
        对话方法（非流式）

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式（默认 True）
            use_tools: 是否使用工具（默认 True）

        Returns:
            LLM 生成的回答
        """
        return self.chat_engine.chat(query, use_rag=use_rag, use_tools=use_tools)

    def chat_stream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True
    ) -> Iterator[str]:
        """
        流式对话方法

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式（默认 True）
            use_tools: 是否使用工具（默认 True）

        Yields:
            每个 token 的字符串片段
        """
        yield from self.chat_engine.chat_stream(query, use_rag=use_rag, use_tools=use_tools)

    def clear_vector_db(self):
        """
        清空向量数据库
        """
        self.rag_engine.clear()
        print("✓ 向量数据库已清空")
    
    # ========== Skill 管理 API ==========
    
    def load_skill(self, name: str) -> bool:
        """
        加载 skill
        
        Args:
            name: Skill 名称
            
        Returns:
            是否加载成功
        """
        return self.skill_manager.load_skill(name)
    
    def unload_skill(self, name: str) -> bool:
        """
        卸载 skill
        
        Args:
            name: Skill 名称
            
        Returns:
            是否卸载成功
        """
        return self.skill_manager.unload_skill(name)
    
    def list_skills(self, loaded_only: bool = False) -> List[str]:
        """
        列出所有 skills
        
        Args:
            loaded_only: 是否只列出已加载的 skills
            
        Returns:
            Skill 名称列表
        """
        if loaded_only:
            return self.skill_manager.list_loaded_skills()
        else:
            return self.skill_manager.list_available_skills()
    
    # ========== 向后兼容的工具管理 API ==========
    
    def invoke_tool(self, name: str, *args, **kwargs) -> Any:
        """
        调用工具（向后兼容）
        
        注意：此方法已废弃，请使用 skill 系统
        
        Args:
            name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            工具执行结果
        """
        # 在所有已加载的 skills 中查找工具
        for skill_name in self.skill_manager.list_loaded_skills():
            skill = self.skill_manager.get_skill(skill_name)
            if skill and skill.loaded and name in skill.tools:
                func = skill.tools[name]["function"]
                return func(*args, **kwargs)
        
        raise ValueError(f"工具不存在: {name}")
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具（向后兼容）
        
        注意：此方法已废弃，请使用 skill 系统
        
        Returns:
            工具名称列表
        """
        tool_names = []
        for skill_name in self.skill_manager.list_loaded_skills():
            skill = self.skill_manager.get_skill(skill_name)
            if skill and skill.loaded:
                tool_names.extend(skill.tools.keys())
        return tool_names
    
    # ========== 任务管理 API ==========
    
    def register_task(self, task: TaskInterface):
        """
        注册分析任务
        
        Args:
            task: 任务对象，实现 TaskInterface 接口
            
        示例:
            class MyTask(AnalysisTask):
                def analyze(self, context, parsed_data):
                    # 自定义分析逻辑
                    results = []
                    # ... 分析代码 ...
                    return results
            
            ai.register_task(MyTask())
        """
        self.tasks.append(task)
        print(f"✓ 任务已注册: {task.get_name()}")
    
    def execute_task(self, task: Union[TaskInterface, str]) -> List[AnalysisResult]:
        """
        执行任务
        
        Args:
            task: 任务对象或任务名称
            
        Returns:
            任务执行结果列表
        """
        # 查找任务
        if isinstance(task, str):
            task_obj = None
            for t in self.tasks:
                if t.get_name() == task:
                    task_obj = t
                    break
            if not task_obj:
                raise ValueError(f"任务不存在: {task}")
        else:
            task_obj = task
        
        # 执行任务
        print(f"▶ 执行任务: {task_obj.get_name()}")
        results = task_obj.execute(self)
        
        # 保存结果
        self.task_results[task_obj.get_name()] = results
        self.reporter.add_results(results)
        
        print(f"✓ 任务完成: {len(results)} 个结果")
        return results
    
    def execute_all_tasks(self) -> Dict[str, List[AnalysisResult]]:
        """
        执行所有已注册的任务
        
        Returns:
            任务名称到结果列表的字典
        """
        print(f"▶ 执行 {len(self.tasks)} 个任务...")
        
        for task in self.tasks:
            self.execute_task(task)
        
        return self.task_results
    
    def list_tasks(self) -> List[str]:
        """
        列出所有已注册的任务
        
        Returns:
            任务名称列表
        """
        return [task.get_name() for task in self.tasks]
    
    # ========== 日志分析 API ==========
    
    def load_log_file(self, file_path: str):
        """
        加载日志文件
        
        Args:
            file_path: 日志文件路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"日志文件不存在: {file_path}")
        
        self.log_file_path = file_path
        print(f"✓ 已加载日志文件: {file_path}")
    
    def load_specification(self, spec_path: str):
        """
        加载规范文档到向量数据库
        
        Args:
            spec_path: 规范文档路径（文件或目录）
        """
        if os.path.isdir(spec_path):
            self.load_documents(spec_path)
        elif os.path.isfile(spec_path):
            with open(spec_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_text(content)
        else:
            raise ValueError(f"规范文档不存在: {spec_path}")
        
        print(f"✓ 规范文档已加载到知识库")
    
    def query_specification(self, query: str, top_k: int = 5) -> str:
        """
        查询规范文档

        Args:
            query: 查询内容
            top_k: 返回结果数量

        Returns:
            相关文档内容
        """
        return self.rag_engine.search(query, top_k=top_k)
    
    # ========== 报告生成 API ==========
    
    def generate_report(self, format: str = "markdown") -> str:
        """
        生成分析报告
        
        Args:
            format: 报告格式，支持 "text", "markdown", "json"
            
        Returns:
            报告内容
        """
        if format == "text":
            return self.reporter.generate_summary()
        elif format == "markdown":
            return self.reporter.generate_markdown_report()
        elif format == "json":
            return self.reporter.generate_json_report()
        else:
            raise ValueError(f"不支持的报告格式: {format}")
    
    def save_report(self, file_path: str, format: str = "markdown"):
        """
        保存报告到文件
        
        Args:
            file_path: 文件路径
            format: 报告格式
        """
        report = self.generate_report(format)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ 报告已保存: {file_path}")
    
    # ========== AI 辅助分析 API ==========
    
    def analyze_with_llm(self, prompt: str, use_rag: bool = True) -> str:
        """
        使用 LLM 进行辅助分析
        
        Args:
            prompt: 分析提示
            use_rag: 是否使用 RAG 查询规范文档
            
        Returns:
            LLM 的分析结果
        """
        return self.chat(prompt, use_rag=use_rag)
    
    def ask_about_log(self, question: str) -> str:
        """
        询问关于日志的问题
        
        Args:
            question: 问题
            
        Returns:
            LLM 的回答
        """
        if self.log_file_path:
            # 读取日志内容
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read(10000)  # 读取前 10000 字符
            
            prompt = f"""基于以下日志内容回答问题：

日志内容（部分）：
```
{log_content}
```

问题：{question}

回答："""
            return self.llm.invoke(prompt)
        else:
            return self.chat(question, use_rag=True)


__all__ = ["BitwiseAI"]
