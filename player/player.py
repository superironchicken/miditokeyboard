import logging
import time
import threading 
from dataclasses import dataclass

from midi.models import NoteEvent
from mapping.keyboard import KEY_MAP

logger = logging.getLogger(__name__)


@dataclass
class KeyEvent:
    """键盘/鼠标事件：某个按键在某个绝对时间按下/释放。

    mouse_left / mouse_middle / mouse_right 是鼠标伪键名。
    key 是实际传给 pynput 的物理键，label 仅用于显示（如 "z#"）。
    """

    time: float
    key: str
    action: str  # "down" / "up"
    label: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.key


def build_key_events(notes: list[NoteEvent], speed: float = 1.0) -> list[KeyEvent]:
    """NoteEvent[] -> KeyEvent[]，按 (time, phase) 排序。

    每个音符的主键拆成 down/up。修饰键（半音键/鼠标键）通过引用计数共享：
    第一个需要它的音符按下，最后一个不需要时才释放，重叠音符不会互相干扰。
    同一时刻的执行顺序：修饰 DOWN -> 主键 DOWN -> 主键 UP -> 修饰 UP。
    """
    # 扫描标记：(时间, 是否音符结束, 音符下标)
    markers = []
    for i, note in enumerate(notes):
        markers.append((note.start / speed, False, i))
        markers.append((note.end / speed, True, i))
    # 同刻先处理新音符开始，保证共享修饰键计数不中断
    markers.sort(key=lambda m: (m[0], m[1]))

    events: list[tuple[float, int, str, str, str]] = []  # (time, phase, key, action, label)
    active: set[int] = set()

    i = 0
    while i < len(markers):
        t = markers[i][0]
        group = []
        while i < len(markers) and markers[i][0] == t:
            group.append(markers[i])
            i += 1

        held_before = _held_modifiers(active, notes)

        for _, is_end, idx in group:
            binding = KEY_MAP[notes[idx].pitch]
            if is_end:
                active.discard(idx)
                events.append((t, 2, binding.key, "up", binding.label))
            else:
                active.add(idx)
                events.append((t, 1, binding.key, "down", binding.label))

        held_after = _held_modifiers(active, notes)
        for mod in sorted(held_after - held_before):
            events.append((t, 0, mod, "down", mod))
        for mod in sorted(held_before - held_after):
            events.append((t, 3, mod, "up", mod))

    events.sort(key=lambda e: (e[0], e[1]))
    return [KeyEvent(time=t, key=k, action=a, label=lbl) for t, _, k, a, lbl in events]


def _held_modifiers(active: set[int], notes: list[NoteEvent]) -> set[str]:
    mods: set[str] = set()
    for idx in active:
        mods.update(KEY_MAP[notes[idx].pitch].modifiers)
    return mods


class Player:
    """按绝对时间执行 KeyEvent 时间轴。

    用 time.perf_counter() 作为播放时钟，避免累计误差。
    鼠标伪键名分派到 pynput.mouse，其余走 pynput.keyboard。
    退出时释放所有仍处于按下状态的键（安全要求）。
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._pressed: set[str] = set()
        self._running = False
        self._thread = None

        if not dry_run:
            from pynput.keyboard import Controller as KeyboardController
            from pynput.mouse import Button, Controller as MouseController

            self._keyboard = KeyboardController()
            self._mouse = MouseController()
            self._mouse_buttons = {
                "mouse_left": Button.left,
                "mouse_middle": Button.middle,
                "mouse_right": Button.right,
            }
        else:
            self._keyboard = None
            self._mouse = None
            self._mouse_buttons = {}

    def play(self, events: list[KeyEvent]) -> None:
        if not events:
            logger.warning("没有可播放的事件")
            return

        try:
            self._run(events)
        except KeyboardInterrupt:
            print("\nInterrupted.")
        finally:
            # 无论正常结束还是 Ctrl+C，都不能留下按住的键
            self._release_all()

    def start(self, events: list[KeyEvent]):
        if(self._thread and self._thread.is_alive()):
            return
        self._running=True
        self._thread = threading.Thread(
            target=self.play,
            args=(events,)
        )
        self._thread.start()
    def stop(self):
        self._running=False

    def _run(self, events: list[KeyEvent]) -> None:
        start_clock = time.perf_counter()
        for event in events:

            if not self._running:
                break
            # 等到事件的绝对时间点（相对播放起点）
            delay = start_clock + event.time - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            self._execute(event)

    def _execute(self, event: KeyEvent) -> None:
        print(f"[{self._format_time(event.time)}] {event.label} {event.action.upper()}")
        if not self.dry_run:
            if event.key in self._mouse_buttons:
                button = self._mouse_buttons[event.key]
                if event.action == "down":
                    self._mouse.press(button)
                else:
                    self._mouse.release(button)
            elif event.action == "down":
                self._keyboard.press(event.key)
            else:
                self._keyboard.release(event.key)

        if event.action == "down":
            self._pressed.add(event.key)
        else:
            self._pressed.discard(event.key)

    def _release_all(self) -> None:
        for key in sorted(self._pressed):
            print(f"[  exit  ] {key} UP")
            if not self.dry_run:
                if key in self._mouse_buttons:
                    self._mouse.release(self._mouse_buttons[key])
                else:
                    self._keyboard.release(key)
        self._pressed.clear()

    @staticmethod
    def _format_time(seconds: float) -> str:
        m, s = divmod(seconds, 60)
        return f"{int(m):02d}:{s:05.2f}"
