import React from "react";
import "./style.css";
import logo from "./logo.png";

function MainContentLoader() {
  return (
    <>
      <img
        src={logo}
        alt="logo"
        style={{
          width: "64px",
          height: "64px",
          position: "absolute",
          top: "50%",
          left: "50%",
          margin: "-32px 0 0 -32px",
        }}
      />
      <div className="nest3" />
    </>
  );
}

export default MainContentLoader;
