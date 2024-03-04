#!/bin/bash

lualatex -interaction=nonstopmode -halt-on-error main.tex
lwarpmk cleanall
lwarpmk html
./build-limages-with-margin.lua limages # same as lwarpmk limages but it also makes pngs
sleep 5
python3 postprocessing.py