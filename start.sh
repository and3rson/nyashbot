#!/bin/bash

echo $$ > /tmp/nyash-start.pid

while true
do
	./bot.py
done
