import argparse
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Optional, Tuple

from pynput.keyboard import Controller, Key, KeyCode


LOG_DIR = Path(__file__).resolve().parents[1] / "logs"

READINESS_PATTERNS = [
    "Global hotkeys installed successfully",
    "Hotkeys registered successfully",
]

TRIGGER_PATTERNS = [
    "Hotkey triggered in main thread:",  # from src/main.py
    "Hotkey triggered:",                 # from pynput_hotkey_manager.py
]


def find_latest_logfile() -> Optional[Path]:
    if not LOG_DIR.exists():
        return None
    files = sorted(LOG_DIR.glob("reInput_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def wait_for_readiness(logfile: Path, timeout: float = 30.0) -> bool:
    """Wait until the app writes readiness patterns to the logfile."""
    end_time = time.time() + timeout
    last_size = logfile.stat().st_size if logfile.exists() else 0
    while time.time() < end_time:
        try:
            with logfile.open("r", encoding="utf-8", errors="ignore") as f:
                f.seek(last_size)
                data = f.read()
                if any(p in data for p in READINESS_PATTERNS):
                    return True
                last_size += len(data)
        except FileNotFoundError:
            pass
        time.sleep(0.5)
    return False


def read_new_lines(logfile: Path, start_pos: int) -> Tuple[str, int]:
    with logfile.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(start_pos)
        data = f.read()
        new_pos = f.tell()
    return data, new_pos


def simulate_combo(kb: Controller, win_key, alt_key, char_key: str, press_delay: float = 0.03):
    # Press modifiers
    if win_key is not None:
        kb.press(win_key)
        time.sleep(press_delay)
    if alt_key is not None:
        kb.press(alt_key)
        time.sleep(press_delay)

    # Press and release character
    keycode = KeyCode.from_char(char_key)
    kb.press(keycode)
    time.sleep(press_delay)
    kb.release(keycode)
    time.sleep(press_delay)

    # Release modifiers (reverse order)
    if alt_key is not None:
        kb.release(alt_key)
        time.sleep(press_delay)
    if win_key is not None:
        kb.release(win_key)
        time.sleep(press_delay)


def combos_to_test(include_win: bool, include_altgr: bool) -> List[Tuple[Optional[Key], Optional[Key]]]:
    win_variants = [None]
    if include_win:
        # Try generic and side-specific variants
        win_variants = [Key.cmd]
        # Side-specific if available on current platform
        for name in ("cmd_l", "cmd_r"):
            if getattr(Key, name, None) is not None:
                win_variants.append(getattr(Key, name))

    alt_variants: List[Optional[Key]] = [Key.alt]
    for name in ("alt_l", "alt_r"):
        if getattr(Key, name, None) is not None:
            alt_variants.append(getattr(Key, name))
    if include_altgr and getattr(Key, "alt_gr", None) is not None:
        alt_variants.append(getattr(Key, "alt_gr"))

    result = []
    for w in win_variants:
        for a in alt_variants:
            result.append((w, a))
    return result


def scan_for_trigger(new_log_data: str) -> Optional[str]:
    for p in TRIGGER_PATTERNS:
        if p in new_log_data:
            return p
    return None


def run_test(target_chars: List[str], retries: int, wait_after_press: float, include_win: bool, include_altgr: bool, logfile: Optional[Path]) -> int:
    if logfile is None:
        logfile = find_latest_logfile()
    if logfile is None:
        print("[ERROR] No log file found under ./logs. Please start the app first.")
        return 2

    print(f"[INFO] Using log file: {logfile}")

    if not wait_for_readiness(logfile, timeout=40.0):
        print("[WARN] Did not detect readiness lines; continuing anyway...")

    start_pos = logfile.stat().st_size

    kb = Controller()

    results = []
    pairs = combos_to_test(include_win=include_win, include_altgr=include_altgr)

    for ch in target_chars:
        for (w, a) in pairs:
            desc = f"{getattr(w, 'name', 'none')} + {getattr(a, 'name', 'none')} + {ch}"
            success = False
            pattern_hit: Optional[str] = None
            for attempt in range(1, retries + 1):
                print(f"[TEST] Attempt {attempt}/{retries}: {desc}")
                simulate_combo(kb, w, a, ch)
                time.sleep(wait_after_press)
                data, start_pos = read_new_lines(logfile, start_pos)
                pattern_hit = scan_for_trigger(data)
                if pattern_hit:
                    success = True
                    break
            results.append((desc, success, pattern_hit))

    # Summary
    print("\n=== Hotkey Trigger Test Summary ===")
    ok = 0
    for desc, success, hit in results:
        status = "OK" if success else "FAIL"
        hit_str = f" (matched: {hit})" if hit else ""
        print(f"{status:>4} | {desc}{hit_str}")
        if success:
            ok += 1
    total = len(results)
    print(f"\n[RESULT] {ok}/{total} combinations triggered according to logs.")
    return 0 if ok > 0 else 1


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Simulate hotkey presses and check app logs for triggers.")
    parser.add_argument("--chars", default="o,p", help="Comma-separated character keys to test (e.g., 'o,p')")
    parser.add_argument("--retries", type=int, default=2, help="Retry count per combination")
    parser.add_argument("--wait", type=float, default=1.0, help="Seconds to wait after each keypress before checking logs")
    parser.add_argument("--win", action="store_true", help="Include Windows key in combinations")
    parser.add_argument("--altgr", action="store_true", help="Include AltGr variant in combinations")
    parser.add_argument("--logfile", type=str, default=None, help="Explicit path to log file")

    args = parser.parse_args(argv)

    target_chars = [c.strip() for c in args.chars.split(",") if c.strip()]
    logfile = Path(args.logfile) if args.logfile else None

    return run_test(
        target_chars=target_chars,
        retries=args.retries,
        wait_after_press=args.wait,
        include_win=args.win,
        include_altgr=args.altgr,
        logfile=logfile,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))