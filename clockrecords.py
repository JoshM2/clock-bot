import sqlite3
import requests
import logging
import json

def getClockRecords(client, channel_id):
    recordArr = []
    connection = sqlite3.connect("./database.sqlite")
    cursor = connection.cursor()

    # add a table for records to sqlite3
    cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS records (
        id VARCHAR(255) PRIMARY KEY,
        tag VARCHAR(255),
        type VARCHAR(255),
        country_iso VARCHAR(8),
        country_name VARCHAR(255),
        attemptResult VARCHAR(255),
        name VARCHAR(255),
        event VARCHAR(255),
        eventId VARCHAR(255),
        competitionId VARCHAR(255),
        competitionName VARCHAR(255),
        roundId VARCHAR(255)
        )
        """
        )
    connection.commit()

  #query stuff
    try:
      def getRecentRecords():
            response = requests.post(
                url="https://live.worldcubeassociation.org/api/graphql",
                json={
                    "query": """
              {
                recentRecords {
                  id
                  type
                  tag
                  attemptResult
                  result {
                    attempts{
                      result
                    }
                    person {
                      name
                      wcaId
                      country {
                        iso2
                        name
                      }
                    }
                    round {
                      id
                      competitionEvent {
                        event{
                          id
                          name
                        }
                        competition {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            """
                },
            )

            allRecords = json.loads(response.text)["data"]["recentRecords"]
            
            # filter to only clock results
            records = [
                x
                for x in allRecords
                if x["result"]["round"]["competitionEvent"]["event"]["name"] == "Clock"
            ]

            for record in records:
              # print(record)
              if not cursor.execute(
                    "SELECT * FROM records WHERE id = ?", (record["id"],)
                ).fetchall():
                    
                    #added this line so it runs only if the person isn't in the database already
                    try:
                      res = requests.get('https://www.worldcubeassociation.org/api/v0/persons/'+record["result"]["person"]["wcaId"])
                    except:
                      #stupid exceptions for first-timers
                      logging.warning("Person does not have wcaId: "+record["result"]["person"]["name"])
                      res = False
                    
                    if(res):
                      pfp = json.loads(res.text)["person"]["avatar"]["url"]
                    else:
                      pfp = False
                    cursor.execute(
                        "INSERT INTO records (id, tag, type, country_name, attemptResult, name, event, competitionName, roundId, country_iso, eventId, competitionId) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?, ?,?,?)",
                        (
                            record["id"],
                            record["tag"],
                            record["type"],
                            record["result"]["person"]["country"]["name"],
                            record["attemptResult"],
                            record["result"]["person"]["name"],
                            record["result"]["round"]["competitionEvent"]["event"]["name"],
                            record["result"]["round"]["competitionEvent"]["competition"]["name"],
                            record["result"]["round"]["id"],
                            record["result"]["person"]["country"]["iso2"],
                            record["result"]["round"]["competitionEvent"]["event"]["id"],
                            record["result"]["round"]["competitionEvent"]["competition"]["id"]
                        ),
                    )
                    record_list = [
                            record["id"],
                            record["tag"],
                            record["type"],
                            record["result"]["person"]["country"]["name"],
                            record["attemptResult"],
                            record["result"]["person"]["name"],
                            record["result"]["round"]["competitionEvent"]["event"]["name"],
                            record["result"]["round"]["competitionEvent"]["competition"]["name"],
                            record["result"]["attempts"],
                            record["result"]["round"]["id"],
                            record["result"]["person"]["country"]["iso2"],
                            record["result"]["round"]["competitionEvent"]["event"]["id"],
                            record["result"]["round"]["competitionEvent"]["competition"]["id"],
                            record["result"]["person"]["wcaId"],
                            record["result"]["person"]["country"]["iso2"],                            
                            pfp
                            ]
                    recordArr.append(record_list)
                    print("added:\n" + json.dumps(record["result"]["person"]["name"]))

              else:
                    print("exists " + json.dumps(record["result"]["person"]["name"]))

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    getRecentRecords()
    connection.commit()
    connection.close()
    return recordArr

#doesn't want to work for minutes but whatever that doesn't matter for clock
def formatTime(centiseconds):
    minutes = centiseconds // 6000
    seconds = (centiseconds // 100) % 60
    centiseconds = centiseconds % 100
    
    if minutes > 0:
        time_string = f"{minutes}:{seconds:02d}.{centiseconds:02d}"
    else:
        time_string = f"{seconds}.{centiseconds:02d}"
    
    return time_string
