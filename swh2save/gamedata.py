# File has been autogenerated by gen_game_data.py
# Generated on: 2024-08-21T18:05:18+00:00
# Don't edit by hand!

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


SHIP_UPGRADES = {
        'ship_boost_00': ShipUpgrade(
            'ship_boost_00',
            "Propeller Booster",
            'ship_booster',
            'ability',
            ),
        'dive_00': ShipUpgrade(
            'dive_00',
            "Pressure Tank",
            'steel_plates_west_caribbea_c',
            'ability',
            ),
        'dive_02': ShipUpgrade(
            'dive_02',
            "Atomic Engine",
            'atomic_engine',
            'ability',
            ),
        'geiger_counter_00': ShipUpgrade(
            'geiger_counter_00',
            "Geiger Counter",
            'keyitem_geiger_counter',
            'ability',
            ),
        'geiger_counter_01': ShipUpgrade(
            'geiger_counter_01',
            "Atomic Engine",
            'atomic_engine',
            'ability',
            ),
        'equip_00': ShipUpgrade(
            'equip_00',
            "Sub Equipment Terminal",
            None,
            'main',
            ),
        'gym_00': ShipUpgrade(
            'gym_00',
            "Personal Upgrade Terminal",
            None,
            'main',
            ),
        'gym_01': ShipUpgrade(
            'gym_01',
            "gym_01",
            None,
            'main',
            ),
        'guildhall_00': ShipUpgrade(
            'guildhall_00',
            "Job Upgrade Terminal",
            None,
            'main',
            ),
        'guildhall_01': ShipUpgrade(
            'guildhall_01',
            "guildhall_01",
            None,
            'main',
            ),
        'guildhall_02': ShipUpgrade(
            'guildhall_02',
            "guildhall_02",
            None,
            'main',
            ),
        'equip_slot_00': ShipUpgrade(
            'equip_slot_00',
            "equip_slot_00",
            None,
            'main',
            ),
        'equip_slot_01': ShipUpgrade(
            'equip_slot_01',
            "equip_slot_01",
            None,
            'main',
            ),
        'equip_slot_02': ShipUpgrade(
            'equip_slot_02',
            "equip_slot_02",
            None,
            'main',
            ),
        'equip_slot_03': ShipUpgrade(
            'equip_slot_03',
            "equip_slot_03",
            None,
            'main',
            ),
        'equip_slot_04': ShipUpgrade(
            'equip_slot_04',
            "equip_slot_04",
            None,
            'main',
            ),
        'equip_slot_05': ShipUpgrade(
            'equip_slot_05',
            "equip_slot_05",
            None,
            'main',
            ),
        'sonar': ShipUpgrade(
            'sonar',
            "sonar",
            None,
            'main',
            ),
        'bunk_bed_00': ShipUpgrade(
            'bunk_bed_00',
            "bunk_bed_00",
            None,
            'main',
            ),
        'bunk_bed_01': ShipUpgrade(
            'bunk_bed_01',
            "bunk_bed_01",
            None,
            'main',
            ),
        'extra_cog_00': ShipUpgrade(
            'extra_cog_00',
            "extra_cog_00",
            None,
            'main',
            ),
        'extra_cog_01': ShipUpgrade(
            'extra_cog_01',
            "extra_cog_01",
            None,
            'main',
            ),
        'extra_cog_02': ShipUpgrade(
            'extra_cog_02',
            "extra_cog_02",
            None,
            'main',
            ),
        'extra_cog_03': ShipUpgrade(
            'extra_cog_03',
            "extra_cog_03",
            None,
            'main',
            ),
        'extra_utility_00': ShipUpgrade(
            'extra_utility_00',
            "extra_utility_00",
            None,
            'main',
            ),
        'exp_bonus_00': ShipUpgrade(
            'exp_bonus_00',
            "exp_bonus_00",
            None,
            'main',
            ),
        'exp_bonus_01': ShipUpgrade(
            'exp_bonus_01',
            "exp_bonus_01",
            None,
            'main',
            ),
        'money_bonus_00': ShipUpgrade(
            'money_bonus_00',
            "money_bonus_00",
            None,
            'main',
            ),
        'money_bonus_01': ShipUpgrade(
            'money_bonus_01',
            "money_bonus_01",
            None,
            'main',
            ),
        'crew_health_00': ShipUpgrade(
            'crew_health_00',
            "crew_health_00",
            None,
            'main',
            ),
        'crew_health_01': ShipUpgrade(
            'crew_health_01',
            "crew_health_01",
            None,
            'main',
            ),
        'crew_health_02': ShipUpgrade(
            'crew_health_02',
            "crew_health_02",
            None,
            'main',
            ),
        'crew_melee_00': ShipUpgrade(
            'crew_melee_00',
            "crew_melee_00",
            None,
            'main',
            ),
        'crew_move_00': ShipUpgrade(
            'crew_move_00',
            "crew_move_00",
            None,
            'main',
            ),
        'jobupgrade_tank_1': ShipUpgrade(
            'jobupgrade_tank_1',
            "jobupgrade_tank_1",
            None,
            'guildhall',
            ),
        'jobupgrade_tank_2': ShipUpgrade(
            'jobupgrade_tank_2',
            "jobupgrade_tank_2",
            None,
            'guildhall',
            ),
        'jobupgrade_tank_3': ShipUpgrade(
            'jobupgrade_tank_3',
            "jobupgrade_tank_3",
            None,
            'guildhall',
            ),
        'jobupgrade_boomer_1': ShipUpgrade(
            'jobupgrade_boomer_1',
            "jobupgrade_boomer_1",
            None,
            'guildhall',
            ),
        'jobupgrade_boomer_2': ShipUpgrade(
            'jobupgrade_boomer_2',
            "jobupgrade_boomer_2",
            None,
            'guildhall',
            ),
        'jobupgrade_boomer_3': ShipUpgrade(
            'jobupgrade_boomer_3',
            "jobupgrade_boomer_3",
            None,
            'guildhall',
            ),
        'jobupgrade_engineer_1': ShipUpgrade(
            'jobupgrade_engineer_1',
            "jobupgrade_engineer_1",
            None,
            'guildhall',
            ),
        'jobupgrade_engineer_2': ShipUpgrade(
            'jobupgrade_engineer_2',
            "jobupgrade_engineer_2",
            None,
            'guildhall',
            ),
        'jobupgrade_engineer_3': ShipUpgrade(
            'jobupgrade_engineer_3',
            "jobupgrade_engineer_3",
            None,
            'guildhall',
            ),
        'jobupgrade_sniper_1': ShipUpgrade(
            'jobupgrade_sniper_1',
            "jobupgrade_sniper_1",
            None,
            'guildhall',
            ),
        'jobupgrade_sniper_2': ShipUpgrade(
            'jobupgrade_sniper_2',
            "jobupgrade_sniper_2",
            None,
            'guildhall',
            ),
        'jobupgrade_sniper_3': ShipUpgrade(
            'jobupgrade_sniper_3',
            "jobupgrade_sniper_3",
            None,
            'guildhall',
            ),
        'jobupgrade_reaper_1': ShipUpgrade(
            'jobupgrade_reaper_1',
            "jobupgrade_reaper_1",
            None,
            'guildhall',
            ),
        'jobupgrade_reaper_2': ShipUpgrade(
            'jobupgrade_reaper_2',
            "jobupgrade_reaper_2",
            None,
            'guildhall',
            ),
        'jobupgrade_reaper_3': ShipUpgrade(
            'jobupgrade_reaper_3',
            "jobupgrade_reaper_3",
            None,
            'guildhall',
            ),
        'jobupgrade_flanker_1': ShipUpgrade(
            'jobupgrade_flanker_1',
            "jobupgrade_flanker_1",
            None,
            'guildhall',
            ),
        'jobupgrade_flanker_2': ShipUpgrade(
            'jobupgrade_flanker_2',
            "jobupgrade_flanker_2",
            None,
            'guildhall',
            ),
        'jobupgrade_flanker_3': ShipUpgrade(
            'jobupgrade_flanker_3',
            "jobupgrade_flanker_3",
            None,
            'guildhall',
            ),
        'celestial_gear_01': ShipUpgrade(
            'celestial_gear_01',
            "Golden Gear",
            'keyitem_celestial_gear_01',
            'ability',
            ),
        'celestial_gear_02': ShipUpgrade(
            'celestial_gear_02',
            "Amethyst Gear",
            'keyitem_celestial_gear_02',
            'ability',
            ),
        'celestial_gear_03': ShipUpgrade(
            'celestial_gear_03',
            "Emerald Gear",
            'keyitem_celestial_gear_03',
            'ability',
            ),
        'celestial_gear_04': ShipUpgrade(
            'celestial_gear_04',
            "Sapphire Gear",
            'keyitem_celestial_gear_04',
            'ability',
            ),
        'celestial_gear_05': ShipUpgrade(
            'celestial_gear_05',
            "Diamond Gear",
            'keyitem_celestial_gear_05',
            'ability',
            ),
        'celestial_gear_06': ShipUpgrade(
            'celestial_gear_06',
            "Citrine Gear",
            'keyitem_celestial_gear_06',
            'ability',
            ),
        'celestial_gear_07': ShipUpgrade(
            'celestial_gear_07',
            "Ruby Gear",
            'keyitem_celestial_gear_07',
            'ability',
            ),
        }

HATS = {
        'hat_captain': Hat('hat_captain', "Captain's Hat"),
        'hat_daisy': Hat('hat_daisy', "Flop Cap"),
        'hat_wesley': Hat('hat_wesley', "Pickelhaube"),
        'hat_cornelius': Hat('hat_cornelius', "Fez"),
        'hat_poe': Hat('hat_poe', "Roguish Antenna"),
        'hat_judy': Hat('hat_judy', "Leather Hat"),
        'hat_adventure_boy': Hat('hat_adventure_boy', "Spiky Hair"),
        'hat_diver': Hat('hat_diver', "A Simple Valve"),
        'hat_crow': Hat('hat_crow', "Soft Cloth Hat"),
        'hat_cyclop': Hat('hat_cyclop', "A Simple Beanie"),
        'hat_chimney': Hat('hat_chimney', "Sailor's Cap"),
        'hat_mother': Hat('hat_mother', "Krakenbane's Hat"),
        'hat_piper': Hat('hat_piper', "Captain Faraday's Hat"),
        'hat_revolution_beret': Hat('hat_revolution_beret', "Rebellious Beret"),
        'hat_navy_seabot': Hat('hat_navy_seabot', "Navy Soldier Cap"),
        'hat_navy_seabot_elite': Hat('hat_navy_seabot_elite', "Elite Soldier Cap"),
        'hat_navy_seabot_machinegunner': Hat('hat_navy_seabot_machinegunner', "Machinegunner Hat"),
        'hat_navy_seabot_machinegunner_elite': Hat('hat_navy_seabot_machinegunner_elite', "Elite Machinegunner Hat"),
        'hat_navy_seabot_shotgunner': Hat('hat_navy_seabot_shotgunner', "Shotgunner Hat"),
        'hat_navy_seabot_shotgunner_elite': Hat('hat_navy_seabot_shotgunner_elite', "Elite Shotgunner Hat"),
        'hat_navy_seabot_sniper': Hat('hat_navy_seabot_sniper', "Sniper Goggle"),
        'hat_navy_seabot_sniper_elite': Hat('hat_navy_seabot_sniper_elite', "Elite Sniper Goggle"),
        'hat_navy_seabot_swordsman': Hat('hat_navy_seabot_swordsman', "Swordsman's Hat"),
        'hat_navy_seabot_swordsman_elite': Hat('hat_navy_seabot_swordsman_elite', "Elite Swordsman's Hat"),
        'hat_navy_seabot_rare01': Hat('hat_navy_seabot_rare01', "Army Helmet"),
        'hat_navy_seabot_rare02': Hat('hat_navy_seabot_rare02', "Safari Hat"),
        'hat_navy_seabot_rare03': Hat('hat_navy_seabot_rare03', "Cowboy Hat"),
        'hat_navy_seabot_rare04': Hat('hat_navy_seabot_rare04', "Bearskin"),
        'hat_navy_seabot_fire': Hat('hat_navy_seabot_fire', "Fire helmet"),
        'hat_navy_seabot_bigsteve': Hat('hat_navy_seabot_bigsteve', "Floppy Hat"),
        'hat_navy_seabot_tough': Hat('hat_navy_seabot_tough', "Iron Mask"),
        'hat_navy_seabot_roaster': Hat('hat_navy_seabot_roaster', "Savory Bucket"),
        'hat_navy_guard': Hat('hat_navy_guard', "Navy Guard Hat"),
        'hat_navy_guard_elite': Hat('hat_navy_guard_elite', "Elite Guard Hat"),
        'hat_navy_guard_roaster': Hat('hat_navy_guard_roaster', "Lit Candle"),
        'hat_navy_commander': Hat('hat_navy_commander', "Commander Hat"),
        'hat_navy_commander_elite': Hat('hat_navy_commander_elite', "Elite Commander Hat"),
        'hat_navy_commander_rare01': Hat('hat_navy_commander_rare01', "Pilot Hat"),
        'hat_navy_commander_rare02': Hat('hat_navy_commander_rare02', "The Bonaparte"),
        'hat_navy_commander_dean': Hat('hat_navy_commander_dean', "Rugged Veteran's Hat"),
        'hat_navy_commander_warden': Hat('hat_navy_commander_warden', "Prison Warden Hat"),
        'hat_navy_commander_fancy01': Hat('hat_navy_commander_fancy01', "Fancier Wig"),
        'hat_navy_commander_fancy02': Hat('hat_navy_commander_fancy02', "Fancy Wig"),
        'hat_navy_commander_fancy03': Hat('hat_navy_commander_fancy03', "...Fancy Wig?"),
        'hat_navy_commander_roaster': Hat('hat_navy_commander_roaster', "Very Cool Cap"),
        'hat_navy_recruit': Hat('hat_navy_recruit', "Recruit Hat"),
        'hat_navy_recruit_rare01': Hat('hat_navy_recruit_rare01', "Paper Boat"),
        'hat_navy_fabio': Hat('hat_navy_fabio', "Glorious Pompadour"),
        'hat_navy_mech_operator': Hat('hat_navy_mech_operator', "Complex Navy Hat"),
        'hat_navy_drone': Hat('hat_navy_drone', "Blue Rotating Beacon"),
        'hat_navy_drone_rare01': Hat('hat_navy_drone_rare01', "Party Light"),
        'hat_navy_bomb': Hat('hat_navy_bomb', "Heated Propeller"),
        'hat_pirate_totem_bearer': Hat('hat_pirate_totem_bearer', "Occult Cone"),
        'hat_pirate_totem_bearer_bone': Hat('hat_pirate_totem_bearer_bone', "Occult Bone Cone"),
        'hat_pirate_totem_bearer_ice': Hat('hat_pirate_totem_bearer_ice', "Occult Ice Cone"),
        'hat_pirate_totem_bearer_retribution': Hat('hat_pirate_totem_bearer_retribution', "Occult Retribution Cone"),
        'hat_pirate_totem_bearer_lightning': Hat('hat_pirate_totem_bearer_lightning', "Occult Conductor Cone"),
        'hat_pirate_totem_bearer_rare01': Hat('hat_pirate_totem_bearer_rare01', "Crown of Thorns"),
        'hat_pirate_totem_bearer_pain': Hat('hat_pirate_totem_bearer_pain', "Knife in the Head"),
        'hat_pirate_skelebot': Hat('hat_pirate_skelebot', "Small Spiky Helmet"),
        'hat_pirate_skelebot_ice': Hat('hat_pirate_skelebot_ice', "Cool Cube"),
        'hat_pirate_swab': Hat('hat_pirate_swab', "Seashellmet"),
        'hat_pirate_swab_elite': Hat('hat_pirate_swab_elite', "Horned Seashell"),
        'hat_pirate_swab_ice': Hat('hat_pirate_swab_ice', "Fur-Lined Seashell Hat"),
        'hat_pirate_swab_tough': Hat('hat_pirate_swab_tough', "Uni-horn"),
        'hat_pirate_swab_rare01': Hat('hat_pirate_swab_rare01', "Tinfoil Hat"),
        'hat_pirate_swab_rare02': Hat('hat_pirate_swab_rare02', "Seagull Nest"),
        'hat_pirate_swab_rare03': Hat('hat_pirate_swab_rare03', "Viking Helmet"),
        'hat_pirate_berserker': Hat('hat_pirate_berserker', "Bull Horns"),
        'hat_pirate_berserker_ice': Hat('hat_pirate_berserker_ice', "Icy Horns"),
        'hat_pirate_berserker_rare01': Hat('hat_pirate_berserker_rare01', "Cardboard Box"),
        'hat_pirate_berserker_rare02': Hat('hat_pirate_berserker_rare02', "Pretty Bow"),
        'hat_pirate_berserker_parley': Hat('hat_pirate_berserker_parley', "Propeller Cap"),
        'hat_pirate_morgan': Hat('hat_pirate_morgan', "Morgan's Spire"),
        'hat_pirate_bomb': Hat('hat_pirate_bomb', "Frosty Propeller"),
        'hat_atomic_reviver': Hat('hat_atomic_reviver', "Atomic Helm"),
        'hat_atomic_reviver_king': Hat('hat_atomic_reviver_king', "Infinity Crown"),
        'hat_atomic_reviver_rare01': Hat('hat_atomic_reviver_rare01', "Graduate Hat"),
        'hat_atomic_reviver_rare02': Hat('hat_atomic_reviver_rare02', "Octopus"),
        'hat_atomic_flying_reviver': Hat('hat_atomic_flying_reviver', "Crystal Crown"),
        'hat_atomic_flying_reviver_rare01': Hat('hat_atomic_flying_reviver_rare01', "Marvin's Helmet"),
        'hat_atomic_walking_bomb': Hat('hat_atomic_walking_bomb', "Delectable Cone"),
        'hat_atomic_walking_bomb_rare01': Hat('hat_atomic_walking_bomb_rare01', "Jellyfish"),
        'hat_atomic_mimic': Hat('hat_atomic_mimic', "Mimic Mask"),
        'hat_atomic_mech_operator': Hat('hat_atomic_mech_operator', "Crown of Reckoning"),
        'hat_atomic_water_scientist': Hat('hat_atomic_water_scientist', "Band of Icy Revenge"),
        'hat_shop_fish': Hat('hat_shop_fish', "A Fish"),
        'hat_shop_fur': Hat('hat_shop_fur', "Fur Hat"),
        'hat_shop_ushanka': Hat('hat_shop_ushanka', "Ushanka"),
        'hat_shop_rain': Hat('hat_shop_rain', "Sylvester"),
        'hat_shop_kanga': Hat('hat_shop_kanga', "Stylish Hat"),
        'hat_shop_valkyrie': Hat('hat_shop_valkyrie', "Valkyrie Helmet"),
        'hat_shop_santa': Hat('hat_shop_santa', "Jolly Hat"),
        'hat_shop_fruit': Hat('hat_shop_fruit', "Fruity Hat"),
        'hat_shop_snorkel': Hat('hat_shop_snorkel', "Snorkling Gear"),
        'hat_shop_screen': Hat('hat_shop_screen', "Green Screen"),
        'hat_shop_straw': Hat('hat_shop_straw', "Straw Hat"),
        'hat_shop_wickedshades': Hat('hat_shop_wickedshades', "Wicked Shades"),
        'hat_shop_top': Hat('hat_shop_top', "Top Hat"),
        'hat_shop_icecream': Hat('hat_shop_icecream', "Magical Horn"),
        'hat_shop_bandana': Hat('hat_shop_bandana', "Purple bandana"),
        }

