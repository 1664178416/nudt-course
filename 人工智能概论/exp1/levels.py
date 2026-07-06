class LevelManager:
    def __init__(self):
        self.current_level = 1
        self.target_scores = [1000, 2500, 5000, 10000, 20000]  # 每关目标分数
        self.time_limits = [60, 60, 60, 60, 60]  # 每关时间限制
    
    def get_current_target(self):
        """获取当前关卡目标分数"""
        if self.current_level <= len(self.target_scores):
            return self.target_scores[self.current_level - 1]
        return self.target_scores[-1] + (self.current_level - len(self.target_scores)) * 5000
    
    def get_current_time_limit(self):
        """获取当前关卡时间限制"""
        if self.current_level <= len(self.time_limits):
            return self.time_limits[self.current_level - 1]
        return self.time_limits[-1]
    
    def check_level_complete(self, score):
        """检查是否完成当前关卡"""
        return score >= self.get_current_target()
    
    def advance_level(self):
        """进入下一关"""
        self.current_level += 1
    
    def reset(self):
        """重置关卡"""
        self.current_level = 1