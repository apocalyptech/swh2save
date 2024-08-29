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

import re
import abc
import enum
import binascii

from .datafile import Datafile

class Chunk:
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


    def to_json(self):
        my_dict = {'chunk': self.header}
        my_dict |= self._to_json()
        return my_dict


    @abc.abstractmethod
    def _to_json(self):
        return {}


    def _json_simple(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = getattr(self, attr)


    def _json_object_arr(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = []
            for element in getattr(self, attr):
                target_dict[attr].append(element.to_json())


    def _json_object_single(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = getattr(self, attr).to_json()


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


    def _to_json(self):
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


    def _to_json(self):
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


    def _to_json(self):
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


    def _to_json(self):
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


    def _to_json(self):
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
            ])
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

        # These basically always appear to be 0
        self.unknown_4 = self.df.read_uint32()
        self.unknown_5 = self.df.read_uint32()
        #print(f'{self.unknown_1} {self.id} {self.flags} {self.name} {self.unknown_4} {self.unknown_5}')


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_1)
        odf.write_varint(self.id)
        odf.write_uint32(self.flags)
        odf.write_string(self.name)
        odf.write_uint32(self.unknown_4)
        odf.write_uint32(self.unknown_5)


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


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_1',
            'id',
            'flags',
            'name',
            'unknown_4',
            'unknown_5',
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

        # Often 0 on my saves, but I've also seen 1; I suspect
        # that means "used in a mission already"
        self.state = self.df.read_uint32()

        #print(f'{self.zero} {self.name} | {self.unknown_3} | {self.state}')


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
        odf.write_uint32(self.state)


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


    def _to_json(self):
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
            'state',
            ])
        return my_dict


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
        self.loadouts = []
        num_chars = self.df.read_uint8()
        for _ in range(num_chars):
            self.loadouts.append(Loadout(self.df, self.items_by_id))


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
        for loadout in self.loadouts:
            loadout.write_to(odf)


    def add_item(self, item_name, item_flags, flag_as_new=True):
        """
        Adds a new item with the given name to our inventory
        """
        self.last_inventory_id += 1
        self.items.append(InventORyItem.create_new(self.last_inventory_id, item_name, item_flags))
        if flag_as_new:
            self.new_items.append(self.last_inventory_id)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_1',
            'last_inventory_id',
            ])
        self._json_object_arr(my_dict, [
            'items',
            ])
        self._json_simple(my_dict, [
            'new_items',
            'unknown_arr_2',
            'hats',
            'new_hats',
            'leeway_hat',
            ])
        self._json_object_arr(my_dict, [
            'loadouts',
            ])
        return my_dict


class ReDe(Chunk):
    """
    `ReDe` chunk.
    So I suspect this is intended to be a list of things that are "ready" ("ReDe")
    to go, or "on deck" to be acquired, or something.  Its first use in the file
    is a ReDe chunk which seems to contain a list of characters you haven't
    recruited yet (so they'd be ready to recruit).  Then a bit later on, there's
    a structure detailing some loot groups.  For instance, from some debug output
    there:

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

    So yeah, not really sure.
    """

    def __init__(self, df):
        super().__init__(df, 'ReDe')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Variable naming is pretty vague here, sorry.
        self.things = []
        num_things = self.df.read_varint()
        for _ in range(num_things):
            self.things.append(self.df.read_string())

        # On my saves, ranges from 0-4.  Bigger values in general when
        # there are more things in the list, though that's not
        # entirely predictive.
        self.unknown = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.things))
        for thing in self.things:
            odf.write_string(thing)
        odf.write_uint32(self.unknown)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'things',
            'unknown',
            ])
        return my_dict


class LootTableDeck(Chunk):
    """
    `LTde` chunk.  A single "deck" inside a Loot Table entry.  See the LTma
    docstring for some more info.
    """

    def __init__(self, df):
        super().__init__(df, 'LTde')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Name of the deck
        self.name = self.df.read_string()

        # Items currently "ready" inside the deck
        self.rede = ReDe(self.df)


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_string(self.name)
        self.rede.write_to(odf)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'name',
            ])
        my_dict['rede'] = self.rede.to_json()
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
        #        for ready_idx, item_name in enumerate(deck.rede.things):
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


    def _to_json(self):
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
                new_dict['decks'].append(deck.to_json())
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


    def _to_json(self):
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


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['decks'] = []
        for deck_name, lodd in self.decks:
            my_dict['decks'].append({
                'name': deck_name,
                'lodd': lodd.to_json(),
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


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'flag',
            'location',
            'region',
            'unknown_1',
            'unknown_2',
            ])
        return my_dict


class RevealedMapData(Chunk):
    """
    `MtBG` chunk.  This holds info about the revealed map; a bit value of
    1 means that a cloud is present, and 0 means that it's been revealed.
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
        self.data = self.df.read(RevealedMapData.MAP_DATA_SIZE)


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_uint8(self.unknown_1)
        odf.write_uint32(self.size_x)
        odf.write_uint32(self.size_y)
        odf.write(self.data)


    def reveal(self):
        self.data = b'\x00'*RevealedMapData.MAP_DATA_SIZE


    def hide(self):
        self.data = b'\xFF'*RevealedMapData.MAP_DATA_SIZE


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            'unknown_1',
            'size_x',
            'size_y',
            ])
        my_dict['data'] = '(omitted)'
        return my_dict


class PWDT(Chunk):
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

        # Revealed map data
        self.revealed_map_data = []
        num_revealed_map_data = self.df.read_varint()
        for _ in range(num_revealed_map_data):
            self.revealed_map_data.append(RevealedMapData(self.df))

        # Then some more data; maybe a series of varints?
        self.unknown_varints = []
        num_unknown_varints = self.df.read_varint()
        for _ in range(num_unknown_varints):
            self.unknown_varints.append(self.df.read_varint())


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_one)
        odf.write_varint(len(self.revealed_map_data))
        for data in self.revealed_map_data:
            data.write_to(odf)
        odf.write_varint(len(self.unknown_varints))
        for varint in self.unknown_varints:
            odf.write_varint(varint)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'unknown_one',
            ])
        self._json_object_arr(my_dict, [
            'revealed_map_data',
            ])
        # Munging a bit...
        my_dict['num_unknown_varints'] = len(self.unknown_varints)
        #self._json_simple(my_dict, [
        #    'unknown_varints',
        #    ])
        return my_dict


class Beha(Chunk):
    """
    `Beha` chunk.  Related to Behaviors, I guess?  In the game data, these seem
    to relate to enemy ships on the map, which would make sense given where it's
    stored in the savegame.
    """

    def __init__(self, df):
        super().__init__(df, 'Beha')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        self.things = []
        num_things = self.df.read_varint()
        for _ in range(num_things):
            initial_varint = self.df.read_varint()
            unknown_1 = self.df.read_uint8()
            unknown_2 = self.df.read_uint8()
            unknown_3 = self.df.read_uint8()
            unknown_4 = self.df.read_uint8()
            self.things.append((initial_varint, unknown_1, unknown_2, unknown_3, unknown_4))

        # Then a couple extra unknown zeroes
        self.unknown_zero_1 = self.df.read_uint8()
        self.unknown_zero_2 = self.df.read_uint8()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.things))
        for varint, unknown_1, unknown_2, unknown_3, unknown_4 in self.things:
            odf.write_varint(varint)
            odf.write_uint8(unknown_1)
            odf.write_uint8(unknown_2)
            odf.write_uint8(unknown_3)
            odf.write_uint8(unknown_4)
        odf.write_uint8(self.unknown_zero_1)
        odf.write_uint8(self.unknown_zero_2)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['things'] = []
        for varint, unknown_1, unknown_2, unknown_3, unknown_4 in self.things:
            my_dict['things'].append({
                'varint': varint,
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


class Component(Chunk):
    """
    `ECTa` chunk.  I'm calling this "components" since the strings which
    prefix each of these chunks are mostly suffixed with `Component` (there
    are a few exceptions, but whatever -- the "CT" in the name could refer
    to Component, too).

    My current conundrum: It feels like these chunks might have varying
    formats depending on what kind of data is stored.  I suspect that to
    properly parse them, we'd need to pass in the component name (which would
    be stored in a string directly before the ECTa chunk), and then switch
    our behavior based on that name.  It could be that I'm missing some
    similarities, though -- I haven't looked through too exhaustively yet.
    """

    def __init__(self, df):
        super().__init__(df, 'ECTa')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)


class Entities(Chunk):
    """
    `ECSD` chunk.  I think this is defining entities on the map
    """

    def __init__(self, df):
        super().__init__(df, 'ECSD')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        # Big ol' list.  I assume the value is an ID of some sort, but
        # maybe it's a position somehow, instead?
        self.entities = []
        num_entities = self.df.read_varint()
        for _ in range(num_entities):
            value = self.df.read_varint()
            name = self.df.read_string()
            self.entities.append((value, name))

        # A bit of unknown data; first two appear to be a pair of u32s.
        self.unknown_1 = self.df.read_uint32()
        self.unknown_2 = self.df.read_uint32()

        # Then, we have, apparently, always 70 components, composed of
        # a string followed by an ECTa chunk.  I don't see anything
        # immediately which seems to provide that number, though I admit
        # I didn't look long
        #self.components = []
        #for _ in range(70):
        #    component_str = self.df.read_string()
        #    component = Component(self.df)
        #    self.components.append((component_str, component))


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.entities))
        for value, name in self.entities:
            odf.write_varint(value)
            odf.write_string(name)

        odf.write_uint32(self.unknown_1)
        odf.write_uint32(self.unknown_2)

        #for component_str, component in self.components:
        #    odf.write_string(component_str)
        #    component.write_to(odf)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'zero',
            ])
        my_dict['entities'] = []
        # Munging a bit
        my_dict['num_entities'] = len(self.entities)
        #for value, name in self.entities:
        #    my_dict['entities'].append({
        #        'value': value,
        #        'name': name,
        #        })
        self._json_simple(my_dict, [
            'unknown_1',
            'unknown_2',
            ])
        return my_dict


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
        # The data here seems like it would always fit in a u16; perhaps we're being
        # too greedy with the 32...
        self.unknown_3 = self.df.read_uint32()
        self.unknown_4 = self.df.read_uint8()

        # Just kind of guessing that it's "active."  It's a list of crew, at least.
        self.active_crew = []
        num_active_crew = self.df.read_varint()
        for _ in range(num_active_crew):
            self.active_crew.append(self.df.read_string())

        # These always seem to be zero
        self.unknown_5 = self.df.read_uint8()
        self.unknown_6 = self.df.read_uint8()

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
        self.unknown_7 = self.df.read_varint()

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

        # Debugging...
        if False:
            print('  ' + ' | '.join([str(i) for i in [
                self.flag,
                self.location,
                self.another_location,
                self.unknown_1,
                self.unknown_2,
                self.unknown_3,
                self.unknown_4,
                #','.join(self.active_crew),
                self.unknown_5,
                self.unknown_6,
                self.unknown_same_1,
                self.unknown_same_2,
                self.unknown_zeroes_1,
                self.unknown_zeroes_2,
                self.unknown_zeroes_3,
                self.unknown_zeroes_4,
                self.unknown_zeroes_5,
                self.unknown_7,
                self.unknown_zeroes_6,
                self.unknown_eight_bytes,
                self.unknown_zeroes_7,
                self.unknown_zeroes_8,
                self.unknown_zeroes_9,
                self.unknown_strings,
                ]]))

        # Then a varint of some sort.  This feels like it's *got* to be an
        # offset of some sort; it very nearly points to a section with the only
        # LuaW chunk (with some associated PBar chunks, and PeCo), and shortly
        # thereafter is some Pers chunks (which is where I think XP + skills are).
        # It's *so close!*  I can't quite figure out exactly how to interpret it,
        # though.  Also: I feel like there are some edge cases with setting this
        # up; you'd need to take into account any strings stored in the inner
        # data, and depending on how that plays out, the byte length could change,
        # which could theoretically cause this varint to change length, which
        # would then need to trigger the inner string references to change yet
        # again, etc...
        #
        # Still, it seems quite regular.  On the first 19 of the saves I collected,
        # if you move backwards three bytes from the start of the varint and then
        # add this offset, you end up directly at the LuaW chunk.  But then at
        # the 20th save, you start having to go backwards more than three bytes.
        # Though the distance stays constant for awhile, before having another
        # similar jump.  So: weird.
        #
        # I'm a bit worried that we'll end up needing to know how to update this
        # value properly, but time will tell.
        self.unknown_offset = self.df.read_varint()

        # Some debugging attempts...
        #cur_pos = self.df.tell()
        #import os
        #self.df.seek(self.unknown_offset-6, os.SEEK_CUR)
        #new_pos = self.df.tell()
        #data = self.df.read(4)
        #self.df.seek(cur_pos)
        #print('0x{:X} + 0x{:X} -> 0x{:X}: {}'.format(
        #    cur_pos,
        #    self.unknown_offset,
        #    new_pos,
        #    data,
        #    ))

        # Yet more debugging
        if False:
            cur_pos = self.df.tell()
            theoretical_target = cur_pos+self.unknown_offset
            start_test = cur_pos + self.unknown_offset - 512
            self.df.seek(start_test)
            remaining_data = self.df.read()
            interested = {
                    b'LuaW': None,
                    b'PeCo': None,
                    }
            cur_idx = 0
            for cur_idx in range(0, len(remaining_data)-4):
                test_chunk = remaining_data[cur_idx:cur_idx+4]
                if test_chunk in interested:
                    interested[test_chunk] = start_test + cur_idx
                    if all([v is not None for v in interested.values()]):
                        break
            if any([v is None for v in interested.values()]):
                print("  (skipping, don't have the full dataset)")
            else:
                print('  -> 0x{:X} - '.format(theoretical_target) + ', '.join([
                    '{} (0x{:X}): {}'.format(
                            k.decode('latin1'),
                            v,
                            v-theoretical_target,
                        ) for k,v in interested.items()
                    ]))
            print('')
            self.df.seek(cur_pos)

        # Well, regardless of how exactly to interpret that offset, it seems that
        # if it's 0 we skip a bunch of processing, but otherwise we have some
        # more chunks to read in.
        # TODO: I kind of suspect that our offset, plus all this processing, belongs
        # out in the "main" area instead of nested inside the MsnD chunk.
        if self.unknown_offset > 0:
            self.pwdt = PWDT(self.df)

            # No clue what's up with these; there are some patterns to be seen,
            # but they remain pretty opaque.  Does seem to be twelve bytes quite
            # consistently, though
            self.unknown_end_bytes = []
            for _ in range(12):
                self.unknown_end_bytes.append(self.df.read_uint8())

            # Behavior state, I guess?
            self.beha = Beha(self.df)

            # Entities, I think?
            self.entities = Entities(self.df)
        else:
            self.pwdt = None
            self.unknown_end_bytes = None
            self.beha = None
            self.entities = None


    def _write_to(self, odf):

        odf.write_uint8(self.flag)
        odf.write_string(self.location)
        odf.write_string(self.another_location)

        odf.write_uint8(self.unknown_1)
        odf.write_uint8(self.unknown_2)
        odf.write_uint32(self.unknown_3)
        odf.write_uint8(self.unknown_4)

        odf.write_varint(len(self.active_crew))
        for crew in self.active_crew:
            odf.write_string(crew)

        odf.write_uint8(self.unknown_5)
        odf.write_uint8(self.unknown_6)

        odf.write_uint32(self.unknown_same_1)
        odf.write_uint32(self.unknown_same_2)
        odf.write_uint32(self.unknown_same_3)
        odf.write_uint32(self.unknown_same_4)
        odf.write_uint8(self.unknown_zeroes_1)
        odf.write_uint8(self.unknown_zeroes_2)
        odf.write_uint8(self.unknown_zeroes_3)
        odf.write_uint8(self.unknown_zeroes_4)
        odf.write_uint8(self.unknown_zeroes_5)
        odf.write_varint(self.unknown_7)

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

        odf.write_varint(self.unknown_offset)

        if self.unknown_offset > 0:
            self.pwdt.write_to(odf)
            for value in self.unknown_end_bytes:
                odf.write_uint8(value)
            self.beha.write_to(odf)
            self.entities.write_to(odf)


    def _to_json(self):
        my_dict = {}
        self._json_simple(my_dict, [
            'flag',
            'location',
            'another_location',
            'unknown_1',
            'unknown_2',
            'unknown_3',
            'unknown_4',
            'active_crew',
            'unknown_5',
            'unknown_6',
            'unknown_same_1',
            'unknown_same_2',
            'unknown_same_3',
            'unknown_same_4',
            'unknown_zeroes_1',
            'unknown_zeroes_2',
            'unknown_zeroes_3',
            'unknown_zeroes_4',
            'unknown_zeroes_5',
            'unknown_7',
            ])
        my_dict['difficulty'] = self.difficulty.to_json()
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
            'unknown_offset',
            ])
        if self.unknown_offset > 0:
            my_dict['pwdt'] = self.pwdt.to_json()
            my_dict['unknown_end_bytes'] = self.unknown_end_bytes
            my_dict['beha'] = self.beha.to_json()
            my_dict['entities'] = self.entities.to_json()
        return my_dict


class Savefile(Datafile):

    # Maximum savefile version that we can parse
    MAX_VERSION = 1

    def __init__(self, filename, do_write=False):
        super().__init__(filename, do_write=do_write)
        if not do_write:
            self._read()


    def _json_simple(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = getattr(self, attr)


    def _json_object_arr(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = []
            for element in getattr(self, attr):
                target_dict[attr] = element.to_json()


    def _json_object_single(self, target_dict, attrs):
        for attr in attrs:
            target_dict[attr] = getattr(self, attr).to_json()


    def _read(self):

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
        self.crew = []
        num_crew = self.read_uint8()
        for _ in range(num_crew):
            self.crew.append(self.read_string())

        # And then another, shorter crew list.  Weird
        self.crew_subset = []
        num_crew_subset = self.read_uint8()
        for _ in range(num_crew_subset):
            self.crew_subset.append(self.read_string())

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

        # Any remaining data at the end that we're not sure of
        self.remaining_loc = self.tell()
        self.remaining = self.read()
        self.finish_remaining_string_registry()

        # Sanity check: make sure that, were we to write the file back right now, it
        # remains identical to the input
        test = self._prep_write_data()
        test.seek(0)
        test_data = test.read()
        if self.data != test_data:
            with open('debug_out.sav', 'wb') as odf:
                odf.write(test_data)
            raise RuntimeError('Could not reconstruct an identical savefile, aborting!')

    def _prep_write_data(self, filename=None):
        if filename is None:
            filename = self.filename
        odf = Savefile(filename, do_write=True)

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
        odf.write_uint8(len(self.crew))
        for crew in self.crew:
            odf.write_string(crew)

        # Crew subset
        odf.write_uint8(len(self.crew_subset))
        for crew in self.crew_subset:
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

        # Any remaining data at the end that we're not sure of
        #odf.write(self.remaining)
        for segment in self.remaining_categorized:
            if type(segment) == bytes:
                odf.write(segment)
            elif type(segment) == str:
                odf.write_string(segment)
            else:
                raise RuntimeError(f'Unknown segment type in remaining data: {type(segment)}')

        # Now fix the checksum
        new_checksum = binascii.crc32(odf.getvalue()[9:])
        odf.seek(5)
        odf.write_uint32(new_checksum)

        # ... and return
        return odf


    def save_to(self, filename):
        odf = self._prep_write_data(filename)
        odf.save()


    def to_json(self):
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
            ])
        self._json_simple(my_dict, [
            'crew',
            'crew_subset',
            ])
        if self.rede is not None:
            self._json_object_single(my_dict, [
                'rede',
                ])
        self._json_object_single(my_dict, [
            'loot_tables',
            'lode',
            'ship_location',
            'missions',
            ])

        return my_dict


    def _read_remaining_varint(self, pos):
        """
        Reads a varint from our remaining data.  This duplicates the logic
        from `datafile.read_varint`, but that function likes working on
        a file-like object, whereas this one's operating on a chunk of
        bytes.  Arguably we could normalize things so that we could use
        a single function, but we'll cope for now.  If I ever get through
        the whole savefile format, I should be able to strip this out
        entirely.
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
        `remaining_categorized` list and advance the current position.

        This duplicates a fair bit of logic from `datafile.read_string`, but
        needs to do various things differently due to the circumstances of
        remaining-data processing, so we'll cope for now.  If I ever get
        through the whole savefile format, I should be able to strip this
        out entirely.
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
            string_val = string_val.decode(self.encoding)
            if not self.valid_string_re.match(string_val):
                # Doesn't look like a string!
                return False
            if string_val in self.string_registry_read_seen:
                # We've already seen this string; that would mean that both are
                # probably false positives.  Not a big deal, but we'll avoid
                # storing this duplicate as a string
                return False
            # Finally, we're as sure as we can be that this is a valid string.
            # Even if it's a false positive, we should be safe writing it out as
            # a string later, since that'll result in the same byte sequence,
            # and nothing would be referencing it unless there's a *really*
            # unlucky coincidence.
            #print(f' <- {string_val}')

            # Store any data from before the string
            if self.remaining_last_pos < self.remaining_cur_pos:
                self.remaining_categorized.append(self.data[self.remaining_last_pos:self.remaining_cur_pos])

            # Store the string
            self.string_registry_read[my_pos] = string_val
            self.string_registry_read_seen.add(string_val)
            self.remaining_categorized.append(string_val)

            # Update current position
            self.remaining_cur_pos = my_pos + strlen
            self.remaining_last_pos = self.remaining_cur_pos
            return True
        else:
            # Potential string reference; take a peek
            target_pos = second_val_pos-second_val
            if target_pos in self.string_registry_read:
                destination_string = self.string_registry_read[target_pos]
                if len(destination_string) != strlen:
                    # String lengths don't match; this is a false positive!
                    return False
                # Now it's almost assured that we've reached a valid string reference.
                # Store it!
                #print(f' -> {destination_string}')

                # Store any data from before the string
                if self.remaining_last_pos < self.remaining_cur_pos:
                    self.remaining_categorized.append(self.data[self.remaining_last_pos:self.remaining_cur_pos])

                # Now store the string
                self.remaining_categorized.append(destination_string)

                # Update current position
                self.remaining_cur_pos = my_pos
                self.remaining_last_pos = self.remaining_cur_pos
                return True
            else:
                return False


    def finish_remaining_string_registry(self):
        """
        So it's unlikely that I'm going to end up decoding the *entire*
        savefile, and even if it eventually happens, I am certainly not
        going to finish that process for some time.  This leaves me with
        the problem of string references in the "remaining" bit of the
        save that I haven't processed.  Namely: any edit I make in here
        which changes the length of the file in any way is almost
        certainly going to break string references after the edit.  There
        are string references very near the end of 300kb saves which
        reference early-save strings, etc.

        So, what to do?  Well: *detecting* string references in the file
        is actually not a huge problem.  Detecting string definitions is
        a bit prone to false-positives, but we don't really have to worry
        about that too much -- a reference will point back to a string
        we've seen earlier on, and we can match on the strlen for an even
        stronger match.  The chances of false positives on the reference
        detection is, IMO, low enough that it's not worth worrying about.

        The plan, then: once I get to the "remaining" data bit, brute-force
        search the remaining data for more strings and string references,
        making a list of string references as I go.  Then when we write
        out the file, instead of just blindly writing out the remaining data,
        we'll have to go through and update them as-needed.  Kind of a pain,
        but I think it should be safe to do, and allow this util to be
        Actually Useful.

        Anyway, this function is the bit which scans the remaining data and
        finishes filling out our `string_registry_read` dict.  It'll also
        create a new list of string references so we can reconstruct later.
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
        self.valid_string_re = re.compile(r'^[-a-zA-Z0-9_]+$')

        # We're going to break the remaining data up into bit: a
        # list whose elements will either be `bytes` or `str`.  `bytes`
        # entries will be written as-is; `str` objects will be handled
        # as strings.
        self.remaining_categorized = []

        # Start looping
        self.remaining_cur_pos = self.remaining_loc
        self.remaining_last_pos = self.remaining_loc
        while self.remaining_cur_pos < self.data_len:
            if not self._check_remaining_string():
                self.remaining_cur_pos += 1

        # Categorize any data after the last string value
        if self.remaining_last_pos < self.data_len:
            self.remaining_categorized.append(self.data[self.remaining_last_pos:])


