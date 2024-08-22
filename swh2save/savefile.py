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
        self.unknown_3 = df.read_uint32()

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
        odf.write_uint32(self.unknown_3)
        odf.write_uint8(self.small_unknown_1)
        odf.write_uint8(self.small_unknown_2)
        odf.write_uint8(self.small_unknown_3)
        odf.write_uint8(self.small_unknown_4)
        odf.write_uint8(self.small_unknown_5)
        odf.write_string(self.cur_campaign_state)
        odf.write_uint8(self.small_unknown_6)


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

        # No clue what this data is
        self.unknown_arr = []
        num_unknown_arr = self.df.read_varint()
        for _ in range(num_unknown_arr):
            self.unknown_arr.append(self.df.read_varint())
            #print(f' - Got unknown: {self.unknown_arr[-1]} ({len(self.unknown_arr)}/{num_unknown_arr})')

        # Another unknown varint array
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

        # Unknown array
        odf.write_varint(len(self.unknown_arr))
        for unknown in self.unknown_arr:
            odf.write_varint(unknown)

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


    def add_item(self, item_name, item_flags):
        """
        Adds a new item with the given name to our inventory
        """
        self.last_inventory_id += 1
        self.items.append(InventoryItem.create_new(self.last_inventory_id, item_name, item_flags))


class ReDe(Chunk):
    """
    `ReDe` chunk.
    I'm *pretty* sure this is basically just a list of characters who are
    ready to go (ie: ReDe); at first glance it seems to mostly just contain
    a list of chars we haven't recruited yet.  Not totally sure, though.
    """

    def __init__(self, df):
        super().__init__(df, 'ReDe')

        # Seems to always be zero (this seems quite common after chunk
        # identifiers, actually)
        self.zero = self.df.read_uint8()

        self.chars = []
        num_chars = self.df.read_varint()
        for _ in range(num_chars):
            self.chars.append(self.df.read_string())

        # On my saves, ranges from 0-4.  Bigger values in general when
        # there are more ready chars in the list, though that's not
        # entirely predictive.
        self.unknown = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.zero)
        odf.write_varint(len(self.chars))
        for char in self.chars:
            odf.write_string(char)
        odf.write_uint32(self.unknown)


class Savefile(Datafile):

    # Maximum savefile version that we can parse
    MAX_VERSION = 1

    def __init__(self, filename, do_write=False):
        super().__init__(filename, do_write=do_write)
        if not do_write:
            self._read()

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


