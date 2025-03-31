import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 替换为你的API密钥或配置环境变量
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def generate_presentation_summary(input_text: str, lang: str = "zh") -> str:

    prompt_zh=f"""
    【系统角色设定】
    你是一位资深学术报告专家，正在准备国际顶会级别的论文汇报PPT。需要从研究论文中精准提取核心信息，并按照学术演讲的最佳实践进行结构化重组。请严格按照下面示例演示的格式进行输出。

    【输入输出格式】
    输入：一个或多个论文段落
    输出：
    [分点数量]
    [提到图的标号] 
    [提到表的标号]
    ◆ 内容要点（技术核心、创新突破、实证结果等）
    ◆ 内容要点2（如果有）
    ...
    （根据实际内容动态增减）
    内容一共在一百五十字到三百字之间

    【核心处理规则】
    1. 信息密度优先原则：
    - 保留段落中以下要素：
        ✓ 方法论创新点（标记"首次""提出""改进"等关键词）
        ✓ 量化指标（匹配\d+\.\d+%、p<0.\d+等模式）
        ✓ 技术对比（SOTA方法、baseline）
    - 弱化处理：
        × 背景介绍（如"近年来..."开头的描述）
        × 基础理论复述（教科书已有内容）
        × 重复性实验细节

    2. 多要点分离策略：
    if 文本包含提到了多个要点，并且内容相对独立；或者提到了多个例子，则进行分点描述，但是不进行不必要的分点。
        一定要输出分点数量，放置在输出的最前方（如"3"）
        不同分点直接使用换行符隔离。
        如果原文是连续而非并列的关系，则不需要进行分点。

    3. 学术表达规范：
    - 保留原始术语（英文技术名词缩写直接保留,其余翻译）
    - 保证语言的连贯性
    - 公式处理：$f(x)=w^Tx+b$ → f(x) = w^T x + b
    - 图表引用：Fig.3所示 → (见图3)
    4. 文本段落的截取和识别可能存在误差；如果段落起始或结束的地方有独立、不完整的句子，与段落主体含义不同的话，将其丢弃。
    5. 图表标号：
        将涉及到的图表标号括在中括号中以数组形式输出。


    【示例演示】
    输入段落：
    4.1 Prerequisites and Threat Model FUZZWARE has the following prerequisites and threat model:Prerequisites. FUZZWARE shares two basic prerequisites with all other re-hosting systems: First, we assume that we are able to obtain a binary firmware image for the target device. Second, just like other re-hosting systems, we assume
    basic memory mappings such as RAM ranges and the broad MMIO space to be provided. Depending on the target CPU architecture, these generic ranges may be standardized [1]. Threat Model. Given no additional knowledge about the
    specific hardware environment of a given binary firmware image, we assume during fuzzing that an attacker is able to control the inputs provided to the firmware. Commonly, these inputs may correspond to the contents of an incoming
    network packet read via MMIO, data received via a serial interface, or sensory data such as temperature measurements. We analyze situations where an attacker has less control over hardware-generated values in figure 4.

    处理输出：
    2
    [4]
    []
    前提条件与威胁模型
    ◆ 前提条件：必须获得目标设备的完整固件二进制文件，同时需要预定义的关键内存区域和不同CPU架构的标准化内存映射规范。
    ◆ 威胁模型：攻击者具有完全控制固件输入源的能力，例如通过网络数据包、串行接口或传感器数据。


    【特殊处理协议】
    当遇到：
    1. 段落无明显技术要点 → 进行概括
    2. 存在矛盾陈述 → 标记"[数据冲突] 需原文核对"
    3. 多个弱关联子点 → 启用重要性排序（保留前4个）
    """

    prompt_en=f"""
    【System Role Setting】
    You are a senior academic presentation expert preparing for top-tier international conference presentations. Your task is to extract core information from research papers and restructure it according to best practices for academic presentations. Maintain strict adherence to the output format shown in examples.

    【Input/Output Format】
    Input: One or multiple paper paragraphs
    Output:
    [Number of key points]
    [Figure numbers mentioned]
    [Table numbers mentioned]
    Presentation Title
    ◆ Key Point 1 (Technical core/Innovation/Empirical results)
    ◆ Key Point 2 (if applicable)
    ...
    (Adjust dynamically based on content)
    Total length: 150-300 words

    【Core Processing Rules】
    1. Information Density Priority:
    - Preserve:
        ✓ Methodological innovations (markers: "first", "proposed", "improved")
        ✓ Quantitative metrics (patterns: \d+\.\d+%, p<0.\d+)
        ✓ Technical comparisons (SOTA methods, baselines)
    - Deprioritize:
        × Background descriptions (e.g., "In recent years...")
        × Textbook theory recitations
        × Repetitive experimental details

    2. Multi-point Separation Strategy:
    if text contains multiple independent points OR distinct examples:
        → Lead with point count (e.g., "3")
        → Separate points with line breaks
        → Avoid unnecessary fragmentation for continuous content

    3. Academic Style Guidelines:
    - Preserve original terminology (retain English technical terms)
    - Maintain linguistic coherence
    - Formula handling: $f(x)=w^Tx+b$ → f(x) = w^T x + b
    - Figure/table references: Fig.3 → (Fig.3)

    4. There may be inaccuracies in text paragraph extraction and recognition; if there are standalone, incomplete sentences at the beginning or end of a paragraph that differ from the main meaning of the paragraph, discard them.

    5. Reference Numbering:
    - Enclose figure/table numbers in square brackets

    【Example Demonstration】
    Input Paragraph:
    4.1 Prerequisites and Threat Model FUZZWARE has the following prerequisites and threat model:Prerequisites. FUZZWARE shares two basic prerequisites with all other re-hosting systems: First, we assume that we are able to obtain a binary firmware image for the target device. Second, just like other re-hosting systems, we assume basic memory mappings such as RAM ranges and the broad MMIO space to be provided. Depending on the target CPU architecture, these generic ranges may be standardized [1]. Threat Model. Given no additional knowledge about the specific hardware environment of a given binary firmware image, we assume during fuzzing that an attacker is able to control the inputs provided to the firmware. Commonly, these inputs may correspond to the contents of an incoming network packet read via MMIO, data received via a serial interface, or sensory data such as temperature measurements. We analyze situations where an attacker has less control over hardware-generated values in figure 4.

    Output:
    2
    [4]
    []
    Prerequisites and Threat Model
    ◆ Prerequisites: Requires obtaining complete firmware binaries and predefined memory mappings (RAM/MMIO), with architecture-dependent standardization [1]
    ◆ Threat Assumptions: Adversaries control all firmware inputs (network packets, serial data, sensors) with limited hardware value control (see Fig.4)

    【Special Protocols】
    1. No technical content → Generate conceptual summary
    2. Contradictory statements → Mark "[Data Conflict] Requires source verification"
    3. Multiple weak-related points → Priority sorting (keep top 3)

    【Language Enforcement】
    - Technical terms: Maintain original English terms (e.g., MMIO, SOTA)
    - Measurement units: Use international standards (MHz, kB/s)
    - Acronyms: Spell out at first occurrence (e.g., MMIO (Memory-Mapped I/O))

    """
    prompt={'en':prompt_en,'zh':prompt_zh}
    # 校验语言参数有效性
    if lang not in prompt:
        raise ValueError(f"Unsupported language option: {lang}. Valid options are {list(prompt.keys())}")
    
    # 构建对话消息
    messages = [
        {"role": "system", "content": prompt[lang]},
        {"role": "user", "content": input_text}
    ]
    
    # 调用大模型API
    completion = client.chat.completions.create(
        model="qwq-32b",
        messages=messages,
        modalities=["text"],
        stream=True,
        stream_options={"include_usage": True},
    )
    
    # 收集流式响应内容
    response_content = []
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            response_content.append(chunk.choices[0].delta.content)
    
    return "".join(response_content)




def generate_with_feedback(
    input_text: str,
    user_feedback: str = None,
    lang: str = "zh",
    temperature: float = 0.3,
    presence_penalty: float = 0.2
) -> str:

    # 构建消息链
    prompt_zh=f"""
    【系统角色设定】
    你是一位资深学术报告专家，正在准备国际顶会级别的论文汇报PPT。需要从研究论文中精准提取核心信息，并按照学术演讲的最佳实践进行结构化重组。请严格按照下面示例演示的格式进行输出。

    【输入输出格式】
    输入：一个或多个论文段落
    输出：
    内容要点（技术核心、创新突破、实证结果等）
    内容要点2（如果有）
    ...
    （根据实际内容动态增减）
    内容一共在一百五十字到三百字之间

    【核心处理规则】
    1. 信息密度优先原则：
    - 保留段落中以下要素：
        ✓ 方法论创新点（标记"首次""提出""改进"等关键词）
        ✓ 量化指标（匹配\d+\.\d+%、p<0.\d+等模式）
        ✓ 技术对比（SOTA方法、baseline）
    - 弱化处理：
        × 背景介绍（如"近年来..."开头的描述）
        × 基础理论复述（教科书已有内容）
        × 重复性实验细节

    2. 多要点分离策略：
    if 文本包含提到了多个要点，并且内容相对独立；或者提到了多个例子，则进行分点描述，但是不进行不必要的分点。
        一定要输出分点数量，放置在输出的最前方（如"3"）
        不同分点直接使用换行符隔离。
        如果原文是连续而非并列的关系，则不需要进行分点。

    3. 学术表达规范：
    - 保留原始术语（英文技术名词缩写直接保留,其余翻译）
    - 保证语言的连贯性
    - 公式处理：$f(x)=w^Tx+b$ → f(x) = w^T x + b
    - 图表引用：Fig.3所示 → (见图3)
    4. 文本段落的截取和识别可能存在误差；如果段落起始或结束的地方有独立、不完整的句子，与段落主体含义不同的话，将其丢弃。



    【示例演示】
    输入段落：
    4.1 Prerequisites and Threat Model FUZZWARE has the following prerequisites and threat model:Prerequisites. FUZZWARE shares two basic prerequisites with all other re-hosting systems: First, we assume that we are able to obtain a binary firmware image for the target device. Second, just like other re-hosting systems, we assume
    basic memory mappings such as RAM ranges and the broad MMIO space to be provided. Depending on the target CPU architecture, these generic ranges may be standardized [1]. Threat Model. Given no additional knowledge about the
    specific hardware environment of a given binary firmware image, we assume during fuzzing that an attacker is able to control the inputs provided to the firmware. Commonly, these inputs may correspond to the contents of an incoming
    network packet read via MMIO, data received via a serial interface, or sensory data such as temperature measurements. We analyze situations where an attacker has less control over hardware-generated values in figure 4.

    处理输出：
    前提条件：必须获得目标设备的完整固件二进制文件，同时需要预定义的关键内存区域和不同CPU架构的标准化内存映射规范。
    威胁模型：攻击者具有完全控制固件输入源的能力，例如通过网络数据包、串行接口或传感器数据。


    【特殊处理协议】
    当遇到：
    1. 段落无明显技术要点 → 进行概括
    2. 存在矛盾陈述 → 标记"[数据冲突] 需原文核对"
    """

    prompt_en=f"""
    【System Role Setting】
    You are a senior academic presentation expert preparing for top-tier international conference presentations. Your task is to extract core information from research papers and restructure it according to best practices for academic presentations. Maintain strict adherence to the output format shown in examples.

    【Input/Output Format】
    Input: One or multiple paper paragraphs
    Output:
    Key Point 1 (Technical core/Innovation/Empirical results)
    Key Point 2 (if applicable)
    ...
    (Adjust dynamically based on content)
    Total length: 150-300 words

    【Core Processing Rules】
    1. Information Density Priority:
    - Preserve:
        ✓ Methodological innovations (markers: "first", "proposed", "improved")
        ✓ Quantitative metrics (patterns: \d+\.\d+%, p<0.\d+)
        ✓ Technical comparisons (SOTA methods, baselines)
    - Deprioritize:
        × Background descriptions (e.g., "In recent years...")
        × Textbook theory recitations
        × Repetitive experimental details

    2. Multi-point Separation Strategy:
    if text contains multiple independent points OR distinct examples:
        → Lead with point count (e.g., "3")
        → Separate points with line breaks
        → Avoid unnecessary fragmentation for continuous content

    3. Academic Style Guidelines:
    - Preserve original terminology (retain English technical terms)
    - Maintain linguistic coherence
    - Formula handling: $f(x)=w^Tx+b$ → f(x) = w^T x + b
    - Figure/table references: Fig.3 → (Fig.3)

    4. There may be inaccuracies in text paragraph extraction and recognition; if there are standalone, incomplete sentences at the beginning or end of a paragraph that differ from the main meaning of the paragraph, discard them.


    【Example Demonstration】
    Input Paragraph:
    4.1 Prerequisites and Threat Model FUZZWARE has the following prerequisites and threat model:Prerequisites. FUZZWARE shares two basic prerequisites with all other re-hosting systems: First, we assume that we are able to obtain a binary firmware image for the target device. Second, just like other re-hosting systems, we assume basic memory mappings such as RAM ranges and the broad MMIO space to be provided. Depending on the target CPU architecture, these generic ranges may be standardized [1]. Threat Model. Given no additional knowledge about the specific hardware environment of a given binary firmware image, we assume during fuzzing that an attacker is able to control the inputs provided to the firmware. Commonly, these inputs may correspond to the contents of an incoming network packet read via MMIO, data received via a serial interface, or sensory data such as temperature measurements. We analyze situations where an attacker has less control over hardware-generated values in figure 4.

    Output:
    Prerequisites: Requires obtaining complete firmware binaries and predefined memory mappings (RAM/MMIO), with architecture-dependent standardization [1]
    Threat Assumptions: Adversaries control all firmware inputs (network packets, serial data, sensors) with limited hardware value control (see Fig.4)

    【Special Protocols】
    1. No technical content → Generate conceptual summary
    2. Contradictory statements → Mark "[Data Conflict] Requires source verification"
    3. Multiple weak-related points → Priority sorting (keep top 4)

    【Language Enforcement】
    - Technical terms: Maintain original English terms (e.g., MMIO, SOTA)
    - Measurement units: Use international standards (MHz, kB/s)
    - Acronyms: Spell out at first occurrence (e.g., MMIO (Memory-Mapped I/O))

    """
    prompt={'en':prompt_en,'zh':prompt_zh}
    if lang not in prompt:
        raise ValueError(f"Unsupported language option: {lang}. Valid options are {list(prompt.keys())}")
    messages = [{"role": "system", "content": prompt[lang]}]
    
    # 处理用户反馈
    if user_feedback:
        feedback_rules = []
        
        # 自动解析常见指令
        if "忽略图表" in user_feedback:
            feedback_rules.append("FIGURE_HANDLING: IGNORE")
        if "强调方法" in user_feedback:
            feedback_rules.append("PRIORITY: METHODOLOGY > 0.8")
        
        # 保留原始反馈文本
        feedback_rules.append(user_feedback)
        
        # 插入反馈指令（位于基础prompt之后）
        messages.insert(1, {
            "role": "system",
            "content": "# 用户特别要求，优先遵守。仅输出概括后的文本，不需要再处理提到的图表等。\n" + "\n".join(feedback_rules)
        })
    
    # 添加用户输入
    messages.append({"role": "user", "content": input_text})
    
    # API调用
    completion = client.chat.completions.create(
        model="qwq-32b",
        messages=messages,
        modalities=["text"],
        temperature=temperature,
        presence_penalty=presence_penalty,
        stream=True,
        stream_options={"include_usage": True},
    )
    
    # 收集流式响应
    response_content = []
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            response_content.append(chunk.choices[0].delta.content)
    
    return "".join(response_content)


def title_translate_function(
    title:str=""
) -> str:
    prompt=f"""将标题准确简洁地翻译成汉语,输出的文本除了标题不要包括其他内容。"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": title}
    ]
    completion = client.chat.completions.create(
        model="qwq-32b",
        messages=messages,
        modalities=["text"],
        stream=True,
        stream_options={"include_usage": True},
    )
    
    # 收集流式响应内容
    response_content = []
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            response_content.append(chunk.choices[0].delta.content)
    
    return "".join(response_content)


if __name__ == "__main__":
    
    title="""6.2 Comparison with the State of the Art"""

    result = title_translate_function(
        title=title
    )
    print("生成结果：\n", result)