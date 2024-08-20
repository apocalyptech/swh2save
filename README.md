DISCLAIMER
==========

This is very pre-alpha, and still in development.  At the moment it can't do
much of use really; time will tell if it gets more fully-functional!

SteamWorld Heist II CLI Save Editor
===================================

This is a Python-based CLI save editor for the excellent
[SteamWorld Heist II](https://store.steampowered.com/app/2396240) from
Thunderful Development.

At time of writing, as the disclaimer above mentions, it is pre-alpha and
can't do much.  As such, I will *not* be including usage instructions and
the like, though if you're familiar enough with running Python stuff from
commandline, feel free to give it a go!  At the moment its only actual
editing capability is water (money) and fragments, though.

Format Info
===========

Just some general notes on the format, for anyone else who may be interested
in looking at it.  The code here should be pretty straightforward, though I'll
note down a few specifics.

First off: the save format uses [varints](https://en.wikipedia.org/wiki/Variable-length_quantity)
quite a bit.  If you see something that looks like a u8/u16 in the file, it's
likely to actually be a varint.  Take the byte value and mask/`&` it with`0x7F`
to get the base value, then check the top bit (mask `0x80`).  If it's set,
read the next byte, applying the same mask before shifting its value seven bits.
Check its top bit and continue as-needed.

The file appears to be arranged into chunks with four-ASCII-letter headers.  `Difc`
for difficulty settings, `Inve` for inventory, etc.  These are likely to be
nested in many cases (such as having multiple `ItIn` chunks inside an `Inve` chunk,
one for each item).  It may be difficult to guess exactly where nesting might be
happening (for instance, I'm not really sure how much info is technically inside
the `Head` header chunk, and how much is just "in" the main savefile).

Reading strings from the file takes a bit of extra effort.  The format re-uses
string data to save on space, so once a string has been written to a file, you won't
see it again later on, even if something else references the same string.  When you
encounter a string record, the first varint is the string length.  Then the *next*
varint is potentially a pointer to where the string lives inside the file.  If
that second value is zero, just read the appropriate number of bytes (based on that
first length) and you're good.  If that second varint is >0, though, it specifies
the number of bytes *backwards* you need to read in the file (starting from the
location of the pointer/second-number varint) to get to the string data.

That backwards-string-referencing is, I *think*, what's getting in the way of some
edits for me at the moment.  I can change simple things like water/fragements, but
if I try to add a new string to the sub-upgrade array or collected-hats array, for
instance, the game won't load the file, claiming that it's corrupt.  I *suspect* that
it's because any future string references after the array whose length I changed
now no longer point at the proper spot, since they were relative offsets.  It could
be that it's something else causing problems, of course, but that's my current theory.

The somewhat annoying upshot of that is that if that *is* the problem I'm having with
modifying those arrays, it seems like I may have to decode nearly all of the save
data in order to be able to safely make changes to those arrays.  The editor would
have to understand the syntax far enough along to at least make it past the *last*
backwards string reference.  In SWH1, they didn't do any of this backwards-referencing,
so that utility was able to just *stop* once we were through the data I cared about,
and it was fine.  Possibly not so with this one!

And, of course, it's possible that the issue I was having with altering arrays was
due to some other problem, too.  There's a lot of unknown values in there at the moment.
If anyone ends up figuring out something about all this, please let me know!

The only other thing to mention is the savefile header.  The first four bytes are the
magic ASCII value `SWH2`.  The next byte (maybe a varint?) is, I assume, the savefile
version number (currently `0x01` at time of writing).  Might be worth checking that, if
writing your own tools.  The next four bytes are a standard
[CRC32](https://en.wikipedia.org/wiki/Cyclic_redundancy_check) checksum, computed against
the bulk of the save data which occurs *after* the checksum (so, starting at byte 9).
Then the first `Head` chunk starts right at `0x9`.

License
=======

`swh2save` is licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
A copy can be found at [LICENSE.txt](LICENSE.txt).

