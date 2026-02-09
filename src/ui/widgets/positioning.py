"""
Simplified Window Positioning Module
Uses Qt6 built-in APIs for cursor following, multi-monitor support, and screen geometry.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, QPoint, QRect, Signal
from PySide6.QtGui import QCursor, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from src.utils.loguru_config import logger, get_logger


class PositionStrategy(Enum):
    """Window positioning strategies"""
    CURSOR_FOLLOW = "cursor_follow"
    SCREEN_CENTER = "screen_center"
    EDGE_AVOID = "edge_avoid"


@dataclass
class PositionConfig:
    """Configuration for window positioning"""
    cursor_offset: QPoint = QPoint(10, -10)
    boundary_margin: int = 20
    edge_threshold: int = 50
    multi_monitor_enabled: bool = True


@dataclass
class PositionResult:
    """Result of positioning calculation"""
    position: QPoint
    strategy_used: PositionStrategy
    screen_used: Optional[QScreen]
    success: bool = True


class WindowPositioning(QObject):
    """
    Simplified window positioning system using Qt6 built-in APIs.
    
    Features:
    - Cursor following with configurable offsets
    - Multi-monitor support using QApplication.screenAt()
    - Screen geometry calculations using QScreen APIs
    - Edge avoidance using Qt's geometry methods
    """
    
    # Signals
    position_calculated = Signal(QPoint, str)  # position, strategy
    screen_changed = Signal(QScreen)  # new screen
    
    def __init__(self, target_widget: QWidget, config: Optional[PositionConfig] = None):
        super().__init__()
        self.logger = get_logger(__name__)
        self.target_widget = target_widget
        self.config = config or PositionConfig()
        self.current_screen: Optional[QScreen] = None
        
        logger.info("WindowPositioning initialized")
    
    def calculate_position(self, strategy: PositionStrategy = PositionStrategy.CURSOR_FOLLOW) -> PositionResult:
        """
        Calculate optimal window position using specified strategy.
        
        Args:
            strategy: Positioning strategy to use
            
        Returns:
            PositionResult with calculated position and metadata
        """
        try:
            # Get current cursor position using Qt API
            cursor_pos = QCursor.pos()
            
            # Get screen for cursor position using Qt6 built-in method
            screen = self._get_screen_for_cursor(cursor_pos)
            if screen != self.current_screen:
                self.current_screen = screen
                self.screen_changed.emit(screen)
            
            # Get screen geometry using Qt API
            screen_rect = screen.availableGeometry()
            widget_size = self.target_widget.size()
            
            # Calculate position based on strategy
            if strategy == PositionStrategy.CURSOR_FOLLOW:
                position = self._calculate_cursor_follow_position(cursor_pos, widget_size, screen_rect)
            elif strategy == PositionStrategy.SCREEN_CENTER:
                position = self._calculate_center_position(widget_size, screen_rect)
            elif strategy == PositionStrategy.EDGE_AVOID:
                position = self._calculate_edge_avoid_position(cursor_pos, widget_size, screen_rect)
            else:
                position = self._calculate_cursor_follow_position(cursor_pos, widget_size, screen_rect)
            
            # Create result
            result = PositionResult(
                position=position,
                strategy_used=strategy,
                screen_used=screen
            )
            
            # Emit signals
            self.position_calculated.emit(position, strategy.value)
            
            logger.debug(f"Position calculated: ({position.x()}, {position.y()}) using {strategy.value}")
            return result
            
        except Exception as e:
            logger.error(f"Position calculation failed: {e}")
            
            # Return fallback position using Qt API
            fallback_pos = self._get_fallback_position()
            return PositionResult(
                position=fallback_pos,
                strategy_used=PositionStrategy.SCREEN_CENTER,
                screen_used=QApplication.primaryScreen(),
                success=False
            )
    
    def _get_screen_for_cursor(self, cursor_pos: QPoint) -> QScreen:
        """Get the screen containing the cursor position using Qt6 API."""
        if self.config.multi_monitor_enabled:
            # Use Qt6's built-in method to find screen at cursor position
            screen = QApplication.screenAt(cursor_pos)
            if screen:
                return screen
        
        # Fallback to primary screen
        return QApplication.primaryScreen()
    
    def _calculate_cursor_follow_position(self, cursor_pos: QPoint, widget_size, screen_rect: QRect) -> QPoint:
        """Calculate position that follows cursor with boundary detection using Qt geometry."""
        # Apply cursor offset
        position = cursor_pos + self.config.cursor_offset
        
        # Use Qt's QRect methods for boundary checking
        widget_rect = QRect(position, widget_size)
        
        # Adjust if widget would go outside screen bounds
        if not screen_rect.contains(widget_rect):
            # Try positioning to the left of cursor
            if widget_rect.right() > screen_rect.right():
                position.setX(cursor_pos.x() - widget_size.width() - abs(self.config.cursor_offset.x()))
            
            # Try positioning above cursor
            if widget_rect.bottom() > screen_rect.bottom():
                position.setY(cursor_pos.y() - widget_size.height() - abs(self.config.cursor_offset.y()))
            
            # Ensure minimum margins using Qt geometry methods
            position = self._ensure_margins(position, widget_size, screen_rect)
        
        return position
    
    def _calculate_center_position(self, widget_size, screen_rect: QRect) -> QPoint:
        """Calculate center position on screen using Qt geometry."""
        # Use Qt's center calculation
        widget_rect = QRect(QPoint(0, 0), widget_size)
        centered_rect = widget_rect
        centered_rect.moveCenter(screen_rect.center())
        return centered_rect.topLeft()
    
    def _calculate_edge_avoid_position(self, cursor_pos: QPoint, widget_size, screen_rect: QRect) -> QPoint:
        """Calculate position that avoids screen edges using Qt geometry."""
        # Start with cursor follow
        position = self._calculate_cursor_follow_position(cursor_pos, widget_size, screen_rect)
        
        # Check if too close to edges using Qt geometry methods
        widget_rect = QRect(position, widget_size)
        margins = QRect(
            screen_rect.left() + self.config.edge_threshold,
            screen_rect.top() + self.config.edge_threshold,
            screen_rect.width() - 2 * self.config.edge_threshold,
            screen_rect.height() - 2 * self.config.edge_threshold
        )
        
        # If widget is too close to edges, move towards center
        if not margins.contains(widget_rect):
            center_pos = self._calculate_center_position(widget_size, screen_rect)
            # Move 30% towards center using Qt point arithmetic
            offset = (center_pos - position) * 0.3
            position += QPoint(int(offset.x()), int(offset.y()))
        
        return position
    
    def _ensure_margins(self, position: QPoint, widget_size, screen_rect: QRect) -> QPoint:
        """Ensure minimum margins from screen edges using Qt geometry."""
        # Use Qt's adjusted method to keep within bounds
        widget_rect = QRect(position, widget_size)
        margin_rect = screen_rect.adjusted(
            self.config.boundary_margin,
            self.config.boundary_margin,
            -self.config.boundary_margin,
            -self.config.boundary_margin
        )
        
        # Clamp widget position to margin rectangle
        if widget_rect.left() < margin_rect.left():
            position.setX(margin_rect.left())
        elif widget_rect.right() > margin_rect.right():
            position.setX(margin_rect.right() - widget_size.width())
        
        if widget_rect.top() < margin_rect.top():
            position.setY(margin_rect.top())
        elif widget_rect.bottom() > margin_rect.bottom():
            position.setY(margin_rect.bottom() - widget_size.height())
        
        return position
    
    def _get_fallback_position(self) -> QPoint:
        """Get fallback position using Qt API."""
        try:
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            widget_size = self.target_widget.size()
            
            # Use Qt geometry to calculate center
            return self._calculate_center_position(widget_size, screen_rect)
        except Exception:
            return QPoint(100, 100)  # Last resort
    
    # Public API methods
    
    def set_cursor_offset(self, offset: QPoint):
        """Set cursor offset for positioning."""
        self.config.cursor_offset = offset
        logger.info(f"Cursor offset set to: ({offset.x()}, {offset.y()})")
    
    def set_boundary_margin(self, margin: int):
        """Set boundary margin in pixels."""
        self.config.boundary_margin = max(0, margin)
        logger.info(f"Boundary margin set to: {self.config.boundary_margin}px")
    
    def set_edge_threshold(self, threshold: int):
        """Set edge avoidance threshold in pixels."""
        self.config.edge_threshold = max(0, threshold)
        logger.info(f"Edge threshold set to: {self.config.edge_threshold}px")
    
    def enable_multi_monitor(self, enabled: bool):
        """Enable or disable multi-monitor support."""
        self.config.multi_monitor_enabled = enabled
        logger.info(f"Multi-monitor support: {'enabled' if enabled else 'disabled'}")
    
    def get_screen_geometry(self) -> dict:
        """Get current screen geometry information using Qt API."""
        if not self.current_screen:
            self.current_screen = QApplication.primaryScreen()
        
        geometry = self.current_screen.geometry()
        available_geometry = self.current_screen.availableGeometry()
        
        return {
            "screen_name": self.current_screen.name(),
            "geometry": {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height()
            },
            "available_geometry": {
                "x": available_geometry.x(),
                "y": available_geometry.y(),
                "width": available_geometry.width(),
                "height": available_geometry.height()
            },
            "device_pixel_ratio": self.current_screen.devicePixelRatio()
        }
    
    def get_all_screens(self) -> list[dict]:
        """Get information about all available screens using Qt API."""
        screens = []
        for screen in QApplication.screens():
            geometry = screen.geometry()
            available_geometry = screen.availableGeometry()
            
            screens.append({
                "name": screen.name(),
                "primary": screen == QApplication.primaryScreen(),
                "geometry": {
                    "x": geometry.x(),
                    "y": geometry.y(),
                    "width": geometry.width(),
                    "height": geometry.height()
                },
                "available_geometry": {
                    "x": available_geometry.x(),
                    "y": available_geometry.y(),
                    "width": available_geometry.width(),
                    "height": available_geometry.height()
                },
                "device_pixel_ratio": screen.devicePixelRatio()
            })
        
        return screens