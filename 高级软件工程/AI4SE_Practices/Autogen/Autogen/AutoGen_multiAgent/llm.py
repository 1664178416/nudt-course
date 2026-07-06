from openai import OpenAI

class LLMClient:
    def __init__(self, model="gpt-4o-mini", temperature=0.7):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def chat(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content
