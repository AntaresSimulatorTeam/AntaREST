/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import type { BotDetailsDTO } from "@/types/types";
import { Box, List, ListItem, Skeleton } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getAuthUser } from "../../../../redux/selectors";
import { getBots, getUser, getUsers } from "../../../../services/api/user";
import { isUserAdmin } from "../../../../services/utils";
import Header from "./Header";
import TokenList from "./TokenList";
import type { BotDetailsDtoWithUser } from "./types";

function Tokens() {
  const { t } = useTranslation();
  const [searchValue, setSearchValue] = useState("");
  const [tokensInLoading, setTokensInLoading] = useState<Array<BotDetailsDTO["id"]>>([]);
  const authUser = useAppSelector(getAuthUser);

  const res = usePromiseWithSnackbarError<BotDetailsDtoWithUser[]>(
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
    { errorMessage: t("settings.error.tokensError"), deps: [authUser] },
  );

  useEffect(() => {
    if (res.data) {
      const tokenIds = res.data.map((token) => token.id);
      setTokensInLoading((prev) => prev.filter((id) => tokenIds.includes(id)));
    }
  }, [res.data]);

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
      <Header setSearchValue={setSearchValue} reloadFetchTokens={res.reload} />
      <List sx={{ overflow: "auto" }}>
        <UsePromiseCond
          response={res}
          ifPending={() =>
            Array.from({ length: 3 }, (v, k) => k).map((v) => (
              <ListItem key={v} disablePadding>
                <Skeleton sx={{ width: 1, height: 50 }} />
              </ListItem>
            ))
          }
          ifFulfilled={(tokens) => (
            <TokenList
              tokens={tokens}
              searchValue={searchValue}
              setTokensInLoading={setTokensInLoading}
              tokensInLoading={tokensInLoading}
              reloadFetchTokens={res.reload}
            />
          )}
        />
      </List>
    </Box>
  );
}

export default Tokens;
