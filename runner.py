from mapping import map_notes
from midi import parse_midi, monophonize
from player import build_key_events
def run(midi_file:str,speed:float=1.0,dry_run:bool=False,optimization:bool=False):

    notes = parse_midi(midi_file)

    mapped = map_notes(notes)
    if not mapped:
        raise ValueError("ERROR: 没有音符落在键位映射范围内")
    duration = max(n.end for n in mapped) / speed
    if optimization:
        mapped = monophonize(mapped)
    events = build_key_events(mapped, speed=speed)
    return {
        "Notes":len(notes),
        "mapped":len(mapped),
        "duration":duration,
        "events":events
    }
