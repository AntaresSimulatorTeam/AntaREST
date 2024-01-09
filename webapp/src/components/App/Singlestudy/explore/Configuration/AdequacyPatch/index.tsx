import { useOutletContext } from "react-router";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  AdequacyPatchFormFields,
  getAdequacyPatchFormFields,
  setAdequacyPatchFormFields,
} from "./utils";
import TableMode from "../../../../../common/TableMode";
import TabsView from "../../../../../common/TabsView";

function AdequacyPatch() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<AdequacyPatchFormFields>,
  ) => {
    return setAdequacyPatchFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      items={[
        {
          label: t("study.configuration.adequacyPatch.tab.general"),
          content: (
            <Form
              key={study.id}
              config={{
                defaultValues: () => getAdequacyPatchFormFields(study.id),
              }}
              onSubmit={handleSubmit}
              enableUndoRedo
            >
              <Fields />
            </Form>
          ),
        },
        {
          label: t("study.configuration.adequacyPatch.tab.perimeter"),
          content: (
            <TableMode
              studyId={study.id}
              type="area"
              columns={["adequacyPatchMode"]}
            />
          ),
        },
      ]}
      TabListProps={{ sx: { mt: -2 } }}
    />
  );
}

export default AdequacyPatch;
