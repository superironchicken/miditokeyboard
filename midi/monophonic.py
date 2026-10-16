"""单音化：把有重叠的 NoteEvent[] 修剪成时间上互不重叠的单旋律。

口琴是单音乐器，同一时刻只能发一个音。MIDI 里同一时刻可能存在和弦、
跨轨叠加、延音未结束就进入下一个音等情况，直接播放会出现"前一个键还没
松开，后一个键已经按下"，表现为丢音。本模块按"低音让路"的原则做修剪。

修剪规则（对每一对重叠的音符 A=前、B=后）：

- A.pitch > B.pitch：B 让路，``B.start = A.end``（高音还在响时低音不发声）
- A.pitch < B.pitch：A 让路，``A.end = B.start``（新音盖住旧的尾音）
- A.pitch == B.pitch：视为"后者让路"，``B.start = A.end``
  （同一个键断奏重按，游戏能识别到新的音头）

两条补充约定：

- **不拆分音符**：只挪 start 或 end，绝不把一个音切成两段。
- **被完全覆盖就丢弃**：修剪后 ``start >= end`` 的音符发不出任何声音，
  直接从结果里去掉。

于是输出满足：按 start 升序、任意两个音符互不重叠（可以首尾相接）。
``NoteEvent`` 是可变的，本函数返回全新对象，不修改传入的列表及其元素。
"""

import logging

from .models import NoteEvent

logger = logging.getLogger(__name__)


def monophonize(notes: list[NoteEvent]) -> list[NoteEvent]:
    """把 NoteEvent[] 修剪为时间上互不重叠的单旋律。

    输入不需要预先排序（内部会按 ``(start, pitch)`` 排序），
    输出按 start 升序，且任意两个音符 ``[start, end)`` 区间互不重叠。

    被完全覆盖或退化为零长度的音符会被丢弃，因此返回的列表长度
    可能小于输入。
    """
    ordered = sorted(notes, key=lambda n: (n.start, n.pitch))

    # 输出列表：最终结果，只增不减（退化音符在最后统一剔除）
    result: list[NoteEvent] = []
    # 工作集合：result 中仍可能和后续音符冲突的音符（按 start 升序）。
    # 由于 result 始终保持两两不重叠，真正冲突的"前一个"最多只有一个。
    active: list[NoteEvent] = []

    for note in ordered:
        # 复制一份，避免修改调用方传入的对象
        current = NoteEvent(
            pitch=note.pitch,
            start=note.start,
            end=note.end,
            velocity=note.velocity,
        )

        # 已结束或已退化的音符不会再和 current 冲突（current.start 只增不减）
        active = [prev for prev in active if prev.start < prev.end and prev.end > current.start]

        # 反复消解冲突：挪动 current.start 或某个前音的 end 之后，可能又暴露
        # 新的重叠。循环一定终止——每一步都让 current.start 严格增大，
        # 或让某个前音的 end 严格减小。
        while True:
            conflict = next(
                (
                    prev
                    for prev in active
                    if prev.end > current.start and prev.start < current.end
                ),
                None,
            )
            if conflict is None:
                break
            if conflict.pitch >= current.pitch:
                # 前者音高不低：后者让路，整体后移
                current.start = conflict.end
            else:
                # 前者更矮：截掉它的尾音
                conflict.end = current.start

        if current.start >= current.end:
            # 被高音完全盖住，或者被削成零长度，发不出声，丢弃
            logger.debug(
                "monophonize: 丢弃 pitch=%d 的音符（区间被完全覆盖）",
                current.pitch,
            )
            continue

        result.append(current)
        active.append(current)

    # 前音被后续音符削短时也可能退化成零长度（同一时刻的和弦就会这样），
    # 此时它已经在 result 里了，统一在最后剔除。同时按 start 重新排序——
    # current.start 被后推之后，可能已越过处理顺序在它后面的音符。
    kept = [note for note in result if note.start < note.end]
    kept.sort(key=lambda n: (n.start, n.pitch))
    return kept
