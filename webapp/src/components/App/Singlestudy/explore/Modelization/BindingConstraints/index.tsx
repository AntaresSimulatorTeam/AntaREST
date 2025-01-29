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

import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import EmptyView from "../../../../../common/page/EmptyView";
import BindingConstPropsView from "./BindingConstPropsView";
import { getBindingConst, getCurrentBindingConstId } from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studySyntheses";
import BindingConstView from "./BindingConstView";
import usePromise from "../../../../../../hooks/usePromise";
import { getBindingConstraintList } from "../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import { useEffect } from "react";
import SplitView from "../../../../../common/SplitView";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import { useTranslation } from "react-i18next";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  const currentConstraintId = useAppSelector(getCurrentBindingConstId);

  const bindingConstraints = useAppSelector((state) => getBindingConst(state, study.id));

  const constraintsRes = usePromise(
    () => getBindingConstraintList(study.id),
    [study.id, bindingConstraints],
  );

  useEffect(() => {
    const { data } = constraintsRes;

    if (!data || data.length === 0 || currentConstraintId) {
      return;
    }

    const firstConstraintId = data[0].id;
    dispatch(setCurrentBindingConst(firstConstraintId));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [constraintsRes.data, currentConstraintId, dispatch]);

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
      response={constraintsRes}
      ifFulfilled={(data) => (
        <SplitView id="binding-constraints" sizes={[10, 90]}>
          {/* Left */}
          <BindingConstPropsView // TODO rename ConstraintsList
            list={data}
            onClick={handleConstraintChange}
            currentConstraint={currentConstraintId}
            reloadConstraintsList={constraintsRes.reload}
          />
          {/* Right */}
          <ViewWrapper>
            {data.length > 0 && currentConstraintId ? (
              <BindingConstView constraintId={currentConstraintId} />
            ) : (
              <EmptyView title={t("study.bindingConstraints.empty")} />
            )}
          </ViewWrapper>
        </SplitView>
      )}
      ifRejected={(error) => <EmptyView title={error?.toString()} />}
    />
  );
}

export default BindingConstraints;
