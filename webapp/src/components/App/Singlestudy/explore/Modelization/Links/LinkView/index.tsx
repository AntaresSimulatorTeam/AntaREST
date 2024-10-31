/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useOutletContext } from "react-router";
import { LinkElement, StudyMetadata } from "@/common/types";
import usePromise from "@/hooks/usePromise";
import LinkForm from "./LinkForm";
import { getDefaultValues } from "./utils";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import Form from "@/components/common/Form";

interface Props {
  link: LinkElement;
}

function LinkView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { link } = props;
  const res = usePromise(
    () => getDefaultValues(study.id, link.area1, link.area2),
    [study.id, link.area1, link.area2],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(data) => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <LinkForm link={link} study={study} />
        </Form>
      )}
    />
  );
}

export default LinkView;
