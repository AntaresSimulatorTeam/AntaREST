import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
  EntityState,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import {
  Area,
  AreaInfoDTO,
  StudyMetadata,
  UpdateAreaUi,
} from "../../common/types";

import { AppAsyncThunkConfig } from "../store";
import { makeActionName, makeLinkId, parseLinkId } from "../utils";
import * as studyApi from "../../services/api/study";
import * as studyDataApi from "../../services/api/studydata";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import { getArea, isStudyMapLinkExist } from "../selectors";
import {
  createArea,
  getAllLinks,
  updateAreaUI,
} from "../../services/api/studydata";

export interface StudyMapNode {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
}

export interface StudyMapLink {
  id: string;
  isTemp?: boolean;
  isDeleting?: boolean;
  // Props for react-d3-graph, don't rename them
  color?: string;
  strokeDasharray?: number[];
  strokeLinecap?: string;
  strokeWidth?: number;
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: Record<StudyMapNode["id"], StudyMapNode>;
  links: Record<StudyMapLink["id"], StudyMapLink>;
}

export const studyMapsAdapter = createEntityAdapter<StudyMap>({
  selectId: (studyMap) => studyMap.studyId,
});

export type StudyMapsState = EntityState<StudyMap>;

const initialState = studyMapsAdapter.getInitialState() as StudyMapsState;

const n = makeActionName("studyMaps");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

const createStudyMapLinkTemp = createAction<{
  studyId: StudyMap["studyId"];
  sourceId: StudyMapNode["id"];
  targetId: StudyMapNode["id"];
}>(n("CREATE_STUDY_MAP_LINK_TEMP"));

const updateStudyMapLink = createAction<{
  studyId: StudyMap["studyId"];
  id: StudyMapLink["id"];
  changes: Partial<Omit<StudyMapLink, "id">>;
}>(n("UPDATE_STUDY_MAP_LINK"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

type LinkStyle = [number[], string];

const makeLinkStyle = R.cond<[string], LinkStyle>([
  [R.equals("dot"), (): LinkStyle => [[1, 5], "round"]],
  [R.equals("dash"), (): LinkStyle => [[16, 8], "square"]],
  [R.equals("dotdash"), (): LinkStyle => [[10, 6, 1, 6], "square"]],
  [R.T, (): LinkStyle => [[0], "butt"]],
]);

async function getLinks(
  studyId: StudyMap["studyId"]
): Promise<StudyMap["links"]> {
  const allLinks = await getAllLinks({ uuid: studyId, withUi: true });
  return allLinks.reduce((acc, link) => {
    const [style, linecap] = makeLinkStyle(link.ui?.style);
    const id = makeLinkId(link.area1, link.area2);
    acc[id] = {
      id,
      color: `rgb(${link.ui?.color}`,
      strokeDasharray: style,
      strokeLinecap: linecap,
      strokeWidth: link.ui?.width < 2 ? 2 : link.ui?.width, // Sets minimum link width to 2
    };
    return acc;
  }, {} as StudyMap["links"]);
}

async function getNodes(
  state: AppState,
  studyId: StudyMap["studyId"]
): Promise<StudyMap["nodes"]> {
  const areaPositions = await studyApi.getAreaPositions(studyId);
  return Object.keys(areaPositions).reduce((acc, areaId) => {
    const { ui } = areaPositions[areaId];
    const rgb = [ui.color_r, ui.color_g, ui.color_b];
    const area = getArea(state, studyId, areaId) as Area;
    acc[areaId] = {
      id: areaId,
      name: area.name,
      x: ui.x,
      y: ui.y,
      color: `rgb(${rgb.join(", ")})`,
      rgbColor: rgb,
      size: { width: getNodeWidth(areaId), height: NODE_HEIGHT },
    };
    return acc;
  }, {} as StudyMap["nodes"]);
}

export const createStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return {
      studyId,
      nodes: await getNodes(getState(), studyId),
      links: await getLinks(studyId),
    };
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const createStudyMapNode = createAsyncThunk<
  {
    newArea: AreaInfoDTO;
    studyId: StudyMap["studyId"];
  },
  { name: AreaInfoDTO["name"]; studyId: StudyMap["studyId"] },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_NODE"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, name } = data;
    const newArea = await createArea(studyId, name);
    return { newArea, studyId };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapNode = createAsyncThunk<
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
  },
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
  },
  AppAsyncThunkConfig
>(n("UPDATE_STUDY_MAP_NODE"), async (data, { rejectWithValue }) => {
  const { studyId, nodeId, nodeUI } = data;

  try {
    await updateAreaUI(studyId, nodeId, nodeUI);
    return { studyId, nodeId, nodeUI };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const setStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("SET_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return {
      studyId,
      nodes: await getNodes(getState(), studyId),
      links: await getLinks(studyId),
    };
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const createStudyMapLink = createAsyncThunk<
  { studyId: StudyMap["studyId"]; linkId: StudyMapLink["id"] },
  {
    studyId: StudyMap["studyId"];
    sourceId: StudyMapNode["id"];
    targetId: StudyMapNode["id"];
  },
  AppAsyncThunkConfig
>(
  n("CREATE_STUDY_MAP_LINK"),
  async (args, { dispatch, rejectWithValue }) => {
    const { studyId, sourceId, targetId } = args;

    dispatch(createStudyMapLinkTemp(args));

    try {
      await studyDataApi.createLink(studyId, {
        area1: sourceId,
        area2: targetId,
      });

      return { studyId, linkId: makeLinkId(sourceId, targetId) };
    } catch (err) {
      return rejectWithValue(err);
    }
  },
  {
    condition: ({ studyId, sourceId, targetId }, { getState }) =>
      !isStudyMapLinkExist(getState(), studyId, makeLinkId(sourceId, targetId)),
    serializeError: () => new Error("Link already exist"),
  }
);

export const deleteStudyMapLink = createAsyncThunk<
  { studyId: StudyMap["studyId"]; linkId: StudyMapLink["id"] },
  {
    studyId: StudyMap["studyId"];
    id: StudyMapLink["id"];
  },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_LINK"),
  async ({ studyId, id }, { dispatch, rejectWithValue }) => {
    dispatch(
      updateStudyMapLink({ id, studyId, changes: { isDeleting: true } })
    );

    try {
      await studyDataApi.deleteLink(studyId, ...parseLinkId(id));
      return { studyId, linkId: id };
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudyMap.fulfilled, studyMapsAdapter.addOne)
    .addCase(setStudyMap.fulfilled, studyMapsAdapter.setOne)
    .addCase(createStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, newArea } = action.payload;
      const entity = draftState.entities[studyId];
      if (entity) {
        entity.nodes[newArea.id] = {
          id: newArea.id,
          name: newArea.name,
          x: 0,
          y: 0,
          color: NODE_COLOR,
          rgbColor: NODE_COLOR.slice(4, -1).split(",").map(Number),
          size: {
            width: getNodeWidth(newArea.name),
            height: NODE_HEIGHT,
          },
        };
      }
    })
    .addCase(updateStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, nodeId, nodeUI } = action.payload;
      const entity = draftState.entities[studyId];

      if (entity) {
        const color = nodeUI.color_rgb;
        entity.nodes[nodeId] = {
          ...entity.nodes[nodeId],
          x: nodeUI.x,
          y: nodeUI.y,
          color: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
          rgbColor: [color[0], color[1], color[2]],
        };
      }
    })
    .addCase(createStudyMapLinkTemp, (draftState, action) => {
      const { studyId, sourceId, targetId } = action.payload;
      const linkId = makeLinkId(sourceId, targetId);
      const entity = draftState.entities[studyId];

      if (entity) {
        entity.links[linkId] = {
          id: linkId,
          color: "rgb(112, 112, 112)",
          strokeDasharray: [0],
          strokeLinecap: "butt",
          strokeWidth: 2,
          isTemp: true,
        };
      }
    })
    .addCase(createStudyMapLink.fulfilled, (draftState, action) => {
      const { studyId, linkId } = action.payload;
      const entity = draftState.entities[studyId];

      if (entity) {
        entity.links[linkId].isTemp = false;
      }
    })
    .addCase(createStudyMapLink.rejected, (draftState, action) => {
      const { studyId, sourceId, targetId } = action.meta.arg;
      const entity = draftState.entities[studyId];

      if (entity) {
        delete entity.links[makeLinkId(sourceId, targetId)];
      }
    })
    .addCase(updateStudyMapLink, (draftState, action) => {
      const { studyId, id, changes } = action.payload;
      const entity = draftState.entities[studyId];

      if (entity && entity.links[id]) {
        entity.links[id] = {
          ...entity.links[id],
          ...changes,
        };
      }
    })
    .addCase(deleteStudyMapLink.fulfilled, (draftState, action) => {
      const { studyId, linkId } = action.payload;
      const entity = draftState.entities[studyId];

      if (entity) {
        delete entity.links[linkId];
      }
    })
    .addCase(deleteStudyMapLink.rejected, (draftState, action) => {
      const { studyId, id } = action.meta.arg;
      const entity = draftState.entities[studyId];

      if (entity) {
        delete entity.links[id]?.isDeleting;
      }
    });
});
