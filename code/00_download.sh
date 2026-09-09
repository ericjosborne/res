#!/usr/bin/env bash
# Fetch the raw inputs that are not committed to the repository.
# Everything here is served from GitHub (raw content, release assets, git),
# which is what the build environment could reach.  Small CSVs are already in
# data/raw/; this script re-downloads them only if missing.
set -euo pipefail
cd "$(dirname "$0")/.."

RD=https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master
mkdir -p data/raw/rdatasets data/raw/policyengine/h5 data/raw/owid
for f in AER/Fertility Ecdat/HI wooldridge/cps91 sampleSelection/Mroz87 Ecdat/Workinghours Ecdat/Participation; do
  out=data/raw/rdatasets/$(echo "$f" | tr / _).csv
  [ -s "$out" ] || curl -sSL "$RD/csv/$f.csv" -o "$out"
  doc=data/raw/rdatasets/$(echo "$f" | tr / _)_codebook.html
  [ -s "$doc" ] || curl -sSL "$RD/doc/$f.html" -o "$doc" || true
done
python3 -c "import wooldridge as w; w.data('labsup').to_csv('data/raw/rdatasets/wooldridge_labsup.csv', index=False)"

# PolicyEngine CPS ASEC person files (raw ASEC persons with PolicyEngine names)
PE=https://github.com/PolicyEngine/policyengine-us-data/releases/download/release
for y in 2021 2022 2023; do
  out=data/raw/policyengine/h5/cps_$y.h5
  [ -s "$out" ] || curl -sSL "$PE/cps_$y.h5" -o "$out"
done

# Our World in Data (git sparse checkout of owid/owid-datasets)
if [ ! -s data/raw/owid/flfp_owid_2017.csv ]; then
  tmp=$(mktemp -d)
  git clone --depth 1 --filter=blob:none --no-checkout https://github.com/owid/owid-datasets "$tmp/owid"
  ( cd "$tmp/owid" && git sparse-checkout init --cone && \
    git sparse-checkout set "datasets/Female labor force participation rate - OWID (2017)" \
      "datasets/US Female Labor Force Participation 1890-2005 - Olivetti (2013)" \
      "datasets/Fertility rate (Complete Gapminder, v12) (2017)" \
      "datasets/Female weekly hours worked – OECD (2017)" && git checkout HEAD -- )
  D="$tmp/owid/datasets"
  cp "$D/Female labor force participation rate - OWID (2017)/Female labor force participation rate - OWID (2017).csv" data/raw/owid/flfp_owid_2017.csv
  cp "$D/Female labor force participation rate - OWID (2017)/datapackage.json" data/raw/owid/flfp_owid_2017_datapackage.json
  cp "$D/US Female Labor Force Participation 1890-2005 - Olivetti (2013)/US Female Labor Force Participation 1890-2005 - Olivetti (2013).csv" data/raw/owid/us_flfp_olivetti_2013.csv
  cp "$D/Fertility rate (Complete Gapminder, v12) (2017)/Fertility rate (Complete Gapminder, v12) (2017).csv" data/raw/owid/fertility_gapminder_v12.csv
  cp "$D/Female weekly hours worked – OECD (2017)/Female weekly hours worked – OECD (2017).csv" data/raw/owid/female_weekly_hours_oecd_2017.csv
  rm -rf "$tmp"
fi
echo "done"
