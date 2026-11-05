# Victory Analytics: Pokémon Rejuvenation team-builder database

**[output/Rejuvenation_Pokemon_Database.xlsx](output/Rejuvenation_Pokemon_Database.xlsx)** has every Pokémon listed on the
[Rejuvenation wiki's Pokémon Locations page](https://rejuvenation.wiki.gg/wiki/Pokémon_Locations): 1,157 entries,
including Alolan, Galarian, Hisuian, Paldean and Aevian forms. For each one it gives:

- where to find it, its types, all of its abilities, base stats and BST, EV yield, weaknesses and resistances, and what it evolves into
- its full learnset in Rejuvenation: level-up, TM numbers, tutors (with locations), egg moves and Move Relearner moves
- a **suggested set**: role, ability, nature, EV spread, item, 4 moves, alternative moves, and the score each ability got

| Tab | Contents |
|---|---|
| README | Sources and how the suggestions are made |
| Pokemon | One row per Pokémon/form. Game data plus the suggested set (green columns) |
| Learnsets | About 92k rows, one per Pokémon + move, with how it's learned, type, category, power, accuracy, PP and STAB |
| Moves | All 950 moves with Rejuvenation descriptions and how many Pokémon learn each one |
| Abilities | The effect of every ability, including the 25 abilities made for Rejuvenation |
| Natures | Reference table |

## Data sources
- The Pokémon list and locations come from the wiki API.
- Stats, abilities, movepools and move data come from the wiki's `Module:Database/*` Lua tables. The wiki
  generates these from the game files and uses them to build each Pokémon page.
- Text for mainline abilities comes from PokeAPI. Text for the Rejuvenation abilities comes from each ability's wiki page.

## Rebuilding
```bash
scripts/build.sh          # downloads into ./build, writes output/Rejuvenation_Pokemon_Database.xlsx
```
`luaparse.py` reads the Lua tables as plain data and never runs them.
`recommend.py` holds the rules behind the suggested sets. Change the ability ratings (`AB_FLAT`) or the move
lists there and run the build again.
