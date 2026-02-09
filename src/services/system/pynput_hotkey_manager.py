"""Pynput-based hotkey manager implementation

This module provides a hotkey manager using the pynput library as a replacement
for the PowerToys-based implementation. It maintains the same interface for
backward compatibility.
"""

import contextlib
import threading
from typing import Dict, List, Optional, Callable, Set
from PySide6.QtCore import QObject, Signal as pyqtSignal
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, GlobalHotKeys
from src.utils.loguru_config import get_logger


class PynputHotkeyManager(QObject):
    """Pynput-based hotkey manager
    
    This class provides hotkey management functionality using the pynput library.
    It maintains compatibility with the PowerToys-based implementation.
    """
    
    # Qt signals
    error_occurred = pyqtSignal(str)
    hotkey_triggered = pyqtSignal(str)
    show_floating_window = pyqtSignal()
    voice_input_requested = pyqtSignal()
    quick_translate_requested = pyqtSignal()
    quick_polish_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()
    emergency_stop_requested = pyqtSignal()
    
    def __init__(self, config_manager=None, floating_window=None, window_service=None):
        """Initialize the pynput hotkey manager
        
        Args:
            config_manager: Configuration manager instance
            floating_window: Floating window instance for callbacks
            window_service: WindowService instance for context capture (optional)
        """
        super().__init__()
        
        # Configuration and UI references
        self.config_manager = config_manager
        self.floating_window = floating_window
        self.window_service = window_service
        
        # Logger
        self.logger = get_logger("PynputHotkeyManager")
        
        # State management
        self._hook_state = 'uninstalled'
        
        # Global hotkeys listener
        self._global_hotkeys: Optional[GlobalHotKeys] = None
        self._hotkey_callbacks: Dict[str, Callable] = {}
        
        # Window context manager
        self.window_context_manager = None
        if window_service:
            try:
                from src.services.system.window_context import create_window_context_manager
                self.window_context_manager = create_window_context_manager(window_service)
                self.logger.info("Window context manager initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize window context manager: {e}")
        
        self.logger.info("Pynput hotkey manager initialized")
    
    def enable(self) -> bool:
        """Enable the hotkey manager
        
        Returns:
            bool: True if enabled successfully
        """
        try:
            if self._hook_state == 'installed':
                return True
            
            if self._install_hook():
                self._hook_state = 'installed'
                self.logger.info("Hotkey manager enabled")
                return True
            else:
                self._hook_state = 'error'
                self.logger.error("Failed to enable hotkey manager")
                return False
                    
        except Exception as e:
            self.logger.error(f"Error enabling hotkey manager: {e}")
            self._hook_state = 'error'
            return False
    
    def disable(self) -> bool:
        """Disable the hotkey manager
        
        Returns:
            bool: True if disabled successfully
        """
        try:
            if self._hook_state == 'uninstalled':
                return True
            
            if self._uninstall_hook():
                self._hook_state = 'uninstalled'
                self.logger.info("Hotkey manager disabled")
                return True
            else:
                self.logger.error("Failed to disable hotkey manager")
                return False
                    
        except Exception as e:
            self.logger.error(f"Error disabling hotkey manager: {e}")
            self._hook_state = 'error'
            return False
    
    def _install_hook(self) -> bool:
        """Install the global hotkey hook
        
        Returns:
            bool: True if hook installed successfully
        """
        try:
            # Always uninstall existing hook first
            if self._global_hotkeys is not None:
                self.logger.debug("Uninstalling existing GlobalHotKeys instance")
                self._global_hotkeys.stop()
                self._global_hotkeys = None
            
            if not self._hotkey_callbacks:
                self.logger.info("No hotkeys to install, hook marked as installed but no GlobalHotKeys created")
                self._hook_state = 'installed'
                return True
            
            # Create GlobalHotKeys instance
            self._global_hotkeys = GlobalHotKeys(self._hotkey_callbacks)
            
            # Start the hotkey listener
            self._global_hotkeys.start()
            
            # Add a small delay to ensure the listener is fully started
            import time
            time.sleep(0.1)
            
            self._hook_state = 'installed'
            self.logger.info(f"Global hotkey hook installed with {len(self._hotkey_callbacks)} hotkeys")
            self.logger.info(f"Registered hotkeys: {list(self._hotkey_callbacks.keys())}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to install hook: {e}")
            self.logger.exception("Full exception details:")
            return False
    
    def _uninstall_hook(self) -> bool:
        """Uninstall global hotkeys
        
        Returns:
            bool: True if hook was uninstalled successfully
        """
        try:
            if self._global_hotkeys:
                self._global_hotkeys.stop()
                self._global_hotkeys = None
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall hook: {e}")
            return False
    
    def _create_hotkey_callback(self, action: str) -> callable:
        """Create a callback function for a hotkey action
        
        Args:
            action: The action to perform when hotkey is pressed
            
        Returns:
            callable: Callback function
        """
        def callback():
            try:
                self.logger.info(f"Hotkey triggered for action: {action}")
                
                # Capture window context before executing action
                window_context = None
                if self.window_context_manager:
                    try:
                        window_context = self.window_context_manager.capture_context(
                            trigger_source=action
                        )
                        if window_context:
                            self.logger.info(f"Window context captured: {window_context.get_display_name()}")
                        else:
                            self.logger.warning("Failed to capture window context")
                    except Exception as e:
                        self.logger.error(f"Error capturing window context: {e}")
                
                # Get the callback function for this action
                action_callback = self._get_callback_for_action(action)
                
                if action_callback:
                    action_callback()
                else:
                    self.logger.warning(f"No callback found for action: {action}")
            except Exception as e:
                self.logger.error(f"Error in hotkey callback for action '{action}': {e}")
                self.logger.exception("Full callback exception:")
        
        self.logger.debug(f"Created callback function for action: {action}")
        return callback
    
    def _convert_to_pynput_format(self, hotkey_string: str) -> List[str]:
        """Convert hotkey string to pynput format
        
        Args:
            hotkey_string: Hotkey string (e.g., 'ctrl+shift+a')
            
        Returns:
            List[str]: List of pynput hotkey format strings
        """
        self.logger.debug(f"Converting hotkey string '{hotkey_string}' to pynput format")
        
        try:
            # Parse hotkey string
            parts = hotkey_string.lower().split('+')
            if not parts:
                self.logger.error(f"Empty hotkey string: '{hotkey_string}'")
                return []
            
            # Build pynput format string
            pynput_parts = []
            for part in parts:
                part = part.strip()
                if part == 'ctrl':
                    pynput_parts.append('<ctrl>')
                elif part == 'alt':
                    pynput_parts.append('<alt>')
                elif part == 'shift':
                    pynput_parts.append('<shift>')
                elif part == 'win' or part == 'cmd':
                    pynput_parts.append('<cmd>')
                else:
                    pynput_parts.append(part)
            
            pynput_format = '+'.join(pynput_parts)
            self.logger.debug(f"Converted '{hotkey_string}' to pynput format: '{pynput_format}'")
            return [pynput_format]
            
        except Exception as e:
            self.logger.error(f"Error converting hotkey format: {e}")
            return []
    
    def register_hotkey(self, hotkey_string: str, action: str) -> bool:
        """Register a single hotkey
        
        Args:
            hotkey_string: Hotkey combination string
            action: Action to execute when hotkey is triggered
            
        Returns:
            bool: True if registered successfully
        """
        try:
            self.logger.debug(f"Converting hotkey '{hotkey_string}' to pynput format")
            pynput_formats = self._convert_to_pynput_format(hotkey_string)
            if not pynput_formats:
                self.logger.error(f"Failed to convert hotkey to pynput format: {hotkey_string}")
                return False
            
            # Get callback function for the action
            callback_func = self._get_callback_for_action(action)
            if callback_func is None:
                self.logger.error(f"No callback function found for action: {action}")
                return False
            
            # Register all format variants
            success = True
            for pynput_format in pynput_formats:
                try:
                    # Create callback wrapper
                    hotkey_callback = self._create_hotkey_callback(action)
                    
                    # Store the callback with string key
                    self._hotkey_callbacks[pynput_format] = hotkey_callback
                    self.logger.debug(f"Registered hotkey: '{pynput_format}' -> '{action}'")
                except Exception as e:
                    self.logger.error(f"Failed to register pynput format '{pynput_format}': {e}")
                    success = False
            
            # If hook is active, reinstall to include new hotkey
            if self._hook_state == 'installed':
                self.logger.debug("Reinstalling hook to include new hotkey")
                if not self._install_hook():
                    self.logger.error("Failed to reinstall hook with new hotkey")
                    self._hook_state = 'error'
                    return False
            
            return success
            
        except Exception as e:
            self.logger.exception(f"Exception registering hotkey {hotkey_string}: {e}")
            return False
    
    def unregister_hotkey(self, hotkey_string: str) -> bool:
        """Unregister a hotkey
        
        Args:
            hotkey_string: Hotkey string to unregister
            
        Returns:
            bool: True if hotkey was unregistered successfully
        """
        try:
            pynput_formats = self._convert_to_pynput_format(hotkey_string)
            if not pynput_formats:
                return False
            
            pynput_hotkey = pynput_formats[0]
            if pynput_hotkey in self._hotkey_callbacks:
                del self._hotkey_callbacks[pynput_hotkey]
            
            # If hook is active, reinstall to exclude removed hotkey
            if self._hook_state == 'installed':
                if not self._install_hook():
                    self.logger.error("Failed to reinstall hook after removing hotkey")
                    self._hook_state = 'error'
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering hotkey {hotkey_string}: {e}")
            return False
    
    def unregister_all(self) -> bool:
        """Unregister all hotkeys
        
        Returns:
            bool: True if all hotkeys unregistered successfully
        """
        try:
            self._hotkey_callbacks.clear()
            
            # If hook is active, reinstall (will be empty now)
            if self._hook_state == 'installed':
                if not self._install_hook():
                    self.logger.error("Failed to reinstall hook after clearing all hotkeys")
                    self._hook_state = 'error'
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering all hotkeys: {e}")
            return False
    
    def is_registered(self, hotkey_string: str) -> bool:
        """Check if a hotkey is registered
        
        Args:
            hotkey_string: Hotkey string to check
            
        Returns:
            bool: True if hotkey is registered
        """
        pynput_formats = self._convert_to_pynput_format(hotkey_string)
        if not pynput_formats:
            return False
        return pynput_formats[0] in self._hotkey_callbacks
    
    def register_hotkeys(self, hotkey_config: Dict[str, str]) -> bool:
        """Register multiple hotkeys from configuration
        
        Args:
            hotkey_config: Dictionary mapping hotkey strings to actions
            
        Returns:
            bool: True if all hotkeys registered successfully
        """
        try:
            self.logger.info(f"Registering {len(hotkey_config)} hotkeys: {list(hotkey_config.keys())}")
            self.logger.debug(f"Full hotkey config received: {hotkey_config}")
            
            success_count = 0
            for hotkey_string, action in hotkey_config.items():
                self.logger.debug(f"Registering hotkey: '{hotkey_string}' -> '{action}'")
                if self.register_hotkey(hotkey_string, action):
                    success_count += 1
                    self.logger.info(f"Successfully registered hotkey: '{hotkey_string}' -> '{action}'")
                else:
                    self.logger.error(f"Failed to register hotkey: '{hotkey_string}' -> '{action}'")
            
            # Add a simple test to verify pynput functionality
            self._test_pynput_functionality()
            
            self.logger.info(f"Registered {success_count}/{len(hotkey_config)} hotkeys successfully")
            self.logger.debug(f"Current _hotkey_callbacks: {list(self._hotkey_callbacks.keys())}")
            self.logger.debug(f"Current hook state: {self._hook_state}")
            
            return success_count == len(hotkey_config)
            
        except Exception as e:
            self.logger.error(f"Error registering hotkeys: {e}")
            return False
    
    def reload_hotkeys(self, hotkey_config: Dict[str, str]) -> bool:
        """Reload hotkeys with new configuration
        
        Args:
            hotkey_config: New hotkey configuration
            
        Returns:
            bool: True if reload successful
        """
        try:
            self.unregister_all()
            return self.register_hotkeys(hotkey_config)
            
        except Exception as e:
            self.logger.error(f"Error reloading hotkeys: {e}")
            return False
    
    def _parse_hotkey_string(self, hotkey_string: str) -> tuple[Optional[Set[Key]], Optional[Key | KeyCode]]:
        """Parse hotkey string into modifiers and key
        
        Args:
            hotkey_string: Hotkey string (e.g., 'ctrl+shift+a')
            
        Returns:
            Tuple[Optional[Set[Key]], Optional[Key | KeyCode]]: (modifiers, key) or (None, None) if parsing failed
        """
        try:
            parts = [part.strip().lower() for part in hotkey_string.split("+")]
            if not parts:
                return None, None
            
            # Last part is the key, others are modifiers
            key_str = parts[-1]
            modifier_parts = parts[:-1]
            
            # Parse main key
            key = self._string_to_key(key_str)
            if key is None:
                self.logger.error(f"Unknown key: {key_str}")
                return None, None
            
            # Parse modifiers - collect all variants
            modifiers = set()
            for modifier in modifier_parts:
                modifier_keys = self._string_to_modifier(modifier)
                if modifier_keys is None:
                    self.logger.error(f"Unknown modifier: {modifier}")
                    return None, None
                modifiers.update(modifier_keys)  # Add all variants to the set
            
            return modifiers, key
            
        except Exception as e:
            self.logger.exception(f"Exception parsing hotkey string {hotkey_string}: {e}")
            return None, None
    
    def _string_to_key(self, key_str: str) -> Optional[Key | KeyCode]:
        """Convert string to pynput key
        
        Args:
            key_str: Key string
            
        Returns:
            Optional[Key | KeyCode]: Pynput key or None if not found
        """
        # Special keys mapping
        special_keys = {
            'space': Key.space,
            'enter': Key.enter,
            'return': Key.enter,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
            'escape': Key.esc,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'insert': Key.insert,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        }
        
        if key_str in special_keys:
            return special_keys[key_str]
        
        # Regular character keys
        if len(key_str) == 1:
            return KeyCode.from_char(key_str)
        
        return None
    
    def _string_to_modifier(self, modifier_str: str) -> Optional[Set[Key]]:
        """Convert string to pynput modifier key variants
        
        Args:
            modifier_str: Modifier string
            
        Returns:
            Optional[Set[Key]]: Set of pynput modifier key variants or None if not found
        """
        modifiers = {
            'ctrl': {Key.ctrl_l, Key.ctrl_r},
            'control': {Key.ctrl_l, Key.ctrl_r},
            'alt': {Key.alt_l, Key.alt_r, Key.alt_gr},  # Include alt_gr for Windows
            'shift': {Key.shift_l, Key.shift_r},
            'win': {Key.cmd_l, Key.cmd_r, Key.cmd},  # Include generic cmd key
            'cmd': {Key.cmd_l, Key.cmd_r, Key.cmd},
            'super': {Key.cmd_l, Key.cmd_r, Key.cmd},
        }
        
        return modifiers.get(modifier_str)
    
    def _test_pynput_functionality(self):
        """Test basic pynput functionality"""
        try:
            self.logger.info("Testing pynput GlobalHotKeys functionality...")
            
            def test_callback():
                self.logger.info("Test hotkey callback triggered!")
            
            # Test creating GlobalHotKeys with a simple string combination
            test_hotkeys = {'<ctrl>+t': test_callback}
            
            try:
                test_global_hotkeys = keyboard.GlobalHotKeys(test_hotkeys)
                self.logger.info("GlobalHotKeys test instance created successfully")
                
                # Don't start it to avoid conflicts, just test creation
                del test_global_hotkeys
                self.logger.info("pynput functionality test passed")
                
            except Exception as e:
                self.logger.error(f"pynput GlobalHotKeys creation failed: {e}")
                
        except Exception as e:
            self.logger.error(f"pynput functionality test failed: {e}")
    
    def _get_callback_for_action(self, action: str) -> Optional[Callable]:
        """Get callback function for a specific action
        
        Args:
            action: Action name
            
        Returns:
            Optional[Callable]: Callback function or None
        """
        callbacks = {
            "SHOW_FLOATING_WINDOW": self._on_show_floating_window,
            "VOICE_INPUT": self._on_voice_input,
            "QUICK_TRANSLATE": self._on_quick_translate,
            "QUICK_POLISH": self._on_quick_polish,
            "TOGGLE_RECORDING": self._on_toggle_recording,
            "EMERGENCY_STOP": self._on_emergency_stop,
            # Legacy mappings for backward compatibility
            "show_floating_window": self._on_show_floating_window,
        }
        return callbacks.get(action)
    

    

    

    

    

    

    

    

    

    

    
    def get_current_window_context(self):
        """
        Get the current captured window context.
        
        Returns:
            WindowContext object or None
        """
        if self.window_context_manager:
            return self.window_context_manager.get_current_context()
        return None
    
    def restore_window_context(self, context=None) -> bool:
        """
        Restore focus to a previously captured window context.
        
        Args:
            context: WindowContext to restore, or None to use current
            
        Returns:
            True if restoration successful
        """
        if self.window_context_manager:
            return self.window_context_manager.restore_context(context)
        return False
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        try:
            self.unregister_all()
            self.disable()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    # Backward compatibility callback methods
    def _on_show_floating_window(self):
        """Show floating window callback"""
        self.logger.info("Show floating window callback triggered")
        try:
            self.show_floating_window.emit()
        except Exception as e:
            self.logger.error(f"Error emitting show_floating_window signal: {e}")
            self.logger.exception("Full signal emission exception:")
    
    def _on_voice_input(self):
        """Voice input callback"""
        self.voice_input_requested.emit()
    
    def _on_quick_translate(self):
        """Quick translate callback"""
        self.quick_translate_requested.emit()
    
    def _on_quick_polish(self):
        """Quick polish callback"""
        self.quick_polish_requested.emit()
    
    def _on_toggle_recording(self):
        """Toggle recording callback"""
        self.toggle_recording_requested.emit()
    
    def _on_emergency_stop(self):
        """Emergency stop callback"""
        self.emergency_stop_requested.emit()
    
    @property
    def hook_state(self):
        """Get current hook state"""
        return self._hook_state
    
    @property
    def is_enabled(self):
        """Check if hotkey manager is enabled"""
        return self._hook_state == 'installed'
    
    @property
    def registered_hotkeys(self):
        """Get list of registered hotkey strings"""
        return [str(hotkey) for hotkey in self._hotkey_callbacks.keys()]
    
    def get_status(self):
        """Get current status of hotkey manager"""
        return {
            'hook_state': self._hook_state,
            'registered_hotkeys_count': len(self._hotkey_callbacks),
            'is_enabled': self.is_enabled
        }