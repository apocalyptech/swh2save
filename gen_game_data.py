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
import argparse

import xml.etree.ElementTree as ET


def quote_string(string, to_quote='"'):
    """
    Quote a string which is being passed inside our constructed Python code.
    This is pretty stupid, but since this stuff gets looked-over by hand
    after generation, it's good enough for me.
    """
    return string.replace(to_quote, f'\\{to_quote}')


def main():

    # TODO: There's various things this util (and the repo in general) should maybe
    # be doing instead of the way things happen now.  Some thoughts:
    #
    #  1. We *could* be reading in this information dynamically at runtime, rather
    #     than pre-generating data extracts.  I'd kind of like this util to be
    #     fully-functional even without a local SWH2 install, though, and this way
    #     we can't be surprised by changes to the game's data structures.
    #
    #  2. We could be storing this as TOML/JSON/YAML/whatever rather than a Python
    #     file.  At the moment I'm happy enough with Python, though.
    #
    #  3. Really we should be supporting all languages that SWH2 has translations
    #     for (at least for the data we're pulling out from here).  At the moment
    #     this only supports pulling a single location
    #
    #  4. Autodetection of game install location (check Steam config, etc).  Ideally
    #     supporting Windows as well.  This would be more important if we were
    #     reading the info dynamically at runtime.

    parser = argparse.ArgumentParser(
            description='Generate gamedata.py for swh2save',
            )

    parser.add_argument('-g', '--gamedir',
            type=str,
            default='/games/Steam/steamapps/common/SteamWorld Heist 2',
            help='Location of SWH2 install',
            )

    parser.add_argument('-l', '--language',
            type=str,
            default='en',
            help='The language to use for pulling in text labels',
            )

    args = parser.parse_args()
    
    core_dir = os.path.join(args.gamedir, 'Bundle', 'Core')

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


            class Experience:
                \"\"\"
                Holds information about what the XP requirements are for levels.  Note
                that this is *not* a GameData object.
                \"\"\"

                def __init__(self, xp_reqs):
                    \"\"\"
                    `xp_reqs` should be a list of the XP values required to unlock the
                    various levels
                    \"\"\"
                    self.xp_to_level = {}
                    self.level_to_xp = {}
                    for level, xp_req in enumerate(xp_reqs):
                        self.xp_to_level[xp_req] = level
                        self.level_to_xp[level] = xp_req
                        self.max_xp = xp_req
                        self.max_level = level


                def __len__(self):
                    return len(self.xp_to_level)


            class Job(GameData):

                def __init__(self, name, label, skills):
                    super().__init__(name, label)
                    self.skills = skills


            class Weapon(GameData):

                def __init__(self, name, label, job):
                    super().__init__(name, label)
                    self.job = job


            class Crew(GameData):

                def __init__(self, name, label, default_job):
                    super().__init__(name, label)
                    self.default_job = default_job


            class Upgrade(GameData):

                def __init__(self, name, label, keyitem, category):
                    super().__init__(name, label)
                    self.keyitem = keyitem
                    self.category = category


            class KeyItem(GameData):

                def __init__(self, name, label, upgrades=None):
                    super().__init__(name, label)
                    if upgrades is None:
                        self.upgrades = []
                    else:
                        self.upgrades = upgrades


            class Hat(GameData):
                pass


            class ShipEquipment(GameData):
                pass


            class Utility(GameData):
                pass

            """), file=odf)

        with zipfile.ZipFile(os.path.join(core_dir, 'Game.pak')) as game_pak:

            # We'll need this for a couple of data types
            weapon_job_mapping = {}

            # First up: load in strings for our selected language
            # TODO: really I should be supporting all languages the game supports.
            # I realize that doing this from the start is almost certainly simpler
            # than doing it later, but I'm feeling lazy in the short-term.
            labels = {}
            with game_pak.open(f'Language/{args.language}.csv') as language_csv:
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


            # Pull in some job information
            with game_pak.open('Definitions/jobs.xml') as job_xml:

                root = ET.fromstring(job_xml.read())

                # First up: Experience
                xp_reqs = ['0']
                first = root[0]
                for child in first:
                    if child.tag == 'ExperienceLevels':
                        for inner_child in child:
                            if inner_child.tag == 'Level':
                                # Not turning these into ints, since all we're doing
                                # is joining them as strings anyway.
                                xp_reqs.append(inner_child.text)
                        break
                if len(xp_reqs) == 0:
                    raise RuntimeError("Couldn't find XP->Level values")
                print('XP = Experience([{}])'.format(
                    ', '.join(xp_reqs),
                    ), file=odf)
                print('', file=odf)

                # Now the actual jobs themselves
                job_redirects = {}
                print('JOBS_REAL = {', file=odf)
                for child in root:
                    if 'Abstract' in child.attrib:
                        continue
                    name = child.attrib['Name']
                    label = labels[f'job_{name}']
                    job_redirects[name] = name
                    job_redirects[label.lower()] = name
                    skills = []
                    for inner_child in child:
                        if inner_child.tag == 'Upgrades':
                            for upgrade in inner_child:
                                upgrade_level = int(upgrade.attrib['Level'])
                                upgrade_name = upgrade.text
                                if upgrade_level+1 > len(skills):
                                    skills.append([])
                                skills[-1].append(upgrade_name)
                            break
                    print("        '{}': Job(".format(name), file=odf)
                    print("            '{}',".format(name), file=odf)
                    print("            \"{}\",".format(quote_string(label)), file=odf)
                    print("            [", file=odf)
                    for level in skills:
                        print("                [", file=odf),
                        for skill in level:
                            print("                    '{}',".format(skill), file=odf)
                        print("                    ],", file=odf)
                    print("                ],", file=odf)
                    print("            ),", file=odf)
                print('        }', file=odf)
                print('', file=odf)

                # And also, we want users to be able to be able to refer to jobs
                # by their in-game names.
                print('JOBS = {', file=odf)
                for job_usable, job_real in job_redirects.items():
                    print(f"        '{job_usable}': JOBS_REAL['{job_real}'],", file=odf)
                print('        }', file=odf)
                print('', file=odf)

            # Next up, what weapons belong to which jobs.  I'm storing this because
            # I want to be able to level up the "current" class for crew, and the
            # only real way to do that is via their weapon.  (I'll also want it for
            # unlocking crew, because I want to be able to give XP in their "default"
            # class, which is defined only by their default weapon.)
            with game_pak.open('Definitions/weapons.xml') as xml_data:

                # A list of weapons we know we don't want to bother with.  These are
                # virtualish weapons used as part of char skills, I think.  Shouldn't
                # ever show up in inventory lists
                known_weapon_skips = {
                        'weapon_utility_grenade_launcher_no_aimline',
                        'weapon_utility_grenade_launcher_crippled',
                        'weapon_utility_grenade_launcher_stun',
                        'weapon_utility_grenade_launcher_ice',
                        'weapon_utility_rocket_launcher_01',
                        'weapon_utility_rocket_launcher_02',
                        'weapon_utility_sidearm_01_aimline',
                        'weapon_action_stun_gun',
                        'weapon_action_diver_laser',
                        }

                print('WEAPONS = {', file=odf)
                root = ET.fromstring(xml_data.read())
                for child in root:
                    name = child.attrib['Name']

                    # Figure out what job this gun belongs to, first reading from
                    # a template (if we're inheriting from one), and then from tags
                    # directly on the weapon.
                    job = None
                    if 'Template' in child.attrib:
                        job = weapon_job_mapping[child.attrib['Template']]
                    for inner_child in child:
                        if inner_child.tag == 'Job':
                            job = inner_child.text
                            break
                    weapon_job_mapping[name] = job

                    # Now, if we're part of the known skips, skip us!
                    if name in known_weapon_skips:
                        continue

                    # Now if we're abstract, continue on -- don't actually care about it.
                    if 'Abstract' in child.attrib:
                        continue

                    # Likewise, if we've been set as a Virtual weapon, we sort of don't care.
                    # Continue.
                    got_virtual = False
                    for inner_child in child:
                        if inner_child.tag == 'Virtual' and inner_child.text == 'true':
                            got_virtual = True
                            break
                    if got_virtual:
                        continue

                    # Get our english label
                    label_lookup = f'weapon_{name}'
                    if label_lookup not in labels:
                        print(f'NOTICE: skipping Weapon "{name}"; no translation found.')
                        continue
                    label = labels[label_lookup]

                    # Now output the struct
                    print(f"        '{name}': Weapon(", file=odf)
                    print(f"            '{name}',", file=odf)
                    print("            \"{}\",".format(quote_string(label)), file=odf)
                    print(f"            JOBS['{job}'],", file=odf)
                    print("            ),", file=odf)
                print('        }', file=odf)
                print('', file=odf)


            # Then: crew
            with game_pak.open('Definitions/personas.xml') as persona_xml:

                crew_redirects = {}
                print('CREW_REAL = {', file=odf)
                root = ET.fromstring(persona_xml.read())
                for child in root:
                    if 'Abstract' in child.attrib:
                        continue
                    if 'Template' not in child.attrib or child.attrib['Template'] != 'CREW':
                        continue
                    name = child.attrib['Name']
                    label = labels[f'persona_{name}']
                    crew_redirects[name] = name
                    crew_redirects[label.lower()] = name
                    job = None
                    for inner_child in child:
                        if inner_child.tag == 'DefaultWeapon':
                            default_weapon = inner_child.text
                            job = weapon_job_mapping[default_weapon]
                            break
                    if job is None:
                        raise RuntimeError(f'No default job found for crew: {name}')
                    print(f"        '{name}': Crew(", file=odf)
                    print(f"            '{name}',", file=odf)
                    print("            \"{}\",".format(quote_string(label)), file=odf)
                    print(f"            JOBS['{job}'],", file=odf)
                    print("            ),", file=odf)
                print('        }', file=odf)
                print('', file=odf)

                # And also, we want users to be able to be able to refer to crew
                # by their in-game names.
                print('CREW = {', file=odf)
                for crew_usable, crew_real in crew_redirects.items():
                    print(f"        '{crew_usable}': CREW_REAL['{crew_real}'],", file=odf)
                print('        }', file=odf)
                print('', file=odf)


            # Some keyitems and upgrades a pretty closely related, and I'd like to be able
            # to enable/disable them together.  So key items need to know what upgrade(s)
            # they unlock, and upgrades need to know what key items are required.  In some
            # cases it hardly matters; if you add the key item to the save, the game will
            # automatically unlock the upgrade, for instance.  But adding an *upgrade*
            # should really add the relevant key items, and removing either should really
            # remove their counterparts.  Also, for key-item-unlocked upgrades, the item
            # name seems to be the only decent way to get an english string for the upgrade
            # name, so we're pulling it from there.
            #
            # So anyway, we need to read key items first so we can get the key item names
            # (to put that info in the upgrades structure), but we also need to read the
            # upgrades first to find out which key items they require.  Fun!  So we'll
            # be sort of doing a double-loop for one of them.  The simplest one to do first
            # is KeyItems, so we'll be doing *that* to get the names, then looping through
            # ugprades, and then looping through key items yet again.
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
            key_item_to_upgrade = {}
            with game_pak.open('Definitions/ship_upgrades.xml') as ship_upgrades:

                print('UPGRADES = {', file=odf)
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
                    name_string_id = None
                    label_suffixes = []
                    for inner_child in child:
                        match inner_child.tag:
                            case 'KeyItem':
                                keyitem = inner_child.text
                                # Keep track of the keyitem->upgrade mapping
                                if keyitem not in key_item_to_upgrade:
                                    key_item_to_upgrade[keyitem] = []
                                key_item_to_upgrade[keyitem].append(child.attrib['Name'])
                            case 'ShowOptionalLayer':
                                optional_layer = inner_child.text
                            case 'Type':
                                upgrade_type = inner_child.text
                            case 'NameStringId':
                                name_string_id = inner_child.text
                            case 'CrewStats':
                                for even_more_inner_child in inner_child:
                                    match even_more_inner_child.tag:
                                        case 'HitPoints':
                                            label_suffixes.append('Health')
                                        case 'MoveDistance':
                                            label_suffixes.append('Move Distance')
                                        case 'AoERange':
                                            label_suffixes.append('Aura')
                                        case 'MeleeDamage':
                                            label_suffixes.append('Melee Damage')
                                        case 'CogCapacity':
                                            label_suffixes.append('Cogs')
                                        case 'Aim':
                                            label_suffixes.append('Aim')
                                        case 'Damage':
                                            label_suffixes.append('Damage')
                            case 'ExperienceBonus':
                                label_suffixes.append('XP Bonus')
                    # Some slightly dodgy attempts to find the name shown in the game,
                    # but it seems to work fine.
                    if name_string_id is not None:
                        label = labels[name_string_id]
                    elif optional_layer is not None:
                        label = labels[optional_layer]
                    elif keyitem is not None:
                        label = keyitems[keyitem]
                    else:
                        test_label_name = 'ship_upgrade_{}'.format(child.attrib['Name'])
                        if test_label_name in labels:
                            label = labels[test_label_name]
                        else:
                            label = child.attrib['Name']
                    if label_suffixes:
                        # These are intended for the Celestial Gears, but they show up in
                        # other upgrades too.  That's mostly fine, though I want to prevent
                        # it from adding `(Cogs)` to the `Extra Cog` upgrade, since that's
                        # kind of redundant and weird-looking.
                        if label != 'Extra Cog':
                            label = '{} ({})'.format(
                                    label,
                                    ', '.join(label_suffixes),
                                    )
                    if upgrade_type is None \
                            and 'Template' in child.attrib \
                            and child.attrib['Template'] in upgrade_template_types:
                        upgrade_type = upgrade_template_types[child.attrib['Template']]
                    print("        '{}': Upgrade(".format(child.attrib['Name']), file=odf)
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


            # Now back to key items
            print('KEY_ITEMS = {', file=odf)
            for keyitem_name, keyitem_label in keyitems.items():
                print("        '{}': KeyItem(".format(keyitem_name), file=odf)
                print("            '{}',".format(keyitem_name), file=odf)
                print("            \"{}\",".format(quote_string(keyitem_label)), file=odf)
                if keyitem_name in key_item_to_upgrade:
                    print("            [{}],".format(
                        ', '.join(["'{}'".format(n) for n in key_item_to_upgrade[keyitem_name]]),
                        ), file=odf)
                print("            ),", file=odf)
            print('        }', file=odf)
            print('', file=odf)


            # Now a few datatypes that we're handling similarly.
            for xml_filename, var_name, class_name in [
                    ('Definitions/hats.xml', 'HATS', 'Hat'),
                    ('Definitions/ship_equipment.xml', 'SHIP_EQUIPMENT', 'ShipEquipment'),
                    ('Definitions/utilities.xml', 'UTILITIES', 'Utility'),
                    ]:

                with game_pak.open(xml_filename) as xml_data:

                    print(f'{var_name} = {{', file=odf)
                    root = ET.fromstring(xml_data.read())
                    for child in root:
                        if 'Abstract' in child.attrib:
                            continue
                        name = child.attrib['Name']
                        got_virtual = False
                        for inner_child in child:
                            if inner_child.tag == 'Virtual' and inner_child.text == 'true':
                                got_virtual = True
                                break
                        if got_virtual:
                            continue
                        if name not in labels:
                            print(f'NOTICE: skipping {class_name} "{name}"; no translation found.')
                            continue
                        print(f"        '{name}': {class_name}(", file=odf)
                        print(f"            '{name}',", file=odf)
                        print("            \"{}\",".format(quote_string(labels[name])), file=odf)
                        print("            ),", file=odf)
                    print('        }', file=odf)
                    print('', file=odf)

    print(f'Wrote to: {output_file}')


if __name__ == '__main__':
    main()

