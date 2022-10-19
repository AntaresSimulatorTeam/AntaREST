import {
  addWeight,
  deleteWeight,
  getWeight,
  getAllWeights,
} from "../../../../../services/api/xpansion";
import FileList from "./FileList";

function Weights() {
  return (
    <FileList
      addResource={addWeight}
      deleteResource={deleteWeight}
      fetchResourceContent={getWeight}
      listResources={getAllWeights}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="xpansion.weights"
      isMatrix
    />
  );
}

export default Weights;
