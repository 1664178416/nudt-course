class MultiAgentSystem:
    def __init__(self, agents):
        self.agents = agents

    def step(self, speaker_name):
        agent = self.agents[speaker_name]
        reply = agent.respond()
        print(f"[{agent.name}]: {reply}\n")
        return reply

    def dialogue(self, order, init_message):
        message = init_message
        for name in order:
            self.agents[name].receive(message)
            message = self.step(name)
