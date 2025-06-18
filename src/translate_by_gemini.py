import os
import re

from google import genai
from google.genai import types
from google.genai.errors import APIError as GenAIAPIError

from retry_with_backoff import retry_with_exponential_backoff


@retry_with_exponential_backoff(
    initial_delay=1, exponential_base=1.2, jitter=True, max_retries=3, errors=(GenAIAPIError,)
)
def generate_in_non_stream_mode(text: str) -> str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-1.5-flash-8b"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(
                text="""You are a highly skilled translator tasked with translating various types of content from other languages into Chinese. Follow these instructions carefully to complete the translation task:

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

Remember to consistently use the provided glossary for technical terms throughout your translation. Ensure that your final translation in step 3 accurately reflects the original meaning while sounding natural in Chinese."""
            ),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    if not response.text:
        raise ValueError("翻译失败")
    return extract_refined_translation(response.text)


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
How many GPUs do I need to be able to serve Llama 70B? In order to answer that, you need to know how much GPU memory will be required by the Large Language Model.

The formula is simple:

```
M = \frac{(P * 4B)}{\left(\frac{32}{Q}\right)} * 1.2
```

| Symbol | Description |
|--------|-------------|
| M | GPU memory expressed in Gigabyte |
| P | The amount of parameters in the model. E.g. a 7B model has 7 billion parameters |
| 4B | 4 bytes, expressing the bytes used for each parameter |
| 32 | There are 32 bits in 4 bytes |
| Q | The amount of bits that should be used for loading the model. E.g. 16 bits, 8 bits or 4 bits |
| 1.2 | Represents a 20% overhead of loading additional things in GPU memory |

Looking to deploy LLMs on Kubernetes? Check out KubeAI, providing private Open AI on Kubernetes.

Now let's try out some examples.

### GPU memory required for serving Llama 70B

Let's try it out for Llama 70B that we will load in 16 bit. The model has 70 billion parameters.

```
\frac{70 * 4\text{bytes}}{32/16} * 1.2 = 168\text{GB}
```

That's quite a lot of memory. A single A100 80GB wouldn't be enough, although 2x A100 80GB should be enough to serve the Llama 2 70B model in 16 bit mode.

**How to further reduce GPU memory required for Llama 2 70B?**

Quantization is a method to reduce the memory footprint. Quantization is able to do this by reducing the precision of the model's parameters from floating-point to lower-bit representations, such as 8-bit integers. This process significantly decreases the memory and computational requirements, enabling more efficient deployment of the model, particularly on devices with limited resources. However, it requires careful management to maintain the model's performance, as reducing precision can potentially impact the accuracy of the outputs.

In general, the consensus seems to be that 8 bit quantization achieves similar performance to using 16 bit. However, 4 bit quantization could have a noticeable impact to the model performance.

Let's do another example where we use **4 bit quantization of Llama 2 70B:**

```
\frac{70 * 4\text{bytes}}{32/4} * 1.2 = 42\text{GB}
```

This is something you could run on 2 x L4 24GB GPUs.
""")
    print(result)
    print(f"✅ 翻译耗时: {time.time() - st:.2f} 秒")
