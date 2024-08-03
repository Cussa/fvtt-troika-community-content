import json
import os
import re
import sys


errorList = []
armour = 0


def handle_json_issue(message, log: bool):
    if log:
        errorList.append(message)
    return None


def find_json(item, type: str, log: bool = True):
    itemName = item.lower().replace(" ", "_")
    folders = {
        "weapon": "weapons-and-attacks",
        "item": "items",
        "skill": "skills",
        "spell": "spells",
    }
    itemTypes = {"weapon": "gear", "item": "items", "skill": "skill", "spell": "spell"}

    result = [
        os.path.join(dp, f)
        for dp, dn, filenames in os.walk(
            f"../../systems/troika/src/packs/troika-srd-{folders[type]}"
        )
        for f in filenames
        if f.lower().startswith(f"{itemTypes[type]}_{itemName}")
    ]

    if len(result) == 0:
        return handle_json_issue(f'{type.capitalize()} "{item}" not found', log)

    if len(result) > 1:
        return handle_json_issue(
            f'MORE than one {type.capitalize()} "{item}" found', log
        )

    with open(result[0], "r") as f:
        itemJson = f.read()
    idRegex = r"\"_id\": (.*?),"
    itemJson = re.sub(idRegex, "", itemJson)
    return itemJson


def handle_srd_possession(possession):
    item = find_json(possession[2:], "item")
    return item


def handle_armour(possession):
    global armour
    parenthesis = possession.index("(")
    armourName = possession[2 : parenthesis - 1]
    armourValueIndex = possession.index(": ")
    armourValue = possession[armourValueIndex + 2 : -2]

    armour = armourValue
    return f"""
    {{
        "name": "{armourName}",
        "type": "gear",
        "system": {{
            "inventorySlots": {int(armourValue) * 2},
            "equipped": true,
            "armourProvided": {armourValue},
            "quantity": 1,
        }},
    }}
"""


def handle_srd_weapon(possession):
    baseWeaponIndex = possession.lower().index("damage as")
    baseWeaponName = possession[baseWeaponIndex + 10 : -2]
    baseWeaponJson = find_json(baseWeaponName, "weapon")

    if not baseWeaponJson:
        return baseWeaponJson

    weaponName = possession[2 : baseWeaponIndex - 2]
    itemJson = json.loads(baseWeaponJson)
    item = baseWeaponJson.replace(itemJson["name"], weaponName)

    return item


def handle_new_item(possession):
    newItemRegex = (
        r"^- (?P<name>.*) \(slot:?\s?(?P<slot>.*?)(?: - (?P<description>.*?))?\)$"
    )
    itemMatch = re.match(newItemRegex, possession)

    if not itemMatch:
        errorList.append(f'NEW ITEM "{clear(possession)}" has format error')
        return None

    itemName = itemMatch.group("name")
    slots = itemMatch.group("slot")
    description = itemMatch.group("description") or ""

    return f"""
    {{
        "name": "{itemName}",
        "type": "gear",
        "system": {{
            "description": "<p>{description}</p>",
            "inventorySlots": {slots},
            "equipped": true,
            "quantity": 1,
        }},
    }}
"""


def handle_possession(possession):
    if "(" not in possession:
        return handle_srd_possession(possession)

    if "(damage as" in possession.lower():
        return handle_srd_weapon(possession)

    if "(armour:" in possession:
        return handle_armour(possession)

    return handle_new_item(possession)


def handle_possessions(possessions):
    items = []
    for line in possessions:
        item = handle_possession(line)
        if item:
            items.append(item)
    return items


def handle_srd_skill(skill: str):
    spaceIndex = skill.index(" ")
    item = find_json(clear(skill[spaceIndex + 1 :]), "skill", False)
    if not item:
        return item

    item = item.replace('"rank": "1",', f'"rank": "{skill[:spaceIndex]}",')
    return item


def handle_new_skill(skill: str):
    newItemRegex = r"^(?P<rank>\d*?) (?P<name>.*?)(?:\s\((?P<description>.*?)\))?$"
    clearSkill = clear(skill)
    itemMatch = re.match(newItemRegex, clearSkill)

    if not itemMatch:
        errorList.append(f'NEW SKILL "{skill}" has format error')

    itemName = itemMatch.group("name")
    rank = itemMatch.group("rank")
    description = itemMatch.group("description") or ""

    return f"""
    {{
        "name": "{itemName}",
        "type": "skill",
        "system": {{
            "description": "<p>{description}</p>",
            "rank": "{rank}",
        }},
    }}
"""


def handle_skill(skill: str):
    if "(" in skill:
        return handle_new_skill(skill)

    item = handle_srd_skill(skill)
    if not item:
        item = handle_new_skill(skill)

    return item


def handle_srd_spell(spell: str):
    spaceIndex = spell.index(" ")
    item = find_json(clear(spell[spaceIndex + 1 :].lower().replace("spell - ", "")), "spell")
    if not item:
        return item

    item = item.replace('"rank": "1",', f'"rank": "{spell[:spaceIndex]}",')
    return item


def handle_new_spell(spell: str):
    pass


def handle_spell(spell: str):
    if "(" in spell:
        return handle_new_spell(spell)

    return handle_srd_spell(spell)


def handle_advanced_skill(advanced_skill: str):
    if "spell" in advanced_skill.lower():
        return handle_spell(advanced_skill)

    return handle_skill(advanced_skill)


def handle_advanced_skills(adavnced_skills: list):
    items = []
    for line in adavnced_skills:
        item = handle_advanced_skill(line)
        if item:
            items.append(item)
    return items


def handle_img(backgroundName):
    fileName = backgroundName.lower().replace(" ", "-")
    backgroundImg = f"./assets/arts/{folder}/{fileName}.webp"
    if os.path.isfile(backgroundImg):
        backgroundImg = (
            f"modules/troika-community-content/assets/arts/{folder}/{fileName}.webp"
        )
        return backgroundImg

    return "icons/svg/mystery-man.svg"


def clear_list(lines):
    current = []
    for line in lines:
        cleared = clear(line)
        if cleared:
            current.append(cleared)
    finalString = "</p><p>".join(current)
    return f"<p>{finalString}</p>"


def clear(line: str, text=None):
    current = line
    if text:
        current = line.replace(text, "")
    return current.replace("\n", "").replace('"', '\\"').strip()


def addBackground(lines):

    name = clear(lines[0])

    possessionsLine = lines.index("POSSESSIONS:\n")
    advancedSkillsLine = lines.index("ADVANCED SKILLS:\n")
    attributionLine = len(lines) - 2

    specialLine = attributionLine
    special = ""
    if "SPECIAL\n" in lines:
        specialLine = lines.index("SPECIAL\n")
        special = clear_list(lines[specialLine + 1 : attributionLine])

    possessions = handle_possessions(lines[possessionsLine + 1 : advancedSkillsLine])
    advancedSkills = handle_advanced_skills(lines[advancedSkillsLine + 1 : specialLine])

    notes = clear_list(lines[1:possessionsLine])

    source = clear(lines[attributionLine][13:])
    link = clear(lines[attributionLine + 1][5:])

    allItems = ",\n".join(possessions + advancedSkills)
    items = f"[{allItems}]"

    img = handle_img(name)

    command = f"""
await Actor.create(
{{
    name: '{name}',
    type: "background",
    img: "{img}",
    system: {{
        armour: {armour},
        attribution: {{
            source: "{source} [Troika! Community Jam: Backgrounds {complement}]",
            link: "{link}"
        }},
        special: "{special}",
        notes: "{notes}"
    }},
    items: {items},
    folder: moduleFolder.id
}});"""

    command = (
        command.replace("True", "true")
        .replace("False", "false")
        .replace("None", "null")
    )
    with open("result.js", "a") as file:
        file.write(command)


folder = sys.argv[1]
complement = sys.argv[2]
filter = sys.argv[3] if len(sys.argv) > 3 else ""

result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./submissions/{folder}")
    for f in filenames
    # if not f.startswith("imported_")
]

if filter:
    result = [f for f in result if filter in f.lower()]

with open("result.js", "w") as file:
    file.write(
        f"""moduleFolder = game.folders.getName("CJ: Backgrounds {complement}");
if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Actor",
        name: "CJ: Backgrounds {complement}"
    }});
}}
"""
    )

for file in result:
    errorList.clear()
    armour = 0
    with open(file, "r") as f:
        lines = f.readlines()
    addBackground(lines)
    if len(errorList):
        print(clear(lines[0]))
        for e in errorList:
            print(f"- {e}")
        print("=================================")
