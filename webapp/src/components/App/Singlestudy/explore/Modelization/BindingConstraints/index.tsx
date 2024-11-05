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

import { useEffect } from "react";
import { useOutletContext } from "react-router";

import { Box } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import SimpleLoader from "@/components/common/loaders/SimpleLoader";
import EmptyView from "@/components/common/page/SimpleContent";
import SplitView from "@/components/common/SplitView";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { setCurrentBindingConst } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getBindingConst, getCurrentBindingConstId } from "@/redux/selectors";
import { getBindingConstraintList } from "@/services/api/studydata";

import BindingConstPropsView from "./BindingConstPropsView";
import BindingConstView from "./BindingConstView";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  const currentConstraintId = useAppSelector(getCurrentBindingConstId);

  const bindingConstraints = useAppSelector((state) =>
    getBindingConst(state, study.id),
  );

  // TODO find better name
  const constraints = usePromise(
    () => getBindingConstraintList(study.id),
    [study.id, bindingConstraints],
  );

  useEffect(() => {
    const { data } = constraints;

    if (!data || data.length === 0 || currentConstraintId) {
      return;
    }

    const firstConstraintId = data[0].id;
    dispatch(setCurrentBindingConst(firstConstraintId));
  }, [constraints, currentConstraintId, dispatch]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConstraintChange = (constraintId: string): void => {
    dispatch(setCurrentBindingConst(constraintId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={constraints}
      ifPending={() => <SimpleLoader />}
      ifResolved={(data) => (
        <SplitView id="binding-constraints" sizes={[10, 90]}>
          {/* Left */}
          <BindingConstPropsView // TODO rename ConstraintsList
            list={data}
            onClick={handleConstraintChange}
            currentConstraint={currentConstraintId}
            reloadConstraintsList={constraints.reload}
          />
          {/* Right */}
          <Box>
            {data.length > 0 && currentConstraintId ? (
              <BindingConstView constraintId={currentConstraintId} />
            ) : (
              <EmptyView title="No Binding Constraints" />
            )}
          </Box>
        </SplitView>
      )}
      ifRejected={(error) => <EmptyView title={error?.toString()} />}
    />
  );
}

export default BindingConstraints;
