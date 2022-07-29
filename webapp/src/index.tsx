import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { StyledEngineProvider } from "@mui/material";
import { initI18n } from "./i18n";
import "./index.css";
import App from "./components/App";
import { Config, initConfig } from "./services/config";
import storage, { StorageKey } from "./services/utils/localStorage";
import store from "./redux/store";

initConfig((config: Config) => {
  const versionInstalled = storage.getItem(StorageKey.Version);
  storage.setItem(StorageKey.Version, config.version.gitcommit);
  if (versionInstalled !== config.version.gitcommit) {
    window.location.reload();
  }

  initI18n(config.version.gitcommit);

  const container = document.getElementById("root") as HTMLElement;
  const root = createRoot(container);

  root.render(
    <StyledEngineProvider injectFirst>
      <Provider store={store}>
        <App />
      </Provider>
    </StyledEngineProvider>
  );
});
