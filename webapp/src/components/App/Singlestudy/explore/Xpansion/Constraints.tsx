import {
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../services/api/xpansion";
import FileList from "./FileList";

function Constraints() {
  return (
    <FileList
      addResource={addConstraints}
      deleteResource={deleteConstraints}
      fetchResourceContent={getConstraint}
      listResources={getAllConstraints}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="global.files"
    />
  );
}

export default Constraints;
