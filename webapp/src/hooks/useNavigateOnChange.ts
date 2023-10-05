import { useNavigate } from "react-router-dom";
import { useUpdateEffect } from "react-use";

function useNavigateOnChange(areaId: string): void {
  const navigate = useNavigate();

  useUpdateEffect(() => {
    navigate(-1);
  }, [areaId, navigate]);
}

export default useNavigateOnChange;
