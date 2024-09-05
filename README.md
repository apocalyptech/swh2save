DISCLAIMER
==========

This is in an alpha state; very much still in development.  It's starting to
get some decent functionality, and it's been awhile since I've generated
a corrupt savefile, but definitely don't think this is a finished product!
Back up your saves and use with caution!  One known deficiency: it *cannot*
deal with mid-mission savegames.  At the moment, only feed it saves from
outside missions.

SteamWorld Heist II CLI Save Editor
===================================

This is a Python-based CLI save editor for the excellent
[SteamWorld Heist II](https://store.steampowered.com/app/2396240) from
Thunderful Development.

Given the early state of development, and the fact that I'm still not
completely sure about it consistently generating valid saves, I'm not
including any usage instructions at the moment.  If you're familiar enough
with running Python stuff from commandline, though, feel free to give it
a go!

At time of writing, here's the stuff you can edit:
- Water (money)
- Fragments
- Upgrades:
  - Sub Upgrade panel
  - Job Upgrade panel
  - Various other item-based upgrades (sub dive/ram, etc)
  - Personal Upgrades
- Inventory
  - Weapons
  - Equippable Gear
  - Sub Equipment
  - Key Items
  - Hats!
- Revealing the full map
- Unlocking Crew
- Setting Crew Job XP
- Spending Reserve XP
- Refresh Crew/Equipment so they can be used again on the same day

I may not be the best at keeping this README updated while still in
development, so it's possible there'll be more stuff by the time you read
this.

WARNING
=======

Due to the nature of the savegame format (see below in the Format Info
section), and the fact that this utility doesn't actually understand the entire
format yet, edits performed to your savegames have a small but nonzero chance
of resulting in corrupted savegames.  I believe the risk is extremely small,
but keep it in mind!  Even if previous similar edits have worked fine, it's
possible that this could encounter an edge case which results in an invalid
save file.  Keep backups of your saves, and use with caution!

Note too that one known deficiency of the utility is that it currently *cannot*
cope with mid-mission savegames.  I believe it'll probably fail before it's even
had a chance to read those in, but definitely don't use the utility on mid-mission
savegames; they are likely to end up corrupted even if the process finishes.

TODO
====

- Pull `string_finder.py` into the module
- Add arg to write out savefiles with all strings expanded
  - The code for this is technically in place but commented out.  It turns out
    that the increased number of strings makes false positives on references
    likely enough that I actually ran into it on at least one of my saves.
    Will keep this commented until I get the rest of the file parsed so we
    can jettison the string searching altogether.
- Crew levelling could use a bit more thorough testing
- Grab a few in-mission saves; I'm pretty sure we error out trying to read them.
  I have no real interest in trying to actually *parse* the in-mission bits,
  but perhaps we could at least detect them more gracefully and fail out with
  a useful message to the user.
- README docs!
- Explicit arg to write debug savefile when our rewrite sanity check fails,
  rather than just blindly writing `debug_out.sav`
- Put in a *sensible* way to create new Chunk objects; my current implementation
  makes that super awkward.
- Finish parsing the remainder of the file.  I actually came across a scenario
  where a detected string ref was a false positive while testing out the string
  expansion (see above).  Still a pretty rare occurrence, but I don't think I'll
  feel 100% about things until that's done.

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

That backwards-string-referencing poses some problems for save editing, namely that
any change in file length (such as adding an inventory item or hat, etc) will break
any future string backreference unless it gets fixed.  For areas of the savegame that
we've parsed out already, that's trivial and happens automatically by the
string-handling functions, but at time of writing, the whole savegame format is *not*
known (and I doubt I'll ever get to the point of having it 100% mapped).  If we write
out a save with those references broken, it'll result in the game saying that the
save is corrupt, and refusing to load it (which is certainly fair!)

So, what to do about it, if I want to be able to make arbitrary edits without having
the whole file mapped?  What I settled on was doing a bruteforce search through the
remaining save data to look for string definitions and string references, and then
run those through our usual string-handling functions on the backend.  The detection
for string definitions is at least somewhat prone to false-positives, but IMO those
aren't problematic; the data will still be written out identically even if we think
something's a string which isn't.  The detection for string references is, I believe,
unlikely to yield false positives, since it must match on both string length and the
exact back-reference length matching up.  IMO we'd have to be super unlucky to encounter
a case where some arbitrary binary data happened to look like a valid string reference.
So, that's what we're doing.  The chance of it causing problems is nonzero, and I've
added a pretty strongly-worded warning on the CLI output, but for now that'll have to
do!

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

