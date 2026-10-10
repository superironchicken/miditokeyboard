from dataclasses import dataclass


@dataclass
class NoteEvent:
    """项目自己的音符模型，屏蔽 pretty_midi 的数据结构。

    pitch: MIDI 音高编号（C4 = 60）
    start: 开始时间（秒）
    end:   结束时间（秒）
    velocity: MIDI 力度 直觉告诉我暂时用不到
    """

    pitch: int
    start: float
    end: float
    velocity: int

    @property
    def duration(self) -> float:
        return self.end - self.start
