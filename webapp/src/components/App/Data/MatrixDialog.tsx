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

import { useEffect, useState } from "react";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";

import { MatrixInfoDTO, MatrixType } from "@/common/types";
import DataViewerDialog from "@/components/common/dialogs/DataViewerDialog";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { getMatrix } from "@/services/api/matrix";

interface PropTypes {
  matrixInfo: MatrixInfoDTO;
  open: boolean;
  onClose: () => void;
}

function MatrixDialog(props: PropTypes) {
  const { matrixInfo, open, onClose } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [loading, setLoading] = useState(false);
  const [matrix, setMatrix] = useState<MatrixType>({
    index: [],
    columns: [],
    data: [],
  });

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        if (matrixInfo) {
          const res = await getMatrix(matrixInfo.id);
          const matrixContent: MatrixType = {
            index: matrix ? res.index : [],
            columns: matrix ? res.columns : [],
            data: matrix ? res.data : [],
          };
          setMatrix(matrixContent);
        }
      } catch (error) {
        enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
      } finally {
        setLoading(false);
      }
    };
    init();
    return () => {
      setMatrix({ index: [], columns: [], data: [] });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enqueueErrorSnackbar, matrixInfo, t]);

  return open ? (
    <DataViewerDialog
      filename={matrixInfo.name}
      onClose={onClose}
      loading={loading}
      content={{ ...matrix, id: matrixInfo.id }}
      isMatrix
    />
  ) : (
    <div />
  );
}

export default MatrixDialog;
