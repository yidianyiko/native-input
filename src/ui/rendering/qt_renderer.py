"""Qt Native Renderer
Simplified renderer using Qt's built-in rendering capabilities and styling system
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect

from src.utils.loguru_config import logger, get_logger


class QtRenderer(QObject):
    """Simplified Qt-based renderer for transparent overlays"""

    # Signals
    render_completed = Signal()
    render_failed = Signal(str)

    def __init__(self, widget: QWidget):
        super().__init__()
        self.logger = get_logger(__name__)
        self.widget = widget

        # Rendering state
        self.is_initialized = False
        self.theme = "dark"
        self.opacity = 0.9
        self.blur_radius = 0.0

        # Initialize Qt renderer
        self._initialize_qt_renderer()

    def _initialize_qt_renderer(self) -> bool:
        """Initialize Qt renderer with transparent window attributes"""
        try:
            logger.info("Initializing Qt native renderer")

            # Set window attributes for transparency
            self.widget.setAttribute(Qt.WA_TranslucentBackground, True)
            self.widget.setWindowFlags(
                self.widget.windowFlags() | 
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint
            )

            self.is_initialized = True
            logger.info("Qt native renderer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Qt renderer: {str(e)}")
            return False

    def render_transparent_background(
        self, opacity: float = 0.9, color: QColor = None, blur_radius: float = 0.0
    ) -> bool:
        """Render transparent background using Qt styling
        
        Args:
            opacity: Background opacity (0.0 to 1.0)
            color: Background color (default: dark gray)
            blur_radius: Background blur radius for shadow effect (0.0 to disable)

        Returns:
            True if rendering succeeded
        """
        if not self.is_initialized:
            logger.error("Qt renderer not initialized")
            return False

        try:
            # Default color
            if color is None:
                color = QColor(30, 30, 30)  # Dark gray

            # Clamp opacity
            opacity = max(0.0, min(1.0, opacity))

            # Apply Qt styling
            self._apply_qt_styling(color, opacity, blur_radius)

            # Add shadow effect if blur is requested
            if blur_radius > 0.0:
                self._apply_shadow_effect(blur_radius)

            self.render_completed.emit()
            return True

        except Exception as e:
            logger.error(f"Error rendering transparent background: {str(e)}")
            self.render_failed.emit(str(e))
            return False

    def _apply_qt_styling(self, color: QColor, opacity: float, blur_radius: float):
        """Apply Qt stylesheet for transparent background"""
        try:
            # Convert color to RGBA
            r, g, b = color.red(), color.green(), color.blue()
            alpha = int(opacity * 255)

            # Create stylesheet with rounded corners and transparency
            style = f"""
                QWidget {{
                    background-color: rgba({r}, {g}, {b}, {alpha});
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
            """

            self.widget.setStyleSheet(style)
            logger.info(f"Applied Qt styling: RGBA({r}, {g}, {b}, {alpha})")

        except Exception as e:
            logger.error(f"Error applying Qt styling: {str(e)}")

    def _apply_shadow_effect(self, blur_radius: float):
        """Apply shadow effect using QGraphicsDropShadowEffect"""
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(blur_radius)
            shadow.setColor(QColor(0, 0, 0, 100))  # Semi-transparent black
            shadow.setOffset(0, 2)  # Slight downward offset

            self.widget.setGraphicsEffect(shadow)
            logger.info(f"Applied shadow effect with blur radius: {blur_radius}")

        except Exception as e:
            logger.error(f"Error applying shadow effect: {str(e)}")

    def set_theme(self, theme: str):
        """Set rendering theme
        
        Args:
            theme: Theme name ('dark' or 'light')
        """
        self.theme = theme
        logger.info(f"Qt renderer theme set to: {theme}")

    def set_blur_radius(self, radius: float):
        """Set background blur radius for shadow effect
        
        Args:
            radius: Blur radius in pixels (0.0 to disable)
        """
        self.blur_radius = max(0.0, radius)
        logger.info(f"Qt renderer blur radius set to: {self.blur_radius}px")

    def set_opacity(self, opacity: float):
        """Set rendering opacity
        
        Args:
            opacity: Opacity value (0.0 to 1.0)
        """
        self.opacity = max(0.0, min(1.0, opacity))
        self.widget.setWindowOpacity(self.opacity)
        logger.info(f"Qt renderer opacity set to: {self.opacity:.2f}")

    def resize(self, width: int, height: int) -> bool:
        """Resize widget (Qt handles this automatically)"""
        try:
            logger.info(f"Qt renderer handling resize to {width}x{height}")
            # Qt automatically handles resize, no special action needed
            return True

        except Exception as e:
            logger.error(f"Error handling resize: {str(e)}")
            return False

    def cleanup(self):
        """Clean up Qt renderer resources"""
        try:
            logger.info("Cleaning up Qt renderer resources")

            # Remove graphics effects
            if self.widget.graphicsEffect():
                self.widget.setGraphicsEffect(None)

            # Clear stylesheet
            self.widget.setStyleSheet("")

            self.is_initialized = False
            logger.info("Qt renderer cleanup completed")

        except Exception as e:
            logger.error(f"Error during Qt renderer cleanup: {str(e)}")

    def is_hardware_accelerated(self) -> bool:
        """Check if hardware acceleration is available (Qt handles this internally)"""
        return True  # Qt uses hardware acceleration when available

    def get_performance_stats(self) -> dict:
        """Get rendering performance statistics (simplified for Qt)"""
        return {
            "renderer_type": "Qt Native",
            "is_hardware_accelerated": True,
            "theme": self.theme,
            "opacity": self.opacity,
            "blur_radius": self.blur_radius
        }

    def get_adapter_info(self) -> dict:
        """Get graphics adapter information (Qt abstracts this)"""
        return {
            "adapter_name": "Qt Native Renderer",
            "renderer_type": "Qt",
            "cross_platform": True
        }

    def enable_hardware_acceleration(self, enabled: bool):
        """Enable or disable hardware acceleration (Qt handles this automatically)
        
        Args:
            enabled: True to enable hardware acceleration (ignored, Qt decides)
        """
        logger.info(f"Hardware acceleration request: {'enabled' if enabled else 'disabled'} (Qt manages automatically)")