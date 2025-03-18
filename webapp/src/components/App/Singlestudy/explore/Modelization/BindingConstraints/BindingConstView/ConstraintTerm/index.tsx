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

import { useMemo, useState } from "react";
import { Box, Button, TextField, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import { useTranslation } from "react-i18next";
import { isLinkTerm, type ConstraintTerm } from "../utils";
import type { AllClustersAndLinks } from "../../../../../../../../types/types";
import OptionsList from "./OptionsList";
import ConstraintElement from "../constraintviews/ConstraintElement";
import OffsetInput from "../constraintviews/OffsetInput";

interface Props {
  options: AllClustersAndLinks;
  term: ConstraintTerm;
  constraintTerms: ConstraintTerm[];
  saveValue: (term: ConstraintTerm) => void;
  deleteTerm: () => void;
}

/**
 * Represents a single constraint term item within the UI, allowing users to
 * modify weight, offset, and select areas or clusters based on the term type.
 *
 * Additionally, the refactor will address the need to incorporate uncontrolled components
 * with `react-hook-form` for better form management practices.
 *
 * @deprecated This component is deprecated due to an upcoming redesign aimed at improving modularity and maintainability.
 * It remains functional for current implementations but will be replaced by a more
 * modular design. Future versions will introduce separate components for handling cluster terms and link terms more efficiently.
 *
 * Additionally, the refactor will address the need to incorporate uncontrolled components
 * with `react-hook-form` for better form management practices.
 *
 * @param  props - The props @see {Props}
 * @param  props.options - The available options for areas and clusters.
 * @param  props.term - The current term being edited, containing its data.
 * @param  props.constraintTerms - All current terms for validation and to prevent duplicates.
 * @param  props.saveValue - Callback function to save the updated term to the global state.
 * @param  props.deleteTerm - Callback function to delete the current term.
 *
 * @example
 * <ConstraintTermItem
 *   options={allClustersAndLinks}
 *   term={currentTerm}
 *   constraintTerms={allTerms}
 *   saveValue={handleSaveValue}
 *   deleteTerm={handleDeleteTerm}
 * />
 *
 * @returns Constraint Term component of type link or cluster
 */
function ConstraintTermItem({ options, term, constraintTerms, saveValue, deleteTerm }: Props) {
  const [t] = useTranslation();
  const [weight, setWeight] = useState(term.weight);
  const [offset, setOffset] = useState(term.offset);

  /**
   * Determines the type of constraint term (link or cluster) and initializes
   * the relevant states for the area and cluster or the two areas in case of a link.
   *
   * The component supports two types of terms:
   * - LinkTerm: Represents a link between two areas (`area1` and `area2`).
   * - ClusterTerm: Represents a cluster within an area (`area` and `cluster`).
   *
   * The `useMemo` hook is utilized to compute and remember the values based on `term.data`.
   * This memoization helps in avoiding unnecessary recalculations during re-renders.
   *
   * @returns An array where:
   *   - The first element (`area`) represents the primary area for both link and cluster terms.
   *   - The second element (`areaOrCluster`) represents either the second area for link terms
   *     or the cluster for cluster terms.
   */
  const [area, areaOrCluster] = useMemo(() => {
    // Using isLinkTerm to check if the term's data matches the structure of a LinkTerm
    // and accordingly returning the appropriate areas or area and cluster.
    return isLinkTerm(term.data)
      ? [term.data.area1, term.data.area2] // For LinkTerm: Extracting both areas.
      : [term.data.area, term.data.cluster]; // For ClusterTerm: Extracting area and cluster.
  }, [term.data]);

  /**
   * State hooks for managing the selected area and cluster (or second area for links),
   * enabling user interaction and updates to these fields.
   *
   * - `selectedArea`: State for managing the primary area selection.
   * - `selectedClusterOrArea2`: State for managing the secondary selection,
   *    which could be a cluster (for ClusterTerm) or a second area (for LinkTerm).
   */
  const [selectedArea, setSelectedArea] = useState(area);

  const [selectedClusterOrArea, setSelectedClusterOrArea] = useState(areaOrCluster);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleWeightChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newWeight = parseFloat(event.target.value) || 0;
    setWeight(newWeight);
    saveValue({ ...term, weight: newWeight });
  };

  const handleOffsetChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const value = event.target.value;
    const newOffset = value === "" ? undefined : parseInt(value, 10);
    setOffset(newOffset);
    saveValue({ ...term, offset: newOffset });
  };

  const handleOffsetRemove = () => {
    if (offset !== undefined && offset > 0) {
      saveValue({ ...term, offset: undefined });
    }
    setOffset(undefined);
  };

  const handleOffsetAdd = () => {
    setOffset(0);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
      }}
    >
      <ConstraintElement
        left={
          <TextField
            label={t("study.modelization.bindingConst.weight")}
            variant="outlined"
            type="number"
            value={weight}
            onChange={handleWeightChange}
            sx={{ maxWidth: 150 }}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              isLink={isLinkTerm(term.data)}
              list={options}
              term={term}
              saveValue={saveValue}
              selectedArea={selectedArea}
              selectedClusterOrArea={selectedClusterOrArea}
              setSelectedArea={setSelectedArea}
              setSelectedClusterOrArea={setSelectedClusterOrArea}
              constraintTerms={constraintTerms}
            />
          </Box>
        }
      />

      <Box sx={{ display: "flex", alignItems: "center" }}>
        {offset !== undefined && offset !== null ? (
          <>
            <Typography sx={{ mx: 1 }}>x</Typography>
            <ConstraintElement
              operator="+"
              left={<Typography>t</Typography>}
              right={
                <OffsetInput onRemove={handleOffsetRemove}>
                  <TextField
                    label={t("study.modelization.bindingConst.offset")}
                    variant="outlined"
                    type="number"
                    value={offset}
                    onChange={handleOffsetChange}
                    sx={{ maxWidth: 100 }}
                  />
                </OffsetInput>
              }
            />
          </>
        ) : (
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<AddCircleOutlineRoundedIcon />}
            onClick={handleOffsetAdd}
            sx={{ ml: 3.5 }}
          >
            {t("study.modelization.bindingConst.offset")}
          </Button>
        )}
      </Box>

      <Box sx={{ display: "flex", alignItems: "center", ml: "auto" }}>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteRoundedIcon />}
          onClick={deleteTerm}
        >
          {t("global.delete")}
        </Button>
      </Box>
    </Box>
  );
}

export default ConstraintTermItem;
