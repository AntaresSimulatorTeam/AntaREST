import ClusterListing from "../common/ClusterListing";

function Renewables() {
  const fixedGroupList = [
    "Wind Onshore",
    "Wind Offshore",
    "Solar Thermal",
    "Solar PV",
    "Solar Rooftop",
    "Other RES 1",
    "Other RES 2",
    "Other RES 3",
    "Other RES 4",
  ];
  return <ClusterListing fixedGroupList={fixedGroupList} />;
}

export default Renewables;
