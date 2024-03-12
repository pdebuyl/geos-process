#!/usr/bin/env bash

script_dir="$(dirname "${0}")"
SLOT="${1}"
shift

SLOT_END="${1}"
shift

storage_dir="/data/ftp/anonymous/ECONTRAIL"

if [ "${SLOT_END}" = "" ]
then
    ls ${storage_dir}/MSG[1-4]/${SLOT:0:4}/${SLOT:4:2}/${SLOT:6:2}/MSG[1-4]_REGION_NA_${SLOT}.nc 1>/dev/null 2>/dev/null
    ls_success=$?
    if [[ "${ls_success}" -eq 0 ]]
    then
        echo "slot ${SLOT} already processed"
	exit 0
    fi

    YYYY="${SLOT:0:4}"
    MM="${SLOT:4:2}"
    DD="${SLOT:6:2}"
    hh="${SLOT:8:2}"
    mm="${SLOT:10:2}"
    SLOT_END="$(date -u --date "${YYYY}-${MM}-${DD} ${hh}:${mm}:00 UTC +1 mins" +"%Y%m%d%H%M")"
fi

function compress_ncfile() {
    FILE="${1}"
    if [[ -e "${FILE}" ]]
    then
        tmp_file="${FILE}.tmp"
        /usr/bin/h5repack -m 1048576 -f SHUF -f GZIP=3 "${FILE}" "${tmp_file}" && \
        mv "${tmp_file}" "${FILE}"
    fi
}

PROCESS_DIR="$(mktemp -d)"
echo "PROCESS_DIR ${PROCESS_DIR}"

(cd "${PROCESS_DIR}" ; "${script_dir}/eum_slot.sh" download HRSEVIRI "${SLOT}" "${SLOT_END}" > download-stdout.txt )

ZIPFILES=$(cat "${PROCESS_DIR}/download-stdout.txt" | sed -n -e 's/Job [0-9]*: Downloading \(.*\)/\1/p')
echo $ZIPFILES
for ZFILE in ${ZIPFILES}
do
    ZFILE="$(basename "${ZFILE}")"
    (cd "${PROCESS_DIR}" ; unzip "${ZFILE}")
    DATAFILE="$(xml_grep --text_only dataObject/path "${PROCESS_DIR}/manifest.xml" )"
    rm "${PROCESS_DIR}/manifest.xml" "${PROCESS_DIR}/EOPMetadata.xml" "${PROCESS_DIR}/${ZFILE}"
    echo "${DATAFILE} available - processing"
    /sdata/anaconda/condabin/conda run -n p39 python "${script_dir}/seviri_resample.py" "${PROCESS_DIR}/${DATAFILE}" --out "${PROCESS_DIR}/${DATAFILE%.nat}.nc"
    rm "${PROCESS_DIR}/${DATAFILE}"
    compress_ncfile "${PROCESS_DIR}/${DATAFILE%.nat}.nc"
    if [[ "${DATAFILE}" =~ MSG[1-4]-SEVI-MSG15-0100-NA-.*-NA.nat ]]
    then
        SAT="${DATAFILE:0:4}"
        SLOT="${DATAFILE:24:12}"
        SLOT="$((SLOT-12))"   # Shift slot time by 12 minutes to have nominal start of repeat cycle
        mv "${PROCESS_DIR}/${DATAFILE%.nat}.nc" "${storage_dir}/${SAT}/${SLOT:0:4}/${SLOT:4:2}/${SLOT:6:2}/${SAT}_REGION_NA_${SLOT}.nc"
    else
        echo "Not recognizing filename ${DATAFILE}"
	exit 1
    fi
done

rm -r "${PROCESS_DIR}"

