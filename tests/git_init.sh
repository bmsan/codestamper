#!/bin/bash

touch file1.py
touch file2.py
touch file3.json

git init
git add file1.py
git add file2.py

git commit -m "c1"

echo mod1 >> file1.py

git add  file1.py
git commit -m "c2"

### 2 commits clean workspace

# change branch push

#