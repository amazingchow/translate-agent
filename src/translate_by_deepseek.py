import os
import re

from openai import OpenAI
from openai._exceptions import APIError as OpenAIAPIError

from retry_with_backoff import retry_with_exponential_backoff


@retry_with_exponential_backoff(
    initial_delay=1, exponential_base=1.2, jitter=True, max_retries=3, errors=(OpenAIAPIError,)
)
def generate_in_non_stream_mode(text: str) -> str:
    client = OpenAI(
        api_key=os.environ.get("ARK_API_KEY"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )

    completion = client.chat.completions.create(
        model="deepseek-r1-250528",
        messages=[
            {
                "role": "system",
                "content": """You are a highly skilled translator tasked with translating various types of content from other languages into Chinese. Follow these instructions carefully to complete the translation task:

## Input

Depending on the type of input, follow these specific instructions:

1. If the input is a URL:
First, request the built-in Action to retrieve the URL content. Once you have the content, proceed with the three-step translation process.

2. If the input is an image or PDF:
Get the content from image (by OCR) or PDF, and proceed with the three-step translation process.

3. Otherwise, proceed directly to the three-step translation process.

## Strategy

You will follow a three-step translation process:
1. Translate the input content into Chinese, respecting the original intent, keeping the original paragraph and text format unchanged, not deleting or omitting any content, including preserving all original Markdown elements like images, code blocks, etc.
2. Carefully read the source text and the translation, and then give constructive criticism and helpful suggestions to improve the translation. The final style and tone of the translation should match the style of 简体中文 colloquially spoken in China. When writing suggestions, pay attention to whether there are ways to improve the translation's
(i) accuracy (by correcting errors of addition, mistranslation, omission, or untranslated text),
(ii) fluency (by applying Chinese grammar, spelling and punctuation rules, and ensuring there are no unnecessary repetitions),
(iii) style (by ensuring the translations reflect the style of the source text and take into account any cultural context),
(iv) terminology (by ensuring terminology use is consistent and reflects the source text domain; and by only ensuring you use equivalent idioms Chinese).
3. Based on the results of steps 1 and 2, refine and polish the translation

## Glossary

Here is a glossary of technical terms to use consistently in your translations:

- AGI -> 通用人工智能
- LLM/Large Language Model -> 大语言模型
- Transformer -> Transformer
- Token -> Token
- Generative AI -> 生成式 AI
- AI Agent -> AI 智能体
- prompt -> 提示词
- zero-shot -> 零样本学习
- few-shot -> 少样本学习
- multi-modal -> 多模态
- fine-tuning -> 微调

## Output

For each step of the translation process, output your results within the appropriate XML tags:

<step1_initial_translation>
[Insert your initial translation here]
</step1_initial_translation>

<step2_reflection>
[Insert your reflection on the translation, write a list of specific, helpful and constructive suggestions for improving the translation. Each suggestion should address one specific part of the translation.]
</step2_reflection>

<step3_refined_translation>
[Insert your refined and polished translation here]
</step3_refined_translation>

Remember to consistently use the provided glossary for technical terms throughout your translation. Ensure that your final translation in step 3 accurately reflects the original meaning while sounding natural in Chinese.""",
            },
            {"role": "user", "content": text},
        ],
    )

    if not completion.choices[0].message.content:
        raise ValueError("翻译失败")
    return extract_refined_translation(completion.choices[0].message.content)


def extract_refined_translation(text: str) -> str:
    """Extract the refined translation from the response text.

    Args:
        text: The response text containing XML tags

    Returns:
        The content between <step3_refined_translation> tags
    """
    pattern = r"<step3_refined_translation>(.*?)</step3_refined_translation>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


if __name__ == "__main__":
    import time

    st = time.time()
    result = generate_in_non_stream_mode("""
## How we built our multi-agent research system

> Our Research feature uses multiple Claude agents to explore complex topics more effectively. We share the engineering challenges and the lessons we learned from building this system.

Claude now has [Research capabilities](https://www.anthropic.com/news/research) that allow it to search across the web, Google Workspace, and any integrations to accomplish complex tasks.

The journey of this multi-agent system from prototype to production taught us critical lessons about system architecture, tool design, and prompt engineering. A multi-agent system consists of multiple agents (LLMs autonomously using tools in a loop) working together. Our Research feature involves an agent that plans a research process based on user queries, and then uses tools to create parallel agents that search for information simultaneously. Systems with multiple agents introduce new challenges in agent coordination, evaluation, and reliability.

This post breaks down the principles that worked for us—we hope you'll find them useful to apply when building your own multi-agent systems. 
""")
    print(result)
    print(f"✅ 翻译耗时: {time.time() - st:.2f} 秒")
