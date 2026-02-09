"""
Agent Selector Dropdown Component
Allows users to select different AI agents in the floating window
"""
import contextlib

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger


class AgentItem(QFrame):
    """Individual agent item in the dropdown list"""

    clicked = Signal(str)  # Emitted when agent is clicked

    def __init__(
        self,
        agent_key: str,
        agent_name: str,
        agent_description: str,
        is_selected: bool = False,
    ):
        super().__init__()
        self.agent_key = agent_key
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.is_selected = is_selected
        self.is_hovered = False

        self._setup_ui()
        self._setup_styling()

    def _setup_ui(self):
        """Setup the agent item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Selection indicator
        self.selection_indicator = QLabel("●" if self.is_selected else "○")
        self.selection_indicator.setFixedWidth(16)
        self.selection_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selection_indicator)

        # Agent name
        self.name_label = QLabel(self.agent_name)
        self.name_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.name_label, 1)

        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_styling(self):
        """Setup styling for the agent item"""
        self.setFixedHeight(32)
        self._update_style()

    def _update_style(self):
        """Update style based on current state"""
        if self.is_selected:
            bg_color = "#0066cc" if self.is_hovered else "#004499"
            text_color = "#ffffff"
            indicator_color = "#00aaff"
        elif self.is_hovered:
            bg_color = "#333333"
            text_color = "#ffffff"
            indicator_color = "#cccccc"
        else:
            bg_color = "transparent"
            text_color = "#ffffff"
            indicator_color = "#888888"

        self.setStyleSheet(
            f"""
            AgentItem {{
                background-color: {bg_color};
                border-radius: 2px;
                color: {text_color};
            }}
        """
        )

        self.selection_indicator.setStyleSheet(f"color: {indicator_color};")
        self.name_label.setStyleSheet(f"color: {text_color};")

    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.selection_indicator.setText("●" if selected else "○")
        self._update_style()

    def enterEvent(self, event):
        """Mouse enter event"""
        self.is_hovered = True
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave event"""
        self.is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press event"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.agent_key)
        super().mousePressEvent(event)

    def cleanup(self):
        """Cleanup resources"""
        with contextlib.suppress(Exception):
            # Disconnect signals to prevent issues
            self.clicked.disconnect()

    def deleteLater(self):
        """Override deleteLater to ensure proper cleanup"""
        self.cleanup()
        super().deleteLater()


class AgentSelector(QWidget):
    """Dropdown agent selector component"""

    agent_changed = Signal(str)  # Emitted when agent selection changes

    def __init__(
        self, config_manager: ConfigManager, ai_service_manager=None, parent=None
    ):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.ai_service_manager = ai_service_manager  # 统一的数据源

        # State
        self.is_expanded = False
        self.current_agent = "translation"  # Default agent
        self.available_agents = {}

        # UI components
        self.header_widget = None
        self.dropdown_widget = None
        self.agent_label = None
        self.dropdown_arrow = None
        self.agent_items = []

        # Animation
        self.expand_animation = None

        # Auto-collapse timer
        self.collapse_timer = QTimer()
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self._collapse_dropdown)

        self._load_available_agents()
        self._setup_ui()
        self._setup_styling()
        self._setup_animation()

        # Debug logging
        logger.info(f"AgentSelector initialized: agents={len(self.available_agents)}")

    def _load_available_agents(self):
        """Load available agents from AI Service Manager and configuration"""
        try:
            self.available_agents = {}

            # 首先从 AI Service Manager 获取已初始化的 Agent（如果可用）
            if self.ai_service_manager and hasattr(
                self.ai_service_manager, "get_available_agents"
            ):
                # 获取实际初始化的 Agent 列表
                initialized_agents = self.ai_service_manager.get_available_agents()

                # 从配置中获取 Agent 详细信息
                agents_config = self.config_manager.get("agents", {})

                # 组合已初始化的 Agent 和配置信息
                for agent_key in initialized_agents:
                    agent_config = agents_config.get(agent_key, {})

                    # 使用配置中的友好名称，或者使用默认名称
                    agent_name = agent_config.get("name")
                    if not agent_name:
                        # 生成友好的显示名称
                        name_map = {
                            "translation": "Translation",
                            "polish": "Text Processing",
                            "correction": "Grammar Check",
                        }
                        agent_name = name_map.get(
                            agent_key, agent_key.replace("_", " ").title()
                        )

                    description = agent_config.get("description", f"{agent_name} agent")

                    self.available_agents[agent_key] = {
                        "name": agent_name,
                        "description": description,
                        "enabled": agent_config.get("enabled", True),
                        **agent_config,
                    }

                logger.info(f"Loaded {len(self.available_agents)} agents from AI Service Manager")

            # 如果没有从 AI Service Manager 获取到 Agent，则从配置文件加载
            if not self.available_agents:
                agents_config = self.config_manager.get("agents", {})

                # 默认 Agent 列表（作为后备）
                default_agents = {
                    "translation": {
                        "name": "Translation",
                        "description": "Translate text to English or other languages",
                        "enabled": True,
                    },
                    "polish": {
                        "name": "Text Processing",
                        "description": "Polish and improve text quality",
                        "enabled": True,
                    },
                    "correction": {
                        "name": "Grammar Check",
                        "description": "Correct grammar and spelling errors",
                        "enabled": True,
                    },
                }

                # 合并配置中的 Agent 信息
                for agent_key, default_info in default_agents.items():
                    agent_config = agents_config.get(agent_key, {})
                    if agent_config.get("enabled", True):
                        self.available_agents[agent_key] = {
                            **default_info,
                            **agent_config,
                        }

                # 添加配置中的其他 Agent
                for agent_key, agent_config in agents_config.items():
                    if agent_key not in self.available_agents and agent_config.get(
                        "enabled", True
                    ):
                        self.available_agents[agent_key] = {
                            "name": agent_key.replace("_", " ").title(),
                            "description": agent_config.get(
                                "description", f"{agent_key} agent"
                            ),
                            "enabled": True,
                            **agent_config,
                        }

                logger.info(f"Loaded {len(self.available_agents)} agents from configuration")

            # 确保至少有一个可用的 Agent
            if not self.available_agents:
                # 最后的后备方案
                self.available_agents = {
                    "translation": {
                        "name": "Translation",
                        "description": "Translate text",
                        "enabled": True,
                    },
                    "polish": {
                        "name": "Text Processing",
                        "description": "Polish text",
                        "enabled": True,
                    },
                    "correction": {
                        "name": "Grammar Check",
                        "description": "Correct grammar",
                        "enabled": True,
                    },
                }
                logger.info("Using fallback agent list")

            # 设置当前选中的 Agent
            self.current_agent = self.config_manager.get(
                "ai.default_agent", "translation"
            )
            if self.current_agent not in self.available_agents:
                self.current_agent = next(
                    iter(self.available_agents.keys()), "translation"
                )

            logger.info(f"Current agent set to: {self.current_agent}")

        except Exception as e:
            logger.error(f"Failed to load agents: {e}")
            # 最终后备方案
            self.available_agents = {
                "translation": {
                    "name": "Translation",
                    "description": "Translate text",
                    "enabled": True,
                },
                "polish": {
                    "name": "Text Processing",
                    "description": "Polish text",
                    "enabled": True,
                },
                "correction": {
                    "name": "Grammar Check",
                    "description": "Correct grammar",
                    "enabled": True,
                },
            }
            self.current_agent = "translation"

    def _setup_ui(self):
        """Setup the agent selector UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (always visible)
        self.header_widget = QFrame()
        self.header_widget.setFixedHeight(28)
        self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_widget.setVisible(True)  # Ensure visibility

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        # Agent label prefix
        agent_prefix = QLabel("Agent:")
        agent_prefix.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(agent_prefix)

        # Current agent display
        current_agent_info = self.available_agents.get(self.current_agent, {})
        self.agent_label = QLabel(current_agent_info.get("name", "Translation"))
        self.agent_label.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(self.agent_label, 1)

        # Dropdown arrow
        self.dropdown_arrow = QLabel("▼")
        self.dropdown_arrow.setFont(QFont("Segoe UI", 8))
        self.dropdown_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.dropdown_arrow)

        main_layout.addWidget(self.header_widget)

        # Dropdown area (initially hidden)
        self.dropdown_widget = QFrame()
        self.dropdown_widget.setFixedHeight(0)  # Start collapsed
        self.dropdown_widget.hide()

        # Scroll area for agent list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Agent list container
        agent_list_widget = QWidget()
        agent_list_layout = QVBoxLayout(agent_list_widget)
        agent_list_layout.setContentsMargins(0, 0, 0, 0)
        agent_list_layout.setSpacing(1)

        # Create agent items
        self.agent_items = []
        for agent_key, agent_info in self.available_agents.items():
            is_selected = agent_key == self.current_agent
            agent_item = AgentItem(
                agent_key,
                agent_info.get("name", agent_key.title()),
                agent_info.get("description", ""),
                is_selected,
            )
            agent_item.clicked.connect(self._on_agent_selected)
            agent_list_layout.addWidget(agent_item)
            self.agent_items.append(agent_item)

        scroll_area.setWidget(agent_list_widget)

        dropdown_layout = QVBoxLayout(self.dropdown_widget)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.addWidget(scroll_area)

        main_layout.addWidget(self.dropdown_widget)

        # Set fixed width to fit floating window better
        self.setFixedWidth(380)  # Fit within 400px window with margins

        # Ensure visibility
        self.setVisible(True)
        if self.header_widget:
            self.header_widget.setVisible(True)

        # Install event filter for click outside detection
        self.installEventFilter(self)

    def _setup_styling(self):
        """Setup styling for the component"""
        # Set main widget background to ensure visibility
        self.setStyleSheet(
            """
            AgentSelector {
                background-color: transparent;
                border: none;
            }
        """
        )

        # Header styling with higher contrast
        if self.header_widget:
            self.header_widget.setStyleSheet(
                """
                QFrame {
                    background-color: rgba(42, 42, 42, 0.95);
                    border: 1px solid #666666;
                    border-radius: 4px;
                    color: #ffffff;
                    min-height: 28px;
                }
                QFrame:hover {
                    background-color: rgba(51, 51, 51, 0.95);
                    border-color: #888888;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                }
            """
            )

        # Dropdown styling
        if self.dropdown_widget:
            self.dropdown_widget.setStyleSheet(
                """
                QFrame {
                    background-color: rgba(42, 42, 42, 0.95);
                    border: 1px solid #666666;
                    border-top: none;
                    border-radius: 0px 0px 4px 4px;
                }
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
            """
            )

    def _setup_animation(self):
        """Setup expand/collapse animation"""
        self.expand_animation = QPropertyAnimation(
            self.dropdown_widget, b"maximumHeight"
        )
        self.expand_animation.setDuration(150)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _toggle_dropdown(self):
        """Toggle dropdown state"""
        if self.is_expanded:
            self._collapse_dropdown()
        else:
            self._expand_dropdown()

    def _expand_dropdown(self):
        """Expand the dropdown"""
        if self.is_expanded:
            return

        self.is_expanded = True
        self.dropdown_arrow.setText("▲")

        # Calculate dropdown height (max 6 items)
        item_height = 32
        max_items = min(6, len(self.available_agents))
        target_height = max_items * item_height + 4  # +4 for padding

        # Show dropdown and animate
        self.dropdown_widget.show()
        self.dropdown_widget.setMaximumHeight(0)

        # Ensure dropdown appears on top of other widgets
        self.dropdown_widget.raise_()
        self.dropdown_widget.activateWindow()

        self.expand_animation.setStartValue(0)
        self.expand_animation.setEndValue(target_height)
        self.expand_animation.start()

        # Start auto-collapse timer
        self.collapse_timer.start(5000)  # Auto-collapse after 5 seconds

    def _collapse_dropdown(self):
        """Collapse the dropdown"""
        if not self.is_expanded:
            return

        self.is_expanded = False
        self.dropdown_arrow.setText("▼")

        # Animate collapse
        self.expand_animation.setStartValue(self.dropdown_widget.height())
        self.expand_animation.setEndValue(0)

        # Properly disconnect previous signal connections to avoid RuntimeWarning
        with contextlib.suppress(TypeError, RuntimeError):
            self.expand_animation.finished.disconnect()

        # Connect the signal for hiding dropdown after animation
        self.expand_animation.finished.connect(lambda: self.dropdown_widget.hide())
        self.expand_animation.start()

        # Stop auto-collapse timer
        self.collapse_timer.stop()

    def _on_agent_selected(self, agent_key: str):
        """Handle agent selection"""
        if agent_key == self.current_agent:
            self._collapse_dropdown()
            return

        # Update selection
        old_agent = self.current_agent
        self.current_agent = agent_key

        # Update UI
        agent_info = self.available_agents.get(agent_key, {})
        self.agent_label.setText(agent_info.get("name", agent_key.title()))

        # Update agent items
        for item in self.agent_items:
            item.set_selected(item.agent_key == agent_key)

        # Save to configuration
        try:
            self.config_manager.set("ai.default_agent", agent_key)
            # Note: ConfigManager doesn't have a save() method, changes are auto-saved
            logger.info(f"Agent changed from {old_agent} to {agent_key}")
        except Exception as e:
            logger.error(f"Failed to save agent selection: {e}")

        # Emit signal
        self.agent_changed.emit(agent_key)

        # Collapse dropdown
        self._collapse_dropdown()

    def mousePressEvent(self, event):
        """Handle mouse press on header"""
        if event.button() == Qt.MouseButton.LeftButton:
            header_rect = self.header_widget.geometry()
            if header_rect.contains(event.position().toPoint()):
                self._toggle_dropdown()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        """Event filter for click outside detection"""
        if event.type() == QEvent.Type.MouseButtonPress and self.is_expanded and not self.geometry().contains(
            self.mapFromGlobal(QCursor.pos())
        ):
            self._collapse_dropdown()
        return super().eventFilter(obj, event)

    def get_current_agent(self) -> str:
        """Get current selected agent"""
        return self.current_agent

    def set_current_agent(self, agent_key: str):
        """Set current agent programmatically"""
        if agent_key in self.available_agents:
            self._on_agent_selected(agent_key)

    def refresh_agents(self):
        """Refresh available agents from AI Service Manager and rebuild UI"""
        try:
            old_agents = set(self.available_agents.keys())

            # 重新加载可用的 Agent
            self._load_available_agents()

            new_agents = set(self.available_agents.keys())

            # 如果 Agent 列表发生了变化，重建 UI
            if old_agents != new_agents:
                logger.info(f"Agent list changed")
                self._rebuild_agent_list()
            else:
                # 只更新当前选中的 Agent 显示
                current_agent_info = self.available_agents.get(self.current_agent, {})
                if self.agent_label:
                    self.agent_label.setText(
                        current_agent_info.get("name", self.current_agent.title())
                    )

                logger.info("Agent list unchanged")

        except Exception as e:
            logger.error(f"Failed to refresh agents: {e}")

    def _rebuild_agent_list(self):
        """Rebuild the agent list UI components"""
        try:
            # 清理旧的 Agent 项目
            for item in self.agent_items:
                item.setParent(None)
                item.deleteLater()
            self.agent_items.clear()

            # 获取 agent list widget
            if self.dropdown_widget:
                scroll_area = self.dropdown_widget.findChild(QScrollArea)
                if scroll_area:
                    agent_list_widget = scroll_area.widget()
                    if agent_list_widget:
                        agent_list_layout = agent_list_widget.layout()

                        # 创建新的 Agent 项目
                        for agent_key, agent_info in self.available_agents.items():
                            is_selected = agent_key == self.current_agent
                            agent_item = AgentItem(
                                agent_key,
                                agent_info.get("name", agent_key.title()),
                                agent_info.get("description", ""),
                                is_selected,
                            )
                            agent_item.clicked.connect(self._on_agent_selected)
                            agent_list_layout.addWidget(agent_item)
                            self.agent_items.append(agent_item)

                        # 更新当前选中的 Agent 显示
                        current_agent_info = self.available_agents.get(
                            self.current_agent, {}
                        )
                        if self.agent_label:
                            self.agent_label.setText(
                                current_agent_info.get(
                                    "name", self.current_agent.title()
                                )
                            )

                        logger.info(f"Rebuilt agent list with {len(self.agent_items)} items")

        except Exception as e:
            logger.error(f"Failed to rebuild agent list: {e}")

    def leaveEvent(self, event):
        """Mouse leave event - start collapse timer"""
        if self.is_expanded:
            self.collapse_timer.start(1000)  # Collapse after 1 second when mouse leaves
        super().leaveEvent(event)

    def enterEvent(self, event):
        """Mouse enter event - stop collapse timer"""
        self.collapse_timer.stop()
        super().enterEvent(event)

    def cleanup(self):
        """Cleanup resources to prevent memory leaks"""
        try:
            # Stop and cleanup timers
            if hasattr(self, "collapse_timer") and self.collapse_timer:
                self.collapse_timer.stop()
                self.collapse_timer.deleteLater()
                self.collapse_timer = None

            # Stop and cleanup animations
            if hasattr(self, "expand_animation") and self.expand_animation:
                self.expand_animation.stop()
                # Safely disconnect all signals before deletion
                with contextlib.suppress(TypeError, RuntimeError):
                    self.expand_animation.finished.disconnect()
                self.expand_animation.deleteLater()
                self.expand_animation = None

            # Cleanup agent items
            if hasattr(self, "agent_items"):
                for item in self.agent_items:
                    if item:
                        item.setParent(None)
                        item.deleteLater()
                self.agent_items.clear()

            logger.info("AgentSelector cleanup completed")

        except Exception as e:
            logger.error(f"Error during AgentSelector cleanup: {e}")

    def deleteLater(self):
        """Override deleteLater to ensure proper cleanup"""
        self.cleanup()
        super().deleteLater()
