SteamWorld Heist II Save Format Info
====================================

The SWH2 savegame format was a fun one to decode!  Lots of neat little gotchas
here and there, and some various nonobvious things, but there's no actual
attempts at obfuscation or misdirection in there, and there are various
aspects of the format which made interpretation pretty easy in places.

This document will contain some general notes on the format, for anyone else
who may be interested in looking at it.  It mostly won't go into specific
details; for that, the sourcecode is probably the best reference.

File Header
-----------

The first four bytes are the magic ASCII value `SWH2`.  The next byte is, I
assume, the savefile version number (currently `0x01` at time of writing).
Might be worth checking that, if writing your own tools.  The next four bytes
are a standard [CRC32](https://en.wikipedia.org/wiki/Cyclic_redundancy_check)
checksum, computed against the bulk of the save data which occurs *after* the
checksum (so, starting at byte 9).  The actual savegame data starts at 
offset `0x9`.

Chunks
------

The file appears to be arranged into chunks with four-ASCII-letter headers.  `Difc`
for difficulty settings, `Inve` for inventory, etc.  These are likely to be
nested in many cases (such as having multiple `ItIn` chunks inside an `Inve` chunk,
one for each item).  It's often difficult to guess exactly where nesting might be
happening (for instance, I'm not really sure how much info is technically inside
the `Head` header chunk, and how much is just "in" the main savefile).

The "tree" in which I've chosen to represent the chunks looks like this, though
of course this may differ from how Thunderful do things on their end.  I've
included what I think the chunks are supposed to imply datawise:

- `Head` (Header)
  - `Difc` (Difficulty Settings)
  - `Difc` *(not sure why there are two of these chunks in here)*
- `Imh2` (not sure really)
- `GaRe` (Game Resources?)
- `Ship` (Ship/Sub Status)
- `Inve` (Inventory)
  - Array of `ItIn` (Inventory Item)
  - Array of `CrLo` (Character Loadout)
- *(optional)* `ReDe` (Resource Deck/Deque?)
- `LTma` (Loot Manager?)
  - Series of `LTde` arrays (Loot Deck/Deque)
    - `ReDe` (Resource Deck/Deque?)
- `LoDe` (Loot Deck/Deque)
  - Dict of `LoDD` (Loot Deck... Data?)
- `ShlD` (Ship/Sub Location)
- `MsnD` (Mission Data)
  - *(for in-Mission saves, has some leaves I have not decoded)*
  - `Difc`
- *(these next few may be skipped over on **very** early-game saves)*
  - `PWDT` (World Data of some sort)
    - Array of `MtBG` (revealed map data; no clue what "MtBG" itself is supposed to mean, though)
    - `Beha` (World Map Behavior States) *(not actually processed by this util)*
    - `ECSD` (World Map Entity Definitions) *(not actually processed by this util)*
  - Dict of `ECTa` (actually a collection of 70 different data types; I think
    the storage format might not be the same for all of them) *(not actually
    processed by this util)*
- Dict of `PBar` (Bar/Shop Market Status)
- `PeCo` (Persona/Crew Controller)
  - Dict of `Pers` (Persona/Crew status)
- `QstS` (Quests)
  - Array of `Qest` (Individual quest data)
  - Another array of `Qest`
  - Another more complicated array which includes `Qest` chunks
- `MiSt`
  - `MsCD` *(optional)*
- *(This is where I've stopped; there's at least some quest-related
  chunks afterwards)*

Practically, even though we have these chunk headers, you'll still have to read
and parse the file from start to end, for various reasons.  There is *one* instance
in the file where we're provided with an offset which lets us skip over a large
chunk of data, but that's definitely the exception and not the rule.

Varints
-------

The save format uses [varints](https://en.wikipedia.org/wiki/Variable-length_quantity)
quite a bit.  If you see something that looks like a u8/u16 in the file, it's
likely to actually be a varint.  Take the byte value and mask/`&` it with`0x7F`
to get the base value, then check the top bit (mask `0x80`).  If it's set,
read the next byte, applying the same mask before shifting its value seven bits.
Check its top bit and continue as-needed.

String Processing
-----------------

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

As an addendum, I should mention that I *have* run into a real false-positive for
the string reference detection, though it was when I was playing around with writing
out saves which *don't* save space with this re-use scheme, so there would have been
more opportunities for the false positive to crop up.  I mostly just mention it because
even though it *seems* super unlikely, it *is* something which might happen regardless.

Skippable Section
-----------------

Immediately after the `MsnD` chunk handling, the game stores a varint which is an
offset which can be used to skip over a large chunk of the file.  Various chunks
inside this section store strings, and use the same string-handling features
described above, but it's worth noting that they are entirely isolated from the
"main" file.  If the string `foo` was stored in the savegame, and then it's
encountered again inside this skippable area, the string `foo` will be written
out again.  Any future instances of `foo` inside the skippable area will refer
back to this newer instance.  Any instances *after* we're past the skippable
area will then start referring back to that original instance.  This is nice
because it decreases ambiguity and lets us process that area totally separately,
which is especially good when writing out the data.

(If the strings *weren't* isolated, we'd have to keep in mind that the back
references are varints, and so their exact values would depend on how many
bytes the initial "skip offset" took, which is itself a varint.  It would be
an edge case for sure, but you would otherwise potentially have to write out
the section multiple times, with different byte lengths for the offset, before
resolving the proper values.  Fortunately we don't have to worry about that.)

