/* eslint-disable @typescript-eslint/camelcase */
import { GroupDTO, MatrixDataSetDTO, MatrixDataSetUpdateDTO, MatrixInfoDTO } from '../../../common/types';
import { createMatrixByImportation, updateDataSet, createDataSet } from '../../../services/api/matrix';

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
): Promise<string> => {
  if (!name.replace(/\s/g, '')) throw Error('data:emptyName');

  if (data === undefined) {
    if (file) {
      const matrixInfos = await createMatrixByImportation(file);
      await createMatrix(name, publicStatus, selectedGroupList, matrixInfos, onNewDataUpdate);
    } else throw Error('data:fileNotUploaded');
  } else {
    await updateMatrix(data, name, publicStatus, selectedGroupList, onNewDataUpdate);
  }

  return data ? 'data:onMatrixUpdate' : 'data:onMatrixCreation';
};

// export const updateDataset = async (id: string, metadata: MatrixDataSetUpdateDTO): Promise<MatrixDataSetUpdateDTO>
// export const createDataset = async (metadata: MatrixDataSetUpdateDTO, matrices: Array<MatrixInfoDTO>): Promise<MatrixDataSetDTO>
export default {};
