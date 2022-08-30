import {
  AllClustersAndLinks,
  AreaInfoDTO,
  LinkCreationInfoDTO,
  LinkInfoWithUI,
  UpdateAreaUi,
} from "../../common/types";
import {
  BindingConstFields,
  ConstraintType,
  UpdateBindingConstraint,
} from "../../components/App/Singlestudy/explore/Modelization/BindingConstraints/BindingConstView/utils";
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

export const updateConstraintTerm = async (
  uuid: string,
  bindingConst: string,
  constraint: Partial<ConstraintType>
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${uuid}/bindingconstraints/${encodeURIComponent(
      bindingConst
    )}/term`,
    constraint
  );
  return res.data;
};

export const addConstraintTerm = async (
  uuid: string,
  bindingConst: string,
  constraint: ConstraintType
): Promise<ConstraintType | null> => {
  const res = await client.post(
    `/v1/studies/${uuid}/bindingconstraints/${encodeURIComponent(
      bindingConst
    )}/term`,
    constraint
  );
  return res.data;
};

export const deleteConstraintTerm = async (
  uuid: string,
  bindingConst: string,
  termId: ConstraintType["id"]
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/bindingconstraints/${encodeURIComponent(
      bindingConst
    )}/term/${encodeURIComponent(termId)}`
  );
  return res.data;
};

export const getBindingConstraint = async (
  uuid: string,
  bindingConst: string
): Promise<BindingConstFields> => {
  const res = await client.get(
    `/v1/studies/${uuid}/bindingconstraints/${encodeURIComponent(bindingConst)}`
  );
  return res.data;
};

export const getBindingConstraintList = async (
  uuid: string
): Promise<Array<BindingConstFields>> => {
  const res = await client.get(`/v1/studies/${uuid}/bindingconstraints`);
  return res.data;
};

export const updateBindingConstraint = async (
  uuid: string,
  bindingConst: string,
  data: UpdateBindingConstraint
): Promise<Array<void>> => {
  const res = await client.put(
    `/v1/studies/${uuid}/bindingconstraints/${encodeURIComponent(
      bindingConst
    )}`,
    data
  );
  return res.data;
};

export const getClustersAndLinks = async (
  uuid: string
): Promise<AllClustersAndLinks> => {
  const res = await client.get(`/v1/studies/${uuid}/linksandclusters`);
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
