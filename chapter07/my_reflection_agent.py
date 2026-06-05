import re
from typing import Optional, List, Tuple, Dict, Any
from hello_agents import ReflectionAgent, HelloAgentsLLM, Config, Message, ToolRegistry

DEFAULT_PROMPTS = {
"initial": """
请根据以下要求完成任务:

任务: {task}

请提供一个完整、准确的回答。
""",

"reflect": """
请仔细审查以下回答，并找出可能的问题或改进空间:

# 原始任务:
{task}

# 当前回答:
{content}

请分析这个回答的质量，指出不足之处，并提出具体的改进建议。
如果回答已经很好，请回答"无需改进"。
""",

"refine": """
请根据反馈意见改进你的回答:

# 原始任务:
{task}

# 上一轮回答:
{last_attempt}

# 反馈意见:
{feedback}

请提供一个改进后的回答。
""",
}


class Memory:
    """
    简单的短期记忆模块，用于存储智能体的行动与反思轨迹。
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """向记忆中添加一条新记录"""
        self.records.append({"type": record_type, "content": content})
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        """将所有记忆记录格式化为一个连贯的字符串文本"""
        trajectory = ""
        for record in self.records:
            if record["type"] == "execution":
                trajectory += f"--- 上一轮尝试 (代码) ---\n{record['content']}\n\n"
            elif record["type"] == "reflection":
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """获取最近一次的执行结果"""
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return ""


class MyReflectionAgent(ReflectionAgent):
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            name, llm, system_prompt, config, max_iterations, custom_prompts
        )
        self.max_iterations = max_iterations
        self.memory = Memory()

        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPTS

    def run(self, input_text: str, **kwargs) -> str:
        print(f"\n {self.name} 开始处理任务：{input_text}")
        self.memory = Memory()

        print("\n--- 正在进行初次尝试 ---")
        initial_prompt = self.prompts["initial"].format(task=input_text)
        initial_result = self._get_llm_response(initial_prompt, **kwargs)
        print(f"\n---initial result---\n {initial_result}")
        self.memory.add_record("execution", initial_result)

        for i in range(self.max_iterations):
            print(f"\n--- 第 {i+1}/{self.max_iterations} 次迭代 ---")

            print("\n-> 正在进行反思")
            last_result = self.memory.get_last_execution()
            reflect_prompt = self.prompts["reflect"].format(
                task=input_text, content=last_result
            )
            feedback = self._get_llm_response(reflect_prompt, **kwargs)
            print(f"\n--- feedback result---\n {feedback}")
            self.memory.add_record("reflection", feedback)            
            # b. 检查是否需要停止
            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ 反思认为结果已无需改进，任务完成。")
                break

            # c. 优化
            print("\n-> 正在进行优化...")
            refine_prompt = self.prompts["refine"].format(
                task=input_text,
                last_attempt=last_result,
                feedback=feedback
            )
            refined_result = self._get_llm_response(refine_prompt, **kwargs)
            print(f"\n--- refined result ---\n {refined_result}")
            self.memory.add_record("execution", refined_result)

        final_result = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终结果:\n{final_result}")

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_result, "assistant"))
