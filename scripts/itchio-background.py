import json
import os
import re
import sys


errorList = []
armour = 0


def find_json(item, type: str):
    itemName = item.lower().replace(" ", "_")
    folders = {"weapon": "weapons-and-attacks", "item": "items"}
    itemTypes = {"weapon": "gear", "item": "items"}

    result = [
        os.path.join(dp, f)
        for dp, dn, filenames in os.walk(
            f"../../systems/troika/src/packs/troika-srd-{folders[type]}"
        )
        for f in filenames
        if f.lower().startswith(f"{itemTypes[type]}_{itemName}")
    ]
    if len(result) == 0:
        errorList.append(f'{type.capitalize()} "{item}" not found')
        return None
    if len(result) > 1:
        errorList.append(f'MORE than one {type.capitalize()} "{item}" found')
        return None

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
    baseWeaponIndex = possession.index("damage as")
    baseWeaponName = possession[baseWeaponIndex + 10 : -2]
    baseWeaponJson = find_json(baseWeaponName, "weapon")

    if not baseWeaponJson:
        return baseWeaponJson

    weaponName = possession[2 : baseWeaponIndex - 2]
    itemJson = json.loads(baseWeaponJson)
    item = baseWeaponJson.replace(itemJson["name"], weaponName)

    return item


def handle_new_item(possession):
    newItemRegex = r"- (?P<name>.*) \(slot:? (?P<slot>.*?) - (?P<description>.*?)\)"
    itemMatch = re.match(newItemRegex, possession)

    if not itemMatch:
        errorList.append(f'NEW ITEM "{possession}" has format error')

    itemName = itemMatch.group("name")
    slots = itemMatch.group("slot")
    description = itemMatch.group("description")

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

    if "(damage as" in possession:
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

    notes = clear_list(lines[1:possessionsLine])

    source = clear(lines[attributionLine][13:])
    link = clear(lines[attributionLine + 1][5:])

    allItems = ",\n".join(possessions)
    items = f"[{allItems}]"
    # damageResult = handle_damage(lines[5])
    # items = damageResult["items"]
    # if damageResult["special"]:
    #     newSpecial = damageResult["special"]
    #     special = f"<p>{newSpecial}</p>{special}"

    command = f"""
await Actor.create(
{{
    name: '{name}',
    type: "background",
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

result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./submissions/{folder}")
    for f in filenames
    # if not f.startswith("imported_")
]

with open("result.js", "w") as file:
    file.write(
        f"""moduleFolder = game.folders.getName("Community Jam: Backgrounds {complement}");
if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Actor",
        name: "Community Jam: Backgrounds {complement}"
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
        print(lines[0])
        for e in errorList:
            print(f"- {e}")
        print("=================================")
