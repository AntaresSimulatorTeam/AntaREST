import ClusterListing from "../common/ClusterListing";

function Thermal() {
  const fixedGroupList = [
    "Gas",
    "Hard Coal",
    "Lignite",
    "Mixed fuel",
    "Nuclear",
    "Oil",
    "Other",
    "Other 2",
    "Other 3",
    "Other 4",
  ];
  return <ClusterListing fixedGroupList={fixedGroupList} />;
}

export default Thermal;
