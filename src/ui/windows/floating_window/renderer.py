"""
Window Renderer Module - Extracted from FloatingWindow
Handles Qt native rendering operations, animation handling, and resource management.
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget

from src.ui.rendering.qt_renderer import QtRenderer
from src.utils.loguru_config import logger, get_logger


class WindowRenderer(QObject):
    """Manages window rendering, animations, and visual effects using Qt native capabilities."""
    
    # Signals
    renderer_initialized = Signal(bool)  # success
    animation_started = Signal(str)  # animation_name
    animation_finished = Signal(str)  # animation_name
    theme_changed = Signal(str)  # theme_name
    
    def __init__(self, target_widget: QWidget, config_manager):
        super().__init__()
        self.target_widget = target_widget
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Qt renderer for native rendering
        self.qt_renderer: Optional[QtRenderer] = None
        
        # Animation system
        self.animations: Dict[str, QPropertyAnimation] = {}
        self.height_animation: Optional[QPropertyAnimation] = None
        
        # Window heights for three-state system
        self.window_heights = {
            "initial": 120,  # 增加8px以适应更高的输入框
            "input": 184,    # 增加8px以适应更高的输入框
            "complete": 232  # 增加8px以适应更高的输入框
        }
        
        # Initialize renderer and animations
        self._init_qt_renderer()
        self._setup_animations()
        
        logger.info("WindowRenderer initialized")
    
    def _init_qt_renderer(self) -> None:
        """Initialize Qt renderer for native rendering."""
        try:
            self.qt_renderer = QtRenderer(self.target_widget)
            
            if self.qt_renderer.is_initialized:
                logger.info("Qt renderer initialized successfully")
                self.renderer_initialized.emit(True)
            else:
                logger.error("Qt renderer initialization failed")
                self.qt_renderer = None
                self.renderer_initialized.emit(False)
                
        except Exception as e:
            logger.error(f"Error initializing Qt renderer: {e}")
            self.qt_renderer = None
            self.renderer_initialized.emit(False)
    
    def _setup_animations(self) -> None:
        """Setup animation system for window state transitions."""
        try:
            # Height animation for three-state window system
            self.height_animation = QPropertyAnimation(self.target_widget, b"maximumHeight")
            self.height_animation.setDuration(300)  # 300ms animation
            self.height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.height_animation.finished.connect(self._on_height_animation_finished)
            
            self.animations["height"] = self.height_animation
            
            logger.info("Animation system setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup animations: {e}")
    
    def animate_to_state(self, state: str) -> None:
        """Animate window to specified state."""
        try:
            # Handle both state names and height values
            target_height = None
            
            if state in self.window_heights:
                # Direct state name (e.g., "initial", "input", "complete")
                target_height = self.window_heights[state]
            elif state.startswith("height_"):
                # Height-based state name (e.g., "height_224")
                try:
                    target_height = int(state.replace("height_", ""))
                except ValueError:
                    logger.error(f"Invalid height format: {state}")
                    return
            else:
                logger.error(f"Unknown window state: {state}")
                return
            
            if self.height_animation and target_height:
                # Clear previous size constraints
                current_height = self.target_widget.height()
                min_height = min(current_height, target_height)
                max_height = max(current_height, target_height)
                self.target_widget.setMinimumHeight(min_height)
                self.target_widget.setMaximumHeight(max_height)
                
                # Set animation values
                self.height_animation.setStartValue(current_height)
                self.height_animation.setEndValue(target_height)
                self.height_animation.start()
                
                self.animation_started.emit(f"height_to_{target_height}")
                logger.info(f"Animating to height: {target_height}px (from state: {state})")
            
        except Exception as e:
            logger.error(f"Failed to animate to state {state}: {e}")
    
    def animate_to_height(self, target_height: int) -> None:
        """Directly animate to a specific height."""
        try:
            if self.height_animation:
                # Clear previous size constraints
                current_height = self.target_widget.height()
                min_height = min(current_height, target_height)
                max_height = max(current_height, target_height)
                self.target_widget.setMinimumHeight(min_height)
                self.target_widget.setMaximumHeight(max_height)
                
                # Set animation values
                self.height_animation.setStartValue(current_height)
                self.height_animation.setEndValue(target_height)
                self.height_animation.start()
                
                self.animation_started.emit(f"height_to_{target_height}")
                logger.info(f"Animating directly to height: {target_height}px")
            
        except Exception as e:
            logger.error(f"Failed to animate to height {target_height}: {e}")
    
    def _on_height_animation_finished(self) -> None:
        """Handle height animation completion."""
        try:
            # Update fixed size to match the animated height
            if self.height_animation:
                final_height = self.height_animation.endValue()
                current_width = self.target_widget.width()
                self.target_widget.setFixedSize(current_width, final_height)
                
                logger.info(f"Height animation completed")
                
            self.animation_finished.emit("height")
            
        except Exception as e:
            logger.error(f"Error handling animation completion: {e}")
    
    def setup_qt_styling(self, transparency: float, theme: str, font_size: int) -> None:
        """Setup Qt styling using native Qt renderer."""
        try:
            if not self.qt_renderer or not self.qt_renderer.is_initialized:
                logger.error("Qt renderer not available for styling")
                return

            # Configure Qt renderer
            self.qt_renderer.set_opacity(transparency)
            self.qt_renderer.set_theme(theme)
            
            # Apply blur effect for enhanced appearance
            blur_radius = self.config_manager.get("ui.floating_window.blur_radius", 5.0)
            self.qt_renderer.set_blur_radius(blur_radius)
            
            # Render transparent background with styling
            color = self._get_theme_color(theme)
            self.qt_renderer.render_transparent_background(transparency, color, blur_radius)
            
            self.theme_changed.emit(theme)
            logger.info(f"Qt styling applied (theme: {theme})")
            
        except Exception as e:
            logger.error(f"Error applying Qt styling: {e}")

    def _get_theme_color(self, theme: str) -> 'QColor':
        """Get theme-appropriate background color."""
        from PySide6.QtGui import QColor
        
        if theme == "light":
            return QColor(255, 255, 255)  # White
        else:  # dark or auto
            return QColor(30, 30, 30)  # Dark gray
    
    def apply_styling(self, transparency: float, theme: str, font_size: int) -> None:
        """Apply styling using Qt native renderer."""
        try:
            # Always use Qt styling (simplified approach)
            self.setup_qt_styling(transparency, theme, font_size)
                
        except Exception as e:
            logger.error(f"Error applying styling: {e}")
    
    def set_opacity(self, opacity: float) -> None:
        """Set window opacity."""
        try:
            if self.qt_renderer and self.qt_renderer.is_initialized:
                self.qt_renderer.set_opacity(opacity)
            else:
                self.target_widget.setWindowOpacity(opacity)
                
            logger.info(f"Opacity set to: {opacity}")
            
        except Exception as e:
            logger.error(f"Failed to set opacity: {e}")
    
    def set_blur_radius(self, radius: float) -> None:
        """Set blur radius for shadow effects."""
        try:
            if self.qt_renderer and self.qt_renderer.is_initialized:
                self.qt_renderer.set_blur_radius(radius)
                logger.info(f"Blur radius set to: {radius}")
            else:
                logger.info("Blur radius not supported without Qt renderer")
                
        except Exception as e:
            logger.error(f"Failed to set blur radius: {e}")
    
    def enable_hardware_acceleration(self, enabled: bool) -> None:
        """Enable or disable hardware acceleration (Qt handles automatically)."""
        try:
            if self.qt_renderer and self.qt_renderer.is_initialized:
                self.qt_renderer.enable_hardware_acceleration(enabled)
                logger.info(f"Hardware acceleration: {'enabled' if enabled else 'disabled'}")
            else:
                logger.info("Hardware acceleration managed by Qt automatically")
                
        except Exception as e:
            logger.error(f"Failed to set hardware acceleration: {e}")
    
    def get_animation(self, name: str) -> Optional[QPropertyAnimation]:
        """Get animation by name."""
        return self.animations.get(name)
    
    def is_qt_renderer_available(self) -> bool:
        """Check if Qt renderer is available and initialized."""
        return self.qt_renderer is not None and self.qt_renderer.is_initialized

    def get_renderer_info(self) -> Dict[str, Any]:
        """Get information about the current renderer."""
        return {
            "qt_renderer_available": self.is_qt_renderer_available(),
            "renderer_type": "Qt Native",
            "animations_count": len(self.animations),
            "window_heights": self.window_heights
        }
    
    def cleanup(self) -> None:
        """Clean up renderer resources."""
        try:
            # Stop all animations
            for animation in self.animations.values():
                if animation.state() == QPropertyAnimation.State.Running:
                    animation.stop()
            
            self.animations.clear()
            
            # Cleanup Qt renderer
            if self.qt_renderer:
                self.qt_renderer.cleanup()
                self.qt_renderer = None
            
            logger.info("WindowRenderer cleanup completed")
            
        except Exception as e:
            logger.error(f"WindowRenderer cleanup failed: {e}")