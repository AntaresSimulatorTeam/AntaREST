/* eslint-disable react/jsx-props-no-spreading */
import React, { useEffect, useMemo, useState } from 'react';
import { Box, styled } from '@mui/material';
import { StudyMetadata, VariantTree } from '../../../../common/types';
import { StudyTree, getTreeNodes } from './utils';

export const Circle = styled(
  'circle',
  { shouldForwardProp: (prop) => prop !== 'hoverColor' },
)<{hoverColor: string }>(({ theme, hoverColor }) => ({
  cursor: 'pointer',
  '&:hover': {
    fill: hoverColor,
  },
}));
export const Rect = styled(
  'rect',
  { shouldForwardProp: (prop) => prop !== 'hoverColor' },
)<{hoverColor: string }>(({ theme, hoverColor }) => ({
  cursor: 'pointer',
  '&:hover': {
    fill: hoverColor,
  },
}));

const fakeTree : StudyTree = {
  name: 'Root',
  attributes: {
    id: 'root',
    modificationDate: Date.now().toString(),
  },
  drawOptions: {
    height: 4,
    nbAllChildrens: 7,
  },
  children: [
    {
      name: 'Node 1',
      attributes: {
        id: 'node1',
        modificationDate: Date.now().toString(),
      },
      drawOptions: {
        height: 3,
        nbAllChildrens: 2,
      },
      children: [
        {
          name: 'Node 1.1',
          attributes: {
            id: 'node1.1',
            modificationDate: Date.now().toString(),
          },
          drawOptions: {
            height: 2,
            nbAllChildrens: 1,
          },
          children: [
            {
              name: 'Node 1.1.1',
              attributes: {
                id: 'node1.1.1',
                modificationDate: Date.now().toString(),
              },
              drawOptions: {
                height: 1,
                nbAllChildrens: 0,
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
      drawOptions: {
        height: 1,
        nbAllChildrens: 0,
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
      drawOptions: {
        height: 1,
        nbAllChildrens: 0,
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
      drawOptions: {
        height: 2,
        nbAllChildrens: 1,
      },
      children: [
        {
          name: 'Node 4.1',
          attributes: {
            id: 'node4.1',
            modificationDate: Date.now().toString(),
          },
          drawOptions: {
            height: 1,
            nbAllChildrens: 0,
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
  onClick: (studyId: string) => void;
}

export default function CustomizedTreeView(props: Props) {
  const { study, parents, childrenTree, onClick } = props;
  const [studyTree, setStudyTree] = useState<StudyTree>(fakeTree);

  const colors = [
    '#00B2FF', // '#A5B6C7',
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

  const TILE_SIZE = 100;
  const TILE_SIZE_2 = TILE_SIZE / 2;
  const CIRCLE_RADIUS = 25;
  const DCX = TILE_SIZE / 2;
  const DCY = TILE_SIZE - CIRCLE_RADIUS;
  const STROKE_WIDTH = 10;
  const STROKE_WIDTH_2 = STROKE_WIDTH / 2;
  const treeWidth = useMemo(() => {
    const { drawOptions } = studyTree;
    const { nbAllChildrens } = drawOptions;
    return TILE_SIZE * (nbAllChildrens + 1);
  }, [studyTree]);

  const RECT_WIDTH = treeWidth / 2;
  const RECT_X_SPACING = 10;
  const RECT_Y_SPACING = 5;
  const RECT_DECORATION = 5;
  const TEXT_SPACING = 30;
  const TEXT_SIZE = RECT_WIDTH / 16;

  const buildRecursiveTree = (tree: StudyTree, i = 0, j = 0) : Array<React.ReactNode> => {
    const { drawOptions, name, attributes, children } = tree;
    const { id, modificationDate } = attributes;
    const { nbAllChildrens } = drawOptions;
    const hoverColor = colors[i % colors.length];
    const color = `${hoverColor}BB`;
    const rectColor = `${hoverColor}22`;
    const rectHoverColor = `${hoverColor}44`;
    const verticalLineColor = `${colors[(i + 1) % colors.length]}BB`;
    let verticalLineEnd = 0;

    if (children.length > 0) {
      verticalLineEnd = nbAllChildrens - children[children.length - 1].drawOptions.nbAllChildrens;
      verticalLineEnd = (j + 1 + verticalLineEnd) * TILE_SIZE - CIRCLE_RADIUS;
    }

    const cx = i * TILE_SIZE + DCX;
    const cy = j * TILE_SIZE + DCY;
    let res : Array<React.ReactNode> = [<Circle key={`circle-${i}-${j}`} cx={cx} cy={cy} r={CIRCLE_RADIUS} fill={color} hoverColor={hoverColor} onClick={() => console.log('NODE: ', tree.name)} />,
      <Rect key={`rect-${i}-${j}`} x="0" y={cy - TILE_SIZE_2} width={RECT_WIDTH} height={TILE_SIZE - RECT_Y_SPACING} fill={rectColor} hoverColor={rectHoverColor} />,
      <Rect key={`rect-for-name-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING} y={cy - TILE_SIZE_2} width={RECT_WIDTH} height={TILE_SIZE - RECT_Y_SPACING} fill={rectColor} hoverColor={hoverColor} onClick={() => onClick(id)} />,
      <Rect key={`rect-for-name-deco-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING} y={cy - TILE_SIZE_2} width={RECT_DECORATION} height={TILE_SIZE - RECT_Y_SPACING} fill={hoverColor} hoverColor={hoverColor} />,
      <text key={`name-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING + RECT_DECORATION + TEXT_SPACING} y={cy} fill="white" fontSize={TEXT_SIZE}>{name}</text>];
    if (verticalLineEnd > 0) { res.push(<path key={`verticalLine-${i}-${j}`} d={`M ${cx} ${cy + CIRCLE_RADIUS} L ${cx} ${verticalLineEnd}`} fill={verticalLineColor} stroke={verticalLineColor} strokeWidth={`${STROKE_WIDTH}`} />); }
    if (i > 0) { res.push(<path key={`horizontalLine-${i}-${j}`} d={`M ${cx - CIRCLE_RADIUS} ${cy} L ${cx - TILE_SIZE - (STROKE_WIDTH_2)} ${cy}`} fill={color} stroke={color} strokeWidth={`${STROKE_WIDTH}`} />); }

    let recursiveHeight = 1;
    res = res.concat(children.map((elm, index) => {
      if (index === 0) recursiveHeight = j + 1;
      else recursiveHeight = recursiveHeight + children[index - 1].drawOptions.nbAllChildrens + 1;
      return buildRecursiveTree(elm, i + 1, recursiveHeight);
    }));
    return res;
  };

  const renderTree = (tree: StudyTree) : React.ReactNode => {
    const { drawOptions } = tree;
    const { height, nbAllChildrens } = drawOptions;
    /*
    NOTES:
    Width = 2*TILE_SIZE*treeHeight + RECT_X_SPACING (why 2* ? Because we reserve a section for text => name of study)
    Height = (nbAllChildrens + 1)  + TILE_SIZE_2;
    */
    return (
      <svg viewBox={`0 0 ${2 * TILE_SIZE * height + RECT_X_SPACING} ${TILE_SIZE * (nbAllChildrens + 1) + TILE_SIZE_2}`}>
        {buildRecursiveTree(tree, 0, 0) }
      </svg>
    );
  };

  useEffect(() => {
    const buildStudyTree = async () => {
      if (study && childrenTree) {
        const tmp = await getTreeNodes(study, parents, childrenTree);
        // setStudyTree(tmp);
      }
    };

    buildStudyTree();
  }, [study, parents, childrenTree]);

  return (
    <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="flex-start" sx={{ width: '100%', flexGrow: 1, overflowY: 'auto' }}>
      <Box flexGrow={1} height="600px" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start">
        {studyTree && renderTree(studyTree)}
      </Box>
    </Box>
  );
}
