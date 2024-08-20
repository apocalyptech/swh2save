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

class Datafile:

    def __init__(self, filename, do_write=False, encoding='utf-8', endian='<'):
        """
        We're essentially hardcoding utf-8 string encoding and little-endianness,
        though those can technically be overridden.  I suspect that the strings
        we read in the file are just plain ol' ASCII, and `latin1` for encoding
        might be more appropriate.  I guess I'm sticking with utf-8 for now, though.
        """
        self.filename = filename
        # TODO: would be nice to figure out what the proper encoding actually is
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
                self.df = io.BytesIO(self.data)
            self.df.seek(0)

        # The savefile format saves space by only storing strings once, and referring
        # back to previous locations if the string pops up again.
        self.string_registry_read = {}
        self.string_registry_write = {}

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
        data = 0
        cur_shift = 0
        keep_going = True
        while keep_going:
            new_byte = self.read_uint8()
            data |= ((new_byte & 0x7F) << cur_shift)
            if new_byte & 0x80 == 0x80:
                cur_shift += 7
            else:
                keep_going = False
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

        We're actually using the "string length" as a byte length, and then
        interpreting the bytes to utf-8.  That may or may not be appropriate;
        I suspect that the strings we read from here might all be ASCII.  If
        I later discover that latin1 is a more-appropriate encoding, I could
        be a little less careful about some of that (like how the
        `string_registry_read` dict currently stores a tuple).
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
            try:
                decoded = data.decode(self.encoding)
                # Storing a tuple here so that we can compare the binary string length properly
                # later on.  I suspect that there's never a case where a reference would point
                # to a *substring*, but we're checking for that case anyway (though we
                # RuntimeError at the moment if we *do* ever find a substring being attempted).
                # If the proper text encoding turns out to be latin1, we could do without the tuple.
                self.string_registry_read[string_loc] = (data, decoded)
                return decoded
            except UnicodeDecodeError as e:
                raise RuntimeError(f'Unable to decode string: {data} -> {e}')
        else:
            target_loc = second_val_loc-second_val
            if target_loc in self.string_registry_read:
                destination_data, destination_string = self.string_registry_read[target_loc]
                if len(destination_data) != strlen:
                    # As mentioned above, I don't *think* that this will ever get hit, but
                    # we're checking for it anyway 'cause I'd want to check it out, if it
                    # ever does happen.
                    raise RuntimeError(f"String redirect length at 0x{initial_loc:X} ({strlen}) doesn't match cached length ({len(destination_data)})")
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
            if data in self.string_registry_write:
                self.write_varint(self.tell() - self.string_registry_write[data])
            else:
                # Technically a varint but whatever
                self.write_uint8(0)
                self.string_registry_write[data] = self.tell()
                self.write(data)

    def write_chunk_header(self, value):
        assert(len(value) == 4)
        self.write(value.encode(self.encoding))

