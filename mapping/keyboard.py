import logging
from dataclasses import dataclass

from midi.models import NoteEvent

logger = logging.getLogger(__name__)

# 半音修饰键（按下主键前需要先按住），伪键名，易修改
SEMITONE_KEY = "mouse_middle"

# 音区对应的鼠标修饰键：48-59 left / 60-71 无 / 72-83 right
REGION_MOUSE = {0: "mouse_left", 1: None, 2: "mouse_right"}

# 半音编号 -> 实际物理按键（z-x-c-v-b-n-m）
NOTE_KEYS = {
    0: "z", 1: "z", 2: "x", 3: "x", 4: "c",
    5: "v", 6: "v", 7: "b", 8: "b", 9: "n", 10: "n", 11: "m",
}

# 哪些半音编号是升号（黑键）
SEMITONE_CLASSES = {1, 3, 6, 8, 10}


@dataclass(frozen=True)
class KeyBinding:
    """一个 pitch 对应的完整按键组合。

    key:      实际按下的物理主键（不含 #）
    semitone: 是否需要按住半音修饰键
    mouse:    需要按住的鼠标键（伪键名），None 表示不需要
    """

    key: str
    semitone: bool = False
    mouse: str | None = None

    @property
    def label(self) -> str:
        """dry-run 显示用：带 # 表示半音。"""
        return self.key + ("#" if self.semitone else "")

    @property
    def modifiers(self) -> tuple[str, ...]:
        mods = []
        if self.semitone:
            mods.append(SEMITONE_KEY)
        if self.mouse:
            mods.append(self.mouse)
        return tuple(mods)


def _make_binding(pitch: int) -> KeyBinding:
    pitch_class = pitch % 12
    region = pitch // 12 - 4  # 48-59 -> 0, 60-71 -> 1, 72-83 -> 2
    return KeyBinding(
        key=NOTE_KEYS[pitch_class],
        semitone=pitch_class in SEMITONE_CLASSES,
        mouse=REGION_MOUSE[region],
    )


# 键位映射：pitch -> KeyBinding
KEY_MAP: dict[int, KeyBinding] = {pitch: _make_binding(pitch) for pitch in range(48, 84)}


def map_notes(notes: list[NoteEvent]) -> list[NoteEvent]:
    """过滤掉没有键位映射的音符，并输出 WARNING。

    返回的是原列表的子集（NoteEvent 不可变，直接复用即可）。
    """
    mapped = []
    for note in notes:
        if note.pitch in KEY_MAP:
            mapped.append(note)
        else:
            logger.warning("unmapped MIDI note %d", note.pitch)
    return mapped
