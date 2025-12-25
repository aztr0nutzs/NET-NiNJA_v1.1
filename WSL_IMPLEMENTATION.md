# WSL Bridge Mode Implementation

This document describes the technical implementation of WSL Bridge Mode as a first-class backend.

## Architecture Overview

WSL Bridge Mode is implemented as a **third execution backend** alongside Linux Native and Windows Native providers. It follows the same provider interface pattern, ensuring consistent behavior across all backends.

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Net.Ninja GUI                        │
│                   (Windows/Linux)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Provider Selection   │
         │  (providers/__init__) │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Linux   │  │ Windows  │  │   WSL    │
│ Provider │  │ Provider │  │ Provider │
└──────────┘  └──────────┘  └────┬─────┘
                                  │
                                  ▼
                            ┌──────────┐
                            │ WslRunner│
                            └────┬─────┘
                                 │
                                 ▼
                            wsl.exe -d <distro> -- <cmd>
                                 │
                                 ▼
                         ┌───────────────┐
                         │ WSL2 Linux VM │
                         │  (ip, nmap,   │
                         │   aircrack,   │
                         │   etc.)       │
                         └───────────────┘
```

## File Structure

```
providers/
├── __init__.py          # Provider factory with backend selection
├── base.py              # BaseProvider interface + data models
├── linux.py             # Linux Native Provider
├── windows.py           # Windows Native Provider
└── wsl.py               # WSL Bridge Provider (NEW)

feature_matrix.py        # Extended with WSL support levels
capabilities.py          # Extended with WSL mode detection
wsl_diagnostics.py       # WSL health checks and diagnostics (NEW)

docs/
├── FEATURE_MATRIX.md    # User-facing feature comparison (NEW)
└── WSL_BRIDGE_MODE.md   # Setup and usage guide (NEW)

test_wsl_bridge.py       # Test script for WSL functionality (NEW)
```

## Key Design Decisions

### 1. Explicit Backend Selection

WSL Bridge is **not** a fallback. It's an explicit choice:

```python
# User selects backend mode in GUI
backend_mode = "wsl"  # or "native"
wsl_distro = "Ubuntu"  # or "" for default

# Provider factory respects the choice
provider = get_provider(capabilities, backend_mode, wsl_distro)
```

This prevents confusion and makes behavior predictable.

### 2. Same Provider Interface

`WslProvider` implements the same `BaseProvider` interface:

```python
class WslProvider(BaseProvider):
    def get_interfaces(self) -> List[InterfaceRecord]: ...
    def get_routes(self) -> List[RouteRecord]: ...
    def get_sockets(self) -> List[SocketRecord]: ...
    def get_neighbors(self) -> List[NeighborRecord]: ...
    def scan_wifi(self) -> List[WifiAPRecord]: ...
    def discover_hosts_quick(self) -> List[HostRecord]: ...
    def discover_hosts_full(self, target: Optional[str]) -> List[HostRecord]: ...
```

The GUI consumes the same data models regardless of backend.

### 3. Safe Command Execution

`WslRunner` handles all WSL command execution:

```python
class WslRunner:
    def run_json(self, args: List[str]) -> object:
        """Execute and parse JSON output"""
    
    def run_text(self, args: List[str]) -> str:
        """Execute and return text output"""
    
    def run_check(self, args: List[str]) -> bool:
        """Execute and check success (rc=0)"""
```

Key features:
- **Safe argument handling**: No shell injection risks
- **Timeout enforcement**: Prevents hanging
- **Error propagation**: Clear error messages
- **Distro selection**: Supports multiple WSL distros

### 4. Three-Level Support Status

Feature matrix now includes three support levels:

```python
SupportLevel = Literal[
    "native",           # Fully supported natively
    "limited",          # Supported with limitations
    "unsupported",      # Not available
    "external_required",# Needs external setup
    "wsl_supported"     # Supported via WSL Bridge
]
```

Each feature defines support for all three backends:

```python
FeatureDefinition(
    key="wireless.monitor_mode",
    support_windows="external_required",
    support_linux="native",
    support_wsl="wsl_supported",  # NEW
    wsl_notes="Requires USB Wi-Fi adapter...",  # NEW
    ...
)
```

### 5. Comprehensive Diagnostics

`wsl_diagnostics.py` provides actionable health checks:

```python
diag = run_wsl_diagnostics(distro="Ubuntu")

# Check results
diag.is_ready()           # Basic WSL functionality
diag.is_wireless_ready()  # Wireless attack capability

# Get recommendations
for rec in diag.recommendations:
    print(rec)
```

Checks include:
- WSL installation and version
- Available distributions
- Distro reachability
- Tool availability (ip, nmap, aircrack, etc.)
- Wireless interface detection
- Actionable error messages

## Implementation Details

### Command Execution Flow

1. **GUI calls provider method**:
   ```python
   interfaces = provider.get_interfaces()
   ```

2. **WSL Provider delegates to WslRunner**:
   ```python
   data = self.runner.run_json(["ip", "-j", "addr", "show"])
   ```

3. **WslRunner builds WSL command**:
   ```python
   cmd = ["wsl.exe", "-d", "Ubuntu", "--", "ip", "-j", "addr", "show"]
   ```

4. **Execute with timeout and error handling**:
   ```python
   result = subprocess.run(cmd, capture_output=True, timeout=8)
   ```

5. **Parse and return structured data**:
   ```python
   return [InterfaceRecord(...) for it in data]
   ```

### Capability Detection

When WSL mode is selected, capabilities are detected **as if running on Linux**:

```python
capabilities = detect_capabilities(
    backend_mode="wsl",
    wsl_distro="Ubuntu"
)

# os_key becomes "wsl" instead of "windows"
# Tool detection checks WSL environment
# Feature support uses WSL-specific rules
```

This ensures correct feature gating.

### Error Handling

All WSL operations use `ProviderError` for consistent error handling:

```python
try:
    interfaces = provider.get_interfaces()
except ProviderError as e:
    # Show user-friendly error in GUI
    show_error(f"WSL command failed: {e}")
```

Errors include:
- WSL not installed
- Distro not found
- Command timeout
- Tool not available
- Permission denied

## Testing

### Manual Testing

```bash
# Run test script
python test_wsl_bridge.py

# Test specific distro
python test_wsl_bridge.py Ubuntu-22.04
```

### Integration Testing

The GUI should include:

1. **Backend selector**: Dropdown with "Windows Native" / "WSL Bridge"
2. **Distro selector**: Dropdown populated from `wsl -l -q`
3. **Test connection button**: Runs basic diagnostics
4. **Status badge**: Shows current backend in header
5. **Diagnostics panel**: Full WSL health check

### Wireless Testing

For wireless features:

1. Attach USB adapter: `usbipd attach --wsl --busid X-Y`
2. Verify in WSL: `wsl -- iw dev`
3. Run diagnostics: Check `wireless_capable` flag
4. Test scan: `provider.scan_wifi()`

## GUI Integration Points

### Settings UI

```python
# Backend selection
backend_mode = QComboBox()
backend_mode.addItems(["Windows Native", "WSL Bridge"])

# Distro selection (enabled when WSL selected)
wsl_distro = QComboBox()
wsl_distro.addItems(get_wsl_distros())

# Test button
test_btn = QPushButton("Test Connection")
test_btn.clicked.connect(run_wsl_diagnostics)

# Save to QSettings
settings.setValue("backend_mode", backend_mode.currentText())
settings.setValue("wsl_distro", wsl_distro.currentText())
```

### Header Badge

```python
# Show current backend
if backend_mode == "wsl":
    badge.setText(f"Backend: WSL ({distro})")
    badge.setStyleSheet("background: #4CAF50")
else:
    badge.setText("Backend: Windows Native")
    badge.setStyleSheet("background: #2196F3")
```

### Feature Gating

```python
# Check if feature is available
feature_def = FEATURE_MATRIX["wireless.monitor_mode"]
support = feature_def.support_for(os_key)

if support == "wsl_supported":
    # Show "Requires WSL Bridge Mode" if not in WSL mode
    # Show "Requires USB adapter" if in WSL mode
    pass
elif support == "unsupported":
    # Disable feature
    pass
```

## Performance Considerations

### Overhead

- **Command startup**: ~50-100ms per WSL command
- **Network I/O**: Near-native (WSL2 uses Hyper-V networking)
- **Disk I/O**: Slower for `/mnt/c/` paths, fast for WSL filesystem

### Optimization

1. **Batch operations**: Combine multiple checks when possible
2. **Cache results**: Store distro list, tool availability
3. **Parallel execution**: Use ThreadPoolExecutor for ping sweeps
4. **Timeout tuning**: Adjust timeouts based on operation type

## Security Considerations

1. **Command injection**: WslRunner uses list-based args (no shell)
2. **Privilege escalation**: Some tools need sudo in WSL
3. **USB passthrough**: Gives WSL direct hardware access
4. **Network isolation**: WSL2 runs in separate network namespace

## Limitations

### What WSL Bridge Cannot Do

- **Direct Windows Wi-Fi control**: Must use USB adapter
- **Kernel modules**: Limited kernel access in WSL2
- **Raw sockets**: May need root in WSL
- **GPU acceleration**: Limited without WSL-GPU drivers

### Compared to Native Linux

- **Slightly higher latency**: WSL command overhead
- **USB limitations**: Requires usbipd-win for passthrough
- **No direct kernel access**: Some advanced features unavailable

## Future Enhancements

### Potential Improvements

1. **Auto-detect best backend**: Suggest WSL if tools missing on Windows
2. **Tool auto-install**: Offer to install missing tools in WSL
3. **USB auto-attach**: Detect and offer to attach Wi-Fi adapters
4. **Multi-distro support**: Run different tools in different distros
5. **Performance profiling**: Track and optimize slow operations

### Advanced Features

1. **WSL config management**: Edit `.wslconfig` from GUI
2. **Distro management**: Install/remove distros from GUI
3. **Tool marketplace**: One-click install of security tools
4. **Wireless wizard**: Guided USB adapter setup

## Troubleshooting

### Common Issues

**"WSL not installed"**
- Solution: Run `wsl --install` in PowerShell as Admin

**"Distro not reachable"**
- Solution: Try `wsl -d <distro> -- echo test`
- Check: `wsl -l -v` shows distro as "Running"

**"Tool not found"**
- Solution: Install in WSL: `wsl -- sudo apt install <tool>`

**"No wireless interfaces"**
- Solution: Attach USB adapter with `usbipd`
- Verify: `wsl -- iw dev` shows interface

## Resources

- [WSL Documentation](https://learn.microsoft.com/en-us/windows/wsl/)
- [usbipd-win](https://github.com/dorssel/usbipd-win)
- [Provider Interface](providers/base.py)
- [Feature Matrix](feature_matrix.py)

## Summary

WSL Bridge Mode provides:
- ✅ First-class backend alongside native providers
- ✅ Same provider interface for consistent behavior
- ✅ Comprehensive diagnostics and error handling
- ✅ Full Linux toolset on Windows
- ✅ Optional wireless attacks with USB adapter
- ✅ Clear documentation and testing

It's production-ready and recommended for Windows users who need professional penetration testing capabilities.
