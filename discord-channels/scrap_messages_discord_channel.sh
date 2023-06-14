#!/bin/bash

AUTH=$1
COOKIE=$2
URL=$3
BEFORE=""

URL_ID=$(echo $URL | sed -r 's|^.*/channels/[0-9]+/||' | sed -r 's|[/?].*$||')

PAGE=0
curl "https://discord.com/api/v9/channels/$URL_ID/messages?limit=100" -H "cookie: $COOKIE" -H "authorization: $AUTH" > "${URL_ID}_page_${PAGE}.json"
NEWBEFORE=$(cat "${URL_ID}_page_${PAGE}.json" | grep '}}, {"id":' | sed 's|}}, {"id": "|\n|g' | tail -n 1 | sed 's/".*$//')

while [ ! -z "$NEWBEFORE" ] && [ "$BEFORE" != "$NEWBEFORE" ]; do
  echo $NEWBEFORE $PAGE
  BEFORE="$NEWBEFORE"
  PAGE=$(($PAGE + 1))
  curl "https://discord.com/api/v9/channels/$URL_ID/messages?before=$BEFORE&limit=100" -H "cookie: $COOKIE" -H "authorization: $AUTH" > "${URL_ID}_page_${PAGE}.json"
  NEWBEFORE=$(cat "${URL_ID}_page_${PAGE}.json" | grep '}}, {"id":' | sed 's|}}, {"id": "|\n|g' | tail -n 1 | sed 's/".*$//')
done

