# -*- coding: utf-8 -*-
"""
文档名匹配器

支持从查询中提取文档名关键词，并匹配相关文档
"""
import os
import re
from typing import List, Dict, Optional, Set
from ..vector_database import MilvusDB


class DocumentNameMatcher:
    """
    文档名匹配器
    
    从向量数据库加载所有文档名，建立索引，支持模糊匹配
    """
    
    def __init__(
        self,
        vector_db: MilvusDB,
        match_threshold: float = 0.3
    ):
        """
        初始化文档名匹配器
        
        Args:
            vector_db: 向量数据库实例
            match_threshold: 匹配阈值（0-1），表示至少需要匹配多少比例的关键词
        """
        self.vector_db = vector_db
        self.match_threshold = match_threshold
        
        # 文档名索引：{file_name: [source_file1, source_file2, ...]}
        self.file_name_index: Dict[str, List[str]] = {}
        
        # 文档名关键词索引：{keyword: Set[file_name]}
        self.keyword_index: Dict[str, Set[str]] = {}
        
        # 所有文档名列表
        self.all_file_names: List[str] = []
        
        # 是否已加载索引
        self._index_loaded = False
    
    def load_index(self) -> bool:
        """
        从向量数据库加载所有文档名，建立索引
        
        Returns:
            是否成功加载
        """
        if self._index_loaded:
            return True
        
        try:
            # 从向量数据库查询所有文档的唯一文档名
            # 使用Milvus的query功能获取所有文档的source_file和file_name
            query_result = self.vector_db.client.query(
                collection_name=self.vector_db.collection_name,
                filter="",  # 无过滤条件
                limit=10000,  # 限制查询数量
                output_fields=["source_file", "file_name", "file_name_keywords"]
            )
            
            if not query_result:
                self._index_loaded = True
                return True
            
            # 建立索引
            seen_files = set()
            for item in query_result:
                source_file = item.get("source_file", "")
                file_name = item.get("file_name", "")
                file_name_keywords = item.get("file_name_keywords", "")
                
                if not source_file or not file_name:
                    continue
                
                # 避免重复处理同一个文件
                if source_file in seen_files:
                    continue
                seen_files.add(source_file)
                
                # 添加到文档名索引
                if file_name not in self.file_name_index:
                    self.file_name_index[file_name] = []
                    self.all_file_names.append(file_name)
                
                if source_file not in self.file_name_index[file_name]:
                    self.file_name_index[file_name].append(source_file)
                
                # 建立关键词索引
                if file_name_keywords:
                    keywords = file_name_keywords.split()
                    for keyword in keywords:
                        if keyword not in self.keyword_index:
                            self.keyword_index[keyword] = set()
                        self.keyword_index[keyword].add(file_name)
            
            self._index_loaded = True
            print(f"✅ 文档名索引加载完成: {len(self.all_file_names)} 个文档, {len(self.keyword_index)} 个关键词")
            return True
            
        except Exception as e:
            print(f"⚠️  加载文档名索引失败: {e}")
            return False
    
    def extract_query_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 用户查询
        
        Returns:
            关键词列表
        """
        if not query:
            return []
        
        # 尝试使用jieba分词（如果可用）
        try:
            import jieba
            words = jieba.cut(query)
            # 过滤停用词和单字符
            stop_words = {
                '的', '是', '在', '有', '和', '与', '或', '但', '如果', '如何', 
                '什么', '哪个', '哪些', '吗', '呢', '吗', '了', '啊', '呀',
                '知道', '了解', '请问', '能否', '可以', '应该', '需要'
            }
            keywords = [w for w in words if w not in stop_words and len(w) > 1]
            return keywords
        except ImportError:
            # 如果没有jieba，使用简单方法
            # 移除标点符号
            text = re.sub(r'[^\w\s]', ' ', query)
            # 分割
            words = [w for w in text.split() if len(w) > 1]
            return words
    
    def match_documents(self, query: str) -> List[str]:
        """
        从查询中匹配文档名，返回匹配的source_file列表
        
        Args:
            query: 用户查询
        
        Returns:
            匹配的source_file列表（如果未匹配到，返回空列表）
        """
        # 确保索引已加载
        if not self._index_loaded:
            self.load_index()
        
        if not self.all_file_names:
            return []
        
        # 提取查询关键词
        query_keywords = self.extract_query_keywords(query)
        if not query_keywords:
            return []
        
        # 模糊匹配：查找包含查询关键词的文档名
        matched_file_names = set()
        
        query_lower = query.lower()
        
        # 方法0: 直接检查查询中的连续子串是否在文档名中（优先）
        # 这样可以匹配 "PE指令" 这样的连续组合
        for file_name in self.all_file_names:
            file_name_lower = file_name.lower()
            # 移除标点符号，保留中文、英文、数字
            query_clean = re.sub(r'[^\w\s]', '', query_lower)
            # 尝试匹配2-10个字符的连续子串
            for i in range(len(query_clean)):
                found = False
                for length in range(2, min(11, len(query_clean) - i + 1)):
                    substring = query_clean[i:i+length].strip()
                    if len(substring) >= 2 and substring in file_name_lower:
                        matched_file_names.add(file_name)
                        found = True
                        break
                if found:
                    break
        
        # 方法1: 直接匹配文档名（包含查询关键词）
        for file_name in self.all_file_names:
            file_name_lower = file_name.lower()
            # 检查文档名是否包含查询中的关键词
            if any(keyword.lower() in file_name_lower for keyword in query_keywords):
                matched_file_names.add(file_name)
        
        # 方法2: 通过关键词索引匹配
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            # 在关键词索引中查找
            for indexed_keyword, file_names in self.keyword_index.items():
                if keyword_lower in indexed_keyword.lower() or indexed_keyword.lower() in keyword_lower:
                    matched_file_names.update(file_names)
        
        # 方法3: 计算匹配度（至少匹配一定比例的关键词）
        if len(query_keywords) > 1:
            for file_name in self.all_file_names:
                file_name_keywords = self._get_file_name_keywords(file_name)
                if not file_name_keywords:
                    continue
                
                # 计算匹配的关键词数量
                matched_count = sum(1 for qk in query_keywords 
                                  if any(qk.lower() in fk.lower() or fk.lower() in qk.lower() 
                                        for fk in file_name_keywords))
                
                # 如果匹配的关键词比例超过阈值，则匹配
                match_ratio = matched_count / len(query_keywords)
                if match_ratio >= self.match_threshold:
                    matched_file_names.add(file_name)
        
        # 收集所有匹配的source_file
        matched_source_files = []
        for file_name in matched_file_names:
            if file_name in self.file_name_index:
                matched_source_files.extend(self.file_name_index[file_name])
        
        # 去重
        matched_source_files = list(set(matched_source_files))
        
        if matched_source_files:
            print(f"📄 匹配到 {len(matched_file_names)} 个文档: {', '.join([os.path.basename(f) for f in matched_source_files[:5]])}")
            if len(matched_source_files) > 5:
                print(f"   ... 共 {len(matched_source_files)} 个文件")
        
        return matched_source_files
    
    def _get_file_name_keywords(self, file_name: str) -> List[str]:
        """
        获取文档名的关键词列表
        
        Args:
            file_name: 文档名
        
        Returns:
            关键词列表
        """
        # 从索引中查找
        for keyword, file_names in self.keyword_index.items():
            if file_name in file_names:
                # 返回该文档名对应的所有关键词
                return [k for k, fns in self.keyword_index.items() if file_name in fns]
        
        # 如果索引中没有，使用简单分词
        return self.extract_query_keywords(file_name)
    
    def refresh_index(self) -> bool:
        """
        刷新索引（重新加载）
        
        Returns:
            是否成功刷新
        """
        self._index_loaded = False
        self.file_name_index.clear()
        self.keyword_index.clear()
        self.all_file_names.clear()
        return self.load_index()


__all__ = ["DocumentNameMatcher"]

