import re
import ast
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from backend.config.logger import logger

@dataclass
class RawChunk:
    chunk_type: str
    name: Optional[str]
    start_line: int
    end_line: int
    parent_scope: Optional[str]
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class ASTParser:
    def __init__(self):
        self.treesitter_available = False
        try:
            import tree_sitter
            import tree_sitter_languages
            self.ts = tree_sitter
            self.ts_langs = tree_sitter_languages
            self.treesitter_available = True
            logger.info("Tree-sitter AST parser loaded successfully.")
        except Exception as e:
            logger.warning(f"Tree-sitter native bindings uninitialized, utilizing AST/Regex fallback: {e}")

    def parse_file(self, content: str, file_path: str, language: str) -> List[RawChunk]:
        if not content.strip():
            return []

        chunks: List[RawChunk] = []

        if language.lower() == "python":
            chunks = self._parse_python_ast(content, file_path)
            if chunks:
                return chunks
        
        if self.treesitter_available:
            try:
                chunks = self._parse_treesitter(content, file_path, language)
                if chunks:
                    return chunks
            except Exception as e:
                logger.warning(f"Tree-sitter parsing error for {file_path}: {e}")

        return self._parse_regex_fallback(content, file_path, language)

    def _parse_python_ast(self, content: str, file_path: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        try:
            tree = ast.parse(content)
            lines = content.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start + 20)
                    chunk_content = "\n".join(lines[start - 1 : end])
                    chunks.append(
                        RawChunk(
                            chunk_type="class",
                            name=node.name,
                            start_line=start,
                            end_line=end,
                            parent_scope=None,
                            content=chunk_content
                        )
                    )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start + 15)
                    parent_class = None
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef) and hasattr(node, 'lineno'):
                            if parent.lineno <= node.lineno <= getattr(parent, 'end_lineno', parent.lineno + 100):
                                parent_class = parent.name
                                break
                    chunk_content = "\n".join(lines[start - 1 : end])
                    chunks.append(
                        RawChunk(
                            chunk_type="method" if parent_class else "function",
                            name=node.name,
                            start_line=start,
                            end_line=end,
                            parent_scope=parent_class,
                            content=chunk_content
                        )
                    )
        except Exception as e:
            logger.debug(f"Python AST parse failed for {file_path}: {e}")
        return chunks

    def _parse_treesitter(self, content: str, file_path: str, language: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lang_map = {
            "python": "python",
            "javascript": "javascript",
            "typescript": "typescript",
            "java": "java",
            "go": "go",
            "rust": "rust",
            "cpp": "cpp",
            "c": "c"
        }
        ts_lang_name = lang_map.get(language.lower())
        if not ts_lang_name:
            return []

        lang = self.ts_langs.get_language(ts_lang_name)
        parser = self.ts_langs.get_parser(ts_lang_name)
        tree = parser.parse(bytes(content, "utf8"))
        lines = content.splitlines()

        def traverse(node, parent_name=None):
            node_type = node.type
            if node_type in ("class_declaration", "class_definition", "struct_specifier", "interface_declaration"):
                start = node.start_point[0] + 1
                end = node.end_point[0] + 1
                name = None
                for child in node.children:
                    if child.type in ("identifier", "type_identifier", "name"):
                        name = content[child.start_byte:child.end_byte]
                        break
                chunk_content = "\n".join(lines[start - 1 : end])
                chunks.append(RawChunk(
                    chunk_type="class" if "class" in node_type else "struct",
                    name=name,
                    start_line=start,
                    end_line=end,
                    parent_scope=parent_name,
                    content=chunk_content
                ))
                for child in node.children:
                    traverse(child, parent_name=name)
                return

            elif node_type in ("function_declaration", "function_definition", "method_definition", "arrow_function"):
                start = node.start_point[0] + 1
                end = node.end_point[0] + 1
                name = None
                for child in node.children:
                    if child.type in ("identifier", "property_identifier", "name"):
                        name = content[child.start_byte:child.end_byte]
                        break
                chunk_content = "\n".join(lines[start - 1 : end])
                chunks.append(RawChunk(
                    chunk_type="method" if parent_name else "function",
                    name=name,
                    start_line=start,
                    end_line=end,
                    parent_scope=parent_name,
                    content=chunk_content
                ))
                return

            for child in node.children:
                traverse(child, parent_name)

        traverse(tree.root_node)
        return chunks

    def _parse_regex_fallback(self, content: str, file_path: str, language: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lines = content.splitlines()
        
        func_pattern = re.compile(r'^\s*(async\s+)?(def|function|fn|pub fn|func|class|interface|type)\s+([A-Za-z0-9_]+)')

        current_name = None
        current_type = "code_block"
        start_line = 1

        for i, line in enumerate(lines, 1):
            match = func_pattern.search(line)
            if match:
                kw = match.group(2)
                name = match.group(3)
                chunk_type = "class" if kw in ("class", "interface", "type") else "function"
                
                if current_name and (i - start_line >= 3):
                    chunk_content = "\n".join(lines[start_line - 1 : i - 1])
                    chunks.append(RawChunk(
                        chunk_type=current_type,
                        name=current_name,
                        start_line=start_line,
                        end_line=i - 1,
                        parent_scope=None,
                        content=chunk_content
                    ))

                start_line = i
                current_name = name
                current_type = chunk_type

        if current_name or lines:
            end_line = len(lines)
            chunk_content = "\n".join(lines[start_line - 1 : end_line])
            if chunk_content.strip():
                chunks.append(RawChunk(
                    chunk_type=current_type if current_name else "file",
                    name=current_name or file_path.split("/")[-1],
                    start_line=start_line,
                    end_line=end_line,
                    parent_scope=None,
                    content=chunk_content
                ))

        return chunks
