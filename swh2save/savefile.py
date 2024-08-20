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

import abc
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

        # Next up, item IDs of some sort?  This uses varints; I wonder how
        # often those are technically used in other places that I may have
        # missed...
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

    def __init__(self, df):
        super().__init__(df, 'ItIn')

        self.unknown_1 = self.df.read_uint8()
        # This one, at least, definitely seems to be a varint -- see savegame_000.dat-17
        self.unknown_2 = self.df.read_varint()
        self.unknown_3 = self.df.read_uint32()

        self.name = self.df.read_string()
        #print(f' - Got name: {self.name}')

        self.unknown_4 = self.df.read_uint32()
        self.unknown_5 = self.df.read_uint32()


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_1)
        odf.write_varint(self.unknown_2)
        odf.write_uint32(self.unknown_3)
        odf.write_string(self.name)
        odf.write_uint32(self.unknown_4)
        odf.write_uint32(self.unknown_5)


    def __str__(self):
        return str(self.name)


class Inventory(Chunk):
    """
    `Inve` chunk -- Inventory!
    """

    def __init__(self, df):
        super().__init__(df, 'Inve')

        self.unknown_1 = self.df.read_uint8()
        self.unknown_2 = self.df.read_uint32()

        # On to the inventory...
        self.items = []
        num_items = self.df.read_varint()
        for _ in range(num_items):
            self.items.append(InventoryItem(self.df))
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


    def _write_to(self, odf):

        odf.write_uint8(self.unknown_1)
        odf.write_uint32(self.unknown_2)

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


#class Loadout(Chunk):
#    """
#    `CrLo` chunk -- Character Loadout?  Possibly stretching a bit
#    with the name there.
#    """
#
#    def __init__(self, df):
#        super().__init__(df, 'CrLo')
#
#        self.unknown_1 = self.df.read_uint8()
#        self.name = self.df.read_string()
#
#        import sys
#        sys.exit(0)
#
#
#    def _write_to(self, odf):
#
#        odf.write_uint8(self.unknown_1)
#        odf.write_string(self.name)


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

        # Character Loadout
        #self.loadouts = []
        #num_chars = self.read_uint8()
        #for _ in range(num_chars):
        #    self.loadouts.append(Loadout(self))

        # Any remaining data at the end that we're not sure of
        self.remaining_loc = self.tell()
        self.remaining = self.read()

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

        # Any remaining data at the end that we're not sure of
        odf.write(self.remaining)

        # Now fix the checksum
        new_checksum = binascii.crc32(odf.getvalue()[9:])
        odf.seek(5)
        odf.write_uint32(new_checksum)

        # ... and return
        return odf


    def save_to(self, filename):
        odf = self._prep_write_data(filename)
        odf.save()

