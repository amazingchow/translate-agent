import os
import re
import time
from typing import List, Tuple

import fire

from translate_by_deepseek import generate_in_non_stream_mode as translate_by_deepseek

# --- 配置项 ---
MAX_CHUNK_SIZE = 100000


class TranslateAgent:
    """
    TranslateAgent is a class that translates a Markdown file into a bilingual format.
    """

    def run(self, file_path: str, keep_original: bool = False, output_path: str = None) -> None:
        try:
            with open(file_path, encoding="utf-8") as f:
                markdown_content = f.read()
        except FileNotFoundError:
            print(f"❌ 错误: 输入文件 {file_path} 不存在。")
            return
        if not output_path:
            output_path = file_path.replace(".md", "_zh_CN.md")
        print(f"✅ 开始翻译任务: {file_path} -> {output_path}")

        # 1. 按标题将文章分割成语义块
        sections = self.split_into_sections_by_headings(markdown_content)
        total_sections = len(sections)
        print(f"✅ 文章已按标题分割成 {total_sections} 个主要部分。")

        # 2. 遍历每个部分进行处理
        final_bilingual_parts = []
        for i, (heading, section_content) in enumerate(sections):
            print(
                f"🚧 正在处理 [{i + 1}/{total_sections}] 部分: \n 标题: {heading.strip() if heading else 'Preamble'}\n 内容: {section_content[:256]} ..."
            )

            # 翻译部分内容（此函数内部会处理代码块、表格、链接、图片、超长块）
            original_part = f"{heading}{section_content}"
            translated_section_content = self.process_and_translate_text_chunk(original_part)

            # 3. 组合成中英交替格式
            # final_bilingual_parts.append(original_part.strip())
            final_bilingual_parts.append(translated_section_content.strip())

        # 4. 写入输出文件
        final_content = "\n\n".join(final_bilingual_parts)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            print(f"\n🎉 翻译完成！结果已保存至: {output_path}")
            if not keep_original:
                os.remove(file_path)
        except OSError as e:
            print(f"❌ 错误: 无法写入文件 at {output_path}. Error: {e}")

    @staticmethod
    def split_into_sections_by_headings(markdown_content: str) -> List[Tuple[str, str]]:
        if not markdown_content.strip():
            return []

        # 正则表达式匹配以'#'开头的行 (标题), re.split会将分隔符也保留在列表中
        parts = re.split(r"(^#+ .*$)", markdown_content, flags=re.MULTILINE)

        sections = []
        # 第一个元素是文章开头到第一个标题前的内容
        if len(parts) > 0 and parts[0].strip():
            sections.append(("", parts[0]))

        # 从第二个元素开始，每两个元素组成一个 (标题, 内容) 对
        for i in range(1, len(parts), 2):
            heading = parts[i]
            section_content = parts[i + 1] if (i + 1) < len(parts) else ""
            sections.append((heading, section_content))

        return sections

    def process_and_translate_text_chunk(self, text_chunk: str) -> str:
        if not text_chunk.strip():
            return ""

        # 1. 分离出不需要翻译的内容
        parts = self.split_by_special_content(text_chunk)
        print(f"✅ 文本块已按特殊内容分割成 {len(parts)} 个部分。")

        translated_parts = []
        for part in parts:
            if not part.strip():
                continue

            # 检查是否是特殊内容（代码块、表格、图片）
            is_special_content = (
                part.startswith("```")  # 代码块
                or part.startswith("|")  # 表格
                or part.startswith("![")  # 图片
            )
            if is_special_content:
                # 特殊内容原样保留
                translated_parts.append(f"\n{part}\n")
                continue

            # 对于普通文本部分，进行大小检查和递归处理
            if len(part) <= MAX_CHUNK_SIZE:
                # 小于限制，直接翻译
                translated_parts.append(self.translate(part))
            else:
                # 块太大，需要进一步分割
                print(
                    f"  - [递归分割] 块大小为 {len(part)} 字符，超过限制（{MAX_CHUNK_SIZE} 个字符），需要进一步分割..."
                )
                raise ValueError(f"块大小为 {len(part)} 字符，超过限制（{MAX_CHUNK_SIZE} 个字符），需要进一步分割...")

        return "".join(translated_parts)

    @staticmethod
    def split_by_special_content(markdown_content: str) -> List[str]:
        if not markdown_content.strip():
            return []

        # 代码块 - 使用非贪婪匹配
        code_pattern = r"(```[\s\S]*?```)"
        # 表格 - 确保表格行之间有换行符
        table_pattern = r"(\|[^\n]*\|(?:\n\|[^\n]*\|)+)"
        # 图片 - 使用非贪婪匹配
        image_pattern = r"(!\[[^\]]*?\]\([^\)]+?\))"
        # 组合所有模式，使用非捕获组
        combined_pattern = f"(?:{code_pattern}|{table_pattern}|{image_pattern})"
        # 使用 re.split 保留分隔符
        parts = re.split(combined_pattern, markdown_content)
        # 过滤掉空字符串
        return [part for part in parts if part]

    def translate(self, content: str) -> str:
        if not content.strip():
            return ""
        st = time.time()
        result = translate_by_deepseek(content)
        print(f"✅ 翻译耗时: {time.time() - st:.2f} 秒")
        return result


if __name__ == "__main__":
    fire.Fire(TranslateAgent)
