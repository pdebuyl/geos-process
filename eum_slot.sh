#!/usr/bin/env bash

action="${1}"
shift

if [ -z "{action}" ]
then
echo "no action given"
exit 0
fi

if [ "${action}" = "download" ]
then
  flag="-y"
fi

product="${1}"
shift

case ${product} in
  "HRSEVIRI" | "CLM" )
    ;;
  "" | * )
    echo "No valid product given"
    exit 0
    ;;
esac

slot="${1}"
shift

slot_end="${1}"
shift

YYYY="${slot:0:4}"
MM="${slot:4:2}"
DD="${slot:6:2}"
if [ -n "${slot:8:2}" ]
then
  hh="${slot:8:2}"
else
  hh="00"
fi
if [ -n "${slot:10:2}" ]
then
  mm="${slot:10:2}"
else
  mm="00"
fi

if [ -z "${slot_end}" ]
then
  conda run -n py311 eumdac "${action}" ${flag} -c "EO:EUM:DAT:MSG:${product}" -s "${YYYY}-${MM}-${DD}T${hh}:${mm}" -e "${YYYY}-${MM}-${DD}T00:00" --limit 96
else
  conda run -n py311 eumdac "${action}" ${flag} -c "EO:EUM:DAT:MSG:${product}" -s "${YYYY}-${MM}-${DD}T${hh}:${mm}" -e "${slot_end:0:4}-${slot_end:4:2}-${slot_end:6:2}T${slot_end:8:2}:${slot_end:10:2}" --limit 200
fi

