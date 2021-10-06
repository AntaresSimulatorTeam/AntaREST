/* eslint-disable @typescript-eslint/camelcase */
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { CSSProperties } from '@material-ui/core/styles/withStyles';
import React from 'react';
import { GroupDTO, MatrixDataSetDTO, MatrixDataSetUpdateDTO, MatrixInfoDTO } from '../../common/types';
import { createMatrixByImportation, updateDataSet, createDataSet } from '../../services/api/matrix';

const updateMatrix = async (
  data: MatrixDataSetDTO,
  name: string,
  publicStatus: boolean,
  selectedGroupList: Array<GroupDTO>,
  onNewDataUpdate: (newData: MatrixDataSetDTO) => void,
): Promise<any> => {
  const matrixMetadata: MatrixDataSetUpdateDTO = {
    name,
    public: publicStatus,
    groups: publicStatus ? [] : selectedGroupList.map((elm) => elm.id),
  };

  const newData = await updateDataSet(data.id, matrixMetadata);
  const newDataset: MatrixDataSetDTO = data;
  newDataset.name = newData.name;
  newDataset.public = newData.public;
  newDataset.groups = selectedGroupList;
  onNewDataUpdate(newDataset);
};

const createMatrix = async (
  name: string,
  publicStatus: boolean,
  selectedGroupList: Array<GroupDTO>,
  matrices: Array<MatrixInfoDTO>,
  onNewDataUpdate: (newData: MatrixDataSetDTO) => void,
): Promise<any> => {
  const matrixMetadata: MatrixDataSetUpdateDTO = {
    name,
    groups: publicStatus ? [] : selectedGroupList.map((elm) => elm.id),
    public: publicStatus,
  };

  const newData = await createDataSet(matrixMetadata, matrices);
  onNewDataUpdate(newData);
};

export const saveMatrix = async (
  name: string,
  publicStatus: boolean,
  selectedGroupList: Array<GroupDTO>,
  onNewDataUpdate: (newData: MatrixDataSetDTO) => void,
  file?: File,
  data?: MatrixDataSetDTO,
  onProgress?: (progress: number) => void,
): Promise<string> => {
  if (!name.replace(/\s/g, '')) throw Error('data:emptyName');

  if (data === undefined) {
    if (file) {
      const matrixInfos = await createMatrixByImportation(file, onProgress);
      await createMatrix(name, publicStatus, selectedGroupList, matrixInfos, onNewDataUpdate);
    } else throw Error('data:fileNotUploaded');
  } else {
    await updateMatrix(data, name, publicStatus, selectedGroupList, onNewDataUpdate);
  }

  return data ? 'data:onMatrixUpdate' : 'data:onMatrixCreation';
};

interface LoaderStyle {
  rootLoader: CSSProperties;
  shadow: CSSProperties;
  loaderWheel: CSSProperties;
  loaderMessage: CSSProperties;
  loaderContainer: CSSProperties;
}

export const loaderStyle: LoaderStyle = {
  rootLoader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    width: '100%',
    height: '100%',
    zIndex: 999,
  },
  shadow: {
    zIndex: 998,
    opacity: 0.9,
    backgroundColor: '#fff',
  },
  loaderWheel: {
    width: '98px',
    height: '98px',
  },
  loaderMessage: {
    marginTop: '1em',
  },
  loaderContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexFlow: 'column',
  },
};

export const CopyIcon = React.forwardRef<HTMLInputElement, React.DetailedHTMLProps<React.HTMLAttributes<HTMLSpanElement>, HTMLSpanElement>>((p: React.DetailedHTMLProps<React.HTMLAttributes<HTMLSpanElement>, HTMLSpanElement>, ref) => {
  if (ref) {
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <span {...p} ref={ref}><FontAwesomeIcon icon={['far', 'copy']} /></span>;
  }
  return <div />;
});

// export const updateDataset = async (id: string, metadata: MatrixDataSetUpdateDTO): Promise<MatrixDataSetUpdateDTO>
// export const createDataset = async (metadata: MatrixDataSetUpdateDTO, matrices: Array<MatrixInfoDTO>): Promise<MatrixDataSetDTO>
export default {};
