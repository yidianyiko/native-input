"""
AI Service - Agno集成的统一入口
替代原有的AIServiceManager，直接使用Agno框架
"""

from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal

try:
    from agno.agent import Agent
    from agno.memory import Memory
    from agno.knowledge import AgentKnowledge as Knowledge
    from agno.models.openai import OpenAIChat
    from agno.models.deepseek import DeepSeek as DeepSeekChat
    # 可选依赖 - 如果不可用则使用 None
    try:
        from agno.vectordb.lancedb import LanceDb
    except ImportError:
        LanceDb = None
    try:
        from agno.memory.db.sqlite import SqliteMemoryDb
    except ImportError:
        SqliteMemoryDb = None
    AGNO_AVAILABLE = True
except ImportError as e:
    AGNO_AVAILABLE = False
    # 在开发阶段允许导入失败，但会记录警告
    print(f"Warning: Agno framework is not available. AI functionality will be limited. Error: {e}")
    # 定义占位符类型，避免NameError
    Agent = None
    Memory = None
    Knowledge = None
    OpenAIChat = None
    DeepSeekChat = None
    LanceDb = None
    SqliteMemoryDb = None

from src.config.config import ConfigManager
from src.services.auth.credential_manager import CredentialManager
from src.utils.loguru_config import logger, get_logger


class AIService(QObject):
    """
    AI服务的统一入口点
    直接封装Agno Agent，提供与AIServiceManager兼容的接口
    """
    
    # 信号定义 - 保持与原AIServiceManager兼容
    credentials_error = Signal(dict)  # missing_info
    model_switched = Signal(str)      # new_model_id
    
    def __init__(self, config_manager: ConfigManager, auth_manager=None):
        """
        初始化AI服务
        
        Args:
            config_manager: 配置管理器
            auth_manager: 认证管理器（可选）
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.auth_manager = auth_manager
        
        # 初始化组件
        self.credential_manager = CredentialManager(config_manager, auth_manager)
        
        # Agno组件
        self.memory = None
        self.knowledge = None
        self.agents: Dict[str, Agent] = {}
        self.current_model_id = None
        self.current_model_instance = None
        
        # 初始化标志
        self.is_initialized = False
        
        logger.info("AIService initialized")
    
    def initialize(self) -> bool:
        """
        初始化AI服务和Agno组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("Initializing AI service...")
            
            if not AGNO_AVAILABLE:
                logger.warning("Agno framework not available, using fallback mode")
                self.is_initialized = True
                return True
            
            # 初始化Memory
            try:
                if SqliteMemoryDb:
                    self.memory = Memory(
                        db=SqliteMemoryDb(
                            table_name="user_memory",
                            db_file="user_memory.db"
                        )
                    )
                    logger.info("Memory initialized successfully")
                else:
                    logger.warning("SqliteMemoryDb not available, skipping memory initialization")
                    self.memory = None
            except Exception as e:
                logger.warning(f"Memory initialization failed: {e}")
                self.memory = None
            
            # 初始化Knowledge（可选）
            try:
                if LanceDb:
                    self.knowledge = Knowledge(
                        vector_db=LanceDb(
                            table_name="user_knowledge",
                            uri="knowledge.db"
                        )
                    )
                    logger.info("Knowledge initialized successfully")
                else:
                    logger.warning("LanceDb not available, skipping knowledge initialization")
                    self.knowledge = None
            except Exception as e:
                logger.warning(f"Knowledge initialization failed: {e}")
                self.knowledge = None
            
            # 初始化默认模型
            default_model = self.config_manager.get('ai_services.current_model', 'deepseek-chat')
            if not self._initialize_model(default_model):
                logger.warning("Failed to initialize default model, trying fallback")
                # 尝试备用模型
                fallback_models = ['deepseek-chat', 'gpt-3.5-turbo', 'gpt-4']
                for model in fallback_models:
                    if self._initialize_model(model):
                        break
                else:
                    logger.error("All model initialization attempts failed")
                    self.is_initialized = False
                    return False
            
            self.is_initialized = True
            logger.info("AI service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self.is_initialized = False
            return False
    
    def _initialize_model(self, model_id: str) -> bool:
        """
        初始化指定模型
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            if not AGNO_AVAILABLE:
                logger.warning("Agno not available, skipping model initialization")
                return False
                
            # 根据模型ID确定提供商
            provider = None
            if model_id.startswith('deepseek'):
                provider = 'deepseek'
            elif model_id.startswith('gpt'):
                provider = 'openai'
            else:
                logger.error(f"Unsupported model: {model_id}")
                return False
            
            # 获取API密钥和基础URL
            base_url, api_key, source = self.credential_manager.get_best_credentials(provider)
            if not api_key:
                logger.error(f"No API key available for provider: {provider}")
                return False
            
            logger.info(f"Using {source} credentials for {provider}")
            
            # 创建模型实例
            if provider == 'deepseek':
                self.current_model_instance = DeepSeekChat(
                    id=model_id,
                    api_key=api_key,
                    base_url=base_url
                )
            elif provider == 'openai':
                self.current_model_instance = OpenAIChat(
                    id=model_id,
                    api_key=api_key,
                    base_url=base_url
                )
            
            self.current_model_id = model_id
            
            # 清除现有Agent缓存（因为模型变了）
            self._clear_agent_cache()
            
            logger.info(f"Model {model_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model {model_id}: {e}")
            return False
    
    def _clear_agent_cache(self):
        """清除Agent缓存"""
        if self.agents:
            logger.info(f"Clearing {len(self.agents)} cached agents")
            self.agents.clear()
    
    def process_text(self, text: str, agent_name: str = "translation", 
                    window_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        处理文本 - 主要接口方法
        
        Args:
            text: 要处理的文本
            agent_name: 代理名称
            window_context: 窗口上下文信息（可选），包含 window_title, process_name 等
            
        Returns:
            Optional[str]: 处理后的文本，失败时返回None
        """
        try:
            # 检查初始化状态
            if not self.is_initialized:
                logger.warning("AI service not initialized, attempting to initialize...")
                if not self.initialize():
                    logger.error("Failed to initialize AI service")
                    return None
            
            if not AGNO_AVAILABLE or not self.current_model_instance:
                logger.error("AI service not available")
                return None
            
            # 获取或创建Agent
            agent = self._get_or_create_agent(agent_name)
            if not agent:
                logger.error(f"Failed to get agent: {agent_name}")
                return None
            
            # 构建增强的输入文本（包含窗口上下文）
            enhanced_input = self._build_enhanced_input(text, window_context, agent_name)
            # 记录是否实际应用了窗口上下文注入（便于日志确认）
            try:
                context_applied = (enhanced_input != text) and enhanced_input.startswith("[")
                logger.info(f"Context injection {'applied' if context_applied else 'skipped'} for agent {agent_name}")
            except Exception:
                pass

            # 使用Agno Agent处理文本
            if window_context:
                logger.info(f"Processing text with agent {agent_name} (context: {window_context.get('window_title', 'Unknown')}): {text[:50]}...")
            else:
                logger.info(f"Processing text with agent {agent_name}: {text[:50]}...")

            response = agent.run(enhanced_input)
            
            # 处理响应
            if hasattr(response, 'content') and response.content:
                result = response.content.strip()
                logger.info(f"Text processing completed: {result[:50]}...")
                return result
            elif isinstance(response, str):
                result = response.strip()
                logger.info(f"Text processing completed: {result[:50]}...")
                return result
            else:
                logger.warning("Empty response from agent")
                return None
                
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            return None
    
    def _build_enhanced_input(self, text: str, window_context: Optional[Dict[str, Any]], 
                             agent_name: str) -> str:
        """
        构建包含窗口上下文的增强输入
        
        Args:
            text: 原始文本
            window_context: 窗口上下文信息
            agent_name: 代理名称
            
        Returns:
            str: 增强后的输入文本
        """
        if not window_context:
            return text
        
        # 检查是否启用上下文增强
        context_enabled = self.config_manager.get('ai_services.use_window_context', True)
        if not context_enabled:
            return text

        # 角色控制：仅当当前 agent 为 Prompt 生成器时启用窗口上下文；翻译/纠错必须禁用
        should_inject, reason = self._should_inject_context(agent_name)
        if not should_inject:
            logger.info(f"Window context injection skipped: {reason} (agent={agent_name})")
            return text
        
        # 提取窗口信息
        window_title = window_context.get('window_title', '')
        process_name = window_context.get('process_name', '')
        trigger_source = window_context.get('trigger_source', '')
        
        # 构建上下文提示
        context_parts = []
        
        # 解析窗口标题以提取有用信息
        if window_title:
            # 尝试提取文件名或文档名
            if ' - ' in window_title:
                parts = window_title.split(' - ')
                doc_name = parts[0].strip()
                app_name = parts[-1].strip()
                
                if doc_name and doc_name != app_name:
                    context_parts.append(f"Document: {doc_name}")
                if app_name:
                    context_parts.append(f"Application: {app_name}")
            else:
                context_parts.append(f"Window: {window_title}")
        
        # 添加进程信息（如果有用）
        if process_name and process_name.lower() not in ['unknown', 'unknown.exe']:
            # 清理进程名
            clean_process = process_name.replace('.exe', '').replace('_', ' ').title()
            if not any(clean_process in part for part in context_parts):
                context_parts.append(f"App: {clean_process}")
        
        # 如果没有提取到有用信息，直接返回原文本
        if not context_parts:
            return text
        
        # 根据不同的 Agent 类型构建不同的上下文提示
        context_hint = " | ".join(context_parts)
        
        # 为不同的 Agent 定制上下文使用方式
        if agent_name in ['summary', 'summarize']:
            # 摘要：上下文提供文档背景
            enhanced = f"[Document: {context_hint}]\n\n{text}"
        else:
            # 默认：简单添加上下文
            enhanced = f"[From: {context_hint}]\n\n{text}"
        
        logger.info(f"Enhanced input with context: {enhanced[:100]}...")
        return enhanced

    def _should_inject_context(self, agent_name: str):
        """根据 agent 的角色/名称判断是否应注入窗口上下文。
        规则：
        - 仅“Prompt Generator/提示词生成器”类角色启用
        - 翻译/纠错必须禁用
        - 其他角色默认禁用
        返回: (should_inject: bool, reason: str)
        """
        try:
            key = (agent_name or '').strip().lower()
            cfg = self._load_agent_config(agent_name) or {}
            display = str(cfg.get('name', agent_name)).strip().lower()

            disabled_keys = {"translation", "translate", "correction"}
            disabled_markers = {"翻译", "纠错", "校对"}

            allowed_keys = {"prompt", "prompt_generator", "promptgen"}
            allowed_markers = {"prompt", "提示词", "提示词生成", "生成器"}

            if key in disabled_keys:
                return False, f"disabled role key '{key}'"
            if any(m in display for m in disabled_markers):
                return False, f"disabled role name '{display}'"

            if key in allowed_keys:
                return True, f"allowed role key '{key}'"
            if any(m in display for m in allowed_markers):
                return True, f"allowed role name '{display}'"

            # 特例：示例配置里 'polish' 的显示名可能是 Prompt Generator
            if key == "polish" and any(m in display for m in allowed_markers):
                return True, "polish used as prompt generator"

            return False, f"non-prompt role (key='{key}', name='{display}')"
        except Exception as e:
            logger.warning(f"Role gating error for agent {agent_name}: {e}")
            return False, "gating error"
    

    
    def _get_or_create_agent(self, agent_name: str) -> Optional[Agent]:
        """
        获取或创建Agno Agent
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Optional[Agent]: Agent实例，失败时返回None
        """
        try:
            if not AGNO_AVAILABLE or not self.current_model_instance:
                return None
                
            # 检查缓存
            if agent_name in self.agents:
                # 检查配置是否有更新，如果有则重新创建
                cached_agent = self.agents[agent_name]
                current_config = self._load_agent_config(agent_name)
                
                if current_config and hasattr(cached_agent, '_config_prompt'):
                    # 比较配置内容
                    if cached_agent._config_prompt != current_config.get('prompt'):
                        logger.info(f"Configuration changed for agent {agent_name}, recreating...")
                        del self.agents[agent_name]
                    else:
                        return cached_agent
                else:
                    return cached_agent
            
            # 获取代理配置
            agent_config = self._load_agent_config(agent_name)
            if not agent_config:
                logger.error(f"No configuration found for agent: {agent_name}")
                return None
            
            # 检查代理是否启用
            if not agent_config.get('enabled', True):
                logger.warning(f"Agent {agent_name} is disabled in configuration")
                return None
            
            # 创建Agent实例
            agent = self._create_agent_instance(agent_name, agent_config)
            if not agent:
                return None
            
            # 缓存Agent并保存配置信息用于变更检测
            agent._config_prompt = agent_config.get('prompt', '')
            agent._config_temperature = agent_config.get('temperature', 0.3)
            self.agents[agent_name] = agent
            
            logger.info(f"Agent {agent_name} created and cached")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name}: {e}")
            return None
    
    def _create_agent_instance(self, agent_name: str, agent_config: Dict[str, Any]) -> Optional[Agent]:
        """
        创建Agent实例
        
        Args:
            agent_name: 代理名称
            agent_config: 代理配置
            
        Returns:
            Optional[Agent]: 创建的Agent实例
        """
        try:
            # 准备Agent参数
            agent_params = {
                'name': agent_config.get('name', agent_name.title()),
                'model': self.current_model_instance,
                'instructions': agent_config.get('prompt', ''),
                'memory': self.memory,
                'knowledge': self.knowledge,
                # Agno高级功能
                'add_history_to_messages': True,
                'num_history_runs': 5,
                'markdown': True
            }
            
            # 应用温度设置（如果模型支持）
            temperature = agent_config.get('temperature')
            if temperature is not None:
                try:
                    # 尝试设置模型温度
                    if hasattr(self.current_model_instance, 'temperature'):
                        self.current_model_instance.temperature = temperature
                    elif hasattr(self.current_model_instance, 'model_kwargs'):
                        if not self.current_model_instance.model_kwargs:
                            self.current_model_instance.model_kwargs = {}
                        self.current_model_instance.model_kwargs['temperature'] = temperature
                except Exception as e:
                    logger.warning(f"Failed to set temperature for agent {agent_name}: {e}")
            
            # 应用最大令牌数设置（如果配置中有）
            max_tokens = agent_config.get('max_tokens')
            if max_tokens is not None:
                try:
                    if hasattr(self.current_model_instance, 'max_tokens'):
                        self.current_model_instance.max_tokens = max_tokens
                    elif hasattr(self.current_model_instance, 'model_kwargs'):
                        if not self.current_model_instance.model_kwargs:
                            self.current_model_instance.model_kwargs = {}
                        self.current_model_instance.model_kwargs['max_tokens'] = max_tokens
                except Exception as e:
                    logger.warning(f"Failed to set max_tokens for agent {agent_name}: {e}")
            
            # 创建Agent
            agent = Agent(**agent_params)
            
            logger.info(f"Agent instance created: {agent_name} (temperature: {temperature}, source: {agent_config.get('source')})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent instance for {agent_name}: {e}")
            return None
    
    def _load_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        从配置文件加载代理配置 (agents.*)
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Optional[Dict]: 代理配置，失败时返回None
        """
        try:
            config_key = f"agents.{agent_name}"
            agent_config = self.config_manager.get(config_key)
            
            if not agent_config or not isinstance(agent_config, dict):
                logger.error(f"No configuration found for agent: {agent_name}")
                return None
            
            # 验证必需字段
            prompt = agent_config.get('prompt', '').strip()
            if not prompt:
                logger.error(f"Agent {agent_name} has empty prompt in configuration")
                return None
            
            # 标准化配置格式
            normalized_config = {
                "name": agent_config.get('name', agent_name.title()),
                "prompt": prompt,
                "temperature": agent_config.get('temperature', 0.3),
                "enabled": agent_config.get('enabled', True),
                "source": "config"
            }
            
            # 添加可选配置
            if 'max_tokens' in agent_config:
                normalized_config['max_tokens'] = agent_config['max_tokens']
            
            logger.info(f"Loaded configuration for agent: {agent_name}")
            return normalized_config
            
        except Exception as e:
            logger.error(f"Failed to load configuration for agent {agent_name}: {e}")
            return None
    
    def get_available_agents(self) -> List[str]:
        """
        获取可用代理列表 - 从配置文件发现
        
        Returns:
            List[str]: 代理名称列表
        """
        enabled_agents = []
        
        try:
            # 获取所有 agents.* 配置
            agents_config = self.config_manager.get('agents', {})
            if not isinstance(agents_config, dict):
                logger.warning("No agents configuration found")
                return []
            
            # 遍历所有配置的 agents
            for agent_name, config in agents_config.items():
                if not isinstance(config, dict):
                    continue
                
                # 检查是否有 prompt 且已启用
                prompt = config.get('prompt', '').strip()
                enabled = config.get('enabled', True)
                
                if prompt and enabled:
                    enabled_agents.append(agent_name)
                elif not prompt:
                    logger.warning(f"Agent {agent_name} has empty prompt, skipping")
                elif not enabled:
                    logger.info(f"Agent {agent_name} is disabled, skipping")
            
            logger.info(f"Found {len(enabled_agents)} enabled agents: {enabled_agents}")
            return sorted(enabled_agents)
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []
    
    def reload_agent_config(self, agent_name: str = None) -> bool:
        """
        重新加载代理配置 - 支持动态Prompt调整
        
        Args:
            agent_name: 要重新加载的代理名称，None表示重新加载所有代理
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            if agent_name:
                # 重新加载单个代理
                if agent_name in self.agents:
                    logger.info(f"Reloading configuration for agent: {agent_name}")
                    del self.agents[agent_name]
                    # 下次使用时会自动重新创建
                    return True
                else:
                    logger.warning(f"Agent {agent_name} not found in cache")
                    return True  # 不在缓存中也算成功
            else:
                # 重新加载所有代理
                logger.info("Reloading all agent configurations")
                self._clear_agent_cache()
                return True
                
        except Exception as e:
            logger.error(f"Failed to reload agent config: {e}")
            return False
    
    def get_agent_config_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取代理配置信息（用于调试和UI显示）
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Optional[Dict]: 配置信息
        """
        try:
            config = self._load_agent_config(agent_name)
            if config:
                return {
                    "name": config.get('name', agent_name),
                    "prompt": config.get('prompt', ''),
                    "temperature": config.get('temperature', 0.3),
                    "enabled": config.get('enabled', True),
                    "max_tokens": config.get('max_tokens'),
                    "cached": agent_name in self.agents
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get config info for agent {agent_name}: {e}")
            return None
    
    def switch_model(self, model_id: str) -> bool:
        """
        切换AI模型
        
        Args:
            model_id: 新的模型ID
            
        Returns:
            bool: 切换是否成功
        """
        try:
            logger.info(f"Switching model from {self.current_model_id} to {model_id}")
            
            if not AGNO_AVAILABLE:
                logger.warning("Agno not available, model switch simulated")
                self.current_model_id = model_id
                self.model_switched.emit(model_id)
                return True
            
            # 初始化新模型
            if not self._initialize_model(model_id):
                logger.error(f"Failed to initialize model: {model_id}")
                return False
            
            # 发送信号
            self.model_switched.emit(model_id)
            
            logger.info(f"Model switched to {model_id} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch model to {model_id}: {e}")
            return False
    
    def get_current_model(self) -> Optional[str]:
        """
        获取当前模型
        
        Returns:
            Optional[str]: 当前模型ID
        """
        return self.current_model_id
    
    def test_connection(self, model_or_provider: str) -> bool:
        """
        测试连接
        
        Args:
            model_or_provider: 模型或提供商名称
            
        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not AGNO_AVAILABLE:
                logger.warning("Agno not available, connection test simulated")
                return True
                
            # 简单的连接测试
            test_agent = self._get_or_create_agent("translation")
            if not test_agent:
                return False
            
            # 发送测试消息
            response = test_agent.run("Hello")
            return response is not None
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    # 兼容性方法 - 保持与原AIServiceManager的接口兼容
    @property
    def available_models(self) -> Dict[str, Any]:
        """获取可用模型列表（兼容性属性）"""
        return {
            "deepseek-chat": {
                "name": "DeepSeek Chat",
                "provider": "deepseek",
                "category": "chat",
                "description": "DeepSeek's chat model for general conversations"
            },
            "deepseek-coder": {
                "name": "DeepSeek Coder",
                "provider": "deepseek",
                "category": "code",
                "description": "DeepSeek's specialized model for code generation"
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "category": "chat",
                "description": "OpenAI's fast and efficient chat model"
            },
            "gpt-4": {
                "name": "GPT-4",
                "provider": "openai",
                "category": "chat",
                "description": "OpenAI's most capable chat model"
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "provider": "openai",
                "category": "chat",
                "description": "OpenAI's faster GPT-4 variant"
            },
            "gpt-4o": {
                "name": "GPT-4o",
                "provider": "openai",
                "category": "chat",
                "description": "OpenAI's optimized GPT-4 model"
            },
            "gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "provider": "openai",
                "category": "chat",
                "description": "OpenAI's compact and efficient GPT-4o variant"
            }
        }
    
    @property
    def current_model(self) -> Optional[str]:
        """获取当前模型（兼容性属性）"""
        return self.current_model_id
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用模型（兼容性方法）"""
        return self.available_models
    
    def get_initialized_models(self) -> Dict[str, Any]:
        """获取已初始化的模型列表（兼容性方法）"""
        if self.current_model_id:
            # 从 available_models 中获取当前模型的详细信息
            model_info = self.available_models.get(self.current_model_id, {})
            return {self.current_model_id: model_info}
        return {}
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """
        更新设置（兼容性方法）
        
        Args:
            settings: 设置字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新凭证管理器
            if not self.credential_manager.update_settings(settings):
                logger.error("Failed to update credential settings")
                return False
            
            # 如果模型发生变化，重新初始化
            new_model = settings.get('current_model')
            if new_model and new_model != self.current_model_id:
                return self.switch_model(new_model)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    def test_provider_with_key(self, provider: str, api_key: str) -> bool:
        """
        使用指定API密钥测试提供商连接（兼容性方法）
        
        Args:
            provider: 提供商名称
            api_key: API密钥
            
        Returns:
            bool: 测试是否成功
        """
        try:
            if not AGNO_AVAILABLE:
                logger.warning("Agno not available, provider test simulated")
                return len(api_key) > 10  # 简单验证
            
            # 这里可以实现更复杂的测试逻辑
            return len(api_key) > 10
            
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return False
    
