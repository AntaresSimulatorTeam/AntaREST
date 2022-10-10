import moment from "moment";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { StudyMetadata, StudyType } from "../common/types";
import { StudiesSortConf, StudyFilters } from "../redux/ducks/studies";

////////////////////////////////////////////////////////////////
// Sort
////////////////////////////////////////////////////////////////

export function sortStudies(
  sortConf: StudiesSortConf,
  studies: StudyMetadata[]
): StudyMetadata[] {
  return R.sort((studyA, studyB) => {
    const first = sortConf.order === "ascend" ? studyA : studyB;
    const second = sortConf.order === "ascend" ? studyB : studyA;
    if (sortConf.property === "name") {
      return first.name.localeCompare(second.name);
    }
    return moment(first.modificationDate).isAfter(
      moment(second.modificationDate)
    )
      ? 1
      : -1;
  }, studies);
}

////////////////////////////////////////////////////////////////
// Predicates
////////////////////////////////////////////////////////////////

const folderPredicate = R.curry(
  (folder: string, strict: boolean, study: StudyMetadata) => {
    let studyNodeId = `root/${study.workspace}`;
    if (study.folder) {
      const folderPathComponents = study.folder.split("/");
      folderPathComponents.pop();
      const folderPath = folderPathComponents.join("/");
      if (folderPath) {
        studyNodeId += `/${folderPath}`;
      }
    }
    return strict
      ? studyNodeId === folder
      : `${studyNodeId}/`.startsWith(`${folder}/`);
  }
);

const inputValuePredicate = R.curry(
  (inputValue: StudyFilters["inputValue"], study: StudyMetadata) => {
    if (!inputValue) {
      return true;
    }
    const regex = new RegExp(inputValue, "i");
    return study.name.search(regex) !== -1 || study.id.search(regex) !== -1;
  }
);

const tagsPredicate = R.curry(
  (tags: StudyFilters["tags"], study: StudyMetadata) => {
    if (tags.length === 0) {
      return true;
    }
    if (!study.tags || study.tags.length === 0) {
      return false;
    }
    return R.intersection(study.tags, tags).length > 0;
  }
);

const versionsPredicate = R.curry(
  (versions: StudyFilters["versions"], study: StudyMetadata) => {
    return versions.length === 0 || versions.includes(study.version);
  }
);

const usersPredicate = R.curry(
  (users: StudyFilters["users"], study: StudyMetadata) => {
    if (users.length === 0) {
      return true;
    }
    return RA.isNumber(study.owner.id) && users.includes(study.owner.id);
  }
);

const groupsPredicate = R.curry(
  (groups: StudyFilters["groups"], study: StudyMetadata) => {
    return (
      groups.length === 0 ||
      R.intersection(study.groups.map(R.prop("id")), groups).length > 0
    );
  }
);

const managedPredicate = R.curry(
  (managed: StudyFilters["managed"], study: StudyMetadata) => {
    return managed ? study.managed : true;
  }
);

const archivedPredicate = R.curry(
  (archived: StudyFilters["archived"], study: StudyMetadata) => {
    return archived ? study.archived : true;
  }
);

const variantPredicate = R.curry(
  (variant: StudyFilters["variant"], study: StudyMetadata) => {
    return variant ? study.type === StudyType.VARIANT : true;
  }
);

////////////////////////////////////////////////////////////////
// Filter
////////////////////////////////////////////////////////////////

export function filterStudies(
  filters: StudyFilters,
  studies: StudyMetadata[]
): StudyMetadata[] {
  const predicates = [
    folderPredicate(filters.folder, filters.strictFolder),
    inputValuePredicate(filters.inputValue),
    tagsPredicate(filters.tags),
    versionsPredicate(filters.versions),
    usersPredicate(filters.users),
    groupsPredicate(filters.groups),
    managedPredicate(filters.managed),
    archivedPredicate(filters.archived),
    variantPredicate(filters.variant),
  ];
  return R.filter(R.allPass(predicates), studies);
}
