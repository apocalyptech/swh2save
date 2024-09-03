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
import json
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

    This is mostly just used in cases where we want to preserve insertion
    order, or when you might want to include the same entry more than once.
    These are things that a user might want for inventory edits.  For cases
    where you only want a set of unique items, you can use FlexiSetAction
    instead.
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


class FlexiSetAction(argparse.Action):
    """
    The equivalent of my FlexiListAction, except it stores data in a
    set instead of a list.  As such, no ordering is preserved.  As with
    FlexiSetAction, if `list` or `help` is specified at any point, the
    only item left in the set after processing will be `list`.
    """

    def __call__(self, parser, namespace, this_value, option_string):

        # Force the attribute to a set, if it isn't already
        arg_value = getattr(namespace, self.dest)
        if not isinstance(arg_value, set):
            arg_value = set()

        # Check for `list`
        if 'list' in arg_value:
            return

        # Split the given arg, if necessary
        if ',' in this_value:
            values = set([v.strip() for v in this_value.split(',')])
        else:
            values = {this_value.strip()}

        # Check to see if `list` or `help` was specified.  If so,
        # trim it down, otherwise add the new values.
        if 'list' in values or 'help' in values:
            arg_value = {'list'}
        else:
            arg_value |= values

        # Set our value and continue on!
        setattr(namespace, self.dest, arg_value)


class FlexiSetAllAction(argparse.Action):
    """
    A variant of FlexiSetAction which, in addition to `help` and `list`,
    will accept the meta-command `all`.  If `all` is encountered at
    any point, the resultant set will only have `all` in it.  `help`/`list`
    will override `all`, though.
    """

    def __call__(self, parser, namespace, this_value, option_string):

        # Force the attribute to a set, if it isn't already
        arg_value = getattr(namespace, self.dest)
        if not isinstance(arg_value, set):
            arg_value = set()

        # Check for `list`
        if 'list' in arg_value:
            return

        # Split the given arg, if necessary
        if ',' in this_value:
            values = set([v.strip() for v in this_value.split(',')])
        else:
            values = {this_value.strip()}

        # Check to see if `list` or `help` was specified.  If so,
        # trim it down, otherwise add the new values.
        if 'list' in values or 'help' in values:
            arg_value = {'list'}
        elif 'all' in values or 'all' in arg_value:
            arg_value = {'all'}
        else:
            arg_value |= values

        # Set our value and continue on!
        setattr(namespace, self.dest, arg_value)


class GameDataLookup:

    def __init__(self, label, lookup, arg_vars, acceptable_extras=None):
        self.label = label
        self.lookup = lookup
        if type(arg_vars) == list:
            self.arg_vars = arg_vars
        else:
            self.arg_vars = [arg_vars]
        if acceptable_extras is None:
            self.acceptable_extras = set()
        else:
            self.acceptable_extras = acceptable_extras
        self.needs_dump = False


    def check_specific(self, arg_value, arg_name):
        # We're doing some duplicate checking here when called via `check_args`,
        # but whatever.
        if arg_value == 'list' or arg_value == 'help':
            self.needs_dump = True
        else:
            if arg_value not in self.lookup and arg_value not in self.acceptable_extras:
                print(f'ERROR: "{arg_value}" is not valid in {arg_name}.  Available options will be shown below.')
                print('')
                self.needs_dump = True


    def check_args(self, args):
        for arg_var in self.arg_vars:
            arg_value = getattr(args, arg_var)
            if arg_value is not None:
                arg_text = '--{}'.format(arg_var.replace('_', '-'))
                if 'list' in arg_value or 'help' in arg_value:
                    self.needs_dump = True
                else:
                    for item in arg_value:
                        self.check_specific(item, arg_text)
                        if self.needs_dump:
                            break


    def show(self, force=False):
        if force or self.needs_dump:
            header = f'Valid {self.label}'
            print(header)
            print('-'*len(header))
            print('')
            for name, obj in sorted(self.lookup.items()):
                if name == obj.label:
                    print(f' - {name}')
                else:
                    print(f' - {name}: {obj.label}')
            for extra in sorted(self.acceptable_extras):
                print(f' - {extra}')
            print('')
            return True
        return False


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

    mode.add_argument('-j', '--json',
            type=str,
            help='JSON-formatted save dump',
            )

    parser.add_argument('-v', '--verbose',
            action='store_true',
            help='Show extra information when listing savegame contents, performing edits, and outputting JSON',
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

    parser.add_argument('--day',
            type=int,
            help='Sets the current day',
            )

    parser.add_argument('--fragments',
            type=int,
            help='Sets the number of fragments',
            )

    parser.add_argument('--water',
            type=int,
            help='Sets the amount of water (money)',
            )

    parser.add_argument('--unlock-crew',
            action=FlexiSetAllAction,
            help="""
                Unlocks the specified crew members.  Can be specified more than once,
                and/or separate crew member names with commas.  Specify `all` to
                unlock all crew, or `list`/`help` to get a list of valid crew
                identifiers.
                """,
            )

    parser.add_argument('--crew-level',
            type=str,
            action='append',
            help="""
                Levels up the specified character(s) to the specified level.
                This arg requires three parts separated by colons: first, the
                character ID (or `all`), then the job ID (or `all` for all
                jobs, `current` for the crewmember's current job, or `default`
                for the crewmember's default job), and finally the level (or
                `max`).  For instance, to level all crew to max level, use
                `all:all:max`.  To level just Wesley's Reaper level to 4, use
                `wesley:reaper:4`.  This argument can be specified more than
                once to perform more that one action.  By default this argument
                will *not* downgrade anyone's level, but if you use the
                --allow-downlevel arg as well, it will do so.  Specify `help`
                or `list` as the argument to show the valid character and job
                IDs.
                """,
            )

    parser.add_argument('--allow-downlevel',
            action='store_true',
            help="""
                Ordinarily when setting crew level/XP, this utility won't move any
                crew's level down -- it'll only go up.  If you do want to set your crew
                levels lower than they currently are, though, use this arg to allow that
                behavior.
                """,
            )

    parser.add_argument('--spend-reserve-xp',
            type=str,
            action='append',
            help="""
                Assigns the specified character's Reserve XP on the specified job.
                This arg requires two parts separated by colons: first, the
                character ID (or `all`), and then the job ID (or `current` for the
                crewmember's current job, or `default` for the crewmember's default
                job).  For instance, to spend all of Daisy's reserve XP on the
                Boomer job, use `daisy:boomer`.  To spend everyone's reserve XP
                on the Engineer job, use `all:engineer`.  This argument can be
                specified more than once to perform more than one action.  This may
                leave some Reserve XP available if the target job reaches max level.
                Specify `help` or `list` as the argument to show the valid character
                and job IDs.
                """,
            )

    parser.add_argument('--refresh-crew',
            action='store_true',
            help='Refreshes all crew/equipment so they can be used again on the current day.',
            )

    parser.add_argument('--add-upgrade',
            action=FlexiSetAction,
            help="""
                Unlock specific upgrades.  This will also unlock Key Items as
                necessary.  Can be specified more than once, and/or separate upgrade names
                with commas.  Specify `list` or `help` to get a list of valid upgrades.
                """,
            )

    parser.add_argument('--remove-upgrade',
            action=FlexiSetAction,
            help="""
                Removes specific upgrades.  Will also remove the matching Key Items if
                needed.  Note that the `atomic_engine` key item provides both the `dive_02`
                and `geiger_counter_01` upgrades.  Removing either of those upgrades will
                trigger the removal of the `atomic_engine` key item, which will then remove
                the other of the upgrade pair.  Removals are processed after all additions.
                """,
            )

    parser.add_argument('--unlock-main-upgrades',
            action='store_true',
            help="""
                Unlock all upgrades ordinarily unlocked by the main Sub Upgrades console
                on your ship.  This includes unlocking the other upgrade stations, sub
                equipment slots, a couple bunk beds, as well as various crew bonuses
                (cogs, utility slots, health, XP bonus, etc).  Upgrades you haven't
                "properly" revealed through quest progress won't show up in the list
                on the console, but their effects should still be active.
                """,
            )

    parser.add_argument('--unlock-item-upgrades',
            action='store_true',
            help="""
                Unlock all upgrades acquired by items, often as part of quest
                progression.  This includes sub improvements such as boosting/diving,
                and the seven bonuses given by celestial gears.  This will also unlock
                Key Items as necessary.
                """,
            )

    parser.add_argument('--unlock-job-upgrades',
            action='store_true',
            help="""
                Unlock all upgrades ordinarily unlocked by the Job Upgrade station on
                the sub.
                """,
            )

    parser.add_argument('--unlock-personal-upgrades',
            action='store_true',
            help="""
                Unlock all avialble personal upgrades from the Personal Upgrade station
                on the sub.  Note that only the upgrades for the currently-unlocked crew
                will be unlocked, and the second upgrade may not be available until the
                necessary sub upgrade has also been acquired.
                """,
            )

    parser.add_argument('--unlock-upgrades',
            action='store_true',
            help="""
                Unlock all upgrades.  This is equivalent to specifying each of the four
                individual `--unlock-*-upgrades` options.  This will also unlock Key Items as
                necessary.  Note that on the main Sub Upgrades console, upgrades you
                haven't "properly" revealed through quest progress won't show up in the list
                on the console, but their effects will still be active.  For personal upgrades,
                only the currently-unlocked crew will have their upgrades enabled.
                """,
            )

    parser.add_argument('--add-key-item',
            action=FlexiSetAction,
            help="""
                Unlock specific Key Items.  These are often tied to ship upgrades, and
                this option will unlock matching upgrades if necessary.  Can be specified
                more than once, and/or separate item names with commas.  Specify `list` or
                `help` to get a list of valid Key Items.
                """,
            )

    parser.add_argument('--remove-key-item',
            action=FlexiSetAction,
            help="""
                Removes specific Key Items.  Will also remove the matching sub upgrades if
                needed.  Note that the `atomic_engine` key item provides both the `dive_02`
                and `geiger_counter_01` upgrades, so removing the Atomic Engine will remove
                both of those upgrades.  Removals are processed after all additions.
                """,
            )

    parser.add_argument('--unlock-key-items',
            action='store_true',
            help="""
                Unlock all Key Items.  These are often tied to ship upgrades, and the game
                should automatically apply the ship upgrade when Key Items are in your
                inventory.
                """,
            )

    parser.add_argument('--unlock-sub-abilities',
            action='store_true',
            help="""
                Unlocks the upgrades and key items necessary to give the sub its full suite
                of abilities (boosting, diving, ram, shield, sonar, and atomic engine).  This also
                ends up unlocking a geiger counter level as a side effect.  This is equivalent
                to using the arguments `--add-upgrade ship_boost_00,dive_00,dive_02,geiger_counter_01,sonar
                --add-key-item keyitem_ship_ram,keyitem_ship_shield`
                """,
            )

    parser.add_argument('--unlock-gears',
            action='store_true',
            help="""
                Unlocks the seven celestial gear upgrades (generally acquired when you
                reach maximum reputation in an area).  Equivalent to using arguments like
                `--add-upgrade celestial_gear_01` for all seven gear numbers.
                """,
            )

    parser.add_argument('--add-hat',
            action=FlexiSetAction,
            help="""
                Unlock specific hats.  Can be specified more than once, and/or
                separate hat names with commas.  Specify `list` or `help` to
                get a list of valid hats.
                """,
            )

    parser.add_argument('--unlock-hats',
            action='store_true',
            help='Unlock all hats',
            )

    parser.add_argument('--add-ship-equipment',
            action=FlexiListAction,
            help="""
                Unlock specific ship equipment.  Can be specified more than once, and/or
                separate ship equipment names with commas.  Specify `list` or `help` to
                get a list of valid ship gear.
                """,
            )

    parser.add_argument('--add-utility',
            action=FlexiListAction,
            help="""
                Unlock specific utility equipment.  Can be specified more than once, and/or
                separate utility equipment names with commas.  Specify `list` or `help` to
                get a list of valid utility gear.
                """,
            )

    parser.add_argument('--add-weapon',
            action=FlexiListAction,
            help="""
                Unlock specific weapons.  Can be specified more than once, and/or
                separate weapon names with commas.  Specify `list` or `help` to
                get a list of valid weapons.
                """,
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

    parser.add_argument('--endgame-pack',
            action='store_true',
            help="""
                Adds a collection of endgame ship equipment, weapons, and equippable utility
                items to your inventory.  This is equivalent to specifying all of the other
                --endgame-*-pack options.
                """,
            )

    parser.add_argument('--no-new-items',
            dest='set_new_item',
            action='store_false',
            help="When adding new items/hats, don't mark them as 'new'",
            )

    map_group = parser.add_mutually_exclusive_group()

    map_group.add_argument('--reveal-map',
            action='store_true',
            help='Fully reveals the world map (removes all clouds)',
            )

    map_group.add_argument('--hide-map',
            action='store_true',
            help='Fully hides the world map (respawns clouds)',
            )

    parser.add_argument('filename',
            type=str,
            nargs=1,
            help='Savefile to open',
            )

    args = parser.parse_args()

    ###
    ### Some basic argument cleanup
    ###

    # Just a single filename
    args.filename = args.filename[0]

    # Normalize the columns arg for print_columns
    if args.single_column:
        columns = 1
    else:
        columns = None

    # --engame-pack is a conglomerate
    if args.endgame_pack:
        args.endgame_ship_pack = True
        args.endgame_weapon_pack = True
        args.endgame_utility_pack = True

    # Check validity of --day arg
    if args.day is not None and args.day < 1:
        parser.error('--day must be at least 1')

    ###
    ### Process additions of key items and unlocks.  There are quite a few
    ### args which end up touching the same vars.  We're going to collapse
    ### all of them down into `add_key_item` and `add_upgrade`, as sets.
    ###
    ### All of this upgrade / key item processing is severely overengineered.
    ### Ah well!
    ###

    # Remember what the user actually asked for.
    user_add_key_item = False
    user_add_upgrade = False
    user_remove_key_item = False
    user_remove_upgrade = False

    # Ensure that our args start out as a set
    if args.add_key_item is None:
        args.add_key_item = set()
    else:
        user_add_key_item = True
    if args.add_upgrade is None:
        args.add_upgrade = set()
    else:
        user_add_upgrade = True

    # Process global/full unlocks for key items
    if args.unlock_key_items:
        args.add_key_item |= set(KEY_ITEMS.keys())
        user_add_key_item = True

    # Process global/full unlocks for upgrades, and also
    # some predefined subsets
    if args.unlock_upgrades:
        args.add_upgrade |= set(UPGRADES.keys())
        user_add_upgrade = True
        args.unlock_personal_upgrades = True
    else:
        for upgrade in UPGRADES.values():
            match upgrade.category:
                case 'main':
                    if args.unlock_main_upgrades:
                        args.add_upgrade.add(upgrade.name)
                        user_add_upgrade = True
                case 'ability':
                    if args.unlock_item_upgrades:
                        args.add_upgrade.add(upgrade.name)
                        user_add_upgrade = True
                case 'guildhall':
                    if args.unlock_job_upgrades:
                        args.add_upgrade.add(upgrade.name)
                        user_add_upgrade = True
                case _:
                    raise RuntimeError('Unknown upgrade category for {upgrade.name}: {upgrade.category}')
            # Unlocking gears, too...
            if args.unlock_gears and upgrade.name.startswith('celestial_gear_'):
                args.add_upgrade.add(upgrade.name)
                user_add_upgrade = True

    # Unlocking sub abilities
    if args.unlock_sub_abilities:
        user_add_upgrade = True
        user_add_key_item = True
        for upgrade in [
                'ship_boost_00',
                'dive_00',
                'sonar',
                # We want dive_02, which is provided by the atomic_engine keyitem.  That
                # same keyitem also provides geiger_counter_01, which IMO we don't really
                # care about, but since we'll get it anyway from the engine, may as well
                # unlock it 'properly' here.
                'dive_02',
                'geiger_counter_01',
                ]:
            if upgrade not in args.add_upgrade:
                args.add_upgrade.add(upgrade)
        # The above upgrades will add in the required keyitems, but there are a couple
        # key items which aren't associated with entries in the upgrade list.  So we're
        # adding those 'by hand,' so to speak.
        for keyitem in [
                'keyitem_ship_ram',
                'keyitem_ship_shield',
                ]:
            if keyitem not in args.add_key_item:
                args.add_key_item.add(keyitem)

    ###
    ### Now we've got args.add_key_item and args.add_upgrade populated based
    ### on user args.  Now we should be able to doublecheck that all of our
    ### passed-in args are valid in terms of the object IDs being used.  This
    ### is all way over-engineered.  Ah well.
    ###

    # First, some definitions for the various things we'll look up
    id_lookups = {
            'job': GameDataLookup('Jobs', JOBS,
                [],
                acceptable_extras={'all', 'current', 'default'},
                ),
            'crew': GameDataLookup('Crew', CREW,
                'unlock_crew',
                acceptable_extras={'all'},
                ),
            'weapon': GameDataLookup('Weapons', WEAPONS,
                'add_weapon',
                ),
            'utility': GameDataLookup('Utilities', UTILITIES,
                'add_utility',
                ),
            'equipment': GameDataLookup('Ship Equipment', SHIP_EQUIPMENT,
                'add_ship_equipment',
                ),
            'key': GameDataLookup('Key Items', KEY_ITEMS,
                [
                    'add_key_item',
                    'remove_key_item',
                    ],
                ),
            'upgrade': GameDataLookup('Upgrades', UPGRADES,
                [
                    'add_upgrade',
                    'remove_upgrade',
                    ],
                ),
            'hat': GameDataLookup('Hats', HATS,
                'add_hat',
                ),
            }

    # Basic arg checking
    if not args.item_info:
        for id_lookup in id_lookups.values():
            id_lookup.check_args(args)

    # Crew Levelling requires some extra fanciness
    if args.crew_level is not None:
        for level_arg in args.crew_level:
            if level_arg == 'list' or level_arg == 'help':
                id_lookups['crew'].needs_dump = True
                id_lookups['job'].needs_dump = True
                break
            parts = level_arg.split(':')
            if len(parts) != 3:
                parser.error('--crew-level argument must contain three parts separated by colons (crew:job:level)')
            crew, job, level = parts
            id_lookups['crew'].check_specific(crew, '--crew-level')
            id_lookups['job'].check_specific(job, '--crew-level')
            if level != 'max':
                try:
                    level = int(level)
                except ValueError as e:
                    parser.error(f'The level component in --crew-level must be `max` or a number from 0 to {XP.max_level}')
                if level < 0 or level > XP.max_level:
                    parser.error(f'The level component in --crew-level must be `max` or a number from 0 to {XP.max_level}')

    # Reserve XP requires some extra fanciness too
    if args.spend_reserve_xp is not None:
        for reserve_arg in args.spend_reserve_xp:
            if reserve_arg == 'list' or reserve_arg == 'help':
                id_lookups['crew'].needs_dump = True
                id_lookups['job'].needs_dump = True
                break
            parts = reserve_arg.split(':')
            if len(parts) != 2:
                parser.error('--spend-reserve-xp argument must contain two parts separated by colons (crew:job)')
            crew, job = parts
            id_lookups['crew'].check_specific(crew, '--spend-reserve-xp')
            id_lookups['job'].check_specific(job, '--spend-reserve-xp')
            # One inconsistency: we do *not* support `all` for the job here
            if job == 'all':
                parser.error('--spend-reserve-xp does not allow `all` for the job component')

    # Now loop through and display whatever needs to be displayed
    did_info_dump = False
    for id_lookup in id_lookups.values():
        did_this_dump = id_lookup.show(force=args.item_info)
        did_info_dump = did_info_dump or did_this_dump
    if did_info_dump:
        return

    ###
    ### Okay, we've got valid args.add_key_item and args.add_upgrade sets.
    ### The next thing to do is process their relative dependencies and add
    ### to the other sets if need be.
    ###

    for upgrade_name in args.add_upgrade:
        upgrade = UPGRADES[upgrade_name]
        if upgrade.keyitem is not None:
            args.add_key_item.add(upgrade.keyitem)
    for key_item_name in args.add_key_item:
        key_item = KEY_ITEMS[key_item_name]
        for upgrade_name in key_item.upgrades:
            args.add_upgrade.add(upgrade_name)

    ###
    ### Okay, now do some pre-processing for our keyitem/upgrade removal args.
    ### No point in adding them in if they're just going to get removed later.
    ### Note that even after "filtering out" removals from our addition sets,
    ### we do still need to test later on to see if they need to be removed
    ### from the savegame in general.
    ###

    if args.remove_key_item is None:
        args.remove_key_item = set()
    else:
        user_remove_key_item = True
    if args.remove_upgrade is None:
        args.remove_upgrade = set()
    else:
        user_remove_upgrade = True

    # Removing upgrade `dive_02` or `geiger_counter_01` would trigger the
    # removal of the `atomic_engine` key item, which would then trigger the
    # removal of the other upgrade, even if it hadn't been explicitly
    # specified.  Given how the data is structured now, we should be okay
    # if we process upgrades first and then key items, so we won't bother to
    # process upgrades more than once.
    for upgrade_name in args.remove_upgrade:
        if upgrade_name in args.add_upgrade:
            args.add_upgrade.remove(upgrade_name)
        upgrade = UPGRADES[upgrade_name]
        if upgrade.keyitem is not None:
            if upgrade.keyitem in args.add_key_item:
                args.add_key_item.remove(upgrade.keyitem)
            args.remove_key_item.add(upgrade.keyitem)
    for key_item_name in args.remove_key_item:
        if key_item_name in args.add_key_item:
            args.add_key_item.remove(key_item_name)
        key_item = KEY_ITEMS[key_item_name]
        for upgrade_name in key_item.upgrades:
            if upgrade_name in args.add_upgrade:
                args.add_upgrade.remove(upgrade_name)
            args.remove_upgrade.add(upgrade_name)

    ###
    ### Okay, back to less involved processing
    ###

    # Load in the savefile
    save = Savefile(args.filename)

    # Now decide what to do.  First up: listing contents!
    if args.list:

        print(f'Savefile Version: {save.version}')
        print('General Game Information:')
        print(f' - Day: {save.imh2.days_elapsed+1}')
        print(f' - Water (money): {save.resources.water}')
        print(f' - Fragments: {save.resources.fragments}')
        print(f'Crew Unlocked: {len(save.header.crew)}')
        crew_report = {}
        for crew in save.crew:
            if crew.name == 'crew_captain_final_boss' or crew.name == 'crew_captain_rearmed_combat':
                continue
            crew_report[CREW[crew.name].label] = crew
        for label, crew in sorted(crew_report.items()):
            print(f' - {label} ({crew.name})')
            job_report = []
            for job in crew.jobs.values():
                if args.verbose:
                    job_report.append('{}: {} ({} XP)'.format(
                        JOBS[job.name].label,
                        job.level,
                        job.xp,
                        ))
                else:
                    job_report.append('{}: {}'.format(
                        JOBS[job.name].label,
                        job.level,
                        ))
            print_columns(
                    job_report,
                    columns=columns,
                    indent='   ',
                    minimum_lines=2,
                    )
            if crew.reserve_xp > 0:
                print(f'   - Reserve XP: {crew.reserve_xp}')
        print(f'Unlocked Sub Upgrades: {len(save.ship.upgrades)}/{len(UPGRADES)}')
        if args.verbose:
            upgrade_mapping = {
                    'main' : 'Main',
                    'ability': 'Item',
                    'guildhall': 'Job',
                    }
            categorized = {
                    'Main': [],
                    'Item': [],
                    'Job': [],
                    }
            for upgrade_str in save.ship.upgrades:
                # Not doing a more thorough check to see if we've got a valid
                # category since that's already been done with verifying the
                # gamedata generation.
                categorized[upgrade_mapping[UPGRADES[upgrade_str].category]].append(upgrade_str)
            for category, upgrades in categorized.items():
                if len(upgrades) > 0:
                    print(f' - {category} ({len(upgrades)}):')
                    print_columns(
                            sorted(upgrades),
                            columns=columns,
                            lookup=UPGRADES,
                            lookup_sort=True,
                            indent='   ',
                            )
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
                    print_columns(
                            sorted(items),
                            columns=columns,
                            lookup=lookups[category],
                            lookup_sort=True,
                            indent='   ',
                            )
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
                start = save.remaining.start_pos + (line*per_line)
                print('0x{:08X}  '.format(start), end='')
                for (idx, byte) in enumerate(save.data[start:start+per_line]):
                    print('{:02X}'.format(byte), end='')
                    print(' ', end='')
                    if idx % 4 == 3:
                        print(' ', end='')
                print('| ', end='')
                for byte in save.data[start:start+per_line]:
                    if byte in printable_chars:
                        print(chr(byte), end='')
                    else:
                        print('.', end='')
                print('')

    # Doing a JSON dump
    elif args.json is not None:

        if not args.force and os.path.exists(args.json):
            print(f'WARNING: {args.json} already exists.')
            response = input('Overwrite (y/N)? ').strip().lower()
            if response == '' or response[0] != 'y':
                print('Exiting!')
                print('')
                return
            print('')

        with open(args.json, 'w') as odf:
            json.dump(
                    save.to_json(args.verbose),
                    odf,
                    indent=2,
                    )
        print('')
        print(f'Wrote to: {args.json}')
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

        # Current Day
        if args.day is not None:
            if save.imh2.days_elapsed == args.day - 1:
                print(f' - Skipping setting the day; already set to {args.day}')
            else:
                print(f' - Setting current day to: {args.day}')
                save.imh2.days_elapsed = args.day - 1
                do_save = True


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

        # Unlock Crew
        if args.unlock_crew is not None:
            warn_about_already_existing = True
            if 'all' in args.unlock_crew:
                warn_about_already_existing = False
                args.unlock_crew = set(CREW_REAL.keys())
            else:
                # Normalize to the 'real' names
                new_unlock = set()
                for crew_name in args.unlock_crew:
                    crew_info = CREW[crew_name]
                    new_unlock.add(crew_info.name)
                args.unlock_crew = new_unlock

            # Figure out the current max level for current chars, which is
            # what we'll use for the new char
            max_level = 0
            for crew_name in save.crew_list:
                crew = save.crew[crew_name]
                for job in crew.jobs.values():
                    max_level = max(max_level, job.level)

            # Loop through and unlock!
            existing_crew_names = set(save.crew_list)
            for crew_name in sorted(args.unlock_crew):
                crew_info = CREW[crew_name]
                if crew_info.name in existing_crew_names:
                    if warn_about_already_existing:
                        print(f'- {crew_info.label} is already unlocked, skipping')
                    continue
                print(f'- Unlocking crew member: {crew_info.label}')
                save.unlock_crew(crew_info.name, max_level, flag_as_new=args.set_new_item)
                do_save = True

        # Crew Level.  Args should be validated by now
        if args.crew_level is not None:
            for level_arg in args.crew_level:
                crew_name, job_name, level = level_arg.split(':')

                # Get the level to set
                if level == 'max':
                    level = XP.max_level
                else:
                    level = int(level)

                # Get the crew we're acting on
                report_not_found = True
                if crew_name == 'all':
                    crew_names = save.crew_list
                    report_not_found = False
                else:
                    crew_names = [crew_name]

                # Loop through crew
                for crew_name in crew_names:
                    crew_info = CREW[crew_name]
                    if crew_info.name not in save.crew:
                        if report_not_found:
                            print(f'- {CREW[crew_name].label} has not been unlocked, not setting level')
                        continue
                    crew = save.crew[crew_info.name]
                    if job_name == 'all':
                        if args.allow_downlevel:
                            print(f'- {crew_info.label}: Setting all jobs to level {level} (allowing downlevelling)')
                        else:
                            print(f'- {crew_info.label}: Upgrading all jobs to level {level}')
                        crew.all_jobs_level_to(level, allow_downlevel=args.allow_downlevel)
                        do_save = True
                    else:
                        if job_name == 'default':
                            job_info = CREW[crew.name].default_job
                        elif job_name == 'current':
                            if crew_name in save.inventory.loadouts:
                                cur_weapon = save.inventory.loadouts[crew.name].cur_weapon
                                if cur_weapon == 0:
                                    # No weapon equipped; current job is the default
                                    job_info = CREW[crew_name].default_job
                                else:
                                    if type(cur_weapon) == int:
                                        raise RuntimeError(f"ERROR: {crew_info.label}'s current weapon (ID {cur_weapon}) was not found in savefile")
                                    if cur_weapon.name not in WEAPONS:
                                        raise RuntimeError(f"ERROR: {crew_info.label}'s current weapon ({cur_weapon}) was not found in gamedata")
                                    job_info = WEAPONS[cur_weapon.name].job
                            else:
                                # No loadout?  I guess current job is the default
                                job_info = CREW[crew_name].default_job
                        else:
                            job_info = JOBS[job_name]
                        do_set = True
                        if job_info.name in crew.jobs:
                            job_status = crew.jobs[job_info.name]
                            if job_status.level == level:
                                print(f"- {crew_info.label}'s {job_info.label} level is already {level}, skipping")
                                do_set = False
                            elif job_status.level > level and not args.allow_downlevel:
                                print(f"- {crew_info.label}'s {job_info.label} level is already {job_status.level}, skipping")
                                do_set = False
                        elif level == 0:
                            print(f"- {crew_info.label}'s {job_info.label} level is already 0, skipping")
                            do_set = False
                        if do_set:
                            if args.allow_downlevel:
                                print(f'- {crew_info.label}: Setting {job_info.label} to level {level} (allowing downlevelling)')
                            else:
                                print(f'- {crew_info.label}: Upgrading {job_info.label} to level {level}')
                            crew.job_level_to(job_info.name, level, allow_downlevel=args.allow_downlevel)
                            do_save = True

        # Reserve XP.  Args should be validated by now
        if args.spend_reserve_xp is not None:
            for reserve_arg in args.spend_reserve_xp:
                crew_name, job_name = reserve_arg.split(':')

                # Get the crew we're acting on
                report_not_found = True
                if crew_name == 'all':
                    crew_names = save.crew_list
                    report_not_found = False
                else:
                    crew_names = [crew_name]

                # Loop through crew
                for crew_name in crew_names:
                    crew_info = CREW[crew_name]
                    if crew_info.name not in save.crew:
                        if report_not_found:
                            print(f'- {CREW[crew_name].label} has not been unlocked, not setting level')
                        continue
                    crew = save.crew[crew_info.name]

                    if crew.reserve_xp == 0:
                        print(f"- {crew_info.label} has no Reserve XP, skipping")
                        continue

                    if job_name == 'default':
                        job_info = CREW[crew.name].default_job
                    elif job_name == 'current':
                        if crew_name in save.inventory.loadouts:
                            cur_weapon = save.inventory.loadouts[crew.name].cur_weapon
                            if cur_weapon == 0:
                                # No weapon equipped; current job is the default
                                job_info = CREW[crew_name].default_job
                            else:
                                if type(cur_weapon) == int:
                                    raise RuntimeError(f"ERROR: {crew_info.label}'s current weapon (ID {cur_weapon}) was not found in savefile")
                                if cur_weapon.name not in WEAPONS:
                                    raise RuntimeError(f"ERROR: {crew_info.label}'s current weapon ({cur_weapon}) was not found in gamedata")
                                job_info = WEAPONS[cur_weapon.name].job
                        else:
                            # No loadout?  I guess current job is the default
                            job_info = CREW[crew_name].default_job
                    else:
                        job_info = JOBS[job_name]

                    do_set = True
                    cur_job_xp = 0
                    if job_info.name in crew.jobs:
                        job_status = crew.jobs[job_info.name]
                        if job_status.xp >= XP.max_xp:
                            print(f"- {crew_info.label}'s {job_info.label} skill is already at max level, skipping")
                            do_set = False
                        cur_job_xp = job_status.xp
                        cur_job_level = job_status.level
                    target_xp = cur_job_xp + crew.reserve_xp
                    if target_xp > XP.max_xp:
                        remaining_reserve_xp = target_xp - XP.max_xp
                        target_xp = XP.max_xp
                        spending_xp = crew.reserve_xp - remaining_reserve_xp
                    else:
                        remaining_reserve_xp = 0
                        spending_xp = crew.reserve_xp
                    target_level = 0
                    for level in range(0, XP.max_level+1):
                        if target_xp >= XP.level_to_xp[level]:
                            target_level = level

                    if do_set:
                        report_parts = []
                        report_parts.append(f'Spending {spending_xp} Reserve XP on {job_info.label}')
                        if remaining_reserve_xp > 0:
                            report_parts.append(f' ({remaining_reserve_xp} Reserve XP remains)')
                        report_parts.append(f', to XP {target_xp}')
                        if target_level == cur_job_level:
                            report_parts.append(' (level unchanged)')
                        else:
                            report_parts.append(f' (level {cur_job_level} -> {target_level})')
                        report = ''.join(report_parts)

                        print(f'- {crew_info.label}: {report}')
                        crew.set_job_xp(job_info.name, target_xp)
                        crew.reserve_xp = remaining_reserve_xp
                        do_save = True

        # Refresh Crew
        if args.refresh_crew:
            did_refresh = False
            print('- Refreshing all crew and equipment')
            for item in save.inventory.items:
                if item.used == 1:
                    item.used = 0
                    did_refresh = True
            for loadout in save.inventory.loadouts.values():
                if loadout.used == 1:
                    loadout.used = 0
                    did_refresh = True
            if len(save.used_crew) > 0:
                save.used_crew = []
                did_refresh = True
            if did_refresh:
                do_save = True
            else:
                print('  - No crew/equipment needed refreshing!')

        # Personal Upgrades
        if args.unlock_personal_upgrades:
            print('- Unlocking all available personal upgrades')
            did_upgrade = False
            for crew_name in save.crew_list:
                crew = save.crew[crew_name]
                if crew.personal_upgrade_count < 2:
                    crew.personal_upgrade_count = 2
                    did_upgrade = True
            if did_upgrade:
                do_save = True
            else:
                print('  - All available personal upgrades were already unlocked!')

        # New upgrades.  Note that all our keyitem mappings have already been computed
        if args.add_upgrade:
            needed_upgrades = args.add_upgrade - set(save.ship.upgrades)
            if len(needed_upgrades) == 0:
                if user_add_upgrade:
                    print('- Skipping upgrade unlocks; all requested upgrades are already unlocked')
            else:
                print(f'- Unlocking {len(needed_upgrades)} upgrades')
                if args.verbose:
                    print_columns(
                            needed_upgrades,
                            columns=columns,
                            lookup=UPGRADES,
                            lookup_sort=True,
                            )
                save.ship.upgrades.extend(sorted(needed_upgrades))
                do_save = True
        elif user_add_upgrade:
            print('- Skipping upgrade unlocks due to other removals requested')

        # Removed upgrades
        if args.remove_upgrade:
            declined_upgrades = args.remove_upgrade & set(save.ship.upgrades)
            if len(declined_upgrades) == 0:
                if user_remove_upgrade:
                    print('- Skipping upgrade removals; all requested removals are already not present')
            else:
                print(f'- Removing {len(declined_upgrades)} upgrades')
                if args.verbose:
                    print_columns(
                            declined_upgrades,
                            columns=columns,
                            lookup=UPGRADES,
                            lookup_sort=True,
                            )
                for upgrade_name in declined_upgrades:
                    save.ship.upgrades.remove(upgrade_name)
                do_save = True

        # New Key Items.  Note that all our upgrade mappings have already been computed
        if args.add_key_item:
            needed_keyitems = args.add_key_item - set([i.name for i in save.inventory.items])
            if len(needed_keyitems) == 0:
                if user_add_key_item:
                    print('- Skipping Key Item unlocks; all requested Key Items are already unlocked')
            else:
                print(f'- Unlocking {len(needed_keyitems)} Key Items')
                if args.verbose:
                    print_columns(
                            needed_keyitems,
                            columns=columns,
                            lookup=KEY_ITEMS,
                            lookup_sort=True,
                            )
                for item in sorted(needed_keyitems):
                    save.inventory.add_item(item, InventoryItem.ItemFlag.KEYITEM, flag_as_new=args.set_new_item)
                do_save = True
        elif user_add_key_item:
            print('- Skipping Key Item unlocks due to other removals requested')

        # Removed Key Items
        if args.remove_key_item:
            declined_items = args.remove_key_item & set([i.name for i in save.inventory.items])
            if len(declined_items) == 0:
                if user_remove_key_item:
                    print('- Skipping Key Item removals; all requested removals are already not present')
            else:
                print(f'- Removing {len(declined_items)} Key Items')
                if args.verbose:
                    print_columns(
                            declined_items,
                            columns=columns,
                            lookup=KEY_ITEMS,
                            lookup_sort=True,
                            )
                to_remove_indexes = []
                for idx, item in enumerate(save.inventory.items):
                    if item.name in declined_items:
                        to_remove_indexes.append(idx)
                for idx in sorted(to_remove_indexes, reverse=True):
                    del save.inventory.items[idx]
                do_save = True

        # Hats!
        if args.unlock_hats or args.add_hat:
            if args.unlock_hats:
                requested_hats = HATS.keys()
            else:
                requested_hats = args.add_hat
            needed_hats = set(requested_hats) - set(save.inventory.hats)
            if len(needed_hats) == 0:
                print(f'- Skipping hat unlocks; all requested hats are already unlocked')
            else:
                print(f'- Unlocking {len(needed_hats)} hats')
                save.inventory.hats.extend(sorted(needed_hats))
                if args.set_new_item:
                    save.inventory.new_hats.extend(sorted(needed_hats))
                do_save = True

        # A cluster of inventory args which are all handled in the same way
        for label, flag, arg in [
                ('ship equipment', InventoryItem.ItemFlag.SHIP_EQUIPMENT, args.add_ship_equipment),
                ('utility equipment', InventoryItem.ItemFlag.UTILITY, args.add_utility),
                ('weapons', InventoryItem.ItemFlag.WEAPON, args.add_weapon),
                ]:
            if arg:
                print(f'- Adding {len(arg)} {label} to inventory')
                for item in arg:
                    save.inventory.add_item(item, flag, flag_as_new=args.set_new_item)
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
                save.inventory.add_item(item, InventoryItem.ItemFlag.SHIP_EQUIPMENT, flag_as_new=args.set_new_item)
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
                save.inventory.add_item(item, InventoryItem.ItemFlag.WEAPON, flag_as_new=args.set_new_item)
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
                save.inventory.add_item(item, InventoryItem.ItemFlag.UTILITY, flag_as_new=args.set_new_item)
            do_save = True

        # Reveal map
        if args.reveal_map:
            if save.world_data:
                print('- Fully revealing world map')
                save.world_data.reveal()
                do_save = True
            else:
                print('- NOTICE: This savegame has not populated any world data yet, so no')
                print('  map reveal is being performed.  Make sure the save has visited')
                print('  the world map at least once.')

        # Hide map
        if args.hide_map:
            if save.world_data:
                print('- Fully hiding world map')
                save.world_data.hide()
                do_save = True
            else:
                print('- NOTICE: This savegame has not populated any world data yet, so no')
                print('  map hiding is being performed.  Make sure the save has visited')
                print('  the world map at least once.')

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

