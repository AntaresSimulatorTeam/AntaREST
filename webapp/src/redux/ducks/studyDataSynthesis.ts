import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import * as RA from "ramda-adjunct";
import {
  AreaInfoDTO,
  CreateMapNodeDTO,
  DeleteMapLinkDTO,
  DeleteMapNodeDTO,
  FileStudyTreeConfigDTO,
  GenericInfo,
  LinkProperties,
  NodeProperties,
  UpdateMapNodeDTO,
  WSMessage,
} from "../../common/types";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import * as api from "../../services/api/study";
import {
  createArea,
  deleteLink,
  deleteArea,
  updateAreaUI,
} from "../../services/api/studydata";
import { getMapNodes, getStudyData, getStudyDataIds } from "../selectors";
import { AppAsyncThunkConfig, AppDispatch, AppThunk } from "../store";
import { makeActionName } from "../utils";

export const studyDataAdapter = createEntityAdapter<FileStudyTreeConfigDTO>({
  selectId: (studyData) => studyData.study_id,
});

export interface StudyDataState
  extends ReturnType<typeof studyDataAdapter.getInitialState> {
  currentArea: string;
  currentLink: string;
  currentBindingConst: string;
  nodes: NodeProperties[];
  selectedNode: NodeProperties | undefined;
  selectedLink: LinkProperties | undefined;
  selectedNodeLinks: LinkProperties[];
}

const initialState = studyDataAdapter.getInitialState({
  currentArea: "",
  currentLink: "",
  currentBindingConst: "",
  nodes: [],
  selectedNode: undefined, // TODO currentArea
  selectedLink: undefined, // TODO currentLink
  selectedNodeLinks: [], // TODO create selector
}) as StudyDataState;

const n = makeActionName("studyDataSynthesis");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentBindingConst = createAction<
  NonNullable<StudyDataState["currentBindingConst"]>
>(n("SET_CURRENT_BINDING_CONST"));

export const updateStudyData = createAction<{
  id: FileStudyTreeConfigDTO["study_id"];
  changes: Partial<Omit<FileStudyTreeConfigDTO, "study_id">>;
}>(n("SET_STUDY_DATA"));

export const setCurrentArea = createAction<
  NonNullable<StudyDataState["currentArea"]>
>(n("SET_CURRENT_AREA"));

export const setCurrentLink = createAction<
  NonNullable<StudyDataState["currentLink"]>
>(n("SET_CURRENT_LINK"));

export const setMapNodes = createAction<StudyDataState["nodes"]>(
  n("SET_MAP_NODES")
);

export const setSelectedNode = createAction<StudyDataState["selectedNode"]>(
  n("SET_SELECTED_NODE")
);

export const setSelectedLink = createAction<StudyDataState["selectedLink"]>(
  n("SET_SELECTED_LINK")
);

export const setSelectedNodeLinks = createAction<
  StudyDataState["selectedNodeLinks"]
>(n("SET_SELECTED_NODE_LINKS"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

const initDefaultAreaLinkSelection = (
  dispatch: AppDispatch,
  studyData?: FileStudyTreeConfigDTO
): void => {
  if (studyData) {
    // Set current area
    const areas = Object.keys(studyData.areas);
    if (areas.length > 0) {
      dispatch(setCurrentArea(areas[0]));
    }
  }
};

export const setDefaultAreaLinkSelection =
  (studyId: FileStudyTreeConfigDTO["study_id"]): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    const studyData = getStudyData(state, studyId);
    initDefaultAreaLinkSelection(dispatch, studyData);
  };

export const createStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("CREATE_STUDY_DATA"), async (studyId, { dispatch, rejectWithValue }) => {
  try {
    // Fetch study synthesis data
    const studyData: FileStudyTreeConfigDTO = await api.getStudySynthesis(
      studyId
    );
    initDefaultAreaLinkSelection(dispatch, studyData);
    return studyData;
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const setStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO,
  WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("SET_STUDY_DATA"), (event, { rejectWithValue }) => {
  const { id } = event.payload;
  return api.getStudySynthesis(id as string).catch(rejectWithValue);
});

export const refreshStudyData =
  (event: WSMessage<GenericInfo>): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    if (getStudyDataIds(state).indexOf(event.payload.id) !== -1) {
      dispatch(setStudyData(event));
    }
  };

export const deleteStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO["study_id"],
  FileStudyTreeConfigDTO["study_id"] | WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("DELETE_STUDY_DATA"), async (arg) => {
  if (RA.isString(arg)) {
    return arg;
  }
  return arg.payload.id as string;
});

export const fetchNodesData = createAsyncThunk<
  void,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("FETCH_NODES_DATA"), async (studyId, { dispatch, rejectWithValue }) => {
  try {
    const studyData: FileStudyTreeConfigDTO = await api.getStudySynthesis(
      studyId
    );
    const areas = await api.getAreaPositions(studyId);
    const mapNodes = Object.keys(areas).map((area) => {
      return {
        id: area,
        name: studyData.areas[area].name,
        x: areas[area].ui.x,
        y: areas[area].ui.y,
        color: `rgb(${areas[area].ui.color_r}, ${areas[area].ui.color_g}, ${areas[area].ui.color_b})`,
        rgbColor: [
          areas[area].ui.color_r,
          areas[area].ui.color_g,
          areas[area].ui.color_b,
        ],
        size: { width: getNodeWidth(area), height: NODE_HEIGHT },
      };
    });
    dispatch(setMapNodes(mapNodes));
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const createMapNode = createAsyncThunk<
  AreaInfoDTO,
  CreateMapNodeDTO,
  AppAsyncThunkConfig
>(
  n("CREATE_MAP_NODE"),
  async (data, { dispatch, getState, rejectWithValue }) => {
    try {
      const state = getState();
      const mapNodes = getMapNodes(state);
      const { studyId, name } = data;
      const createdNode = await createArea(studyId, name);
      if (createdNode) {
        dispatch(
          setMapNodes([
            ...mapNodes,
            {
              id: createdNode.id,
              name: createdNode.name,
              x: 0,
              y: 0,
              color: NODE_COLOR,
              rgbColor: NODE_COLOR.slice(4, -1).split(",").map(Number),
              size: { width: getNodeWidth(name), height: NODE_HEIGHT },
            },
          ])
        );
      }
      return createdNode;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const updateMapNodeUI = createAsyncThunk<
  void,
  UpdateMapNodeDTO,
  AppAsyncThunkConfig
>(
  n("UPDATE_MAP_NODE_UI"),
  async (data, { dispatch, getState, rejectWithValue }) => {
    try {
      const state = getState();
      const mapNodes = getMapNodes(state);
      const { studyId, nodeId, nodeUI } = data;
      await updateAreaUI(studyId, nodeId, nodeUI);
      const updatedMapNodes = mapNodes.map((node) => {
        const updatedNode = { ...node };
        if (node.id === nodeId) {
          updatedNode.x = nodeUI.x;
          updatedNode.y = nodeUI.y;
          updatedNode.color = `rgb(${nodeUI.color_rgb[0]}, ${nodeUI.color_rgb[1]}, ${nodeUI.color_rgb[2]})`;
          updatedNode.rgbColor = [
            nodeUI.color_rgb[0],
            nodeUI.color_rgb[1],
            nodeUI.color_rgb[2],
          ];
        }
        return updatedNode;
      });
      dispatch(setMapNodes(updatedMapNodes));
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteMapLink = createAsyncThunk<
  void,
  DeleteMapLinkDTO,
  AppAsyncThunkConfig
>(
  n("DELETE_MAP_LINK"),
  async (data, { dispatch, getState, rejectWithValue }) => {
    try {
      // const state = getState();
      // const mapLinks = getMapLinks(state);
      const { studyId, source, target } = data;
      await deleteLink(studyId, source, target);
      /*   const updatedLinks = mapLinks.filter(
        (link) => link.source !== source || link.target !== target
      );
      dispatch(setMapLinks([...updatedLinks])); */
      dispatch(setSelectedLink(undefined));
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteMapNode = createAsyncThunk<
  void,
  DeleteMapNodeDTO,
  AppAsyncThunkConfig
>(
  n("DELETE_MAP_NODE"),
  async (data, { dispatch, getState, rejectWithValue }) => {
    try {
      const state = getState();
      const mapNodes = getMapNodes(state);
      const { studyId, source } = data;
      await deleteArea(studyId, source);
      const updatedNodes = mapNodes.filter((node) => node.id !== source);
      dispatch(setMapNodes([...updatedNodes]));
      dispatch(setSelectedNode(undefined));
      dispatch(setSelectedLink(undefined));
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudyData.fulfilled, studyDataAdapter.addOne)
    .addCase(setStudyData.fulfilled, studyDataAdapter.setOne)
    .addCase(updateStudyData, studyDataAdapter.updateOne)
    .addCase(deleteStudyData.fulfilled, studyDataAdapter.removeOne)
    .addCase(setCurrentArea, (draftState, action) => {
      draftState.currentArea = action.payload;
    })
    .addCase(setCurrentLink, (draftState, action) => {
      draftState.currentLink = action.payload;
    })
    .addCase(setCurrentBindingConst, (draftState, action) => {
      draftState.currentBindingConst = action.payload;
    })
    .addCase(setMapNodes, (draftState, action) => {
      draftState.nodes = action.payload;
    })
    .addCase(setSelectedNode, (draftState, action) => {
      draftState.selectedNode = action.payload;
    })
    .addCase(setSelectedLink, (draftState, action) => {
      draftState.selectedLink = action.payload;
    })
    .addCase(setSelectedNodeLinks, (draftState, action) => {
      draftState.selectedNodeLinks = action.payload;
    });
});
