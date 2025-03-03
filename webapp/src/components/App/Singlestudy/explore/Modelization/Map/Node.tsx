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

import AddLinkIcon from "@mui/icons-material/AddLink";
import type { StudyMapNode } from "../../../../../../redux/ducks/studyMaps";
import { NodeContainer, NodeDefault, NodeHighlighted } from "./style";

interface PropType {
  node: StudyMapNode;
  linkCreation: (id: string) => void;
}

function Node(props: PropType) {
  const { node, linkCreation } = props;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <NodeContainer>
      {node.highlighted ? (
        <NodeHighlighted
          label={node.name}
          clickable
          nodecolor={node.color}
          rgbcolor={node.rgbColor}
        />
      ) : (
        <NodeDefault
          label={node.name}
          clickable
          nodecolor={node.color}
          rgbcolor={node.rgbColor}
          onDelete={() => linkCreation(node.id)}
          deleteIcon={<AddLinkIcon />}
        />
      )}
    </NodeContainer>
  );
}

export default Node;
