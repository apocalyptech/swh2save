#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright (C) 2024 Christopher J. Kucera
#
# swh2save is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os
import math
import argparse
import textwrap
import itertools

from .gamedata import *
from .savefile import Savefile, InventoryItem

def column_chunks(l, columns):
    """
    Divide up a given list `l` into the specified number of
    `columns`.  Yields each column in turn, as a list.  (Does
    *not* do any padding.)
    """
    length = len(l)
    if length == 0:
        yield []
    else:
        n = math.ceil(length/columns)
        for i in range(0, length, n):
            yield l[i:i + n]


def print_columns(
        data,
        *, 
        minimum_lines=12,
        max_width=79,
        indent=' ',
        padding='  ',
        prefix='- ',
        columns=None,
        lookup=None,
        lookup_sort=False,
        ):
    """
    Function to take a list of `data` and output in columns, if we can.

    `minimum_lines` determines how many items there should be before we
    start outputting in columns.
    
    `max_width` determines how wide the output is allowed to be.

    `indent` is the start-of-line indentation that will be prefixed on
    every line (and is taken into account when computing versus
    `max_width`).

    `padding` is the padding that will be printed between each column.

    `prefix` is a string prefix which will be prefixed on each item to
    be printed.

    `columns` can be used to force a certain number of columns without
    doing any width checking.

    `lookup` is a dict which, if defined, will be used to see if we have
    a better way to show the data.  This is assumed to have values which
    are GameData objects, but it could be anything.

    `lookup_sort`, if True, will cause our `lookup`-processed objects to
    be sorted after doing the conversion.  Otherwise the order will be
    left as-is.
    """
    if len(data) == 0:
        return
    if lookup is not None:
        new_data = []
        for item in data:
            if item in lookup:
                new_data.append(lookup[item])
            else:
                new_data.append(item)
        if lookup_sort:
            new_data.sort()
        data = new_data
    str_data = [f'{prefix}{item}' for item in data]
    force_output = False
    if columns is None:
        num_columns = math.ceil(len(str_data)/minimum_lines)
    else:
        num_columns = columns
        force_output = True

    # There might be a better way to do this, but what we're doing is starting
    # at our "ideal" column number, seeing if it fits in our max_width, and
    # then decreasing by one until it actually fits.  We could, instead, take
    # a look at the max length overall and base stuff on that, or take an
    # average and hope for the best, but the upside is that this *will* give
    # us the most number of columns we can fit for the data, if need be.
    while True:
        max_widths = [0]*num_columns
        cols = list(column_chunks(str_data, num_columns))
        for idx, col in enumerate(cols):
            for item in col:
                max_widths[idx] = max(max_widths[idx], len(item))
        total_width = len(indent) + sum(max_widths) + (len(padding)*(num_columns-1))
        if force_output or total_width <= max_width or num_columns == 1:
            format_str = '{}{}'.format(
                    indent,
                    padding.join([f'{{:<{l}}}' for l in max_widths]),
                    )
            for row_data in itertools.zip_longest(*cols, fillvalue=''):
                print(format_str.format(*row_data))
            break
        else:
            num_columns -= 1


class FlexiListAction(argparse.Action):
    """
    A custom argparse action which sort of acts like `append` in that
    it creates a list and can be specified multiple times.  The main
    difference is that users can also submit a comma-separated list
    and it will be automatically split apart and added to the list.

    Additionally, if `list` or `help` ever appears anywhere in the list,
    it'll trim down the list to just a single option (will use `list`,
    regardless of whether `list` or `help` was specified).

    Given what we're using this for, there's actually *relatively*
    little reason not to use a set rather than a list.  The one reason
    I'm not is that when adding inventory items, they'll show up in
    the in-game inventory in the order they're added (well, the reverse
    of the order added, anyway), and I'd like the user-specified
    item adding to reflect that.  So, a list it is.
    """

    def __call__(self, parser, namespace, this_value, option_string):

        # Force the attribute to a list, if it isn't already
        arg_value = getattr(namespace, self.dest)
        if not isinstance(arg_value, list):
            arg_value = []

        # Check for `list`
        if 'list' in arg_value:
            return

        # Split the given arg, if necessary
        if ',' in this_value:
            values = [v.strip() for v in this_value.split(',')]
        else:
            values = [this_value.strip()]

        # Check to see if `list` or `help` was specified.  If so,
        # trim it down, otherwise add the new values.
        if 'list' in values or 'help' in values:
            arg_value = ['list']
        else:
            arg_value.extend(values)

        # Set our value and continue on!
        setattr(namespace, self.dest, arg_value)


def main():

    parser = argparse.ArgumentParser(
            description='SteamWorld Heist II CLI Save Editor',
            )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument('-l', '--list',
            action='store_true',
            help='Just show information about the savegame',
            )

    mode.add_argument('-c', '--check',
            action='store_true',
            help='Just check that we can load the file and can produce a 100%%-accurate replica',
            )

    mode.add_argument('-o', '--output',
            type=str,
            help='Output filename (required if making changes)',
            )

    # TODO: We shouldn't have to specify a filename when using this one
    mode.add_argument('-i', '--item-info',
            action='store_true',
            help='Dump a list of item strings that can be used with this app',
            )

    parser.add_argument('-v', '--verbose',
            action='store_true',
            help='Show extra information when listing savegame contents',
            )

    parser.add_argument('-d', '--debug',
            action='store_true',
            help='Extra debugging info (at the moment just some extra data dumps while --check is active)',
            )

    parser.add_argument('-1', '--single_column',
            dest='single_column',
            action='store_true',
            help='Force the verbose view to have one item per line instead of trying to use columns',
            )

    parser.add_argument('--no-warning',
            dest='show_warning',
            action='store_false',
            help='Suppress the warning about potential savefile corruption',
            )

    parser.add_argument('-f', '--force',
            action='store_true',
            help='Overwrite the output filename without prompting, if it already exists',
            )

    parser.add_argument('--fragments',
            type=int,
            help='Sets the number of fragments',
            )

    parser.add_argument('--water',
            type=int,
            help='Sets the amount of water (money)',
            )

    parser.add_argument('--add-upgrade',
            action=FlexiListAction,
            help="""
                Unlock a specific upgrade/upgrades.  This will also unlock key items as
                necessary.  Can be specified more than once, and/or separate upgrade names
                with commas.  Specify `list` or `help` to get a list of valid upgrades.
                """,
            )

    # TODO: I'd like to be able to unlock these by category, as well...
    parser.add_argument('--unlock-upgrades',
            action='store_true',
            help="""
                Unlock all upgrades.  This will also unlock key items as necessary.  Note
                that some upgrades are dependent on story triggers to actually become active,
                so you may not actually have access to all of them immediately.
                """,
            )

    parser.add_argument('--add-key-item',
            action=FlexiListAction,
            help="""
                Unlock a specific key item/items.  These are often tied to ship upgrades, and
                the game should automatically apply the ship upgrade if the key item is in
                your inventory.  Can be specified more than once, and/or separate item names
                with commas.  Specify `list` or `help` to get a list of valid key items.
                """,
            )

    parser.add_argument('--unlock-key-items',
            action='store_true',
            help="""
                Unlock all Key Items.  These are often tied to ship upgrades, and the game
                should automatically apply the ship upgrade when key items are in your
                inventory.
                """,
            )

    parser.add_argument('--unlock-hats',
            action='store_true',
            help='Unlock all hats',
            )

    parser.add_argument('--endgame-ship-pack',
            action='store_true',
            help='Adds a collection of endgame ship equipment to your inventory',
            )

    parser.add_argument('--endgame-weapon-pack',
            action='store_true',
            help='Adds a collection of endgame weapons to your inventory',
            )

    parser.add_argument('--endgame-utility-pack',
            action='store_true',
            help='Adds a collection of endgame utility (equippable) items to your inventory',
            )

    parser.add_argument('filename',
            type=str,
            nargs=1,
            help='Savefile to open',
            )

    args = parser.parse_args()
    args.filename = args.filename[0]

    # If we need to do some info dumps, do them now before we even try loading
    # a file.
    did_info_dump = False
    for section, lookup, arg_var in [
            ('Weapons', WEAPONS, None),
            ('Utilities', UTILITIES, None),
            ('Ship Equipment', SHIP_EQUIPMENT, None),
            ('Key Items', KEY_ITEMS, 'add_key_item'),
            ('Upgrades', UPGRADES, 'add_upgrade'),
            ('Hats', HATS, None),
            ]:
        show_possibilities = False
        if args.item_info:
            show_possibilities = True
        else:
            if arg_var is not None:
                arg_value = getattr(args, arg_var)
                if arg_value is not None:
                    arg_text = '--{}'.format(arg_var.replace('_', '-'))
                    if 'list' in arg_value:
                        show_possibilities = True
                    else:
                        for item in arg_value:
                            if item not in lookup:
                                print(f'ERROR: "{item}" is not valid in {arg_text}.  Showing available options:')
                                print('')
                                show_possibilities = True
                                break
        if show_possibilities:
            header = f'Valid {section}'
            print(header)
            print('-'*len(header))
            print('')
            for name, obj in sorted(lookup.items()):
                if name == obj.label:
                    print(f' - {name}')
                else:
                    print(f' - {name}: {obj.label}')
            print('')
            did_info_dump = True
    if did_info_dump:
        return

    # Normalize the columns arg for print_columns
    if args.single_column:
        columns = 1
    else:
        columns = None

    # Load in the savefile
    save = Savefile(args.filename)

    # Now decide what to do.  First up: listing contents!
    if args.list:

        print(f'Savefile Version: {save.version}')
        print('General Game Information:')
        print(f' - Water (money): {save.resources.water}')
        print(f' - Fragments: {save.resources.fragments}')
        print(f'Crew Unlocked: {len(save.header.crew)}')
        print_columns(save.header.crew)
        print(f'Unlocked Sub Upgrades: {len(save.ship.upgrades)}/{len(UPGRADES)}')
        if args.verbose:
            print_columns(sorted(save.ship.upgrades), columns=columns, lookup=UPGRADES, lookup_sort=True)
        print(f'Equipped Sub Equipment: {len(save.ship.equipped)}')
        if args.verbose:
            # Not sorting this one since it's a short enough list; that way it should match what shows
            # up in-game.
            print_columns(save.ship.equipped, columns=columns, lookup=SHIP_EQUIPMENT)
        print(f'Items in inventory: {len(save.inventory.items)}')
        if args.verbose:
            # Gonna sort these into categories for ease of browsing.
            lookups = {
                    'Weapons': WEAPONS,
                    'Utilities': UTILITIES,
                    'Ship Equipment': SHIP_EQUIPMENT,
                    'Key Items': KEY_ITEMS,
                    'Other': {},
                    }
            categorized = {
                    'Weapons': [],
                    'Utilities': [],
                    'Ship Equipment': [],
                    'Key Items': [],
                    'Other': [],
                    }
            for item in save.inventory.items:
                for category, lookup in lookups.items():
                    if category == 'Other' or item.name in lookup:
                        categorized[category].append(item.name)
                        break
            for category, items in categorized.items():
                if len(items) > 0:
                    print(f' - {category} ({len(items)}):')
                    print_columns(sorted(items), columns=columns, lookup=lookups[category], lookup_sort=True, indent='   ')
        print(f'Unlocked hats: {len(save.inventory.hats)}/{len(HATS)}')
        if args.verbose:
            print_columns(sorted(save.inventory.hats), columns=columns, lookup=HATS, lookup_sort=True)

    # If we get here, just checking to make sure our parsing works!
    # (That's technically already done by this point; we're just checking to
    # see if we need to print some extra debug info.)
    elif args.check:

        if args.debug:

            # Print the next bunch of data we haven't parsed yet.
            per_line = 16
            lines = 5
            printable_chars = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
            for line in range(lines):
                start = line*per_line
                print('0x{:08X}  '.format(save.remaining_loc+start), end='')
                for (idx, byte) in enumerate(save.remaining[start:start+per_line]):
                    print('{:02X}'.format(byte), end='')
                    print(' ', end='')
                    if idx % 4 == 3:
                        print(' ', end='')
                print('| ', end='')
                for byte in save.remaining[start:start+per_line]:
                    if byte in printable_chars:
                        print(chr(byte), end='')
                    else:
                        print('.', end='')
                print('')

    # Otherwise, we're actually making some edits, theoretically
    elif args.output:

        # Print a warning, now that we're attempting to find+fix string references
        # even in parts of the file we don't actually know how to parse yet.
        if args.show_warning:
            print(textwrap.dedent("""
                    ***WARNING**
                    Due to the nature of the savegame format, and the fact that this utility
                    doesn't actually understand the entire format yet, edits performed to
                    your savegames have a small but nonzero chance of resulting in corrupted
                    savegames.  I believe the risk is extremely small, but keep it in mind!
                    Even if previous similar edits have worked fine, it's possible that this
                    could encounter an edge case which results in an invalid save file.  Keep
                    backups of your saves, and use with caution!
                    ***WARNING**
                    """))

        if not args.force and os.path.exists(args.output):
            print(f'WARNING: {args.output} already exists.')
            response = input('Overwrite (y/N)? ').strip().lower()
            if response == '' or response[0] != 'y':
                print('Exiting!')
                print('')
                return
            print('')

        do_save = False

        # Show the filename again
        print(f'Processing: {args.filename}')
        print('')

        # Water (money)
        if args.water is not None:
            if save.resources.water == args.water:
                print(f'- Skipping water; already set to {args.water}')
            else:
                print(f'- Setting water to: {args.water}')
                save.resources.water = args.water
                do_save = True

        # Fragments
        if args.fragments is not None:
            if save.resources.fragments == args.fragments:
                print(f'- Skipping fragments; already set to {args.fragments}')
            else:
                print(f'- Setting fragments to: {args.fragments}')
                save.resources.fragments = args.fragments
                do_save = True

        # Upgrades
        added_key_items_from_upgrades = False
        if args.unlock_upgrades or args.add_upgrade:
            if args.unlock_upgrades:
                requested_upgrades = UPGRADES.keys()
            else:
                requested_upgrades = args.add_upgrade
            needed_upgrades = set(requested_upgrades) - set(save.ship.upgrades)
            if len(needed_upgrades) == 0:
                print(f'- Skipping upgrade unlocks; all requested upgrades are already unlocked')
            else:
                print(f'- Unlocking {len(needed_upgrades)} upgrades')
                save.ship.upgrades.extend(sorted(needed_upgrades))
                required_keyitems = set()
                for upgrade_str in needed_upgrades:
                    upgrade = UPGRADES[upgrade_str]
                    if upgrade.keyitem is not None:
                        required_keyitems.add(upgrade.keyitem)
                # Theoretically we shouldn't have to bother with checking to see if
                # we have these keyitems; if we *had* the item we'd've probably already
                # had the upgrade.  But still, let's check anyway.
                needed_keyitems = required_keyitems - set([i.name for i in save.inventory.items])
                if len(needed_keyitems) > 0:
                    added_key_items_from_upgrades = True
                    print(f' - Also unlocking {len(needed_keyitems)} needed key items')
                    for item in sorted(needed_keyitems):
                        save.inventory.add_item(item, InventoryItem.ItemFlag.KEYITEM)
                do_save = True

        # Key Items
        if args.unlock_key_items or args.add_key_item:
            if args.unlock_key_items:
                requested_items = KEY_ITEMS.keys()
            else:
                requested_items = args.add_key_item
            needed_keyitems = set(requested_items) - set([i.name for i in save.inventory.items])
            if len(needed_keyitems) == 0:
                print(f'- Skipping key unlocks; all requested key items are already unlocked')
            else:
                if added_key_items_from_upgrades:
                    extra = ' more'
                else:
                    extra = ''
                print(f'- Unlocking {len(needed_keyitems)}{extra} key items')
                for item in sorted(needed_keyitems):
                    save.inventory.add_item(item, InventoryItem.ItemFlag.KEYITEM)
                do_save = True

        # Hats!
        if args.unlock_hats:
            needed_hats = set(HATS.keys()) - set(save.inventory.hats)
            if len(needed_hats) == 0:
                print(f'- Skipping hat unlocks; all requested hats are already unlocked')
            else:
                print(f'- Unlocking {len(needed_hats)} hats')
                save.inventory.hats.extend(sorted(needed_hats))
                save.inventory.new_hats.extend(sorted(needed_hats))
                do_save = True

        # Endgame Ship Equipment Pack
        if args.endgame_ship_pack:
            to_give = [
                    # Front weapons
                    'ship_equipment_torpedo_03',
                    'ship_equipment_charge_laser_02',
                    # Side weapons
                    'ship_equipment_micro_torpedo_02',
                    'ship_equipment_laser_02',
                    # Top weapons
                    'ship_equipment_torpedo_top_01',
                    'ship_equipment_laser_top_01',
                    # Torpedo Damage
                    'ship_equipment_module_torpedo_damage_02',
                    'ship_equipment_module_torpedo_damage_02',
                    # Laser Damage
                    'ship_equipment_module_laser_cooldown_rare_02',
                    'ship_equipment_module_laser_cooldown_rare_02',
                    # Health
                    'ship_equipment_module_health_03',
                    'ship_equipment_module_health_03',
                    # Speed
                    'ship_equipment_module_speed_03',
                    'ship_equipment_module_speed_03',
                    # Air
                    'ship_equipment_module_air_01',
                    ]
            print(f'- Giving {len(to_give)} items in a ship equipment pack')
            for item in to_give:
                save.inventory.add_item(item, InventoryItem.ItemFlag.SHIP_EQUIPMENT)
            do_save = True

        # Endgame weapon pack
        if args.endgame_weapon_pack:
            to_give = [
                    # Snipers
                    'sniper_06',
                    'sniper_06',
                    'sniper_05_rare',
                    'sniper_05_rare',
                    # SMGs (Reaper)
                    'smg_06',
                    'smg_06',
                    'crossbow_05_rare',
                    'crossbow_05_rare',
                    # Handguns (Engineer)
                    'handgun_06',
                    'handgun_06',
                    'handgun_05_rare',
                    'handgun_05_rare',
                    # Launchers (Boomer)
                    'rpg_06',
                    'rpg_06',
                    'launcher_05_rare',
                    'launcher_05_rare',
                    # Hammers (Brawler)
                    'hammer_06',
                    'hammer_06',
                    'hammer_05_rare',
                    'hammer_05_rare',
                    # Shotguns (Flanker)
                    'shotgun_06',
                    'shotgun_06',
                    'shotgun_05_rare',
                    'shotgun_05_rare',
                    ]
            print(f'- Giving {len(to_give)} items in a weapon equipment pack')
            for item in to_give:
                save.inventory.add_item(item, InventoryItem.ItemFlag.WEAPON)
            do_save = True

        # Endgame utility equipment pack
        if args.endgame_utility_pack:
            to_give = [
                    # Repair
                    'utility_repair_03',
                    'utility_repair_03',
                    'utility_repair_03_rare',
                    'utility_repair_03_rare',
                    'utility_stimpack_rare',
                    'utility_stimpack_rare',
                    # Armor
                    'utility_armor_03',
                    'utility_armor_03',
                    'utility_armor_03',
                    'utility_armor_03',
                    'utility_alloy_rare',
                    'utility_alloy_rare',
                    'utility_alloy_rare',
                    'utility_alloy_rare',
                    # Grenades / Rockets
                    'utility_grenade_06_rare',
                    'utility_grenade_06_rare',
                    'utility_rocket_02_rare',
                    'utility_rocket_02_rare',
                    # Sidearms
                    'utility_sidearm_05_rare',
                    'utility_sidearm_05_rare',
                    'utility_sidearm_06_rare',
                    'utility_sidearm_06_rare',
                    # Weapon Chargers
                    'utility_weapon_charger',
                    'utility_weapon_charger',
                    # Knuckles
                    'utility_knuckle_02',
                    'utility_knuckle_02',
                    # Boots / Movement
                    'utility_boots_03_rare',
                    'utility_boots_03_rare',
                    'utility_boots_03_rare',
                    'utility_boots_03_rare',
                    'utility_boots_fireproof',
                    'utility_boots_fireproof',
                    'utility_boots_warm',
                    'utility_boots_warm',
                    'utility_boots_crippleproof',
                    'utility_boots_crippleproof',
                    'utility_jetpack',
                    'utility_jetpack',
                    'utility_jetpack',
                    'utility_jetpack',
                    # Crit / Sniper Tools
                    'utility_crit_plus_1',
                    'utility_crit_plus_1',
                    'utility_scope_02_rare',
                    'utility_scope_02_rare',
                    'utility_scope_03',
                    'utility_scope_03',
                    'utility_goggles_02_rare',
                    'utility_goggles_02_rare',
                    # Cogs
                    'utility_cogs_03',
                    'utility_cogs_03',
                    'utility_cogs_03',
                    'utility_cogs_03',
                    # Aura / Radiance
                    'utility_aura_plus_rare',
                    'utility_aura_plus_rare',
                    'utility_radiance_rare',
                    'utility_radiance_rare',
                    # Damage
                    'utility_damage_rare',
                    'utility_damage_rare',
                    'utility_damage_rare',
                    'utility_damage_rare',
                    # Cooldowns
                    'utility_cool_rare',
                    'utility_cool_rare',
                    'utility_cool_rare',
                    'utility_cool_rare',
                    # XP
                    'utility_experience_badge_02_rare',
                    'utility_experience_badge_02_rare',
                    'utility_experience_badge_02_rare',
                    'utility_experience_badge_02_rare',
                    ]
            print(f'- Giving {len(to_give)} items in a utility equipment pack')
            for item in to_give:
                save.inventory.add_item(item, InventoryItem.ItemFlag.UTILITY)
            do_save = True

        # Save out, assuming we did anything
        if do_save:
            save.save_to(args.output)
            print('')
            print(f'Wrote to: {args.output}')
            print('')
        else:
            print('')
            print('NOTICE: No changes made, not writing any data!')
            print('')


if __name__ == '__main__':
    main()

