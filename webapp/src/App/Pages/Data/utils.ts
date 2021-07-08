/* eslint-disable @typescript-eslint/camelcase */
import { GroupDTO, MatrixMetadata, MatrixMetadataDTO } from '../../../common/types';
import { Metadata } from '../../../components/Data/KeyValue';
import { createMatrixByImportation, updateMetadata } from '../../../services/api/matrix';

const updateMatrix = async (
  id: string,
  name: string,
  publicStatus: boolean,
  metadataList: Array<Metadata>,
  selectedGroupList: Array<GroupDTO>,
  onNewDataUpdate: (newData: MatrixMetadataDTO) => void,
): Promise<any> => {
  const metadata: MatrixMetadata = {};
  metadataList.forEach((elm) => {
    if (!elm.editStatus) {
      metadata[elm.key] = elm.value;
    }
  });
  const matrixMetadata: MatrixMetadataDTO = {
    id,
    name,
    metadata,
    public: publicStatus,
    groups: publicStatus ? [] : selectedGroupList,
  };

  const newData = await updateMetadata(matrixMetadata);
  onNewDataUpdate(newData);
};

export const saveMatrix = async (
  name: string,
  publicStatus: boolean,
  metadataList: Array<Metadata>,
  selectedGroupList: Array<GroupDTO>,
  onNewDataUpdate: (newData: MatrixMetadataDTO) => void,
  file?: File,
  data?: MatrixMetadataDTO,
): Promise<string> => {
  let id = '';
  if (!name.replace(/\s/g, '')) throw Error('data:emptyName');

  if (data === undefined) {
    if (file) {
      id = await createMatrixByImportation(file);
    } else throw Error('data:fileNotUploaded');
  } else {
    id = data.id;
  }

  await updateMatrix(id, name, publicStatus, metadataList, selectedGroupList, onNewDataUpdate);
  return data ? 'data:onMatrixUpdate' : 'data:onMatrixCreation';
};

export default {};
