import asyncio
import threading

from PySide6.QtCore import (
    Q_ARG,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.services.audio import AudioService, AudioState
from src.utils.loguru_config import logger, get_logger


class AsyncTaskRunner(QObject):
    """Async task executor"""

    def __init__(self):
        super().__init__()
        self.loop = None
        self.thread = None

    def start_loop(self):
        """Start event loop"""
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def _run_loop(self):
        """Run event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async(self, coro):
        """Run async task"""
        if self.loop is None:
            self.start_loop()
            # Wait for loop to start
            import time

            time.sleep(0.1)

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(coro, self.loop)

    def cleanup(self):
        """Clean up resources"""
        if self.loop and not self.loop.is_closed():
            # Stop event loop
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.thread and self.thread.is_alive():
            # Wait for thread to end
            self.thread.join(timeout=2.0)

        self.loop = None
        self.thread = None


class VoiceInputWidget(QWidget):
    """Voice input UI component"""

    # Signal definitions
    voice_result_ready = Signal(str)  # Voice recognition result ready
    voice_error_occurred = Signal(str)  # Voice recognition error

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.voice_service: AudioService | None = None
        self.is_recording = False
        self.current_state = AudioState.IDLE
        self.async_runner = AsyncTaskRunner()
        self.async_runner.start_loop()

        # Track active single-shot timers for proper cleanup
        self._active_timers: set[QTimer] = set()

        self._setup_ui()
        self._setup_shortcuts()
        self._setup_timers()

    def _setup_ui(self):
        """Setup UI interface"""
        self.setFixedSize(400, 300)
        self.setWindowTitle("Voice Input")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
        )

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Status indicator
        self._setup_status_indicator(main_layout)

        # Recording control area
        self._setup_recording_controls(main_layout)

        # Result display area
        self._setup_result_display(main_layout)

        # Apply styles
        self._apply_styles()

    def _setup_status_indicator(self, layout):
        """Setup status indicator"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QHBoxLayout(status_frame)

        # Status label
        self.status_label = QLabel("Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)

        # Status indicator light
        self.status_indicator = QLabel("●")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setStyleSheet("color: #28a745; font-size: 16px;")
        status_layout.addWidget(self.status_indicator)

        layout.addWidget(status_frame)

    def _setup_recording_controls(self, layout):
        """Setup recording controls"""
        controls_layout = QHBoxLayout()

        # Recording button
        self.record_button = QPushButton("Click to Record")
        self.record_button.setMinimumHeight(50)
        self.record_button.setCheckable(True)
        # Only use clicked signal to toggle recording state
        self.record_button.clicked.connect(self._on_button_clicked)
        controls_layout.addWidget(self.record_button)

        # Shortcut hint
        shortcut_label = QLabel("Shortcut: Ctrl+Shift+V | Click to toggle recording")
        shortcut_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        controls_layout.addWidget(shortcut_label)

        layout.addLayout(controls_layout)

    def _setup_result_display(self, layout):
        """Setup result display area"""
        # Result label
        result_label = QLabel("Recognition Result:")
        layout.addWidget(result_label)

        # Result text box
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(80)
        self.result_text.setPlaceholderText(
            "Voice recognition results will be displayed here..."
        )
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def _setup_shortcuts(self):
        """Setup shortcuts"""
        # Ctrl+Shift+V triggers voice input
        self.voice_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        self.voice_shortcut.activated.connect(self._toggle_recording)

    def _setup_timers(self):
        """Setup timers"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(100)  # Update status every 100ms

        # Heartbeat log timer (used during recording)
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._log_heartbeat)
        self.heartbeat_counter = 0

    def _apply_styles(self):
        """Apply styles"""
        self.setStyleSheet(
            """
            VoiceInputWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #dc3545;
            }
            QLabel {
                color: #495057;
                font-weight: 500;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QFrame {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
            }
        """
        )

    def set_voice_service(self, service: AudioService):
        """Set voice input service"""
        self.voice_service = service
        if service:
            # Set service callbacks
            service.set_transcription_callback(self._on_transcription_ready)
            service.set_error_callback(self._on_error_occurred)

    def _on_button_clicked(self):
        """Button click handler"""
        try:
            self._toggle_recording()
        except Exception as e:
            self.logger.error(f"Button click handling failed: {e}")
            self._show_error(f"Operation failed: {str(e)}")

    def _start_recording(self):
        """Start recording"""
        try:
            if self.is_recording:
                self.logger.warning(
                    "Recording already in progress, ignoring duplicate request"
                )
                return

            self.logger.info("Starting recording...")
            self.is_recording = True
            self.record_button.setText("Stop Recording")
            self.record_button.setChecked(True)

            # Start heartbeat logging
            self.heartbeat_timer.start(5000)  # Log heartbeat every 5 seconds

            # Clear previous results
            self.result_text.clear()

            # Start recording service
            self.async_runner.run_async(self.voice_service.start_voice_input())

        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self._reset_recording_state()
            self._show_error(f"Failed to start recording: {str(e)}")

    def _stop_recording(self):
        """Stop recording"""
        try:
            if not self.is_recording:
                self.logger.warning("Not currently recording, ignoring stop request")
                return

            self.logger.info("Stopping recording...")
            self.is_recording = False
            self.record_button.setText("Click to Record")
            self.record_button.setChecked(False)

            # Stop heartbeat logging
            self.heartbeat_timer.stop()

            # Stop recording service
            self.async_runner.run_async(self.voice_service.stop_voice_input())

        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self._reset_recording_state()
            self._show_error(f"Failed to stop recording: {str(e)}")

    def _toggle_recording(self):
        """Toggle recording state"""
        try:
            if self.is_recording:
                self.logger.info("User requested to stop recording")
                self._stop_recording()
            else:
                self.logger.info("User requested to start recording")
                self._start_recording()
        except Exception as e:
            self.logger.error(f"Failed to toggle recording state: {e}")
            self._show_error(f"Recording operation failed: {str(e)}")

    def _update_status(self):
        """Update status display"""
        if not self.voice_service:
            return

        # Get current state
        current_state = self.voice_service.voice_state_manager.current_state

        if current_state != self.current_state:
            self.current_state = current_state
            self._update_status_display()

    def _update_status_display(self):
        """Update status display"""
        # 简化状态映射 - 移除不需要的连接状态
        state_info = {
            AudioState.IDLE: ("Idle", "#28a745"),
            AudioState.RECORDING: ("Recording", "#dc3545"),
            AudioState.PROCESSING: ("Processing", "#6f42c1"),
            AudioState.ERROR: ("Error", "#dc3545"),
        }

        text, color = state_info.get(self.current_state, ("Unknown", "#6c757d"))
        self.status_label.setText(text)
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 16px;")

        # Update button text based on state
        if self.current_state == AudioState.IDLE:
            self.record_button.setText("Start Recording")
            self.record_button.setEnabled(True)
        elif self.current_state == AudioState.RECORDING:
            self.record_button.setText("Stop Recording")
            self.record_button.setEnabled(True)
        elif self.current_state == AudioState.PROCESSING:
            self.record_button.setText("Processing...")
            self.record_button.setEnabled(False)
        elif self.current_state == AudioState.ERROR:
            self.record_button.setText("Retry")
            self.record_button.setEnabled(True)

    def _on_transcription_ready(self, text: str):
        """Handle transcription results"""
        self.logger.info(
            f"[E2E-DEBUG] _on_transcription_ready called, received text: '{text}'",
            extra={"category": category.value},
        )

        # Use QMetaObject.invokeMethod to ensure UI updates are executed in the main thread
        QMetaObject.invokeMethod(
            self, "_update_transcription_ui", Qt.QueuedConnection, Q_ARG(str, text)
        )

        self.logger.info(
            f"[E2E-DEBUG] Voice recognition completed: {text[:50]}...",
            extra={"category": category.value},
        )

    def _on_error_occurred(self, error_type: str, error_message: str):
        """Handle errors"""
        error_text = f"{error_type}: {error_message}"

        # Use QMetaObject.invokeMethod to ensure UI updates are executed in the main thread
        QMetaObject.invokeMethod(
            self, "_update_error_ui", Qt.QueuedConnection, Q_ARG(str, error_text)
        )

    def _show_error(self, message: str):
        """Display error information"""
        self.result_text.setPlainText(f"Error: {message}")
        self.result_text.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #dc3545;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8d7da;
                color: #721c24;
            }
        """
        )
        self.logger.error(
            f"Voice input error: {message}", extra={"category": category.value}
        )

        # Restore normal style after 3 seconds
        self._create_single_shot_timer(3000, self._reset_result_style)

    def _reset_result_style(self):
        """Reset result display style"""
        self.result_text.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """
        )



    async def _reinitialize_voice_service(self):
        """Reinitialize voice service"""
        try:
            self.logger.info(
                "[DEBUG] Starting voice service reinitialization",
                extra={"category": category.value},
            )

            # Clean up existing connections
            if self.voice_service:
                await self.voice_service.cleanup()

            # Reinitialize
            await self.voice_service.initialize()

            self.logger.info(
                "[DEBUG] Voice service reinitialization completed",
                extra={"category": category.value},
            )

        except Exception as e:
            self.logger.error(
                f"[DEBUG] Voice service reinitialization failed: {str(e)}",
                extra={"category": category.value},
            )
            self._show_error(f"Voice service initialization failed: {str(e)}")

    def _log_heartbeat(self):
        """Output heartbeat log"""
        self.heartbeat_counter += 1
        if self.is_recording:
            # Get current state information
            state_text = "Unknown"
            if self.voice_service and hasattr(
                self.voice_service, "voice_state_manager"
            ):
                current_state = self.voice_service.voice_state_manager.current_state
                # 简化状态文本映射
                state_map = {
                    AudioState.IDLE: "Idle",
                    AudioState.RECORDING: "Recording",
                    AudioState.PROCESSING: "Processing",
                    AudioState.ERROR: "Error",
                }
                state_text = state_map.get(current_state, "Unknown")

            self.logger.info(
                f"[HEARTBEAT] Recording in progress - {self.heartbeat_counter} seconds | Status: {state_text} | Button text: {self.record_button.text()}",
                extra={"category": category.value},
            )
        else:
            # If not in recording state, stop heartbeat
            self.heartbeat_timer.stop()
            self.logger.info(
                "[HEARTBEAT] Recording ended, heartbeat logging stopped",
                extra={"category": category.value},
            )

    @Slot(str)
    def _update_transcription_ui(self, text: str):
        """Update transcription result UI in main thread"""
        self.logger.info(
            "[E2E-DEBUG] Setting UI text box content",
            extra={"category": category.value},
        )
        self.result_text.setPlainText(text)

        self.logger.info(
            "[E2E-DEBUG] Emitting voice_result_ready signal",
            extra={"category": category.value},
        )
        self.voice_result_ready.emit(text)

    @Slot(str)
    def _update_error_ui(self, error_text: str):
        """Update error UI in main thread"""
        self._show_error(error_text)
        self.voice_error_occurred.emit(error_text)

    def _create_single_shot_timer(self, delay_ms: int, callback):
        """Create a tracked single-shot timer for proper cleanup"""
        try:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._on_timer_finished(timer, callback))
            self._active_timers.add(timer)
            timer.start(delay_ms)
            return timer
        except RuntimeError:
            # Qt object already deleted, ignore
            return None

    def _on_timer_finished(self, timer: QTimer, callback):
        """Handle timer completion and cleanup"""
        try:
            # Remove from active timers
            self._active_timers.discard(timer)
            # Execute callback
            if callback:
                callback()
            # Clean up timer
            timer.deleteLater()
        except RuntimeError:
            # Qt object already deleted, ignore
            pass

    def _cleanup_active_timers(self):
        """Clean up all active timers"""
        try:
            # Check if Python is shutting down
            import sys

            if sys.meta_path is None:
                return  # Python is shutting down, skip cleanup

            for timer in list(self._active_timers):
                try:
                    if timer and timer.thread() == self.thread():
                        timer.stop()
                        timer.deleteLater()
                except RuntimeError:
                    # Timer already deleted, ignore
                    pass
            self._active_timers.clear()
        except (ImportError, RuntimeError, AttributeError):
            # Python is shutting down or Qt objects already deleted, ignore
            pass

    def cleanup(self):
        """Clean up resources"""
        try:
            # Clean up active timers first
            self._cleanup_active_timers()

            # Stop recording
            if self.is_recording:
                self._stop_recording()

            # Stop timers
            if hasattr(self, "status_timer") and self.status_timer:
                self.status_timer.stop()
                self.status_timer = None

            if hasattr(self, "heartbeat_timer") and self.heartbeat_timer:
                self.heartbeat_timer.stop()
                self.heartbeat_timer = None

            # Clean up async task executor
            if hasattr(self, "async_runner") and self.async_runner:
                self.async_runner.cleanup()
                self.async_runner = None

            # Clean up voice service reference
            self.voice_service = None

        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"VoiceInputWidget cleanup error: {e}")
