#!/usr/bin/env bash

script_dir="$(dirname "${0}")"

SAT="${1}"
shift
if [[ -z "${SAT}" ]]
then
    echo "No SAT given"
    exit
fi

SLOT="${1}"
shift
if [[ -z "${SLOT}" ]]
then
    echo "No slot given"
    exit
fi

SLOT_END="${1}"
shift

export XRIT_DECOMPRESS_PATH=/usr/bin/xRITDecompress

if [[ -z "${SLOT_END}" ]]
then
    SLOTS="${SLOT}"
else
    SLOTS="$(create_seviri_slot_list "${SLOT}" "${SLOT_END}" -ex)"
fi

storage_dir="/data/ftp/anonymous/ECONTRAIL"

#MSG[1-4]_REGION_NA_${SLOT}.nc 

function compress_ncfile() {
    FILE="${1}"
    if [[ -e "${FILE}" ]]
    then
        tmp_file="${FILE}.tmp"
        /usr/bin/h5repack -m 1048576 -f SHUF -f GZIP=3 "${FILE}" "${tmp_file}" && \
        mv "${tmp_file}" "${FILE}"
    fi
}

for SLOT in $SLOTS
do
    INPUT_DIR="/mnt/MSG/${SLOT:0:4}/${SAT}_${SLOT:0:8}/HRIT_${SLOT}"
    INPUT_DIR="/mnt/GEO/archive/${SAT}_${SLOT:0:8}/${SAT}_${SLOT}"
    OUTPUT_DIR="${storage_dir}/${SAT}/${SLOT:0:4}/${SLOT:4:2}/${SLOT:6:2}/"
    PRODUCT_FILE="${SAT}_${SLOT}_ECONTRAIL.nc"
    if [[ -d "${INPUT_DIR}" ]]
    then
	echo "${SLOT} available - processing"
    else
	echo "${SLOT} not available - not processing"
	continue
    fi
    /sdata/anaconda/condabin/conda run -n p39 python "${script_dir}/seviri_resample.py" "${INPUT_DIR}"/H* --out "${PRODUCT_FILE}" --reader seviri_l1b_hrit
    compress_ncfile "${PRODUCT_FILE}"
    mkdir -p "${OUTPUT_DIR}"
    mv -v "${PRODUCT_FILE}" "${OUTPUT_DIR}"

done

