import {
  getAllCapacities,
  deleteCapacity,
  getCapacity,
  addCapacity,
} from "../../../../../services/api/xpansion";
import FileList from "./FileList";

function Capacities() {
  return (
    <FileList
      addResource={addCapacity}
      deleteResource={deleteCapacity}
      fetchResourceContent={getCapacity}
      listResources={getAllCapacities}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="xpansion.capacities"
      isMatrix
    />
  );
}

export default Capacities;
