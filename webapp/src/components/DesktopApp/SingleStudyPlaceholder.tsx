/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */
import { useNavigate } from "react-router";
import { useEffect } from "react";
import client from "@/services/api/client";

export function SingleStudyPlaceholder() {
  const navigate = useNavigate();

  useEffect(() => {
    window.onOpenStudy((path) => {
      async function loadStudy() {
        const res = await client.post(`/v1/studies/_open`, { path: path });
        const studyId = res.data;
        navigate(`/studies/${studyId}/explore`);
      }
      loadStudy();
    });
  }, [navigate]);
  return <></>;
}

export default SingleStudyPlaceholder;
