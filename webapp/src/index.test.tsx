import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { StyledEngineProvider } from "@mui/material";
import App from "./components/App";
import store from "./redux/store";

describe("Application Render", () => {
  test("renders the App component with providers", () => {
    const { getByText } = render(
      <StyledEngineProvider injectFirst>
        <Provider store={store}>
          <App />
        </Provider>
      </StyledEngineProvider>,
    );

    expect(getByText("Antares Web")).toBeInTheDocument();
  });
});
