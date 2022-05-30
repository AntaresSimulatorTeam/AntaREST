import { Button, useTheme } from "@mui/material";
import { useForm } from "react-hook-form";

interface Inputs {
  file: FileList;
}

interface PropTypes {
  onImport: (file: File) => void;
  text: string;
}

function ImportForm(props: PropTypes) {
  const { text, onImport } = props;
  const { register, handleSubmit } = useForm<Inputs>();
  const theme = useTheme();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const onSubmit = (data: Inputs) => {
    if (data.file && data.file.length === 1) {
      onImport(data.file[0]);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <form
      style={{ display: "flex", alignItems: "center" }}
      onSubmit={handleSubmit(onSubmit)}
    >
      <Button type="submit" variant="outlined" color="primary">
        {text}
      </Button>
      <input
        style={{ width: "200px", margin: theme.spacing(0, 2) }}
        type="file"
        {...register("file", { required: true })}
      />
    </form>
  );
}

export default ImportForm;
