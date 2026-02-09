# Requirements Document

## Introduction

**Core Value**: Simple, efficient, cross-application AI text processing tool.

## Feature Overview

Scenario 1: User activates floating window, inputs text in the input box, status bar displays real-time results, press Enter to insert text, press Ctrl+Enter to input original text

Scenario 2: User activates voice input, floating window appears, after user speaks, input box displays recognized text, status bar shows real-time polished results, press Enter to insert text, press Ctrl+Enter to input original text

Scenario 3: User selects text, presses shortcut key (supports translation, polishing, etc.), automatically sends to input box, and displays returned results through status box.

### User Interface Layer Requirements

#### Feature Priority Description

- **P0 (Core Features)**: Essential features for basic product functionality, must be included in MVP version
- **P1 (Important Features)**: Important features that significantly improve user experience, should be included in first official release
- **P2 (Enhancement Features)**: Nice-to-have features, gradually added in subsequent versions

| Priority | Main Module | Secondary Function | Tertiary Function | Feature Description | Acceptance Criteria |
| -------- | ----------- | ------------------ | ----------------- | ------------------- | ------------------- |
| P1 | System Tray Interface | Tray Icon Display | - | Display application icon, provide status indication, support right-click menu operations | Icon displays normally, right-click menu responds properly |
| P2 | | Tray Menu | Account Settings | Click to display account name, login/logout options | Menu items clickable, login status displays correctly |
| P1 | | | Show Floating Window Menu | Show floating window function item in tray menu, displays floating window interface after clicking | Floating window displays normally after clicking |
| P2 | | | About | Click to display application version and related information, support update checking | Version information displays correctly, update check function works |
| P1 | | | Exit | Exit function item in tray menu, gracefully closes application after clicking | Application exits normally, no residual processes |
| P2 | | Tray Notifications | Status Notifications | Display application status changes, error prompts, processing completion and other notification information | Notifications display timely, content accurate |
| P2 | Menu Window | Basic Settings | Startup Settings | Configure auto-start on boot, minimize to tray and other basic startup options | Settings save and take effect, auto-start works normally |
| P2 | | | Interface Language Settings | Support multiple language interface switching including Chinese, English, etc. | Language switching takes effect immediately, interface fully translated |
| P2 | | | Theme Selection | Provide multiple interface theme options including dark theme, light theme, etc. | Theme switching takes effect immediately, interface coordinated and beautiful |
| P0 | | Shortcut Key Settings | Floating Window Activation Shortcut | Support custom shortcut key configuration (default: win+shift+o), validate effectiveness, avoid system conflicts, provide shortcut key reset function | Shortcut key settings take effect, no system conflicts |
| P1 | | | Voice Service Activation Shortcut | Configure shortcut key for voice input function (default: win+shift+i), support custom key combinations (P1 phase design) | Voice shortcut triggers normally |
| P1 | | | Quick Polish Shortcut | Configure global shortcut key for quick polish function (default: win+shift+q) | Polish shortcut works globally |
| P1 | | | Quick Translation Shortcut | Configure global shortcut key for quick translation function (default: win+shift+r) | Translation shortcut works globally |
| P0 | | AI Service Configuration Dialog | LLM Provider Configuration | Configure API keys and service addresses for LLM service providers like OpenAI, Qwen, DeepSeek, etc. | API keys saved successfully, service addresses configured correctly |
| P1 | | | Agent Settings | Support users to customize and manage previously created Agents (such as translation, polishing, error correction) and their mapped window information | Agent creation and editing normal, window mapping accurate |
| P0 | | | Connection Test | Provide LLM service connection test function, verify API key validity and service availability | Connection test 100% accuracy, clear error prompts |
| P1 | | Floating Window Interface Settings | Transparency Settings | Configure floating window transparency level, support 0-100% transparency adjustment | Transparency adjustment takes effect in real-time, range 0-100% |
| P1 | | | Theme Color Settings | Configure floating window color theme, including background color, text color, border color, etc. | Color settings take effect immediately, theme coordinated and beautiful |
| P2 | | | Font Size Settings | Configure text font size in floating window, support DPI adaptation | Font size adjustment takes effect, DPI adaptation normal |
| P2 | | Advanced Settings | Debug Mode | Enable debug mode, display detailed runtime logs and error information | Debug mode switch normal, log information detailed and accurate |
| P2 | | | Log Level Settings | Configure application log detail level, including error, warning, info, debug levels | Log level settings take effect, output content matches level |
| P2 | | | Performance Monitoring | Display application performance metrics, including memory usage, response time, etc. | Performance data displays in real-time, metrics accurate and reliable |
| P1 | | Voice Recognition | Voice Service Provider | Support switching between different voice recognition service providers (P1 phase design) | Service provider switching normal, recognition function stable |
| P1 | | | Voice Recognition Language | Configure target language for voice recognition, support multiple languages including Chinese, English, etc. (P1 phase design) | Language switching takes effect, recognition accuracy >90% |
| P0 | Floating Window Interface | Transparent Floating Window Display | Default Transparent State | Floating window remains completely transparent when not activated, does not interfere with user normal operations | Completely transparent when not activated, does not affect other application operations |
| P0 | | | Shortcut Key Trigger Display | Automatically displays floating window when triggered by global shortcut key, floats at cursor position | Shortcut key trigger response time <200ms, positioning accurate |
| P0 | | | Smart Positioning Algorithm | If no cursor position when activated, intelligently calculates optimal display position based on screen boundaries, avoids obstruction | Smart positioning accuracy >95%, no interface obstruction |
| P0 | | Input Box Component | Transparent Input Box | Provide transparent text input box, support multi-line text input and editing | Input box transparency adjustable, multi-line input normal |
| P0 | | | Auto Focus Acquisition | Automatically sets focus to transparent input box when floating window displays, user can start typing immediately | Focus acquisition success rate 100%, input response timely |
| P0 | | Result Box Component | AI Result Real-time Display | Located above input box, real-time display of translation, polishing and other AI processing results | Result display delay <500ms, content displays accurately |
| P1 | | | Agent Status Display | Display current Agent being used (translation or error correction) through icon, click to switch Agent | Agent status displays accurately, switching function normal |
| P0 | | | Status Indicator | Display AI processing status, including processing, completed, error and other status indications | Status indication updates in real-time, status display accurate |
| P1 | | | Result Operation Buttons | Provide copy, replace, reprocess and other operation buttons for convenient user result operations | Operation buttons respond normally, functions execute accurately |
| P1 | | | Window Status Display | Display current window where input box is located | Window status recognition accurate, display information correct |
| P1 | | | Voice Status Display | When in typing state, click to switch to voice mode | Voice mode switching normal, status display accurate |

#### Floating Window Effect Display

The floating window adopts a semi-transparent dark gray background (#cc1E1E1E), light green text (#FFC9E47E), green cursor (#AA00FF00) and red border (#ffff0000) design, with surrounding areas completely transparent, not interfering with user operations.

### Business Logic Layer Requirements

| Priority | Main Module | Secondary Function | Tertiary Function | Feature Description | Acceptance Criteria |
| -------- | ----------- | ------------------ | ----------------- | ------------------- | ------------------- |
| P2 | Cloud Account Service | User Authentication Management | User Identity Verification | Provide user login verification, support multiple authentication methods (username password, OAuth, third-party login, etc.) | Login success rate >99%, support mainstream authentication methods |
| P2 | | | Token Management | Manage access token generation, verification, refresh and revocation, support JWT and OAuth2.0 protocols | Tokens secure and valid, automatic refresh mechanism normal |
| P2 | | | Multi-device Authentication | Support user identity authentication and device management across multiple devices | Multi-device login status sync, device management function complete |
| P2 | | Account Data Management | User Profile Storage | Cloud storage of user basic information, personal profiles and account metadata | Data integrity 100%, cloud sync timely |
| P2 | | | Preference Settings Cloud Storage | Cloud storage of user personalized settings and preference configurations, support cross-device sync | Settings cross-device sync success rate >95% |
| P2 | | | Data Backup Recovery | Provide cloud backup, recovery and version management functions for user data | Backup recovery success rate 100%, version management clear |
| P2 | | Permission Control Management | Role Permission Management | Manage user roles and permission allocation, support Role-Based Access Control (RBAC) | Permission control accurate, no unauthorized access |
| P1 | Client Account Service | Local Session Management | Session State Maintenance | Manage creation, maintenance, expiration and secure logout of local user login sessions | Session management stable, no abnormal logout |
| P1 | | | Auto Login Control | Support remember login state, auto login and secure session recovery | Auto login success rate >95% |
| P1 | | | Offline Mode Support | Maintain basic user state and functionality availability when network is disconnected | Offline mode functions normal, core features available |
| P1 | | Local Data Cache | User Information Cache | Locally cache user basic information and common settings, reduce network requests | Cache hit rate >80%, data consistency guaranteed |
| P0 | | | Configuration Local Storage | Locally store user preference settings and application configurations, support offline access | Configuration save success rate 100%, offline accessible |
| P0 | | | Sensitive Data Protection | Encrypt and securely clean sensitive information stored locally | Sensitive data encrypted storage, security audit passed |
| P2 | | Cloud Sync Service | Data Sync Management | Manage bidirectional sync between local data and cloud, handle conflict resolution | Data sync success rate >95%, conflict resolution mechanism normal |
| P2 | | | Incremental Sync Optimization | Implement incremental data sync, reduce network transmission and improve sync efficiency | Sync efficiency improvement >50%, network traffic optimization obvious |
| P2 | | | Sync Status Monitoring | Monitor sync status, provide sync progress feedback and error handling | Sync status monitoring real-time, error handling timely |
| P1 | | Client Security Management | Local Authentication Verification | Verify authentication tokens and user permission information returned from cloud | Authentication verification accuracy 100%, permission control correct |
| P1 | | | Device Fingerprint Management | Generate and manage unique device identifiers, support device trust and security verification | Device fingerprint uniqueness guaranteed, trust mechanism normal |
| P1 | | | Local Security Audit | Record local security events and user operation logs, support security analysis | Security logs completely recorded, audit function normal |
| P0 | Configuration Management Service | Application Configuration Management | Startup Configuration Management | Manage reading, saving and validation of startup options like auto-start on boot, minimize to tray, etc. | Configuration items save and take effect, startup behavior matches settings |
| P1 | | | Interface Configuration Management | Manage persistent storage and dynamic switching of UI configurations like interface language, theme selection, etc. | Interface configuration takes effect immediately, maintains after restart |
| P1 | | | User Preference Settings | Manage user personalized settings, including transparency, font size, color theme and other configuration items | Personalized settings save and take effect, interface responds to configuration changes |
| P0 | | Shortcut Key Configuration Management | Shortcut Key Registration Verification | Verify validity of shortcut key combinations, detect system conflicts, provide shortcut key reset and restore default functions | Shortcut key conflict detection accurate, reset function normal |
| P0 | | | Shortcut Key Mapping Management | Manage shortcut key mapping relationships for functions like floating window activation (win+shift+o), voice input (win+shift+i), quick polish (win+shift+q), quick translation (win+shift+r), etc. | Shortcut key mapping accurate, function triggering normal |
| P0 | | | Global Shortcut Key Listening | Implement registration, listening and response of global shortcut keys, ensure normal triggering in any application | Global shortcut key response rate >99%, available in any application |
| P0 | AI Service Management | AI Service Configuration Management | LLM Provider Management | Manage configuration information for multiple LLM service providers, including API keys, service addresses, model parameters, etc. | Support mainstream LLM service providers, configuration saved correctly |
| P0 | | | Connection Status Management | Monitor and manage AI service connection status, provide connection testing, auto-reconnect, failover and other functions | Connection status real-time monitoring, auto-reconnect success rate >90% |
| P0 | | | Configuration Validation Service | Validate API key validity, service availability, provide configuration error diagnosis and repair suggestions | Configuration validation accuracy 100%, clear error prompts |
| P1 | | Agent Management Service | Agent Lifecycle Management | Manage creation, configuration, enable, disable and deletion of Agents like translation, polishing, error correction, etc. | Agent management function complete, operation response timely |
| P1 | | | Agent Context Management | Manage Agent context information, including conversation history, user preferences, processing records, etc. | Context information completely saved, retrieval accurate |
| P1 | Voice Recognition Service | Voice Input Management | Voice Collection Control | Manage microphone enable, disable, volume control and audio quality optimization (P1 phase design) | Microphone control normal, audio quality clear |
| P1 | | | Real-time Voice Recognition | Provide real-time voice-to-text function, support multi-language recognition and real-time update of recognition results (P1 phase design) | Voice recognition accuracy >90%, real-time <1 second |
| P1 | | | Voice Status Management | Manage start, pause, stop states of voice input, provide visual status feedback (P1 phase design) | Status switching timely, visual feedback clear |
| P1 | | | Multi-provider Support | Support multiple voice recognition service providers, provide unified voice recognition interface (P1 phase design) | Support mainstream voice services, unified interface |
| P0 | Window Management Service | Floating Window Control | Window Display Control | Manage floating window display, hide, transparency control and layer management | Floating window display/hide normal, transparency control precise |
| P0 | | | Smart Positioning Algorithm | Implement smart positioning of floating window, including cursor following, screen boundary detection and obstruction avoidance | Positioning algorithm accurate, no obstruction issues |
| P0 | | | Window Status Management | Manage floating window state changes like activation, focus loss, minimization and corresponding UI responses | Status management accurate, UI response timely |
| P0 | | Focus Management | Auto Focus Control | Manage automatic focus acquisition and loss of input box, ensure smooth user operations | Focus control accurate, user experience smooth |
| P1 | | | Window Switch Detection | Detect changes in user's current active window, provide data support for window status display | Window switch detection accuracy >95% |
| P0 | System Integration Service | Clipboard Management | Text Insertion Service | Implement text insertion of processing results into target applications, support multiple insertion methods and formats | Text insertion success rate >99%, support mainstream applications |
| P0 | | | Selected Text Acquisition | Acquire text content selected by user in other applications, support multiple applications and text formats | Text acquisition accuracy >95%, format maintained correctly |
| P2 | | | Clipboard Monitoring | Monitor system clipboard changes, provide clipboard history and intelligent text processing suggestions | Clipboard monitoring real-time, history records complete |
| P1 | | System Notification Service | Status Notification Management | Manage display and user interaction of notifications for application status changes, error prompts, processing completion, etc. | Notifications timely and accurate, user interaction friendly |
| P1 | | | Tray Icon Control | Control system tray icon display status, right-click menu and status indication | Tray icon status accurate, menu functions normal |
| P0 | | | Application Lifecycle | Manage application startup, running, pause, resume and graceful shutdown processes | Application lifecycle management complete, graceful shutdown normal |