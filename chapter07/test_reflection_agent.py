from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM,ToolRegistry
from my_reflection_agent import MyReflectionAgent
import os

load_dotenv()

llm = HelloAgentsLLM(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

code_prompts = {
    "initial": "你是Python专家，请编写函数:{task}",
    "reflect": "请审查代码的算法效率:\n任务:{task}\n代码:{content}",
    "refine": "请根据反馈优化代码:\n任务:{task}\n反馈:{feedback}"
}
agent = MyReflectionAgent(
    name="我的代码生成助手",
    llm=llm,
    custom_prompts=code_prompts
)

result = agent.run("编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。请使用暴力破解办法")
print(result)