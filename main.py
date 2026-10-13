"""
    python main.py song.mid            # 真实键盘操作
    python main.py song.mid --dry-run  # 只打印事件，不按键
    python main.py song.mid --speed 0.5
"""

import argparse
import logging
import sys

from player import Player
from runner import run

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
        info=run(args.midi_file,args.speed,args.dry_run)
    except FileNotFoundError:
        print(f"ERROR: 文件不存在: {args.midi_file}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: 无法解析 MIDI 文件: {e}", file=sys.stderr)
        return 1

    print("MIDI Keyboard Player")
    print()
    print(f"File: {args.midi_file}")
    print(f"Notes: {info['Notes']} (mapped: {info['mapped']})")
    print(f"Duration: {info['duration']}")
    if args.dry_run:
        print("Mode: dry-run (不执行键盘操作)")
    print()
    input("Press Enter to start...")
    player = Player(dry_run=args.dry_run)
    player.start(info['events'])
    player.play(info['events'])
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
