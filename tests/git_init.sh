#!/bin/bash

touch file1.py
touch file2.py
touch file3.json

git init
git config user.name "Test Bot"
git config user.email "Testing@git.stamp"

git add file1.py
git add file2.py

git commit -m "c1" --author "Test Bot <testing@git.stamp>"

echo mod1 >> file1.py

git add  file1.py

git commit -m "c2" --author "Gogu Gigi <gogu@gigi.com>"

### 2 commits clean workspace

# change branch push

#