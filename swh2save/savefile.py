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
import re
import abc
import enum
import binascii

from .datafile import Datafile, StringStorage
from .gamedata import CREW, XP, JOBS


class InMissionSavegameException(Exception):
    """
    An exception to throw when we detect that the savefile might have been
    saved while inside a mission, so we can fail more gracefully when
    that happens.  (Since I really don't want to try and parse in-mission
    data.)
    """


class Serializable:
    """
    An object that we want to be able to JSONify.  Note that despite
    the function names, these functions themselves don't actually do
    any JSON; we're basically just turning ourselves into a dict.
    """


    def to_json(self, verbose=False, initial_dict=None):
        """
        The main entry point.
        """
        if initial_dict is None:
            initial_dict = {}
        initial_dict |= self._to_json(verbose)
        return initial_dict


    @abc.abstractmethod
    def _to_json(self, verbose=False):
        """
        This method needs to be implemented in the implementing class,
        to actually do the serialization.
        """
        return {}


    def _json_simple(self, target_dict, attrs):
        """
        Helper method to loop over a bunch of attribute strings and
        add in their raw values to our serialization.
        """
        for attr in attrs:
            target_dict[attr] = getattr(self, attr)


    def _json_object_single(self, target_dict, attrs, verbose=False):
        """
        Helper method to loop over a bunch of attribute strings,
        interpreting them as a single instance of a Serializable object.
        """
        for attr in attrs:
            target_dict[attr] = getattr(self, attr).to_json(verbose)


    def _json_object_arr(self, target_dict, attrs, verbose=False):
        """
        Helper method to loop over a bunch of attribute strings,
        interpreting them as an array of Serializable objects.
        """
        for attr in attrs:
            target_dict[attr] = []
            for element in getattr(self, attr):
                target_dict[attr].append(element.to_json(verbose))


class Chunk(Serializable):
    """
    A chunk that we're wrapping with an object.
    """

    def __init__(self, df, check_header):
        self.df = df
        self.header = self.df.read_chunk_header()
        if self.header != check_header:
            raise RuntimeError(f'Expected chunk header "{check_header}" but got "{self.header}"')


    def write_to(self, odf):
        odf.write_chunk_header(self.header)
        self._write_to(odf)


    @abc.abstractmethod
    def _write_to(self, odf):
        return


    def to_json(self, verbose=False):
        """
        We want our basic serialization to include the chunk name/header.
        """
        return super().to_json(
                verbose=verbose,
                initial_dict={'chunk': self.header},
                )


class Difficulty(Chunk):
    """
    `Difc` chunk which holds info about the configured game difficulty
    """

    def __init__(self, df):
        super().__init__(df, 'Difc')

        self.unknown = df.read_uint8()
        self.settings = []
        for _ in range(8):
            self.settings.append(df.read_uint32())


    def _write_to(self, odf):

        odf.write_uint8(self.unknown)
        for setting in self.settings:
            odf.write_uint32(setting)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown',
            'settings',
            ])
        return my_dict


class Imh2(Chunk):
    """
    `imh2` chunk.  Presumably some mission state stuff...
    """

    def __init__(self, df):
        super().__init__(df, 'imh2')

        self.unknown_start = df.read_uint8()
        
        self.cur_outset = df.read_string()

        self.unknown_1 = df.read_uint32()
        self.unknown_2 = df.read_uint32()

        # For Day 1, this will be set to 0, etc...
        self.days_elapsed = df.read_uint32()

        self.small_unknown_1 = df.read_uint8()
        self.small_unknown_2 = df.read_uint8()
        self.small_unknown_3 = df.read_uint8()
        self.small_unknown_4 = df.read_uint8()
        self.small_unknown_5 = df.read_uint8()

        self.cur_campaign_state = df.read_string()

        self.small_unknown_6 = df.read_uint8()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_start)
        odf.write_string(self.cur_outset)
        odf.write_uint32(self.unknown_1)
        odf.write_uint32(self.unknown_2)
        odf.write_uint32(self.days_elapsed)
        odf.write_uint8(self.small_unknown_1)
        odf.write_uint8(self.small_unknown_2)
        odf.write_uint8(self.small_unknown_3)
        odf.write_uint8(self.small_unknown_4)
        odf.write_uint8(self.small_unknown_5)
        odf.write_string(self.cur_campaign_state)
        odf.write_uint8(self.small_unknown_6)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_start',
            'cur_outset',
            'unknown_1',
            'unknown_2',
            'days_elapsed',
            'small_unknown_1',
            'small_unknown_2',
            'small_unknown_3',
            'small_unknown_4',
            'small_unknown_5',
            'cur_campaign_state',
            'small_unknown_6',
            ])
        return my_dict


class GameResources(Chunk):
    """
    `GaRe` chunk: game resources
    """

    def __init__(self, df):
        super().__init__(df, 'GaRe')

        self.unknown = df.read_uint8()

        self.fragments = df.read_uint32()
        self.water = df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown)
        odf.write_uint32(self.fragments)
        odf.write_uint32(self.water)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown',
            'fragments',
            'water',
            ])
        return my_dict


class Ship(Chunk):
    """
    `Ship` chunk: ship status
    """

    def __init__(self, df):
        super().__init__(df, 'Ship')

        self.unknown = df.read_uint8()

        # Ship Equipment
        self.equipped = []
        num_equipped = df.read_uint8()
        for _ in range(num_equipped):
            self.equipped.append(df.read_string())

        # Next up, item IDs for each of the equipped items.  These relate
        # to the item IDs in our inventory (to know which one in particular
        # is equipped), but we haven't read the inventory at this point.
        # So we'll just leave them as IDs.
        self.item_ids = []
        num_item_ids = df.read_uint8()
        for _ in range(num_item_ids):
            self.item_ids.append(df.read_varint())

        # And now, also apparently related to the equipped items, what has for
        # me always been a series of increasing uint32s (starting at 0, so:
        # 0, 1, 2, ..., N-1).
        self.item_sequences = []
        num_item_sequences = df.read_uint8()
        for _ in range(num_item_sequences):
            self.item_sequences.append(df.read_uint32())

        # On to something which seems simpler (at least on the surface): upgrades
        self.upgrades = []
        num_upgrades = df.read_uint8()
        for _ in range(num_upgrades):
            self.upgrades.append(df.read_string())

        # 14 bytes of unknown data.  No clue if this is actually ship-related,
        # or part of an enclosing chunk.  Pure guesses as to structure here!
        self.unknown_b1 = df.read_uint8()
        self.unknown_b2 = df.read_uint8()
        self.unknown_b3 = df.read_uint8()
        self.unknown_b4 = df.read_uint8()
        self.unknown_i1 = df.read_uint32()
        self.unknown_i2 = df.read_uint32()
        self.unknown_s1 = df.read_uint16()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown)

        # Equipped items
        odf.write_uint8(len(self.equipped))
        for equipment in self.equipped:
            odf.write_string(equipment)

        # Item IDs?
        odf.write_uint8(len(self.item_ids))
        for item_id in self.item_ids:
            odf.write_varint(item_id)

        # Item sequences
        odf.write_uint8(len(self.item_sequences))
        for item_sequence in self.item_sequences:
            odf.write_uint32(item_sequence)

        # Upgrades
        odf.write_uint8(len(self.upgrades))
        for upgrade in self.upgrades:
            odf.write_string(upgrade)

        # Unknown data
        odf.write_uint8(self.unknown_b1)
        odf.write_uint8(self.unknown_b2)
        odf.write_uint8(self.unknown_b3)
        odf.write_uint8(self.unknown_b4)
        odf.write_uint32(self.unknown_i1)
        odf.write_uint32(self.unknown_i2)
        odf.write_uint16(self.unknown_s1)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown',
            'equipped',
            'item_ids',
            'item_sequences',
            'upgrades',
            'unknown_b1',
            'unknown_b2',
            'unknown_b3',
            'unknown_b4',
            'unknown_i1',
            'unknown_i2',
            'unknown_s1',
            ])
        return my_dict


class Header(Chunk):
    """
    `Head` chunk; the main save header.
    """

    def __init__(self, df):
        super().__init__(df, 'Head')

        # Basically have no clue what any of this is
        self.zero_1 = df.read_uint8()
        self.unknown_1 = df.read_uint32()
        self.zero_2 = df.read_uint32()
        self.unknown_2 = df.read_uint32()
        # Seven bytes remain at this point.  The last few seem to maybe
        # be a counter of some sort (time elapsed?  though I've not yet seen
        # how that would be interpreted), so I'm grouping those together.
        self.unknown_3 = df.read_uint8()
        self.unknown_4 = df.read_uint8()
        self.unknown_5 = df.read_uint8()
        self.unknown_6 = df.read_uint32()

        # Two difficulty chunks; not sure what's up with that.
        self.difficulties = []
        self.difficulties.append(Difficulty(df))
        self.difficulties.append(Difficulty(df))

        # Some easier-to-interpret data
        self.cur_location = df.read_string()
        self.cur_region = df.read_string()
        self.cur_quest = df.read_string()

        # Note: merely adding a new crew string to this list does *not* properly
        # unlock crew in the game.
        self.crew = []
        # Not sure yet if this is a "standard" string list, so not abstracting it.
        num_crew = df.read_uint8()
        for _ in range(num_crew):
            self.crew.append(df.read_string())


    def _write_to(self, odf):

        odf.write_uint8(self.zero_1)
        odf.write_uint32(self.unknown_1)
        odf.write_uint32(self.zero_2)
        odf.write_uint32(self.unknown_2)
        odf.write_uint8(self.unknown_3)
        odf.write_uint8(self.unknown_4)
        odf.write_uint8(self.unknown_5)
        odf.write_uint32(self.unknown_6)

        # Two difficulty chunks; not sure what's up with that.
        self.difficulties[0].write_to(odf)
        self.difficulties[1].write_to(odf)

        # Some easier-to-interpret data
        odf.write_string(self.cur_location)
        odf.write_string(self.cur_region)
        odf.write_string(self.cur_quest)
        odf.write_uint8(len(self.crew))
        for bot in self.crew:
            odf.write_string(bot)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero_1',
            'unknown_1',
            'zero_2',
            'unknown_2',
            'unknown_3',
            'unknown_4',
            'unknown_5',
            'unknown_6',
            ])
        self._json_object_arr(my_dict, [
            'difficulties',
            ], verbose)
        self._json_simple(my_dict, [
            'cur_location',
            'cur_region',
            'cur_quest',
            'crew',
            ])
        return my_dict


class InventoryItem(Chunk):
    """
    `ItIn` chunk -- A single inventory item.
    (Or "Item Inventory" as the four-letter code would imply. :)
    """


    class ItemFlag(enum.Enum):
        """
        Flags used in the item chunk.  So far I've only ever seen these
        four.  Given the values, it seems like this is maybe intended
        to be a bitfield, but I've never actually seen them mixed.
        """
        WEAPON = 0x01
        UTILITY = 0x02
        SHIP_EQUIPMENT = 0x04
        KEYITEM = 0x08


    def __init__(self, df):
        super().__init__(df, 'ItIn')

        # Seems to always be 0
        self.unknown_1 = self.df.read_uint8()

        # Item ID (see Inventory for where the last-ID-used is stored)
        self.id = self.df.read_varint()

        # See the ItemFlag enum
        self.flags = self.df.read_uint32()

        # The name
        self.name = self.df.read_string()

        # This basically always appear to be 0
        self.unknown_4 = self.df.read_uint32()

        # Used in the past day
        self.used = self.df.read_uint32()
        #print(f'{self.unknown_1} {self.id} {self.flags} {self.name} {self.unknown_4} {self.unknown_5}')


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_1)
        odf.write_varint(self.id)
        odf.write_uint32(self.flags)
        odf.write_string(self.name)
        odf.write_uint32(self.unknown_4)
        odf.write_uint32(self.used)


    def __str__(self):
        return str(self.name)


    def __lt__(self, other):
        if type(other) == str:
            return self.name.casefold() < other.casefold()
        else:
            return self.name.casefold() < other.name.casefold()


    def __gt__(self, other):
        if type(other) == str:
            return self.name.casefold() > other.casefold()
        else:
            return self.name.casefold() > other.name.casefold()


    @staticmethod
    def create_new(item_id, item_name, item_flags):
        """
        Creates a new item with the given ID and name.  The way this is done at
        the moment is absurd; need to rethink how I'm instantiating these
        things.
        """
        # TODO: seriously, this is absurd and weird.
        odf = Savefile('foo', do_write=True)
        odf.write_chunk_header('ItIn')
        odf.write_uint8(0)
        odf.write_varint(item_id)
        if type(item_flags) == InventoryItem.ItemFlag:
            odf.write_uint32(item_flags.value)
        else:
            odf.write_uint32(item_flags)
        odf.write_string(item_name)
        odf.write_uint32(0)
        odf.write_uint32(0)
        odf.seek(0)
        return InventoryItem(odf)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_1',
            'id',
            'flags',
            'name',
            'unknown_4',
            'used',
            ])
        return my_dict


class Loadout(Chunk):
    """
    `CrLo` chunk -- Character Loadout, I guess
    """

    def __init__(self, df, items_by_id):
        super().__init__(df, 'CrLo')
        self.items_by_id = items_by_id

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        self.name = self.df.read_string()
        self.cur_weapon = self._get_inventory_item_or_id()

        # In all my saves, this value seems to always be 3
        self.unknown = self.df.read_varint()

        self.utility_1 = self._get_inventory_item_or_id()
        self.utility_2 = self._get_inventory_item_or_id()
        self.utility_3 = self._get_inventory_item_or_id()
        self.cur_hat = self.df.read_string()

        # 0 for available, 1 for "used in a mission today"
        self.used = self.df.read_uint32()

        #print(f'{self.zero} {self.name} | {self.unknown_3} | {self.used}')


    def _get_inventory_item_or_id(self):
        """
        Reads a varint and attempts to return the matching inventory item
        based on ID.  Will just return the number if not found (as will
        happen for values of zero, for instance).  Theoretically any nonzero
        value we find here should exist in inventory, but whatever.
        """
        item_id = self.df.read_varint()
        if item_id in self.items_by_id:
            return self.items_by_id[item_id]
        else:
            return item_id


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_string(self.name)
        self._write_inventory_item(self.cur_weapon, odf)
        odf.write_varint(self.unknown)
        self._write_inventory_item(self.utility_1, odf)
        self._write_inventory_item(self.utility_2, odf)
        self._write_inventory_item(self.utility_3, odf)
        odf.write_string(self.cur_hat)
        odf.write_uint32(self.used)


    def _write_inventory_item(self, value, odf):
        """
        Given an inventory var, write out the item ID whether it's a number
        or an InventoryItem object
        """
        if type(value) == InventoryItem:
            odf.write_varint(value.id)
        else:
            odf.write_varint(value)


    def _to_json_item(self, value):
        if type(value) == InventoryItem:
            return value.id
        else:
            return value


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'name',
            ])
        my_dict['cur_weapon'] = self._to_json_item(self.cur_weapon)
        my_dict['unknown'] = self.unknown
        my_dict['utility_1'] = self._to_json_item(self.utility_1)
        my_dict['utility_2'] = self._to_json_item(self.utility_2)
        my_dict['utility_3'] = self._to_json_item(self.utility_3)
        self._json_simple(my_dict, [
            'cur_hat',
            'used',
            ])
        return my_dict


    @staticmethod
    def create_new(name, items_by_id):
        """
        Creates a new loadout with just the name filled in.  You'll have to
        fill in the remaining fields after creation.  The way this is
        done at the moment is absurd.
        """
        # TODO: seriously, this is absurd and weird.
        odf = Savefile('foo', do_write=True)
        odf.write_chunk_header('CrLo')
        odf.write_uint8(0)
        odf.write_string(name)
        odf.write_string(None)
        odf.write_varint(3)
        odf.write_string(None)
        odf.write_string(None)
        odf.write_string(None)
        odf.write_string(None)
        odf.write_uint32(0)
        odf.seek(0)
        return Loadout(odf, items_by_id)


class Inventory(Chunk):
    """
    `Inve` chunk -- Inventory!
    """

    def __init__(self, df):
        super().__init__(df, 'Inve')

        self.unknown_1 = self.df.read_uint8()

        # Goes up with each item you acquire.  New items will increment this by 1
        # and use that as the ID
        self.last_inventory_id = self.df.read_uint32()

        # On to the inventory...
        self.items = []
        self.items_by_id = {}
        num_items = self.df.read_varint()
        for _ in range(num_items):
            new_item = InventoryItem(self.df)
            self.items.append(new_item)
            self.items_by_id[new_item.id] = new_item
            #print(f' - Got item: {self.items[-1]} ({len(self.items)}/{num_items})')

        # A list of "new" items (based on ID)
        self.new_items = []
        num_new_items = self.df.read_varint()
        for _ in range(num_new_items):
            self.new_items.append(self.df.read_varint())

        # Another unknown varint array.  I thought this might be related to ordering,
        # based on item ID, but that didn't seem to line up at all.
        self.unknown_arr_2 = []
        num_unknown_arr_2 = self.df.read_varint()
        for _ in range(num_unknown_arr_2):
            self.unknown_arr_2.append(self.df.read_varint())
            #print(f' - Got unknown_2: {self.unknown_arr_2[-1]} ({len(self.unknown_arr_2)}/{num_unknown_arr_2})')

        # Hats!
        self.hats = []
        num_hats = self.df.read_varint()
        for _ in range(num_hats):
            self.hats.append(self.df.read_string())
            #print(f' - Got hat: {self.hats[-1]} ({len(self.hats)}/{num_hats})')

        # New hats
        self.new_hats = []
        num_new_hats = self.df.read_varint()
        for _ in range(num_new_hats):
            self.new_hats.append(self.df.read_string())

        # Captain Leeway's hat
        self.leeway_hat = self.df.read_string()

        # Character Loadouts
        self.loadouts = {}
        num_chars = self.df.read_uint8()
        for _ in range(num_chars):
            loadout = Loadout(self.df, self.items_by_id)
            self.loadouts[loadout.name] = loadout


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_1)

        odf.write_uint32(self.last_inventory_id)

        # Items
        odf.write_varint(len(self.items))
        for item in self.items:
            item.write_to(odf)

        # "New" Items
        odf.write_varint(len(self.new_items))
        for item in self.new_items:
            odf.write_varint(item)

        # Second unknown array
        odf.write_varint(len(self.unknown_arr_2))
        for unknown in self.unknown_arr_2:
            odf.write_varint(unknown)

        # Hats
        odf.write_varint(len(self.hats))
        for hat in self.hats:
            odf.write_string(hat)

        # New Hats
        odf.write_varint(len(self.new_hats))
        for new_hat in self.new_hats:
            odf.write_string(new_hat)

        # Leeway's Hat
        odf.write_string(self.leeway_hat)

        # Character Loadout
        odf.write_uint8(len(self.loadouts))
        for loadout in self.loadouts.values():
            loadout.write_to(odf)


    def add_item(self, item_name, item_flags, flag_as_new=True):
        """
        Adds a new item with the given name to our inventory
        """
        self.last_inventory_id += 1
        self.items.append(InventoryItem.create_new(self.last_inventory_id, item_name, item_flags))
        if flag_as_new:
            self.new_items.append(self.last_inventory_id)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_1',
            'last_inventory_id',
            ])
        self._json_object_arr(my_dict, [
            'items',
            ], verbose)
        self._json_simple(my_dict, [
            'new_items',
            'unknown_arr_2',
            'hats',
            'new_hats',
            'leeway_hat',
            ])
        my_dict['loadouts'] = list([l.to_json() for l in self.loadouts.values()])
        return my_dict


class ReDe(Chunk):
    """
    `ReDe` chunk.

    I suspect this chunk is storing the state of a "deque", which the game
    interally spells "Deck."  The chunk name might mean "Resource Deck/Deque"
    or somesuch?  My original thought was that it was a list of things that
    are "ready" ("ReDe") to go, or "on deck" to be acquired, or something.  Its
    first use in the file is a ReDe chunk which seems to contain a list of
    characters you haven't recruited yet (so they'd be ready to recruit).
    Then a bit later on, there's a structure detailing some loot groups.  For
    instance, from some debug output there:

         - Deck 3: deck_utility_and_rare
            - ReDe:
               0. combat_utility
               1. combat_rare
               2. combat_utility
               3. combat_utility
         - Deck 4: deck_resources
            - ReDe:
               0. combat_fragments
               1. combat_money
               2. combat_money
               3. combat_money
               4. combat_money
               5. combat_money
               6. combat_fragments

    So yeah, not totally sure, but the deck/deque relationship feels solid
    to me.
    """

    def __init__(self, df):
        super().__init__(df, 'ReDe')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # When the game uses this struct, it's *usually* for loot pools
        # and such, though it also seems to be used to store which crew
        # members are available at bars.  I'm just calling the var
        # `items` for simplicity's sake, though.
        self.items = []
        num_items = self.df.read_varint()
        for _ in range(num_items):
            self.items.append(self.df.read_string())

        # On my saves, ranges from 0-4.  Bigger values in general when
        # there are more things in the list, though that's not
        # entirely predictive.  I think it might have something to do with
        # how many things can *possibly* be in the current pool, though
        # eh...
        self.unknown = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.items))
        for thing in self.items:
            odf.write_string(thing)
        odf.write_uint32(self.unknown)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'items',
            'unknown',
            ])
        return my_dict


class LootTableDeck(Chunk):
    """
    `LTde` chunk.  A single "deck" inside a Loot Table entry.  See the LTma
    docstring for some more info.  I'm guessing that this is actually a
    "deque" data structure.
    """

    def __init__(self, df):
        super().__init__(df, 'LTde')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Name of the deck
        self.name = self.df.read_string()

        # Items currently ready inside the deck/deque
        self.rede = ReDe(self.df)


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_string(self.name)
        self.rede.write_to(odf)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'name',
            ])
        my_dict['rede'] = self.rede.to_json(verbose)
        return my_dict


class LootTableStatus(Chunk):
    """
    `LTma` chunk.  "LT" refers to "Loot Table," not sure what "ma" refers to though,
    but there's only one of these in the savegame, and it's clearly holding Loot Table
    state.

    From the game data, talking about Loot Tables:

		Controls the distribution of loot, for example by guaranteeing that you
		eventually get weapons for each type of job.

    So this chunk is basically storing the current state of the loot tables, and the
    "decks" stored within, so that the loot distribution still works inbetween play
    sessions.
    """

    def __init__(self, df):
        super().__init__(df, 'LTma')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Variable names in here are pretty vague, sorry.  This structure
        # probably isn't the best, but it'll do for now until I figure out
        # what in the world this is actually used for.  (Assuming that ever
        # happens; I suspect I probably don't care about the data in here.)
        self.loot_groups = []
        num_loot_groups = self.df.read_varint()
        for _ in range(num_loot_groups):
            loot_group_name = self.df.read_string()
            decks = []
            num_decks = self.df.read_varint()
            for _ in range(num_decks):
                decks.append(LootTableDeck(self.df))
            self.loot_groups.append((loot_group_name, decks))

        # report, to see if I can figure out what these things are doing.
        #for idx, (loot_group_name, decks) in enumerate(self.loot_groups):
        #    print(f'Loot Group {idx}: {loot_group_name}')
        #    for inner_idx, deck in enumerate(decks):
        #        print(f' - Deck {inner_idx}: {deck.name}')
        #        print(f'    - ReDe:')
        #        for ready_idx, item_name in enumerate(deck.rede.items):
        #            print(f'       {ready_idx}. {item_name}')
        #    print('')


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.loot_groups))
        for loot_group_name, decks in self.loot_groups:
            odf.write_string(loot_group_name)
            odf.write_varint(len(decks))
            for deck in decks:
                deck.write_to(odf)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['loot_groups'] = []
        for loot_group_name, decks in self.loot_groups:
            new_dict = {
                    'name': loot_group_name,
                    'decks': [],
                    }
            for deck in decks:
                new_dict['decks'].append(deck.to_json(verbose))
            my_dict['loot_groups'].append(new_dict)
        return my_dict


class LootDeckData(Chunk):
    """
    `LoDD` chunk.  Loot Deck... data?
    """

    def __init__(self, df):
        super().__init__(df, 'LoDD')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        self.items = []
        num_items = self.df.read_varint()
        for _ in range(num_items):
            name = self.df.read_string()
            self.items.append(name)


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.items))
        for name in self.items:
            odf.write_string(name)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'items',
            ])
        return my_dict


class LootDeckStatus(Chunk):
    """
    `LoDe` chunk.  Loot Deck status.  Related to the LTma chunks above.
    """

    def __init__(self, df):
        super().__init__(df, 'LoDe')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # TODO: should probably store these as a dict
        self.decks = []
        num_decks = self.df.read_varint()
        for _ in range(num_decks):
            deck_name = self.df.read_string()
            lodd = LootDeckData(self.df)
            self.decks.append((deck_name, lodd))

        # Debug!
        #for deck_name, lodd in self.decks:
        #    print(f'Deck: {deck_name}')
        #    for item in lodd.items:
        #        print(f' - {item}')

        # Various unknown data here.  The first six bytes for nearly all
        # my saves were: 19 E5 F3 28 00 01.  The only exceptions were
        # at the *very* beginning where they were all zeroes; and one other
        # where the last byte was zero.  No clue what to do with 'em, so
        # just reading as bytes for now.
        self.unknown_1 = self.df.read_uint8()
        self.unknown_2 = self.df.read_uint8()
        self.unknown_3 = self.df.read_uint8()
        self.unknown_4 = self.df.read_uint8()
        self.unknown_5 = self.df.read_uint8()
        self.unknown_6 = self.df.read_uint8()

        # Then one more unknown which, fo rall my saves, seems to be a
        # uint32 which is always 1
        self.unknown_one = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.decks))
        for deck_name, lodd in self.decks:
            odf.write_string(deck_name)
            lodd.write_to(odf)

        odf.write_uint8(self.unknown_1)
        odf.write_uint8(self.unknown_2)
        odf.write_uint8(self.unknown_3)
        odf.write_uint8(self.unknown_4)
        odf.write_uint8(self.unknown_5)
        odf.write_uint8(self.unknown_6)
        odf.write_uint32(self.unknown_one)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['decks'] = []
        for deck_name, lodd in self.decks:
            my_dict['decks'].append({
                'name': deck_name,
                'lodd': lodd.to_json(verbose),
                })
        self._json_simple(my_dict, [
            'unknown_1',
            'unknown_2',
            'unknown_3',
            'unknown_4',
            'unknown_5',
            'unknown_6',
            'unknown_one',
            ])
        return my_dict


class ShipLocation(Chunk):
    """
    `ShlD` chunk.  Pretty sure this is ship location.
    """

    def __init__(self, df):
        super().__init__(df, 'ShlD')

        # Hm, I wonder if this is a flag of some sort?  Doesn't start with
        # the usual 0x00 which the first byte of so many other chunks seem to
        # be.
        self.flag = self.df.read_uint8()

        self.location = self.df.read_string()
        self.region = self.df.read_string()

        # Values seen in my saves: 0, 7, 9
        self.unknown_1 = self.df.read_uint32()
        # Values seen in my saves: 0, 1
        self.unknown_2 = self.df.read_uint8()


    def _write_to(self, odf):

        odf.write_uint8(self.flag)
        odf.write_string(self.location)
        odf.write_string(self.region)
        odf.write_uint32(self.unknown_1)
        odf.write_uint8(self.unknown_2)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'flag',
            'location',
            'region',
            'unknown_1',
            'unknown_2',
            ])
        return my_dict


class WorldCloudData(Chunk):
    """
    `MtBG` chunk.  No clue what MtBG actually stands for.

    This holds info about the revealed map.  A bit value of 1 means
    that a cloud is present, and 0 means that it's been revealed.
    """

    # This is hardcoded here, but possibly it's technically reliant on
    # the size stored in the chunk.
    MAP_DATA_SIZE = 10440

    def __init__(self, df):
        super().__init__(df, 'MtBG')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # maybe a flag of some sort?  Value of 1 seems common
        self.unknown_1 = self.df.read_uint8()

        # Pretty sure these are the size of the area; in my saves
        # it's always 270 and then 290
        self.size_x = self.df.read_uint32()
        self.size_y = self.df.read_uint32()

        # Revealed map data -- one bit per "pixel" of the map, in general.
        # 10440/290 is 36, fwiw, and 36 bytes is enough to store 270 bit
        # values (can get 288).  So I think that not all of this data is
        # actually used, but it's pretty close
        self.data = self.df.read(WorldCloudData.MAP_DATA_SIZE)


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_uint8(self.unknown_1)
        odf.write_uint32(self.size_x)
        odf.write_uint32(self.size_y)
        odf.write(self.data)


    def reveal(self):
        self.data = b'\x00'*WorldCloudData.MAP_DATA_SIZE


    def hide(self):
        self.data = b'\xFF'*WorldCloudData.MAP_DATA_SIZE


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'unknown_1',
            'size_x',
            'size_y',
            ])
        # Munging a bit...
        # TODO: should maybe have a couple of levels of verbosity; with
        # our "basic" verbosity I still don't want to include the data here.
        my_dict['data'] = '(omitted)'
        return my_dict


class BehaviorState(Chunk):
    """
    `Beha` chunk.  Behavior States, it seems.  In the game data, these seem
    to relate to enemy ships on the map, which would make sense given where it's
    stored in the savegame.

    NOTE: This class is no longer used since I pared down what data WorldData
    reads in.  It's left here in case I decide to start parsing more of the
    skippable section again, though.
    """

    def __init__(self, df):
        super().__init__(df, 'Beha')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # I haven't *actually* mapped these out to confirm, but I am 99% sure that
        # the first varint corresponds to an entity ID as defined in the ECSD chunk.
        # Presumably this list is storing parameters describing the entity's current
        # behavior state in its behavior tree.
        self.entities = []
        num_entities = self.df.read_varint()
        for _ in range(num_entities):
            entity_id = self.df.read_varint()
            unknown_1 = self.df.read_uint8()
            unknown_2 = self.df.read_uint8()
            unknown_3 = self.df.read_uint8()
            unknown_4 = self.df.read_uint8()
            self.entities.append((entity_id, unknown_1, unknown_2, unknown_3, unknown_4))

        # Then a couple extra unknown zeroes
        self.unknown_zero_1 = self.df.read_uint8()
        self.unknown_zero_2 = self.df.read_uint8()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.entities))
        for entity_id, unknown_1, unknown_2, unknown_3, unknown_4 in self.entities:
            odf.write_varint(entity_id)
            odf.write_uint8(unknown_1)
            odf.write_uint8(unknown_2)
            odf.write_uint8(unknown_3)
            odf.write_uint8(unknown_4)
        odf.write_uint8(self.unknown_zero_1)
        odf.write_uint8(self.unknown_zero_2)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['entities'] = []
        for entity_id, unknown_1, unknown_2, unknown_3, unknown_4 in self.entities:
            my_dict['entities'].append({
                'entity_id': entity_id,
                'unknown_1': unknown_1,
                'unknown_2': unknown_2,
                'unknown_3': unknown_3,
                'unknown_4': unknown_4,
                })
        self._json_simple(my_dict, [
            'unknown_zero_1',
            'unknown_zero_2',
            ])
        return my_dict


class Entities(Chunk):
    """
    `ECSD` chunk.  I think this is defining entities on the map.
    The "wm_*" prefix on the entity names found in here almost certainly
    imply "world map."

    NOTE: This class is no longer used since I pared down what data WorldData
    reads in.  It's left here in case I decide to start parsing more of the
    skippable section again, though.
    """

    def __init__(self, df):
        super().__init__(df, 'ECSD')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Big ol' list.  Almost 100% sure this is a list of entities, mapping
        # their ID to the type of object they are. (value -> name).  Other data
        # will presumably refer to these IDs.
        self.entities = []
        num_entities = self.df.read_varint()
        for _ in range(num_entities):
            value = self.df.read_varint()
            name = self.df.read_string()
            self.entities.append((value, name))

        # A bit of unknown data; first two appear to be a pair of u32s.
        self.unknown_1 = self.df.read_uint32()
        self.unknown_2 = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.entities))
        for value, name in self.entities:
            odf.write_varint(value)
            odf.write_string(name)

        odf.write_uint32(self.unknown_1)
        odf.write_uint32(self.unknown_2)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        # Munging a bit...
        if verbose:
            my_dict['entities'] = []
            for value, name in self.entities:
                my_dict['entities'].append({
                    'value': value,
                    'name': name,
                    })
        else:
            my_dict['num_entities'] = len(self.entities)
            my_dict['entities'] = '(omitted)'
        self._json_simple(my_dict, [
            'unknown_1',
            'unknown_2',
            ])
        return my_dict


class WorldData(Chunk):
    """
    `PWDT` chunk.  Not exactly sure what this is meant to store, though
    the main thing seems to be storing the various revealed-map chunks.
    Could the "WD" mean "World Discovery?"  Seems like a stretch, esp.
    since I have no idea what the P or T would mean.  :)
    """

    def __init__(self, df):
        super().__init__(df, 'PWDT')

        # Seems to always be one?
        self.unknown_one = self.df.read_uint8()

        # Cloud Data
        self.cloud_data = []
        num_cloud_data = self.df.read_varint()
        for _ in range(num_cloud_data):
            self.cloud_data.append(WorldCloudData(self.df))

        ### --------------------
        ### SKIPPABLE ORIG BEGIN
        ### --------------------
        ### Original processing we used to do, which I don't actually
        ### care about.  Omitting it lets us simplify our skipped-data
        ### handling.  See the comments in the main Savefile class's
        ### read routines for more details.

        ## I'm pretty sure that the stuff below belongs here in the PWDT
        ## chunk, since the "behaviors" seem to just be for overworld
        ## enemies, and the Entities processing seems to be similarly map-
        ## related.

        ## I *think* that these are Entity IDs, as defined in the later
        ## ECSD chunk.  I have not confirmed as such, though.  (And I
        ## don't know what these entities' presence in this list
        ## signifies.)
        #self.unknown_entity_ids = []
        #num_unknown_entity_ids = self.df.read_varint()
        #for _ in range(num_unknown_entity_ids):
        #    self.unknown_entity_ids.append(self.df.read_varint())

        ## No clue what's up with these; there are some patterns to be seen,
        ## but they remain pretty opaque.  Does seem to be twelve bytes quite
        ## consistently, though
        #self.unknown_end_bytes = []
        #for _ in range(12):
        #    self.unknown_end_bytes.append(self.df.read_uint8())

        ## Behavior state
        #self.behavior_state = BehaviorState(self.df)

        ## World Map Entities
        #self.entities = Entities(self.df)

        ### ------------------
        ### SKIPPABLE ORIG END
        ### ------------------


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_one)
        odf.write_varint(len(self.cloud_data))
        for data in self.cloud_data:
            data.write_to(odf)

        ### --------------------
        ### SKIPPABLE ORIG BEGIN
        ### --------------------

        #odf.write_varint(len(self.unknown_entity_ids))
        #for entity_id in self.unknown_entity_ids:
        #    odf.write_varint(entity_id)
        #for value in self.unknown_end_bytes:
        #    odf.write_uint8(value)
        #self.behavior_state.write_to(odf)
        #self.entities.write_to(odf)

        ### ------------------
        ### SKIPPABLE ORIG END
        ### ------------------


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_one',
            ])
        self._json_object_arr(my_dict, [
            'cloud_data',
            ], verbose)

        ### --------------------
        ### SKIPPABLE ORIG BEGIN
        ### --------------------

        ## Munging a bit...
        #if verbose:
        #    self._json_simple(my_dict, [
        #        'unknown_entity_ids',
        #        ])
        #else:
        #    my_dict['num_unknown_entity_ids'] = len(self.unknown_entity_ids)
        #    my_dict['unknown_entity_ids'] = '(omitted)'
        #self._json_simple(my_dict, [
        #    'unknown_end_bytes',
        #    ])
        #self._json_object_single(my_dict, [
        #    'behavior_state',
        #    'entities',
        #    ], verbose)

        ### ------------------
        ### SKIPPABLE ORIG END
        ### ------------------

        return my_dict


    def reveal(self):
        for data in self.cloud_data:
            data.reveal()


    def hide(self):
        for data in self.cloud_data:
            data.hide()


# Commenting this for now.  As mentioned in the docstring, I suspect that
# each instance of this chunk technically has its own serialization format,
# and I don't really feel like figuring that out for 70 distinct types.
# It could be that they're all technically the same format and I could just
# figure it out once, but since we can skip over the data for now, that's
# what I'm doing.
#class Component(Chunk):
#    """
#    `ECTa` chunk.  I'm calling this "components" since the strings which
#    prefix each of these chunks are mostly suffixed with `Component` (there
#    are a few exceptions, but whatever -- the "CT" in the name could refer
#    to Component, too).
#
#    My current conundrum: It feels like these chunks might have varying
#    formats depending on what kind of data is stored.  I suspect that to
#    properly parse them, we'd need to pass in the component name (which would
#    be stored in a string directly before the ECTa chunk), and then switch
#    our behavior based on that name.  It could be that I'm missing some
#    similarities, though -- I haven't looked through too exhaustively yet.
#    """
#
#    def __init__(self, df):
#        super().__init__(df, 'ECTa')
#
#        # Seems to always be zero (this seems quite common after chunk
#        # identifiers, actually)
#        self.zero = self.df.read_uint8()
#
#
#    def _write_to(self, odf):
#
#        odf.write_uint8(self.zero)


class MissionData(Chunk):
    """
    `MsnD` chunk.  Pretty sure this is mission data.
    """

    def __init__(self, df):
        super().__init__(df, 'MsnD')

        # Hm, I wonder if this is a flag of some sort?  Doesn't start with
        # the usual 0x00 which the first byte of so many other chunks seem to
        # be.
        self.flag = self.df.read_uint8()

        self.location = self.df.read_string()
        self.another_location = self.df.read_string()

        self.unknown_1 = self.df.read_uint8()
        self.unknown_2 = self.df.read_uint8()
        self.unknown_3 = self.df.read_uint8()
        self.unknown_4 = self.df.read_uint8()

        # A couple of values which seem to be zero when outside of a mission
        # but are >0 when inside one.  I really don't feel like parsing the
        # mission data, so we're trying to fail gracefully here
        self.unknown_mission_related_1 = self.df.read_uint8()
        self.unknown_mission_related_2 = self.df.read_uint8()
        if self.unknown_mission_related_1 > 0 or self.unknown_mission_related_2:
            raise InMissionSavegameException()

        self.unknown_5 = self.df.read_uint8()

        # Just kind of guessing that it's "active."  It's a list of crew, at least.
        self.active_crew = []
        num_active_crew = self.df.read_varint()
        for _ in range(num_active_crew):
            self.active_crew.append(self.df.read_string())

        # These always seem to be zero
        self.unknown_6 = self.df.read_uint8()
        self.unknown_7 = self.df.read_uint8()

        # Sixteen bytes of unknown data, but for all my collected saves, it's
        # literally the same value in each one: a sequence of eight bytes which
        # are then repeated once more for good measure.  Just reading these in
        # as u32s for now.  TODO: should maybe check for 1==3 and 2==4, and alert
        # if that's not the case, so we could maybe investigate.
        #
        # The byte sequence that I see on my saves:
        #
        #    B5 3B 12 1F  E5 55 9A 15  B5 3B 12 1F  E5 55 9A 15
        self.unknown_same_1 = self.df.read_uint32()
        self.unknown_same_2 = self.df.read_uint32()
        self.unknown_same_3 = self.df.read_uint32()
        self.unknown_same_4 = self.df.read_uint32()
        if self.unknown_same_1 != self.unknown_same_3 or self.unknown_same_2 != self.unknown_same_4:
            print("NOTICE: unknown_same_* in MsnD doesn't look how we think it should...")

        # Then a further five bytes which, in my saves, are all zero.  Go team?
        self.unknown_zeroes_1 = self.df.read_uint8()
        self.unknown_zeroes_2 = self.df.read_uint8()
        self.unknown_zeroes_3 = self.df.read_uint8()
        self.unknown_zeroes_4 = self.df.read_uint8()
        self.unknown_zeroes_5 = self.df.read_uint8()

        # And then a varint of some sort -- my one save where this is anything
        # but zero is right after the sub kraken fight, at the end.
        self.unknown_8 = self.df.read_varint()

        # Difficulty.  Different from the "main" difficulty, I guess?
        self.difficulty = Difficulty(self.df)

        # Some more unknown stuff
        self.unknown_zeroes_6 = self.df.read_uint8()

        # Not sure if this is a list, or just a flag saying that there's another
        # varint here.  Treating it as a list for now, I guess?
        self.unknown_eight_bytes = []
        num_unknown_eight_bytes = self.df.read_varint()
        for _ in range(num_unknown_eight_bytes):
            # No clue what these might mean, or how they should be interpreted.
            # There's no string references, at least.  Reading as two uint32s
            # for now.
            self.unknown_eight_bytes.append((
                self.df.read_uint32(),
                self.df.read_uint32(),
                ))

        # Some more unknown stuff
        self.unknown_zeroes_7 = self.df.read_uint8()
        self.unknown_zeroes_8 = self.df.read_uint8()
        self.unknown_zeroes_9 = self.df.read_uint8()

        # Another thing where I don't know if it's a flag or a list.  Treating
        # as a list for now.
        self.unknown_strings = []
        num_unknown_strings = self.df.read_varint()
        for _ in range(num_unknown_strings):
            self.unknown_strings.append(self.df.read_string())


    def _write_to(self, odf):

        odf.write_uint8(self.flag)
        odf.write_string(self.location)
        odf.write_string(self.another_location)

        odf.write_uint8(self.unknown_1)
        odf.write_uint8(self.unknown_2)
        odf.write_uint8(self.unknown_3)
        odf.write_uint8(self.unknown_4)
        odf.write_uint8(self.unknown_mission_related_1)
        odf.write_uint8(self.unknown_mission_related_2)
        odf.write_uint8(self.unknown_5)

        odf.write_varint(len(self.active_crew))
        for crew in self.active_crew:
            odf.write_string(crew)

        odf.write_uint8(self.unknown_6)
        odf.write_uint8(self.unknown_7)

        odf.write_uint32(self.unknown_same_1)
        odf.write_uint32(self.unknown_same_2)
        odf.write_uint32(self.unknown_same_3)
        odf.write_uint32(self.unknown_same_4)
        odf.write_uint8(self.unknown_zeroes_1)
        odf.write_uint8(self.unknown_zeroes_2)
        odf.write_uint8(self.unknown_zeroes_3)
        odf.write_uint8(self.unknown_zeroes_4)
        odf.write_uint8(self.unknown_zeroes_5)
        odf.write_varint(self.unknown_8)

        self.difficulty.write_to(odf)

        odf.write_uint8(self.unknown_zeroes_6)
        odf.write_varint(len(self.unknown_eight_bytes))
        for one, two in self.unknown_eight_bytes:
            odf.write_uint32(one)
            odf.write_uint32(two)

        odf.write_uint8(self.unknown_zeroes_7)
        odf.write_uint8(self.unknown_zeroes_8)
        odf.write_uint8(self.unknown_zeroes_9)

        odf.write_varint(len(self.unknown_strings))
        for string in self.unknown_strings:
            odf.write_string(string)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'flag',
            'location',
            'another_location',
            'unknown_1',
            'unknown_2',
            'unknown_3',
            'unknown_4',
            'unknown_mission_related_1',
            'unknown_mission_related_2',
            'unknown_5',
            'active_crew',
            'unknown_6',
            'unknown_7',
            'unknown_same_1',
            'unknown_same_2',
            'unknown_same_3',
            'unknown_same_4',
            'unknown_zeroes_1',
            'unknown_zeroes_2',
            'unknown_zeroes_3',
            'unknown_zeroes_4',
            'unknown_zeroes_5',
            'unknown_8',
            ])
        my_dict['difficulty'] = self.difficulty.to_json(verbose)
        self._json_simple(my_dict, [
            'unknown_zeroes_6',
            ])
        my_dict['unknown_eight_bytes'] = []
        for one, two in self.unknown_eight_bytes:
            my_dict['unknown_eight_bytes'].append({
                'one': one,
                'two': two,
                })
        self._json_simple(my_dict, [
            'unknown_zeroes_7',
            'unknown_zeroes_8',
            'unknown_zeroes_9',
            'unknown_strings',
            ])
        return my_dict


class ShopData(Chunk):
    """
    `PBar` chunk.  This stores information about a shop/bar's status, which
    apparently means a list of available crew-for-hire, and a list of
    items the player has bought from the store (to determine if the item
    should remain for sale or not).
    """

    def __init__(self, df, name):
        super().__init__(df, 'PBar')
        self.name = name

        # Couple of unknown values
        self.unknown_begin_1 = self.df.read_uint8()
        self.unknown_begin_2 = self.df.read_uint8()

        # Available crew
        self.available_crew = []
        self.crew_unknown_zero = 0
        # This appears to just be a flag.  Should only ever be 0 or 1
        # but we're saving the value just in case
        self.has_crew = self.df.read_uint8()
        if self.has_crew > 0:
            self.crew_unknown_zero = self.df.read_uint8()
            num_crew = self.df.read_varint()
            for _ in range(num_crew):
                self.available_crew.append(self.df.read_string())

        # Now purchased items
        self.purchased_items = []
        num_purchased_items = self.df.read_varint()
        for _ in range(num_purchased_items):
            item = self.df.read_string()
            # I bet this is actually a varint and then three bytes of
            # unknown data, actually...
            qty = self.df.read_uint32()
            self.purchased_items.append((item, qty))

        # Then an unknown
        self.unknown_end = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_begin_1)
        odf.write_uint8(self.unknown_begin_2)

        # Crew
        if len(self.available_crew) == 0:
            odf.write_uint8(0)
        else:
            odf.write_uint8(self.has_crew)
            odf.write_uint8(self.crew_unknown_zero)
            odf.write_varint(len(self.available_crew))
            for crew in self.available_crew:
                odf.write_string(crew)

        # Purchased Items
        odf.write_varint(len(self.purchased_items))
        for item, qty in self.purchased_items:
            odf.write_string(item)
            odf.write_uint32(qty)

        # Final unknown
        odf.write_uint32(self.unknown_end)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'name',
            'unknown_begin_1',
            'unknown_begin_2',
            ])
        crew_section = {}
        crew_section['has_crew'] = self.has_crew
        if len(self.available_crew) > 0:
            self._json_simple(crew_section, [
                'crew_unknown_zero',
                'available_crew',
                ])
        my_dict['crew_section'] = crew_section
        item_section = []
        for item, qty in self.purchased_items:
            item_section.append({
                'item': item,
                'qty': qty,
                })
        my_dict['purchased_items'] = item_section
        self._json_simple(my_dict, [
            'unknown_end',
            ])
        return my_dict


class Shops(Serializable):
    """
    Object to encapsulate a collection of PBar objects which store information
    about bar/shop stocks.  This is fudging a few things because it's not an
    actual chunk type, but we want the object to tie into our usual mechanisms.

    I'm wrapping this up in an object mostly so that I can support clearing
    out "available" crew from shops if I manage to support unlocking crew via
    the save editor.
    """

    def __init__(self, df):
        self.df = df

        # Using a dict and relying on Python's remembered dictionary-insertion
        # ordering.
        self.shops = {}

        num_shops = self.df.read_varint()
        for _ in range(num_shops):
            shop_name = self.df.read_string()
            self.shops[shop_name] = ShopData(self.df, shop_name)


    def __iter__(self):
        return iter(self.shops.values())


    def __len__(self):
        return len(self.shops)


    def write_to(self, odf):
        """
        Note the lack of underscore; this object doesn't inherit from Chunk, so
        our usual encapsulation doesn't happen
        """
        odf.write_varint(len(self.shops))
        for shop in self.shops.values():
            odf.write_string(shop.name)
            shop.write_to(odf)


    def _to_json(self, verbose=False):
        my_list = []
        for shop in self.shops.values():
            my_list.append(shop.to_json(verbose))
        return my_list


class JobStatus:
    """
    Just a bit of encapsulation of job data for our crew.
    """

    def __init__(self, name):
        self.name = name
        self.level = None
        self.xp = None


class CrewStatus(Chunk):
    """
    `Pers` chunk.  SWH2's data implies this is "Persona."  I like "Crew"
    better, though.
    """

    # The order that jobs seem to appear in; used when adding new jobs
    # to our structure.  I don't think we *have* to do this, but I
    # like keeping the save as vanilla as possible.
    JOB_ORDER = [
            'engineer',
            'tank',
            'hunter',
            'boomer',
            'flanker',
            'sniper',
            ]

    def __init__(self, df):
        super().__init__(df, 'Pers')

        # Unknown value.  Seems to usually be 2?
        self.unknown_start = self.df.read_uint8()

        self.name = self.df.read_string()

        # Presumably a varint, but how could we have more than 6?  Just
        # using a u8.  :D
        self.jobs = {}
        num_jobs = self.df.read_uint8()
        for _ in range(num_jobs):
            job_name = self.df.read_string()
            job = JobStatus(job_name)
            job.level = self.df.read_uint32()
            self.jobs[job_name] = job

        # Just trusting that the data is properly-written here.  This
        # could KeyError if not.
        num_jobs = self.df.read_uint8()
        for _ in range(num_jobs):
            job_name = self.df.read_string()
            self.jobs[job_name].xp = self.df.read_uint32()

        self.cog_selections = []
        num_cog_selections = self.df.read_varint()
        for _ in range(num_cog_selections):
            self.cog_selections.append(self.df.read_string())

        # These do seem to be uint32s instead of varints w/ some extra unknown data
        self.reserve_xp = self.df.read_uint32()
        self.num_missions = self.df.read_uint32()
        self.personal_upgrade_count = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_start)
        odf.write_string(self.name)
        odf.write_uint8(len(self.jobs))
        for job in self.jobs.values():
            odf.write_string(job.name)
            odf.write_uint32(job.level)
        odf.write_uint8(len(self.jobs))
        for job in self.jobs.values():
            odf.write_string(job.name)
            odf.write_uint32(job.xp)
        odf.write_varint(len(self.cog_selections))
        for selection in self.cog_selections:
            odf.write_string(selection)
        odf.write_uint32(self.reserve_xp)
        odf.write_uint32(self.num_missions)
        odf.write_uint32(self.personal_upgrade_count)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_start',
            'name',
            ])
        jobs = []
        for job in self.jobs.values():
            jobs.append({
                'name': job.name,
                'level': job.level,
                'xp': job.xp,
                })
        my_dict['jobs'] = jobs
        self._json_simple(my_dict, [
            'cog_selections',
            'reserve_xp',
            'num_missions',
            'personal_upgrade_count',
            ])
        return my_dict


    def job_level_to(self, job_name, to_level, allow_downlevel=False):
        """
        Sets the specified `job_name` to the given `to_level`.  By default this will
        only allow *increasing* the level, but if you pass `allow_downlevel` as `True`,
        it'll do so, and also remove any selected cogs from the levels that are
        being removed.

        A fair bit of the logic in here is technically also done in the argument-validation
        routines on the CLI side, but that's fine.
        """
        # Clamp level to our max
        to_level = min(to_level, XP.max_level)

        # The CLI supports passing in job names by their in-game names in addition to
        # the "real" names, and that should all be normalized by the time it gets here,
        # but there's no good reason not to support them here, too.
        if job_name not in JOBS:
            raise RuntimeError(f'Job "{job_name}" not found in gamedata structures')
        job_info = JOBS[job_name]
        if job_name in self.jobs:
            # Already have a job record for this job
            job = self.jobs[job_name]
            if job.level == to_level:
                return
            elif job.level < to_level:
                job.level = to_level
                job.xp = XP.level_to_xp[to_level]
            else:
                if allow_downlevel:
                    # First remove any cog selections which would require a level we
                    # no longer have.  This may not actually be required; I suspect the
                    # game would just auto-remove an invalid cog selection if we didn't
                    # do it here.  Still, may as well.
                    cur_cog_selections = set(self.cog_selections)
                    for skills_idx in range(job.level, to_level, -1):
                        level_skills = job_info.skills[skills_idx]
                        for skill in level_skills:
                            if skill in cur_cog_selections:
                                # This is kind of inefficient 'cause it's a list, but whatever.
                                self.cog_selections.remove(skill)

                    # Now do the actual down-levelling
                    job.level = to_level
                    job.xp = XP.level_to_xp[to_level]
        else:
            # Need a new job record for the job.  We're doing some shenanigans here to
            # ensure that the jobs are stored in the same order the game would.  The
            # alternative would be to do that in the save routine, but I think I'd rather
            # have that complexity here, and that way the save routines would generate
            # identical files even if the game changes up which order it writes stuff.
            if to_level == 0:
                # Don't bother if the level set was zero, though
                return
            new_jobs = {}
            for new_job_name in CrewStatus.JOB_ORDER:
                if new_job_name in self.jobs:
                    new_jobs[new_job_name] = self.jobs[new_job_name]
                elif new_job_name == job_name:
                    new_job = JobStatus(new_job_name)
                    new_job.level = to_level
                    new_job.xp = XP.level_to_xp[to_level]
                    new_jobs[new_job_name] = new_job
            self.jobs = new_jobs


    def all_jobs_level_to(self, to_level, allow_downlevel=False):
        """
        Sets *all* jobs to the given `to_level`.  By default this will only increase
        the level, not decrease.  To allow downlevelling, set `allow_downlevel`
        to `True`.
        """
        for job_name in CrewStatus.JOB_ORDER:
            self.job_level_to(job_name, to_level, allow_downlevel=allow_downlevel)


    def set_job_xp(self, job_name, to_xp):
        """
        Sets the given job's XP to the specified level.  At the moment, this will
        only allow *increasing* the XP.
        """
        # Clamp XP to our max
        to_xp = min(to_xp, XP.max_xp)

        # The CLI supports passing in job names by their in-game names in addition to
        # the "real" names, and that should all be normalized by the time it gets here,
        # but there's no good reason not to support them here, too.
        if job_name not in JOBS:
            raise RuntimeError(f'Job "{job_name}" not found in gamedata structures')
        job_info = JOBS[job_name]
        if job_name in self.jobs:
            # Already have a job record for this job
            job = self.jobs[job_name]
            if job.xp == to_xp:
                return
            if job.xp > to_xp:
                raise RuntimeError('set_job_xp does not currently support decreasing XP')
            job.xp = to_xp
            for level in range(job.level, XP.max_level+1):
                if to_xp >= XP.level_to_xp[level]:
                    job.level = level
        else:
            # Need a new job record for the job.  We're doing some shenanigans here to
            # ensure that the jobs are stored in the same order the game would.  The
            # alternative would be to do that in the save routine, but I think I'd rather
            # have that complexity here, and that way the save routines would generate
            # identical files even if the game changes up which order it writes stuff.
            if to_xp == 0:
                # Don't bother if the XP set was zero, though
                return
            new_jobs = {}
            for new_job_name in CrewStatus.JOB_ORDER:
                if new_job_name in self.jobs:
                    new_jobs[new_job_name] = self.jobs[new_job_name]
                elif new_job_name == job_name:
                    new_job = JobStatus(new_job_name)
                    new_job.xp = to_xp
                    for level in range(0, XP.max_level+1):
                        if to_xp >= XP.level_to_xp[level]:
                            new_job.level = level
                    new_jobs[new_job_name] = new_job
            self.jobs = new_jobs


    @staticmethod
    def create_new(name):
        """
        Creates a new character with just the name filled in.  You'll have to
        fill in the remaining fields after creation.  The way this is
        done at the moment is absurd.
        """
        # TODO: seriously, this is absurd and weird.
        odf = Savefile('foo', do_write=True)
        odf.write_chunk_header('Pers')
        odf.write_uint8(2)
        odf.write_string(name)
        odf.write_uint8(0)
        odf.write_uint8(0)
        odf.write_varint(0)
        odf.write_uint32(0)
        odf.write_uint32(0)
        odf.write_uint32(0)
        odf.seek(0)
        return CrewStatus(odf)


class CrewController(Chunk):
    """
    `PeCo` chunk.  Contains a bunch of `Pers` chunks, which for SWH2 presumably
    means "Persona" given the game data names.  So I expect that "PeCo" means
    something like "Persona Controller" or whatever.  I'm using "Crew" instead
    'cause it's fewer chars and I like the sound better.

    NOTE: It's actually probably not the best idea to iterate over this structure
    when doing save-edit tasks on your unlocked crew, because at a couple points
    in the game, you end up with some extra records in here, namely:
    crew_captain_rearmed_combat and crew_captain_final_boss.  It's probably best
    to iterate over the main `crew_list` instead, which should be out in the
    main Savefile object, and then use that to get to the crew objects we want.
    """

    def __init__(self, df):
        super().__init__(df, 'PeCo')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        self.crew = {}
        num_crew = self.df.read_varint()
        for _ in range(num_crew):
            crew_name = self.df.read_string()
            self.crew[crew_name] = CrewStatus(self.df)


    def __iter__(self):
        return iter(self.crew.values())


    def __len__(self):
        return len(self.crew)


    def __getitem__(self, name):
        return self.crew[name]


    def __contains__(self, name):
        return name in self.crew


    def keys(self):
        return self.crew.keys()


    def values(self):
        return self.crew.values()


    def items(self):
        return self.crew.items()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.crew))
        for crew_name, crew in self.crew.items():
            odf.write_string(crew_name)
            crew.write_to(odf)


    def _to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        crew_dict = {}
        for crew_name, crew in self.crew.items():
            crew_dict[crew_name] = crew.to_json(verbose)
        my_dict['crew'] = crew_dict
        return my_dict


class UnparsedData:
    """
    So it's unlikely that I'm going to end up decoding the *entire*
    savefile, and even if it eventually happens, I am certainly not
    going to finish that process for some time.  This leaves me with
    the problem of string references in any unprocessed bit of the
    save.  Namely: any edit I make which changes the length of the
    file in any way is almost certainly going to break string
    references in the unparsed bit, after the edit.  There are string
    references very near the end of 300kb saves which reference
    early-save strings, etc.

    So, what to do?  Well: *detecting* string references in the data
    is actually not a huge problem.  Detecting string definitions is
    a bit prone to false-positives, but we don't really have to worry
    about that too much -- a reference will point back to a string
    we've seen earlier on, and we can match on the strlen for an even
    stronger match.  The chances of false positives on the reference
    detection is, IMO, low enough that it's not worth worrying about.

    The plan, then: once I get to the unparsed data, brute-force search
    the remaining data for more strings and string references, making
    a list of string references as I go.  Then when we write out the
    file, instead of just blindly writing out the remaining data,
    we'll have to go through and update them as-needed.  Kind of a pain,
    but I think it should be safe to do, and allow this util to be
    Actually Useful.

    If I ever get to the point of having decoded the entire savefile,
    this class could be stripped out entirely.
    """


    # regex we're using to determine to autodetect strings.
    # A few additions we *could* make:
    #      /\(\) \.
    # Those would let us match literally every top-level `Name`
    # attr in Definitions/*.xml, but the extra ones we pull in
    # are largely dumb (file paths, and one name with a
    # parenthetical comment in it).  Gonna go ahead and leave
    # those out, on the theory that they're unlikely to show up
    # in savefiles.
    VALID_STRING_RE = re.compile(r'^[-a-zA-Z0-9_]+$')


    def __init__(self, savefile, last_pos=None):
        """
        Initializes ourself from the specified savefile, optionally stopping
        at a final position (instead of going until the end of the file).
        That lets us process, for instance, the PBar offset which lets us
        skip a pretty huge chunk of the file.
        """
        self.savefile = savefile
        self.data = self.savefile.data
        self.start_pos = self.savefile.tell()
        if last_pos is None:
            self.last_pos = len(self.data)
        else:
            self.last_pos = last_pos

        # We're going to break the remaining data up into bit: a
        # list whose elements will either be `bytes` or `str`.  `bytes`
        # entries will be written as-is; `str` objects will be handled
        # as strings.
        self.categorized = []

        # We may need to eventually make a guess as to the StringStorage
        # being read.
        self.string_storage_guess = StringStorage.UNKNOWN

        # Start looping
        self.remaining_cur_pos = self.start_pos
        self.remaining_prev_pos = self.start_pos
        while self.remaining_cur_pos < self.last_pos:
            if not self._check_remaining_string():
                self.remaining_cur_pos += 1

        # Categorize any data after the last string value
        if self.remaining_prev_pos < self.last_pos:
            self.categorized.append(self.data[self.remaining_prev_pos:self.last_pos])

        # ... and seek to the end location
        self.savefile.seek(self.last_pos)


    def _read_remaining_varint(self, pos):
        """
        Reads a varint from our remaining data.  This duplicates the logic
        from `datafile.read_varint`, but that function likes working on
        a file-like object, whereas this one's operating on a chunk of
        bytes.  Arguably we could normalize things so that we could use
        a single function, but we'll cope for now.
        """
        iter_count = 0
        data = 0
        cur_shift = 0
        keep_going = True
        while keep_going:
            if iter_count >= 4:
                # If we've gone more than 4 bytes, there's no way
                # it's a value we care about.
                return None
            new_byte = self.data[pos]
            pos += 1
            data |= ((new_byte & 0x7F) << cur_shift)
            if new_byte & 0x80 == 0x80:
                cur_shift += 7
            else:
                keep_going = False
            iter_count += 1
        return (data, pos)


    def _check_remaining_string(self):
        """
        Checks our current position in the remaining data to see if there's
        a string stored here, either as an initial definition or a reference.
        Returns `True` if we found a string, and `False` otherwise.  If we
        did find a string, we will also store any inbetween data in our
        `categorized` list and advance the current position.

        This duplicates a fair bit of logic from `datafile.read_string`, but
        needs to do various things differently due to the circumstances of
        remaining-data processing, so we'll cope for now.
        """
        my_pos = self.remaining_cur_pos
        result = self._read_remaining_varint(my_pos)
        if result is None:
            return False
        strlen, my_pos = result
        if strlen == 0:
            return False
        elif strlen > 255:
            # Very arbitrary size restriction here, but the maximum name for
            # top-level elements in Definitions/*.xml, even including the
            # sillier chars in the regex, is 50.  I'm assuming anything this
            # big isn't worth checking; it's likely to be a false positive.
            return False
        second_val_pos = my_pos
        result = self._read_remaining_varint(my_pos)
        if result is None:
            return False
        second_val, my_pos = result
        if second_val == 0:
            # Potential string; read it in and see
            string_val = self.data[my_pos:my_pos+strlen]
            if len(string_val) != strlen:
                # Probably overflowed past the end of the file?
                return False
            string_val = string_val.decode(self.savefile.encoding)
            if not UnparsedData.VALID_STRING_RE.match(string_val):
                # Doesn't look like a string!
                return False

            if string_val in self.savefile.string_read_seen:
                # We've already seen this string; that could either mean that both
                # are false positives, or that we're reading a file that's been
                # saved with StringStorage.EXPANDED.  By the time we start processing
                # unparsed data (as we're doing now), we *should* be able to guess
                # which is which.  If it looks like we've had duplicates prior to
                # this point, we'll proceed, but if we haven't had duplicates, we'll
                # assume it's a false positive and return
                if self.string_storage_guess == StringStorage.UNKNOWN:
                    self.string_storage_guess = self.savefile.get_string_storage_guess()
                if self.string_storage_guess == StringStorage.COMPRESSED:
                    return False

            # Finally, we're as sure as we can be that this is a valid string.
            # Even if it's a false positive, we should be safe writing it out as
            # a string later, since that'll result in the same byte sequence,
            # and nothing would be referencing it unless there's a *really*
            # unlucky coincidence.
            #print(f' <- {string_val}')

            # Store any data from before the string
            if self.remaining_prev_pos < self.remaining_cur_pos:
                self.categorized.append(self.data[self.remaining_prev_pos:self.remaining_cur_pos])

            # Store the string (though if it's a duplicate, remember the *first*
            # location, not this new one)
            if string_val not in self.savefile.string_read_seen:
                self.savefile.string_read_lookup[my_pos] = string_val
                self.savefile.string_read_seen.add(string_val)
            self.categorized.append(string_val)

            # Update current position
            self.remaining_cur_pos = my_pos + strlen
            self.remaining_prev_pos = self.remaining_cur_pos
            return True
        else:
            # Potential string reference; take a peek
            target_pos = second_val_pos-second_val
            if target_pos in self.savefile.string_read_lookup:
                destination_string = self.savefile.string_read_lookup[target_pos]
                if len(destination_string) != strlen:
                    # String lengths don't match; this is a false positive!
                    return False
                # Now it's almost assured that we've reached a valid string reference.
                # Store it!
                #print(f' -> {destination_string}')

                # Store any data from before the string
                if self.remaining_prev_pos < self.remaining_cur_pos:
                    self.categorized.append(self.data[self.remaining_prev_pos:self.remaining_cur_pos])

                # Now store the string
                self.categorized.append(destination_string)

                # Update current position
                self.remaining_cur_pos = my_pos
                self.remaining_prev_pos = self.remaining_cur_pos
                return True
            else:
                return False


    def write_to(self, odf):
        """
        Write ourselves out to the specified file
        """
        for segment in self.categorized:
            if type(segment) == bytes:
                odf.write(segment)
            elif type(segment) == str:
                odf.write_string(segment)
            else:
                raise RuntimeError(f'Unknown segment type in remaining data: {type(segment)}')


class Savefile(Datafile, Serializable):


    # Maximum savefile version that we can parse
    MAX_VERSION = 1


    def __init__(self, filename, do_write=False, error_save_to=None, force_overwrite=False):
        super().__init__(filename, do_write=do_write)
        if not do_write:
            self.read_and_parse()

            # Sanity check: make sure that, were we to write the file back right now, it
            # remains identical to the input
            test = self._prep_write_data(force_string_mode=self.string_storage)
            test.seek(0)
            test_data = test.read()
            if self.data != test_data:
                extra = ''
                if error_save_to is not None:
                    do_write = True
                    if not force_overwrite and os.path.exists(error_save_to):
                        print(f'WARNING: Error dump target {error_save_to} already exists.')
                        response = input('Overwrite (y/N)? ').strip().lower()
                        if response == '' or response[0] != 'y':
                            print('Not writing error dump file')
                            do_write = False
                    if do_write:
                        with open(error_save_to, 'wb') as odf:
                            odf.write(test_data)
                        extra = f' (Wrote error dump file to: {error_save_to})'
                raise RuntimeError(f'Could not reconstruct an identical savefile, aborting!{extra}')


    def _read_and_parse(self):

        # TODO: I suspect many things which I'm assuming are uint8s are
        # actually varints!

        # File magic
        magic = self.read(4)
        if magic != b'SWH2':
            raise RuntimeError('"SWH2" header not found; this is not a SWH2 savefile?')

        # Save version
        self.version = self.read_uint8()
        if self.version > Savefile.MAX_VERSION:
            raise RuntimeError(f'Savefile version {self.version} found, we only support up to {Savefile.MAX_VERSION}')

        # Checksum
        self.checksum = self.read_uint32()

        # Header chunk
        self.header = Header(self)

        # NOTE: it's entirely possible that some of these subsequent chunks
        # are technically part of the Header chunk.  Time will tell if there
        # are any clues about that

        # Some mission state?
        self.imh2 = Imh2(self)

        # Game resources
        self.resources = GameResources(self)

        # Ship status
        self.ship = Ship(self)

        # Inventory
        self.inventory = Inventory(self)

        # Another character list?  We sort of already had this in the header,
        # though; weird.  The last stuff that I put in the Inventory chunk
        # was Character Loadouts, which sort of made sense, but not for this.
        # Maybe Ship and Inventory are a part of GameResources?  Anyway,
        # just putting here for now, which makes it outside a chunk so that's
        # probably not right.  The list does seem to generally be in a
        # different order than the one in the header.
        self.crew_list = []
        num_crew_list = self.read_uint8()
        for _ in range(num_crew_list):
            self.crew_list.append(self.read_string())

        # List of crew which have already been used today
        self.used_crew = []
        num_used_crew = self.read_uint8()
        for _ in range(num_used_crew):
            self.used_crew.append(self.read_string())

        # More data which feels like we must still be inside another chunk.
        # Maybe we're really not even out of the header yet?  Anyway.
        has_rede_chunk = self.read_uint8()
        if has_rede_chunk != 0 and has_rede_chunk != 1:
            # I'm not sure if this is a flag or a count; would like to know
            # if we get other numbers
            raise RuntimeError('Unknown ReDe chunk signifier: {self.has_rede_chunk}')
        if has_rede_chunk == 0:
            self.rede = None
        else:
            rede_zero = self.read_uint8()
            if rede_zero != 0:
                # Likewise, the zero here weirds me out.  Prefer erroring out
                # if I ever see this not zero.
                raise RuntimeError('Unknown ReDe chunk prefix: {rede_zero}')
            self.rede = ReDe(self)

        # Loot Table status
        self.loot_tables = LootTableStatus(self)

        # Loot Deck status
        self.lode = LootDeckStatus(self)

        # Ship Location
        self.ship_location = ShipLocation(self)

        # Mission Data
        self.missions = MissionData(self)

        # This varint contains an offset which can be used to skip to the PBar
        # array near the end of the file.  This skips over the map data, behavior
        # states, world-map entities, a whole series of Component dumps which take
        # up more than 50% of the file, and Lua variable state.
        self.shops_offset = self.read_varint()
        self.pbar_start_loc = self.tell() + self.shops_offset

        # If shops_offset is zero, we end up skipping right to the PeCo chunks, otherwise
        # we're digging a bit into it.
        if self.shops_offset > 0:

            # A few values we only have with a zero offset
            self.skipped_unknown_zero_1 = None
            self.skipped_unknown_zero_2 = None

            ### -------------------
            ### SKIPPABLE NEW BEGIN
            ### -------------------
            ### This is the new handling for the skippable section.  WorldData now
            ### only reads in the initial data, which has no strings.  Since string
            ### handling in the skippable area is totally isolated from the rest of
            ### the file, we can just read the remaining data as one big set of
            ### bytes and be done with it.  The original (more complex) processing
            ### is commented below.
            ###

            # World Data
            self.world_data = WorldData(self)

            # Skipped Data
            remaining_skip_len = self.pbar_start_loc - self.tell()
            self.skipped_data = self.read(remaining_skip_len)

            ### -----------------
            ### SKIPPABLE NEW END
            ### -----------------

            ### --------------------
            ### SKIPPABLE ORIG BEGIN
            ### --------------------
            ### This is the original processing I was doing while reading in this
            ### section, which turned out to be more complicated than we need.
            ### I'd added in some code to handle the isolated strings, and also
            ### parsed a ways into the section more than we cared (which did involve
            ### reading strings). This all *works* but there's no reason to do it,
            ### and IMO carries more risk since our string handling for the
            ### unparsed bit could technically go wrong if we get really unlucky.
            ### So, it's commented now!
            ###
            ### NOTE: Technically this section won't actually work anymore when
            ### uncommented, because I ripped out the StringRegistry abstraction.
            ### If I ever do resurrect this, my plan would be to create a separate
            ### io.BytesIO object which contains just the skippable data, and then
            ### use that as a `Savefile` object to read from.  That would isolate
            ### the string handling properly and be a little less janky.

            ## World Data
            #self.world_data = WorldData(self)

            ## Then, we have, apparently, always 70 components, composed of
            ## a string followed by an ECTa chunk.  I don't see anything
            ## immediately which seems to provide that number, though I admit
            ## I didn't look long.  We're just skipping these for now, since
            ## shops_offset lets us skip right over, and I'd otherwise have to
            ## start parsing 70 unique serialization formats.
            ##self.components = []
            ##for _ in range(70):
            ##    component_str = self.df.read_string()
            ##    component = Component(self.df)
            ##    self.components.append((component_str, component))

            ## Now just go ahead and skip the rest of the inbetween
            ## data that our shops_offset lets us ignore
            #self.skipped_data = UnparsedData(self, self.pbar_start_loc)

            ### ------------------
            ### SKIPPABLE ORIG END
            ### ------------------

        else:

            self.world_data = None
            self.skipped_data = None

        # There seems to be a spare uint8 which is always `0x00` before the
        # Shops data.
        self.pre_shops_zero = self.read_uint8()

        # Shop Status
        self.shops = Shops(self)

        # Crew status!
        self.crew = CrewController(self)

        # Any remaining data at the end that we're not sure of
        self.remaining = UnparsedData(self)


    def _prep_write_data(self, filename=None, force_string_mode=StringStorage.UNKNOWN):
        if filename is None:
            filename = self.filename
        odf = Savefile(filename, do_write=True)

        # Potentially force a string-writing mode
        match force_string_mode:
            case StringStorage.COMPRESSED | StringStorage.EXPANDED:
                # Forcing a specific mode
                odf.string_storage = force_string_mode
            case _:
                # Just use whatever our method is
                odf.string_storage = self.string_storage

        # File magic
        odf.write(b'SWH2')

        # Save version
        odf.write_uint8(self.version)

        # Temp checksum
        odf.write_uint32(0)

        # Header chunk
        self.header.write_to(odf)

        # Some mission state?
        self.imh2.write_to(odf)

        # Game resources
        self.resources.write_to(odf)

        # Ship status
        self.ship.write_to(odf)

        # Inventory
        self.inventory.write_to(odf)

        # Crew list, again?
        odf.write_uint8(len(self.crew_list))
        for crew in self.crew_list:
            odf.write_string(crew)

        # Used Crew
        odf.write_uint8(len(self.used_crew))
        for crew in self.used_crew:
            odf.write_string(crew)

        # ReDe
        if self.rede is None:
            odf.write_uint8(0)
        else:
            odf.write_uint8(1)
            odf.write_uint8(0)
            self.rede.write_to(odf)

        # Loot Table Status
        self.loot_tables.write_to(odf)

        # Loot Deck status
        self.lode.write_to(odf)

        # Ship Location
        self.ship_location.write_to(odf)

        # Mission Data
        self.missions.write_to(odf)

        ###
        ### PBar offset handling...
        ###

        # Offset to get to shop/PBar chunks, plus some of that otherwise-skipped
        # data.  Note that the skippable section handles its strings totally
        # separately from the rest of the file.  If a string was used earlier
        # on, its use in this skippable section will cause it to be written
        # out again, and string references will *never* go beyond the beginning
        # of the skippable section.  Likewise, any string references *after*
        # that point can't point inside the skippable area.

        if self.shops_offset == 0:

            # If it's zero, just write the offset
            odf.write_varint(self.shops_offset)

        else:

            # Set up a new file to write to
            skipped_data_start_loc = odf.tell()
            skippable_df = Savefile('virtual', do_write=True)

            ### -------------------
            ### SKIPPABLE NEW BEGIN
            ### -------------------
            ### See the comments up in the reading section re: this

            # World Data
            self.world_data.write_to(skippable_df)

            # Skipped Data
            skippable_df.write(self.skipped_data)

            ### -----------------
            ### SKIPPABLE NEW END
            ### -----------------

            ### --------------------
            ### SKIPPABLE ORIG BEGIN
            ### --------------------
            ### See the comments up in the reading section re: this.  With the
            ### StringRegistry abstraction ripped out, this is actually hardly
            ### any different.

            ## Write the remaining data
            #self.world_data.write_to(skippable_df)
            ##for component_str, component in self.components:
            ##    skippable_df.write_string(component_str)
            ##    component.write_to(skippable_df)
            #self.skipped_data.write_to(skippable_df)

            ### ------------------
            ### SKIPPABLE ORIG END
            ### ------------------

            # The offset should just be the length of the data we just wrote
            self.shops_offset = skippable_df.tell()
            odf.write_varint(self.shops_offset)
            skippable_df.seek(0)
            odf.write(skippable_df.read())

        ###
        ### Resuming our ordinary processing...
        ###

        # Now post-skipped data which still relies on having
        # a nonzero shops_offset.
        odf.write_uint8(self.pre_shops_zero)

        # Shop Status
        self.shops.write_to(odf)

        # Crew status
        self.crew.write_to(odf)

        # Any remaining data at the end that we're not sure of
        self.remaining.write_to(odf)

        # Now fix the checksum
        new_checksum = binascii.crc32(odf.getvalue()[9:])
        odf.seek(5)
        odf.write_uint32(new_checksum)

        # ... and return
        return odf


    def save_to(self, filename, force_string_mode=StringStorage.UNKNOWN):
        odf = self._prep_write_data(filename, force_string_mode=force_string_mode)
        odf.save()


    def to_json(self, verbose=False):
        my_dict = {}
        self._json_simple(my_dict, [
            'version',
            ])
        self._json_object_single(my_dict, [
            'header',
            'imh2',
            'resources',
            'ship',
            'inventory',
            ], verbose)
        self._json_simple(my_dict, [
            'crew_list',
            'used_crew',
            ])
        if self.rede is not None:
            self._json_object_single(my_dict, [
                'rede',
                ], verbose)
        self._json_object_single(my_dict, [
            'loot_tables',
            'lode',
            'ship_location',
            'missions',
            ], verbose)
        self._json_simple(my_dict, [
            'shops_offset',
            ])
        if self.shops_offset > 0:
            my_dict['world_data'] = self.world_data.to_json(verbose)
            my_dict['skipped_data'] = '(omitted)'
        self._json_simple(my_dict, [
            'pre_shops_zero',
            ])
        self._json_object_arr(my_dict, [
            'shops',
            ], verbose)
        self._json_object_single(my_dict, [
            'crew',
            ])
        my_dict['remaining_data'] = '(omitted)'
        return my_dict


    def unlock_crew(self, crew_name, level, flag_as_new=True):
        """
        Unlock the specified crewmember, if they're not already unlocked.
        The crew will be levelled up in their default job to the specified
        `level`.  If `flag_as_new` is `True` (the default), the crew's new
        hat will be flagged as New.
        """
        # We *should* have only been passed valid crew names by now, but there's
        # no reason not to do the lookup anyway.
        if crew_name not in CREW:
            raise RuntimeError(f'Unknown crew member to unlock: {crew_name}')
        crew_info = CREW[crew_name]

        # One more sanity check for already-existing.  Inefficient since
        # this is a list, not a set.
        if crew_info.name in self.crew_list:
            return

        # Now do our work
        self.header.crew.append(crew_info.name)
        if crew_info.default_hat not in self.inventory.hats:
            self.inventory.hats.append(crew_info.default_hat)
            if flag_as_new:
                self.inventory.new_hats.append(crew_info.default_hat)
        loadout = Loadout.create_new(crew_info.name, self.inventory.items_by_id)
        loadout.cur_hat = crew_info.default_hat
        self.inventory.loadouts[crew_info.name] = loadout
        self.crew_list.append(crew_info.name)
        # This structure is still a bit of a mystery to me.  It actually looks
        # like we could probably just leave it alone entirely and the game works.
        # If we clear it out entirely (by unlocking all crew) but then *don't*
        # set that `unknown` value to 0, the game will crash upon entering a bar
        # which usually has crew available.  I guess I'm just contenting myself
        # with that for now.
        if self.rede is not None:
            # Inefficient lookup since it's a list
            if crew_info.name in self.rede.items:
                self.rede.items.remove(crew_info.name)
            # If we empty out the list, we need to do this too
            if len(self.rede.items) == 0:
                self.rede.unknown = 0
        for shop in self.shops:
            for idx in range(len(shop.available_crew)):
                if shop.available_crew[idx] == crew_info.name:
                    shop.available_crew[idx] = None
        crew = CrewStatus.create_new(crew_info.name)
        crew.job_level_to(crew_info.default_job.name, level)
        self.crew.crew[crew_info.name] = crew

