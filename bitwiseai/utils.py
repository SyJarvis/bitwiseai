# -*- coding: utf-8 -*-
"""
工具函数：文档加载和文本切分
"""
import os
import re
import time
import hashlib
from typing import List, Dict, Optional, Any
from PyPDF2 import PdfReader


class DocumentLoader:
    """
    文档加载器

    支持加载 txt, md, pdf 格式的文件
    """

    def __init__(self):
        self.supported_formats = ["txt", "md", "pdf"]

    def load_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        加载文件夹中的所有文档

        Args:
            folder_path: 文件夹路径

        Returns:
            文档对象列表，每个对象包含：
                - content: 文档内容
                - file_path: 文件路径
                - file_hash: 文件哈希值
                - file_size: 文件大小
                - timestamp: 加载时间戳
        """
        if not os.path.exists(folder_path):
            raise ValueError(f"文件夹不存在: {folder_path}")

        documents = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = file.split(".")[-1].lower()

                if ext in self.supported_formats:
                    try:
                        content = self.load_file(file_path)
                        if content:
                            # 计算文件哈希
                            file_hash = self._calculate_file_hash(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            documents.append({
                                "content": content,
                                "file_path": file_path,
                                "file_hash": file_hash,
                                "file_size": file_size,
                                "timestamp": time.time()
                            })
                    except Exception as e:
                        print(f"⚠️  加载文件失败 {file_path}: {e}")

        return documents

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件内容的哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的SHA256哈希值
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"⚠️  计算文件哈希失败 {file_path}: {e}")
            return ""

    def load_file(self, file_path: str) -> Optional[str]:
        """
        加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        ext = file_path.split(".")[-1].lower()

        if ext == "pdf":
            return self._load_pdf(file_path)
        elif ext in ["txt", "md"]:
            return self._load_text(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def _load_pdf(self, file_path: str) -> str:
        """加载 PDF 文件"""
        reader = PdfReader(file_path)
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        return "\n".join(text_content)

    def _load_text(self, file_path: str) -> str:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class TextSplitter:
    """
    文本切分器

    基于句子和段落的智能切分
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        初始化文本切分器

        Args:
            chunk_size: 每个文本块的最大字符数
            chunk_overlap: 文本块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 中文句子分隔符
        self._chinese_separators = ['。', '！', '？', '；', '：']
        # 英文句子分隔符
        self._english_separators = ['.', '!', '?', ';', ':']

    def split(self, text: str) -> List[str]:
        """
        切分文本

        Args:
            text: 输入文本

        Returns:
            切分后的文本块列表
        """
        if not text or not isinstance(text, str):
            return []

        # 按段落切分
        paragraphs = self._split_by_paragraphs(text)

        # 合并并按 chunk_size 切分
        chunks = self._merge_and_split(paragraphs)

        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落切分"""
        # 按空行分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子切分"""
        if not text:
            return []

        sentences = []
        current_sentence = ""

        for char in text:
            current_sentence += char

            # 检查是否是分隔符
            is_separator = (char in self._chinese_separators or
                          char in self._english_separators)

            if is_separator:
                sentences.append(current_sentence.strip())
                current_sentence = ""

        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        return [s for s in sentences if s]

    def _merge_and_split(self, paragraphs: List[str]) -> List[str]:
        """合并段落并按 chunk_size 切分"""
        if not paragraphs:
            return []

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # 如果段落超过 chunk_size，按句子切分
            if len(paragraph) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = ""

                sentences = self._split_by_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
            else:
                # 检查添加段落后是否会超出 chunk_size
                if len(current_chunk) + len(paragraph) + 1 <= self.chunk_size:
                    current_chunk += (" " if current_chunk else "") + paragraph
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


__all__ = ["DocumentLoader", "TextSplitter"]
