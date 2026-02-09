"""
Interaction Module
Owns user interactions, UI state transitions, animations, and window lifecycle.
"""

from typing import Optional
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from src.utils.loguru_config import logger

from .window_manager import WindowState
from ...widgets.positioning import PositionStrategy


class InteractionModule:
    """
    Encapsulates interaction logic to keep the main window lean.
    """

    def __init__(self, window: QWidget):
        self.window = window

    def show_window(self):
        """Show the floating window with positioning (migrated)."""
        try:
            result = self.window.positioning.calculate_position(PositionStrategy.CURSOR_FOLLOW)
            if result.success:
                self.window.move(result.position)

            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

            if self.window.config_manager.get("ui.floating_window.auto_focus", True):
                self.set_input_focus()

            logger.info(" Window shown")

        except Exception as e:
            logger.error(f" Failed to show window: {e}")

    def set_input_focus(self):
        """Set focus to input text field (migrated)."""
        try:
            input_text = self.window.ui_manager.get_component("input_text")
            if input_text:
                self.create_single_shot_timer(10, lambda: input_text.setFocus())
                self.create_single_shot_timer(100, lambda: input_text.setFocus())
                logger.info(" Input focus set")
        except Exception as e:
            logger.error(f" Failed to set input focus: {e}")

    def hide_window(self):
        """Hide the floating window (migrated)."""
        try:
            logger.info(" Starting to hide window")

            self.window.hide()

            self.clear_window_content()

            self.window.window_manager.current_state = WindowState.INITIAL
            self.on_window_state_changed(WindowState.INITIAL)

            self.window.window_closed.emit()

            logger.info(" Window hidden successfully")

        except Exception as e:
            logger.error(f" Failed to hide window: {e}")

    def clear_window_content(self):
        """Clear all window content (migrated)."""
        try:
            input_text = self.window.ui_manager.get_component("input_text")
            if input_text:
                input_text.clear()

            result_label = self.window.ui_manager.get_component("result_label")
            if result_label:
                result_label.clear()

            if getattr(self.window, 'input_buffer', None):
                self.window.input_buffer.clear()
            if getattr(self.window, 'output_buffer', None):
                self.window.output_buffer.clear()

            self.window.processed_text = ""

            logger.info("Window content cleared")

        except Exception as e:
            logger.error(f"Failed to clear window content: {e}")

    def on_window_state_changed(self, new_state: WindowState):
        """Handle window state changes (migrated)."""
        try:
            self.update_ui_for_state(new_state)

            if new_state == WindowState.INITIAL:
                self.animate_to_height(120)
            elif new_state == WindowState.INPUT:
                self.animate_to_height(184)
            elif new_state == WindowState.COMPLETE:
                self.animate_to_height(232)
            else:
                self.animate_to_height(120)

            logger.info(f"Window state changed to: {new_state.value}")

        except Exception as e:
            logger.error(f"Failed to handle state change: {e}")

    def update_ui_for_state(self, state: WindowState):
        """Update UI component visibility based on window state (migrated)."""
        result_separator = self.window.ui_manager.get_component("result_separator")
        result_container = self.window.ui_manager.get_component("result_container")
        clear_button = self.window.ui_manager.get_component("clear_button")
        upload_button = self.window.ui_manager.get_component("upload_button")

        if state == WindowState.INITIAL:
            if result_separator:
                result_separator.hide()
            if result_container:
                result_container.hide()
            if clear_button:
                clear_button.hide()
            if upload_button:
                upload_button.hide()

        elif state == WindowState.INPUT:
            if result_separator:
                result_separator.show()
            if result_container:
                result_container.hide()
            if upload_button:
                upload_button.hide()
            self.update_clear_button_visibility()

        elif state == WindowState.COMPLETE:
            if result_separator:
                result_separator.show()
            if result_container:
                result_container.show()
            if clear_button:
                clear_button.show()
            if upload_button:
                upload_button.show()

    def update_clear_button_visibility(self):
        """Update clear button visibility based on content existence (migrated)."""
        clear_button = self.window.ui_manager.get_component("clear_button")
        if not clear_button:
            return

        input_text = self.window.ui_manager.get_component("input_text")
        result_label = self.window.ui_manager.get_component("result_label")

        has_input = bool(input_text.toPlainText().strip()) if input_text else False
        has_output = bool(result_label.text().strip()) if result_label else False

        if has_input or has_output:
            clear_button.show()
        else:
            clear_button.hide()

    def animate_to_height(self, target_height: int):
        """Animate window to target height (migrated)."""
        try:
            self.window.renderer.animate_to_height(target_height)
            logger.info(f"Animating to height: {target_height}px")

        except Exception as e:
            logger.error(f"Animation failed: {e}")
            self.window.setFixedSize(581, target_height)

    def on_enter_pressed(self):
        """Handle Enter key press - process text and inject result directly (migrated)."""
        try:
            if hasattr(self.window, '_is_processing') and self.window._is_processing:
                logger.info("Already processing")
                return

            input_text = self.window.ui_manager.get_component("input_text")
            if input_text:
                text = input_text.toPlainText().strip()
                if text:
                    self.window._is_processing = True
                    if hasattr(self.window, 'trigger_manager'):
                        self.window.trigger_manager.set_processing_state(True)
                    self.process_and_inject_text(text)
                else:
                    logger.info("No text to process")

        except Exception as e:
            logger.error(f" Failed to handle Enter press: {e}")
            self.window._is_processing = False

    def process_and_inject_text(self, text: str):
        """Process text with AI and inject result to active application (migrated)."""
        try:
            logger.info(f"Processing and injecting text: {text[:50]}...")

            agent_type = self.window.current_agent_type
            window_context = self.window._get_window_context_dict()

            if self.window.ai_service_manager:
                processed_text = self.window.ai_service_manager.process_text(
                    text,
                    agent_type,
                    window_context=window_context,
                )

                if processed_text and processed_text.strip():
                    if self.window.system_service:
                        # Hide window first
                        self.hide_window()
                        # Small delay to ensure window focus is restored
                        self.create_single_shot_timer(100, lambda: self.inject_with_system_service(processed_text))
                    else:
                        self._inject_with_clipboard_fallback(processed_text)
                        self.hide_window()

                    logger.info("Text processed and injected successfully")
                else:
                    logger.error("AI processing returned empty result")
            else:
                logger.error("AI service manager not available")

        except Exception as e:
            logger.error(f"Failed to process and inject text: {e}")
        finally:
            self.window._is_processing = False
            if hasattr(self.window, 'trigger_manager'):
                self.window.trigger_manager.set_processing_state(False)

    def inject_with_system_service(self, text: str):
        """Inject text using SystemIntegrationService (migrated)."""
        try:
            target_window = None
            if self.window.captured_window_context and self.window.window_context_manager:
                try:
                    target_window = self.window.window_context_manager._convert_to_system_window_info(
                        self.window.captured_window_context.window_info
                    )
                    logger.info(f"Using captured window context for text injection: {target_window.title}")
                except Exception as e:
                    logger.exception(f"Failed to convert captured window context: {e}")
                    target_window = None

            result = self.window.system_service.inject_text(text, target_window=target_window)
            if result.success:
                logger.info(f"Text injection successful using {result.method_used.value}")
            else:
                logger.error(f"Text injection failed: {result.error_message}")

        except Exception as e:
            logger.exception("Exception in system service injection")

    def on_ctrl_enter_pressed(self):
        """Handle Ctrl+Enter key press (migrated)."""
        try:
            result_label = self.window.ui_manager.get_component("result_label")
            if result_label and result_label.text():
                self.window.text_processed.emit(result_label.text())
                self.hide_window()

        except Exception as e:
            logger.error(f" Failed to handle Ctrl+Enter press: {e}")

    def on_animation_finished(self, animation_name: str):
        """Handle animation completion (migrated)."""
        logger.info(f" Animation completed: {animation_name}")

    def on_position_calculated(self, position, strategy: str):
        """Handle position calculation (migrated)."""
        logger.info(f" Position calculated: ({position.x()}) using {strategy}")

    def on_screen_changed(self, screen):
        """Handle screen change (migrated)."""
        logger.info(f" Screen changed to: {screen.name() if screen else 'Unknown'}")

    def create_single_shot_timer(self, delay_ms: int, callback):
        """Create a tracked single-shot timer for proper cleanup (migrated)."""
        try:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.on_timer_finished(timer, callback))
            self.window._active_timers.add(timer)
            timer.start(delay_ms)
            return timer
        except RuntimeError:
            return None

    def on_timer_finished(self, timer, callback):
        """Handle timer completion and cleanup (migrated)."""
        try:
            self.window._active_timers.discard(timer)
            if callback:
                callback()
            timer.deleteLater()
        except RuntimeError:
            pass

    # Internal helper used when system_service is not available
    def _inject_with_clipboard_fallback(self, text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
            logger.info("Copied text to clipboard as fallback")
        except Exception as e:
            logger.error(f"Clipboard fallback failed: {e}")