"""Simplified Voice Button Component v2

A voice button refactored based on technical specifications, integrating the new VoiceService_v2 architecture.
Referencing the design philosophy of the brainwave project, it provides a concise and efficient voice input interface.
"""

import asyncio
import contextlib

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QPushButton, QWidget

from src.services.audio import AudioService, AudioState
from src.utils.loguru_config import get_logger

logger = get_logger(__name__)


class VoiceButton(QPushButton):
    """Simplified voice button component

    A simplified voice button designed based on technical specifications, providing:
    - Unified state management
    - Concise UI feedback
    - Seamless integration with VoiceService_v2
    - Animation effects and visual feedback
    """

    # Signal definitions
    recording_started = Signal()
    recording_stopped = Signal()
    transcription_ready = Signal(str)
    error_occurred = Signal(str)
    state_changed = Signal(str)  # State change signal

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Core properties
        self.voice_service: AudioService | None = None
        self.current_state = AudioState.IDLE
        self._is_recording = False

        # Asynchronous event loop management
        self._event_loop = None
        self._event_loop_thread = None
        self._setup_event_loop()

        # UI properties
        self._pulse_opacity = 1.0
        self.pulse_animation = None  # Initialize animation property
        self._setup_ui()
        self._setup_animations()

        # Connect click event
        self.clicked.connect(self._on_button_clicked)

        logger.info("VoiceButton_v2 initialized.")

    def _setup_event_loop(self):
        """Set up a dedicated event loop thread."""
        import threading

        def run_event_loop():
            """Run the event loop in a dedicated thread."""
            try:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
                logger.info("Voice service event loop has been started.")
                self._event_loop.run_forever()
            except Exception as e:
                logger.error(f"Event loop thread exception: {e}")
            finally:
                logger.info("Voice service event loop has ended.")

        self._event_loop_thread = threading.Thread(target=run_event_loop, daemon=True)
        self._event_loop_thread.start()

        # Wait for the event loop to start
        import time

        timeout = 5.0
        start_time = time.time()
        while self._event_loop is None and (time.time() - start_time) < timeout:
            time.sleep(0.01)

        if self._event_loop is None:
            logger.error("Event loop startup timed out.")
        else:
            logger.info("Voice service event loop is ready.")

    def set_voice_service(self, service: AudioService):
        """Set voice service

        Args:
            service: AudioService instance.
        """
        if self.voice_service:
            # Disconnect from the old service
            self.voice_service.on_state_change = None
            self.voice_service.on_transcription = None
            self.voice_service.on_error = None

        self.voice_service = service
        if service:
            # Connect callbacks for the new service
            service.on_state_change = self._on_state_change
            service.on_transcription = self._on_transcription
            service.on_error = self._on_error

            # Synchronize the current state
            self.current_state = service.state
            self._update_appearance()

            logger.info("Voice service has been connected to VoiceButton.")

    def _setup_ui(self):
        """Set up the UI style."""
        self.setFixedSize(40, 40)
        self.setToolTip("Click to start/stop voice input")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Set the base style
        self._update_appearance()

    def _setup_animations(self):
        """Set up animations."""
        # Pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"pulse_opacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setStartValue(1.0)
        self.pulse_animation.setEndValue(0.3)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop

    @Property(float)
    def pulse_opacity(self):
        return self._pulse_opacity

    @pulse_opacity.setter
    def pulse_opacity(self, value):
        self._pulse_opacity = value
        self.update()  # Trigger a repaint

    def _on_button_clicked(self):
        """Handle button clicks."""
        if not self.voice_service:
            logger.warning("Voice service is not set.")
            self.error_occurred.emit("Voice service is not initialized.")
            return

        try:
            if self.current_state == AudioState.IDLE:
                # Start recording - use QTimer to schedule the asynchronous operation
                QTimer.singleShot(
                    0, lambda: self._schedule_async_operation(self._start_recording())
                )
            elif self.current_state == AudioState.RECORDING:
                # Stop recording - use QTimer to schedule the asynchronous operation
                QTimer.singleShot(
                    0, lambda: self._schedule_async_operation(self._stop_recording())
                )
            else:
                logger.warning(
                    f"Operation not allowed in the current state: {self.current_state}"
                )
        except Exception as e:
            logger.error(f"Button click handling failed: {e}")
            self.error_occurred.emit(f"Operation failed: {str(e)}")

    def _schedule_async_operation(self, coro):
        """Schedule an asynchronous operation - use a dedicated event loop."""
        try:
            if not self._event_loop:
                logger.error("Event loop is not ready.")
                self.error_occurred.emit("Event loop is not ready.")
                return

            # Schedule the task in the dedicated event loop
            future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)

            # Add a completion callback
            def handle_result(fut):
                try:
                    result = fut.result()
                    logger.debug(f"Asynchronous operation complete: {result}")
                except Exception as e:
                    logger.error(f"Asynchronous operation failed: {e}")
                    # Emit the error signal in the main thread
                    QTimer.singleShot(
                        0,
                        lambda: self.error_occurred.emit(
                            f"Asynchronous operation failed: {str(e)}"
                        ),
                    )

            future.add_done_callback(handle_result)

        except Exception as e:
            logger.error(f"Failed to schedule asynchronous operation: {e}")
            self.error_occurred.emit(f"Failed to schedule operation: {str(e)}")

    def _handle_async_task_result(self, task):
        """Handle the result of an asynchronous task."""
        try:
            if task.exception():
                error = task.exception()
                logger.error(f"Asynchronous task execution failed: {error}")
                self.error_occurred.emit(f"Operation execution failed: {str(error)}")
        except Exception as e:
            logger.error(f"Failed to handle the result of the asynchronous task: {e}")

    async def _start_recording(self):
        """Start recording."""
        try:
            logger.info("Starting voice recording.")
            success = await self.voice_service.start_recording()
            if success:
                self.recording_started.emit()
                logger.info("Recording started successfully.")
            else:
                self.error_occurred.emit("Failed to start recording.")
                logger.error("Failed to start recording.")
        except Exception as e:
            logger.error(f"Exception while starting recording: {e}")
            self.error_occurred.emit(f"Exception while starting recording: {str(e)}")

    async def _stop_recording(self):
        """Stop recording."""
        try:
            logger.info("Stopping voice recording.")
            result = await self.voice_service.stop_recording()
            self.recording_stopped.emit()

            if result:
                logger.info(
                    f"Recording complete, transcription result: {result[:50]}..."
                )
                self.transcription_ready.emit(result)
            else:
                logger.warning(
                    "Recording stopped but no transcription result was obtained."
                )
        except Exception as e:
            logger.error(f"Exception while stopping recording: {e}")
            self.error_occurred.emit(f"Exception while stopping recording: {str(e)}")

    def _on_state_change(self, old_state: AudioState, new_state: AudioState):
        """Handle state changes."""
        logger.debug(f"Voice state changed: {old_state} -> {new_state}")
        self.current_state = new_state
        self._update_appearance()
        self.state_changed.emit(new_state.value)

    def _on_transcription(self, text: str):
        """Handle transcription results."""
        logger.info(f"Received transcription result: {text[:50]}...")
        self.transcription_ready.emit(text)

    def _on_error(self, error_message: str):
        """Handle errors."""
        try:
            logger.error(f"Voice service error: {error_message}")

            # Ensure the state is updated correctly
            if self.current_state != AudioState.ERROR:
                self.current_state = AudioState.ERROR
                self._update_appearance()

            # Emit the error signal
            self.error_occurred.emit(error_message)

            # Set an automatic recovery timer (try to recover to IDLE state after 5 seconds)
            if not hasattr(self, "_recovery_timer"):
                self._recovery_timer = QTimer()
                self._recovery_timer.setSingleShot(True)
                self._recovery_timer.timeout.connect(self._attempt_recovery)

            # Start the recovery timer
            self._recovery_timer.start(5000)  # Try to recover after 5 seconds

        except Exception as e:
            logger.error(f"An exception occurred during error handling: {e}")
            # Ensure at least the error signal is emitted
            with contextlib.suppress(Exception):
                self.error_occurred.emit(f"Error handling failed: {str(e)}")

    def _attempt_recovery(self):
        """Attempt to recover from an error state."""
        try:
            logger.info("Attempting to recover from the error state.")

            # Check if the voice service is available
            if self.voice_service and hasattr(self.voice_service, "state_manager"):
                # If the voice service state is normal, recover to the IDLE state
                if self.voice_service.state_manager.current_state in [
                    AudioState.IDLE,
                    AudioState.ERROR,
                ]:
                    self.current_state = AudioState.IDLE
                    self._update_appearance()
                    logger.info("Recovered from the error state to the IDLE state.")
                else:
                    # If the voice service still has issues, delay the recovery attempt again
                    self._recovery_timer.start(10000)  # Try again after 10 seconds
                    logger.warning(
                        "Voice service state is abnormal, will delay the recovery attempt."
                    )
            else:
                logger.warning("Voice service is not available, unable to recover.")

        except Exception as e:
            logger.error(f"State recovery failed: {e}")
            # If recovery fails, remain in the error state

    def _update_appearance(self):
        """Update the button's appearance."""
        # Set the style and animation based on the state
        if self.current_state == AudioState.IDLE:
            self._set_idle_style()
            self._stop_pulse_animation()
        elif self.current_state == AudioState.RECORDING:
            self._set_recording_style()
            self._start_pulse_animation()
        elif self.current_state == AudioState.PROCESSING:
            self._set_processing_style()
            self._stop_pulse_animation()
        elif self.current_state == AudioState.ERROR:
            self._set_error_style()
            self._stop_pulse_animation()

        # Update the tooltip
        self._update_tooltip()

    def _set_idle_style(self):
        """Set the idle state style."""
        self.setStyleSheet(
            """
            QPushButton {
                border-radius: 20px;
                background-color: #4CAF50;
                border: 2px solid #45a049;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #3d8b40;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        )
        self.setText("Rec")

    def _set_connecting_style(self):
        """Set the connecting state style."""
        self.setStyleSheet(
            """
            QPushButton {
                border-radius: 20px;
                background-color: #FF9800;
                border: 2px solid #f57c00;
                color: white;
                font-weight: bold;
            }
        """
        )
        self.setText("...")

    def _set_recording_style(self):
        """Set the recording state style."""
        self.setStyleSheet(
            """
            QPushButton {
                border-radius: 20px;
                background-color: #F44336;
                border: 2px solid #d32f2f;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """
        )
        self.setText("Stop")

    def _set_processing_style(self):
        """Set the processing state style."""
        self.setStyleSheet(
            """
            QPushButton {
                border-radius: 20px;
                background-color: #2196F3;
                border: 2px solid #1976d2;
                color: white;
                font-weight: bold;
            }
        """
        )
        self.setText("...")

    def _set_error_style(self):
        """Set the error state style."""
        self.setStyleSheet(
            """
            QPushButton {
                border-radius: 20px;
                background-color: #9E9E9E;
                border: 2px solid #757575;
                color: white;
                font-weight: bold;
            }
        """
        )
        self.setText("Err")

    def _start_pulse_animation(self):
        """Start the pulse animation."""
        if self.pulse_animation.state() != QPropertyAnimation.State.Running:
            self.pulse_animation.start()

    def _stop_pulse_animation(self):
        """Stop the pulse animation."""
        try:
            if (
                hasattr(self, "pulse_animation")
                and self.pulse_animation
                and self.pulse_animation.state() == QPropertyAnimation.State.Running
            ):
                self.pulse_animation.stop()
            self._pulse_opacity = 1.0
            if hasattr(self, "update"):
                self.update()
        except RuntimeError:
            # Qt object already deleted, ignore
            pass

    def _update_tooltip(self):
        """Update the tooltip."""
        tooltips = {
            AudioState.IDLE: "Click to start voice input",
            AudioState.RECORDING: "Recording, click to stop",
            AudioState.PROCESSING: "Processing voice...",
            AudioState.ERROR: "Voice service error, click to retry",
        }
        self.setToolTip(tooltips.get(self.current_state, "Voice Input"))

    def paintEvent(self, event):
        """Custom paint event, add pulse effect."""
        super().paintEvent(event)

        # Draw the pulse effect in the recording state
        if self.current_state == AudioState.RECORDING and self._pulse_opacity < 1.0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Set the pulse ring
            pen = QPen(Qt.GlobalColor.red)
            pen.setWidth(3)
            painter.setPen(pen)

            # Calculate the opacity and size of the pulse ring
            opacity = int(self._pulse_opacity * 255)
            pen.setColor(pen.color().lighter(150))
            pen.color().setAlpha(opacity)
            painter.setPen(pen)

            # Draw the pulse ring
            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.drawEllipse(rect)

    def _safe_log(self, message: str):
        """Safely log a message, ignoring errors during shutdown."""
        try:
            import sys

            # Don't log if Python is shutting down
            if sys.meta_path is None:
                return
            # Try to log, but catch any errors
            logger.info(message)
        except Exception:
            # Any error during logging, ignore silently
            pass

    def cleanup(self):
        """Clean up resources."""
        try:
            # Check if Python is shutting down
            import sys

            if sys.meta_path is None:
                return  # Python is shutting down, skip cleanup

            # Safe logging - only log if we're not in shutdown
            self._safe_log("Cleaning up VoiceButton resources.")

            # Stop and delete the recovery timer
            if hasattr(self, "_recovery_timer") and self._recovery_timer:
                try:
                    self._recovery_timer.stop()
                    self._recovery_timer.deleteLater()
                    self._recovery_timer = None
                except RuntimeError:
                    pass  # Qt object already deleted

            # Stop and delete the animation
            if hasattr(self, "pulse_animation") and self.pulse_animation:
                self._stop_pulse_animation()
                self.pulse_animation.deleteLater()
                self.pulse_animation = None

            # Disconnect from the voice service
            if hasattr(self, "voice_service") and self.voice_service:
                try:
                    self.voice_service.on_state_change = None
                    self.voice_service.on_transcription = None
                    self.voice_service.on_error = None
                    self.voice_service = None
                except (AttributeError, RuntimeError):
                    pass  # Service already cleaned up or Qt object deleted

            # Stop the event loop
            if hasattr(self, "_event_loop") and self._event_loop:
                try:
                    if self._event_loop.is_running():
                        self._event_loop.call_soon_threadsafe(self._event_loop.stop)
                    self._event_loop = None
                except (AttributeError, RuntimeError):
                    pass

            # Wait for the event loop thread to finish
            if hasattr(self, "_event_loop_thread") and self._event_loop_thread:
                try:
                    if self._event_loop_thread.is_alive():
                        self._event_loop_thread.join(timeout=1.0)
                    self._event_loop_thread = None
                except (AttributeError, RuntimeError):
                    pass

            # Safe logging - only log if we're not in shutdown
            self._safe_log("VoiceButton resources cleaned up.")
        except (ImportError, RuntimeError, AttributeError):
            # Python is shutting down or Qt objects already deleted, ignore
            pass

    def __del__(self):
        """Destructor."""
        with contextlib.suppress(ImportError, RuntimeError, AttributeError):
            self.cleanup()
