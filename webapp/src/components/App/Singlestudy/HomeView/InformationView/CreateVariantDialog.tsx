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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { createVariant } from "../../../../../services/api/variant";
import { createListFromTree } from "../../../../../services/utils";
import type { GenericInfo, VariantTree } from "../../../../../types/types";
import FormDialog from "../../../../common/dialogs/FormDialog";
import StringFE from "../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../common/Fieldset";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";

interface Props {
  parentId: string;
  open: boolean;
  variantTree: VariantTree;
  onClose: () => void;
}

function CreateVariantDialog({ parentId, open, variantTree, onClose }: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const [sourceList, setSourceList] = useState<GenericInfo[]>([]);
  const defaultValues = { name: "", sourceId: parentId };

  const existingVariants = useMemo(() => sourceList.map((variant) => variant.name), [sourceList]);

  useEffect(() => {
    setSourceList(createListFromTree(variantTree));
  }, [variantTree]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { sourceId, name } = data.values;
    return createVariant(sourceId, name);
  };

  const handleSubmitSuccessful = (
    data: SubmitHandlerPlus<typeof defaultValues>,
    variantId: string,
  ) => {
    onClose();
    navigate(`/studies/${variantId}`);
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
              validate: (v) => validateString(v, { existingValues: existingVariants }),
            }}
          />
          <SelectFE
            label={t("study.versionSource")}
            name="sourceId"
            variant="outlined"
            options={sourceList.map((ver) => ({
              label: ver.name,
              value: ver.id,
            }))}
            control={control}
            rules={{ required: true }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateVariantDialog;
