#!/bin/bash
# A simple script to use curl to speak with alpaca's API.
# https://alpaca.markets/docs/api-documentation/how-to/
#
#   Connor Shugg

# globals
url_paper="https://paper-api.alpaca.markets"
url_live="https://api.alpaca.markets"

key_dpath=/home/snowmiser/snowbroker/keys
key_paper_api_fpath=${key_dpath}/alpaca_paper_api.key           # paper API key
key_paper_secret_fpath=${key_dpath}/alpaca_paper_secret.key     # paper secret key
key_live_api_fpath=${key_dpath}/alpaca_paper_api.key            # TODO live API key
key_live_secret_fpath=${key_dpath}/alpaca_paper_secret.key      # TODO live secret key

# ============================= Helper Functions
function __api_request_usage()
{
    echo "Usage: $0 API_TYPE [ENDPOINT] [METHOD] [DATA]"
    echo "Where:"
    echo "  - API_TYPE is either 'paper' or 'live'"
    echo "  - ENDPOINT is the endpoint to send the request to (default: /v2/account)"
    echo "  - METHOD is the HTTP method (default: GET)"
    echo "  - DATA is the data to send in the HTTP request body (default: no data)"
}

# ============================= Runner Code
# first, check command-line arguments
if [ $# -lt 1 ]; then
    __api_request_usage
    exit 0
fi

# parse the API type
api_type=$1
key_api_fpath=""
key_secret_fpath=""
url=""
if [[ "${api_type}" == "paper" ]] || [[ "${api_type}" == "p" ]]; then
    api_type=0
    key_api_fpath=${key_paper_api_fpath}
    key_secret_fpath=${key_paper_secret_fpath}
    url=${url_paper}
elif [[ "${api_type}" == "live" ]] || [[ "${api_type}" == "l" ]]; then
    api_type=1
    key_api_fpath=${key_live_api_fpath}
    key_secret_fpath=${key_live_secret_fpath}
    url=${url_live}
else
    __api_request_usage
    exit 0
fi

# get the endpoint, method, and data
endpoint=/v2/account
if [ $# -ge 2 ]; then
    endpoint=$2
fi
method=GET
if [ $# -ge 3 ]; then
    method=$3
fi
data=""
dfile=./data.txt
if [ $# -ge 4 ]; then
    data="$4"
fi

# try to read the keys
if [ ! -f ${key_api_fpath} ]; then
    echo "Can't find API key file: ${key_api_fpath}"
    exit 1
fi
if [ ! -f ${key_secret_fpath} ]; then
    echo "Can't find secret key file: ${key_secret_fpath}"
    exit 1
fi
key_api="$(cat ${key_api_fpath})"
key_secret="$(cat ${key_secret_fpath})"

# send the HTTP request
ofile=./out.txt
echo "DATA ARG: ${data}"
if [ -z "${data}" ]; then
    curl -v -X ${method} \
         -H "APCA-API-KEY-ID: ${key_api}" \
         -H "APCA-API-SECRET-KEY: ${key_secret}" \
         ${url}/${endpoint} > ${ofile}
else
    # dump data into a file
    echo "${data}" > ${dfile}
    # send the curl, specifying the file path
    curl -v -X ${method} \
         --data "@${dfile}" \
         -H "APCA-API-KEY-ID: ${key_api}" \
         -H "APCA-API-SECRET-KEY: ${key_secret}" \
         ${url}/${endpoint} > ${ofile}
    # remove the data file
    rm ${dfile}
fi

# pretty-print the response via python
cat ${ofile} | python -m json.tool
rm ${ofile}

     
