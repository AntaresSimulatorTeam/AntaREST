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

import FieldEditorButtonGroup from "@/components/common/FieldEditorButtonGroup";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import SearchIcon from "@mui/icons-material/Search";
import { Button } from "@mui/material";
import type { UseFormReset } from "react-hook-form";
import { useTranslation } from "react-i18next";

function SearchStudies() {
  const searchValue = useAppSelector((state) => getStudyFilters(state).search);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const defaultValues = { search: searchValue };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setSearchValue = (newValue = "") => {
    dispatch(updateStudyFilters({ search: newValue }));
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { search } }: SubmitHandlerPlus<typeof defaultValues>) => {
    setSearchValue(search);
  };

  const handleChange =
    (reset: UseFormReset<typeof defaultValues>) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      if (value === "") {
        setSearchValue("");
        reset({ search: "" });
      }
    };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      hideSubmitButton
      disableCloseProtection
      sx={{
        minWidth: 200,
        transition: "min-width 0.2s ease",
        ":focus-within": {
          minWidth: 500,
        },
      }}
    >
      {({ control, formState: { isDirty }, reset }) => (
        <FieldEditorButtonGroup size="extra-small">
          <StringFE
            placeholder={t("global.search")}
            name="search"
            type="search"
            control={control}
            fullWidth
            onChange={handleChange(reset)}
          />
          <Button type="submit" disabled={!isDirty}>
            <SearchIcon />
          </Button>
        </FieldEditorButtonGroup>
      )}
    </Form>
  );
}

export default SearchStudies;
