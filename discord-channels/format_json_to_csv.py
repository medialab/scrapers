import json
import csv
import sys
from glob import glob

def parse_channel_id(url):
    return url.split("/")[5].strip()

def write_csv_formatted_result(url):
    channel_id = parse_channel_id(url)

    with open("{}_all_pages.csv".format(channel_id), "w") as fo:
        writer = csv.writer(fo)
        writer.writerow(["id", "content", "username", "global_name", "timestamp", "mentions"])


        for file in sorted(glob("{}*.json".format(channel_id))):
            print("Load page: {}".format(file))

            with open(file, "r") as f:
                data = json.load(f)


                for message in data:
                    writer.writerow([
                        message["id"],
                        message["content"],
                        message["author"]["username"],
                        message["author"]["global_name"],
                        message["timestamp"],
                        "|".join(mention["username"] for mention in message["mentions"])
                    ])

if __name__ == "__main__":
    url = sys.argv[1]
    write_csv_formatted_result(url)