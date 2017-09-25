#!/bin/bash

#  git-update-hook for CFEngine 3.5 - DCO Release v2.0
#  
#  Created by Joshua Sonstroem on 6/19/13, Updated July 8, 2014 v0.99
#
#  Note: This script requires libpromises.so.1 from CF3.4 to exist at /var/cfengine/lib/libpromises.so.1

REF_NAME="$1"
OLD_REV="$2"
NEW_REV="$3"

GIT=/opt/git/bin/git
TAR=/bin/tar
REPOS=`hostname`
CF_PROMISES=/var/cfengine/bin/cf-promises
TMP_CHECKOUT_DIR=/tmp/cfengine-post-commit-syntax-check
MAIN_POLICY_FILE=masterfiles/promises.cf

if [ ! -d ${TMP_CHECKOUT_DIR} ]; then
    echo "Creating temporary checkout directory at ${TMP_CHECKOUT_DIR}"
    mkdir -p ${TMP_CHECKOUT_DIR}
fi

# Clearing previous data in temporary checkout directory
rm -rf ${TMP_CHECKOUT_DIR}/*
rm -rf ${TMP_CHECKOUT_DIR}/.git

# Validate that the world readable copy is available at /local/cfengine
if [ ! -d /local/cfengine ]; then
    echo "ERROR --> Login to the STASH server and run the following commands as root"
    echo "          to make a world-readable copy of /var/cfengine @ /local/cfengine"
    echo "          before trying your commit again."
    echo
    echo " # cp -prv /var/cfengine /local/cfengine"
    echo " # find /local/cfengine -type f -perm 0600 | xargs chmod 0644"
    echo " # find /local/cfengine -type d -perm 0700 | xargs chmod 0755"
    echo
    exit 1
fi

# use rsync to copy files into place from /local/cfengine to ${TMP_CHECKOUT_DIR}
rsync -avvP --exclude 'outputs' --exclude 'state' --exclude 'share' --exclude 'masterfiles' --exclude 'ppkeys' --exclude 'bin' --include 'inputs/lib' --exclude 'lib' --exclude 'modules' --exclude 'reports' --exclude 'lastseen' --exclude 'inputs/*.cfsaved' --exclude 'inputs/app-configs'  --exclude 'inputs/promises.cf'  --exclude 'inputs/cf_promises_validated' --exclude '*.pid' --exclude '*runlog*' --exclude '*tcdb*' --exclude 'randseed' --exclude 'promise_summary.log' --exclude 'policy_server.dat' --exclude '*.log' /local/cfengine/ ${TMP_CHECKOUT_DIR}/ 1>&2 > /dev/null
mv ${TMP_CHECKOUT_DIR}/inputs ${TMP_CHECKOUT_DIR}/masterfiles

# Checkout the archive of the files into the temp location and untar them
echo "Checking out revision (${NEW_REV}) from ${REPOS} to ${TMP_CHECKOUT_DIR}"
${GIT} archive ${NEW_REV} | tar -x -C ${TMP_CHECKOUT_DIR}
if [ $? -ne 0 ]; then
    echo "ERROR --> Could not check out the repository to temporary folder for syntax checking!" >&2
    return 1
fi

# Check the policy with cf-promises
echo "Running cf-promises -f on ${TMP_CHECKOUT_DIR}/${MAIN_POLICY_FILE}"
${CF_PROMISES} -f ${TMP_CHECKOUT_DIR}/${MAIN_POLICY_FILE}

if [ $? -ne 0 ]; then
    echo "ERROR --> There were syntax or policy errors in pushed revision (${NEW_REV})" >&2
    return 1
else
    echo "Policy check completed successfully!"
    exit 0
fi
