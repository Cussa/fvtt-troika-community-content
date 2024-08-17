import json
import os
import re
from datetime import datetime


nameRegex = re.compile(r"[^a-zA-Z0-9]")
bestiaryList = []
bestiaryIndex = []
backgroundsList = []
backgroundsIndex = []


def addNpc(npc):
    system = npc["system"]
    special = ""
    damage = ""
    image = ""

    if system["special"]:
        special = f"<h2>Special</h2>{system['special']}"

    if npc["img"] != "icons/svg/mystery-man.svg":
        image = f"""<img src="{npc["img"].replace("modules/troika-community-content/", "")}" >"""

    if len(npc["items"]):
        # damage = '<p><span class="bold">DAMAGE:</span> '
        for item in npc["items"]:
            damage += f"""
<table class="attack">
    <caption>{item["name"]}</caption>
    <tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7+</td></tr>
    <tr><td>{item["system"]["attack"]["dr1"]}</td><td>{item["system"]["attack"]["dr2"]}</td><td>{item["system"]["attack"]["dr3"]}</td><td>{item["system"]["attack"]["dr4"]}</td><td>{item["system"]["attack"]["dr5"]}</td><td>{item["system"]["attack"]["dr6"]}</td><td>{item["system"]["attack"]["dr7"]}</td></tr>
</table>
"""
    link = npc["name"].replace(" ", "§")  # re.sub(nameRegex, "", npc["name"])
    command = f"""
<div class="enemy" id="{link}">
    
    <div class="text">
        <h1><a class="bookmark" href="https://internal/{link}">{npc["name"]}</a></h1>
        <p><a href="{system["attribution"]["link"]}" target="_blank">{system["attribution"]["source"].replace("[", "<br>[")}</a></p>
        {system["notes"]}
        {special}
    </div>
    <div class="info">
        {image}
        <p><span class="bold">SKILL:</span> <span class="italic">{system["skill"]["value"]}</span></p>
        <p><span class="bold">STAMINA:</span> <span class="italic">{system["stamina"]["value"]}</span></p>
        <p><span class="bold">INITIATIVE:</span> <span class="italic">{system["initiativeTokens"]}</span></p>
        <p><span class="bold">ARMOUR:</span> <span class="italic">{system["armour"]}</span></p>
        {damage}

        <table class="mien">
            <caption>Mien</caption>
            <tr><td>1</td><td>{system["mienOptions"]["0"]["description"]}</td></tr>
            <tr><td>2</td><td>{system["mienOptions"]["1"]["description"]}</td></tr>
            <tr><td>3</td><td>{system["mienOptions"]["2"]["description"]}</td></tr>
            <tr><td>4</td><td>{system["mienOptions"]["3"]["description"]}</td></tr>
            <tr><td>5</td><td>{system["mienOptions"]["4"]["description"]}</td></tr>
            <tr><td>6</td><td>{system["mienOptions"]["5"]["description"]}</td></tr>
        </table>
    </div>
</div>"""

    author = system["attribution"]["source"][
        : system["attribution"]["source"].index(" [")
    ]
    link = f"""<li><a class="bookmark" href="https://index/Bestiary±{link}"><em>{npc["name"]}</em> by {author}</a></li>"""

    return [command, link]


def handlePossession(item):
    name = item["name"]
    inventorySlots = item["system"]["inventorySlots"]
    description = ""
    attribution = item["system"]["attribution"]
    armour = ""
    if attribution and attribution["source"]:
        description = item["system"]["description"].replace("<p></p>", "")
        if description:
            description = f"<em>{description}</em>"
    if item["system"]["armourProvided"] > 0:
        armourValue = item["system"]["armourProvided"]
        armour = f" - Armour: {armourValue}"
    return f"<li>{name} (Slot: {inventorySlots}{armour}){description}</li>"


def handleSkill(item):
    name = item["name"]
    rank = item["system"]["rank"]
    description = ""
    attribution = item["system"]["attribution"]
    if attribution and attribution["source"]:
        description = item["system"]["description"].replace("<p></p>", "")
        if description:
            description = f"<em>{description}</em>"
    return f"<li>{rank} {name}{description}</li>"


def handleSpell(item):
    name = item["name"]
    rank = item["system"]["rank"]
    description = ""
    cost = item["system"]["castingCost"]
    attribution = item["system"]["attribution"]
    if attribution and attribution["source"]:
        description = item["system"]["description"].replace("<p></p>", "")
        description = description.replace(
            "@UUID[Compendium.troika.troika-srd-roll-tables.RollTable.F5Hxv1QRaOCAVbpg]{SRD Random Spell Roll Table}",
            "Roll the SRD Random Spell Table",
        )
        if description:
            description = f"<em>{description}</em>"
    return f"<li>{rank} Spell - {name} (Cost: {cost}){description}</li>"


def addBackground(background):
    system = background["system"]
    special = ""
    image = f"""<img src="{background["img"].replace("modules/troika-community-content/", "")}" >"""

    if system["special"]:
        special = f"<h2>Special</h2>{system['special']}"

    possessionsList = []
    advancedSkillsList = []

    damage = ""

    for item in background["items"]:
        if item["type"] == "gear":
            possessionsList.append(handlePossession(item))
        elif item["type"] == "skill":
            advancedSkillsList.append(handleSkill(item))
        elif item["type"] == "spell":
            advancedSkillsList.append(handleSpell(item))

        if item["system"]["canAttack"]:
            damage += f"""
<table class="attack">
    <caption>{item["name"]}</caption>
    <tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7+</td></tr>
    <tr><td>{item["system"]["attack"]["dr1"]}</td><td>{item["system"]["attack"]["dr2"]}</td><td>{item["system"]["attack"]["dr3"]}</td><td>{item["system"]["attack"]["dr4"]}</td><td>{item["system"]["attack"]["dr5"]}</td><td>{item["system"]["attack"]["dr6"]}</td><td>{item["system"]["attack"]["dr7"]}</td></tr>
</table>
"""

    advancedSkillsList.sort(reverse=True)

    #     if len(background["items"]):

    #         for item in background["items"]:
    #             damage += f"""
    # <table class="attack">
    #     <caption>{item["name"]}</caption>
    #     <tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7+</td></tr>
    #     <tr><td>{item["system"]["attack"]["dr1"]}</td><td>{item["system"]["attack"]["dr2"]}</td><td>{item["system"]["attack"]["dr3"]}</td><td>{item["system"]["attack"]["dr4"]}</td><td>{item["system"]["attack"]["dr5"]}</td><td>{item["system"]["attack"]["dr6"]}</td><td>{item["system"]["attack"]["dr7"]}</td></tr>
    # </table>
    # """
    link = background["name"].replace(" ", "§")  # re.sub(nameRegex, "", npc["name"])
    command = f"""
<div class="background" id="{link}">
    
    <div class="text">
        <h1><a class="bookmark" href="https://internal/{link}">{background["name"]}</a></h1>
        <p><a href="{system["attribution"]["link"]}" target="_blank">{system["attribution"]["source"].replace("[", "<br>[")}</a></p>
        {system["notes"]}
        <h2 class="bold">Possessions</h2>
        <ul>
        {"".join(possessionsList)}
        </ul>
        <h2 class="bold">Advanced Skills</h2>
        <ul>
        {"".join(advancedSkillsList)}
        </ul>
        {special}
    </div>
    <div class="info">
        {image}
        <p><span class="bold">SKILL:</span> <span class="italic">{system["skill"]}</span></p>
        <p><span class="bold">STAMINA:</span> <span class="italic">{system["stamina"]}</span></p>
        <p><span class="bold">INITIATIVE:</span> <span class="italic">{system["initiativeTokens"]}</span></p>
        <p><span class="bold">ARMOUR:</span> <span class="italic">{system["armour"]}</span></p>
        {damage}
    </div>
</div>"""

    author = system["attribution"]["source"][
        : system["attribution"]["source"].index(" [")
    ]
    link = f"""<li><a class="bookmark" href="https://index/Backgrounds±{link}"><em>{background["name"]}</em> by {author}</a></li>"""
    command = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", command)
    command = re.sub(r"\*(.*?)\*", r"<em>\1</em>", command)

    return [command, link]


def addObject(filename, filedata):
    global bestiaryIndex, bestiaryList, backgroundsIndex, backgroundsList
    if "tcc-bestiary" in filename:
        result = addNpc(filedata)
        bestiaryList.append(result[0])
        bestiaryIndex.append(result[1])
    elif "tcc-backgrounds" in filename:
        result = addBackground(filedata)
        backgroundsList.append(result[0])
        backgroundsIndex.append(result[1])


result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./src/packs")
    for f in filenames
    if not f.startswith("folder")
]
result.sort()


# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("%m-%Y (%d.%H.%M)")

for file in result:
    with open(file, "r") as f:
        filedata = json.load(f)
    addObject(file, filedata)


with open("pdf.html", "w") as file:
    file.write(
        f"""<html>
<head>
  <title>Troika! Community Content</title>
  <link rel="stylesheet" type="text/css" href="/Users/cussa/Library/Application Support/FoundryVTT/Data/modules/troika-community-content/css/tcc.css">
</head>
<body>
<div class="title">
<h1>Troika!<br>Community Content</h1>

<p>The content from this module is created by the Troika Community,<br>via the <a href="https://itch.io/jams/hosted-by-cussa" target="_blank">Jams</a> organized by <a href="https://cussa.itch.io" target="_blank">Cussa Mitre/Hod Publishing</a> and other resources.</p>

<p style="margin:0">Sources:</p>
<ul style="margin:0; margin-bottom: 1em;">
<li><a href="https://itch.io/jam/troika-community-jam-bestiary-2024" target="_blank">Troika! Community Jam: Bestiary 2024</a>
<li><a href="https://itch.io/jam/troika-community-jam-backgrounds-2024" target="_blank">Troika! Community Jam: Backgrounds 2024</a>
</ul>
<p>All creations included in this module were authorized by the authors.<br>Each author is attributed on the item created.</p>
<p>Organization and compilation: <a href="https://discord.com/users/416651725060046859">Cussa Mitre</a><br>
Layout and Cover Design: <a href="https://hodpub.com" target="_blank">Rodrigo Grola</a><br>
Publisher: <a href="https://hodpub.com" target="_blank">Hod Publishing</a><br>
Cover Image: <a href="https://commons.wikimedia.org/wiki/File:James_Gillray_-_Weird_Sisters,_Ministers_of_Darkness,_Minions_of_the_Moon_(Thurlow,_Pitt,_and_Dundas)_-_B1981.25.853_-_Yale_Center_for_British_Art.jpg">James Gillray</a>, CC0, via Wikimedia Commons<br>
Icons: Lorc, Delapouite, Willdabeast. Available on <a href="https://game-icons.net" target="_blank">https://game-icons.net</a></p>

<p class="italic">The Troika Community Content is an independent production<br>by several creators and is not affiliated with the Melsonian Arts Council.</p>
<p>Download the Foundry Module with all the content for FREE here:<br><a href="https://foundryvtt.com/packages/troika-community-content">https://foundryvtt.com/packages/troika-community-content</a></p>
<p>Version: {dt_string}</p>
<img src="imgs/compatible-with-troika.png" style="width: 50%">
</div>
<table class="page">
<thead><tr><td><img src="assets/header.webp"></td></tr></thead>
<tfoot><tr><td><hr>{dt_string}</td></tr></tfoot>
<tbody><tr><td>
<div class="page title">
<h1><a class="bookmark" href="https://group/Backgrounds">Backgrounds</a></h1>
</div>
{"".join(backgroundsList)}
<div class="page title">
<h1><a class="bookmark" href="https://group/Bestiary">Bestiary</a></h1>
</div>
{"".join(bestiaryList)}
<div class="page">
<h1><a class="bookmark" href="https://group/Index">Index</a></h1>
<h2>Backgrounds</h2>
<ul>
{''.join(backgroundsIndex)}
</ul>
<h2>Bestiary</h2>
<ul>
{''.join(bestiaryIndex)}
</ul>
</div>
<div class="page title">
<h1>Thanks for supporting the Troika Community!</h1>
</div>
</td></tr></tbody></table>
</body>
</html>
"""
    )

# <ol>
# {"".join(bestiaryList)}
# </ol>
