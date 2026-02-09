"""
Floating Window Controller
Handles component initialization, window setup, and signal wiring.
"""

from PySide6.QtWidgets import QWidget

from src.utils.loguru_config import logger

from .window_manager import WindowManager
from .event_handler import EventHandler
from .ui_components import UIComponentManager
from .renderer import WindowRenderer
from ...widgets.positioning import WindowPositioning, PositionConfig


class FloatingWindowController:
    """
    Orchestrates component assembly and signal connections for the floating window.

    This class keeps construction and wiring logic out of the main window class,
    reducing its size and clarifying responsibilities.
    """

    def __init__(self, window: QWidget):
        self.window = window

    def init_components(self):
        """Initialize all modular components (migrated from _init_components)."""
        try:
            # Core window management
            self.window.window_manager = WindowManager(self.window, self.window.config_manager)

            # Event handling
            self.window.event_handler = EventHandler(self.window)

            # UI component management
            self.window.ui_manager = UIComponentManager(self.window, self.window.config_manager)

            # Rendering and animations
            self.window.renderer = WindowRenderer(self.window, self.window.config_manager)

            # Window positioning
            positioning_config = PositionConfig()
            self.window.positioning = WindowPositioning(self.window, positioning_config)

            # Audio service (替代原来的 VoiceService)
            from src.services.audio import AudioService
            self.window.voice_service = AudioService(self.window.config_manager)

            logger.info(" All modular components initialized (controller)")

        except Exception as e:
            logger.error(f" Failed to initialize components (controller): {e}")
            raise

    def setup_window(self):
        """Setup the complete window using modular components (migrated from _setup_window)."""
        try:
            # Setup window properties
            self.window.window_manager.setup_window_flags()

            # Create UI layout and components
            main_layout = self.window.ui_manager.setup_main_layout()

            # Create toolbar
            toolbar_layout = self.window.ui_manager.create_toolbar_layout()
            main_layout.addLayout(toolbar_layout)

            # Create input area
            input_text = self.window.ui_manager.create_input_area()
            main_layout.addWidget(input_text)

            # Create result area
            result_separator, result_container = self.window.ui_manager.create_result_area()
            main_layout.addWidget(result_separator)
            main_layout.addWidget(result_container)

            # Create hidden controls for compatibility
            status_label, process_button = self.window.ui_manager.create_hidden_controls()

            # Setup function selector
            function_selector = self.window.ui_manager.get_component("function_selector")
            if function_selector:
                self.window.ui_manager.populate_function_selector(function_selector, self.window.ai_service_manager)

            # Apply initial styling
            self.window.renderer.apply_styling(0.9, "dark", 14)

            # Set initial window size
            self.window.setFixedSize(581, 120)

            # Install event filters
            if input_text:
                self.window.event_handler.install_event_filter(input_text)

            logger.info(" Window setup completed (controller)")

        except Exception as e:
            logger.error(f" Failed to setup window (controller): {e}")
            raise

    def connect_signals(self):
        """Connect signals between components (migrated from _connect_signals)."""
        try:
            # Window manager signals
            self.window.window_manager.state_changed.connect(self.window._on_window_state_changed)

            # Event handler signals
            self.window.event_handler.escape_pressed.connect(self.window.hide)
            self.window.event_handler.enter_pressed.connect(self.window._on_enter_pressed)
            self.window.event_handler.ctrl_enter_pressed.connect(self.window._on_ctrl_enter_pressed)

            # Renderer signals
            self.window.renderer.animation_finished.connect(self.window._on_animation_finished)

            # Positioning signals
            self.window.positioning.position_calculated.connect(self.window._on_position_calculated)
            self.window.positioning.screen_changed.connect(self.window._on_screen_changed)

            # Function selector signals
            function_selector = self.window.ui_manager.get_component("function_selector")
            if function_selector:
                function_selector.currentIndexChanged.connect(self.window._on_agent_selection_changed)

            logger.info(" Component signals connected (controller)")

        except Exception as e:
            logger.error(f" Failed to connect signals (controller): {e}")