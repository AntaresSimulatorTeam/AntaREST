import { Button } from "@mui/material";
import { useForm } from "react-hook-form";
import { StyledForm, StyledInput } from "./style";

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

  const onSubmit = (data: Inputs) => {
    if (data.file && data.file.length === 1) {
      onImport(data.file[0]);
    }
  };

  return (
    <StyledForm onSubmit={handleSubmit(onSubmit)}>
      <Button type="submit" variant="outlined" color="primary">
        {text}
      </Button>
      <StyledInput type="file" {...register("file", { required: true })} />
    </StyledForm>
  );
}

export default ImportForm;
