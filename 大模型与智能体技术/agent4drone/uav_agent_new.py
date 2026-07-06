"""
UAV Control Agent - 重构版本
采用分层架构设计：
1. 配置层 - 处理 LLM 和 UAV API 的配置
2. 策略层 - 定义不同的任务执行策略
3. 执行层 - 统一的命令执行接口
4. 交互层 - 用户交互和命令行接口

与原始版本的主要区别：
- 策略模式替代简单的顺序执行
- 清晰的错误处理和重试机制
- 模块化的任务分类处理
- 更易扩展的架构
"""

from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from uav_api_client_new import UAVAPIClient
from uav_langchain_tools_new import create_uav_tools
from template.agent_prompt_new import AGENT_PROMPT
from template.parsing_error_new import PARSING_ERROR_TEMPLATE
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import os
from pathlib import Path
import logging

# ============================================================================
# 日志配置
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置层
# ============================================================================

@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1


def load_llm_settings(settings_path: str = "llm_settings.json") -> Optional[Dict[str, Any]]:
    """加载 LLM 设置文件"""
    try:
        path = Path(settings_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"无法加载 LLM 设置 {settings_path}: {e}")
    return None


def prompt_user_for_llm_config() -> Dict[str, Any]:
    """用户交互式配置 LLM"""
    settings = load_llm_settings()

    if not settings or 'provider_configs' not in settings:
        print("⚠️  未找到 llm_settings.json 或格式无效。使用命令行参数。")
        return {}

    provider_configs = settings['provider_configs']
    selected_provider = settings.get('selected_provider', '')

    print("\n" + "="*60)
    print("🤖 LLM 提供商配置")
    print("="*60)

    # 显示可用的提供商
    providers = list(provider_configs.keys())
    print("\n可用的提供商:")
    for i, provider in enumerate(providers, 1):
        config = provider_configs[provider]
        default_marker = " (设置中选中)" if provider == selected_provider else ""
        print(f"  {i}. {provider}{default_marker}")
        print(f"     类型: {config.get('type', '未知')}")
        print(f"     Base URL: {config.get('base_url', 'N/A')}")
        print(f"     需要 API Key: {config.get('requires_api_key', False)}")

    # 选择提供商
    print(f"\n选择提供商 (1-{len(providers)}) [默认: {selected_provider or providers[0]}]: ", end='')
    provider_choice = input().strip()

    if not provider_choice:
        chosen_provider = selected_provider or providers[0]
    else:
        try:
            idx = int(provider_choice) - 1
            chosen_provider = providers[idx] if 0 <= idx < len(providers) else (selected_provider or providers[0])
        except ValueError:
            chosen_provider = selected_provider or providers[0]

    config = provider_configs[chosen_provider]
    print(f"\n✅ 选择的提供商: {chosen_provider}")

    # 选择模型
    default_models = config.get('default_models', [])
    default_model = config.get('default_model', '')

    if default_models:
        print("\n可用的模型:")
        for i, model in enumerate(default_models, 1):
            default_marker = " (默认)" if model == default_model else ""
            print(f"  {i}. {model}{default_marker}")
        print(f"  {len(default_models) + 1}. 自定义模型 (手动输入)")

        print(f"\n选择模型 (1-{len(default_models) + 1}) [默认: {default_model}]: ", end='')
        model_choice = input().strip()

        if not model_choice:
            chosen_model = default_model
        else:
            try:
                idx = int(model_choice) - 1
                if 0 <= idx < len(default_models):
                    chosen_model = default_models[idx]
                elif idx == len(default_models):
                    print("输入自定义模型名称: ", end='')
                    chosen_model = input().strip() or default_model
                else:
                    chosen_model = default_model
            except ValueError:
                chosen_model = default_model
    else:
        print("\n输入模型名称 [默认: llama2]: ", end='')
        chosen_model = input().strip() or 'llama2'

    print(f"\n✅ 选择的模型: {chosen_model}")

    # 确定提供商类型
    provider_type = config.get('type', 'ollama')
    
    # 根据提供商名称和类型判断使用哪个 LLM 类
    if provider_type == 'ollama':
        llm_provider = 'ollama'
    elif provider_type == 'openai-compatible':
        # 检查是否是官方 OpenAI 或兼容的
        base_url = config.get('base_url', '').lower()
        if 'api.openai.com' in base_url or chosen_provider.lower() == 'openai':
            llm_provider = 'openai'
        else:
            llm_provider = 'openai-compatible'
    else:
        llm_provider = provider_type

    # 从配置文件中自动读取 API Key
    api_key = config.get('api_key', '').strip()
    
    # 只在需要且未提供时才提示用户
    if config.get('requires_api_key', False) and not api_key:
        print("\n⚠️  此提供商需要 API Key")
        print("输入 API Key (不会显示): ", end='')
        api_key = input().strip()

    # 构建配置返回值
    result = {
        'llm_provider': llm_provider,
        'llm_model': chosen_model,
        'llm_base_url': config.get('base_url'),
        'provider_name': chosen_provider
    }
    
    if api_key:
        result['llm_api_key'] = api_key

    return result


# ============================================================================
# 执行层
# ============================================================================

class UAVControlAgent:
    """重构后的 UAV 控制智能体
    
    核心设计改进：
    1. 采用策略模式，支持多种任务执行方式
    2. 清晰的错误处理和重试机制
    3. 执行上下文管理
    4. 详细的日志记录
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        uav_api_key: Optional[str] = None,
        llm_provider: str = "ollama",
        llm_model: str = "llama2",
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        temperature: float = 0.1,
        verbose: bool = True,
        debug: bool = False
    ):
        """初始化 UAV 控制智能体"""
        self.verbose = verbose
        self.debug = debug
        self.logger = logger
        
        if self.debug:
            self._print_debug_header("初始化 UAV 智能体")
        
        # 初始化 UAV API 客户端
        self.client = UAVAPIClient(base_url, api_key=uav_api_key)
        self._test_connection()
        
        # 初始化 LLM
        self.llm = self._initialize_llm(llm_provider, llm_model, llm_api_key, llm_base_url, temperature)
        
        # 会话和历史
        self.session_context = {}
        self.execution_history: List[Dict[str, Any]] = []
        # 环境记忆：存储障碍物和目标位置（必须在创建工具之前初始化）
        self.environment_memory: Dict[str, Any] = {
            'obstacles': [],  # 格式: [{'name': '...', 'position': {'x': ..., 'y': ..., 'z': ...}, 'type': '...'}]
            'targets': [],    # 格式: [{'name': '...', 'position': {'x': ..., 'y': ..., 'z': ...}, 'type': '...'}]
            'explored_by': {},  # 记录哪些无人机探索过哪些区域
            'map_bounds': {}  # 地图边界信息
        }
        
        # 初始化工具和执行器（传入environment_memory引用，让工具可以更新记忆）
        # verbose参数控制搜索工具的详细日志输出
        self.tools = create_uav_tools(self.client, self.environment_memory)
        self.refresh_session_context()
        
        # 创建prompt（每次execute前会更新环境记忆）
        self.prompt = self._create_prompt()
        self.agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)
        
        # 创建执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=lambda error: PARSING_ERROR_TEMPLATE.format(error=str(error)),
            max_iterations=60,
            return_intermediate_steps=True
        )
        
        if self.debug:
            print("✅ UAV 智能体初始化完成\n")
    
    def _print_debug_header(self, message: str):
        """打印调试头"""
        print("\n" + "="*60)
        print(f"🔧 {message}")
        print("="*60)
    
    def _test_connection(self):
        """测试 API 连接"""
        try:
            session = self.client.get_current_session()
            if self.debug:
                print(f"✅ 连接到 UAV API")
                print(f"   会话: {session.get('name', '未知')}")
                print(f"   任务: {session.get('task', '未知')}")
        except Exception as e:
            if self.debug:
                print(f"⚠️  警告: 无法连接到 UAV API: {e}")
    
    def _initialize_llm(self, provider: str, model: str, api_key: Optional[str], 
                       base_url: Optional[str], temperature: float):
        """初始化 LLM"""
        if self.debug:
            print(f"🤖 初始化 LLM: {provider}/{model}")
        
        if provider == "ollama":
            llm = ChatOllama(model=model, temperature=temperature)
            if self.debug:
                print(f"✅ Ollama LLM 初始化成功")
        elif provider in ["openai", "openai-compatible"]:
            if not api_key:
                raise ValueError(f"{provider} 需要 API Key")
            kwargs = {
                "model": model,
                "temperature": temperature,
                "api_key": api_key,
                "base_url": base_url or "https://api.openai.com/v1"
            }
            llm = ChatOpenAI(**kwargs)
            if self.debug:
                print(f"✅ OpenAI LLM 初始化成功")
        else:
            raise ValueError(f"未知的 LLM 提供商: {provider}")
        
        return llm
    
    def _create_prompt(self) -> PromptTemplate:
        """创建提示词模板，包含环境记忆"""
        # 构建环境记忆字符串
        memory_text = ""
        if self.environment_memory.get('map_bounds'):
            bounds = self.environment_memory['map_bounds']
            memory_text += f"\nMAP BOUNDARIES: width={bounds.get('width', 1024)}, height={bounds.get('height', 768)}, center=({bounds.get('center', {}).get('x', 512):.0f}, {bounds.get('center', {}).get('y', 384):.0f})"
        
        if self.environment_memory['obstacles']:
            memory_text += "\n\nENVIRONMENT MEMORY (from other drones' exploration):"
            memory_text += "\nKnown obstacles:"
            for obs in self.environment_memory['obstacles']:
                pos = obs.get('position')
                if pos:
                    memory_text += f"\n  - {obs.get('name')} at ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f}, {pos.get('z', 0):.0f}), type={obs.get('type')}"
                else:
                    memory_text += f"\n  - {obs.get('name')} (type={obs.get('type')}, location unknown - blocks paths)"
        
        if self.environment_memory['targets']:
            if not memory_text:
                memory_text += "\n\nENVIRONMENT MEMORY (from other drones' exploration):"
            memory_text += "\nKnown targets:"
            for tgt in self.environment_memory['targets']:
                pos = tgt.get('position', {})
                memory_text += f"\n  - {tgt.get('name')} at ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f}, {pos.get('z', 0):.0f})"
        
        if memory_text:
            memory_text += "\nUse this information to plan paths and avoid obstacles."
        
        return PromptTemplate(
            template=AGENT_PROMPT,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools]),
                "environment_memory": memory_text
            }
        )
    
    
    def refresh_session_context(self):
        """刷新会话上下文"""
        try:
            session = self.client.get_current_session()
            self.session_context = {
                'session_id': session.get('id'),
                'task_type': session.get('task'),
                'task_description': session.get('task_description'),
                'status': session.get('status')
            }
        except Exception as e:
            if self.verbose:
                self.logger.warning(f"无法刷新会话上下文: {e}")
    
    def get_environment_memory_summary(self) -> str:
        """获取环境记忆摘要"""
        try:
            memory_summary = []
            
            # 地图边界信息
            if self.environment_memory.get('map_bounds'):
                bounds = self.environment_memory['map_bounds']
                memory_summary.append(f"地图边界: {bounds.get('width', 1024):.0f} x {bounds.get('height', 768):.0f} m")
                center = bounds.get('center', {})
                memory_summary.append(f"地图中心: ({center.get('x', 512):.0f}, {center.get('y', 384):.0f})")
            
            # 障碍物信息
            obstacles = self.environment_memory.get('obstacles', [])
            if obstacles:
                memory_summary.append(f"\n已知障碍物 ({len(obstacles)} 个):")
                for obs in obstacles:
                    pos = obs.get('position')
                    if pos:
                        memory_summary.append(f"  - {obs.get('name')}: ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f}, {pos.get('z', 0):.0f}), 类型: {obs.get('type')}")
                    else:
                        memory_summary.append(f"  - {obs.get('name')}: 位置未知, 类型: {obs.get('type')} (阻挡路径)")
            else:
                memory_summary.append("\n已知障碍物: 无")
            
            # 目标信息
            targets = self.environment_memory.get('targets', [])
            if targets:
                memory_summary.append(f"\n已知目标 ({len(targets)} 个):")
                for tgt in targets:
                    pos = tgt.get('position', {})
                    memory_summary.append(f"  - {tgt.get('name')}: ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f}, {pos.get('z', 0):.0f})")
            else:
                memory_summary.append("\n已知目标: 无")
            
            return "\n".join(memory_summary) if memory_summary else "环境记忆为空"
        except Exception as e:
            return f"获取环境记忆错误: {e}"
    
    def get_session_summary(self) -> str:
        """获取会话摘要"""
        try:
            session = self.client.get_current_session()
            progress = self.client.get_task_progress()
            drones = self.client.list_drones()

            summary = f"""
=== 当前会话摘要 ===
会话: {session.get('name', '未知')}
任务: {session.get('task', '未知')} - {session.get('task_description', '')}
状态: {session.get('status', '未知')}

进度: {progress.get('progress_percentage', 0)}% ({progress.get('status_message', '未知')})
完成: {progress.get('is_completed', False)}

无人机: {len(drones)} 架可用
"""
            for drone in drones:
                summary += f"  - {drone.get('name')} ({drone.get('id')}): {drone.get('status')}, 电量: {drone.get('battery_level', 0):.1f}%\n"
            
            # 添加环境记忆摘要
            summary += "\n=== 环境记忆 ===\n"
            summary += self.get_environment_memory_summary()

            return summary.strip()
        except Exception as e:
            return f"获取会话摘要错误: {e}"
    
    def _record_obstacle_from_error(self, error_message: str):
        """从错误消息中提取障碍物信息并记录到记忆"""
        try:
            # 从错误消息中提取障碍物名称和类型
            # 例如: "Path to waypoint 1 blocked: Flight path intersects with ObstacleType.POLYGON obstacle 'Polygon Obstacle 3'"
            import re
            match = re.search(r"ObstacleType\.(\w+)\s+obstacle\s+'([^']+)'", error_message)
            if match:
                obs_type = match.group(1).lower()
                obs_name = match.group(2)
                
                # 检查是否已记录
                existing_ids = {obs.get('id') or obs.get('name') for obs in self.environment_memory['obstacles']}
                if obs_name not in existing_ids:
                    # 记录障碍物（位置未知，但知道名称和类型）
                    self.environment_memory['obstacles'].append({
                        'name': obs_name,
                        'id': obs_name,
                        'type': obs_type,
                        'position': None,  # 位置未知，只知道在路径上
                        'blocked_paths': []  # 记录哪些路径被阻挡
                    })
                    logger.info(f"记录障碍物: {obs_name} ({obs_type})")
        except Exception as e:
            logger.warning(f"记录障碍物失败: {e}")
    
    def _initialize_environment_memory(self):
        """初始化环境记忆，只记录地图边界信息
        
        不再使用其他无人机预先探索，改为在执行任务过程中记录发现的位置
        """
        try:
            session = self.client.get_current_session()
            canvas_width = session.get('canvas_width', 1024)
            canvas_height = session.get('canvas_height', 768)
            
            # 将地图边界信息添加到记忆
            self.environment_memory['map_bounds'] = {
                'width': canvas_width,
                'height': canvas_height,
                'center': {'x': canvas_width / 2, 'y': canvas_height / 2}
            }
        except Exception as e:
            logger.error(f"初始化环境记忆失败: {e}")
    
    def _record_from_observation(self, observation: str, drone_id: str = None):
        """从执行过程中的观察结果中记录障碍物和目标
        
        在执行任务过程中，如果get_nearby_entities返回了障碍物或目标，记录到记忆
        
        Args:
            observation: 观察结果（JSON字符串或字典）
            drone_id: 执行任务的无人机ID（可选，用于记录）
        """
        try:
            if isinstance(observation, str):
                try:
                    import json
                    obs_data = json.loads(observation)
                except:
                    return
            else:
                obs_data = observation
            
            if not isinstance(obs_data, dict):
                return
            
            # 记录障碍物
            obstacles = obs_data.get('obstacles', [])
            existing_obs_ids = {obs.get('id') or obs.get('name') for obs in self.environment_memory['obstacles']}
            
            for obstacle in obstacles:
                obs_id = obstacle.get('id') or obstacle.get('name')
                if obs_id and obs_id not in existing_obs_ids:
                    existing_obs_ids.add(obs_id)
                    self.environment_memory['obstacles'].append({
                        'name': obstacle.get('name', 'Unknown'),
                        'id': obs_id,
                        'position': obstacle.get('position', {}),
                        'type': obstacle.get('type', 'unknown'),
                        'radius': obstacle.get('radius'),
                        'vertices': obstacle.get('vertices', [])
                    })
                    logger.info(f"执行过程中发现障碍物: {obstacle.get('name')} at {obstacle.get('position')}")
            
            # 记录目标
            targets = obs_data.get('targets', [])
            existing_tgt_ids = {tgt.get('id') or tgt.get('name') for tgt in self.environment_memory['targets']}
            
            for target in targets:
                tgt_id = target.get('id') or target.get('name')
                if tgt_id and tgt_id not in existing_tgt_ids:
                    existing_tgt_ids.add(tgt_id)
                    self.environment_memory['targets'].append({
                        'name': target.get('name', 'Unknown'),
                        'id': tgt_id,
                        'position': target.get('position', {}),
                        'type': target.get('type', 'unknown')
                    })
                    logger.info(f"执行过程中发现目标: {target.get('name')} at {target.get('position')}")
                    
        except Exception as e:
            logger.warning(f"从观察结果记录环境信息失败: {e}")
    
    def _extract_task_drone_id(self, command: str) -> str:
        """从命令中提取执行任务的无人机ID
        
        使用LLM来识别命令中指定的无人机，因为正则匹配可能不够准确
        例如："Drone Drone 1 executes..." 或 "Drone 3 executes..."
        """
        try:
            drones = self.client.list_drones()
            if not drones:
                return None
            
            # 构建无人机列表信息
            drone_info = []
            for drone in drones:
                drone_info.append(f"- {drone.get('name', 'Unknown')} (ID: {drone.get('id', 'Unknown')})")
            drone_list_text = "\n".join(drone_info)
            
            # 使用LLM识别命令中指定的无人机
            prompt = f"""从以下命令中识别出执行任务的无人机名称或ID。

命令: {command}

可用的无人机列表:
{drone_list_text}

请只返回无人机名称（如 "Drone 1"、"Drone 2"、"Drone 3"）或ID，如果命令中没有明确指定无人机，返回 "None"。
只返回一个结果，不要有其他解释。"""
            
            try:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
                
                # 清理结果，移除可能的引号或多余字符
                result = result.replace('"', '').replace("'", '').strip()
                
                # 如果返回None或空，尝试正则匹配作为后备
                if result.lower() in ['none', 'null', ''] or not result:
                    import re
                    # 尝试匹配 "Drone X" 或 "Drone Drone X" 格式
                    pattern = r'Drone\s+(?:Drone\s+)?(\d+)'
                    match = re.search(pattern, command, re.IGNORECASE)
                    if match:
                        drone_num = match.group(1)
                        result = f"Drone {drone_num}"
                
                # 根据识别结果查找对应的无人机ID
                if result and result.lower() != 'none':
                    for drone in drones:
                        drone_name = drone.get('name', '')
                        drone_id = drone.get('id', '')
                        # 匹配名称或ID
                        if result.lower() in drone_name.lower() or result.lower() in drone_id.lower():
                            logger.info(f"识别到执行任务的无人机: {drone_name} (ID: {drone_id})")
                            return drone_id
                
                logger.warning(f"未能识别命令中的无人机: {command[:50]}...")
                return None
                
            except Exception as e:
                logger.warning(f"LLM识别无人机失败，使用正则匹配: {e}")
                # 后备方案：使用正则匹配
                import re
                pattern = r'Drone\s+(?:Drone\s+)?(\d+)'
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    drone_num = match.group(1)
                    for drone in drones:
                        if f"Drone {drone_num}" in drone.get('name', ''):
                            return drone.get('id')
                return None
                
        except Exception as e:
            logger.error(f"提取任务无人机ID失败: {e}")
            return None
    
    def execute(self, command: str) -> Dict[str, Any]:
        """执行命令
        
        核心执行流程：
        1. 环境探索（使用其他无人机）
        2. 更新prompt中的环境记忆
        3. 直接调用agent_executor执行（只调用一次）
        
        Returns:
            字典包含以下字段：
            - success: 是否成功
            - output: 执行输出信息
            - steps: 执行步骤数
            - execution_time: 执行耗时（秒）
            - error: 错误信息（如果失败）
        """
        logger.info(f"执行命令: {command[:50]}...")
        import time
        start_time = time.time()
        
        try:
            # 初始化环境记忆（只记录地图边界，不主动探索）
            self._initialize_environment_memory()
            
            # 更新prompt以包含最新的环境记忆
            self.prompt = self._create_prompt()
            self.agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=self.verbose,
                handle_parsing_errors=lambda error: PARSING_ERROR_TEMPLATE.format(error=str(error)),
                max_iterations=50,
                return_intermediate_steps=True
            )
            
            # 直接调用agent_executor，只传入command（LangChain会自动使用prompt）
            result = self.agent_executor.invoke({"input": command})
            
            # 执行完成后，环境记忆已经通过record_environment_discovery工具在执行过程中更新
            # 这里只获取输出结果
            output = result.get('output', '')
            
            execution_time = round(time.time() - start_time, 2)
            
            # 记录执行历史
            execution_record = {
                'command': command,
                'success': True,
                'output': output,
                'steps': len(result.get('intermediate_steps', [])),
                'execution_time': execution_time,
                'intermediate_steps': result.get('intermediate_steps', [])
            }
            self.execution_history.append(execution_record)
            
            return {
                'success': True,
                'output': output,
                'steps': len(result.get('intermediate_steps', [])),
                'execution_time': execution_time,
                'intermediate_steps': result.get('intermediate_steps', [])
            }
        
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            import traceback
            print(traceback.format_exc())
            execution_time = round(time.time() - start_time, 2)
            error_result = {
                'success': False,
                'output': f"执行命令失败: {e}",
                'steps': 0,
                'execution_time': execution_time,
                'error': str(e)
            }
            self.execution_history.append(error_result)
            return error_result
    
    def run_interactive(self):
        """运行交互模式"""
        print("\n" + "="*60)
        print("🚁 UAV 控制智能体 - 交互模式")
        print("="*60)
        print("\n输入 'quit', 'exit', 或 'q' 退出")
        print("输入 'status' 查看会话状态")
        print("输入 'memory' 查看环境记忆")
        print("输入 'help' 查看示例命令\n")

        print(self.get_session_summary())
        print("\n" + "-"*60 + "\n")

        while True:
            try:
                user_input = input("\n🎮 命令: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 再见！")
                    break

                if user_input.lower() == 'status':
                    print(self.get_session_summary())
                    continue

                if user_input.lower() == 'memory':
                    print("\n" + "="*60)
                    print("🧠 环境记忆")
                    print("="*60)
                    print(self.get_environment_memory_summary())
                    print()
                    continue

                if user_input.lower() == 'help':
                    self._print_help()
                    continue

                # 执行命令
                print("\n🤖 处理中...\n")
                result = self.execute(user_input)

                if result['success']:
                    print(f"\n✅ {result['output']}\n")
                else:
                    print(f"\n❌ {result['output']}\n")

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")

    def _print_help(self):
        """打印帮助信息"""
        help_text = """
示例命令:
==================

信息查询:
- "有哪些无人机可用?"
- "当前任务进度如何?"
- "我需要访问哪些目标?"

基本控制:
- "让无人机 drone-abc123 起飞到 15 米"
- "移动无人机到坐标 x=100, y=50, z=20"
- "降落无人机"
- "所有无人机返航"

队形控制:
- "无人机 abc 移动到 (0,0,20)，无人机 def 移动到 (100,0,20)，保持 100m 距离"
- "编队控制：保持梯形队形"

任务执行:
- "访问所有目标位置"
- "搜索指定区域"
- "完成任务"

安全相关:
- "检查 (0,0,10) 到 (100,100,10) 之间是否有障碍物"
- "无人机附近有什么"
- "检查电池电量"
"""
        print(help_text)


# ============================================================================
# 配置和命令行接口
# ============================================================================

def main():
    """主函数 - 命令行接口"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="UAV 控制智能体 - 自然语言无人机控制"
    )
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='UAV API 服务器地址')
    parser.add_argument('--uav-api-key', help='UAV API 密钥')
    parser.add_argument('--llm-provider', choices=['ollama', 'openai', 'openai-compatible'],
                       help='LLM 提供商')
    parser.add_argument('--llm-model', help='LLM 模型名称')
    parser.add_argument('--llm-api-key', help='LLM API 密钥')
    parser.add_argument('--llm-base-url', help='LLM 基础 URL (用于 openai-compatible)')
    parser.add_argument('--temperature', type=float, default=0.1,
                       help='LLM 温度 (0.0-1.0)')
    parser.add_argument('--command', '-c', help='单条命令执行后退出')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式')
    parser.add_argument('--debug', '-d', action='store_true', help='调试模式')
    parser.add_argument('--no-prompt', action='store_true', help='禁用配置提示')

    args = parser.parse_args()

    # 确定是否显示配置提示
    should_prompt = (
        not args.no_prompt and
        not args.command and
        args.llm_provider is None and
        args.llm_model is None
    )

    # 获取 LLM 配置
    if should_prompt:
        config = prompt_user_for_llm_config()
        llm_provider = config.get('llm_provider', 'ollama')
        llm_model = config.get('llm_model', 'llama2')
        llm_base_url = config.get('llm_base_url')
        llm_api_key = config.get('llm_api_key')
    else:
        llm_provider = args.llm_provider or 'ollama'
        llm_model = args.llm_model or 'llama2'
        llm_base_url = args.llm_base_url
        llm_api_key = args.llm_api_key

    # 从环境变量获取 API 密钥
    if not llm_api_key:
        llm_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    uav_api_key = args.uav_api_key or os.getenv("UAV_API_KEY")

    # 创建智能体
    try:
        agent = UAVControlAgent(
            base_url=args.base_url,
            uav_api_key=uav_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            temperature=args.temperature,
            verbose=not args.quiet,
            debug=args.debug
        )
    except Exception as e:
        print(f"❌ 创建智能体失败: {e}")
        print("\n请确保:")
        print("  - Ollama 运行中 (如果使用 --llm-provider ollama)")
        print("  - OPENAI_API_KEY 已设置 (如果使用 --llm-provider openai)")
        print("  - UAV API 服务可访问")
        return 1

    # 执行单条命令或交互模式
    if args.command:
        result = agent.execute(args.command)
        print(result['output'])
        return 0 if result['success'] else 1
    else:
        agent.run_interactive()
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

# 每次任务前执行charge和take off


# 不要重复读一样的内容


# 主要问题，避障以及搜索


# TODO 能不能使用skill这样的方式
# TODO Area Coverage 任务还有问题，设计一个tool解决？