import json
import os
import re
import sys
from unidecode import unidecode


errorList = []
armour = 0

newSkillList = []
newSpellList = []
newGearList = []

attributionJsonText = ""

rankRegex = r"\"rank\":\s?\"\d*?\""


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
    item = find_json(possession[2:], "item", False)
    return item


def handle_armour(possession: str):
    global armour
    parenthesis = possession.index("(")
    armourName = possession[2 : parenthesis - 1]
    armourValueIndex = possession.index(": ")
    armourEndIndex = (
        possession[armourValueIndex:].index(" -") if " -" in possession else -1
    )
    armourValue = ""

    description = ""
    if armourEndIndex > -1:
        armourValue = possession[
            armourValueIndex + 2 : armourValueIndex + armourEndIndex
        ]
        description = f"<p>{possession[armourValueIndex + armourEndIndex + 3 :-1]}</p>"
    else:
        armourValue = possession[armourValueIndex + 2 : -1]

    armour = armourValue
    return f"""
    {{
        "name": "{armourName}",
        "type": "gear",
        "system": {{
            "description": "{description}",
            "inventorySlots": {int(armourValue) * 2},
            "equipped": true,
            "armourProvided": {armourValue},
            "quantity": 1,
        }},
    }}
"""


def handle_srd_weapon(possession):
    baseWeaponIndex = possession.lower().index("damage as")
    baseWeaponName = possession[baseWeaponIndex + 10 : -1]
    if "beast" in baseWeaponName.lower():
        baseWeaponName = f"damage_as_{baseWeaponName}"
    baseWeaponJson = find_json(baseWeaponName, "weapon")

    if not baseWeaponJson:
        return baseWeaponJson

    weaponName = possession[2 : baseWeaponIndex - 2]
    itemJson = json.loads(baseWeaponJson)
    item = baseWeaponJson.replace(itemJson["name"], weaponName)

    return item


def handle_new_item_simple(possession):
    global attributionJsonText
    return f"""
    {{
        "name": "{clear(possession)[2:]}",
        "type": "gear",
        "system": {{
            "inventorySlots": 1,
            "equipped": true,
            "quantity": 1,
            "description": "",
            {attributionJsonText},
        }},
    }}
"""


def handle_new_item(possession):
    global attributionJsonText
    if "(" not in possession:
        return handle_new_item_simple(possession)

    newItemRegex = r"^- (?P<name>.*) \([Ss]lot:?\s?(?P<slot>.*?)(?: - (?P<description>.*?))?\).?\s?$"
    clearItem = clear(possession)
    itemMatch = re.match(newItemRegex, clearItem)

    if not itemMatch:
        errorList.append(f'NEW ITEM "{clear(possession)}" has format error')
        return None

    itemName = itemMatch.group("name")
    slots = itemMatch.group("slot") or 1
    description = itemMatch.group("description") or ""
    if description:
        description = f"<p>{clear(description)}</p>"

    newGear = f"""
    {{
        "name": "{itemName}",
        "type": "gear",
        "img": "modules/troika-community-content/assets/tokens/item.svg",
        "system": {{
            "description": "{description}",
            "inventorySlots": {slots},
            "equipped": true,
            "quantity": 1,
            {attributionJsonText},
        }},
    }}
"""
    if description:
        newGearList.append(newGear)
    return newGear


def handle_possession(possession):
    if "(damage as" in possession.lower():
        return handle_srd_weapon(possession)

    if "(armour:" in possession.lower():
        return handle_armour(possession)

    item = handle_srd_possession(possession)
    if item:
        return item

    return handle_new_item(possession)


def handle_possessions(possessions: list[str]):
    items = []
    for line in possessions:
        line = clear(line)
        if not line.strip():
            continue

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
    global attributionJsonText
    newItemRegex = r"^(?P<rank>\d*?) (?P<name>.*?)(?:\s\((?P<description>.*?)\))?$"
    clearSkill = skill
    itemMatch = re.match(newItemRegex, clearSkill)

    if not itemMatch:
        errorList.append(f'NEW SKILL "{skill}" has format error')
        return None

    itemName = itemMatch.group("name")
    rank = itemMatch.group("rank")
    description = itemMatch.group("description") or ""

    if description:
        description = f"<p>{description}</p>"

    newSkill = f"""
    {{
        "name": "{itemName}",
        "type": "skill",
        "img": "modules/troika-community-content/assets/tokens/skill.svg",
        "system": {{
            "description": "{description}",
            "rank": "{rank}",
            {attributionJsonText},
        }},
    }}
"""
    if description:
        newSkillList.append(newSkill)
    return newSkill


def handle_skill(skill: str):
    if "(" in skill:
        return handle_new_skill(skill)

    item = handle_srd_skill(skill)
    if not item:
        item = handle_new_skill(skill)

    return item


def handle_srd_spell(spell: str):
    spaceIndex = spell.index(" ")
    item = find_json(
        clear(spell[spaceIndex + 1 :])
        .lower()
        .replace("'", "_")
        .replace("spell - ", ""),
        "spell",
    )
    if not item:
        return item

    item = item.replace('"rank": "1",', f'"rank": "{spell[:spaceIndex]}",')
    return item


def handle_attack_spell(spell, spell_description: str):
    if not spell_description.startswith("<p>damage: "):
        return ""

    damageRegex = r"\[(?P<damage>.*?)\]"
    itemMatch = re.search(damageRegex, spell_description)

    if not itemMatch:
        errorList.append(f'NEW SPELL "{spell}" has format error')
        return None

    damageList = itemMatch.group("damage").split(",")

    return f"""
"canAttack": true,
"attack": {{
      "dr1": "{damageList[0].strip()}",
      "dr2": "{damageList[1].strip()}",
      "dr3": "{damageList[2].strip()}",
      "dr4": "{damageList[3].strip()}",
      "dr5": "{damageList[4].strip()}",
      "dr6": "{damageList[5].strip()}",
      "dr7": "{damageList[6].strip()}",
    }},
"""


def handle_new_spell(spell: str):
    global attributionJsonText
    newSpellRegex = r"^(?P<rank>\d*?) Spell [–-] (?P<name>.*?) \((?P<cost>.*?) -\s?(?P<description>.*?)\)$"
    clearSpell = clear(spell)
    itemMatch = re.match(newSpellRegex, clearSpell)

    if not itemMatch:
        errorList.append(f'NEW SPELL "{clearSpell}" has format error')
        return None

    itemName = itemMatch.group("name")
    rank = itemMatch.group("rank")
    cost = itemMatch.group("cost")
    description = clear(itemMatch.group("description"))
    if description:
        description = f"<p>{description}</p>"

    if not cost or not description:
        errorList.append(f'NEW SPELL "{clearSpell}" has format error')
        return None

    attackInfo = handle_attack_spell(spell, description)
    if attackInfo:
        descIndex = description.index("-")
        description = f"<p>{description[descIndex+2:]}"

    newSpell = f"""
    {{
        "name": "{itemName}",
        "type": "spell",
        "img": "modules/troika-community-content/assets/tokens/spell.svg",
        "system": {{
            "description": "{description}",
            "rank": "{rank}",
            "castingCost": "{cost}",
            {attributionJsonText},
            {attackInfo}
        }},
    }}
"""

    newSpellList.append(newSpell)
    return newSpell


def handle_spell(spell: str):
    if "(" in spell:
        return handle_new_spell(spell)

    return handle_srd_spell(spell)


def handle_advanced_skill(advanced_skill: str):
    if "spell - " in advanced_skill.lower():
        return handle_spell(advanced_skill)

    return handle_skill(advanced_skill)


def handle_advanced_skills(adavnced_skills: list[str]):
    items = []
    for line in adavnced_skills:
        line = clear(line)
        if not line.strip():
            continue

        item = handle_advanced_skill(line)
        if item:
            items.append(item)
    return items


def handle_img(backgroundName):
    fileName = unidecode(backgroundName.lower().replace(" ", "-").replace(",", "").replace("[", "").replace("]", ""))
    backgroundImg = f"./assets/arts/{folder}/{fileName}.webp"
    if os.path.isfile(backgroundImg):
        backgroundImg = (
            f"modules/troika-community-content/assets/arts/{folder}/{fileName}.webp"
        )
        return backgroundImg

    return "modules/troika-community-content/assets/tokens/backgrounds.svg"


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
    return current.replace("\n", "").replace('"', '\\"').replace("–", "-").strip()


def addBackground(lines):
    global attributionJsonText
    name = clear(lines[0])

    possessionsLine = lines.index("POSSESSIONS:\n")
    advancedSkillsLine = lines.index("ADVANCED SKILLS:\n")
    attributionLine = len(lines) - 2

    specialLine = attributionLine
    special = ""
    if "SPECIAL\n" in lines:
        specialLine = lines.index("SPECIAL\n")
        special = clear_list(lines[specialLine + 1 : attributionLine])

    source = clear(lines[attributionLine][13:])
    link = clear(lines[attributionLine + 1][5:])

    attributionJsonText = f""""attribution": {{
    "source": "{source} [Troika! Community Jam: Backgrounds {complement}]",
    "link": "{link}"
}}"""

    possessions = handle_possessions(lines[possessionsLine + 1 : advancedSkillsLine])
    advancedSkills = handle_advanced_skills(lines[advancedSkillsLine + 1 : specialLine])

    notes = clear_list(lines[1:possessionsLine])

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
        {attributionJsonText},
        special: "{special}",
        notes: "{notes}"
    }},
    items: {items},
    folder: moduleFolder.id
}}, {{ pack:"troika-community-content.troika-community-content-backgrounds" }});"""

    command = (
        command.replace("True", "true")
        .replace("False", "false")
        .replace(" None", " null")
    )
    with open("result.js", "a") as file:
        file.write(command)


folder = sys.argv[1]
complement = sys.argv[2]
filterIndex = sys.argv.index("--filter") if "--filter" in sys.argv else -1
filter = sys.argv[filterIndex + 1] if filterIndex > -1 else ""
deleteExistingFolders = "--delete" in sys.argv


result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./submissions/{folder}")
    for f in filenames
]

if filter:
    result = [f for f in result if filter in f.lower()]

result = sorted(result, key=str.casefold)


with open("result.js", "w") as file:
    if deleteExistingFolders:
        file.write(
            f"""
const moduleList = ["backgrounds", "skills", "spells", "gear"];
for (const packName of moduleList) {{
    moduleFolder = game.packs.get(`troika-community-content.troika-community-content-${{packName}}`).folders.getName("CJ: Backgrounds {complement}");
    if (moduleFolder){{
        console.log(packName, moduleFolder);
        await moduleFolder.delete({{deleteSubfolders: true, deleteContents: true}});
    }}
}}
"""
        )

    file.write(
        f"""moduleFolder = await game.packs.get("troika-community-content.troika-community-content-backgrounds").folders.getName("CJ: Backgrounds {complement}");

if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Actor",
        name: "CJ: Backgrounds {complement}",
        color: "#AA0000"
    }}, {{ pack:"troika-community-content.troika-community-content-backgrounds" }});
}}
"""
    )

for file in result:
    errorList.clear()
    armour = 0

    with open(file, "r") as f:
        lines = f.readlines()
    try:
        addBackground(lines)
        if len(errorList):
            print(clear(lines[0]))
            for e in errorList:
                print(f"- {e}")
            print("=================================")
    except Exception as e:
        print(file, e)


with open("result.js", "a") as file:
    file.write(
        f"""
moduleFolder = game.packs.get("troika-community-content.troika-community-content-skills").folders.getName("CJ: Backgrounds {complement}");

if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Item",
        name: "CJ: Backgrounds {complement}",
        color: "#AA0000"
    }}, {{ pack:"troika-community-content.troika-community-content-skills" }});
}}
await Item.createDocuments([
"""
    )

    for newSkill in newSkillList:
        newSkill = re.sub(rankRegex, '"rank": "1"', newSkill)
        file.write(
            f"""{newSkill[:-2]}
    folder: moduleFolder.id }},
"""
        )
    file.write(
        '], { pack:"troika-community-content.troika-community-content-skills" });'
    )

    file.write(
        f"""
moduleFolder = game.packs.get("troika-community-content.troika-community-content-spells").folders.getName("CJ: Backgrounds {complement}");

if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Item",
        name: "CJ: Backgrounds {complement}",
        color: "#AA0000"
    }}, {{ pack:"troika-community-content.troika-community-content-spells" }});
}}
await Item.createDocuments([
"""
    )

    for newSpell in newSpellList:
        newSpell = re.sub(rankRegex, '"rank": "1"', newSpell)
        file.write(
            f"""{newSpell[:-2]}
    folder: moduleFolder.id }},
"""
        )
    file.write(
        '], { pack:"troika-community-content.troika-community-content-spells" });'
    )

    file.write(
        f"""
moduleFolder = game.packs.get("troika-community-content.troika-community-content-gear").folders.getName("CJ: Backgrounds {complement}");

if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Item",
        name: "CJ: Backgrounds {complement}",
        color: "#AA0000"
    }}, {{ pack:"troika-community-content.troika-community-content-gear" }});
}}
await Item.createDocuments([
"""
    )

    for newGear in newGearList:
        file.write(
            f"""{newGear[:-2]}
    folder: moduleFolder.id }},
"""
        )
    file.write('], { pack:"troika-community-content.troika-community-content-gear" });')
