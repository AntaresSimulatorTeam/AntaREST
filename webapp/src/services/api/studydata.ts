import {
  AllClustersAndLinks,
  LinkCreationInfoDTO,
  LinkInfoWithUI,
  UpdateAreaUi,
} from "../../common/types";
import {
  BindingConstraint,
  ConstraintTerm,
  bindingConstraintModelAdapter,
} from "../../components/App/Singlestudy/explore/Modelization/BindingConstraints/BindingConstView/utils";
import { StudyMapNode } from "../../redux/ducks/studyMaps";
import client from "./client";

export const createArea = async (
  uuid: string,
  name: string,
): Promise<StudyMapNode> => {
  const res = await client.post(`/v1/studies/${uuid}/areas?uuid=${uuid}`, {
    name,
    type: "AREA",
  });
  return res.data;
};

export const createLink = async (
  uuid: string,
  linkCreationInfo: LinkCreationInfoDTO,
): Promise<string> => {
  const res = await client.post(
    `/v1/studies/${uuid}/links?uuid=${uuid}`,
    linkCreationInfo,
  );
  return res.data;
};

export const updateAreaUI = async (
  uuid: string,
  areaId: string,
  layerId: string,
  areaUi: UpdateAreaUi,
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${uuid}/areas/${areaId}/ui?uuid=${uuid}&area_id=${areaId}&layer=${layerId}`,
    areaUi,
  );
  return res.data;
};

export const deleteArea = async (
  uuid: string,
  areaId: string,
): Promise<string> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/areas/${areaId}?uuid=${uuid}&area_id=${areaId}`,
  );
  return res.data;
};

export const deleteLink = async (
  uuid: string,
  areaIdFrom: string,
  areaIdTo: string,
): Promise<string> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/links/${areaIdFrom}/${areaIdTo}?uuid=${uuid}&area_from=${areaIdFrom}&area_to=${areaIdTo}`,
  );
  return res.data;
};

export const updateConstraintTerm = async (
  studyId: string,
  constraintId: string,
  term: Partial<ConstraintTerm>,
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term`,
    term,
  );
  return res.data;
};

export const createConstraintTerm = async (
  studyId: string,
  constraintId: string,
  term: ConstraintTerm,
): Promise<void> => {
  const res = await client.post(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term`,
    term,
  );
  return res.data;
};

export const deleteConstraintTerm = async (
  studyId: string,
  constraintId: string,
  termId: ConstraintTerm["id"],
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term/${encodeURIComponent(termId)}`,
  );
  return res.data;
};

export const getBindingConstraint = async (
  studyId: string,
  constraintId: string,
): Promise<BindingConstraint> => {
  const res = await client.get(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}`,
  );

  return bindingConstraintModelAdapter(res.data);
};

export const getBindingConstraintList = async (
  studyId: string,
): Promise<BindingConstraint[]> => {
  const res = await client.get(`/v1/studies/${studyId}/bindingconstraints`);
  return res.data;
};

export const updateBindingConstraint = async (
  studyId: string,
  constraintId: string,
  data: BindingConstraint,
): Promise<void> => {
  const adaptedData = bindingConstraintModelAdapter(data);

  const res = await client.put(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}`,
    adaptedData,
  );
  return res.data;
};

export const createBindingConstraint = async (
  studyId: string,
  data: Partial<BindingConstraint>,
): Promise<BindingConstraint> => {
  const res = await client.post(
    `/v1/studies/${studyId}/bindingconstraints`,
    data,
  );
  return res.data;
};

export const getClustersAndLinks = async (
  uuid: string,
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
  params: T,
): Promise<Array<LinkTypeFromParams<T>>> => {
  const { uuid, withUi } = params;
  const res = await client.get(
    `/v1/studies/${uuid}/links${withUi ? `?with_ui=${withUi}` : ""}`,
  );
  return res.data;
};

export default {};
