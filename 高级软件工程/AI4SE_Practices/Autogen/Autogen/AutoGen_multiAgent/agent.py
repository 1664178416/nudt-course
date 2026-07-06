class Agent:
    def __init__(self, name, system_prompt, llm_client):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm_client
        self.memory = [
            {"role": "system", "content": system_prompt}
        ]

    def receive(self, message):
        self.memory.append({"role": "user", "content": message})

    def respond(self):
        reply = self.llm.chat(self.memory)
        self.memory.append({"role": "assistant", "content": reply})
        return reply
