# Short-Term Storage Configuration

[⬅ Area Configuration](../02-areas.md)

## Introduction

This documentation is dedicated to configuring short-term storage (ST Storage) in the Antares Web application.
Please note that this feature is available starting from version 8.6 of the studies.

To access the configuration of ST storages:

1. From the "Study" view, click on the "MODELIZATION" tab.
2. Click on the "AREAS" tab, then choose an area from the sidebar.
3. Next, click on the "STORAGES" tab to access the page dedicated to ST storages.

![08-st-storages.tab.png](../../../assets/media/user-guide/study/areas/08-st-storages.tab.png)

## ST Storage List

![08-st-storages.list.png](../../../assets/media/user-guide/study/areas/08-st-storages.list.png)

On the ST storages page, you will find the following elements:

- **Command Bar:** Add, duplicate, or delete storages using the "Add," "Duplicate," and "Delete" buttons.
- **Toolbar:** Use the toolbar to filter and quickly search in the storages table.
- **Selection and Actions:** Click on a row to select a storage. You can then delete or duplicate it.

The storages table displays the following information:

- **Group:** Name of the group to which the storage belongs.
- **Name:** Name of the storage (link to the properties form).
- **Withdrawal (MW):** Withdrawal power of the storage.
- **Injection (MW):** Injection power of the storage.
- **Reservoir (MWh):** Reservoir capacity of the storage.
- **Efficiency (%):** Efficiency of the storage.
- **Initial Level (%):** Initial level of the storage.
- **Initial Level Optimized:** Indicates whether the initial level of the storage is optimized.

- The **Total** row displays the sum of the values in the **Withdrawal** and **Injection** columns.


## Configuration Form

Click on the name of a storage to open the properties form.

![08-st-storages.form.png](../../../assets/media/user-guide/study/areas/08-st-storages.form.png)

You will find the following elements:

- Click on the "Return" link to go back to the list of storages.
- Modify the values and click "Save" to confirm the changes.
- Use the "↶" buttons to undo changes and "↷" to redo them, confirm the modification with "Save."

The detailed configuration is available in the [Antares Simulator documentation](https://antares-simulator.readthedocs.io/en/latest/reference-guide/13-file-format/#short-term-storage_1).

## Time Series Matrices

In the tabs, you will find time series matrices composed of 8760 rows (hourly for a simulation year).

![08-st-storages.series.png](../../../assets/media/user-guide/study/areas/08-st-storages.series.png)

The available commands are:

- **Assign a Matrix:** Search and assign a matrix from the matrix store to short-term storage.
- **Import:** Drag and drop a TSV file to update the time series matrices.
- **Export:** Download the current TSV file using the "Export" button.

You can edit a cell and confirm with the "Enter" key. You can also edit a group of cells or an entire column and confirm with the "Ctrl+Enter" key combination.

The detailed configuration is available in the [Antares Simulator documentation](https://antares-simulator.readthedocs.io/en/latest/reference-guide/13-file-format/#short-term-storage_1).
