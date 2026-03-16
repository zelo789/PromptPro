"""
需求文档模块

支持自定义需求文档功能，用于记录项目/任务的背景和调优要求。
文档使用 Markdown 格式存储，包含 name/intro/tune 字段。
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import re
import os

from src.exceptions import RequirementError, ErrorCode


@dataclass
class RequirementDoc:
    """需求文档数据模型"""
    name: str           # 文档名称
    intro: str          # 背景介绍
    tune: str           # 调优要求
    file_path: str      # 文件路径
    updated_at: str     # 更新时间


class RequirementParser:
    """需求文档解析器"""

    @staticmethod
    def parse_file(file_path: str) -> RequirementDoc:
        """解析 .md 文件

        Args:
            file_path: 文件路径

        Returns:
            RequirementDoc 对象

        Raises:
            RequirementError: 文件读取或解析失败
        """
        path = Path(file_path)
        if not path.exists():
            raise RequirementError(
                f"文档不存在: {file_path}",
                error_code=ErrorCode.REQUIREMENT_NOT_FOUND,
            )

        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            raise RequirementError(
                f"读取文档失败: {e}",
                error_code=ErrorCode.REQUIREMENT_READ_FAILED,
                details=str(e),
            )

        return RequirementParser.parse_content(content, file_path)

    @staticmethod
    def parse_content(content: str, file_path: str = "") -> RequirementDoc:
        """解析文本内容

        Args:
            content: 文档内容
            file_path: 文件路径（用于记录）

        Returns:
            RequirementDoc 对象
        """
        fields = RequirementParser._extract_fields(content)

        # 验证必要字段
        if 'name' not in fields:
            raise RequirementError(
                "文档缺少 'name' 字段",
                error_code=ErrorCode.REQUIREMENT_INVALID,
            )

        # 获取更新时间
        updated_at = ""
        if file_path:
            try:
                stat = Path(file_path).stat()
                updated_at = str(stat.st_mtime)
            except Exception:
                pass

        return RequirementDoc(
            name=fields.get('name', ''),
            intro=fields.get('intro', ''),
            tune=fields.get('tune', ''),
            file_path=file_path,
            updated_at=updated_at,
        )

    @staticmethod
    def _extract_fields(content: str) -> dict:
        """提取字段（支持多行块）

        支持两种格式：
        1. 单行格式: name: 值
        2. 多行块格式:
           name: |
             多行内容
        """
        fields = {}

        # 匹配多行块格式 (field: | 后跟缩进内容)
        multiline_pattern = r'^(\w+):\s*\|\s*\n((?:[ \t]+.*\n?)*)'
        for match in re.finditer(multiline_pattern, content, re.MULTILINE):
            field_name = match.group(1).lower()
            field_value = match.group(2)
            # 移除公共缩进
            lines = field_value.strip().split('\n')
            if lines:
                # 计算最小缩进
                min_indent = min(
                    len(line) - len(line.lstrip())
                    for line in lines
                    if line.strip()
                )
                # 移除缩进
                field_value = '\n'.join(
                    line[min_indent:] if len(line) > min_indent else line.lstrip()
                    for line in lines
                )
            fields[field_name] = field_value.strip()

        # 移除已匹配的多行块，再匹配单行格式
        remaining = re.sub(multiline_pattern, '', content, flags=re.MULTILINE)
        singleline_pattern = r'^(\w+):\s*(.+)$'
        for match in re.finditer(singleline_pattern, remaining, re.MULTILINE):
            field_name = match.group(1).lower()
            if field_name not in fields:  # 不覆盖多行格式的值
                fields[field_name] = match.group(2).strip()

        return fields


class RequirementManager:
    """需求文档管理器"""

    def __init__(self, prompts_dir: str = "prompts"):
        """初始化管理器

        Args:
            prompts_dir: 需求文档目录
        """
        self.prompts_dir = Path(prompts_dir)
        self._current_doc: Optional[RequirementDoc] = None
        self._docs_cache: Optional[List[RequirementDoc]] = None

    def discover_docs(self) -> List[RequirementDoc]:
        """发现 prompts/ 目录下的所有文档

        Returns:
            文档列表
        """
        if not self.prompts_dir.exists():
            self._docs_cache = []
            return []

        docs = []
        for md_file in self.prompts_dir.glob("*.md"):
            try:
                doc = RequirementParser.parse_file(str(md_file))
                docs.append(doc)
            except RequirementError as e:
                # 跳过解析失败的文档，但记录日志
                pass

        self._docs_cache = docs
        return docs

    def list_docs(self) -> List[dict]:
        """列出文档基本信息

        Returns:
            文档信息列表 [{'name': ..., 'file': ..., 'preview': ...}, ...]
        """
        docs = self.discover_docs() if self._docs_cache is None else self._docs_cache

        result = []
        for doc in docs:
            # 生成预览（前 50 字符，移除换行符）
            intro_clean = doc.intro.replace('\n', ' ').strip()
            preview = intro_clean[:50] + "..." if len(intro_clean) > 50 else intro_clean
            result.append({
                'name': doc.name,
                'file': Path(doc.file_path).stem,
                'preview': preview,
            })

        return result

    def load_doc(self, file_identifier: str) -> RequirementDoc:
        """加载指定文档

        Args:
            file_identifier: 文件名（不含扩展名）或完整路径

        Returns:
            RequirementDoc 对象

        Raises:
            RequirementError: 文档不存在或解析失败
        """
        # 判断是否为完整路径
        if Path(file_identifier).is_absolute() or file_identifier.endswith('.md'):
            file_path = file_identifier
        else:
            # 作为文件名处理，添加 .md 扩展名
            file_path = self.prompts_dir / f"{file_identifier}.md"

        doc = RequirementParser.parse_file(str(file_path))
        return doc

    def select_doc(self, file_identifier: str) -> RequirementDoc:
        """选择并设为当前文档

        Args:
            file_identifier: 文件名（不含扩展名）或完整路径

        Returns:
            选中的 RequirementDoc 对象
        """
        doc = self.load_doc(file_identifier)
        self._current_doc = doc
        return doc

    def get_current_doc(self) -> Optional[RequirementDoc]:
        """获取当前选中的文档

        Returns:
            当前文档，未选中则返回 None
        """
        return self._current_doc

    def clear_current_doc(self) -> None:
        """清除当前文档"""
        self._current_doc = None

    def create_doc(self, name: str, intro: str, tune: str, filename: Optional[str] = None) -> str:
        """创建新文档

        Args:
            name: 文档名称
            intro: 背景介绍
            tune: 调优要求
            filename: 文件名（不含扩展名），不指定则使用 name

        Returns:
            创建的文件路径
        """
        # 确保目录存在
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if not filename:
            # 从 name 生成安全的文件名
            filename = re.sub(r'[^\w\u4e00-\u9fff-]', '_', name)
            filename = filename.strip('_') or "untitled"

        file_path = self.prompts_dir / f"{filename}.md"

        # 生成内容
        content = f"""name: {name}
intro: |
  {intro.replace(chr(10), chr(10) + '  ')}
tune: |
  {tune.replace(chr(10), chr(10) + '  ')}
"""

        # 写入文件
        file_path.write_text(content, encoding='utf-8')

        # 刷新缓存
        self._docs_cache = None

        return str(file_path)


# 全局管理器实例
global_manager = RequirementManager()


def get_requirement_manager() -> RequirementManager:
    """获取全局需求文档管理器"""
    return global_manager