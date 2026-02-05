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
import { createVariant } from "@/services/api/variant";
import { createListFromTree } from "@/services/utils";
import type { VariantTree } from "@/types/types";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useNavigate } from "@tanstack/react-router";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  parentId: string;
  open: boolean;
  variantTree: VariantTree;
  onClose: () => void;
}

function CreateVariantDialog({ parentId, open, variantTree, onClose }: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const defaultValues = { name: "", sourceId: parentId };
  const dispatch = useAppDispatch();

  const studiesSource = useMemo(() => createListFromTree(variantTree), [variantTree]);

  const studySourceOptions = useMemo(
    () => studiesSource.map(({ id, name }) => ({ value: id, label: name })),
    [studiesSource],
  );

  const existingNames = useMemo(() => studiesSource.map(({ name }) => name), [studiesSource]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { sourceId, name } = data.values;
    const variantId = await createVariant(sourceId, name);
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
      maxWidth="sm" // Study name source can be long
      title={t("studies.createNewStudy")}
      titleIcon={AddCircleIcon}
      open={open}
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
            name="sourceId"
            variant="outlined"
            options={studySourceOptions}
            control={control}
            rules={{ required: true }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateVariantDialog;
