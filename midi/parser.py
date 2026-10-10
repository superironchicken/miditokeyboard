import pretty_midi

from .models import NoteEvent


def parse_midi(path: str) -> list[NoteEvent]:
    """解析 .mid 文件为 NoteEvent 列表。

    - 跳过 percussion/drum track（鼓不是钢琴音符）
    - 过滤 end <= start 的非法音符
    - 合并非鼓轨的所有 instrument（第一阶段策略）
    - 按 start 排序，保证时间轴顺序正确
    """
    midi = pretty_midi.PrettyMIDI(path)

    notes: list[NoteEvent] = []
    for instrument in midi.instruments:
        if instrument.is_drum:
            continue
        for note in instrument.notes:
            if note.end <= note.start:
                continue
            notes.append(
                NoteEvent(
                    pitch=note.pitch,
                    start=note.start,
                    end=note.end,
                    velocity=note.velocity,
                )
            )

    if not notes:
        raise ValueError(f"MIDI 文件中没有可播放的音符: {path}")

    notes.sort(key=lambda n: n.start)
    return notes
