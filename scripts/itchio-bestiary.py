import json
import os


def handle_damage(damageInfo):
    if "(" not in damageInfo:
        return {"items": "[]", "special": damageInfo.strip()}
    startP = damageInfo.index("(") + 4
    weapon = damageInfo.strip()[startP:-1]
    items = take_item_for_damage(weapon)
    weaponName = damageInfo[6 : startP - 4].replace(":", "").strip()
    itemJson = json.loads(items)
    items = items.replace(itemJson[0]["name"], weaponName)
    return {"items": items, "special": ""}


def take_item_for_damage(weapon):
    weapon = weapon.lower().replace(" ", "_")
    if "beast" in weapon:
        weapon = f"damage_as_{weapon}"
    result = [
        os.path.join(dp, f)
        for dp, dn, filenames in os.walk(
            "../../systems/troika/src/packs/troika-srd-weapons-and-attacks"
        )
        for f in filenames
        if f.lower().startswith(f"gear_{weapon}")
    ]
    if len(result) == 0:
        raise Exception(f'Weapon "{weapon}" not found')
    if len(result) > 1:
        raise Exception(f'MORE than one Weapon "{weapon}" found')

    with open(result[0], "r") as f:
        items = f.read()
    return f"[{items}]"


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


def addMonster(lines):

    name = clear(lines[0])
    skill = clear(lines[1], "SKILL:")
    stamina = clear(lines[2], "STAMINA:")
    initative = clear(lines[3], "INITIATIVE:")
    armour = clear(lines[4], "ARMOUR:")

    mienLine = lines.index("MIEN\n")
    specialLine = mienLine
    special = ""
    if "SPECIAL\n" in lines:
        specialLine = lines.index("SPECIAL\n")
        special = clear_list(lines[specialLine + 1 : mienLine])

    notes = clear_list(lines[6:specialLine])

    source = clear(lines[mienLine + 8])
    link = clear(lines[mienLine + 11])

    damageResult = handle_damage(lines[5])
    items = damageResult["items"]
    if damageResult["special"]:
        newSpecial = damageResult["special"]
        special = f"<p>{newSpecial}</p>{special}"

    command = f"""
await Actor.create(
{{
    name: '{name}',
    type: "npc",
    system: {{
        initiativeTokens: {initative},
        stamina: {{
            value: {stamina},
            max: {stamina}
        }},
        skill: {{
            value: {skill}
        }},
        armour: {armour},
        mienOptions: {{
            0: {{
                number: 1,
                description: "{clear(lines[mienLine + 1], "1:")}"
            }},
            1: {{
                number: 2,
                description: "{clear(lines[mienLine + 2], "2:")}"
            }},
            2: {{
                number: 3,
                description: "{clear(lines[mienLine + 3], "3:")}"
            }},
            3: {{
                number: 4,
                description: "{clear(lines[mienLine + 4], "4:")}"
            }},
            4: {{
                number: 5,
                description: "{clear(lines[mienLine + 5], "5:")}"
            }},
            5: {{
                number: 6,
                description: "{clear(lines[mienLine + 6], "6:")}"
            }}
        }},
        attribution: {{
            source: "{source} [Troika! Community Jam: Bestiary 2024]",
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


result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./submissions")
    for f in filenames
    #if not f.startswith("imported_")
]

with open("result.js", "w") as file:
    file.write(
        f"""moduleFolder = game.folders.getName("Community Jam: Bestiary 2024");
if (moduleFolder == undefined){{
    moduleFolder = await Folder.create({{
        type: "Actor",
        name: "Community Jam: Bestiary 2024"
    }});
}}
"""
    )

for file in result:
    with open(file, "r") as f:
        lines = f.readlines()
    addMonster(lines)
