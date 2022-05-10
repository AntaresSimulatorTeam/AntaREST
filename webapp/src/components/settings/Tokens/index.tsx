import {
  Box,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Typography,
} from "@mui/material";
import produce from "immer";
import { ReactNode, useMemo, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper, useUpdateEffect } from "react-use";
import { Action } from "redux";
import DeleteIcon from "@mui/icons-material/Delete";
import InfoIcon from "@mui/icons-material/Info";
import TokenIcon from "@mui/icons-material/Token";
import * as R from "ramda";
import { useSnackbar } from "notistack";
import { useSelector } from "react-redux";
import { BotDTO, BotDetailsDTO, UserDTO } from "../../../common/types";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import {
  deleteBot,
  getBots,
  getUser,
  getUsers,
} from "../../../services/api/user";
import { isUserAdmin, sortByProp } from "../../../services/utils";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import Header from "./Header";
import { getAuthUser } from "../../../store/selectors";
import TokenInfoDialog from "./dialog/TokenInfoDialog";

/**
 * Types
 */

interface BotDetailsDtoWithUser extends BotDetailsDTO {
  user: UserDTO;
}

enum TokenActionKind {
  ADD = "ADD",
  DELETE = "DELETE",
  RESET = "RESET",
}

interface TokenAction extends Action<string> {
  payload?: BotDTO["id"] | BotDTO | BotDTO[];
}

/**
 * Utils
 */

const reducer = produce<BotDetailsDtoWithUser[], [TokenAction]>(
  (draft, action) => {
    const { payload } = action;

    switch (action.type) {
      case TokenActionKind.ADD: {
        draft.push(payload as BotDetailsDtoWithUser);
        return;
      }
      case TokenActionKind.DELETE: {
        const index = draft.findIndex((token) => token.id === payload);
        if (index > -1) {
          draft.splice(index, 1);
        }
        return;
      }
      case TokenActionKind.RESET:
        return payload as BotDetailsDtoWithUser[];
    }
  }
);

/**
 * Component
 */

function Tokens() {
  const [tokenToDisplayInfo, setTokenToDisplayInfo] = useState<BotDetailsDTO>();
  const [tokenToDelete, setTokenToDelete] = useState<BotDetailsDTO>();
  const [tokensInLoading, setTokensInLoading] = useState<BotDetailsDTO[]>([]);
  const [tokens, dispatch] = useReducer(reducer, []);
  const [searchValue, setSearchValue] = useState("");
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();
  const authUser = useSelector(getAuthUser);

  const {
    data: initialTokens,
    isLoading,
    reload: reloadFetchTokens,
  } = usePromiseWithSnackbarError(
    async () => {
      if (!authUser) {
        return [];
      }

      const isAuthUserAdmin = isUserAdmin(authUser);
      const bots = await getBots({
        verbose: 1,
        owner: isAuthUserAdmin ? undefined : authUser.id,
      });

      if (isAuthUserAdmin) {
        const users = await getUsers();
        return bots.map((bot) => ({
          ...bot,
          user: users.find((user) => user.id === bot.owner),
        }));
      }

      const user = await getUser(authUser.id);
      return bots.map((bot) => ({ ...bot, user }));
    },
    { errorMessage: t("settings:tokensError") },
    [authUser]
  );

  useUpdateEffect(() => {
    setTokenToDelete(undefined);
    setTokensInLoading([]);

    dispatch({ type: TokenActionKind.RESET, payload: initialTokens || [] });
  }, [initialTokens]);

  const filteredAndSortedTokens = useMemo(() => {
    let list = tokens;
    if (searchValue) {
      const searchVal = searchValue.toLowerCase();
      list = tokens?.filter(
        ({ name, user }) =>
          name.toLowerCase().includes(searchVal) ||
          user.name.toLocaleLowerCase().includes(searchVal)
      );
    }
    return sortByProp((token) => token.user.name, list);
  }, [searchValue, tokens]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const addToken = (token: BotDTO) => {
    dispatch({ type: TokenActionKind.ADD, payload: token });
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteToken = () => {
    if (!tokenToDelete) {
      return;
    }

    const token = tokenToDelete;
    setTokensInLoading((prev) => [...prev, token]);
    setTokenToDelete(undefined);

    mounted(deleteBot(token.id))
      .then(() => {
        dispatch({ type: TokenActionKind.DELETE, payload: token.id });
        enqueueSnackbar(t("settings:onTokenDeleteSuccess", [token.name]), {
          variant: "success",
        });
      })
      .catch((err) => {
        enqueueErrorSnackbar(
          t("settings:onTokenDeleteError", [token.name]),
          err
        );
      })
      .finally(() => {
        setTokensInLoading((prev) => prev.filter((u) => u !== token));
      });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: 1,
      }}
    >
      <Header
        setSearchValue={setSearchValue}
        addToken={addToken}
        reloadFetchTokens={reloadFetchTokens}
      />
      <List sx={{ overflow: "auto" }}>
        {R.cond([
          // Loading
          [
            () => isLoading,
            () =>
              Array.from({ length: 3 }, (v, k) => k).map((v) => (
                <ListItem key={v} disablePadding>
                  <Skeleton sx={{ width: 1, height: 50 }} />
                </ListItem>
              )) as ReactNode,
          ],
          // Token list
          [
            () => filteredAndSortedTokens.length > 0,
            () =>
              filteredAndSortedTokens.map((token) => (
                <ListItem
                  key={token.id}
                  secondaryAction={
                    tokensInLoading.includes(token) ? (
                      <Box sx={{ display: "flex" }}>
                        <CircularProgress color="inherit" size={25} />
                      </Box>
                    ) : (
                      <>
                        <IconButton
                          onClick={() => setTokenToDisplayInfo(token)}
                        >
                          <InfoIcon />
                        </IconButton>
                        <IconButton
                          edge="end"
                          onClick={() => setTokenToDelete(token)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )
                  }
                  disablePadding
                >
                  <ListItemButton onClick={() => setTokenToDisplayInfo(token)}>
                    <ListItemIcon>
                      <TokenIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: "flex" }}>
                          {token.name}
                          <Typography
                            sx={{ ml: 2, opacity: 0.4, fontStyle: "italic" }}
                          >
                            {token.user.name}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              )),
          ],
          // No token
          [
            R.T,
            () => (
              <Typography sx={{ m: 2 }} align="center">
                {t("settings:noToken")}
              </Typography>
            ),
          ],
        ])()}
      </List>
      {tokenToDelete && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setTokenToDelete(undefined)}
          onConfirm={handleDeleteToken}
          alert="warning"
          open
        >
          {t("settings:deleteTokenConfirmation", [tokenToDelete.name])}
        </ConfirmationDialog>
      )}
      {tokenToDisplayInfo && (
        <TokenInfoDialog
          open
          onOk={() => setTokenToDisplayInfo(undefined)}
          token={tokenToDisplayInfo}
        />
      )}
    </Box>
  );
}

export default Tokens;
