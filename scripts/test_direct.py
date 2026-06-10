# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

from tmp import load_map, search, trace_path, floor_search, has_item, can_fight_guard, check_boss, check_guard_then_boss

# 构造MT6后的状态（策略A的实际路径）
state = {
    'hp': 584, 'atk': 21, 'def': 10, 'yk': 2, 'bk': 0,
    'collected': {
        (11, 11, 'sword1'), (2, 9, 'redGem'), (2, 1, 'blueGem'),
        (11, 11, 'redPotion'), (11, 11, 'yellowKey')
    }
}

print(f"MT6后状态: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")

# MT7: 优先保留YK
print("\n=== MT7 ===")
results, _ = floor_search('MT7', state, ['upFloor', 'redGem'], state['collected'])
yk2 = [r for r in results if r['yk'] >= 2]
print(f"MT7 results: {len(results)}, YK>=2: {len(yk2)}")
for r in sorted(results, key=lambda x: -x['hp'])[:8]:
    print(f"  HP={r['hp']} ATK={r['atk']} DEF={r['def']} YK={r['yk']}")

if yk2:
    state = max(yk2, key=lambda x: x['hp'])
    print(f"选: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
else:
    results2, _ = floor_search('MT7', state, ['upFloor'], state['collected'])
    yk2 = [r for r in results2 if r['yk'] >= 2]
    if yk2:
        state = max(yk2, key=lambda x: x['hp'])
        print(f"MT7(upFloor only)选: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
    else:
        print("MT7: no YK>=2 result")
        state = None

if state:
    # 1F flyback
    print("\n=== 1F flyback ===")
    if state['yk'] >= 2:
        results, _ = floor_search('MT1', state, ['redGem', 'blueGem'], state['collected'])
        gem = [r for r in results if has_item(r, 'redGem')]
        print(f"1F results: {len(results)}, gem: {len(gem)}")
        for r in sorted(results, key=lambda x: -x['hp'])[:5]:
            print(f"  HP={r['hp']} ATK={r['atk']} DEF={r['def']} YK={r['yk']}")
        if gem:
            state = max(gem, key=lambda x: x['hp'])
            print(f"1F选: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
        else:
            print("1F: no gem")
    else:
        print(f"1F skipped: YK={state['yk']} < 2")

    # MT8
    print("\n=== MT8 ===")
    results, _ = floor_search('MT8', state, ['upFloor'], state['collected'])
    passable = [r for r in results if can_fight_guard(r['atk'], r['def'])]
    print(f"MT8 results: {len(results)}, passable: {len(passable)}")
    for r in sorted(results, key=lambda x: -x['hp'])[:5]:
        print(f"  HP={r['hp']} ATK={r['atk']} DEF={r['def']} YK={r['yk']}")
    if passable:
        state = max(passable, key=lambda x: x['hp'])
        print(f"MT8选: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
    elif results:
        state = max(results, key=lambda x: x['hp'])
        print(f"MT8选(非passable): HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
    else:
        print("MT8: NO PATH")
        state = None

    if state:
        # MT9
        print("\n=== MT9 ===")
        results, _ = floor_search('MT9', state, ['shield1', 'upFloor'], state['collected'])
        shield = [r for r in results if has_item(r, 'shield1')]
        print(f"MT9 results: {len(results)}, shield: {len(shield)}")
        for r in sorted(results, key=lambda x: -x['hp'])[:5]:
            print(f"  HP={r['hp']} ATK={r['atk']} DEF={r['def']} YK={r['yk']}")
        if shield:
            state = max(shield, key=lambda x: x['hp'])
            print(f"MT9选: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")
            ok_g, total_g, sur_g = check_guard_then_boss(state)
            ok_b, boss_dmg, sur_b = check_boss(state)
            print(f"\n最终: HP={state['hp']} ATK={state['atk']} DEF={state['def']}")
            print(f"  守卫+Boss={total_g}, 通关(含守卫): {'YES' if ok_g else 'NO'} 余量={sur_g}")
            print(f"  仅Boss={boss_dmg}, 通关(仅Boss): {'YES' if ok_b else 'NO'} 余量={sur_b}")
        else:
            print("MT9: no shield")
