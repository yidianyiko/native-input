"""
Credentials Error Dialog
Shows when no API credentials are available and guides user to configure them
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)


class CredentialsErrorDialog(QDialog):
    """Dialog shown when no API credentials are configured"""
    
    login_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, missing_info: dict, parent=None):
        super().__init__(parent)
        self.missing_info = missing_info
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup credentials error dialog UI"""
        self.setWindowTitle("API Credentials Required")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        # Set window icon
        from PySide6.QtGui import QIcon
        from pathlib import Path
        
        icon_path = Path(__file__).parent.parent.parent.parent / "resources" / "icons" / "icon.png"
        if icon_path.exists():
            dialog_icon = QIcon(str(icon_path))
            self.setWindowIcon(dialog_icon)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        
        # Icon and title
        title_layout = QHBoxLayout()
        
        icon_label = QLabel("🔑")
        icon_label.setStyleSheet("font-size: 48px;")
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("API Credentials Required")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 15px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Description
        desc_label = QLabel(
            "No API credentials are configured. You need to either login to get gateway access "
            "or configure provider-specific API keys to use AI features."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px 0;")
        header_layout.addWidget(desc_label)
        
        layout.addLayout(header_layout)
        
        # Missing credentials info
        if self.missing_info:
            info_frame = QFrame()
            info_frame.setFrameStyle(QFrame.Box)
            info_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; }")
            
            info_layout = QVBoxLayout(info_frame)
            
            info_title = QLabel("Missing Credentials:")
            info_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            info_layout.addWidget(info_title)
            
            for key, message in self.missing_info.items():
                info_label = QLabel(f"• {message}")
                info_label.setStyleSheet("margin-left: 10px; color: #dc3545;")
                info_layout.addWidget(info_label)
            
            layout.addWidget(info_frame)
        
        # Options
        options_layout = QVBoxLayout()
        
        options_title = QLabel("Choose an option:")
        options_title.setStyleSheet("font-weight: bold; margin: 20px 0 10px 0;")
        options_layout.addWidget(options_title)
        
        # Option 1: Login
        login_frame = self._create_option_frame(
            "Login for Gateway Access",
            "Login to get unified gateway credentials that work with all AI models.",
            "Login",
            self._on_login_clicked
        )
        options_layout.addWidget(login_frame)
        
        # Option 2: Configure providers
        settings_frame = self._create_option_frame(
            "⚙️ Configure Provider Keys",
            "Configure API keys for specific providers (DeepSeek, OpenAI, etc.) in Settings.",
            "Open Settings",
            self._on_settings_clicked
        )
        options_layout.addWidget(settings_frame)
        
        layout.addLayout(options_layout)
        
        layout.addStretch()
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        close_layout.addWidget(close_button)
        
        layout.addLayout(close_layout)
    
    def _create_option_frame(self, title: str, description: str, button_text: str, callback):
        """Create an option frame with title, description and button"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }")
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        button = QPushButton(button_text)
        button.setMinimumWidth(120)
        button.clicked.connect(callback)
        button_layout.addWidget(button)
        
        layout.addLayout(button_layout)
        
        return frame
    
    def _on_login_clicked(self):
        """Handle login button click"""
        self.login_requested.emit()
        self.accept()
    
    def _on_settings_clicked(self):
        """Handle settings button click"""
        self.settings_requested.emit()
        self.accept()


def show_credentials_error(missing_info: dict, parent=None):
    """Show credentials error dialog and return user choice"""
    dialog = CredentialsErrorDialog(missing_info, parent)
    return dialog.exec()