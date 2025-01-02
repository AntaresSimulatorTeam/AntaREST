# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.


class APITag:
    users = "Users"
    launcher = "Launch Studies"
    study_permissions = "Manage Study Permissions"
    study_management = "Manage Studies"
    xpansion_study_management = "Manage Expansion Studies"
    study_data = "Manage Study Data"
    study_variant_management = "Manage Study Variant"
    study_raw_data = "Manage Study Raw File Data"
    study_outputs = "Manage Outputs"
    downloads = "Manage downloads"
    matrix = "Manage Matrix"
    tasks = "Manage tasks"
    misc = "Miscellaneous"
    filesystem = "Filesystem Management"
    explorer = "Explorer"


tags_metadata = [
    {
        "name": APITag.study_management,
    },
    {
        "name": APITag.study_data,
    },
    {
        "name": APITag.study_variant_management,
    },
    {
        "name": APITag.study_raw_data,
    },
    {
        "name": APITag.launcher,
    },
    {
        "name": APITag.xpansion_study_management,
    },
    {
        "name": APITag.study_outputs,
    },
    {
        "name": APITag.matrix,
    },
    {
        "name": APITag.downloads,
    },
    {
        "name": APITag.tasks,
    },
    {
        "name": APITag.study_permissions,
    },
    {
        "name": APITag.users,
    },
    {
        "name": APITag.misc,
    },
    {
        "name": APITag.filesystem,
    },
    {
        "name": APITag.explorer,
    },
]
