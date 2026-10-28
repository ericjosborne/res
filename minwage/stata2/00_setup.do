*==============================================================================
* 00_setup.do -- paths and settings.  Every other file in stata2/ starts with:  do "stata2/00_setup.do"
*   Run Stata with the working directory set to the minwage/ folder (File > Change Working Directory).
*   Packages used in this folder: reghdfe, ftools, estout (ssc install reghdfe ftools estout).
*==============================================================================
version 16
clear all
set more off
global ROOT  "`c(pwd)'"
global RAW   "$ROOT/data/raw"
global MW    "$ROOT/data/raw/minwage"
global CLEAN "$ROOT/data/clean"
global OUT   "$ROOT/output/stata2"          // every table (.tex) and figure (.png) from this folder goes here
capture mkdir "$OUT"
capture mkdir "$CLEAN"
