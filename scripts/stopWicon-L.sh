#!/usr/bin/env bash

ps -ef | grep wicon_lite_main.py | grep -v grep | awk '{print $2}' | xargs kill -9
