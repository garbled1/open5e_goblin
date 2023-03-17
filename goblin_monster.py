#!/usr/bin/python3

"""
Find a mosnter on open5e, spit out thegoblinsnotebook .md
"""

import os
import re
import requests
import argparse
import json
from rich import print
from rich.console import Console
from pprint import pprint
from PyInquirer import prompt
from prompt_toolkit.validation import Validator, ValidationError
from urllib import error as u_errors
from markdowngenerator import MarkdownGenerator

open5e_url = 'https://api.open5e.com/'
limit = '100'


class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end


def search_by_cr():
    """Search by CR"""

    questions = [
        {
            'type': 'input',
            'name': 'cr',
            'message': 'CR Rating (whole number)',
            #'validate': NumberValidator,
            #'filter': lambda val: int(val),
            'default': '1',
        }
    ]
    answers = prompt(questions)
    data = requests.get(open5e_url + 'monsters/?limit=' + limit + '&challenge_rating=' + str(answers['cr']))
    json_data = data.json()

    return json_data['results']


def search_by_type():
    """Search by type"""

    questions = [
        {
            'type': 'list',
            'name': 'type',
            'message': 'Monster type',
            'choices': [
                'Aberration',
                'Beast',
                'Celestial',
                'Construct',
                'Dragon',
                'Elemental',
                'Fey',
                'Fiend',
                'Giant',
                'Humanoid',
                'Monstrosity',
                'Ooze',
                'Plant',
                'Undead',
            ],
        }
    ]
    answers = prompt(questions)
    data = requests.get(open5e_url + 'monsters/?limit=' + limit + '&type=' + answers['type'])
    json_data = data.json()
    results = json_data['results']

    data2 = requests.get(open5e_url + 'monsters/?limit=' + limit + '&type=' + answers['type'].lower())
    json_data = data2.json()
    for r in json_data['results']:
        results.append(r)

    return results


def search_by_name():
    """Search by monster name"""

    questions = [
        {
            'type': 'input',
            'name': 'name',
            'message': 'Monster name (partials ok)',
            'default': '',
        }
    ]
    answers = prompt(questions)
    data = requests.get(open5e_url + 'monsters/?limit=' + limit + '&search=' + answers['name'])
    json_data = data.json()

    return json_data['results']


def mod5e(stat):
    """Print a stat as num +/-X"""
    mod = int(round((stat - 10) / 2))
    return str(stat) + ' (' + ('+' if mod > 0 else '') + str(mod) + ')'


def basemod5e(stat):
    """return modifier for stat"""
    return int(round((stat - 10) / 2))


def cr_to_xp(cr):
    """Given a CR, print XP"""

    crxp = {
        "0": "10",
        "1/8": "25",
        "1/4": "50",
        "1/2": "100",
        "1": "200",
        "2": "450",
        "3": "700",
        "4": "1100",
        "5": "1800",
        "6": "2,300",
        "7": "2,900",
        "8": "3,900",
        "9": "5,000",
        "10": "5,900",
        "11": "7,200",
        "12": "8,400",
        "13": "10,000",
        "14": "11,500",
        "15": "13,000",
        "16": "15,000",
        "17": "18,000",
        "18": "20,000",
        "19": "22,000",
        "20": "25,000",
        "21": "33,000",
        "22": "41,000",
        "23": "50,000",
        "24": "62,000",
        "25": "75,000",
        "26": "90,000",
        "27": "105,000",
        "28": "120,000",
        "29": "135,000",
        "30": "155,000",
        }

    return crxp[cr]


def rollable_text(string):
    """Add rollable() to a string as needed"""
    xstring = re.sub(r'(\([0-9]*d[0-9 +]*\))', r'rollable\1', string)
    return re.sub(r'(\+[0-9]*) to hit', r'rollable(1d20\1) to hit', xstring)


def numplus(num):
    """print number with +"""
    if num > 0:
        return '+' + str(num)
    return str(num)


def make_md_from_json(jdata):
    """Make an md file from json data"""

    with MarkdownGenerator(enable_write=False) as doc:
        doc.addHeader(1, '$\[objectname]')
        doc.writeTextLine(f'{doc.addItalicizedText(jdata["size"] + " " + jdata["type"] + ", " + jdata["alignment"])}')

        doc.addHorizontalRule()
        
        # AC
        doc.writeTextLine(f'{doc.addBoldedText("Armor Class")}' + f' {str(jdata["armor_class"]) + " (" + str(jdata["armor_desc"]) + ")"}')

        # HP
        doc.writeTextLine(
            f'{doc.addBoldedText("Hit Points")}' + f' {str(jdata["hit_points"]) + " rollable(" + jdata["hit_dice"] + ")"}')

        # speed
        speedline = doc.addBoldedText("Speed") + "\n"
        for spd in jdata['speed'].keys():
            if jdata['speed'][spd] > 2:
                xline = spd + ' ' + str(jdata['speed'][spd]) + 'ft.,\n'
                speedline = speedline + xline
        for spd in jdata['speed'].keys():
            if jdata['speed'][spd] and jdata['speed'][spd] < 2:
                xline = '(' + spd + ') '
                speedline = speedline + xline        
        doc.writeTextLine(speedline)

        # stats

        doc.addHorizontalRule()
        doc.writeText(text='<style>div#blurb-text td,div#blurb-text th{border-bottom:1px solid #DB6214; padding: 0 0.5em 0 0.2em}div#blurb-text thead{background-color: #ccc}</style>', html_escape=False)
        header = [ 'STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA' ]
        row = [
            mod5e(jdata['strength']),
            mod5e(jdata['dexterity']),
            mod5e(jdata['constitution']),
            mod5e(jdata['intelligence']),
            mod5e(jdata['wisdom']),
            mod5e(jdata['charisma']),
        ]
        hdr = '|'
        sep = '|'
        vals = '|'
        for x in header:
            hdr = hdr + x + '|'
            sep = sep + ':---:|'
        for x in row:
            vals = vals + x + '|'
        doc.writeText(hdr)
        doc.writeText(sep)
        doc.writeText(vals)
        doc.addHorizontalRule()

        sline = ''
        saves = {
            'strength_save': 'Str',
            'dexterity_save': 'Dex',
            'constitution_save': 'Con',
            'intelligence_save': 'Int',
            'wisdom_save': 'Wis',
            'charisma_save': 'Cha',
        }
        for s in saves.keys():
            m_s = re.sub('_save', '', s)
            if jdata[s] is not None:
                sline = sline + saves[s] + ' ' + numplus(jdata[s] + basemod5e(jdata[m_s])) + ' '
            else:
                sline = sline + saves[s] + ' ' + numplus(basemod5e(jdata[m_s])) + ' '
        if sline != '':
            doc.writeTextLine(f'{doc.addBoldedText("Saving Throws") + " " + sline}')

        if len(jdata['skills']) > 0:
            skilltext = ''
            for sk in jdata['skills'].keys():
                skilltext = skilltext + sk.ucfirst() + ' ' + numplus(jdata['skills'][sk]) + ', '
            doc.writeTextLine(f'{doc.addBoldedText("Skills") + " " + skilltext}')
            
        vulns = {
            'damage_vulnerabilities': 'Damage Vulnerabilities',
            'damage_resistances': 'Damage Resistances',
            'damage_immunities': 'Damage Immunities',
            'condition_immunities': 'Condition Immunities',
        }

        for v in vulns.keys():
            if jdata[v] != '':
                doc.writeTextLine(f'{doc.addBoldedText(vulns[v]) + " " + jdata[v]}')

        doc.writeTextLine(f'{doc.addBoldedText("Senses") + " " + jdata["senses"]}')

        doc.writeTextLine(f'{doc.addBoldedText("Languages") + " " + jdata["languages"]}')
        doc.writeTextLine(f'{doc.addBoldedText("Challenge") + " " + str(jdata["challenge_rating"]) + " (" + cr_to_xp(str(jdata["challenge_rating"])) + " XP)"}')
        doc.addHorizontalRule()

        # Special abilities:

        for sa in jdata['special_abilities']:
            doc.writeTextLine(f'{doc.addBoldedText(sa["name"]) + " " + sa["desc"]}')

        doc.addHeader(2, 'Actions')
        for action in jdata['actions']:
            doc.writeTextLine(f'{doc.addBoldedText(action["name"] + ".") + " " + rollable_text(action["desc"])}')

        if jdata['reactions'].len() > 0:
            doc.addHeader(2, 'Reactions')
            for action in jdata['reactions']:
                doc.writeTextLine(f'{doc.addBoldedText(action["name"] + ".") + " " + rollable_text(action["desc"])}')

        if jdata['legendary_actions'].len() > 0:
            doc.addHeader(2, 'Legendary Actions')
            doc.writeTextLine(jdata['legendary_desc'])
            for action in jdata['legendary_actions']:
                doc.writeTextLine(f'{doc.addBoldedText(action["name"] + ".") + " " + rollable_text(action["desc"])}')


        # Now print dat
        for line in doc.document_data_array:
            print(line)


def opening_menu():
    """Ask for a mosnter to search for"""

    console = Console()
    console.clear()

    jdata = dict()

    questions = [
        {
            'type': 'list',
            'name': 'whatsearch',
            'message': 'What would you like to search by?',
            'choices': [
                'name',
                'challenge rating',
                'type',
                ],
        }
    ]

    answers = prompt(questions)

    mquestions = [
        {
            'type': 'list',
            'name': 'whichmonster',
            'message': 'Which monster?',
        }
    ]
    
    if answers['whatsearch'] == 'challenge rating':
        jdata = search_by_cr()

    if answers['whatsearch'] == 'name':
        jdata = search_by_name()

    if answers['whatsearch'] == 'type':
        jdata = search_by_type()
        
    mlist = []
    for monster in jdata:
        mlist.append(monster['name'])
    mquestions[0]['choices'] = mlist

    answers = prompt(mquestions)
    for m in jdata:
        if m['name'] == answers['whichmonster']:
            make_md_from_json(m)


    

if __name__ == '__main__':
    opening_menu()
