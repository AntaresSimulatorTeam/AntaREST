/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Button } from "@mui/material";
import { useSnackbar } from "notistack";
import {
  MatrixType,
  StudyMetadata,
  XpansionCandidate,
  XpansionSettings,
  XpansionRenderView,
  LinkCreationInfo,
} from "../../../../common/types";
import SplitLayoutView from "../../../common/SplitLayoutView";
import {
  getAllCandidates,
  getXpansionSettings,
  xpansionConfigurationExist,
  getAllConstraints,
  getAllCapacities,
  createXpansionConfiguration,
  deleteXpansionConfiguration,
  addCandidate,
  deleteCandidate,
  deleteConstraints,
  deleteCapacity,
  getConstraint,
  getCapacity,
  addCapacity,
  addConstraints,
  updateCandidate,
  updateXpansionSettings,
} from "../../../../services/api/xpansion";
import { transformNameToId } from "../../../../services/utils/index";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { getAllLinks } from "../../../../services/api/studydata";
import SimpleLoader from "../../../common/loaders/SimpleLoader";
// import MatrixView from "../../ui/MatrixView";
import BasicModal from "../../../common/BasicModal";
import XpansionPropsView from "./XpansionPropsView";
import CreateCandidateModal from "./CreateCandidateModal";
import CandidateForm from "./CandidateForm";
import SettingsForm from "./SettingsForm";
import XpansionTable from "./XpansionTable";

function XpansionView() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [candidateCreationModal, setCandidateCreationModal] =
    useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [view, setView] = useState<XpansionRenderView | undefined>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [candidates, setCandidates] = useState<Array<XpansionCandidate>>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [links, setLinks] = useState<Array<LinkCreationInfo>>();
  const [capacities, setCapacities] = useState<Array<string>>();
  const [createConfigView, setCreateConfigView] = useState<boolean>(false);
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewModal, setConstraintViewModal] = useState<{
    filename: string;
    content: string;
  }>();
  const [capacityViewModal, setCapacityViewModal] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const initSettings = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const tempSettings = await getXpansionSettings(study.id);
          setSettings(tempSettings);
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    },
    [study?.id, t]
  );

  const initCandidate = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const tempCandidates = await getAllCandidates(study.id);
          for (let i = 0; i < tempCandidates.length; i += 1) {
            tempCandidates[i].link = tempCandidates.map((item) =>
              item.link
                .split(" - ")
                .map((index: any) => transformNameToId(index))
                .join(" - ")
            )[i];
          }
          setCandidates(tempCandidates);
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    },
    [study?.id, t]
  );

  const initFiles = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const tempConstraints = await getAllConstraints(study.id);
          setConstraints(tempConstraints);
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    },
    [study?.id, t]
  );

  const initCapa = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const tempCapa = await getAllCapacities(study.id);
          setCapacities(tempCapa);
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    },
    [study?.id, t]
  );

  const init = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const exist = await xpansionConfigurationExist(study.id);
          if (exist) {
            initSettings();
            initCandidate();
            initFiles();
            initCapa();
            const tempLinks = await getAllLinks(study.id);
            setLinks(tempLinks);
          } else {
            setCreateConfigView(true);
          }
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    },
    [study?.id, t, initSettings, initCandidate, initFiles, initCapa]
  );

  const createXpansion = async () => {
    try {
      if (study) {
        await createXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:createXpansionError"), e as AxiosError);
    } finally {
      setCreateConfigView(false);
      setLoaded(true);
      init();
    }
  };

  const deleteXpansion = async () => {
    try {
      if (study) {
        await deleteXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:deleteXpansionError"), e as AxiosError);
    } finally {
      setCreateConfigView(true);
    }
  };

  const createCandidate = async (candidate: XpansionCandidate) => {
    try {
      if (study) {
        if (candidate["annual-cost-per-mw"] === 0) {
          await addCandidate(study.id, {
            ...candidate,
            "annual-cost-per-mw": null,
          });
        } else {
          await addCandidate(study.id, candidate);
        }
        setCandidateCreationModal(false);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:createCandidateError"), e as AxiosError);
    } finally {
      initCandidate(() => {
        setSelectedItem(candidate.name);
        setView(XpansionRenderView.candidate);
      });
    }
  };

  const handleDeleteCandidate = async (name: string) => {
    if (candidates) {
      const obj = candidates.filter((o) => o.name !== name);
      try {
        if (study) {
          await deleteCandidate(study.id, name);
          setCandidates(obj);
          setSelectedItem(undefined);
          setView(undefined);
        }
      } catch (e) {
        enqueueErrorSnackbar(
          t("xpansion:deleteCandidateError"),
          e as AxiosError
        );
      } finally {
        initCandidate();
      }
    }
  };

  const handleUpdateCandidate = async (
    name: string,
    value: XpansionCandidate
  ) => {
    try {
      if (study) {
        if (value["link-profile"]?.length === 0) {
          if (value["already-installed-link-profile"]?.length === 0) {
            await updateCandidate(study.id, name, {
              ...value,
              "link-profile": null,
              "already-installed-link-profile": null,
            });
          } else {
            await updateCandidate(study.id, name, {
              ...value,
              "link-profile": null,
            });
          }
        } else if (value["already-installed-link-profile"]?.length === 0) {
          await updateCandidate(study.id, name, {
            ...value,
            "already-installed-link-profile": null,
          });
        } else {
          await updateCandidate(study.id, name, value);
        }
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:updateCandidateError"), e as AxiosError);
    } finally {
      if (name && value["annual-cost-per-mw"] && value.link) {
        if (
          ((value["max-investment"] && value["max-investment"] >= 0) ||
            (value["max-units"] &&
              value["max-units"] >= 0 &&
              value["unit-size"] &&
              value["unit-size"] >= 0)) &&
          value["max-investment"] &&
          !value["max-units"] &&
          value["max-investment"] &&
          !value["unit-size"]
        ) {
          initCandidate(() => setSelectedItem(name));
          enqueueSnackbar(t("studymanager:savedatasuccess"), {
            variant: "success",
          });
        }
      }
    }
  };

  const updateSettings = async (value: XpansionSettings) => {
    try {
      if (study) {
        await updateXpansionSettings(study.id, value);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:updateSettingsError"), e as AxiosError);
    } finally {
      initSettings(() => setView(XpansionRenderView.settings));
      enqueueSnackbar(t("studymanager:savedatasuccess"), {
        variant: "success",
      });
    }
  };

  const addOneConstraint = async (file: File) => {
    if (constraints) {
      try {
        if (study) {
          await addConstraints(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:addFileError"), e as AxiosError);
      } finally {
        initFiles(() => setView(XpansionRenderView.files));
      }
    }
  };

  const getOneConstraint = async (filename: string) => {
    try {
      if (study) {
        const content = await getConstraint(study.id, filename);
        setConstraintViewModal({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:getFileError"), e as AxiosError);
    }
  };

  const deleteConstraint = async (filename: string) => {
    if (constraints) {
      const tempConstraints = constraints.filter((a) => a !== filename);
      try {
        if (study) {
          await deleteConstraints(study.id, filename);
          setConstraints(tempConstraints);
          setView(XpansionRenderView.files);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:deleteFileError"), e as AxiosError);
      }
    }
  };

  const addOneCapa = async (file: File) => {
    if (capacities) {
      try {
        if (study) {
          await addCapacity(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:addFileError"), e as AxiosError);
      } finally {
        initCapa(() => setView(XpansionRenderView.capacities));
      }
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      if (study) {
        const content = await getCapacity(study.id, filename);
        setCapacityViewModal({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:getFileError"), e as AxiosError);
    }
  };

  const deleteCapa = async (filename: string) => {
    if (capacities) {
      const tempCapa = capacities.filter((a) => a !== filename);
      try {
        if (study) {
          await deleteCapacity(study.id, filename);
          setCapacities(tempCapa);
          setView(XpansionRenderView.capacities);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:deleteFileError"), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  const onClose = () => setCandidateCreationModal(false);

  const renderView = () => {
    if (view === XpansionRenderView.candidate) {
      if (candidates) {
        const candidate = candidates.find((o) => o.name === selectedItem);
        if (candidate) {
          return (
            <CandidateForm
              candidate={candidate}
              links={links || []}
              capacities={capacities || []}
              deleteCandidate={handleDeleteCandidate}
              updateCandidate={handleUpdateCandidate}
              onRead={getOneCapa}
            />
          );
        }
      }
    }
    if (view === XpansionRenderView.settings) {
      if (settings) {
        return (
          <SettingsForm
            settings={settings}
            constraints={constraints || []}
            updateSettings={updateSettings}
            onRead={getOneConstraint}
          />
        );
      }
    }
    if (view === XpansionRenderView.files) {
      return (
        <XpansionTable
          title={t("main:files")}
          content={constraints || []}
          onDelete={deleteConstraint}
          onRead={getOneConstraint}
          uploadFile={addOneConstraint}
        />
      );
    }
    if (view === XpansionRenderView.capacities) {
      return (
        <XpansionTable
          title={t("xpansion:capacities")}
          content={capacities || []}
          onDelete={deleteCapa}
          onRead={getOneCapa}
          uploadFile={addOneCapa}
        />
      );
    }
    return <Box />;
  };

  return (
    <>
      {loaded ? (
        createConfigView && (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            width="100%"
            flexGrow={1}
          >
            <Button
              sx={{
                width: "140px",
                border: "2px solid primary.main",
                "&:hover": {
                  border: "2px solid secondary.main",
                  color: "secondary.main",
                },
                fontWeight: "bold",
              }}
              color="primary"
              variant="outlined"
              onClick={createXpansion}
            >
              {t("xpansion:newXpansionConfig")}
            </Button>
          </Box>
        )
      ) : (
        <SimpleLoader />
      )}
      {loaded && !createConfigView && (
        <SplitLayoutView
          left={
            <XpansionPropsView
              candidateList={candidates || []}
              onAdd={() => setCandidateCreationModal(true)}
              selectedItem={selectedItem || ""}
              setView={setView}
              setSelectedItem={setSelectedItem}
              deleteXpansion={deleteXpansion}
            />
          }
          right={
            <Box width="100%" height="100%" padding={2} boxSizing="border-box">
              {renderView()}
            </Box>
          }
        />
      )}

      {candidateCreationModal && (
        <CreateCandidateModal
          open={candidateCreationModal}
          onClose={onClose}
          onSave={createCandidate}
          links={links || []}
        />
      )}
      {!!constraintViewModal && (
        <BasicModal
          open={!!constraintViewModal}
          title={constraintViewModal.filename}
          onClose={() => setConstraintViewModal(undefined)}
          rootStyle={{
            backgroundColor: "white",
            maxWidth: "80%",
            maxHeight: "70%",
            display: "flex",
            flexFlow: "column nowrap",
            alignItems: "center",
          }}
        >
          <Box
            width="900px"
            height="600px"
            display="flex"
            flexDirection="column"
            alignItems="flex-start"
            overflow="auto"
            padding="8px"
          >
            <code style={{ whiteSpace: "pre" }}>
              {constraintViewModal.content}
            </code>
          </Box>
        </BasicModal>
      )}
      {!!capacityViewModal && (
        <BasicModal
          open={!!capacityViewModal}
          title={capacityViewModal.filename}
          onClose={() => setCapacityViewModal(undefined)}
          rootStyle={{
            backgroundColor: "white",
            maxWidth: "80%",
            maxHeight: "70%",
            display: "flex",
            flexFlow: "column nowrap",
            alignItems: "center",
          }}
        >
          <Box
            width="900px"
            height="600px"
            display="flex"
            flexDirection="column"
            alignItems="flex-start"
            overflow="auto"
            padding="8px"
          >
            {/* <MatrixView matrix={capacityViewModal.content} readOnly /> */}
            salut
          </Box>
        </BasicModal>
      )}
    </>
  );
}

export default XpansionView;
