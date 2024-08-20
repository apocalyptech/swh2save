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
import itertools

from .gamedata import *
from .savefile import Savefile

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
    """
    if len(data) == 0:
        return
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
    # ... also, this currently ends up creating a "corrupt" save.  I suspect it
    # has to do with breaking string references later in the file that we haven't
    # gotten around to parsing yet.
    #parser.add_argument('--unlock-upgrades',
    #        action='store_true',
    #        help='Unlock all sub upgrades',
    #        )

    # TODO: Likewise, this currently causes "corrupt" saves.  Again, I suspect it
    # may have to do with breaking future string references (though of course it
    # could also be something else entirely -- there's some bytes immediately after
    # the hat list that I don't yet understand)
    #parser.add_argument('--unlock-hats',
    #        action='store_true',
    #        help='Unlock all hats',
    #        )

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
            print_columns(sorted(save.ship.upgrades), columns=columns)
        print(f'Equipped Sub Equipment: {len(save.ship.equipped)}')
        if args.verbose:
            print_columns(save.ship.equipped, columns=columns)
        print(f'Items in inventory: {len(save.inventory.items)}')
        if args.verbose:
            print_columns(save.inventory.items, columns=columns)
        print(f'Unlocked hats: {len(save.inventory.hats)}')
        if args.verbose:
            print_columns(save.inventory.hats, columns=columns)

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

        #if args.unlock_upgrades:
        #    needed_upgrades = SHIP_UPGRADES ^ set(save.ship.upgrades)
        #    if len(needed_upgrades) == 0:
        #        print(f'Skipping upgrade unlocks; all upgrades are already unlocked')
        #    else:
        #        print(f'Unlocking {len(needed_upgrades)} sub upgrades')
        #        save.ship.upgrades.extend(sorted(list(needed_upgrades)))
        #        do_save = True

        #if args.unlock_hats:
        #    needed_hats = HATS ^ set(save.inventory.hats)
        #    if len(needed_hats) == 0:
        #        print(f'Skipping hat unlocks; all hats are already unlocked')
        #    else:
        #        print(f'Unlocking {len(needed_hats)} hats')
        #        save.inventory.hats.extend(sorted(list(needed_hats)))
        #        do_save = True

        save.inventory.hats = ['hat_cyclop', 'hat_piper']
        do_save = True

        if do_save:
            save.save_to(args.output)
            print(f'Wrote to: {args.output}')
            print('')


if __name__ == '__main__':
    main()

