"""
Modular FloatingWindow Implementation

Refactor status:
- Modularized in 2025-10; main orchestrator maintained without further splitting.
- Delegates responsibilities to controller, renderer, interaction, processing, and UI components.
"""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from .window_manager import WindowManager, WindowState
from .event_handler import EventHandler
from .ui_components import UIComponentManager
from .renderer import WindowRenderer
from ...widgets.positioning import WindowPositioning, PositionConfig, PositionStrategy
from .processing import ProcessingModule
from .interaction import InteractionModule
from .controller import FloatingWindowController

from src.platform_integration.system_integration import create_system_integration_service
from src.services.ai.ai_service import AIService
from src.services.audio import AudioService
from src.config.config import ConfigManager
from src.utils.loguru_config import logger

try:
    from src.services.system.cursor_recovery.window_context_manager import WindowContextManager
except ImportError:
    WindowContextManager = None


class ModularFloatingWindow(QWidget):
    """
    Modular floating window implementation using extracted components.
    
    This class orchestrates all the extracted modules:
    - WindowManager: Core window lifecycle and state management
    - EventHandler: Keyboard and mouse event processing
    - UIComponentManager: UI element creation and layout management
    - WindowRenderer: Qt native rendering and animations
    - WindowPositioning: Cursor following and multi-monitor support
    """
    
    # Signals
    text_processed = Signal(str)  # Emitted when AI processing completes
    window_closed = Signal()  # Emitted when window is closed
    
    def __init__(self, config_manager: ConfigManager, ai_service_manager: AIService):
        super().__init__()
        self.logger = logger
        self.config_manager = config_manager
        self.ai_service_manager = ai_service_manager
        
        # System integration service
        self.system_service = create_system_integration_service()
        if not self.system_service:
            logger.error("Failed to create SystemIntegrationService")
        
        # Window context manager for cursor recovery
        self.window_context_manager = None
        self.captured_window_context = None
        if WindowContextManager and self.system_service:
            self.window_context_manager = WindowContextManager(self.system_service)
            logger.info("WindowContextManager initialized")
        
        # Initialize state
        self._current_agent_type = "translation"  # Default agent type
        self.processed_text = ""  # Store processed text result
        self._is_processing = False  # Flag to prevent duplicate processing
        
        # Initialize active timers tracking
        self._active_timers: set = set()
        
        # Initialize buffers and processors (will be set up later)
        self.input_buffer = None
        self.output_buffer = None
        self.trigger_manager = None
        self.async_processor = None
        
        # Initialize modular components via controller
        self.controller = FloatingWindowController(self)
        self.controller.init_components()
        self.controller.setup_window()

        # Setup processing and interaction modules
        self.processing = ProcessingModule(self)
        self.processing.setup_buffers_and_processors()
        self.interaction = InteractionModule(self)

        # Connect signals via controller
        self.controller.connect_signals()
        
        logger.info(" ModularFloatingWindow initialized")
    
    def _init_components(self):
        """Delegate to controller for component initialization."""
        self.controller.init_components()
    
    def _setup_buffers_and_processors(self):
        """Delegate to processing module to setup buffers/processors."""
        self.processing.setup_buffers_and_processors()
    
    def _setup_window(self):
        """Delegate to controller for window setup."""
        self.controller.setup_window()
    
    def _connect_signals(self):
        """Delegate to controller for signal wiring."""
        self.controller.connect_signals()
    
    # Buffer and processor event handlers
    def _on_input_buffer_changed(self, text: str):
        """Delegate to processing module for input change handling."""
        self.processing.on_input_buffer_changed(text)
    
    def _on_agent_selection_changed(self, index: int):
        """Delegate to processing module for agent selection changes."""
        self.processing.on_agent_selection_changed(index)
    
    def _on_output_updated(self, content: str):
        """Delegate to processing module for output updates."""
        self.processing.on_output_updated(content)
    
    def _on_output_state_changed(self, state: str):
        """Delegate to processing module for output state changes."""
        self.processing.on_output_state_changed(state)
    
    def _on_processing_triggered(self, trigger_type: str, text: str, agent_name: str):
        """Delegate to processing module for processing trigger."""
        self.processing.on_processing_triggered(trigger_type, text, agent_name)
    
    def _on_trigger_cancelled(self, trigger_type: str):
        """Delegate to processing module for trigger cancellation."""
        self.processing.on_trigger_cancelled(trigger_type)
    
    def _on_async_processing_started(self, request_id: int, agent_name: str):
        """Delegate to processing module for async start."""
        self.processing.on_async_processing_started(request_id, agent_name)
    
    def _on_async_processing_completed(self, request_id: int, agent_name: str, result: str):
        """Delegate to processing module for async completion."""
        self.processing.on_async_processing_completed(request_id, agent_name, result)
    
    def _on_async_processing_failed(self, request_id: int, agent_name: str, error: str):
        """Delegate to processing module for async failure."""
        self.processing.on_async_processing_failed(request_id, agent_name, error)
    
    def _on_async_processing_cancelled(self, request_id: int, agent_name: str):
        """Delegate to processing module for async cancellation."""
        self.processing.on_async_processing_cancelled(request_id, agent_name)
    
    def show_window(self):
        """Delegate to interaction module to show window."""
        self.interaction.show_window()
    
    def _set_input_focus(self):
        """Delegate to interaction module to set input focus."""
        self.interaction.set_input_focus()
    
    def hide_window(self):
        """Delegate to interaction module to hide window."""
        self.interaction.hide_window()
    
    def _clear_window_content(self):
        """Delegate to interaction module to clear content."""
        self.interaction.clear_window_content()
    
    def _on_window_state_changed(self, new_state: WindowState):
        """Delegate to interaction module for state change handling."""
        self.interaction.on_window_state_changed(new_state)
    
    def _update_ui_for_state(self, state: WindowState):
        """Delegate to interaction module to update UI for state."""
        self.interaction.update_ui_for_state(state)
    
    def _update_clear_button_visibility(self):
        """Delegate to interaction module to update clear button visibility."""
        self.interaction.update_clear_button_visibility()
    
    def _animate_to_height(self, target_height: int):
        """Delegate to interaction module to animate window height."""
        self.interaction.animate_to_height(target_height)
    
    def _on_enter_pressed(self):
        """Delegate to interaction module for Enter key handling."""
        self.interaction.on_enter_pressed()
    
    def _process_and_inject_text(self, text: str):
        """Delegate to interaction module to process and inject text."""
        self.interaction.process_and_inject_text(text)
    
    def _inject_with_system_service(self, text: str):
        """Delegate to interaction module to inject via system service."""
        self.interaction.inject_with_system_service(text)
    

    
    def _on_ctrl_enter_pressed(self):
        """Delegate to interaction module for Ctrl+Enter handling."""
        self.interaction.on_ctrl_enter_pressed()
    
    def _on_animation_finished(self, animation_name: str):
        """Delegate to interaction module for animation finished."""
        self.interaction.on_animation_finished(animation_name)
    
    def _on_position_calculated(self, position, strategy: str):
        """Delegate to interaction module for position calculated."""
        self.interaction.on_position_calculated(position, strategy)
    
    def _on_screen_changed(self, screen):
        """Delegate to interaction module for screen changed."""
        self.interaction.on_screen_changed(screen)
    
    def _create_single_shot_timer(self, delay_ms: int, callback):
        """Delegate to interaction module to create tracked timer."""
        return self.interaction.create_single_shot_timer(delay_ms, callback)

    def _on_timer_finished(self, timer, callback):
        """Delegate to interaction module for timer finished."""
        self.interaction.on_timer_finished(timer, callback)
    
    # Backward compatibility methods
    
    def show_at_cursor(self, clear_content: bool = False):
        """Show window at cursor position (backward compatibility method)."""
        try:
            if clear_content:
                self.clear_content()
            
            self.show_window()
            logger.info(" Window shown at cursor (compatibility method)")
            
        except Exception as e:
            logger.error(f" Failed to show at cursor: {e}")
    
    def clear_content(self):
        """Clear window content and return to initial state."""
        try:
            self._clear_window_content()
            logger.info(" Content cleared")
            
        except Exception as e:
            logger.error(f" Failed to clear content: {e}")
    
    def set_agent_type(self, agent_type: str):
        """Set the current agent type (backward compatibility method)."""
        try:
            self._current_agent_type = agent_type
            
            function_selector = self.ui_manager.get_component("function_selector")
            if function_selector:
                # Find the item with matching agent type
                for i in range(function_selector.count()):
                    if function_selector.itemData(i) == agent_type:
                        function_selector.setCurrentIndex(i)
                        break
            
            logger.info(f" Agent type set to: {agent_type}")
            
        except Exception as e:
            logger.error(f" Failed to set agent type: {e}")
    
    def get_input_text(self) -> str:
        """Get current input text (backward compatibility method)."""
        try:
            input_text = self.ui_manager.get_component("input_text")
            if input_text:
                return input_text.toPlainText()
            return ""
            
        except Exception as e:
            logger.error(f" Failed to get input text: {e}")
            return ""
    
    def set_result_text(self, text: str):
        """Set result text (backward compatibility method)."""
        try:
            result_label = self.ui_manager.get_component("result_label")
            if result_label:
                result_label.setText(text)
            
            # Update processed text
            self.processed_text = text
            
            # Show complete state if text is provided
            if text.strip():
                self.window_manager.current_state = WindowState.COMPLETE
                self._on_window_state_changed(WindowState.COMPLETE)
            
            logger.info(f" Result text set: {text[:50]}...")
            
        except Exception as e:
            logger.error(f" Failed to set result text: {e}")
    
    def hide_window_delayed(self, delay_ms: int = 3000):
        """Hide window after delay (backward compatibility method)."""
        try:
            self._create_single_shot_timer(delay_ms, self.hide_window)
            logger.info(f" Window will hide in {delay_ms}ms")
            
        except Exception as e:
            logger.error(f" Failed to setup delayed hide: {e}")
    
    def capture_selected_text(self):
        """Capture selected text from the system (for backward compatibility)."""
        try:
            if self.system_service:
                selected_text = self.system_service.capture_selected_text()
                if selected_text:
                    logger.info(f"Captured selected text: {selected_text[:50]}...")
                    return selected_text
                else:
                    logger.info("No selected text found")
                    return ""
            return ""
            
        except Exception as e:
            logger.error(f" Failed to capture selected text: {e}")
            return ""
    
    def capture_window_context(self):
        """Capture the current window context before showing floating window"""
        try:
            if self.window_context_manager:
                self.captured_window_context = self.window_context_manager.capture_context()
                if self.captured_window_context:
                    logger.info(f" Window context captured: {self.captured_window_context.window_info.title}")
                else:
                    logger.error(" Failed to capture window context")
        except Exception as e:
            logger.error(f" Error capturing window context: {e}")
    
    def _get_window_context_dict(self) -> Optional[dict]:
        """
        Get window context as a dictionary for AI processing
        
        Returns:
            Optional[dict]: Window context information or None
        """
        try:
            # Try to get context from context integration first
            if hasattr(self, 'get_captured_context'):
                context = self.get_captured_context()
                if context:
                    return {
                        'window_title': context.title,
                        'process_name': context.process_name,
                        'process_id': context.process_id,
                        'trigger_source': context.trigger_source,
                        'timestamp': context.timestamp,
                        'class_name': context.class_name
                    }
            
            # Fallback: try captured_window_context
            if hasattr(self, 'captured_window_context') and self.captured_window_context:
                context = self.captured_window_context
                if hasattr(context, 'window_info'):
                    window_info = context.window_info
                    return {
                        'window_title': getattr(window_info, 'title', ''),
                        'process_name': getattr(window_info, 'process_name', ''),
                        'process_id': getattr(window_info, 'process_id', 0),
                        'trigger_source': getattr(context, 'trigger_source', ''),
                        'timestamp': getattr(context, 'timestamp', ''),
                        'class_name': getattr(window_info, 'class_name', '')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting window context dict: {e}")
            return None
    
    def inject_text_to_application(self, text: str) -> bool:
        """Inject text to the active application (for backward compatibility)."""
        try:
            if self.system_service:
                result = self.system_service.inject_text(text)
                return result.success
            return False
            
        except Exception as e:
            logger.error(f" Failed to inject text: {e}")
            return False
    
    def set_text(self, text: str):
        """Set text in the input area (for backward compatibility)."""
        try:
            input_text = self.ui_manager.get_component("input_text")
            if input_text:
                input_text.setPlainText(text)
                logger.info(f" Text set: {text[:50]}...")
            
        except Exception as e:
            logger.error(f" Failed to set text: {e}")
    
    def receive_external_input(self, text: str, button_number: int = 1, role_number: int = 1):
        """
        Receive text from an external source (e.g. HTTP POST) and display it
        in the floating window. Auto-opens the window if it is not visible.
        
        Args:
            text: The text content to display as user input.
            button_number: Button identifier from the external client.
            role_number: Role identifier from the external client.
        """
        try:
            logger.info(f"External input received: {text[:80]}... button={button_number} role={role_number}")
            
            # Clear previous content
            self.clear_content()
            
            # Set the text into the input field
            self.set_text(text)
            
            # Auto-open the floating window if not visible
            if not self.isVisible():
                self.show_window()
            else:
                # Already visible — just ensure it's raised and focused
                self.raise_()
                self.activateWindow()
                self._set_input_focus()
            
            logger.info("External input applied to floating window")
            
        except Exception as e:
            logger.error(f"Failed to receive external input: {e}")
    
    def update_settings(self, ui_settings: dict) -> None:
        """Update floating window settings dynamically"""
        try:
            logger.info(f"Updating floating window settings: {list(ui_settings.keys())}")

            # Update styling if relevant settings changed
            styling_keys = {"transparency", "theme", "font_size"}
            if any(key in ui_settings for key in styling_keys):
                transparency = ui_settings.get("transparency", 0.9)
                theme = ui_settings.get("theme", "dark")
                font_size = ui_settings.get("font_size", 14)
                
                self.renderer.apply_styling(transparency, theme, font_size)
                logger.info("Window styling updated")

            # Update positioning if relevant settings changed
            positioning_keys = {
                "cursor_offset_x", "cursor_offset_y", 
                "boundary_margin", "occlusion_threshold"
            }
            if any(key in ui_settings for key in positioning_keys):
                self._configure_positioning()
                logger.info("Window positioning updated")

            logger.info("Floating window settings updated successfully")

        except Exception as e:
            logger.error(f"Error updating floating window settings: {e}")
    
    def _configure_positioning(self):
        """Configure positioning parameters from config"""
        try:
            from PySide6.QtCore import QPoint
            
            # Get positioning configuration
            cursor_offset_x = int(self.config_manager.get("ui.cursor_offset_x", 10))
            cursor_offset_y = int(self.config_manager.get("ui.cursor_offset_y", -10))
            boundary_margin = int(self.config_manager.get("ui.boundary_margin", 20))
            
            # Apply configuration to positioning system
            if hasattr(self.positioning, 'set_cursor_offset'):
                self.positioning.set_cursor_offset(QPoint(cursor_offset_x, cursor_offset_y))
            if hasattr(self.positioning, 'set_boundary_margin'):
                self.positioning.set_boundary_margin(boundary_margin)

            logger.info(f"Positioning configured - offset: ({cursor_offset_x}), margin: {boundary_margin}px")
        except Exception as e:
            logger.error(f"Error configuring positioning: {e}")
    
    # Properties for backward compatibility
    @property
    def input_text(self):
        """Get input text widget (backward compatibility property)."""
        return self.ui_manager.get_component("input_text")
    
    @property
    def result_label(self):
        """Get result label widget (backward compatibility property)."""
        return self.ui_manager.get_component("result_label")
    
    @property
    def function_selector(self):
        """Get function selector widget (backward compatibility property)."""
        return self.ui_manager.get_component("function_selector")
    
    @property
    def voice_button(self):
        """Get voice button widget (backward compatibility property)."""
        return self.ui_manager.get_component("voice_button")
    
    @property
    def process_button(self):
        """Get process button widget (backward compatibility property)."""
        return self.ui_manager.get_component("process_button")
    
    @property
    def status_label(self):
        """Get status label widget (backward compatibility property)."""
        return self.ui_manager.get_component("status_label")
    
    @property
    def current_agent_type(self):
        """Get current agent type for compatibility."""
        return self._current_agent_type
    
    @current_agent_type.setter
    def current_agent_type(self, value):
        """Set current agent type for compatibility."""
        self._current_agent_type = value
    
    @property
    def async_processor(self):
        """Get async processor (for backward compatibility)."""
        return getattr(self, '_async_processor', None)
    
    @async_processor.setter
    def async_processor(self, value):
        """Set async processor (for backward compatibility)."""
        self._async_processor = value
    
    @property
    def voice_service_v2(self):
        """Get voice service (for backward compatibility)."""
        return getattr(self, 'voice_service', None)
    
    @voice_service_v2.setter
    def voice_service_v2(self, value):
        """Set voice service (for backward compatibility)."""
        self.voice_service = value
    
    def _cleanup_active_timers(self):
        """Clean up all active timers"""
        try:
            for timer in list(self._active_timers):
                try:
                    if timer and hasattr(timer, "stop"):
                        timer.stop()
                        timer.deleteLater()
                except RuntimeError:
                    # Timer already deleted, ignore
                    pass
            self._active_timers.clear()
        except Exception:
            # Ignore cleanup errors during shutdown
            pass
    
    def cleanup(self):
        """Clean up all components."""
        try:
            # Clean up active timers first
            self._cleanup_active_timers()
            
            # Stop async processor
            if hasattr(self, 'async_processor') and self.async_processor:
                self.async_processor.stop_processing()
                if not self.async_processor.wait(3000):  # Wait up to 3 seconds
                    self.async_processor.terminate()
                    self.async_processor.wait(1000)
                self.async_processor = None
            
            # Cleanup buffers and managers
            if hasattr(self, 'trigger_manager') and self.trigger_manager:
                self.trigger_manager.cleanup()
                self.trigger_manager = None
            
            if hasattr(self, 'input_buffer') and self.input_buffer:
                self.input_buffer.cleanup()
                self.input_buffer = None
            
            if hasattr(self, 'output_buffer') and self.output_buffer:
                self.output_buffer.cleanup()
                self.output_buffer = None
            
            # Cleanup components in reverse order
            if hasattr(self, 'positioning'):
                self.positioning.cleanup()
            
            if hasattr(self, 'renderer'):
                self.renderer.cleanup()
            
            if hasattr(self, 'ui_manager'):
                self.ui_manager.cleanup()
            
            if hasattr(self, 'event_handler'):
                self.event_handler.cleanup()
            
            # Cleanup voice service
            if hasattr(self, 'voice_service') and hasattr(self.voice_service, 'cleanup'):
                self.voice_service.cleanup()
            
            logger.info(" ModularFloatingWindow cleanup completed")
            
        except Exception as e:
            logger.error(f" ModularFloatingWindow cleanup failed: {e}")


# Alias for backward compatibility
__all__ = ["ModularFloatingWindow", "FloatingWindow"]
FloatingWindow = ModularFloatingWindow