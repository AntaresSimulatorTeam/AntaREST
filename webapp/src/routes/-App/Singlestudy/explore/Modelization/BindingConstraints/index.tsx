/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import EmptyView from "@/components/page/EmptyView";
import SplitView from "@/components/page/SplitView";
import ViewWrapper from "@/components/page/ViewWrapper";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
// @ts-expect-error Temporary fix for missing lib
import { useOutletContext } from "react-router";
import usePromise from "../../../../../../hooks/usePromise";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentBindingConstId } from "../../../../../../redux/selectors";
import { getBindingConstraintList } from "../../../../../../services/api/studydata";
import type { StudyMetadata } from "../../../../../../types/types";
import BindingConstPropsView from "./BindingConstPropsView";
import BindingConstView from "./BindingConstView";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  const currentConstraintId = useAppSelector(getCurrentBindingConstId);

  const constraintsRes = usePromise(() => getBindingConstraintList(study.id), [study.id]);

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
        <SplitView splitId="binding-constraints">
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
              <BindingConstView
                constraintId={currentConstraintId}
                reloadConstraintsList={constraintsRes.reload}
              />
            ) : (
              <EmptyView title={t("study.bindingConstraints.empty")} />
            )}
          </ViewWrapper>
        </SplitView>
      )}
    />
  );
}

export default BindingConstraints;
