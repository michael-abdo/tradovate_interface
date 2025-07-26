# Chrome GPU Stability Flags Update Summary

## Updated Files

### 1. `/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/start_chrome_debug.sh`
- **Port**: 9222
- **Added GPU stability flags** to prevent SharedImageManager crashes

### 2. `/Users/Mike/trading/tradovate_interface/src/auto_login.py` 
- **Port**: 9223+
- **Already had GPU flags**, added `--force-color-profile=srgb` for consistency

## GPU Stability Flags Added

```bash
--disable-gpu-sandbox           # Prevents GPU sandbox crashes
--disable-software-rasterizer   # Avoids software rendering issues
--disable-dev-shm-usage        # Fixes shared memory problems
--no-sandbox                   # Disables Chrome sandbox (improves stability)
--disable-gpu-compositing      # Prevents GPU composition crashes
--force-color-profile=srgb     # Forces consistent color profile
```

## Additional Stability Flags

```bash
--disable-background-timer-throttling
--disable-renderer-backgrounding
--disable-features=TranslateUI
--disable-ipc-flooding-protection
--max_old_space_size=4096
```

## To Apply Changes

### For Port 9222 (Proposal Automation)
The next time you run the script, it will use the new flags:
```bash
/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/start_chrome_debug.sh
```

### For Port 9223+ (Tradovate)
The next time you run start_all.py or auto_login.py, it will use the new flags:
```bash
python3 start_all.py
# or
python3 src/auto_login.py
```

## Why These Flags Help

1. **GPU Crashes**: The `--disable-gpu-sandbox` and `--disable-gpu-compositing` flags prevent the SharedImageManager errors
2. **Memory Issues**: `--disable-dev-shm-usage` and `--max_old_space_size=4096` help with memory management
3. **Stability**: `--no-sandbox` and other flags improve overall Chrome stability during automation

## Important Note

These changes will only take effect when Chrome is restarted. The current running Chrome instance on port 9222 will continue to run without these flags until it's restarted.