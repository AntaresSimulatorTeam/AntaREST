#!/bin/bash
previous_tag=0

printf "# Change Log Docs files \n"
printf "All notable changes to the documents of this projects will be documented in this file. \n\n"

for current_tag in $(git tag --sort=-creatordate)
do

if [ "$previous_tag" != 0 ];then
    tag_date=$(git log -1 --pretty=format:'%ad' --date=short ${previous_tag})
    printf "## ${previous_tag} (${tag_date})\n\n"
    git log ${current_tag}...${previous_tag} --pretty=format:'*  %s [%h](https://github.com/AntaresSimulatorTeam/AntaREST/commit/%H)' --reverse docs | grep -v Merge
    printf "\n\n"
fi
previous_tag=${current_tag}
done
