"""
Processing Module
Owns input/output buffers, trigger manager, and async processing lifecycle.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget

from src.utils.loguru_config import logger

from .window_manager import WindowState


class ProcessingModule:
    """
    Encapsulates text processing flow: buffering, debouncing triggers, and async execution.
    """

    def __init__(self, window: QWidget):
        self.window = window

    def setup_buffers_and_processors(self):
        """Setup input/output buffers and async processors (migrated)."""
        try:
            from ...widgets.input_buffer import InputBuffer
            from ...widgets.output_buffer import OutputBuffer
            from ...widgets.trigger_manager import TriggerManager
            from ...widgets.async_processor import AsyncProcessor

            # Setup input buffer
            input_text = self.window.ui_manager.get_component("input_text")
            if input_text:
                self.window.input_buffer = InputBuffer(input_text)
                self.window.input_buffer.text_changed.connect(self.on_input_buffer_changed)
                logger.info("Input buffer initialized (processing)")

            # Setup output buffer
            result_label = self.window.ui_manager.get_component("result_label")
            if result_label:
                self.window.output_buffer = OutputBuffer(result_label)
                self.window.output_buffer.content_updated.connect(self.on_output_updated)
                self.window.output_buffer.state_changed.connect(self.on_output_state_changed)
                logger.info("Output buffer initialized (processing)")

            # Setup trigger manager
            debounce_ms = self.window.config_manager.get("processing.debounce_ms", 800)
            self.window.trigger_manager = TriggerManager(debounce_ms)
            self.window.trigger_manager.processing_triggered.connect(self.on_processing_triggered)
            self.window.trigger_manager.trigger_cancelled.connect(self.on_trigger_cancelled)
            logger.info(f" Trigger manager initialized with {debounce_ms}ms debounce (processing)")

            # Setup async processor
            async_processor = AsyncProcessor(self.window.ai_service_manager)
            async_processor.processing_started.connect(self.on_async_processing_started)
            async_processor.processing_completed.connect(self.on_async_processing_completed)
            async_processor.processing_failed.connect(self.on_async_processing_failed)
            async_processor.processing_cancelled.connect(self.on_async_processing_cancelled)
            async_processor.start()
            self.window.async_processor = async_processor  # use property for backward compat
            logger.info("Async processor initialized and started (processing)")

        except Exception as e:
            logger.error(f" Failed to setup buffers and processors (processing): {e}")

    # Buffer and processor event handlers
    def on_input_buffer_changed(self, text: str):
        """Handle input buffer text changes (migrated)."""
        try:
            # Skip processing if we're already processing to prevent duplicate triggers
            if hasattr(self.window, '_is_processing') and self.window._is_processing:
                logger.info("Processing in progress")
                return

            # Update window state based on content
            if text.strip():
                if self.window.window_manager.current_state == WindowState.INITIAL:
                    self.window.window_manager.set_state(WindowState.INPUT)
                    self.window._animate_to_height(184) if not hasattr(self.window, 'interaction') else self.window.interaction.animate_to_height(184)
            else:
                if self.window.window_manager.current_state == WindowState.INPUT and not self.window.processed_text:
                    self.window.window_manager.set_state(WindowState.INITIAL)
                    self.window._animate_to_height(120) if not hasattr(self.window, 'interaction') else self.window.interaction.animate_to_height(120)

            # Trigger processing via trigger manager only if text is not empty
            if hasattr(self.window, 'trigger_manager') and text.strip():
                self.window.trigger_manager.on_text_changed(text, self.window.current_agent_type)

        except Exception as e:
            logger.error(f"Error handling input buffer change (processing): {e}")

    def on_agent_selection_changed(self, index: int):
        """Handle agent selection changes from function selector (migrated)."""
        try:
            function_selector = self.window.ui_manager.get_component("function_selector")
            if function_selector and index >= 0:
                agent_type = function_selector.itemData(index)
                if agent_type:
                    self.window._current_agent_type = agent_type
                    logger.info(f"Agent selection changed to: {agent_type}")

                    input_text = self.window.ui_manager.get_component("input_text")
                    if input_text and hasattr(self.window, 'trigger_manager'):
                        current_text = input_text.toPlainText().strip()
                        if current_text:
                            self.window.trigger_manager.on_text_changed(current_text, agent_type)

        except Exception as e:
            logger.error(f"Error handling agent selection change (processing): {e}")

    def on_output_updated(self, content: str):
        """Handle output buffer content updates (migrated)."""
        try:
            self.window.processed_text = content

            if content.strip():
                self.window.window_manager.set_state(WindowState.COMPLETE)
                self.window._animate_to_height(232) if not hasattr(self.window, 'interaction') else self.window.interaction.animate_to_height(232)

        except Exception as e:
            logger.error(f"Error handling output update (processing): {e}")

    def on_output_state_changed(self, state: str):
        """Handle output buffer state changes (migrated)."""
        try:
            status_label = self.window.ui_manager.get_component("status_label")
            if status_label:
                if state == "processing":
                    status_label.setText("Processing...")
                elif state == "success":
                    status_label.setText("Ready")
                elif state == "error":
                    status_label.setText("Error")
                elif state == "cancelled":
                    status_label.setText("Cancelled")
                else:
                    status_label.setText("Ready")

        except Exception as e:
            logger.error(f"Error handling output state change (processing): {e}")

    def on_processing_triggered(self, trigger_type: str, text: str, agent_name: str):
        """Handle processing trigger from trigger manager (migrated)."""
        try:
            if hasattr(self.window, 'async_processor') and self.window.async_processor:
                from src.ui.widgets.async_processor import RequestPriority

                priority = RequestPriority.IMMEDIATE if trigger_type == "enter_key" else RequestPriority.NORMAL
                window_context = self.window._get_window_context_dict()

                request_id = self.window.async_processor.submit_request(
                    text,
                    agent_name,
                    priority,
                    window_context=window_context,
                )

                if window_context:
                    logger.info(
                        f" Processing queued: {trigger_type} trigger with context: {window_context.get('window_title', 'Unknown')}"
                    )
                else:
                    logger.info(f" Processing queued: {trigger_type} trigger")

        except Exception as e:
            logger.error(f" Error handling processing trigger (processing): {e}")

    def on_trigger_cancelled(self, trigger_type: str):
        """Handle trigger cancellation (migrated)."""
        logger.info(f" Trigger cancelled: {trigger_type}")

    def on_async_processing_started(self, request_id: int, agent_name: str):
        """Handle async processing start (migrated)."""
        try:
            if hasattr(self.window, 'trigger_manager'):
                self.window.trigger_manager.set_processing_state(True)

            if hasattr(self.window, 'output_buffer') and self.window.output_buffer:
                self.window.output_buffer.start_processing(agent_name)

            logger.info(f"Async processing started: request_id={request_id}")

        except Exception as e:
            logger.error(f"Error handling async processing start (processing): {e}")

    def on_async_processing_completed(self, request_id: int, agent_name: str, result: str):
        """Handle async processing completion (migrated)."""
        try:
            if hasattr(self.window, 'trigger_manager'):
                self.window.trigger_manager.set_processing_state(False)

            if hasattr(self.window, 'output_buffer') and self.window.output_buffer:
                self.window.output_buffer.complete_processing(result)

            if hasattr(self.window, 'input_buffer') and self.window.input_buffer:
                self.window.input_buffer.mark_processed()

            self.window.text_processed.emit(result)

            logger.info(f"Async processing completed: request_id={request_id}")

        except Exception as e:
            logger.error(f"Error handling async processing completion (processing): {e}")

    def on_async_processing_failed(self, request_id: int, agent_name: str, error: str):
        """Handle async processing failure (migrated)."""
        try:
            if hasattr(self.window, 'trigger_manager'):
                self.window.trigger_manager.set_processing_state(False)

            if hasattr(self.window, 'output_buffer') and self.window.output_buffer:
                self.window.output_buffer.error_processing(error)

            logger.error(f"Async processing failed: request_id={request_id}")

        except Exception as e:
            logger.error(f"Error handling async processing failure (processing): {e}")

    def on_async_processing_cancelled(self, request_id: int, agent_name: str):
        """Handle async processing cancellation (migrated)."""
        try:
            if hasattr(self.window, 'trigger_manager'):
                self.window.trigger_manager.set_processing_state(False)

            if hasattr(self.window, 'output_buffer') and self.window.output_buffer:
                self.window.output_buffer.cancel_processing()

            logger.info(f"Async processing cancelled: request_id={request_id}")

        except Exception as e:
            logger.error(f"Error handling async processing cancellation (processing): {e}")