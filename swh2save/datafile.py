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

import io
import os
import struct

class StringRegistry:
    """
    The savefile format saves space by only storing strings once, and referring
    back to previous locations if the string pops up again.  This class just holds
    a few variables we use for keeping track of this (separate ones for reading
    + writing).

    Ideally we should probably pull all the string handling in here, but it's
    historically been right in Datafile and I don't feel like refactoring it over
    here.  I've wrapped these up in their own class because it turns out that
    the "skippable" section (starting with PWDT and proceeding until PBar) uses
    its own separate string registry, so I wanted to be able to flip between 'em
    easily.

    Note that since implementing this, the app has stopped processing any strings
    inside that "skippable" section, so this abstraction wasn't really needed.
    """

    def __init__(self):
        self.read_lookup = {}
        self.read_strings_seen = set()
        self.write_lookup = {}


class Datafile:

    def __init__(self, filename, do_write=False, encoding='latin1', endian='<'):
        """
        We're essentially hardcoding latin1 string encoding and little-endianness,
        though those can technically be overridden.  I suspect that the strings
        we read in the file are just plain ol' ASCII.  Looping through the various
        top-level names in Definitions/*.xml, I'm pretty confident we'll be fine
        with just latin1.
        """
        self.filename = filename
        self.encoding = encoding
        self.endian = endian
        self.struct_uint8 = f'{self.endian}B'
        self.struct_uint16 = f'{self.endian}H'
        self.struct_uint32 = f'{self.endian}I'
        if do_write:
            self.data = None
            self.df = io.BytesIO()
        else:
            with open(self.filename, 'rb') as temp_df:
                self.data = temp_df.read()
                self.data_len = len(self.data)
                self.df = io.BytesIO(self.data)
            self.df.seek(0)

        # The "skippable" section in our data handles strings completely isolated
        # from the main file, so we're setting up two StringRegistry objects we
        # can flip between.  Note that we've since stopped handling strings inside
        # that section at all, since we don't care about any data beyond the
        # cloudcover, at the moment.
        self.sr_default = StringRegistry()
        self.sr_skipped = StringRegistry()
        self.set_default_string_registry()

    def set_default_string_registry(self):
        """
        Switch back to the "default" string registry
        """
        self.sr = self.sr_default

    def set_skipped_string_registry(self):
        """
        Switch to the "skipped" area string registry.  Note that this is currently
        not actually used, since we stopped processing enough of that area to
        require string handling.
        """
        self.sr = self.sr_skipped

    def seek(self, offset, whence=os.SEEK_SET):
        self.df.seek(offset, whence)

    def tell(self):
        return self.df.tell()

    def close(self):
        self.df.close()

    def read(self, size=-1):
        return self.df.read(size)

    def write(self, b):
        return self.df.write(b)

    def getvalue(self):
        return self.df.getvalue()

    def save(self):
        self.df.seek(0)
        with open(self.filename, 'wb') as odf:
            odf.write(self.read())

    def read_uint8(self):
        return struct.unpack(self.struct_uint8, self.read(1))[0]

    def read_uint16(self):
        return struct.unpack(self.struct_uint16, self.read(2))[0]

    def read_uint32(self):
        return struct.unpack(self.struct_uint32, self.read(4))[0]

    def read_varint(self):
        """
        The save format uses varints quite a bit; I suspect that many of
        the places where I'm reading something as a u8 are actually
        supposed to be varints.
        """
        iter_count = 0
        data = 0
        cur_shift = 0
        keep_going = True
        while keep_going:
            if iter_count >= 4:
                # If we've gone more than four bytes, there's no way
                # it's a value we care about.
                raise RuntimeError(f'Runaway varint detected at 0x{self.tell()-iter_count:X}')
            new_byte = self.read_uint8()
            data |= ((new_byte & 0x7F) << cur_shift)
            if new_byte & 0x80 == 0x80:
                cur_shift += 7
            else:
                keep_going = False
            iter_count += 1
        return data

    def read_string(self):
        """
        Strings are a bit complex.  The first varint is the string length,
        and then the next varint is a potential offset to a location in the
        save where the string already exists, which is presumably just done
        as a space-saving mechanism.  If that second varint is zero, just
        read however many bytes there were.  Otherwise, use that offset to
        go backwards in the file to find the original string reference.

        I suspect that the game will never attempt to read a substring this
        way (ie: specifying a shorter string length on the reference record
        than there was on the string that it's pointing to), though we check
        for it anyway (though throw an error if found, because I'd like to
        confirm).

        We've moved to using latin1 for string encoding, which means the
        byte length will be identical to the string length.  If we ever end
        up needing to use something fancier like utf-8, we may need to keep
        track of byte-vs-string-length differences.  See the state of this
        function as of here, for an example which should work:

            https://github.com/apocalyptech/swh2save/blob/cadc382be834a68ef741af345c2b589cbafe1cc4/swh2save/datafile.py#L103
        """
        initial_loc = self.tell()
        strlen = self.read_varint()
        if strlen == 0:
            return None
        second_val_loc = self.tell()
        second_val = self.read_varint()
        if second_val == 0:
            string_loc = self.tell()
            data = self.read(strlen)
            decoded = data.decode(self.encoding)
            self.sr.read_lookup[string_loc] = decoded
            self.sr.read_strings_seen.add(decoded)
            return decoded
        else:
            target_loc = second_val_loc-second_val
            if target_loc in self.sr.read_lookup:
                destination_string = self.sr.read_lookup[target_loc]
                if len(destination_string) != strlen:
                    # I don't believe there will ever be a case where the string reference
                    # requests a "substring" of the original string, but we're checking for
                    # the length here, regardless.  Raising an exception because I'd want
                    # to check it out to make sure that the real problem wasn't something else.
                    raise RuntimeError(f"String redirect length at 0x{initial_loc:X} ({strlen}) doesn't match cached length ({len(destination_string)})")
                return destination_string
            else:
                raise RuntimeError(f'Computed string redirect at 0x{second_val_loc:X} (-> 0x{target_loc:X}) not found')

    def read_chunk_header(self):
        return self.read(4).decode(self.encoding)

    def write_uint8(self, value):
        self.write(struct.pack(self.struct_uint8, value))

    def write_uint16(self, value):
        self.write(struct.pack(self.struct_uint16, value))

    def write_uint32(self, value):
        self.write(struct.pack(self.struct_uint32, value))

    def write_varint(self, value):
        while True:
            to_write = value & 0x7F
            value >>= 7
            if value > 0:
                to_write |= 0x80
            self.write(struct.pack(self.struct_uint8, to_write))
            if value == 0:
                break

    def write_string(self, value):
        if value is None:
            self.write_uint8(0)
        else:
            data = value.encode(self.encoding)
            self.write_varint(len(data))
            if data in self.sr.write_lookup:
                self.write_varint(self.tell() - self.sr.write_lookup[data])
            else:
                # Technically a varint but whatever
                self.write_uint8(0)
                self.sr.write_lookup[data] = self.tell()
                self.write(data)


    def write_chunk_header(self, value):
        assert(len(value) == 4)
        self.write(value.encode(self.encoding))

