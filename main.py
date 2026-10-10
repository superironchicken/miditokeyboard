"""MIDI Keyboard Player 第一阶段 CLI。

用法:
    python main.py song.mid            # 真实键盘操作
    python main.py song.mid --dry-run  # 只打印事件，不按键
    python main.py song.mid --speed 0.5
"""

import argparse
import logging
import sys

from mapping import map_notes
from midi import parse_midi
from player import Player, build_key_events


def format_duration(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:04.1f}"


def main() -> int:
    parser = argparse.ArgumentParser(description="MIDI Keyboard Player")
    parser.add_argument("midi_file", help="MIDI 文件路径 (.mid/.midi)")
    parser.add_argument("--dry-run", action="store_true", help="只打印事件，不执行键盘操作")
    parser.add_argument("--speed", type=float, default=1.0, help="播放速度倍率，如 0.5 表示 50%% 速度")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.speed <= 0:
        print("ERROR: --speed 必须大于 0", file=sys.stderr)
        return 1

    try:
        notes = parse_midi(args.midi_file)
    except FileNotFoundError:
        print(f"ERROR: 文件不存在: {args.midi_file}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: 无法解析 MIDI 文件: {e}", file=sys.stderr)
        return 1

    mapped = map_notes(notes)
    if not mapped:
        print("ERROR: 没有音符落在键位映射范围内", file=sys.stderr)
        return 1

    duration = max(n.end for n in mapped) / args.speed
    print("MIDI Keyboard Player")
    print()
    print(f"File: {args.midi_file}")
    print(f"Notes: {len(notes)} (mapped: {len(mapped)})")
    print(f"Duration: {format_duration(duration)}")
    if args.dry_run:
        print("Mode: dry-run (不执行键盘操作)")
    print()
    input("Press Enter to start...")

    events = build_key_events(mapped, speed=args.speed)
    player = Player(dry_run=args.dry_run)
    player.play(events)
    return 0


if __name__ == "__main__":
    sys.exit(main())
