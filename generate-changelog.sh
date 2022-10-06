#!/bin/bash
previous_tag=0

printf "# Change Log \n"
printf "All notable changes to this project will be documented in this file. \n"

for current_tag in $(git tag --sort=-creatordate)
do

if [ "$previous_tag" != 0 ];then
    tag_date=$(git log -1 --pretty=format:'%ad' --date=short ${previous_tag})
    printf "## ${previous_tag} (${tag_date})\n\n"
    git log ${current_tag}...${previous_tag} --pretty=format:'*  %s [%h](https://github.com/AntaresSimulatorTeam/AntaREST/commit/%H)' --reverse | grep -v Merge
    printf "\n\n"
fi
previous_tag=${current_tag}
done
