#pragma once
// World-state tile variants ("disasters" in the engine): the overworld tiles the game swaps for a second
// version after an event. Mirrors tools/world_variants.py, which bakes the same rule into the markers.
//
// eldenring.exe hardcodes it (1.16 FUN_140678260 / 1.17.1 0x1406790b0; disaster table {300, 310, 330}; RE
// 2026-10-19): a tile belongs to the disaster of its LOD2 ancestor (gx >> 2, gz >> 2) -
//   area 61: (11, 11) -> 330  (after Messmer's Kindling); any other LOD2 block of area 61 -> none
//   other areas: x2 == 11, z2 == 13 -> 300  (Leyndell outskirts after the Erdtree burns)
//                x2 == 11, z2 == 9  -> 310  (Mistwood after Radahn's star falls)
// (the 300/310 test is the else branch of the area-61 test: m61_44..47_36..39 have one version)
// The disaster id is the event flag. While it is ON the streamer loads the tile with index byte 0x10 | lod
// (`_10`; `_11`/`_12` at LOD 1/2) instead of 0x00 | lod; the switch lands at the next map load, and every
// setter warps or reloads at once. ERR also turns 300 back OFF (Roundtable Hold braziers); 310 and 330 only
// its world resets clear.
//
// The game keeps the collected state of the two versions apart (GeomFlagSaveDataManager is keyed by the exact
// tile id: a `_10` tile loads with none of its `_00` twin's records, nothing copies them), so the spots
// standing in both versions are separate pickups - one marker each (same asset name and InstanceID, so the
// same GEOF slot), whose state is the standing version's.

#include <cstdint>

namespace goblin::world_variants
{
    constexpr uint32_t kDisasterFlags[] = {300, 310, 330};

    // The disaster (= its event flag) of a tile id (area << 24 | gx << 16 | gz << 8 | index), or 0.
    constexpr uint32_t tile_disaster(uint32_t tile_id)
    {
        const uint32_t area = (tile_id >> 24) & 0xFF;
        if (area < 50 || area > 88) return 0;   // eldenring-rs BlockId::is_overworld
        const uint32_t x2 = ((tile_id >> 16) & 0xFF) >> 2, z2 = ((tile_id >> 8) & 0xFF) >> 2;
        if (area == 61) return (x2 == 11 && z2 == 11) ? 330 : 0;
        if (x2 == 11 && z2 == 13) return 300;
        if (x2 == 11 && z2 == 9) return 310;
        return 0;
    }

    // The world-state version a stored tile id (save / GEOF key, low byte = variant << 4 | lod) belongs to.
    constexpr uint32_t key_variant(uint32_t raw_key) { return (raw_key >> 4) & 0xF; }

    static_assert(tile_disaster(0x3C2D2500u) == 310, "m60_45_37 is Mistwood");
    static_assert(tile_disaster(0x3C2E3400u) == 300, "m60_46_52 is the Leyndell outskirts");
    static_assert(tile_disaster(0x3D2E2D00u) == 330, "m61_46_45 is past Messmer's Kindling");
    static_assert(tile_disaster(0x3D2E2500u) == 0, "m61_46_37 has one version (area 61 knows only 330)");
    static_assert(tile_disaster(0x3C2A2400u) == 0, "m60_42_36 has one version");
    static_assert(tile_disaster(0x0C020000u) == 0, "not an overworld tile");
    static_assert(key_variant(0x3C2D2510u) == 1 && key_variant(0x3C2D2500u) == 0, "index nibbles");
}
