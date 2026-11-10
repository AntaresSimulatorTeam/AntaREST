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

import FormDialog from "@/components/dialogs/FormDialog";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { setStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { createVariant } from "@/services/api/studies/variants";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { createListFromTree, getSubTree, sortByName } from "@/services/utils";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  defaultParentId: string;
  variantTree: VariantTree;
  onClose: () => void;
}

function CreateStudyVariantDialog({ defaultParentId, variantTree, onClose }: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const defaultValues = { name: "", parentId: defaultParentId };
  const dispatch = useAppDispatch();
  const [parentId, setParentId] = useState(defaultParentId);

  const studySourceOptions = useMemo(() => {
    const studiesSource = createListFromTree(variantTree);
    return sortByName(studiesSource).map(({ id, name }) => ({ value: id, label: name }));
  }, [variantTree]);

  const existingNames = useMemo(() => {
    const subTree = getSubTree(variantTree, parentId);
    return subTree ? subTree.children.map(({ node }) => node.name) : [];
  }, [variantTree, parentId]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { parentId, name } = data.values;
    const variantId = await createVariant({ studyId: parentId, name });
    await dispatch(setStudy(variantId)).unwrap();
    return variantId;
  };

  const handleSubmitSuccessful = (
    data: SubmitHandlerPlus<typeof defaultValues>,
    variantId: string,
  ) => {
    onClose();
    navigate({ to: "/studies/$studyId", params: { studyId: variantId } });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open
      maxWidth="sm" // Study name source can be long
      title={t("studies.createNewStudy")}
      titleIcon={AddCircleIcon}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      config={{ defaultValues }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("variants.newVariant")}
            name="name"
            control={control}
            rules={{
              validate: (v) => validateString(v, { existingValues: existingNames }),
            }}
          />
          <SelectFE
            label={t("study.versionSource")}
            name="parentId"
            variant="outlined"
            options={studySourceOptions}
            control={control}
            rules={{ required: true, deps: ["name"] }}
            onChange={(event) => setParentId(event.target.value)}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateStudyVariantDialog;
