/* eslint-disable react/jsx-props-no-spreading */
import React, { useEffect, useState } from 'react';
import SvgIcon, { SvgIconProps } from '@mui/material/SvgIcon';
import { alpha, styled } from '@mui/material/styles';
import TreeView from '@mui/lab/TreeView';
import TreeItem, { TreeItemProps, treeItemClasses } from '@mui/lab/TreeItem';
import Collapse from '@mui/material/Collapse';
import { TransitionProps } from '@mui/material/transitions';
import { StudyMetadata, VariantTree } from '../../../../common/types';
import { StudyTree, getTreeNodes } from './utils';

function Circle(props: SvgIconProps & { circleColor: string }) {
  const { circleColor } = props;
  return (
    <SvgIcon
      className="close"
      fontSize="inherit"
      style={{ width: 14, height: 14, color: circleColor }}
      {...props}
    >
      {/* tslint:disable-next-line: max-line-length */}
      {/* <path d="M17.485 17.512q-.281.281-.682.281t-.696-.268l-4.12-4.147-4.12 4.147q-.294.268-.696.268t-.682-.281-.281-.682.294-.669l4.12-4.147-4.12-4.147q-.294-.268-.294-.669t.281-.682.682-.281.696 .268l4.12 4.147 4.12-4.147q.294-.268.696-.268t.682.281 .281.669-.294.682l-4.12 4.147 4.12 4.147q.294.268 .294.669t-.281.682zM22.047 22.074v0 0-20.147 0h-20.12v0 20.147 0h20.12zM22.047 24h-20.12q-.803 0-1.365-.562t-.562-1.365v-20.147q0-.776.562-1.351t1.365-.575h20.147q.776 0 1.351.575t.575 1.351v20.147q0 .803-.575 1.365t-1.378.562v0z" /> */}
      <circle cx="12" cy="12" r="12" />
    </SvgIcon>
  );
}

const StyledTreeItem = styled((props: TreeItemProps & { lineColor: string }) => {
  const { lineColor, ...other } = props;
  return <TreeItem {...other} />;
})(({ theme, lineColor }) => ({
  [`& .${treeItemClasses.iconContainer}`]: {
    '& .close': {
      opacity: 0.9,
    },
  },
  [`& .${treeItemClasses.group}`]: {
    marginLeft: 15,
    paddingLeft: 18,
    borderLeft: `3px solid ${lineColor}`,
  },
}));

const fakeTree : StudyTree = {
  name: 'Root',
  attributes: {
    id: 'root',
    modificationDate: Date.now().toString(),
  },
  children: [
    {
      name: 'Node 1',
      attributes: {
        id: 'node1',
        modificationDate: Date.now().toString(),
      },
      children: [
        {
          name: 'Node 1.1',
          attributes: {
            id: 'node1.1',
            modificationDate: Date.now().toString(),
          },
          children: [
            {
              name: 'Node 1.1.1',
              attributes: {
                id: 'node1.1.1',
                modificationDate: Date.now().toString(),
              },
              children: [

              ],
            },
          ],
        },
      ],
    },
    {
      name: 'Node 2',
      attributes: {
        id: 'node2',
        modificationDate: Date.now().toString(),
      },
      children: [

      ],
    },
    {
      name: 'Node 3',
      attributes: {
        id: 'node3',
        modificationDate: Date.now().toString(),
      },
      children: [

      ],
    },
    {
      name: 'Node 4',
      attributes: {
        id: 'node4',
        modificationDate: Date.now().toString(),
      },
      children: [
        {
          name: 'Node 4.1',
          attributes: {
            id: 'node4.1',
            modificationDate: Date.now().toString(),
          },
          children: [

          ],
        },
      ],
    },
  ],
};

interface Props {
  study: StudyMetadata | undefined;
  parents: Array<StudyMetadata>;
  childrenTree: VariantTree | undefined;
}

export default function CustomizedTreeView(props: Props) {
  const { study, parents, childrenTree } = props;
  const [studyTree, setStudyTree] = useState<StudyTree>(fakeTree);
  let currentColorIndex = 0;

  const colors = [
    '#00B2FF',//'#A5B6C7',
    '#F56637',
    '#335622',
    '#56B667',
    '#793467',
    '#039944',
    '#297887',
    '#77A688',
    '#227878',
    '#676045',
  ];

  const renderTree = (tree: StudyTree) : React.ReactNode => {
    const colorIndex = currentColorIndex;
    //currentColorIndex += 1;
    return (
      <StyledTreeItem
        key={tree.attributes.id}
        nodeId={tree.attributes.id}
        label={tree.name}
        lineColor={colors[colorIndex]}
        expandIcon={<Circle circleColor={colors[colorIndex]} />}
        collapseIcon={<Circle circleColor={colors[colorIndex]} />}
        endIcon={<Circle circleColor={colors[colorIndex]} />}
      >
        {tree.children.length > 0 && tree.children.map((elm) => renderTree(elm))}
      </StyledTreeItem>
    );
  };

  useEffect(() => {
    const buildStudyTree = async () => {
      if (study && childrenTree) {
        const tmp = await getTreeNodes(study, parents, childrenTree);
        //setStudyTree(tmp);
      }
    };

    buildStudyTree();
  }, [study, parents, childrenTree]);

  return (
    <TreeView
      aria-label="customized"
      defaultExpanded={['1']}
      sx={{ width: '100%', flexGrow: 1, overflowY: 'auto' }}
    >
      {studyTree && renderTree(studyTree)}
    </TreeView>
  );
}
