import urllib.request
import json
import datetime as dt
import gspread
from oauth2client.service_account import ServiceAccountCredentials


## table of relative state positions
mapgrid = [
    [0,0,"AK"],
    [0,1,""],
    [0,2,""],
    [0,3,""],
    [0,4,""],
    [0,5,""],
    [0,6,"MP"],
    [0,7,"GU"],

    [1,0,""],
    [1,1,""],
    [1,2,"WA"],
    [1,3,"OR"],
    [1,4,"CA"],
    [1,5,""],
    [1,6,""],
    [1,7,"AS"],

    [2,0,""],
    [2,1,""],
    [2,2,"ID"],
    [2,3,"NV"],
    [2,4,"UT"],
    [2,5,"AZ"],
    [2,6,""],
    [2,7,"HI"],

    [3,0,""],
    [3,1,""],
    [3,2,"MT"],
    [3,3,"WY"],
    [3,4,"CO"],
    [3,5,"NM"],
    [3,6,""],
    [3,7,""],

    [4,0,""],
    [4,1,""],
    [4,2,"ND"],
    [4,3,"SD"],
    [4,4,"NE"],
    [4,5,"KS"],
    [4,6,"OK"],
    [4,7,"TX"],

    [5,0,""],
    [5,1,""],
    [5,2,"MN"],
    [5,3,"IA"],
    [5,4,"MO"],
    [5,5,"AR"],
    [5,6,"LA"],
    [5,7,""],

    [6,0,""],
    [6,1,""],
    [6,2,"IL"],
    [6,3,"IN"],
    [6,4,"KY"],
    [6,5,"TN"],
    [6,6,"MS"],
    [6,7,""],

    [7,0,""],
    [7,1,""],
    [7,2,"WI"],
    [7,3,"OH"],
    [7,4,"WV"],
    [7,5,"NC"],
    [7,6,"AL"],
    [7,7,""],

    [8,0,""],
    [8,1,""],
    [8,2,"MI"],
    [8,3,"PA"],
    [8,4,"VA"],
    [8,5,"SC"],
    [8,6,"GA"],
    [8,7,""],

    [9,0,""],
    [9,1,""],
    [9,2,"NY"],
    [9,3,"NJ"],
    [9,4,"MD"],
    [9,5,"DC"],
    [9,6,""],
    [9,7,"FL"],

    [10,0,""],
    [10,1,"VT"],
    [10,2,"RI"],
    [10,3,"CT"],
    [10,4,"DE"],
    [10,5,""],
    [10,6,""],
    [10,7,""],

    [11,0,"ME"],
    [11,1,"NH"],
    [11,2,"MA"],
    [11,3,""],
    [11,4,""],
    [11,5,""],
    [11,6,"PR"],
    [11,7,"VI"]
    ]


timeNow = dt.datetime.now() - dt.timedelta(hours = 4)
timeNow = timeNow.strftime("%d %b, %I:%M %p")

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)


def getStateDetails():

    sheet = client.open_by_key("1PY38shiRJlVxY35LNjUOu_lhjKeBSuTm1uCCR6-TnII")
    ws = sheet.worksheet("Sheet1")

    global stateDB
    stateDB = ws.get_all_values()

    global totPop
    totPop = 0

    for row in stateDB:
        row[2] = int(row[2].replace(",",""))
        totPop += row[2]  ##  adding state populations to get US pop
##        row.append([])


## state by state data by day
page = urllib.request.urlopen('https://covidtracking.com/api/states/daily')
stateData = page.read()
stateData = json.loads(stateData)

## national data by day
page = urllib.request.urlopen('https://covidtracking.com/api/us/daily')
usData = page.read()
usData = json.loads(usData)

## pulling state details from GSheet
## format: ["CA", "California", 39512223]
getStateDetails()


db = []

## intital db steup
for row in mapgrid:
    i = {
        "abr" : row[2],
        "mapRow" : row[1],
        "mapCol" : row[0]
        }
    db.append(i)

## add state info to db
for row in stateDB:
    for i in db:
        if i["abr"] == row[0]:
            i["name"] = row[1]
            i["pop"] = row[2]
            i["data"] = []

## add state datapoints to db
for i in db:
    for row in stateData:
        if row["state"] == i["abr"]:
            i["data"].append(row)


## nationwide details tile
usTile = {
    "abr" : "US",
    "mapRow" : 0,
    "mapCol" : 3,
    "name" : "United States",
    "pop" : totPop,
    "data" : []
    }

## add national data to db
for row in usData:
    usTile["data"].append(row)

db.append(usTile)


sheet = client.open_by_key("1Z-Nm2Pk2RsIv5cgEPN9B_-8m90WoT1pEeNlWHYjwUOY")
ws = sheet.worksheet("Map")
##ws.clear()


numCols = 12
rowsOffset = 1
dataRows = 3
dataCols = 2

cellList = ws.range(1,1,100,numCols*dataCols)

cellList[0].value = "Last Updated: " + timeNow
#cellList[23].value = "Designed and built by Joel Paul, data from covidtracking.com"

#cellList[29].value = "Region >"
#cellList[53].value = "Cases / Million >"
#cellList[77].value = "Deaths / Million >"
#cellList[56].value = "< 3 Day Δ (Cases)"
#cellList[80].value = "< 3 Day Δ (Deaths)"

cellList[62].value = usData[0]["positive"]
cellList[63].value = usData[0]["positive"] - usData[1]["positive"]
cellList[86].value = usData[0]["death"]
cellList[87].value = usData[0]["death"] - usData[1]["death"]

stateNameCells = []
stateD1Cells = []
stateD2Cells = []

for i in db:
    try:
        if i["abr"] != "":
            cell = (i["mapRow"]*dataRows+rowsOffset)*numCols*dataCols+(i["mapCol"]*dataCols)
            cellList[cell].value = i["abr"]

            ## number positive cases per M population
            if i["data"][0]["positive"] == None:
                casesPop = 0
            else:
                casesPop = round((i["data"][0]["positive"]/i["pop"])*1000000)
            cellList[cell+numCols*dataCols].value = casesPop


            ####################
            if i["data"][0]["positive"] == None or i["data"][3]["positive"] == None:
                pctChg = "0%"
            elif i["data"][3]["positive"] == 0:
                pctChg = "N/A"
            else:
                pctChg = round((i["data"][0]["positive"]-i["data"][3]["positive"])/i["data"][3]["positive"],4)
    ##            pctChg = "+" + str(pctChg) + "%"
            cellList[cell+numCols*dataCols+1].value = pctChg
            ####################

            ## number deaths per M population
            if i["data"][0]["death"] == None:
                deathsPop = 0.00
            else:
                deathsPop = round((i["data"][0]["death"]/i["pop"])*1000000,2)
            cellList[cell+2*numCols*dataCols].value = deathsPop

            ####################
            if i["data"][0]["death"] == None or i["data"][3]["death"] == None:
                pctChg = "0%"
            elif i["data"][3]["death"] == 0:
                pctChg = "N/A"
            else:
                pctChg = round((i["data"][0]["death"]-i["data"][3]["death"])/i["data"][3]["death"],4)
    ##            pctChg = "+" + str(pctChg) + "%"
            cellList[cell+2*numCols*dataCols+1].value = pctChg
            ####################
    except Exception:
        continue

outList = []

for cell in cellList:
    if cell.value != "":
        outList.append(cell)

ws.update_cells(outList, value_input_option="RAW")
