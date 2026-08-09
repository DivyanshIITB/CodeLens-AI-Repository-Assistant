import pytest
from backend.parser.ast_parser import ASTParser
from backend.parser.chunker import CodeChunker

def test_ast_parser_python():
    parser = ASTParser()
    code = """
class AuthHandler:
    def login(self, username, password):
        return True

def generate_token():
    return "secret"
"""
    chunks = parser.parse_file(code, "auth.py", "python")
    assert len(chunks) >= 2
    types = [c.chunk_type for c in chunks]
    assert "class" in types or "function" in types or "method" in types

def test_code_chunker():
    chunker = CodeChunker()
    code = "def sample():\n    print('hello world')\n"
    final_chunks = chunker.create_chunks(code, "test.py", "python", "TestRepo")
    assert len(final_chunks) >= 1
    assert "Repository: TestRepo" in final_chunks[0]["content"]
    assert "File: test.py" in final_chunks[0]["content"]
