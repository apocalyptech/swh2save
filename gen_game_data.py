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
import io
import sys
import zipfile
import datetime
import textwrap

import xml.etree.ElementTree as ET


def quote_string(string, to_quote='"'):
    """
    Quote a string which is being passed inside our constructed Python code.
    This is pretty stupid, but since this stuff gets looked-over by hand
    after generation, it's good enough for me.
    """
    return string.replace(to_quote, f'\\{to_quote}')


def main():

    # TODO: I'd eventually like to make this more general, autodetect install
    # locations, and at least attempt to make it cross-platform.

    game_dir = '/games/Steam/steamapps/common/SteamWorld Heist 2'
    language = 'en'
    
    core_dir = os.path.join(game_dir, 'Bundle', 'Core')

    output_file = os.path.join('swh2save', 'gamedata.py')

    with open(output_file, 'w') as odf:

        print('# File has been autogenerated by gen_game_data.py', file=odf)
        print('# Generated on: {}'.format(
            datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
            ), file=odf)
        print("# Don't edit by hand!", file=odf)
        
        print(textwrap.dedent("""
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


            class GameData:

                def __init__(self, name, label):
                    self.name = name
                    self.label = label

                def __str__(self):
                    return f'{self.label} ({self.name})'

                def __lt__(self, other):
                    if isinstance(other, GameData):
                        return self.label.casefold() < other.label.casefold()
                    else:
                        return self.label.casefold() < other.casefold()

                def __gt__(self, other):
                    if isinstance(other, GameData):
                        return self.label.casefold() > other.label.casefold()
                    else:
                        return self.label.casefold() > other.casefold()


            class ShipUpgrade(GameData):

                def __init__(self, name, label, keyitem, category):
                    super().__init__(name, label)
                    self.keyitem = keyitem
                    self.category = category


            class Hat(GameData):

                def __init__(self, name, label):
                    super().__init__(name, label)

            """), file=odf)

        with zipfile.ZipFile(os.path.join(core_dir, 'Game.pak')) as game_pak:

            # First up: load in strings for our selected language
            # TODO: really I should be supporting all languages the game supports.
            # I realize that doing this from the start is almost certainly simpler
            # than doing it later, but I'm feeling lazy in the short-term.
            labels = {}
            with game_pak.open(f'Language/{language}.csv') as language_csv:
                # Not actually using a CSV processor.  Will I regret it?  Time will tell!
                text_file = io.TextIOWrapper(language_csv)
                for line in text_file:
                    line = line.strip()
                    if line == '':
                        continue
                    if line.startswith('#'):
                        continue
                    parts = line.split("\t")
                    # The fields seem to be: key, translation, comment
                    # comment is optional
                    if len(parts) < 2:
                        continue
                    labels[parts[0]] = parts[1]


            # Get a list of keyitems; not storing these separately, but we want 'em
            # for the ship-upgrade handling
            keyitems = {}
            with game_pak.open('Definitions/key_items.xml') as keyitem_xml:
                root = ET.fromstring(keyitem_xml.read())
                for child in root:
                    if 'Abstract' in child.attrib:
                        continue
                    loc_name = child.attrib['Name']
                    for inner_child in child:
                        if inner_child.tag == 'LocalizedNameId':
                            loc_name = inner_child.text
                            break
                    keyitems[child.attrib['Name']] = labels[loc_name]


            # Now a list of ship upgrades
            # TODO: get English labels for these as well
            with game_pak.open('Definitions/ship_upgrades.xml') as ship_upgrades:

                print('SHIP_UPGRADES = {', file=odf)
                root = ET.fromstring(ship_upgrades.read())
                upgrade_template_types = {}
                for child in root:
                    if 'Abstract' in child.attrib:
                        for inner_child in child:
                            if inner_child.tag == 'Type':
                                upgrade_template_types[child.attrib['Name']] = inner_child.text
                                break
                        continue
                    keyitem = None
                    optional_layer = None
                    upgrade_type = None
                    for inner_child in child:
                        if inner_child.tag == 'KeyItem':
                            keyitem = inner_child.text
                        elif inner_child.tag == 'ShowOptionalLayer':
                            optional_layer = inner_child.text
                        elif inner_child.tag == 'Type':
                            upgrade_type = inner_child.text
                    if optional_layer is not None:
                        label = labels[optional_layer]
                    elif keyitem is not None:
                        label = keyitems[keyitem]
                    else:
                        label = child.attrib['Name']
                    if upgrade_type is None \
                            and 'Template' in child.attrib \
                            and child.attrib['Template'] in upgrade_template_types:
                        upgrade_type = upgrade_template_types[child.attrib['Template']]
                    print("        '{}': ShipUpgrade(".format(child.attrib['Name']), file=odf)
                    print("            '{}',".format(child.attrib['Name']), file=odf)
                    print("            \"{}\",".format(quote_string(label)), file=odf)
                    if keyitem is None:
                        print("            None,", file=odf)
                    else:
                        print("            '{}',".format(keyitem), file=odf)
                    if upgrade_type is None:
                        print("            None,", file=odf)
                    else:
                        print("            '{}',".format(upgrade_type), file=odf)
                    print("            ),", file=odf)
                print('        }', file=odf)
                print('', file=odf)

            # Now hats!
            with game_pak.open('Definitions/hats.xml') as hat_xml:

                print('HATS = {', file=odf)
                root = ET.fromstring(hat_xml.read())
                for child in root:
                    if 'Abstract' in child.attrib:
                        continue
                    print("        '{}': Hat('{}', \"{}\"),".format(
                        child.attrib['Name'],
                        child.attrib['Name'],
                        quote_string(labels[child.attrib['Name']]),
                        ), file=odf)
                print('        }', file=odf)
                print('', file=odf)

    print(f'Wrote to: {output_file}')


if __name__ == '__main__':
    main()

