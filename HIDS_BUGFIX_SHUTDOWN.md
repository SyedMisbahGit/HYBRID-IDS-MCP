# HIDS Bug Fix - Graceful Shutdown Handling

## Issue 1: Signal Handler During Initialization

**Error:**
```
SystemExit: 0

During handling of the above exception, another exception occurred:

TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'
```

**Scenario**: User presses Ctrl+C while HIDS is creating the baseline (during initialization phase)

**Root Cause**:
1. Signal handler called `sys.exit(0)` which raises `SystemExit` exception
2. `finally` block calls `hids.shutdown()`
3. `shutdown()` tries to print stats with `uptime = time.time() - self.stats['start_time']`
4. `start_time` is `None` because `run()` was never called (it sets `start_time`)
5. Results in TypeError: `float - NoneType`

## Issue 2: Ungraceful Signal Handling

**Problem**: Using `sys.exit(0)` in signal handler causes abrupt termination and prevents proper cleanup

## Solution

### Fix 1: Null-safe Stats Calculation

**File**: `src/hids/hids_main.py` - `_print_stats()` method

**Before:**
```python
def _print_stats(self):
    """Print monitoring statistics"""
    uptime = time.time() - self.stats['start_time']  # Crashes if start_time is None
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
```

**After:**
```python
def _print_stats(self):
    """Print monitoring statistics"""
    print("\n" + "="*60)
    print("  HIDS Statistics")
    print("="*60)

    # Calculate uptime if monitoring has started
    if self.stats['start_time'] is not None:
        uptime = time.time() - self.stats['start_time']
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        print(f"Uptime:             {hours}h {minutes}m")
    else:
        print(f"Uptime:             Not started")
```

**Benefit**: Handles early shutdown gracefully, shows "Not started" instead of crashing

### Fix 2: Graceful Signal Handler

**File**: `src/hids/hids_main.py` - `main()` function

**Before:**
```python
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\n[SIGNAL] Received signal {signum}")
    sys.exit(0)  # Abrupt termination

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    hids.initialize()
    hids.run()
except Exception as e:
    logger.error(f"HIDS error: {e}")
    return 1
finally:
    hids.shutdown()  # May crash if start_time is None
```

**After:**
```python
# Define signal handler locally to access hids instance
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\n[SIGNAL] Received signal {signum}, shutting down...")
    hids.running = False
    # Allow cleanup to happen in finally block
    raise KeyboardInterrupt  # Graceful exception instead of sys.exit

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    hids.initialize()
    hids.run()
except KeyboardInterrupt:
    logger.info("\n[INFO] Interrupted by user")  # Clean exit message
except Exception as e:
    logger.error(f"HIDS error: {e}")
    return 1
finally:
    hids.shutdown()  # Now safe - won't crash
```

**Benefits**:
1. Raises `KeyboardInterrupt` instead of `SystemExit` (more Pythonic)
2. Sets `hids.running = False` to stop monitoring loop
3. Allows `finally` block to execute cleanup safely
4. Proper logging of shutdown reason

## Testing

### Before Fix

**Test 1**: Press Ctrl+C during baseline creation
```
[INFO] Creating file integrity baseline...
[INFO] Scanning: C:\Windows\System32
^C
Traceback (most recent call last):
  File "hids_main.py", line 338, in main
    hids.initialize()
  File "hids_main.py", line 105, in initialize
    self.file_monitor.create_baseline()
SystemExit: 0

During handling of the above exception, another exception occurred:

TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'
```

### After Fix

**Test 1**: Press Ctrl+C during baseline creation
```
[INFO] Creating file integrity baseline...
[INFO] Scanning: C:\Windows\System32
^C
[SIGNAL] Received signal 2, shutting down...
[INFO] Interrupted by user

[INFO] Shutting down HIDS...

============================================================
  HIDS Statistics
============================================================
Uptime:             Not started
Total Alerts:       0
  File Alerts:      0
  Process Alerts:   0
  Log Alerts:       0
============================================================

[INFO] HIDS stopped
```

**Test 2**: Press Ctrl+C during monitoring
```
[INFO] HIDS initialized successfully
[INFO] Press Ctrl+C to stop

[FIM] Checking file integrity...
^C
[SIGNAL] Received signal 2, shutting down...
[INFO] Interrupted by user

[INFO] Shutting down HIDS...

============================================================
  HIDS Statistics
============================================================
Uptime:             0h 2m
Total Alerts:       3
  File Alerts:      2
  Process Alerts:   1
  Log Alerts:       0
============================================================

[INFO] HIDS stopped
```

## Unit Test Results

All tests continue to pass:
```
============================================================
  Test Summary
============================================================
Tests Run:     20
Successes:     20
Failures:      0
Errors:        0
============================================================
```

## Impact

### Positive Changes
- ✅ No more crashes on Ctrl+C during initialization
- ✅ Clean shutdown messages
- ✅ Proper statistics display (even if not started)
- ✅ Graceful cleanup of resources
- ✅ Better user experience

### No Negative Impact
- ✅ All tests pass
- ✅ Normal operation unchanged
- ✅ Shutdown still saves baseline and closes files
- ✅ Signal handling works on both Windows and Linux

## Edge Cases Handled

| Scenario | Before | After |
|----------|--------|-------|
| Ctrl+C during baseline creation | Crash with TypeError | Clean exit with "Not started" |
| Ctrl+C during monitoring | Works but uses sys.exit | Clean exit with KeyboardInterrupt |
| Ctrl+C during file scan | Crash with SystemExit | Clean exit with stats |
| Normal shutdown | Works | Works (unchanged) |
| Exception during init | Crash with TypeError | Clean exit with error message |

## Files Modified

1. `src/hids/hids_main.py`:
   - `_print_stats()` - Added null check for `start_time`
   - `main()` - Improved signal handler with KeyboardInterrupt
   - Removed standalone `signal_handler()` function

## Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| Windows 10/11 | ✅ Tested | Works with Ctrl+C |
| Linux | ✅ Compatible | SIGINT and SIGTERM handled |
| macOS | ✅ Compatible | SIGINT and SIGTERM handled |

## Best Practices Implemented

1. **Null Safety**: Always check if optional values are None before using them
2. **Graceful Exceptions**: Use KeyboardInterrupt instead of sys.exit() for user interruption
3. **Context-aware Handlers**: Define signal handlers in local scope to access instance variables
4. **Informative Messages**: Log shutdown reason clearly
5. **Clean Finally Blocks**: Ensure finally blocks can handle all states

## Related Issues

This fix also prevents issues with:
- File handles left open
- Alert logs not being saved
- Baseline not being persisted
- Elasticsearch connections not being closed

## Version

- **Fixed in**: October 2025
- **Severity**: Medium (crashes on user interruption)
- **Priority**: High (affects user experience)
- **Status**: ✅ Resolved

## Additional Notes

### Why KeyboardInterrupt is Better than SystemExit

1. **Standard Practice**: Python convention for user interruption
2. **Catchable**: Can be caught and handled gracefully
3. **Cleanup Friendly**: Allows finally blocks to execute
4. **Debugging**: Easier to debug than abrupt exit

### Why Check start_time for None

The monitoring lifecycle:
1. `__init__()` - Creates instance, `start_time = None`
2. `initialize()` - Loads config, creates baseline
3. `run()` - Sets `start_time = time.time()`, starts monitoring
4. `shutdown()` - Prints stats, saves baseline

If interrupted during step 2, `start_time` is still None, so we must check before using it.

## Testing Checklist

- ✅ Press Ctrl+C during baseline creation
- ✅ Press Ctrl+C during monitoring
- ✅ Press Ctrl+C during file scanning
- ✅ Send SIGTERM signal (Linux)
- ✅ Run full test suite
- ✅ Normal shutdown (no interruption)

All scenarios now work correctly.

---

**Status**: ✅ **RESOLVED**

**Impact**: Improved stability and user experience

**Testing**: 20/20 tests passing + manual interrupt testing

**Ready for**: Production deployment
