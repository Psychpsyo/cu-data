# 
# This file runs as a Github Action and updates the following cloud variables in
# Neos based on the data in cards.txt and the NEOS_CREDENTIALS repository secret.
# 
# {0} in these names is a placeholder for an index that ranges from 0 to however
# many atlases for the given card type there are.
# 
# {lang} is a placeholder for the language code associated with the atlas.
# Currently only "en" and "ja" are possible.
# 
# G-Cross-Universe.unitCount
# G-Cross-Universe.spellCount
# G-Cross-Universe.itemCount
# G-Cross-Universe.tokenCount
# G-Cross-Universe.unitAtlas{0}{lang}
# G-Cross-Universe.spellAtlas{0}{lang}
# G-Cross-Universe.itemAtlas{0}{lang}
# G-Cross-Universe.tokenAtlas{0}{lang}

import os
import requests
import json
import sys
import time

# TODO: Switch back to api.neos.com once that SSL cert gets renewed
neosApiUrl = "https://cloudx.azurewebsites.net/"

languages = ["en", "ja"]
langLinkColumn = {
	"en": 4,
	"ja": 5
}
cardTypes = ["U", "S", "I", "T"]
# the way card types are identified in the cloud variable names
cardTypeNames = {
	"U": "unit",
	"S": "spell",
	"I": "item",
	"T": "token"
}

# card atlas links will be filled into these
atlases = {}

for lang in languages:
	atlases[lang] = {}
	for type in cardTypes:
		atlases[lang][type] = []

cardAmounts = {
	"U": 0,
	"S": 0,
	"I": 0,
	"T": 0
}

# checks if a potential link from cards.txt is actually valid and not just a placeholder
def isValidNeosdbLink(link):
	return link.startswith("neosdb:///") and len(link) > 16 # 16 is enough for "neosdb:///", a 4 letter file extension (.webp) and one character inbetween

# read all atlas links and amounts of cards from cards.txt
with open("cards.txt", "r", encoding="utf-8") as cardList:
	for line in cardList:
		if len(line) > 0:
			parts = line.split("|")
			cardType = line[0] # "U", "S", "I" or "T" for Unit, Spell, Item or Token
			atlasIndex = int(parts[6]) # the how many'th card in the atlas this is
			
			cardAmounts[cardType] += 1
			
			for lang in languages:
				atlasLink = parts[langLinkColumn[lang]] # Link to the card atlas
				
				# Ends up keeping the last valid atlas link it finds for each atlas
				if isValidNeosdbLink(atlasLink):
					if atlasIndex == 0:
						atlases[lang][cardType].append(atlasLink)
					else:
						atlases[lang][cardType][-1] = atlasLink

print("Found:")
print(str(cardAmounts["U"]) + " Units")
print(str(cardAmounts["S"]) + " Spells")
print(str(cardAmounts["I"]) + " Items")
print(str(cardAmounts["T"]) + " Tokens\n\n")

# prepare list of cloud var definitions to send to Neos' API
cloudVars = []
# card amounts
for type in cardTypes:
	cloudVars.append({
			"ownerId": "G-Cross-Universe",
			"path": "G-Cross-Universe." + cardTypeNames[type] + "Count",
			"value": str(cardAmounts[type])
		}
	)
# card atlas links
for lang in languages:
	for type in cardTypes:
		for i, link in enumerate(atlases[lang][type]):
			cloudVars.append({
					"ownerId": "G-Cross-Universe",
					"path": "G-Cross-Universe." + cardTypeNames[type] + "Atlas" + str(i) + lang,
					"value": atlases[lang][type][i]
				}
			)

# Dump it to the console for good measure
print("Setting the following cloud vars:")
print(json.dumps(cloudVars, indent=4) + "\n\n")

print("Loading Neos credentials...")
neosCredentials = os.getenv("NEOS_CREDENTIALS")
if not neosCredentials:
	print("Could not load Neos credentials, exiting.")
	sys.exit(1)

print("Sucessfully read credentials.")
neosCredentials = neosCredentials.split("\n")
username = neosCredentials[0]
userId = neosCredentials[1]
password = neosCredentials[2]

# log in to the Neos account
print("Logging in to Neos account...")
loginResponse = requests.post(
	neosApiUrl + "api/userSessions",
	json = {
		"username": username,
		"password": password,
		"rememberMe": False
	}
)

if loginResponse.status_code != 200:
	print("Could not log in to Neos with the given credentials. (Error Code " + str(loginResponse.status_code) + ", Error message \"" + loginResponse.text + "\")")
	sys.exit(1)

print("Sucessfully logged in.")
sessionToken = loginResponse.json()["token"]

print("Updating cloud variables.")
updateError = False
batchSize = 32
# batch the cloud var update list into groups of 32 since that is the limit of Neos' API
for batch in range(0, len(cloudVars), batchSize):
	print("Submitting batch #" + str(int(batch / 32)) + ".")
	updateResponse = requests.post(
		neosApiUrl + "api/writevars",
		headers = {
			"Authorization": "neos " + userId + ":" + sessionToken
		},
		json = cloudVars[batch:batch+batchSize]
	)
	
	if updateResponse.status_code != 200:
		print("Failed to update cloud variable batch #" + str(int(batch / 32)) + " (Error Code " + str(updateResponse.status_code) + ", Error message \"" + updateResponse.text + "\")")
		updateError = True
	# hoping to not get caught in some undocumented rate-limiting system
	time.sleep(2)

# log out of the Neos account
print("Logging out of Neos account.")
requests.delete(
	neosApiUrl + "api/userSessions/" + userId + "/" + sessionToken,
	headers = {
		"Authorization": "neos " + userId + ":" + sessionToken
	}
)

sys.exit(1 if updateError else 0)