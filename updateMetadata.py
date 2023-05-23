# This script uses the API at https://crossuniverse.net/cardInfo to update the card metadata for the cards.txt file.
# It does so by spitting out a new, updated file called cards.txt.new
# This is intentional since this file is not meant to be run fully unsupervised/automated and is more of a quick helper script to alleviate some manual busywork.

import requests

jaTypes = {
	"Psychic": "PSI",
	"Dragon": "ドラゴン",
	"Figure": "人形",
	"Samurai": "侍",
	"Light": "光",
	"Katana": "刀",
	"Sword": "剣",
	"Curse": "呪い",
	"Earth": "地",
	"Landmine": "地雷",
	"Angel": "天使",
	"Rock": "岩石",
	"Illusion": "幻想",
	"Structure": "建造物",
	"Demon": "悪鬼",
	"Warrior": "戦士",
	"Book": "書物",
	"Plant": "植物",
	"Machine": "機械",
	"Ghost": "死霊",
	"Water": "水",
	"Ice": "氷",
	"Fire": "炎",
	"Beast": "獣",
	"Shield": "盾",
	"Myth": "神話",
	"Spirit": "精霊",
	"Boundary": "結界",
	"Medicine": "薬",
	"Bug": "虫",
	"Gravity": "重力",
	"Chain": "鎖",
	"Armor": "鎧",
	"Dark": "闇",
	"Electric": "雷",
	"Wind": "風",
	"Mage": "魔術師",
	"Fish": "魚",
	"Bird": "鳥"
}

jaResponse = requests.post("https://crossuniverse.net/cardInfo", json={"language": "ja"});
enResponse = requests.post("https://crossuniverse.net/cardInfo", json={"language": "en"});

cards = {}
for card in jaResponse.json():
	cards[card["cardID"]] = {}
	cards[card["cardID"]]["ja"] = card
for card in enResponse.json():
	cards[card["cardID"]]["en"] = card

# Updates rows of this format: U00199|2|200|0|neosdb:///|neosdb:///|18|Ripper Doll/切り裂きドール/きりさきどーる|Dark, Ghost, Figure, Curse/闇,死霊,人形,呪い
upadatedLines = []
with open("cards.txt", "r", encoding="UTF-8") as file:
	for line in file:
		columns = line.split("|")
		jaCard = cards[columns[0]]["ja"]
		enCard = cards[columns[0]]["en"]
		columns[1] = str(jaCard["level"]) if jaCard["level"] != -1 else "?"
		if jaCard["cardType"] == "unit" or jaCard["cardType"] == "token":
			columns[2] = str(jaCard["attack"]) if jaCard["attack"] != -1 else "?"
			columns[3] = str(jaCard["defense"]) if jaCard["defense"] != -1 else "?"
		else:
			columns[2] = "0"
			columns[3] = "0"
		columns[7] = str(enCard["name"] + "/" + jaCard["name"] + "/" + jaCard["nameHiragana"])
		columns[8] = str(", ".join(jaCard["types"]) + "/" + ",".join(map(lambda type: jaTypes[type], jaCard["types"])))
		
		upadatedLines.append("|".join(columns) + "\n")

with open("cards.txt.new", "w", encoding="UTF-8") as file:
	file.writelines(upadatedLines)