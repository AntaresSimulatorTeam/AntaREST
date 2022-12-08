import { createEntityAdapter, createSelector } from "@reduxjs/toolkit";
import {
  AllClustersAndLinks,
  Area,
  Cluster,
  GroupDetailsDTO,
  LinkElement,
  StudyMetadata,
  UserDetailsDTO,
} from "../common/types";
import { buildStudyTree } from "../components/App/Studies/utils";
import { filterStudies, sortStudies } from "../utils/studiesUtils";
import { convertVersions, isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { GroupsState } from "./ducks/groups";
import { StudiesSortConf, StudiesState, StudyFilters } from "./ducks/studies";
import {
  studySynthesesAdapter,
  StudySynthesesState,
} from "./ducks/studySyntheses";
import { UIState } from "./ducks/ui";
import { UsersState } from "./ducks/users";
import {
  StudyMapLink,
  StudyMap,
  studyMapsAdapter,
  StudyMapsState,
} from "./ducks/studyMaps";
import { makeLinkId, parseLinkId } from "./utils";

// TODO resultEqualityCheck

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

export const getAuthUser = (state: AppState): AuthState["user"] => {
  return state.auth.user;
};

export const isAuthUserAdmin = createSelector(getAuthUser, isUserAdmin);

export const isAuthUserInGroupAdmin = createSelector(getAuthUser, isGroupAdmin);

////////////////////////////////////////////////////////////////
// Study
////////////////////////////////////////////////////////////////

export const getStudiesState = (state: AppState): StudiesState => state.studies;

export const getStudiesStatus = (state: AppState): StudiesState["status"] => {
  return getStudiesState(state).status;
};

export const getStudiesScrollPosition = (
  state: AppState
): StudiesState["scrollPosition"] => {
  return getStudiesState(state).scrollPosition;
};

const studiesSelectors =
  createEntityAdapter<StudyMetadata>().getSelectors(getStudiesState);

export const getStudies = studiesSelectors.selectAll;

export const getStudiesById = studiesSelectors.selectEntities;

export const getStudyIds = studiesSelectors.selectIds;

export const getStudy = studiesSelectors.selectById;

export const getFavoriteStudyIds = (
  state: AppState
): StudiesState["favorites"] => {
  return getStudiesState(state).favorites;
};

export const getFavoriteStudies = createSelector(
  getStudiesById,
  getFavoriteStudyIds,
  (studiesById, favoriteIds) => {
    return favoriteIds
      .map((favId) => studiesById[favId])
      .filter((item): item is StudyMetadata => !!item);
  }
);

export const isStudyFavorite = (
  state: AppState,
  id: StudyMetadata["id"]
): boolean => {
  return getFavoriteStudyIds(state).includes(id);
};

export const getStudyFilters = (state: AppState): StudyFilters => {
  return getStudiesState(state).filters;
};

export const getStudiesSortConf = (state: AppState): StudiesSortConf => {
  return getStudiesState(state).sort;
};

export const getStudiesFilteredAndSorted = createSelector(
  getStudies,
  getStudyFilters,
  getStudiesSortConf,
  (studies, filters, sortConf) => {
    const sorted = sortStudies(sortConf, studies);
    return filterStudies(filters, sorted);
  }
);

export const getStudyIdsFilteredAndSorted = createSelector(
  getStudiesFilteredAndSorted,
  (studies) => studies.map((study) => study.id)
);

export const getStudiesTree = createSelector(getStudies, buildStudyTree);

export const getStudyVersions = (
  state: AppState
): StudiesState["versionList"] => {
  return getStudiesState(state).versionList;
};

export const getStudyVersionsFormatted = createSelector(
  getStudyVersions,
  convertVersions
);

export const getCurrentStudyId = (state: AppState): StudiesState["current"] => {
  return getStudiesState(state).current;
};

export const getCurrentStudy = createSelector(
  getStudiesById,
  getCurrentStudyId,
  (studies, current) => studies[current]
);

export const isCurrentStudyFavorite = createSelector(
  getFavoriteStudyIds,
  getCurrentStudyId,
  (favorites, current) => favorites.includes(current)
);

////////////////////////////////////////////////////////////////
// Users
////////////////////////////////////////////////////////////////

const getUsersState = (state: AppState): UsersState => state.users;

const usersSelectors =
  createEntityAdapter<UserDetailsDTO>().getSelectors(getUsersState);

export const getUsers = usersSelectors.selectAll;

export const getUsersById = usersSelectors.selectEntities;

export const getUserIds = usersSelectors.selectIds;

export const getUser = usersSelectors.selectById;

////////////////////////////////////////////////////////////////
// Groups
////////////////////////////////////////////////////////////////

const getGroupsState = (state: AppState): GroupsState => state.groups;

const groupsSelectors =
  createEntityAdapter<GroupDetailsDTO>().getSelectors(getGroupsState);

export const getGroups = groupsSelectors.selectAll;

export const getGroupsById = groupsSelectors.selectEntities;

export const getGroupIds = groupsSelectors.selectIds;

export const getGroup = groupsSelectors.selectById;

////////////////////////////////////////////////////////////////
// Study Syntheses
////////////////////////////////////////////////////////////////

export const getStudySynthesesState = (state: AppState): StudySynthesesState =>
  state.studySyntheses;

const studySynthesesSelectors = studySynthesesAdapter.getSelectors(
  getStudySynthesesState
);

export const getStudySynthesisById = studySynthesesSelectors.selectEntities;

export const getStudySynthesisIds = studySynthesesSelectors.selectIds;

export const getStudySyntheses = studySynthesesSelectors.selectAll;

export const getStudySynthesis = studySynthesesSelectors.selectById;

export const getCurrentStudySynthesis = createSelector(
  getStudySynthesisById,
  getCurrentStudyId,
  (syntheses, currentStudyId) => syntheses[currentStudyId]
);

export const getAreas = createSelector(getStudySynthesis, (synthesis) => {
  if (synthesis) {
    return Object.keys(synthesis.areas).map((id) => ({
      ...synthesis.areas[id],
      id,
    })) as Array<Area & { id: string }>;
  }
  return [];
});

export const getArea = createSelector(
  getStudySynthesis,
  (state: AppState, studyId: StudyMetadata["id"], areaId: string) => areaId,
  (synthesis, areaId) => synthesis?.areas[areaId]
);

export const getCurrentAreaId = (
  state: AppState
): StudySynthesesState["currentArea"] => {
  return getStudySynthesesState(state).currentArea;
};

export const getCurrentArea = createSelector(
  getCurrentStudySynthesis,
  getCurrentAreaId,
  (synthesis, areaId) => {
    if (synthesis?.areas[areaId]) {
      return { id: areaId, ...synthesis?.areas[areaId] } as Area & {
        id: string;
      };
    }
  }
);

export const getLinks = createSelector(getStudySynthesis, (synthesis) => {
  const links: LinkElement[] = [];
  if (synthesis) {
    Object.keys(synthesis.areas).forEach((id1) => {
      const area1 = { id: id1, ...synthesis.areas[id1] };
      Object.keys(area1.links).forEach((id2) => {
        const area2 = { id: id2, ...synthesis.areas[id2] };
        const id = makeLinkId(area1.id, area2.id);
        links.push({
          id, // For consistency
          name: id,
          label: `${area1.name} / ${area2.name}`,
          area1: area1.id,
          area2: area2.id,
        });
      });
    });
  }
  return links;
});

export const getCurrentLinkId = (
  state: AppState
): StudySynthesesState["currentLink"] => {
  return getStudySynthesesState(state).currentLink;
};

export const getCurrentLink = createSelector(
  getLinks,
  getCurrentLinkId,
  (links, linkId) => links.find((link) => link.name === linkId)
);

export const getCurrentAreaLinks = createSelector(
  getCurrentStudySynthesis,
  getLinks,
  getCurrentAreaId,
  (currStudySynthesis, links, currAreaId) => {
    if (currStudySynthesis && links && currAreaId) {
      const areaLinks = links.filter(
        (link) => link.area1 === currAreaId || link.area2 === currAreaId
      );
      return areaLinks;
    }
    return [];
  }
);

export const getCurrentBindingConstId = (
  state: AppState
): StudySynthesesState["currentBindingConst"] => {
  return getStudySynthesesState(state).currentBindingConst;
};

export const getCurrentClusters = (
  type: "thermals" | "renewables",
  studyId: string,
  state: AppState
): Array<Cluster> => {
  const currentStudyState = getStudySynthesesState(state);
  const { currentArea } = currentStudyState;
  const clusters =
    currentStudyState.entities[studyId]?.areas[currentArea][type];
  return clusters || [];
};

export const getBindingConst = createSelector(getStudySynthesis, (studyData) =>
  studyData ? studyData.bindings || [] : []
);

export const getLinksAndClusters = createSelector(
  getStudySynthesis,
  (synthesis) => {
    const linksAndClusters: AllClustersAndLinks = {
      links: [],
      clusters: [],
    };
    if (synthesis) {
      const res = Object.keys(synthesis.areas).reduce((acc, areaId) => {
        const area = { id: areaId, name: synthesis.areas[areaId].name };
        acc.links.push({
          element: area,
          item_list: Object.keys(synthesis.areas[areaId].links).map(
            (area2) => ({
              id: area2,
              name: synthesis.areas[area2].name,
            })
          ),
        });
        acc.clusters.push({
          element: area,
          item_list: synthesis.areas[areaId].thermals.map((thermal) => ({
            id: thermal.id,
            name: thermal.name,
          })),
        });
        return acc;
      }, linksAndClusters);
      return res;
    }
    return linksAndClusters;
  }
);

export const getStudyOutput = createSelector(
  getStudySynthesis,
  (state: AppState, studyId: StudyMetadata["id"], outputId: string) => outputId,
  (synthesis, outputId) => {
    if (synthesis?.outputs[outputId]) {
      return { id: outputId, ...synthesis?.outputs[outputId] };
    }
  }
);

////////////////////////////////////////////////////////////////
// Study Maps
////////////////////////////////////////////////////////////////

export const getStudyMapsState = (state: AppState): StudyMapsState =>
  state.studyMaps;

const studyMapsSelectors = studyMapsAdapter.getSelectors(getStudyMapsState);

export const getStudyMapsById = studyMapsSelectors.selectEntities;

export const getStudyMapsIds = studyMapsSelectors.selectIds;

export const getStudyMaps = studyMapsSelectors.selectAll;

export const getStudyMap = studyMapsSelectors.selectById;

export const getStudyMapNodes = createSelector(getStudyMap, (studyMap) =>
  Object.values(studyMap?.nodes || {})
);

export const getCurrentStudyMapNode = createSelector(
  getStudyMapsById,
  getCurrentStudyId,
  getCurrentAreaId,
  (studyMapsById, currentStudyId, currentAreaId) =>
    studyMapsById[currentStudyId]?.nodes[currentAreaId]
);

export const getStudyMapLinks = createSelector(
  getLinks,
  getStudyMap,
  (
    links,
    studyMap
  ): Array<
    LinkElement &
      Partial<StudyMapLink> & {
        source: string;
        target: string;
        opacity?: number;
      }
  > => {
    const nodeLinks = links
      .filter((link) => !studyMap?.links[link.id]?.isDeleting)
      .map((link) => ({
        ...link,
        ...studyMap?.links[link.id],
        source: link.area1,
        target: link.area2,
      }));

    const tempNodeLinks = Object.values(studyMap?.links || [])
      .filter((link) => link.isTemp)
      .map((link) => {
        const [area1, area2] = parseLinkId(link.id);
        return {
          label: "",
          name: link.id,
          area1,
          area2,
          source: area1,
          target: area2,
          ...link,
          // For react-d3-graph
          opacity: 0.3,
        };
      });

    return [...nodeLinks, ...tempNodeLinks];
  }
);

export const isStudyMapLinkExist = createSelector(
  getStudyMap,
  (state: AppState, studyId: StudyMap["studyId"], linkId: StudyMapLink["id"]) =>
    linkId,
  (studyMap, linkId) => !!studyMap?.links[linkId]
);

////////////////////////////////////////////////////////////////
// UI
////////////////////////////////////////////////////////////////

const getUIState = (state: AppState): AppState["ui"] => state.ui;

export const getWebSocketConnected = (
  state: AppState
): UIState["webSocketConnected"] => {
  return getUIState(state).webSocketConnected;
};

export const getTaskNotificationsCount = (
  state: AppState
): UIState["taskNotificationsCount"] => {
  return getUIState(state).taskNotificationsCount;
};

export const getMaintenanceMode = (
  state: AppState
): UIState["maintenanceMode"] => {
  return getUIState(state).maintenanceMode;
};

export const getMessageInfo = (state: AppState): UIState["messageInfo"] => {
  return getUIState(state).messageInfo;
};

export const getMenuExtended = (state: AppState): UIState["menuExtended"] => {
  return getUIState(state).menuExtended;
};
