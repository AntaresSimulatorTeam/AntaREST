import { TabContext, TabList, TabListProps, TabPanel } from "@mui/lab";
import { Tab } from "@mui/material";
import { useState } from "react";
import { mergeSxProp } from "../../utils/muiUtils";

interface TabsViewProps {
  items: Array<{
    label: string;
    content?: React.ReactNode;
  }>;
  TabListProps?: TabListProps;
}

function TabsView({ items, TabListProps }: TabsViewProps) {
  const [value, setValue] = useState("0");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
    TabListProps?.onChange?.(event, newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabContext value={value}>
      <TabList
        {...TabListProps}
        onChange={handleChange}
        sx={mergeSxProp(
          { borderBottom: 1, borderColor: "divider" },
          TabListProps?.sx,
        )}
      >
        {items.map(({ label }, index) => (
          <Tab key={index} label={label} value={index.toString()} />
        ))}
      </TabList>
      {items.map(({ content }, index) => (
        <TabPanel
          key={index}
          value={index.toString()}
          sx={{
            px: 0,
          }}
        >
          {content}
        </TabPanel>
      ))}
    </TabContext>
  );
}

export default TabsView;
