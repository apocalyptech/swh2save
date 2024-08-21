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

    # TODO: Would like to do these more selectively
    parser.add_argument('--unlock-upgrades',
            action='store_true',
            help="""
                Unlock all sub upgrades.  Note that some upgrades are dependent on story triggers
                to actually become active, so you may not actually have access to all of them
                immediately.
                """,
            )

    parser.add_argument('--unlock-hats',
            action='store_true',
            help='Unlock all hats',
            )

    parser.add_argument('filename',
            type=str,
            nargs=1,
            help='Savefile to open',
            )

    args = parser.parse_args()
    args.filename = args.filename[0]

    if args.single_column:
        columns = 1
    else:
        columns = None

    save = Savefile(args.filename)

    if args.list:

        # TODO: would like to pull in english titles for various of the raw values
        print(f'Savefile Version: {save.version}')
        print('General Game Information:')
        print(f' - Water (money): {save.resources.water}')
        print(f' - Fragments: {save.resources.fragments}')
        print(f'Crew Unlocked: {len(save.header.crew)}')
        print_columns(save.header.crew)
        print(f'Unlocked Sub Upgrades: {len(save.ship.upgrades)}/{len(SHIP_UPGRADES)}')
        if args.verbose:
            print_columns(sorted(save.ship.upgrades), columns=columns, lookup=SHIP_UPGRADES, lookup_sort=True)
        print(f'Equipped Sub Equipment: {len(save.ship.equipped)}')
        if args.verbose:
            print_columns(save.ship.equipped, columns=columns)
        print(f'Items in inventory: {len(save.inventory.items)}')
        if args.verbose:
            print_columns(save.inventory.items, columns=columns)
        print(f'Unlocked hats: {len(save.inventory.hats)}/{len(HATS)}')
        if args.verbose:
            print_columns(sorted(save.inventory.hats), columns=columns, lookup=HATS, lookup_sort=True)

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

        if args.water is not None:
            if save.resources.water == args.water:
                print(f'Skipping water; already set to {args.water}')
            else:
                print(f'Setting water to: {args.water}')
                save.resources.water = args.water
                do_save = True

        if args.fragments is not None:
            if save.resources.fragments == args.fragments:
                print(f'Skipping fragments; already set to {args.fragments}')
            else:
                print(f'Setting fragments to: {args.fragments}')
                save.resources.fragments = args.fragments
                do_save = True

        if args.unlock_upgrades:
            needed_upgrades = set(SHIP_UPGRADES.keys()) - set(save.ship.upgrades)
            if len(needed_upgrades) == 0:
                print(f'Skipping upgrade unlocks; all upgrades are already unlocked')
            else:
                print(f'Unlocking {len(needed_upgrades)} sub upgrades')
                save.ship.upgrades.extend(sorted(needed_upgrades))
                required_keyitems = set()
                for upgrade_str in needed_upgrades:
                    upgrade = SHIP_UPGRADES[upgrade_str]
                    if upgrade.keyitem is not None:
                        required_keyitems.add(upgrade.keyitem)
                # Theoretically we shouldn't have to bother with checking to see if
                # we have these keyitems; if we *had* the item we'd've probably already
                # had the upgrade.  But still, let's check anyway.
                needed_keyitems = required_keyitems - set([i.name for i in save.inventory.items])
                print(f' - Also unlocking {len(needed_keyitems)} needed key items')
                for item in sorted(needed_keyitems):
                    save.inventory.add_item(item, InventoryItem.ItemFlag.KEYITEM)
                do_save = True

        if args.unlock_hats:
            needed_hats = set(HATS.keys()) - set(save.inventory.hats)
            if len(needed_hats) == 0:
                print(f'Skipping hat unlocks; all hats are already unlocked')
            else:
                print(f'Unlocking {len(needed_hats)} hats')
                save.inventory.hats.extend(sorted(needed_hats))
                save.inventory.new_hats.extend(sorted(needed_hats))
                do_save = True

        if do_save:
            save.save_to(args.output)
            print(f'Wrote to: {args.output}')
            print('')


if __name__ == '__main__':
    main()

