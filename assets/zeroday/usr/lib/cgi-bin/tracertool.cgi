#!/bin/bash
echo "Content-type: text/html"
echo ""
echo "<html><head><title>Super Cool Webpage"
echo "</title></head>"
echo "<b>MORTY'S MACHINE TRACER MACHINE</b>"
echo "<br>Enter an IP address to trace.</br>"
echo "<form action=/cgi-bin/tracertool.cgi"
echo "    method=\"GET\">"
echo "<textarea name=\"ip\" cols=40 rows=4>"
echo "</textarea>"
echo "<input type=\"submit\" value=\"Trace!\">"
echo "</form>"

OIFS="$IFS"

IFS="${IFS}&"
set $QUERY_STRING > /dev/null
args="$*"
IFS="$OIFS"
IP=""

if [ -z "$QUERY_STRING" ]; then
    exit 0
fi

IP=`echo "$QUERY_STRING" | sed -n 's/^.*ip=\([^&]*\).*$/\1/p' | sed "s/%3B/;/g" | sed "s/%20/ /g" | sed "s/%2F/\//g" | sed "s/\+/ /g" | sed "s/%3C/\</g" | sed "s/%3E/\>/g"`

echo "<pre>"
eval "traceroute $IP"
echo "</pre>"
echo "</html>"
exit 0
