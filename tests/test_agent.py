import pytest

from agent import TranslateAgent


@pytest.fixture
def agent():
    return TranslateAgent()


def test_only_content_no_headings(agent):
    """Test content without any headings"""
    content = "This is some content\nwithout any headings."
    result = agent.split_into_sections_by_headings(content)
    assert len(result) == 1
    assert result[0] == ("", content)


def test_single_heading_with_content(agent):
    """Test single heading with content"""
    content = "# Heading 1\nSome content here"
    result = agent.split_into_sections_by_headings(content)
    assert len(result) == 1
    assert result[0] == ("# Heading 1", "\nSome content here")


def test_multiple_headings(agent):
    """Test multiple headings with content"""
    content = """# Heading 1
Content 1

## Heading 2
Content 2

### Heading 3
Content 3"""
    result = agent.split_into_sections_by_headings(content)
    assert len(result) == 3
    assert result[0] == ("# Heading 1", "\nContent 1\n\n")
    assert result[1] == ("## Heading 2", "\nContent 2\n\n")
    assert result[2] == ("### Heading 3", "\nContent 3")


def test_content_before_first_heading(agent):
    """Test content that appears before the first heading"""
    content = """Some preamble text
# First Heading
Content after heading"""
    result = agent.split_into_sections_by_headings(content)
    assert len(result) == 2
    assert result[0] == ("", "Some preamble text\n")
    assert result[1] == ("# First Heading", "\nContent after heading")


def test_nested_headings(agent):
    """Test nested headings with different levels"""
    content = """# Main Heading
Main content

## Sub Heading
Sub content

### Sub Sub Heading
Sub sub content"""
    result = agent.split_into_sections_by_headings(content)
    assert len(result) == 3
    assert result[0] == ("# Main Heading", "\nMain content\n\n")
    assert result[1] == ("## Sub Heading", "\nSub content\n\n")
    assert result[2] == ("### Sub Sub Heading", "\nSub sub content")


def test_empty_text(agent):
    """测试空文本"""
    result = agent.split_by_special_content("")
    assert result == []


def test_plain_text(agent):
    """测试纯文本"""
    text = "这是一段普通文本"
    result = agent.split_by_special_content(text)
    assert result == [text]


def test_code_block(agent):
    """测试代码块"""
    text = """这是一段文本
```python
def hello():
    print("Hello")
```
这是另一段文本"""
    result = agent.split_by_special_content(text)
    assert len(result) == 3
    assert result[0] == "这是一段文本\n"
    assert result[1] == '```python\ndef hello():\n    print("Hello")\n```'
    assert result[2] == "\n这是另一段文本"


def test_table(agent):
    """测试表格"""
    text = """文本开始
| 标题1 | 标题2 |
|-------|-------|
| 内容1 | 内容2 |
文本结束"""
    result = agent.split_by_special_content(text)
    assert len(result) == 3
    assert result[0] == "文本开始\n"
    assert result[1] == "| 标题1 | 标题2 |\n|-------|-------|\n| 内容1 | 内容2 |"
    assert result[2] == "\n文本结束"


def test_image(agent):
    """测试图片"""
    text = "这是一张![图片](image.jpg)在文本中"
    result = agent.split_by_special_content(text)
    assert len(result) == 3
    assert result[0] == "这是一张"
    assert result[1] == "![图片](image.jpg)"
    assert result[2] == "在文本中"


def test_mixed_content(agent):
    """测试混合内容"""
    text = """开始文本
```python
print("代码")
```
| 表格 |
|------|
| 内容 |
这是一个[链接](url)和![图片](img.jpg)
结束文本"""
    result = agent.split_by_special_content(text)
    assert len(result) == 7
    assert result[0] == "开始文本\n"
    assert result[1] == '```python\nprint("代码")\n```'
    assert result[2] == "\n"
    assert result[3] == "| 表格 |\n|------|\n| 内容 |"
    assert result[4] == "\n这是一个[链接](url)和"
    assert result[5] == "![图片](img.jpg)"
    assert result[6] == "\n结束文本"


def test_nested_content(agent):
    """测试嵌套内容"""
    text = """开始
```markdown
| 表格中的表格 |
|-------------|
| 内容        |
```
结束"""
    result = agent.split_by_special_content(text)
    assert len(result) == 3
    assert result[0] == "开始\n"
    assert result[1] == "```markdown\n| 表格中的表格 |\n|-------------|\n| 内容        |\n```"
    assert result[2] == "\n结束"


def test_multiple_special_content(agent):
    """测试多个连续的特殊内容"""
    text = """开始
[链接1](url1)和![图片1](img1)和[链接2](url2)和![图片2](img2)
结束"""
    result = agent.split_by_special_content(text)
    assert len(result) == 5
    assert result[0] == "开始\n[链接1](url1)和"
    assert result[1] == "![图片1](img1)"
    assert result[2] == "和[链接2](url2)和"
    assert result[3] == "![图片2](img2)"
    assert result[4] == "\n结束"
