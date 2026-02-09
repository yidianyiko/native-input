"""
UI Components Manager Module - Extracted from FloatingWindow
Handles UI element creation, layout management, and theme application.
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QFrame
)

from src.utils.loguru_config import logger, get_logger


class UIComponentManager(QObject):
    """Manages UI component creation, layout, and styling for the floating window."""
    
    # Signals
    component_created = Signal(str, QWidget)  # component_name, widget
    layout_updated = Signal(str)  # layout_name
    theme_applied = Signal(str)  # theme_name
    
    def __init__(self, parent_widget: QWidget, config_manager):
        super().__init__()
        self.parent_widget = parent_widget
        self.config_manager = config_manager
        self.logger = get_logger()
        
        # Component references
        self.components: Dict[str, QWidget] = {}
        self.layouts: Dict[str, Any] = {}
        
        # Main layout
        self.main_layout: Optional[QVBoxLayout] = None
        
        logger.info("UIComponentManager initialized")
    
    def setup_main_layout(self) -> QVBoxLayout:
        """Setup the main layout with proper margins and spacing."""
        try:
            # Main layout with minimal margins for compact design
            self.main_layout = QVBoxLayout(self.parent_widget)
            self.main_layout.setContentsMargins(12, 8, 12, 8)
            self.main_layout.setSpacing(6)
            
            self.layouts["main"] = self.main_layout
            self.layout_updated.emit("main")
            
            logger.info("Main layout created")
            return self.main_layout
            
        except Exception as e:
            logger.error(f"Failed to setup main layout: {e}")
            raise
    
    def create_toolbar_layout(self) -> QHBoxLayout:
        """Create the top toolbar layout with AI icon, function selector, and buttons."""
        try:
            toolbar_layout = QHBoxLayout()
            toolbar_layout.setSpacing(8)
            
            # AI Assistant icon (fixed, no interaction)
            ai_icon_label = self._create_ai_icon()
            toolbar_layout.addWidget(ai_icon_label)
            
            # Function selector (32x32 compact design)
            function_selector = self._create_function_selector()
            toolbar_layout.addWidget(function_selector)
            
            toolbar_layout.addStretch()
            
            # Clear button (X) - shows when content exists
            clear_button = self._create_clear_button()
            toolbar_layout.addWidget(clear_button)
            
            # Voice input button
            voice_button = self._create_voice_button()
            toolbar_layout.addWidget(voice_button)
            
            self.layouts["toolbar"] = toolbar_layout
            self.layout_updated.emit("toolbar")
            
            logger.info("Toolbar layout created")
            return toolbar_layout
            
        except Exception as e:
            logger.error(f"Failed to create toolbar layout: {e}")
            raise
    
    def _create_ai_icon(self) -> QLabel:
        """Create the AI assistant icon label."""
        ai_icon_label = QLabel()
        ai_icon_label.setFixedSize(32, 32)
        ai_icon_label.setStyleSheet("""
            QLabel {
                background-color: rgba(59, 130, 246, 0.8);
                border-radius: 16px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        ai_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_icon_label.setText("AI")
        
        self.components["ai_icon"] = ai_icon_label
        self.component_created.emit("ai_icon", ai_icon_label)
        return ai_icon_label
    
    def _create_function_selector(self) -> QComboBox:
        """Create the function selector dropdown."""
        function_selector = QComboBox()
        function_selector.setFixedSize(32, 32)
        
        # Apply styling
        function_selector.setStyleSheet("""
            QComboBox {
                background-color: rgba(75, 85, 99, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
                text-align: center;
            }
            QComboBox:hover {
                background-color: rgba(75, 85, 99, 0.8);
            }
            QComboBox:focus {
                background-color: rgba(59, 130, 246, 0.8);
                border: 1px solid rgba(59, 130, 246, 1.0);
            }
            QComboBox::drop-down {
                border: none;
                width: 12px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid white;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(75, 85, 99, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(59, 130, 246, 0.8);
                padding: 4px;
                min-width: 180px;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(59, 130, 246, 0.6);
            }
        """)
        
        self.components["function_selector"] = function_selector
        self.component_created.emit("function_selector", function_selector)
        return function_selector
    
    def _create_clear_button(self) -> QPushButton:
        """Create the clear button (X)."""
        clear_button = QPushButton()
        clear_button.setFixedSize(32, 32)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.8);
            }
            QPushButton:pressed {
                background-color: rgba(239, 68, 68, 1.0);
            }
        """)
        clear_button.setText("×")
        clear_button.setToolTip("Clear content and return to initial state")
        clear_button.hide()  # Initially hidden
        
        self.components["clear_button"] = clear_button
        self.component_created.emit("clear_button", clear_button)
        return clear_button
    
    def _create_voice_button(self) -> QPushButton:
        """Create the voice input button."""
        voice_button = QPushButton()
        voice_button.setFixedSize(32, 32)
        voice_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(75, 85, 99, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(75, 85, 99, 0.8);
            }
        """)
        voice_button.setText("🎤")
        voice_button.setToolTip("点击开始语音输入")
        voice_button.setEnabled(True)
        
        self.components["voice_button"] = voice_button
        self.component_created.emit("voice_button", voice_button)
        return voice_button    

    def create_input_area(self) -> QTextEdit:
        """Create the main input text area."""
        try:
            input_text = QTextEdit()
            input_text.setPlaceholderText("点击输入需要翻译的内容")
            input_text.setFixedHeight(56)  # 增加高度从48到56
            input_text.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(31, 41, 55, 0.9);
                    border: 2px solid rgba(59, 130, 246, 0.3);
                    border-radius: 16px;
                    padding: 8px 16px;
                    color: white;
                    font-size: 14px;
                    line-height: 1.4;
                    selection-background-color: rgba(59, 130, 246, 0.3);
                }
                QTextEdit:focus {
                    border-color: rgba(59, 130, 246, 0.6);
                    background-color: rgba(31, 41, 55, 1.0);
                }
            """)
            
            self.components["input_text"] = input_text
            self.component_created.emit("input_text", input_text)
            
            logger.info("Input area created")
            return input_text
            
        except Exception as e:
            logger.error(f"Failed to create input area: {e}")
            raise
    
    def create_result_area(self) -> tuple[QFrame, QWidget]:
        """Create the result display area with separator and container."""
        try:
            # Result separator
            result_separator = QFrame()
            result_separator.setFrameShape(QFrame.Shape.HLine)
            result_separator.setStyleSheet("""
                QFrame { border: 1px solid rgba(255,255,255,0.06); margin-top: 4px; margin-bottom: 4px; }
            """)
            result_separator.hide()
            
            # Result container
            result_container = QWidget()
            result_container_layout = QVBoxLayout(result_container)
            result_container_layout.setContentsMargins(0, 0, 0, 0)
            result_container_layout.setSpacing(0)
            
            # Inner container for label and button positioning
            inner_container = QWidget()
            inner_layout = QHBoxLayout(inner_container)
            inner_layout.setContentsMargins(8, 8, 8, 8)
            inner_layout.setSpacing(8)
            
            # Result label
            result_label = self._create_result_label()
            inner_layout.addWidget(result_label, 1)  # Take most space
            
            # Upload button
            upload_button = self._create_upload_button()
            button_layout = QVBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(upload_button)
            inner_layout.addLayout(button_layout)
            
            result_container_layout.addWidget(inner_container)
            
            # Style the container
            result_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(31, 41, 55, 0.8);
                    border: 1px solid rgba(75, 85, 99, 0.3);
                    border-radius: 8px;
                }
                QLabel {
                    background-color: transparent;
                    border: none;
                    color: white;
                    font-size: 14px;
                    selection-background-color: rgba(59, 130, 246, 0.35);
                }
            """)
            result_container.hide()  # Initially hidden
            
            self.components["result_separator"] = result_separator
            self.components["result_container"] = result_container
            self.component_created.emit("result_separator", result_separator)
            self.component_created.emit("result_container", result_container)
            
            logger.info("Result area created")
            return result_separator, result_container
            
        except Exception as e:
            logger.error(f"Failed to create result area: {e}")
            raise
    
    def _create_result_label(self) -> QLabel:
        """Create the result display label."""
        result_label = QLabel()
        result_label.setMinimumHeight(56)
        result_label.setWordWrap(True)
        result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        result_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        
        self.components["result_label"] = result_label
        self.component_created.emit("result_label", result_label)
        return result_label
    
    def _create_upload_button(self) -> QPushButton:
        """Create the upload button."""
        upload_button = QPushButton("↑")
        upload_button.setFixedSize(32, 32)
        upload_button.setToolTip("Upload result (same as Enter key)")
        upload_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.8);
                border: 1px solid rgba(59, 130, 246, 1.0);
                border-radius: 16px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(37, 99, 235, 1.0);
            }
        """)
        upload_button.hide()  # Initially hidden
        
        self.components["upload_button"] = upload_button
        self.component_created.emit("upload_button", upload_button)
        return upload_button
    
    def create_hidden_controls(self) -> tuple[QLabel, QPushButton]:
        """Create hidden status and control elements for compatibility."""
        try:
            # Status indicator (hidden)
            status_label = QLabel("Ready")
            status_label.hide()
            
            # Process button (hidden, functionality preserved)
            process_button = QPushButton("Process")
            process_button.setMaximumWidth(80)
            process_button.hide()  # Hidden in new design
            
            self.components["status_label"] = status_label
            self.components["process_button"] = process_button
            self.component_created.emit("status_label", status_label)
            self.component_created.emit("process_button", process_button)
            
            logger.info("Hidden controls created")
            return status_label, process_button
            
        except Exception as e:
            logger.error(f"Failed to create hidden controls: {e}")
            raise
    
    def populate_function_selector(self, function_selector: QComboBox, ai_service_manager, fallback_functions: Optional[Dict[str, str]] = None):
        """Populate function selector with available agents."""
        try:
            # Clear existing items
            function_selector.clear()
            
            # Get available agents from AI Service Manager
            if ai_service_manager:
                try:
                    available_agents = ai_service_manager.get_available_agents()
                    if available_agents:
                        # Get agent configurations for display names and icons
                        agents_config = self.config_manager.get('agents', {})
                        
                        # Define default icons for agents
                        default_icons = {
                            'translation': '🌐',
                            'polish': '✨', 
                            'correction': '✏️',
                            'grammar': '✏️',
                            'summary': '📝',
                            'chat': '💬',
                            'ocr': '📷',
                            'voice': '🎤'
                        }
                        
                        # Add agents to selector
                        for agent_key in available_agents:
                            agent_config = agents_config.get(agent_key, {})
                            
                            # Get display name from config or use default
                            if isinstance(agent_config, dict):
                                display_name = agent_config.get('name', agent_key.title())
                            else:
                                display_name = agent_key.title()
                            
                            # Get icon for agent
                            icon = default_icons.get(agent_key, '[T]')
                            
                            # Format display text with icon
                            display_text = f"{icon} {display_name}"
                            
                            function_selector.addItem(display_text, agent_key)
                        
                        logger.info(f"Populated function selector with {len(available_agents)} agents")
                        return
                        
                except Exception as e:
                    logger.error(f"Error getting agents from AI Service Manager: {e}")
            
            # Fallback to provided functions
            if fallback_functions:
                # Add fallback functions to selector
                for func_key, func_display in fallback_functions.items():
                    function_selector.addItem(func_display, func_key)
                
                logger.info(f"Using fallback functions for function selector ({len(fallback_functions)} agents)")
            else:
                logger.warning("No agents available and no fallback functions provided")
            
        except Exception as e:
            logger.error(f"Error populating function selector: {e}")
    
    def apply_theme_styling(self, theme_config: Dict[str, Any]):
        """Apply theme-based styling to components."""
        try:
            # Extract theme colors
            bg_color = theme_config.get('background_color', 'rgba(0, 0, 0, 0.8)')
            text_color = theme_config.get('text_color', 'white')
            border_color = theme_config.get('border_color', 'rgba(255, 255, 255, 0.3)')
            cursor_color = theme_config.get('cursor_color', '#3B82F6')
            
            # Apply window style
            window_style = f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 12px;
                color: {text_color};
            }}
            """
            
            # Input text style
            input_style = f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px;
                color: {text_color};
                selection-background-color: rgba(255, 255, 255, 0.3);
            }}
            QTextEdit:focus {{
                border: 2px solid {cursor_color};
            }}
            """
            
            # Result label style
            result_style = f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px;
                color: {text_color};
            }}
            """
            
            # Button style
            button_style = f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:disabled {{
                background-color: rgba(0, 0, 0, 0.2);
                color: rgba(255, 255, 255, 0.5);
            }}
            """
            
            # Status label style
            status_style = f"""
            QLabel {{
                color: {text_color};
                font-size: 12px;
                padding: 4px;
            }}
            """
            
            # Apply styles to components
            if self.parent_widget:
                self.parent_widget.setStyleSheet(window_style)
            
            if "input_text" in self.components:
                self.components["input_text"].setStyleSheet(input_style)
            
            if "result_label" in self.components:
                self.components["result_label"].setStyleSheet(result_style)
            
            if "process_button" in self.components:
                self.components["process_button"].setStyleSheet(button_style)
            
            if "status_label" in self.components:
                self.components["status_label"].setStyleSheet(status_style)
            
            self.theme_applied.emit(theme_config.get('name', 'custom'))
            logger.info(f"Theme styling applied: {theme_config.get('name')}")
            
        except Exception as e:
            logger.error(f"Failed to apply theme styling: {e}")
    
    def get_component(self, name: str) -> Optional[QWidget]:
        """Get a component by name."""
        return self.components.get(name)
    
    def get_layout(self, name: str) -> Optional[Any]:
        """Get a layout by name."""
        return self.layouts.get(name)
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.components.clear()
            self.layouts.clear()
            logger.info("UIComponentManager cleanup completed")
            
        except Exception as e:
            logger.error(f"UIComponentManager cleanup failed: {e}")