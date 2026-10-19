"""World-state tile variants ("disasters" in the engine): which overworld tiles the game swaps for a second
version after an event, and which event flag decides it. Mirrors src/goblin_world_variants.hpp.

eldenring.exe hardcodes it (1.16 FUN_140678260 / 1.17.1 0x1406790b0, the disaster table {300, 310, 330}; RE
2026-10-19): a tile belongs to the disaster of its LOD2 ancestor (gx >> 2, gz >> 2):
    area 61: (11, 11) -> 330  (after Messmer's Kindling), any other LOD2 block of area 61 -> none
    other areas: x2 == 11, z2 == 13 -> 300  (Leyndell outskirts after the Erdtree burns)
                 x2 == 11, z2 == 9  -> 310  (Mistwood after Radahn's star falls)
(the 300/310 test is the ELSE branch of the area-61 test - m61_44..47_36..39 have no second version)
The disaster id IS the event flag: while it is ON the streamer loads the tile with index 0x10 | lod (the
`_10` MSB, `_11`/`_12` at LOD 1/2) instead of `_00`. The switch lands at the next map load; every setter warps or
reloads at once. In ERR flag 300 also goes back OFF (Roundtable Hold braziers), 310 and 330 only by ERR's world
resets. The game keeps the collected state (GEOF) of the two versions apart, under their exact tile ids.
"""

DISASTER_FLAGS = (300, 310, 330)
OVERWORLD_AREAS = range(50, 89)   # eldenring-rs BlockId::is_overworld


def disaster_of(area, gx, gz):
    """The disaster (= its event flag) a LOD0 overworld tile belongs to, or 0."""
    if area not in OVERWORLD_AREAS:
        return 0
    x2, z2 = gx >> 2, gz >> 2
    if area == 61:
        return 330 if (x2, z2) == (11, 11) else 0
    if x2 == 11:
        if z2 == 13:
            return 300
        if z2 == 9:
            return 310
    return 0


def split_map(map_name):
    """'m60_45_37_10' -> (60, 45, 37, variant 1, lod 0); the MSB name's last two digits are the index byte's
    two nibbles (variant, lod). None for anything else."""
    parts = map_name.split('_')
    if len(parts) != 4 or not parts[0].startswith('m'):
        return None
    try:
        area, gx, gz, idx = int(parts[0][1:]), int(parts[1]), int(parts[2]), parts[3]
    except ValueError:
        return None
    if len(idx) != 2 or not idx.isdigit():
        return None
    return area, gx, gz, int(idx[0]), int(idx[1])


def single_variant_tags(items, same=0.5):
    """For items on disaster tiles: {id(item): variant} for every item whose spot exists in ONE version of its
    tile only (no item of the other version within `same` m in x, y and z). Items with a twin in the other version
    are left out - one marker serves both (their asset name and InstanceID match, so the GEOF slot does too).

    Only assets (AEG*) count: their collected state is per version (GEOF). A spot kept by an event flag - a
    boss's piece named after the enemy part - is one state across both versions and keeps its marker as is."""
    by_tile = {}
    for it in items:
        if not str(it.get('name', '')).startswith('AEG'):
            continue
        s = split_map(it.get('map', ''))
        if not s or s[4] != 0 or not disaster_of(s[0], s[1], s[2]):
            continue
        by_tile.setdefault((s[0], s[1], s[2]), {0: [], 1: []}).setdefault(s[3], []).append(it)
    tags = {}
    for versions in by_tile.values():
        for v in (0, 1):
            other = versions.get(1 - v, [])
            for it in versions.get(v, []):
                if not any(abs(it['x'] - o['x']) <= same and abs(it['z'] - o['z']) <= same
                           and abs(it.get('y', 0.0) - o.get('y', 0.0)) <= same for o in other):
                    tags[id(it)] = v
    return tags
