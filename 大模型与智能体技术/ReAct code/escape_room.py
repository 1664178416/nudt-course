import random
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class RoomItem(Enum):
  EMPTY = 0
  KEY = 1
  DOOR = 2


class Action(Enum):
  MOVE_LEFT = "向左移动"
  MOVE_RIGHT = "向右移动"
  PICK_UP = "拾取钥匙"
  OPEN_DOOR = "开门"
  WAIT = "等待"


@dataclass
class RoomEnvironment:
  """密室环境"""
  size: int = 3
  positions: List[RoomItem] = None
  key_position: int = None
  door_position: int = 2  # 门固定在位置2

  def __post_init__(self):
    if self.positions is None:
      self.positions = [RoomItem.EMPTY] * self.size
      # 放置门
      self.positions[self.door_position] = RoomItem.DOOR
      # 随机放置钥匙（不在门的位置）
      self.key_position = random.randint(0, self.size - 2)
      self.positions[self.key_position] = RoomItem.KEY

  def get_item_at(self, position: int) -> RoomItem:
    """获取指定位置的物品"""
    if 0 <= position < self.size:
      return self.positions[position]
    return RoomItem.EMPTY

  def remove_key(self, position: int) -> bool:
    """移除钥匙"""
    if self.positions[position] == RoomItem.KEY:
      self.positions[position] = RoomItem.EMPTY
      return True
    return False

  def is_door_at(self, position: int) -> bool:
    """检查是否是门"""
    return self.positions[position] == RoomItem.DOOR

  def display(self, agent_pos: int) -> str:
    """可视化显示房间状态"""
    display_chars = []
    for i, item in enumerate(self.positions):
      if i == agent_pos:
        if item == RoomItem.KEY:
          display_chars.append("🔑🤖")
        elif item == RoomItem.DOOR:
          display_chars.append("🚪🤖")
        else:
          display_chars.append("  🤖")
      else:
        if item == RoomItem.KEY:
          display_chars.append("🔑 ")
        elif item == RoomItem.DOOR:
          display_chars.append("🚪 ")
        else:
          display_chars.append("⬜ ")
    return " ".join(display_chars)


class ReActAgent:
  """ReAct智能体"""

  def __init__(self, env: RoomEnvironment):
    self.env = env
    self.position = 0
    self.has_key = False
    self.steps = 0
    self.history = []

  def perceive(self) -> Tuple[RoomItem, bool, bool]:
    """感知环境"""
    current_item = self.env.get_item_at(self.position)
    at_door = self.env.is_door_at(self.position)
    return current_item, at_door

  def reason(self, current_item: RoomItem, at_door: bool) -> Action:
    """推理下一步行动"""
    self.steps += 1

    # 如果有钥匙且在门前
    if at_door and self.has_key:
      return Action.OPEN_DOOR

    # 如果在钥匙上且没有钥匙
    if current_item == RoomItem.KEY and not self.has_key:
      return Action.PICK_UP

    # 如果还没有钥匙，先去钥匙位置
    if not self.has_key:
      if self.position < self.env.key_position:
        return Action.MOVE_RIGHT
      elif self.position > self.env.key_position:
        return Action.MOVE_LEFT
      else:
        # 在钥匙位置但没看到钥匙？应该不会发生
        return Action.WAIT
    else:
      # 已经有钥匙，去找门
      if self.position < self.env.door_position:
        return Action.MOVE_RIGHT
      elif self.position > self.env.door_position:
        return Action.MOVE_LEFT
      else:
        # 在门的位置但之前没开门？应该不会发生
        return Action.WAIT

  def act(self, action: Action) -> Tuple[bool, str]:
    """执行行动"""
    result = ""

    if action == Action.MOVE_RIGHT:
      if self.position < self.env.size - 1:
        self.position += 1
        result = f"向右移动到位置 {self.position}"
      else:
        result = "已在最右，无法向右移动"

    elif action == Action.MOVE_LEFT:
      if self.position > 0:
        self.position -= 1
        result = f"向左移动到位置 {self.position}"
      else:
        result = "已在最左，无法向左移动"

    elif action == Action.PICK_UP:
      if self.env.get_item_at(
        self.position) == RoomItem.KEY and not self.has_key:
        self.env.remove_key(self.position)
        self.has_key = True
        result = "拾取钥匙成功！"
      else:
        result = "拾取失败：这里没有钥匙或已有钥匙"

    elif action == Action.OPEN_DOOR:
      if self.env.is_door_at(self.position) and self.has_key:
        return True, "成功开门！🎉 任务完成！"
      elif not self.env.is_door_at(self.position):
        result = "开门失败：这里没有门"
      else:
        result = "开门失败：没有钥匙"
    else:  # WAIT
      result = "等待..."

    return False, result

  def get_status(self) -> str:
    """获取当前状态描述"""
    items = {
      RoomItem.EMPTY: "空",
      RoomItem.KEY: "钥匙",
      RoomItem.DOOR: "门"
    }
    current_item = self.env.get_item_at(self.position)
    return f"位置:{self.position} 物品:{items[current_item]} 钥匙:{'是' if self.has_key else '否'}"


def main():
  """主程序"""
  print("=" * 50)
  print("ReAct智能体 - 密室逃脱游戏")
  print("=" * 50)

  # 创建环境和智能体
  env = RoomEnvironment(size=3)
  agent = ReActAgent(env)

  print(f"\n初始房间状态:")
  print(env.display(agent.position))
  print(f"钥匙位置: {env.key_position}")
  print(f"门位置: {env.door_position}")
  print("-" * 30)

  max_steps = 20

  for i in range(max_steps):
    print(f"\n步骤 {i + 1}:")
    print(env.display(agent.position))
    print(f"状态: {agent.get_status()}")

    # ReAct循环
    current_item, at_door = agent.perceive()
    print(
      f"感知 -> 看到: {current_item.name}, 在门前: {'是' if at_door else '否'}")

    action = agent.reason(current_item, at_door)
    print(f"推理 -> 决定: {action.value}")

    done, result = agent.act(action)
    print(f"行动 -> {result}")

    if done:
      print(f"\n🎉 任务完成！用了 {agent.steps} 步")
      print("=" * 50)
      break

    time.sleep(0.5)
  else:
    print(f"\n⚠️ 在 {max_steps} 步内未完成任务")

  print(
    f"\n游戏结束。最终位置: {agent.position}, 持有钥匙: {'是' if agent.has_key else '否'}")


if __name__ == "__main__":
  main()
