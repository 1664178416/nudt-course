import os
from smolagents import CodeAgent, WebSearchTool, InferenceClientModel, OpenAIServerModel, GradioUI

# model = InferenceClientModel()
model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base=os.getenv("OPENAI_BASE_URL"), # Leave this blank to query OpenAI servers.
    api_key=os.getenv("OPENAI_API_KEY"), # Switch to the API key for the server you're targeting.
)
agent = CodeAgent(tools=[WebSearchTool()], model=model, stream_outputs=True)


# agent.run("Help me write a Python code for quick sorting")
demo = GradioUI(agent)
demo.launch()