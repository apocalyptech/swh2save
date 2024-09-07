SteamWorld Heist II CLI Save Editor
===================================

This is a Python-based CLI save editor for the excellent
[SteamWorld Heist II](https://store.steampowered.com/app/2396240) from
Thunderful Development.

- [WARNING](#warning)
- [Running / Installation](#running--installation)
  - [Easiest Method: pip](#easiest-method-pip)
  - [Git Checkout (the proper way)](#git-checkout-the-proper-way)
  - [Git Checkout (the lazy way)](#git-checkout-the-lazy-way)
- [Usage](#usage)
  - [Operational Modes](#operational-modes)
    - [Save Editing](#save-editing)
    - [Show IDs](#show-ids)
    - [Showing Savegame Info](#showing-savegame-info)
    - [Output as JSON](#output-as-json)
    - [Check Savegame (Test our Parsing)](#check-savegame-test-our-parsing)
  - [Basic Options](#basic-options)
    - [Setting the current day](#setting-the-current-day)
    - [Fragments and Water (Money)](#fragments-and-water-money)
  - [Crew Editing](#crew-editing)
    - [Unlock Crew](#unlock-crew)
    - [Set Crew Job Levels](#set-crew-job-levels)
    - [Spending Reserve XP](#spending-reserve-xp)
    - [Refresh Crew](#refresh-crew)
  - [Upgrades](#upgrades)
    - [Adding Specific Upgrades](#adding-specific-upgrades)
    - [Removing Specific Upgrades](#removing-specific-upgrades)
    - [Unlocking Upgrade Groups](#unlocking-upgrade-groups)
    - [Adding Specific Key Items](#adding-specific-key-items)
    - [Removing Specific Key Items](#removing-specific-key-items)
    - [Unlocking All Key Items](#unlocking-all-key-items)
    - [Unlocking Sub Abilities](#unlocking-sub-abilities)
    - [Unlocking Celestial Gears](#unlocking-celestial-gears)
  - [Inventory](#inventory)
    - [Add Specific Hats](#add-specific-hats)
    - [Unlocking All Hats](#unlocking-all-hats)
    - [Set Capt. Leeway's Hat](#set-capt-leeways-hat)
    - [Add Specific Ship Equipment](#add-specific-ship-equipment)
    - [Add Specific Utility Items](#add-specific-utility-items)
    - [Add Specific Weapons](#add-specific-weapons)
    - [Endgame Item Packs](#endgame-item-packs)
  - [World Map](#world-map)
    - [Reveal/Hide Map](#revealhide-map)
- [TODO](#todo)
- [Format Info](#format-info)
- [License](#license)

WARNING
=======

Due to the nature of the savegame format (see below in the Format Info
section), and the fact that this utility doesn't actually understand the entire
format yet, edits performed to your savegames have a small but nonzero chance
of resulting in corrupted savegames.  I believe the risk is extremely small,
but keep it in mind!  Even if previous similar edits have worked fine, it's
possible that this could encounter an edge case which results in an invalid
save file.  Keep backups of your saves, and use with caution!

Note too that one known deficiency of the utility is that it currently *cannot*
cope with mid-mission savegames.  It should fail gracefully with a useful error
message to that point, if you try to use it with a save that is mid-mission.

Running / Installation
======================

This is a Python-based CLI app and library.  It should run on Python 3.10+,
though it's received most of its testing on Python 3.12.  There is currently
no GUI component -- you'll have to be comfortable working in the commandline
for this to work.

### Easiest Method: pip

*(This has not yet been released on PyPi, so pip install is not currently
available!)*

### Git Checkout (the proper way)

The app can also be run right from a git checkout.  The "correct" way to
do this is with a virtual environment using
["editable" mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
From the main project checkout dir, this is what you'd run on Unix/MacOS:

    python -m venv .venv
    source .venv/bin/activate
    pip install --editable .

... or on Windows:

    python -m venv virtualenv_dir
    virtualenv_dir\Scripts\activate
    pip install --editable .

Once done, you should be able to run the `heist2save` command from the commandline:

    heist2save --help

### Git Checkout (the lazy way)

Alternatively, if you want to run it directly from a git checkout *without*
setting up a virtual environment and setting it to editable mode, you can
just use the shortcut `heist2save.py` script right in the main dir:

    ./heist2save.py --help

Or, you can call the cli module directly:

    python -m heist2save.cli --help

Usage
=====

Note that for the actual editing arguments, you can specify as many as you want
at once.  For instance, a command to produce a savegame that cheats in about every
possible way, you could run:

    heist2save savegame_000.dat -o new.dat --fragments 2000 --water 20000 \
        --unlock-crew all --crew-level all:all:max \
        --unlock-upgrades --unlock-sub-abilities \
        --unlock-hats --endgame-pack

## Operational Modes

### Save Editing

The usual thing to do with the app is to edit a savegame.  For this, you use the
`-o`/`--output` argument:

    heist2save savegame_000.dat -o new.dat
    heist2save savegame_000.dat --output new.dat

The app will prompt you if the new filename already exists, but if you want to
force it to overwrite an existing file without prompting, you can add the
`-f`/`--force` flag:

    heist2save savegame_000.dat -o new.dat -f
    heist2save savegame_000.dat --output new.dat --force

The app will by default display a warning about making backups to your savegames.
This remains an important consideration: due to the nature of the savegame format,
and the fact that I haven't yet decoded the entire file, the app has to make a
few guesses as to the savefile content, and it could get those guesses wrong.
Even if you've used the utility to do edits in the past without problems, running
them on a fresh savefile could end up in a situation where we don't do the right
thing.  You can disable the display of this warning with the `--no-warning`
flag if you like, though:

    heist2save savegame_000.dat -o new.dat -f --no-warning

### Show IDs

Many of the arguments for save editing, such as adding inventory items, require
using the string IDs used by the game itself.  To get a list of all of these
strings, you can use the `-s`/`--show-ids` argument:

    heist2save -s
    heist2save --show-ids

Whenever you use an argument which requires one of those strings, you can just
use `help` or `list` in place of the ID, and that will also output a list of
valid values for whatever it is you're editing.

### Showing Savegame Info

You can also just show the current state of a savegame using the `-l`/`--list`
option:

    heist2save savegame_000.dat -l
    heist2save savegame_000.dat --list

You can get even more information in the listing by also using `-v`/`--verbose`:

    heist2save savegame_000.dat -l -v
    heist2save savegame_000.dat --list --verbose

When using the verbose output mode, the output will attempt to put some data
into columns (though mostly the output is too wide to do so).  To force it to
use one line per item instead, you can use `-1`/`--single-column`:

    heist2save savegame_000.dat -l -v -1
    heist2save savegame_000.dat --list --verbose --single-column

### Output as JSON

This is mostly just useful to myself, for investigating the savefile and looking
for patterns inbetween saved games, but the data we read in can be dumped in JSON
format for easier browsing.  Note that the JSON dump is incomplete, and does
*not* include all the info that's in the savefile.  (Or in other words, there's
definitely no way to turn a JSON dump back into a savefile.)

    heist2save savegame_000.dat -j dump.json
    heist2save savegame_000.dat --json dump.json

As with the usual save-editing `-o` argument, you can force an overwrite of
the destination file by using `-f`/`--force`.

### Check Savegame (Test our Parsing)

Finally, the app can be used to just check to make sure that our parsing worked
on the specified savegame.  This is mostly just useful for myself -- after making
changes to the app I'll run this option against my collection of savegames to
make sure I didn't break something.  Technically this check happens with every
savegame load regardless of what you're doing; this option's mostly just here to
specify that nothing else needs to be done.  The argument for this is `-c`/`--check`:

    heist2save savegame_000.dat -c
    heist2save savegame_000.dat --check

You can also alternately add some debugging output to this mode, which at the moment
merely dumps the hex values immediately after we stop parsing the file.  Again, this
is really only useful to myself.  It can be done with the `-d`/`--debug` argument:

    heist2save savegame_000.dat -c -d
    heist2save savegame_000.dat --check --debug

Also, if a savegame fails this verification step, you can have it save out the
version of the savegame that the utility would've written out, so that the
discrepancy can be investigated.  Again, this is mostly just useful for myself.
The `-e`/`--error-save-to` argument can be used to specify the output filename for
this debugging file:

    heist2save savegame_000.dat -c -e debug.dat
    heist2save savegame_000.dat --check --error-save-to debug.dat

## Basic Options

### Setting the current day

The current day can be set with the `--day` argument.  Really the only reason you
might want to use this to cheat on one of the game's achievements:

    heist2save savegame_000.dat -o new.dat --day 10

### Fragments and Water (Money)

You can set your count of Fragments and Water with the `--fragments` and `--water`
arguments, respectively:

    heist2save savegame_000.dat -o new.dat --fragments 100
    heist2save savegame_000.dat -o new.dat --water 2000

I have not yet figured out how the savegame stores your current Bounty points,
actually!  I suspect it might be in the mission/quest status somewhere?  That or
I've just missed it entirely.

## Crew Editing

### Unlock Crew

You can unlock crewmembers using the `--unlock-crew` argument.  You can specify
this argument more than once, and/or use a comma to specify more than one crewmember
in the same argument.  For instance, these two commands are functionally identical:

    heist2save savegame_000.dat -o new.dat --unlock-crew sola --unlock-crew crow
    heist2save savegame_000.dat -o new.dat --unlock-crew sola,crow

You can use the special value `all` to unlock all crewmembers:

    heist2save savegame_000.dat -o new.dat --unlock-crew all

Using `help` or `list` will have the app write out the valid IDs you can use for
the crew.  The utility will support both the in-game names plus the names used
internally by the game.  Sometimes those are the same, but for a few characters
they're different.  The possible values are:

- Beacon: `beacon`, `cyclop`
- Chimney: `chimney`
- Cornelius: `cornelius`
- Crowbar: `crowbar`, `crow`
- Daisy: `daisy`
- Judy: `judy`
- Poe: `poe`
- Sola: `sola`, `diver`
- Tristan: `tristan`, `adventure_boy`
- Wesley: `wesley`

### Set Crew Job Levels

You can also set the Level/XP of your crewmembers using the `--crew-level` argument.
The argument syntax for this one is a bit complex: it consists of three values
separated by colons.  The first bit is the crewmember to act on, the second is
the job to alter, and the last is the level to set it to.  So for instance, to set
Sola's Reaper job to Level 5, you would specify:

    heist2save savegame_000.dat -o new.dat --crew-level sola:reaper:5

You can specify this more than once to perform more than one operation.  For instance:

    heist2save savegame_000.dat -o new.dat --crew-level sola:reaper:5 --crew-level wesley:boomer:4

You can specify `all` for the crew component to have this operate on all unlocked
crewmembers, and also use `all` for the job field to apply the level to all jobs.
So to set all unlocked crew to have maximum level, you could use:

    heist2save savegame_000.dat -o new.dat --crew-level all:all:5

You can also use `max` to mean level 5, so this is valid as well:

    heist2save savegame_000.dat -o new.dat --crew-level all:all:max

For the job selection, you can use the value `current` to level up the job that the
crewmember is currently using (based on their equipped weapon), or `default` for
the default class that they're assigned when they have no weapon explicitly equipped:

    heist2save savegame_000.dat -o new.dat --crew-level daisy:current:3
    heist2save savegame_000.dat -o new.dat --crew-level poe:default:max

By default, this argument will only *increase* the level.  If you tell it to set a
job to level 3 but the crewmember is already at level 4 or 5, it will leave that
level alone.  If you specify `--allow-downlevel`, though, then the levels could
be reduced to match your specification:

    heist2save savegame_000.dat -o new.dat --crew-level daisy:brawler:2 --allow-downlevel

For both the crew and job IDs, you can use `help` or `list` to have the app show you
the list of valid options.  The crew names are the same as the list given above in
the `--unlock-crew` section.  The job IDs can also be either the in-game names, or the
names used internally by the game data:

- Boomer: `boomer`
- Brawler: `brawler`, `tank`
- Engineer: `engineer`
- Flanker: `flanker`
- Reaper: `reaper`, `hunter`
- Sniper: `sniper`

### Spending Reserve XP

The `--spend-reserve-xp` argument can be used to assign a crewmember's reserve XP on
the job of your choosing.  This argument needs to be two values separated by a colon.
The first part is the crew name, and the second is the job name to spend it on.  If
the specified job is already at max level, nothing will be done, and if there's more
reserve XP available than is needed to bring the job to maximum level, it will only
consume the necessary reserve XP to do so.  As with the other options, you can use
`help` or `list` to get a list of the valid IDs (they are the same as listed above
in `--unlock-crew` and `--crew-level`).  For the crew component, you can use `all`
to specify all crew.  For the job component, you can use `current` to mean the
currently-active job, or `default` for that crewmember's default job, but you *cannot*
use `all` to specify all jobs:

    heist2save savegame_000.dat -o new.dat --spend-reserve-xp wesley:flanker
    heist2save savegame_000.dat -o new.dat --spend-reserve-xp all:current

### Refresh Crew

The `--refresh-crew` option can be used to mark all crew and equipment as ready for
use in the current day, rather than having to go back to a bar to rest:

    heist2save savegame_000.dat -o new.dat --refresh-crew

## Upgrades

Note that Upgrades are often closely related to Key Items.  For all of the options
in this section, if there is an association between the two, the utility will
automatically do what's necessary to ensure that the two are synced up.  So if
you add an upgrade which requires a key item, that key item will also be added.
Likewise, if you for instance *remove* a key item, it might also remove one or
more upgrades that are associated with it.  In generaly you shouldn't have to
worry about those details, though!

### Adding Specific Upgrades

You can add specific upgrades with the `--add-upgrade` argument.  This can be
specified more than once, and/or you can use multiple upgrades separated by
a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-upgrade crew_health_00 --add-upgrade exp_bonus_00
    heist2save savegame_000.dat -o new.dat --add-upgrade crew_health_00,exp_bonus_00

To get a list of all valid upgrade IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-upgrade help

Adding an upgrade may also add the required key item, if there is a relationship
between the two.

### Removing Specific Upgrades

You can remove specific upgrades wiht the `--remove-upgrade` argument.  This can be
specified more than once, and/or you can use multiple upgrades separated by
a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --remove-upgrade crew_health_00 --remove-upgrade exp_bonus_00
    heist2save savegame_000.dat -o new.dat --remove-upgrade crew_health_00,exp_bonus_00

To get a list of all valid upgrade IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --remove-upgrade help

Removing an upgrade may also remove the associated key item, if there is a relationship
between the two.  Note that this could end up also removing more than just the one
upgrade you intended: the `atomic_engine` Key Item supplies the upgrades `dive_02`
and `geiger_counter_01`.  If you remove either `dive_02` or `geiger_counter_01`, the
`atomic_engine` Key Item will be removed, which will also remove the other upgrade.

### Unlocking Upgrade Groups

All "main" upgrades (from the main Sub Upgrades panel on the sub) can be unlocked
with the `--unlock-main-upgrades` argument.  Note that some of these won't show up
in the sub console until the relevant story triggers have been activated, but their
effects should be active regardless:

    heist2save savegame_000.dat -o new.dat --unlock-main-upgrades

All upgrades acquired via item acquisition through the storyline (such as boosting/diving,
celestial gears, etc) can be unlocked with the `--unlock-item-upgrades` argument.
This will also add in a number of key items:

    heist2save savegame_000.dat -o new.dat --unlock-item-upgrades

All upgrades acquired via the Job Upgrade station on the sub can be unlocked with
the `--unlock-job-upgrades` argument:

    heist2save savegame_000.dat -o new.dat --unlock-job-upgrades

All Personal Upgrades can be unlocked with the `--unlock-personal-upgrades` argument.
Note that this will *only* unlock personal upgrades for crew which are already unlocked.
(Though if you use `--unlock-crew` at the same time, the crew will be unlocked first,
so this argument will work for any freshly-unlocked crew.)

    heist2save savegame_000.dat -o new.dat --unlock-personal-upgrades

*All* upgrades, regardless of category, can be unlocked using the `--unlock-upgrades`
argument.  This is equivalent to specifying the four individual unlock commands at
once.  For instance, these two commands are functionally identical:

    heist2save savegame_000.dat -o new.dat --unlock-upgrades
    heist2save savegame_000.dat -o new.dat --unlock-main-upgrades \
        --unlock-item-upgrades --unlock-job-upgrades \
        --unlock-personal-upgrades

### Adding Specific Key Items

You can add specific Key Items with the `--add-key-item` argument.  This can be
specified more than once, and/or you can use multiple Key Items separated by
a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-key-item keyitem_glow_rod_01 --add-key-item hub_c_flagship_codes
    heist2save savegame_000.dat -o new.dat --add-key-item keyitem_glow_rod_01,hub_c_flagship_codes

To get a list of all valid Key Item IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-key-item help

Adding a Key Item may also add the associated upgrade(s), if there is a relationship
between the two.

### Removing Specific Key Items

You can remove specific Key Items with the `--remove-key-item` argument.  This can be
specified more than once, and/or you can use multiple Key Items separated by
a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --remove-key-item keyitem_glow_rod_01 --add-upgrade hub_c_flagship_codes
    heist2save savegame_000.dat -o new.dat --remove-key-item keyitem_glow_rod_01,hub_c_flagship_codes

To get a list of all valid Key Item IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --remove-key-item help

Removing a Key Item may also remove the associated upgrade(s), if there is a relationship
between the two.

### Unlocking All Key Items

You can also unlock *all* Key Items using the `--unlock-key-items` argument.  This
will also unlock a number of upgrades:

    heist2save savegame_000.dat -o new.dat --unlock-key-items

### Unlocking Sub Abilities

A shortcut argument to unlock all sub abilities (boosting, diving, ram, shield,
sonar, and atomic engine) is `--unlock-sub-abilities`.  This also ends up unlocking
a geiger counter level as a side effect.  These two commands are equivalent:

    heist2save savegame_000.dat -o new.dat --unlock-sub-abilities
    heist2save savegame_000.dat -o new.dat \
        --add-upgrade ship_boost_00,dive_00,dive_02,geiger_counter_01,sonar \
        --add-key-item keyitem_ship_ram,keyitem_ship_shield

### Unlocking Celestial Gears

There are seven gears in the game which can be unlocked after reaching maximum
reputation in their map areas, from the bar in the area.  These provide various
buffs to your whole crew.  These can all be unlocked with the `--unlock-gears`
argument.  It will unlock both the Key Items and their related upgrades.

    heist2save savegame_000.dat -o new.dat --unlock-gears

This is equivalent to using `--add-upgrade` or `--add-key-item` arguments and
specifying all seven upgrades/item IDs.

## Inventory

Where possible, when adding new items of any sort to the game, the utility will
mark the added items as "New" ingame.  To prevent that from happening (so you
don't have to mouseover the items in inventory to get rid of the flashing
notifier), use the `--no-new-items` argument.  (This is also true for Key Items
listed above, actually.)

    heist2save savegame_000.dat -o new.dat --unlock-key-items --no-new-items

### Add Specific Hats

Specific hats can be added using the `--add-hat` argument.  This can be
specified more than once, and/or you can specify multiple hats separated by
a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-hat hat_navy_seabot_sniper --add-hat hat_shop_fish
    heist2save savegame_000.dat -o new.dat --add-hat hat_navy_seabot_sniper,hat_shop_fish

To get a list of all valid hat IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-hat help

Note that this does *not* remove the associated hats from the various Hat
Shops you can find on the map.

### Unlocking All Hats

You can unlock all hats using the `--unlock-hats` argument:

    heist2save savegame_000.dat -o new.dat --unlock-hats

### Set Capt. Leeway's Hat

Yes, you can set the hat that Capt. Leeway wears, with the `--set-leeway-hat`
argument!  It's likely that this choice will be overwritten by the game when
certain story moments are triggered, but you should be able to just set the
hat back afterwards:

    heist2save savegame_000.dat -o new.dat --set-leeway-hat hat_atomic_reviver_king

This does *not* unlock the specified hat for crew use; use the `--add-hat` or
`--unlock-hats` args for that.

### Add Specific Ship Equipment

Specific ship equipment (wepons, armor, speed boosts, etc) can be added using the
`--add-ship-equipment` argument.  This can be specified more than once, and/or you
can specify multiple items separated by a comma.  For instance, these two statements
are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-ship-equipment ship_equipment_cannon_01 \
        --add-ship-equipment ship_equipment_torpedo_01
    heist2save savegame_000.dat -o new.dat --add-ship-equipment \
        ship_equipment_cannon_01,ship_equipment_torpedo_01

To get a list of all valid item IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-ship-equipment help

### Add Specific Utility Items

Specific utility items (armor, boots, XP boosts, etc) can be added using the
`--add-utility` argument.  This can be specified more than once, and/or you
can specify multiple items separated by a comma.  For instance, these two statements
are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-utility utility_boots_01 --add-utility utility_jetpack
    heist2save savegame_000.dat -o new.dat --add-utility utility_boots_01,utility_jetpack

To get a list of all valid item IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-utility help

### Add Specific Weapons

Specific weapons can be added using the `--add-weapon` argument.  This can be
specified more than once, and/or you can specify multiple weapons separated
by a comma.  For instance, these two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --add-weapon hammer_04 --add-weapon shotgun_03_rare
    heist2save savegame_000.dat -o new.dat --add-weapon hammer_04,shotgun_03_rare

To get a list of all valid item IDs, use `list` or `help` for the name:

    heist2save savegame_000.dat -o new.dat --add-weapon help

### Endgame Item Packs

There are a few cheaty arguments to add sets of items to your inventory all
at once, in case you just feel like cheating from the early game with a
full set of endgame gear.

To add a collection of endgame ship equipment, use the `--endgame-ship-pack`
argument:

    heist2save savegame_000.dat -o new.dat --endgame-ship-pack

To add a collection of endgame weapons, use the `--endgame-weapon-pack`
argument:

    heist2save savegame_000.dat -o new.dat --endgame-weapon-pack

To add a collection of endgame utility items, use the `--endgame-utility-pack`
argument:

    heist2save savegame_000.dat -o new.dat --endgame-utility-pack

And finally, to add all three of those packs at once, use the `--endgame-pack`
option.  These two statements are functionally identical:

    heist2save savegame_000.dat -o new.dat --endgame-pack
    heist2save savegame_000.dat -o new.dat --endgame-ship-pack \
        --endgame-utility-pack --endgame-weapon-pack

## World Map

### Reveal/Hide Map

You can reveal or hide the entire world map using the `--reveal-map` or
`--hide-map` arguments:

    heist2save savegame_000.dat -o new.dat --reveal-map
    heist2save savegame_000.dat -o new.dat --hide-map

TODO
====

- Pull `string_finder.py` into the module
- Add arg to write out savefiles with all strings expanded
  - The code for this is technically in place but commented out.  It turns out
    that the increased number of strings makes false positives on references
    likely enough that I actually ran into it on at least one of my saves.
    Will keep this commented until I get the rest of the file parsed so we
    can jettison the string searching altogether.
- Crew levelling could use a bit more thorough testing
- Put in a *sensible* way to create new Chunk objects; my current implementation
  makes that super awkward.
- Finish parsing the remainder of the file.  I actually came across a scenario
  where a detected string ref was a false positive while testing out the string
  expansion (see above).  Still a pretty rare occurrence, but I don't think I'll
  feel 100% about things until that's done.
- Would be nice to figure out where Bounty points are stored

Format Info
===========

I've got various notes on the file format in [FORMAT.md](FORMAT.md), detailing
some of the aspects of the format which necessitates having the big WARNING
up at the top of this README.  That doesn't go into specific details about
the nuts-and-bolts; for that, just check the sourcecode.

License
=======

`swh2save` is licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
A copy can be found at [LICENSE.txt](LICENSE.txt).

