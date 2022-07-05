import {
  AreaInfoDTO,
  LinkCreationInfoDTO,
  LinkInfoWithUI,
  UpdateAreaUi,
} from "../../common/types";
import client from "./client";

export const createArea = async (
  uuid: string,
  name: string
): Promise<AreaInfoDTO> => {
  const res = await client.post(`/v1/studies/${uuid}/areas?uuid=${uuid}`, {
    name,
    type: "AREA",
  });
  return res.data;
};

export const createLink = async (
  uuid: string,
  linkCreationInfo: LinkCreationInfoDTO
): Promise<string> => {
  const res = await client.post(
    `/v1/studies/${uuid}/links?uuid=${uuid}`,
    linkCreationInfo
  );
  return res.data;
};

export const updateAreaUI = async (
  uuid: string,
  areaId: string,
  areaUi: UpdateAreaUi
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${uuid}/areas/${areaId}/ui?uuid=${uuid}&area_id=${areaId}`,
    areaUi
  );
  return res.data;
};

export const deleteArea = async (
  uuid: string,
  areaId: string
): Promise<string> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/areas/${areaId}?uuid=${uuid}&area_id=${areaId}`
  );
  return res.data;
};

export const deleteLink = async (
  uuid: string,
  areaIdFrom: string,
  areaIdTo: string
): Promise<string> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/links/${areaIdFrom}/${areaIdTo}?uuid=${uuid}&area_from=${areaIdFrom}&area_to=${areaIdTo}`
  );
  return res.data;
};

interface GetAllLinksParams {
  uuid: string;
  withUi?: boolean;
}

type LinkTypeFromParams<T extends GetAllLinksParams> = T["withUi"] extends true
  ? LinkInfoWithUI
  : LinkCreationInfoDTO;

export const getAllLinks = async <T extends GetAllLinksParams>(
  params: T
): Promise<Array<LinkTypeFromParams<T>>> => {
  const { uuid, withUi } = params;
  const res = await client.get(
    `/v1/studies/${uuid}/links${withUi ? `?with_ui=${withUi}` : ""}`
  );
  return res.data;
};

export default {};
