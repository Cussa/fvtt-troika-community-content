import json
import os
import re


nameRegex = re.compile(r"[^a-zA-Z0-9]")


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

    link = f"""<li><a href="#{link}">{npc["name"]}</a></li>"""

    return [command, link]


result = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(f"./src/packs")
    for f in filenames
    if not f.startswith("folder")
]
result.sort()
info = []
bestiaryList = []

for file in result:

    with open(file, "r") as f:
        filedata = json.load(f)
    result = addNpc(filedata)
    info.append(result[0])
    bestiaryList.append(result[1])


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

<p>The content from this module is created by the Troika Community,<br>via the <a href="https://cussa.itch.io/" target="_blank">Jams</a> organized by <a href="https://hodpub.com" target="_blank">Cussa Mitre/Hod Publishing</a> and other resources.</p>

<p style="margin:0">Sources:</p>
<ul style="margin:0; margin-bottom: 1em;">
<li><a href="https://itch.io/jam/troika-community-jam-bestiary-2024" target="_blank">Troika! Community Jam: Bestiary 2024</a>
</ul>
<p>All creations included in this module were authorized by the authors.<br>Each author is attributed on the item created.</p>

<p class="italic">The Troika Community Content Foundry module is an independent production<br>by several creators and is not affiliated with the Melsonian Arts Council.</p>
<img src="imgs/compatible-with-troika.png">
</div>
<table class="page">
<thead><tr><td>Troika! Community Content</td></tr></thead>
<tfoot><tr><td>Organized and Compiled by Cussa Mitre - Layout by Rodrigo Grola - Hod Publishing</td></tr></tfoot>
<tbody><tr><td>
<div class="title">
<h1><a class="bookmark" href="https://group/Bestiary">Bestiary</a></h1>
</div>
{"".join(info)}
<div class="title">
<h1>Thanks for supporting the Troika Community!</h1>
</div>
</td></tr></tfoot></table>
</body>
</html>
"""
    )

# <ol>
# {"".join(bestiaryList)}
# </ol>
